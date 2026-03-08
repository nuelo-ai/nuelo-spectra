"""LangGraph Pulse Agent pipeline: orchestrator pattern with structured output.

Stateless pipeline -- each invocation starts with fresh PulseAgentState.
No message history between runs. Every LLM call is a one-shot request.

Architecture: Pulse Agent acts as brain/orchestrator calling independent tool agents.
All LLM calls (except code-generating ones) use with_structured_output() with Pydantic models.

Nodes:
  1. profile_data_node: Deep-profile files via E2B sandbox
  2. generate_hypotheses_node: Pulse brain generates signal candidates (structured output)
  3. validate_signals_node: Fan-out per-signal validation loop (Coder -> Validator -> Sandbox -> Interpret -> Viz)
  4. write_report_node: Report Writer agent generates final report (structured output)
"""

import asyncio
import json
import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph

from app.agents.config import (
    get_agent_config_field,
    get_agent_max_tokens,
    get_agent_model,
    get_agent_prompt,
    get_agent_provider,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm
from app.agents.pulse_profiler import profile_files_in_sandbox
from app.config import get_settings
from app.schemas.pulse import (
    BusinessFinding,
    HypothesisOutput,
    ReportOutput,
)

logger = logging.getLogger(__name__)


class PulseAgentState(TypedDict):
    """State for the LangGraph Pulse Agent pipeline."""

    collection_id: str
    user_id: str
    pulse_run_id: str
    user_context: str  # Optional user guidance
    file_data: list[dict]  # [{file_id, filename, file_bytes, file_type, data_summary, deep_profile}]
    file_profiles: list[dict]  # Deep profile JSON per file (from profiling node)
    hypotheses: list[dict]  # From hypothesis node
    signal_results: list[dict]  # Merged results per signal
    report: dict  # From report writer node (executive_summary, content)
    error: str  # Error message if failed


def _get_llm_for_agent(agent_name: str):
    """Create LLM instance configured for a specific agent.

    Args:
        agent_name: Agent config key (e.g., 'pulse_agent', 'pulse_coder').

    Returns:
        Configured LLM instance.
    """
    settings = get_settings()
    provider = get_agent_provider(agent_name)
    model = get_agent_model(agent_name)
    temperature = get_agent_temperature(agent_name)
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens(agent_name)

    return get_llm(
        provider=provider,
        model=model,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )


async def profile_data_node(state: PulseAgentState) -> dict:
    """Profile files using E2B sandbox.

    Calls profile_files_in_sandbox with file_data from state.
    Returns file_profiles list.
    """
    try:
        settings = get_settings()
        profiles = await profile_files_in_sandbox(state["file_data"], settings)
        # profiles is list of (file_id, profile_dict) tuples
        file_profiles = [profile for _, profile in profiles]
        return {"file_profiles": file_profiles}
    except Exception as e:
        logger.error("Profiling failed: %s", str(e))
        return {"error": str(e), "file_profiles": []}


async def generate_hypotheses_node(state: PulseAgentState) -> dict:
    """Pulse brain generates signal candidates using structured output.

    Uses with_structured_output(HypothesisOutput) -- no manual JSON parsing.
    Only the Pulse Agent (brain) receives data_summary.
    """
    if state.get("error"):
        return {"hypotheses": []}

    try:
        llm = _get_llm_for_agent("pulse_agent")
        structured_llm = llm.with_structured_output(HypothesisOutput)
        system_prompt = get_agent_prompt("pulse_agent")

        # Build deep profile context
        file_profiles_str = json.dumps(state.get("file_profiles", []), indent=2)

        # Build data summaries (only Pulse Agent gets this)
        data_summaries = []
        for fd in state.get("file_data", []):
            summary = fd.get("data_summary", "")
            if summary:
                data_summaries.append(f"- {fd.get('filename', 'unknown')}: {summary}")
        data_summaries_str = "\n".join(data_summaries) if data_summaries else "No summaries available"

        user_context = state.get("user_context", "") or "No specific user context provided"

        analysis_prompt = (
            f"Analyze the following data profiles and generate signal candidates.\n\n"
            f"## Data Summaries\n{data_summaries_str}\n\n"
            f"## Deep Profiles\n{file_profiles_str}\n\n"
            f"## User Context\n{user_context}\n\n"
            f"Generate 5-8 signal candidates as hypotheses for investigation. "
            f"Each hypothesis must have a business-language title, severity assessment, "
            f"category, specific prescriptive code_instructions for validation, "
            f"and a chart_hint describing what the visualization should show."
        )

        result = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_prompt),
        ])

        logger.info(
            "Pulse hypotheses generated: %d candidates",
            len(result.hypotheses),
        )

        return {"hypotheses": [h.model_dump() for h in result.hypotheses]}

    except Exception as e:
        logger.error("Hypothesis generation failed: %s", str(e))
        return {"hypotheses": [], "error": f"Hypothesis generation failed: {str(e)}"}


