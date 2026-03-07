"""LangGraph Pulse Agent pipeline: profile -> analyze -> generate.

Stateless pipeline -- each invocation starts with fresh PulseAgentState.
No message history between runs. Every LLM call is a one-shot request.

Nodes:
  1. profile_data_node: Deep-profile files via E2B sandbox
  2. run_analyses_node: LLM generates signal candidates, fan-out validation
  3. generate_signals_node: Validate signals through PulseAgentOutput, generate report
"""

import asyncio
import json
import logging
import uuid
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph

from app.agents.config import (
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
from app.schemas.pulse import PulseAgentOutput, SignalOutput

logger = logging.getLogger(__name__)


class PulseAgentState(TypedDict):
    """State for the LangGraph Pulse Agent pipeline."""

    collection_id: str
    user_id: str
    pulse_run_id: str
    user_context: str  # Optional user guidance
    file_data: list[dict]  # [{file_id, filename, file_bytes, file_type, data_summary, deep_profile}]
    file_profiles: list[dict]  # Deep profile JSON per file (from profiling node)
    signal_candidates: list[dict]  # Hypotheses from Pulse Agent brain
    validated_signals: list[dict]  # Confirmed signals after Coder pipeline
    signals_output: list[dict]  # Final PulseAgentOutput-validated dicts
    report_content: str  # Generated markdown report
    error: str  # Error message if failed


def _get_pulse_llm():
    """Create LLM instance configured for the pulse_agent."""
    settings = get_settings()
    provider = get_agent_provider("pulse_agent")
    model = get_agent_model("pulse_agent")
    temperature = get_agent_temperature("pulse_agent")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("pulse_agent")

    return get_llm(
        provider=provider,
        model=model,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )


async def _validate_single_candidate(
    candidate: dict,
    file_data: list[dict],
    settings,
) -> dict | None:
    """Validate a single signal candidate through Coder -> Checker -> E2B pipeline.

    Args:
        candidate: Signal candidate dict with code_instructions, title, etc.
        file_data: List of file data dicts for sandbox execution.
        settings: App settings instance.

    Returns:
        Validated result dict with analysis_text, statistical_evidence,
        chart_data, chart_type. None on failure.
    """
    from app.agents.code_checker import validate_code
    from app.agents.coding import extract_code_block
    from app.services.sandbox.e2b_runtime import E2BSandboxRuntime

    try:
        # Step 1: Generate analysis code via Coding Agent LLM
        pulse_prompt = get_agent_prompt("pulse_agent")
        llm = _get_pulse_llm()

        code_instructions = candidate.get("code_instructions", "")
        chart_hint = candidate.get("chart_hint", "")

        code_gen_prompt = (
            f"Write a Python script that performs the following statistical analysis:\n"
            f"{code_instructions}\n\n"
            f"Chart suggestion: {chart_hint}\n\n"
            f"The script should:\n"
            f"1. Read the CSV file from /home/user/ directory\n"
            f"2. Perform the analysis\n"
            f"3. Print a JSON result with keys: analysis_text (str), "
            f"statistical_evidence (dict with metric, context, benchmark, impact), "
            f"chart_data (dict or null), chart_type (bar/line/scatter)\n"
            f"4. Use only pandas, numpy, scipy, json\n"
            f"5. Wrap output in print(json.dumps(result))\n"
        )

        response = await llm.ainvoke([
            SystemMessage(content=pulse_prompt),
            HumanMessage(content=code_gen_prompt),
        ])

        code = extract_code_block(response.content)

        # Step 2: Validate code safety
        validation = validate_code(code)
        if not validation.is_valid:
            logger.warning(
                "Code validation failed for candidate '%s': %s",
                candidate.get("title", "unknown"),
                validation.errors,
            )
            return None

        # Step 3: Execute in E2B sandbox
        runtime = E2BSandboxRuntime(
            timeout_seconds=settings.pulse_sandbox_timeout_seconds
        )

        # Prepare data files for sandbox
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
                "Sandbox execution failed for candidate '%s': %s",
                candidate.get("title", "unknown"),
                execution_result.error,
            )
            return None

        # Parse result JSON from stdout
        last_line = execution_result.stdout[-1].strip()
        result = json.loads(last_line)

        # Validate required keys
        if "analysis_text" not in result:
            return None

        return result

    except Exception as e:
        logger.warning(
            "Candidate validation failed for '%s': %s",
            candidate.get("title", "unknown"),
            str(e),
        )
        return None


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


