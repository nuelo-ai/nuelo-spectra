"""Visualization Agent for generating Plotly chart code from execution results.

This agent generates Plotly Python code -- it does NOT execute it.
Execution is handled separately (Phase 22). The agent receives tabular JSON
data from the Coding Agent's sandbox run and produces chart code that outputs
Plotly figure JSON via fig.to_json().
"""

import logging
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer

from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm, validate_llm_response, EmptyLLMResponseError
from app.agents.coding import extract_code_block
from app.agents.state import ChatAgentState
from app.config import get_settings

_MAX_DATA_CHARS = 8000
"""Max characters of execution_result to include in prompt (approximately 200 data rows)."""

logger = logging.getLogger("spectra.visualization")


def build_data_shape_hints(execution_result: str) -> str:
    """Build data shape hints to help the LLM select the correct chart type.

    Analyzes the execution_result JSON to report:
    - For list of dicts: row count, column count, per-column type and unique values
    - For single dict: key count and key names
    - For unparseable data: fallback message

    Args:
        execution_result: JSON string of execution results from sandbox.

    Returns:
        str: Human-readable data shape description for the LLM prompt.

    Examples:
        >>> build_data_shape_hints('[{"region": "East", "sales": 50000}]')
        'Data shape: 1 rows, 2 columns\\n  - region: categorical (1 unique)\\n  - sales: numeric (1 unique)'
    """
    try:
        data = json.loads(execution_result)
    except (json.JSONDecodeError, TypeError):
        return "Data shape: unable to parse"

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        rows = len(data)
        columns = list(data[0].keys())
        col_count = len(columns)
        hints = [f"Data shape: {rows} rows, {col_count} columns"]

        for col in columns:
            # Collect sample values (first 5 rows)
            sample_values = []
            for row in data[:5]:
                if col in row:
                    sample_values.append(row[col])

            # Detect type from sample values
            all_unique = set()
            for row in data:
                if col in row and row[col] is not None:
                    all_unique.add(row[col])
            unique_count = len(all_unique)

            # Type detection: check if all sample values are numeric
            is_numeric = all(
                isinstance(v, (int, float)) for v in sample_values if v is not None
            )

            col_type = "numeric" if is_numeric else "categorical"
            hints.append(f"  - {col}: {col_type} ({unique_count} unique)")

        return "\n".join(hints)

    elif isinstance(data, dict):
        key_count = len(data)
        key_names = ", ".join(data.keys())
        return f"Data shape: single dict with {key_count} keys: {key_names}"

    return "Data shape: unable to parse"


async def visualization_agent_node(state: ChatAgentState) -> dict:
    """Generate Plotly chart code from execution results and user query.

    This agent node:
    1. Loads per-agent config from prompts.yaml
    2. Truncates large execution_result to prevent token overflow
    3. Builds data shape hints for chart type selection
    4. Invokes LLM with system prompt containing data, query, and chart hints
    5. Extracts Python code from the LLM response

    Args:
        state: Current chat workflow state containing:
            - execution_result: JSON string from sandbox execution
            - user_query: User's natural language query
            - chart_hint: User's explicit chart type preference (or empty string)
            - analysis: Data Analysis Agent's interpretation

    Returns:
        dict: State update with chart_code key (and optionally chart_error).

    Examples:
        >>> state = {
        ...     "execution_result": '[{"region": "East", "sales": 50000}]',
        ...     "user_query": "Show sales by region",
        ...     "chart_hint": "bar",
        ...     "analysis": "East leads with $50K",
        ...     "visualization_requested": True,
        ... }
        >>> result = await visualization_agent_node(state)
        >>> "chart_code" in result
        True
    """
    writer = get_stream_writer()

    # Send SSE event
    writer({
        "type": "visualization_started",
        "message": "Generating chart...",
    })

    settings = get_settings()

    # Load per-agent config from prompts.yaml (same pattern as coding.py)
    provider = get_agent_provider("visualization")
    model = get_agent_model("visualization")
    temperature = get_agent_temperature("visualization")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("visualization")

    # Build kwargs for provider-specific options
    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Load system prompt template
    system_prompt_template = get_agent_prompt("visualization")

    # Get state fields
    execution_result = state.get("execution_result", "")
    user_query = state.get("user_query", "")
    chart_hint = state.get("chart_hint", "")
    analysis = state.get("analysis", "")

    # Build data shape hints on FULL execution_result (before truncation)
    data_shape_hints = build_data_shape_hints(execution_result)

    # Truncate execution_result if too large
    if len(execution_result) > _MAX_DATA_CHARS:
        execution_result = execution_result[:_MAX_DATA_CHARS] + "\n... (data truncated for charting)"

    # Format system prompt
    system_prompt = system_prompt_template.format(
        execution_result=execution_result,
        user_query=user_query,
        chart_hint=chart_hint,
        analysis=analysis,
        data_shape_hints=data_shape_hints,
    )

    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the Plotly chart code."),
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Validate non-empty response
    try:
        content = validate_llm_response(response, provider, model, "visualization")
    except EmptyLLMResponseError:
        logger.warning("Visualization agent received empty LLM response")
        return {
            "chart_code": "",
            "chart_error": "Chart generation failed: empty LLM response",
        }

    # Extract code from response (reuse coding.py's extract_code_block)
    chart_code = extract_code_block(content)

    return {"chart_code": chart_code}