async def _process_single_signal(
    hypothesis: dict,
    file_data: list[dict],
    settings,
) -> dict | None:
    """Process a single signal through Coder -> Validator -> Sandbox -> Interpret -> Viz.

    Args:
        hypothesis: Signal hypothesis dict from generate_hypotheses_node.
        file_data: List of file data dicts for sandbox execution.
        settings: App settings instance.

    Returns:
        Merged signal result dict, or None on failure.
    """
    from app.agents.code_checker import validate_code
    from app.agents.coding import extract_code_block
    from app.services.sandbox.e2b_runtime import E2BSandboxRuntime

    title = hypothesis.get("title", "Unknown")

    try:
        # --- Step A: Coder ---
        # Coder gets deep_profile + code_instructions + file paths (NOT data_summary)
        coder_llm = _get_llm_for_agent("pulse_coder")
        coder_prompt = get_agent_prompt("pulse_coder")

        code_instructions = hypothesis.get("code_instructions", "")
        chart_hint = hypothesis.get("chart_hint", "")

        # Build file list and deep_profile context for coder
        file_lines = []
        deep_profiles_for_coder = []
        for fd in file_data:
            fn = fd.get("filename", "data.csv")
            ft = fd.get("file_type", "csv")
            read_func = "pd.read_excel" if ft in ("xlsx", "xls") or fn.endswith((".xlsx", ".xls")) else "pd.read_csv"
            file_lines.append(f"  - /home/user/{fn} (use {read_func})")
            dp = fd.get("deep_profile")
            if dp:
                deep_profiles_for_coder.append(f"File: {fn}\n{json.dumps(dp, indent=2)}")
        files_str = "\n".join(file_lines)
        deep_profile_str = "\n\n".join(deep_profiles_for_coder) if deep_profiles_for_coder else "No deep profiles available"

        code_gen_template = get_agent_config_field("pulse_coder", "code_gen_prompt")
        code_gen_prompt = code_gen_template.format(
            code_instructions=code_instructions,
            chart_hint=chart_hint,
            files_str=files_str,
        )

        # Append deep profile context so coder knows data schema
        code_gen_prompt += f"\n\n## Data Schema (Deep Profile)\n{deep_profile_str}"

        response = await coder_llm.ainvoke([
            SystemMessage(content=coder_prompt),
            HumanMessage(content=code_gen_prompt),
        ])

        code = extract_code_block(response.content)
        logger.info("  [%s] Code generated (%d chars)", title, len(code) if code else 0)

        # --- Step B: Validator ---
        validation = validate_code(code)
        if not validation.is_valid:
            logger.warning("  [%s] Code validation FAILED: %s", title, validation.errors)
            return None

        logger.info("  [%s] Code validation passed", title)

        # --- Step C: Sandbox ---
        runtime = E2BSandboxRuntime(
            timeout_seconds=settings.pulse_sandbox_timeout_seconds
        )

        data_files = []
        for fd in file_data:
            fb = fd.get("file_bytes")
            fn = fd.get("filename", "data.csv")
            if fb:
                data_files.append((fb, fn))

        execution_result = await asyncio.to_thread(
            runtime.execute,
            code=code,
            timeout=float(settings.pulse_sandbox_timeout_seconds),
            data_files=data_files if data_files else None,
        )

        if not execution_result.success or not execution_result.stdout:
            logger.warning(
                "  [%s] Sandbox execution FAILED: error=%s stderr=%s",
                title,
                execution_result.error,
                execution_result.stderr[:500] if execution_result.stderr else None,
            )
            return None

        logger.info("  [%s] Sandbox execution OK, stdout lines: %d", title, len(execution_result.stdout))

        # Parse result JSON from last stdout line
        last_line = execution_result.stdout[-1].strip()
        sandbox_result = json.loads(last_line)

        if "analysis_text" not in sandbox_result:
            logger.warning("  [%s] Missing analysis_text in sandbox output", title)
            return None

        # --- Step D: Interpreter ---
        interpreter_llm = _get_llm_for_agent("pulse_interpreter")
        structured_interpreter = interpreter_llm.with_structured_output(BusinessFinding)
        interpreter_prompt = get_agent_prompt("pulse_interpreter")

        # Pass compact sandbox output + hypothesis context (NOT raw data or profiles)
        interpret_message = (
            f"Interpret the following statistical finding for executive leadership.\n\n"
            f"## Hypothesis\n"
            f"Title: {title}\n"
            f"Original instructions: {code_instructions}\n\n"
            f"## Statistical Results\n"
            f"Analysis: {sandbox_result.get('analysis_text', '')}\n"
            f"Evidence: {json.dumps(sandbox_result.get('statistical_evidence', {}))}\n\n"
            f"Convert this into a business-language finding. No statistical jargon."
        )

        finding = await structured_interpreter.ainvoke([
            SystemMessage(content=interpreter_prompt),
            HumanMessage(content=interpret_message),
        ])

        logger.info("  [%s] Interpretation complete: %s", title, finding.title)

        # --- Step E: Visualization (with 1 retry) ---
        chart_data = None
        chart_type = sandbox_result.get("chart_type")

        try:
            viz_llm = _get_llm_for_agent("pulse_viz")
            viz_system_prompt = get_agent_prompt("pulse_viz")

            viz_prompt_template = get_agent_config_field("pulse_viz", "viz_prompt")
            viz_message = viz_prompt_template.format(
                finding_title=finding.title,
                finding_text=finding.finding,
                chart_hint=chart_hint,
                files_str=files_str,
                deep_profile=deep_profile_str,
                statistical_evidence=json.dumps(sandbox_result.get("statistical_evidence", {})),
                analysis_text=sandbox_result.get("analysis_text", ""),
            )

            for viz_attempt in range(2):
                viz_response = await viz_llm.ainvoke([
                    SystemMessage(content=viz_system_prompt),
                    HumanMessage(content=viz_message),
                ])

                viz_code = extract_code_block(viz_response.content)
                viz_validation = validate_code(viz_code)

                if not viz_validation.is_valid:
                    logger.warning("  [%s] Viz code validation failed (attempt %d): %s", title, viz_attempt + 1, viz_validation.errors)
                    if viz_attempt == 0:
                        viz_message += f"\n\nPREVIOUS ATTEMPT FAILED code validation: {viz_validation.errors}\nFix the issues and try again."
                    continue

                viz_runtime = E2BSandboxRuntime(
                    timeout_seconds=settings.pulse_sandbox_timeout_seconds
                )
                viz_result = await asyncio.to_thread(
                    viz_runtime.execute,
                    code=viz_code,
                    timeout=float(settings.pulse_sandbox_timeout_seconds),
                    data_files=data_files if data_files else None,
                )

                if viz_result.success and viz_result.stdout:
                    viz_last_line = viz_result.stdout[-1].strip()
                    chart_data = json.loads(viz_last_line)
                    # Handle wrapped chart JSON
                    if isinstance(chart_data, dict) and "chart" in chart_data:
                        chart_data = chart_data["chart"]
                    logger.info("  [%s] Visualization generated (attempt %d)", title, viz_attempt + 1)
                    break
                else:
                    error_info = str(viz_result.error)[:300] if viz_result.error else "unknown"
                    logger.warning(
                        "  [%s] Viz sandbox failed (attempt %d): error=%s",
                        title, viz_attempt + 1, error_info,
                    )
                    if viz_attempt == 0:
                        viz_message += f"\n\nPREVIOUS ATTEMPT FAILED with sandbox error:\n{error_info}\nFix the error and try again."

        except Exception as viz_err:
            logger.warning("  [%s] Visualization failed (signal still valid): %s", title, str(viz_err))

        # --- Merge result ---
        return {
            "title": finding.title,
            "finding": finding.finding,
            "severity": finding.severity,
            "category": finding.category,
            "evidence": finding.evidence.model_dump(),
            "chart_data": chart_data,
            "chart_type": chart_type,
            "generated_code": code,
            "analysis_text": sandbox_result.get("analysis_text", ""),
        }

    except Exception as e:
        logger.warning(
            "Pulse signal '%s' exception: %s: %s",
            title,
            type(e).__name__,
            str(e)[:500],
        )
        return None