async def run_analyses_node(state: PulseAgentState) -> dict:
    """Run Pulse Agent brain + fan-out validation.

    Step A: LLM generates signal candidates from file profiles.
    Step B: Fan-out validation of each candidate via Coder pipeline.

    Stateless: No message history. One-shot LLM call with current run data.
    """
    if state.get("error"):
        return {"validated_signals": [], "signal_candidates": []}

    try:
        # Step A: Pulse Agent brain -- generate signal candidates
        llm = _get_pulse_llm()
        system_prompt = get_agent_prompt("pulse_agent")

        # Build analysis request
        file_profiles_str = json.dumps(state.get("file_profiles", []), indent=2)
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
            f"Return a JSON array of signal candidates. Each candidate must have:\n"
            f"- title (str): Brief signal title\n"
            f"- severity_hint (str): critical, warning, or info\n"
            f"- category (str): e.g., anomaly, trend, correlation, distribution\n"
            f"- code_instructions (str): What Python code should do to validate this signal\n"
            f"- chart_hint (str): Suggested chart type and what to show\n\n"
            f"Return ONLY the JSON array, no markdown formatting."
        )

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_prompt),
        ])

        # Parse candidates from LLM response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        candidates = json.loads(content)

        if not isinstance(candidates, list):
            candidates = [candidates]

        # Step B: Fan-out validation
        settings = get_settings()
        tasks = [
            _validate_single_candidate(candidate, state.get("file_data", []), settings)
            for candidate in candidates
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        validated_signals = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning("Fan-out validation exception: %s", str(r))
                continue
            if r is not None:
                validated_signals.append(r)

        if len(validated_signals) == 0:
            return {
                "signal_candidates": candidates,
                "validated_signals": [],
                "error": "No signals could be validated from the analysis",
            }

        return {
            "signal_candidates": candidates,
            "validated_signals": validated_signals,
        }

    except Exception as e:
        logger.error("Analysis node failed: %s", str(e))
        return {
            "signal_candidates": [],
            "validated_signals": [],
            "error": f"Analysis failed: {str(e)}",
        }


async def generate_signals_node(state: PulseAgentState) -> dict:
    """Validate signals through PulseAgentOutput and generate report.

    For each validated signal, constructs a SignalOutput dict with normalized
    severity/chartType. Validates all through PulseAgentOutput Pydantic model.
    Generates markdown detection summary report via LLM.
    """
    if state.get("error"):
        return {"signals_output": [], "report_content": ""}

    validated_signals = state.get("validated_signals", [])
    if not validated_signals:
        return {
            "signals_output": [],
            "report_content": "",
            "error": "No validated signals to generate output from",
        }

    # Build SignalOutput dicts
    signal_dicts = []
    for i, vs in enumerate(validated_signals):
        try:
            # Extract evidence, ensuring all required fields
            evidence = vs.get("statistical_evidence", {})
            if not isinstance(evidence, dict):
                evidence = {"metric": str(evidence), "context": "", "benchmark": "", "impact": ""}

            # Ensure all evidence fields exist
            evidence.setdefault("metric", "N/A")
            evidence.setdefault("context", "N/A")
            evidence.setdefault("benchmark", "N/A")
            evidence.setdefault("impact", "N/A")

            # Get severity from candidate or evidence, normalize to lowercase
            severity_raw = vs.get("severity_hint", vs.get("severity", "info"))
            severity = severity_raw.lower() if isinstance(severity_raw, str) else "info"
            if severity not in ("critical", "warning", "info"):
                severity = "info"

            # Get chart type, normalize
            chart_type_raw = vs.get("chart_type", vs.get("chartType", "bar"))
            chart_type = chart_type_raw.lower() if isinstance(chart_type_raw, str) else "bar"
            if chart_type not in ("bar", "line", "scatter"):
                chart_type = "bar"

            signal_dict = {
                "id": f"sig-{uuid.uuid4().hex[:8]}",
                "title": vs.get("title", f"Signal {i + 1}"),
                "severity": severity,
                "category": vs.get("category", "general"),
                "chartType": chart_type,
                "analysis_text": vs.get("analysis_text", ""),
                "statistical_evidence": evidence,
                "chart_data": vs.get("chart_data"),
            }
            signal_dicts.append(signal_dict)
        except Exception as e:
            logger.warning("Failed to build signal dict for index %d: %s", i, str(e))
            continue

    # Validate through PulseAgentOutput
    valid_signals = []
    for sd in signal_dicts:
        try:
            signal = SignalOutput(**sd)
            valid_signals.append(signal)
        except Exception as e:
            logger.warning("Signal validation failed: %s -- %s", sd.get("title", "?"), str(e))
            continue

    if not valid_signals:
        return {
            "signals_output": [],
            "report_content": "",
            "error": "All signals failed PulseAgentOutput validation",
        }

    # Validate as a batch through PulseAgentOutput
    try:
        output = PulseAgentOutput(signals=valid_signals)
    except Exception as e:
        logger.error("PulseAgentOutput batch validation failed: %s", str(e))
        return {
            "signals_output": [],
            "report_content": "",
            "error": f"PulseAgentOutput validation failed: {str(e)}",
        }

    # Generate report via LLM
    try:
        llm = _get_pulse_llm()
        system_prompt = get_agent_prompt("pulse_agent")

        signals_summary = json.dumps(
            [s.model_dump() for s in output.signals], indent=2
        )

        report_prompt = (
            f"Generate a detection summary report in markdown format.\n\n"
            f"## Detected Signals\n{signals_summary}\n\n"
            f"The report should include:\n"
            f"1. Executive summary (2-3 sentences)\n"
            f"2. Signal-by-signal breakdown\n"
            f"3. Methodology notes\n\n"
            f"Write in professional analytical tone."
        )

        report_response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=report_prompt),
        ])
        report_content = report_response.content
    except Exception as e:
        logger.warning("Report generation failed: %s", str(e))
        report_content = "Report generation failed."

    return {
        "signals_output": [s.model_dump() for s in output.signals],
        "report_content": report_content,
    }


def build_pulse_graph():
    """Build and compile the Pulse Agent LangGraph pipeline.

    Returns:
        CompiledGraph: Compiled LangGraph ready for ainvoke().
    """
    graph = StateGraph(PulseAgentState)
    graph.add_node("profile_data", profile_data_node)
    graph.add_node("run_analyses", run_analyses_node)
    graph.add_node("generate_signals", generate_signals_node)
    graph.set_entry_point("profile_data")
    graph.add_edge("profile_data", "run_analyses")
    graph.add_edge("run_analyses", "generate_signals")
    graph.set_finish_point("generate_signals")
    return graph.compile()