async def validate_signals_node(state: PulseAgentState) -> dict:
    """Fan-out per-signal validation loop.

    For each hypothesis, runs the full sub-pipeline:
    Coder -> Validator -> Sandbox -> Interpret -> Viz

    Uses asyncio.gather() for parallelism across signals.
    """
    if state.get("error"):
        return {"signal_results": []}

    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        return {
            "signal_results": [],
            "error": "No hypotheses to validate",
        }

    settings = get_settings()
    tasks = [
        _process_single_signal(h, state.get("file_data", []), settings)
        for h in hypotheses
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    signal_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.warning(
                "Pulse hypothesis [%d] '%s' exception: %s",
                i, hypotheses[i].get("title", "?"), str(r)
            )
            continue
        if r is None:
            logger.warning(
                "Pulse hypothesis [%d] '%s' rejected (None)",
                i, hypotheses[i].get("title", "?")
            )
            continue
        logger.info(
            "Pulse hypothesis [%d] '%s' validated",
            i, hypotheses[i].get("title", "?")
        )
        signal_results.append(r)

    logger.info(
        "Pulse fan-out complete: %d hypotheses, %d validated",
        len(hypotheses), len(signal_results)
    )

    if len(signal_results) == 0:
        return {
            "signal_results": [],
            "error": "No signals could be validated from the hypotheses",
        }

    return {"signal_results": signal_results}


async def write_report_node(state: PulseAgentState) -> dict:
    """Report Writer agent generates the final report using structured output.

    Uses with_structured_output(ReportOutput).
    Receives only signal results as context.
    """
    if state.get("error"):
        return {"report": {"executive_summary": "", "content": ""}}

    signal_results = state.get("signal_results", [])
    if not signal_results:
        return {"report": {"executive_summary": "", "content": "No signals detected."}}

    try:
        report_llm = _get_llm_for_agent("pulse_report_writer")
        structured_report = report_llm.with_structured_output(ReportOutput)
        report_prompt = get_agent_prompt("pulse_report_writer")

        # Pass only signal results to report writer (no raw data or profiles)
        signals_summary = json.dumps(signal_results, indent=2)

        report_message = (
            f"Generate a detection report based on these findings.\n\n"
            f"## Detected Signals ({len(signal_results)} total)\n{signals_summary}\n\n"
            f"Write an executive-friendly report with:\n"
            f"1. Executive summary (2-3 sentences)\n"
            f"2. Signal-by-signal breakdown with key metrics\n"
            f"3. Actionable insights\n\n"
            f"Write in professional business language for leadership."
        )

        result = await structured_report.ainvoke([
            SystemMessage(content=report_prompt),
            HumanMessage(content=report_message),
        ])

        logger.info("Report generated: %d chars", len(result.content))
        return {"report": result.model_dump()}

    except Exception as e:
        logger.error("Report generation failed: %s", str(e))
        return {"report": {"executive_summary": "", "content": "Report generation failed."}}


def build_pulse_graph():
    """Build and compile the Pulse Agent LangGraph pipeline.

    4 nodes in sequence:
    profile_data -> generate_hypotheses -> validate_signals -> write_report

    Returns:
        CompiledGraph: Compiled LangGraph ready for ainvoke().
    """
    graph = StateGraph(PulseAgentState)
    graph.add_node("profile_data", profile_data_node)
    graph.add_node("generate_hypotheses", generate_hypotheses_node)
    graph.add_node("validate_signals", validate_signals_node)
    graph.add_node("write_report", write_report_node)
    graph.set_entry_point("profile_data")
    graph.add_edge("profile_data", "generate_hypotheses")
    graph.add_edge("generate_hypotheses", "validate_signals")
    graph.add_edge("validate_signals", "write_report")
    graph.set_finish_point("write_report")
    return graph.compile()
