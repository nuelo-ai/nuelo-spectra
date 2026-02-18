# Phase 21: Visualization Agent - Research

**Researched:** 2026-02-13
**Domain:** AI agent module for generating Plotly Python code from analysis results (LangGraph node, prompts.yaml config, chart type heuristics, data embedding)
**Confidence:** HIGH

## Summary

Phase 21 creates the Visualization Agent -- the 6th AI agent in Spectra's pipeline. This agent receives execution results (tabular JSON from the Coding Agent's sandbox run) and generates Plotly Python code that produces chart JSON via `fig.to_json()`. The agent does NOT execute code; it only generates it. Code execution happens in a separate node (Phase 22).

The key architectural insight is that the Visualization Agent is a **code generator, not a code executor**. It follows the exact same pattern as the existing Coding Agent: receive context via `ChatAgentState`, call an LLM with a system prompt from `prompts.yaml`, extract generated code from the response, and write it to a state field (`chart_code`). The only differences are: (1) the input is `execution_result` instead of `user_query` + `data_profile`, (2) the output is Plotly chart code instead of pandas analysis code, and (3) the code embeds data as Python literals instead of reading from files.

Phase 20 has already completed all infrastructure: Plotly is in the allowlist, `ChatAgentState` has 5 visualization fields (`visualization_requested`, `chart_hint`, `chart_code`, `chart_specs`, `chart_error`), the sandbox output parser extracts chart JSON from the `{"chart": ...}` key, and E2B Plotly 6.0.1 availability is verified. Phase 21 only needs to create the agent module, configure it in `prompts.yaml`, and write unit tests.

**Primary recommendation:** Create `backend/app/agents/visualization.py` following the exact pattern of `coding.py` (same imports, same config loading, same LLM invocation, same code extraction). The system prompt must include chart type selection heuristics, data embedding instructions, and the strict output contract (`print(json.dumps({"chart": json.loads(pio.to_json(fig))}))`). Configure in `prompts.yaml` as a new `visualization` agent entry. Do NOT wire it into the graph yet -- that is Phase 22.

## Standard Stack

### Core (Already Available -- No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LangGraph | Current (installed) | Agent state management, node interface | Already used by all 5 existing agents. `ChatAgentState` TypedDict is the contract. |
| langchain-core | Current (installed) | `SystemMessage`, `HumanMessage`, `AIMessage` | Standard message types used by all agent nodes. |
| Plotly (E2B sandbox) | 6.0.1 (pre-installed) | Chart generation library in sandbox | Verified in Phase 20 (test_plotly_availability.py). Agent generates code that uses it, but doesn't import it directly. |
| Python AST | stdlib | Code extraction from LLM response | `extract_code_block()` pattern already in `coding.py` -- reuse directly. |
| YAML config | `prompts.yaml` | Agent prompt + LLM provider/model config | All 5 agents use this pattern via `get_agent_prompt()`, `get_agent_model()`, etc. |

### Supporting (Already Available)

| Library | Version | Purpose | When Used |
|---------|---------|---------|-----------|
| `app.agents.config` | Internal | `get_agent_prompt()`, `get_agent_provider()`, `get_agent_model()`, `get_agent_temperature()`, `get_agent_max_tokens()`, `get_api_key_for_provider()` | Every agent node uses these to load per-agent config from prompts.yaml |
| `app.agents.llm_factory` | Internal | `get_llm()`, `validate_llm_response()`, `EmptyLLMResponseError` | Creates provider-agnostic LLM instances. Handles empty response validation. |
| `app.agents.coding.extract_code_block()` | Internal | Extracts Python code from markdown fences | Reuse for extracting generated Plotly code from LLM response |
| `app.config.get_settings()` | Internal | Application settings (API keys, timeouts) | Required for `get_api_key_for_provider()` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LLM-generated Plotly code | Template-based chart generation (no LLM) | Templates are faster and cheaper but cannot handle arbitrary data shapes, custom labels, or nuanced chart type selection. LLM approach is necessary for the "intelligent" agent requirement. |
| Single agent node | Two-stage agent (chart type proposal + code generation) | Two-stage is more accurate but adds latency (2 LLM calls). Single-stage with good heuristics in the prompt is sufficient for Phase 21. |
| Separate visualization code extractor | Reuse `extract_code_block()` from coding.py | Reusing is correct -- both agents produce Python code in markdown fences. No need for a new extractor. |

**Installation:**

No new packages needed. The Visualization Agent uses only existing backend dependencies.

## Architecture Patterns

### Recommended Project Structure

```
backend/app/agents/
  visualization.py          # NEW: Visualization Agent node function
backend/app/config/
  prompts.yaml              # MODIFY: Add "visualization" agent entry
backend/tests/
  test_visualization_agent.py  # NEW: Unit tests
```

### Pattern 1: Agent Node Function (Established Pattern)

**What:** Every agent in Spectra is an async function that takes `ChatAgentState` and returns a `dict` of state updates. The Visualization Agent follows this exact contract.

**When to use:** Always. This is the LangGraph node interface.

**Example (from existing `coding.py`, to be replicated):**

```python
# Source: backend/app/agents/coding.py (lines 62-210)
async def coding_agent(state: ChatAgentState) -> dict:
    """Generate Python code from natural language query."""
    writer = get_stream_writer()

    # Load per-agent config
    settings = get_settings()
    provider = get_agent_provider("coding")
    model = get_agent_model("coding")
    temperature = get_agent_temperature("coding")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("coding")

    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Load system prompt from YAML
    system_prompt_template = get_agent_prompt("coding")
    system_prompt = system_prompt_template.format(...)

    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Validate + extract
    content = validate_llm_response(response, provider, model, "coding")
    generated_code = extract_code_block(content)

    return {"generated_code": generated_code}
```

The Visualization Agent will follow this pattern but return `{"chart_code": chart_code}`.

### Pattern 2: YAML-Configured Agent (Established Pattern)

**What:** All agents are configured in `prompts.yaml` with `provider`, `model`, `temperature`, `system_prompt`, and `max_tokens`.

**When to use:** Always. This is how the project manages per-agent LLM configuration.

**Example (from existing `prompts.yaml`):**

```yaml
# Source: backend/app/config/prompts.yaml
agents:
  coding:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.0
    system_prompt: |
      Generate Python code for data analysis.
      ...
    max_tokens: 7000
```

The new `visualization` entry follows this exact structure.

### Pattern 3: Data Embedding in Generated Code

**What:** The Visualization Agent embeds `execution_result` data as a Python literal in the generated chart code. The chart sandbox does NOT upload data files.

**When to use:** Always for chart code generation. The execution_result is already computed, aggregated, and small (typically <100 rows).

**Why:** Avoids a second E2B file upload (~2-3s overhead), simplifies error handling, and makes chart code self-contained and reproducible.

**Example of generated code pattern:**

```python
import plotly.express as px
import plotly.io as pio
import json

# Data embedded as Python literal (from execution_result)
data = [
    {"region": "East", "sales": 50000},
    {"region": "West", "sales": 35000},
    {"region": "North", "sales": 42000},
    {"region": "South", "sales": 28000}
]

fig = px.bar(data, x="region", y="sales", title="Sales by Region")
fig.update_layout(template="plotly_white", height=400,
                  margin=dict(l=40, r=40, t=50, b=40))

chart_json = json.loads(pio.to_json(fig))
print(json.dumps({"chart": chart_json}))
```

### Pattern 4: Chart Type Heuristics in Prompt

**What:** The system prompt includes explicit rules for chart type selection based on data shape, with fallbacks when the user provides a chart_hint.

**When to use:** Always in the system prompt. These heuristics compensate for the known 15-30% chart type error rate in LLMs (per academic research referenced in PITFALLS-v0.4-visualization.md).

**Heuristic rules (to embed in system prompt):**

```
Chart Type Selection Rules:
1. If user specifies a chart type (chart_hint is not empty), use that type.
2. If data has a date/time column + numeric column: LINE chart (sort by date).
3. If data has one categorical column + one numeric column:
   - <= 8 categories: PIE chart (or DONUT with hole=0.4)
   - > 8 categories: BAR chart (horizontal if labels are long)
4. If data has two numeric columns: SCATTER plot.
5. If data has one numeric column only: HISTOGRAM.
6. If data has one categorical + one numeric with natural ordering: BAR chart.
7. For distribution analysis: BOX plot.
8. If fewer than 3 data points: DO NOT chart. Return empty chart_code.
9. Default fallback: BAR chart (safest for most data shapes).
```

### Pattern 5: Strict Output Contract

**What:** The generated chart code MUST end with the standard output contract that the Phase 20 output parser expects.

**When to use:** Always. The output parser in `graph.py:467-468` looks for `"chart"` key in parsed stdout JSON.

**Contract:**

```python
# Single chart output contract
chart_json = json.loads(pio.to_json(fig))
print(json.dumps({"chart": chart_json}))
```

This aligns with the parser at `graph.py` line 467: `if "chart" in parsed: chart_specs = json.dumps(parsed["chart"])`.

### Anti-Patterns to Avoid

- **Anti-pattern: Generating HTML instead of JSON** -- Never use `fig.to_html()`. The output contract is JSON via `fig.to_json()`. HTML is 100x larger and requires iframe rendering.
- **Anti-pattern: Including `fig.write_image()` in generated code** -- Kaleido requires Chrome, which E2B lacks. Image export is client-side only (Phase 24).
- **Anti-pattern: Reading from files in chart code** -- Data must be embedded as Python literals. The viz sandbox should NOT upload data files.
- **Anti-pattern: Importing `open` or file I/O in chart code** -- The chart code only needs `plotly`, `json`, and optionally `pandas` for data manipulation.
- **Anti-pattern: Allowing custom JavaScript callbacks** -- Prior decision: Disallow custom JS in Plotly charts (XSS via prompt injection risk). No `updatemenus`, `sliders`, or JS callbacks.
- **Anti-pattern: Hardcoding specific hex colors** -- The prompt should instruct the agent to use `plotly_white` template and let Plotly's default `colorway` apply. Frontend overrides colors for theming (Phase 25).
- **Anti-pattern: Wiring the agent into the graph** -- Phase 21 creates the module only. Graph integration (conditional routing, viz_execute, viz_response) is Phase 22.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM provider instantiation | Custom provider factory | `get_llm()` from `llm_factory.py` | Already handles 5 providers (anthropic, openai, google, ollama, openrouter) with proper kwargs |
| Agent config loading | Reading YAML manually | `get_agent_prompt()`, `get_agent_model()`, etc. from `config.py` | Established pattern, includes LRU caching, handles fallback to default provider |
| Code extraction from LLM response | Custom regex parser | `extract_code_block()` from `coding.py` | Handles `python` markers, generic markers, and no-marker fallback |
| Empty response handling | Custom try/catch | `validate_llm_response()` from `llm_factory.py` | Centralized logging, structured error (EmptyLLMResponseError), consistent across all agents |
| Chart JSON serialization | Custom JSON encoder | `plotly.io.to_json(fig)` in generated code | Handles ndarray, datetime, NaN, removes UIDs -- custom encoder would miss edge cases |
| State typing | Ad-hoc dict | `ChatAgentState` TypedDict from `state.py` | Type safety, IDE completion, consistent with all other nodes |

**Key insight:** The Visualization Agent is architecturally identical to the Coding Agent. The only differences are: (1) different input fields (`execution_result` + `analysis` instead of `user_query` + `data_profile`), (2) different output field (`chart_code` instead of `generated_code`), and (3) different system prompt (chart-focused instead of data-focused). All infrastructure is reusable.

## Common Pitfalls

### Pitfall 1: LLM Generates Wrong Chart Type for Data Shape

**What goes wrong:** The LLM generates a pie chart for 25 categories (unreadable), a line chart for unordered categorical data, or a scatter plot with only 2 data points.
**Why it happens:** LLMs associate keywords with chart types ("distribution" -> histogram) without analyzing data shape. Academic research shows 15-30% chart type error rate.
**How to avoid:** Embed explicit chart type selection heuristics in the system prompt (Pattern 4 above). Include data shape metadata in the prompt: number of unique values per column, data types, row count. Provide the `chart_hint` from user query when available.
**Warning signs:** Charts that don't match the data (pie with many tiny slices, line connecting unrelated categories).
**Confidence:** HIGH -- verified by academic research (arxiv: 2412.02764v1, 2403.06158v1) and PITFALLS-v0.4-visualization.md Pitfall 3.

### Pitfall 2: Generated Code Fails to Embed Data Correctly

**What goes wrong:** The LLM generates code that references `df` or `execution_result` as a variable instead of embedding the actual data values as a Python literal. The viz sandbox has no `df` -- it runs standalone code.
**Why it happens:** The Coding Agent's prompt trains the LLM to assume `df` exists. The Visualization Agent must break this assumption. If the system prompt is not explicit enough, the LLM falls back to its training.
**How to avoid:** The system prompt must explicitly state: "Embed the data as a Python list of dicts. DO NOT reference `df` or any file. The sandbox has NO data files uploaded." Include the actual `execution_result` data in the prompt so the LLM can see and embed it.
**Warning signs:** Generated code contains `df[` or `pd.read_csv` references.
**Confidence:** HIGH -- based on codebase analysis showing the architectural separation between data sandbox (with files) and viz sandbox (without files).

### Pitfall 3: Execution Result Too Large for Prompt Context

**What goes wrong:** The `execution_result` from the Coding Agent is a stringified JSON of 10,000+ rows. Embedding this in the Visualization Agent's prompt exceeds token limits or produces garbled output.
**Why it happens:** Some queries produce large result sets (e.g., "Show me all transactions"). The full result is in `execution_result` as a JSON string.
**How to avoid:** Truncate `execution_result` in the Visualization Agent's prompt. For charting, typically only the first 100-200 rows matter. Add a truncation notice: "Data truncated to first N rows for charting." Alternatively, instruct the LLM to include aggregation in the chart code if the data is too granular.
**Warning signs:** LLM returns empty response (token budget exhausted on input), or generated code has truncated data literals.
**Confidence:** HIGH -- based on understanding that execution_result can be arbitrarily large (some queries return thousands of rows).

### Pitfall 4: Output Contract Mismatch with Parser

**What goes wrong:** The generated chart code ends with `print(fig.to_json())` instead of `print(json.dumps({"chart": json.loads(pio.to_json(fig))}))`. The output parser in `graph.py` looks for a `"chart"` key in the parsed JSON object.
**Why it happens:** The LLM simplifies the output format or uses Plotly's native `fig.to_json()` directly instead of wrapping it in the expected JSON structure.
**How to avoid:** Include the exact output code block in the system prompt as a mandatory template. The prompt should say: "Your code MUST end with exactly these lines: [template]. DO NOT modify this output pattern."
**Warning signs:** Chart code executes successfully in sandbox but `chart_specs` is empty (parser didn't find `"chart"` key).
**Confidence:** HIGH -- verified by reading the output parser in graph.py lines 467-468.

### Pitfall 5: System Prompt Too Long for Visualization Agent

**What goes wrong:** The system prompt includes execution_result data, analysis text, chart type heuristics, output contract, styling guidelines, and all rules. Combined with the LLM's internal context, this exceeds effective prompt length and the LLM loses focus on code generation.
**Why it happens:** Visualization requires more context than data analysis: the agent needs the data values, column names, the analysis interpretation, chart type rules, and styling requirements.
**How to avoid:** Structure the prompt efficiently: (1) Role and output contract first (most important), (2) Data next (what to chart), (3) Chart type rules, (4) Styling guidelines last (least critical). Keep total prompt under 2000 tokens excluding the data. Use `max_tokens: 4000` for the response (chart code is typically 20-40 lines).
**Warning signs:** LLM generates partial code, omits the output contract, or returns analysis text instead of code.
**Confidence:** MEDIUM -- prompt length is an empirical concern that will need tuning during implementation.

## Code Examples

### Example 1: Visualization Agent Node Function

```python
# Source: New file, following pattern from backend/app/agents/coding.py
"""Visualization Agent for generating Plotly chart code.

Receives execution results and user intent, generates Plotly Python code
that produces chart JSON via fig.to_json() to stdout.
"""

import logging

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

logger = logging.getLogger("spectra.visualization")

# Maximum characters of execution_result to include in prompt
_MAX_DATA_CHARS = 8000


async def visualization_agent_node(state: ChatAgentState) -> dict:
    """Generate Plotly Python code from execution results and user intent.

    Args:
        state: Current chat workflow state containing:
            - execution_result: JSON string of computed data from Coding Agent
            - analysis: Data Analysis Agent's interpretation text
            - user_query: Original user question (may contain chart hints)
            - chart_hint: Extracted chart type preference ('' if none)

    Returns:
        dict: State update with chart_code key
    """
    writer = get_stream_writer()
    writer({
        "type": "visualization_started",
        "message": "Generating chart...",
    })

    # Load per-agent config from prompts.yaml
    settings = get_settings()
    provider = get_agent_provider("visualization")
    model = get_agent_model("visualization")
    temperature = get_agent_temperature("visualization")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("visualization")

    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Load and format system prompt
    system_prompt_template = get_agent_prompt("visualization")

    # Truncate execution_result if too large for prompt
    execution_result = state.get("execution_result", "")
    if len(execution_result) > _MAX_DATA_CHARS:
        execution_result = execution_result[:_MAX_DATA_CHARS] + "\n... (truncated)"

    system_prompt = system_prompt_template.format(
        execution_result=execution_result,
        user_query=state.get("user_query", ""),
        chart_hint=state.get("chart_hint", ""),
        analysis=state.get("analysis", ""),
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
        logger.warning("Visualization Agent returned empty response")
        return {"chart_code": "", "chart_error": "Chart generation failed: empty LLM response"}

    # Extract code from response (reuse coding agent's extractor)
    chart_code = extract_code_block(content)

    return {"chart_code": chart_code}
```

### Example 2: prompts.yaml Configuration Entry

```yaml
# Source: Addition to backend/app/config/prompts.yaml
  visualization:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.0
    system_prompt: |
      You are a Visualization Agent for the Spectra analytics platform.
      Generate Plotly Python code that creates a chart from the given data.

      **User's Query:** {user_query}
      **User's Chart Preference:** {chart_hint}
      **Analysis Context:** {analysis}

      **Data to Visualize:**
      {execution_result}

      **Chart Type Selection Rules:**
      1. If chart_hint is specified (not empty), use that chart type.
      2. Date/time column + numeric column: LINE chart (sort by date first).
      3. One categorical + one numeric column:
         - 8 or fewer categories: PIE chart
         - More than 8 categories: horizontal BAR chart
      4. Two numeric columns: SCATTER plot.
      5. Single numeric column: HISTOGRAM.
      6. Categorical + numeric with natural ordering: vertical BAR chart.
      7. Distribution analysis: BOX plot.
      8. Fewer than 3 data points: Return NO CODE (set chart_code to empty).
      9. Default: BAR chart.

      **Code Requirements:**
      - Embed the data as a Python list of dicts or appropriate literal. DO NOT reference `df` or read any files.
      - Import only: plotly.express (as px), plotly.io (as pio), plotly.graph_objects (as go), json, pandas (as pd if needed for data manipulation).
      - Use template="plotly_white" for all charts.
      - Set transparent background: paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)".
      - Set reasonable dimensions: height=400, do NOT set width (responsive).
      - Set tight margins: margin=dict(l=40, r=40, t=50, b=40).
      - Add a descriptive title based on the user's query.
      - Add axis labels that match column names.
      - DO NOT set explicit trace colors (let Plotly defaults apply).
      - DO NOT use fig.write_image() or any image export.
      - DO NOT use custom JavaScript callbacks, updatemenus, or sliders.
      - DO NOT use fig.show().

      **Mandatory Output (MUST be the last lines of your code):**
      ```python
      chart_json = json.loads(pio.to_json(fig))
      print(json.dumps({{"chart": chart_json}}))
      ```

      Return ONLY Python code in a ```python code block. No explanations.

    max_tokens: 4000
```

### Example 3: Unit Test for Visualization Agent

```python
# Source: New file backend/tests/test_visualization_agent.py
"""Tests for Visualization Agent code generation."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.visualization import visualization_agent_node, _MAX_DATA_CHARS


class TestVisualizationAgentNode:
    """Test visualization_agent_node function."""

    @pytest.fixture
    def sample_state(self):
        """Create a sample ChatAgentState for testing."""
        return {
            "execution_result": '[{"region": "East", "sales": 50000}, {"region": "West", "sales": 35000}]',
            "analysis": "Sales are highest in the East region at $50K.",
            "user_query": "Show me a bar chart of sales by region",
            "chart_hint": "bar",
            "visualization_requested": True,
        }

    @pytest.mark.asyncio
    @patch("app.agents.visualization.get_stream_writer")
    @patch("app.agents.visualization.get_llm")
    @patch("app.agents.visualization.validate_llm_response")
    async def test_returns_chart_code(self, mock_validate, mock_get_llm, mock_writer, sample_state):
        """Should return dict with chart_code key."""
        mock_writer.return_value = MagicMock()
        mock_llm = AsyncMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.return_value = MagicMock(content="```python\nimport plotly\n```")
        mock_validate.return_value = "```python\nimport plotly\n```"

        result = await visualization_agent_node(sample_state)

        assert "chart_code" in result
        assert isinstance(result["chart_code"], str)

    @pytest.mark.asyncio
    @patch("app.agents.visualization.get_stream_writer")
    @patch("app.agents.visualization.get_llm")
    @patch("app.agents.visualization.validate_llm_response")
    async def test_truncates_large_execution_result(self, mock_validate, mock_get_llm, mock_writer, sample_state):
        """Should truncate execution_result exceeding _MAX_DATA_CHARS."""
        mock_writer.return_value = MagicMock()
        mock_llm = AsyncMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.return_value = MagicMock(content="```python\nprint('test')\n```")
        mock_validate.return_value = "```python\nprint('test')\n```"

        # Set execution_result larger than limit
        sample_state["execution_result"] = "x" * (_MAX_DATA_CHARS + 5000)

        result = await visualization_agent_node(sample_state)

        # Verify the LLM was called (agent didn't crash on large input)
        assert mock_llm.ainvoke.called
        assert "chart_code" in result

    @pytest.mark.asyncio
    @patch("app.agents.visualization.get_stream_writer")
    @patch("app.agents.visualization.get_llm")
    @patch("app.agents.visualization.validate_llm_response")
    async def test_handles_empty_llm_response(self, mock_validate, mock_get_llm, mock_writer, sample_state):
        """Should return chart_error when LLM returns empty response."""
        from app.agents.llm_factory import EmptyLLMResponseError

        mock_writer.return_value = MagicMock()
        mock_llm = AsyncMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.return_value = MagicMock(content="")
        mock_validate.side_effect = EmptyLLMResponseError("anthropic", "claude-sonnet-4-20250514", "visualization")

        result = await visualization_agent_node(sample_state)

        assert result["chart_code"] == ""
        assert "chart_error" in result
        assert result["chart_error"] != ""
```

### Example 4: Chart Type Heuristic Helper (Optional Enhancement)

```python
# Source: Could be added to backend/app/agents/visualization.py
import json

def build_data_shape_hints(execution_result: str) -> str:
    """Analyze execution_result and generate data shape hints for the prompt.

    Returns a string describing the data shape to help the LLM select
    the correct chart type.

    Args:
        execution_result: JSON string of execution results

    Returns:
        str: Human-readable data shape description
    """
    try:
        data = json.loads(execution_result)
    except (json.JSONDecodeError, TypeError):
        return "Data shape: unable to parse"

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        row_count = len(data)
        columns = list(data[0].keys())

        # Analyze column types from first row
        col_hints = []
        for col in columns:
            values = [row.get(col) for row in data if row.get(col) is not None]
            unique_count = len(set(str(v) for v in values))

            if all(isinstance(v, (int, float)) for v in values[:5]):
                col_type = "numeric"
            else:
                col_type = "categorical"

            col_hints.append(f"  - {col}: {col_type}, {unique_count} unique values")

        return (
            f"Data shape: {row_count} rows, {len(columns)} columns\n"
            f"Columns:\n" + "\n".join(col_hints)
        )

    elif isinstance(data, dict):
        return f"Data shape: single dict with {len(data)} keys: {list(data.keys())}"

    return f"Data shape: {type(data).__name__}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monolithic agent generates data + chart code | Separate Coding Agent (data) + Visualization Agent (charts) | Spectra v0.4 architecture decision | Clean separation of concerns. Chart failures don't break data pipeline. |
| LLM freely selects chart type | Heuristic guardrails in prompt constrain chart type selection | Academic research (2024-2025) showing 15-30% LLM chart type error rate | Reduces incorrect chart types. `chart_hint` from user overrides heuristics. |
| `fig.to_html()` for chart transport | `fig.to_json()` for JSON-over-the-wire | Spectra v0.4 architecture decision | 100x smaller payload, native React rendering, no iframe needed, theme-able. |
| Server-side image export via Kaleido | Client-side export via `Plotly.downloadImage()` | Kaleido v1.0 (2025) broke bundled Chrome | E2B sandbox lacks Chrome. Client-side is faster and costs nothing. |

**Deprecated/outdated:**
- **react-plotly.js wrapper:** Not updated in 3+ years, unverified React 19 compatibility. Spectra uses custom `ChartRenderer` component (Phase 23).
- **Kaleido for E2B image export:** Requires Chrome, broken in sandbox environment. Client-side only.
- **Custom JavaScript in Plotly charts:** Disallowed by project decision (XSS via prompt injection risk).

## Open Questions

### 1. Optimal Model for Visualization Agent

**What we know:** All current agents use `claude-sonnet-4-20250514`. Chart code generation is structurally simpler than data analysis code (shorter, more templated).

**What's unclear:** Whether a cheaper/faster model (e.g., `claude-haiku-3-5-20241022`) would produce acceptable chart code quality, reducing cost and latency per visualization query.

**Recommendation:** Start with `claude-sonnet-4-20250514` for consistency and quality. The `prompts.yaml` config makes model switching trivial for future optimization. This is a non-blocking decision -- can be tuned post-implementation.

### 2. Multi-Chart Support in Generated Code

**What we know:** Milestone requirements state "2-3 charts to show different perspectives." The current `chart_specs` state field is `str` (single JSON string). The output parser extracts a single `"chart"` key.

**What's unclear:** Whether Phase 21 should generate multi-chart code or single-chart only.

**Recommendation:** Phase 21 generates single-chart code only. The output contract is `{"chart": {...}}` (singular). Multi-chart support (`{"charts": [{...}, {...}]}`) is deferred to Phase 22/24 when graph integration provides the routing context for multi-chart decisions. This keeps Phase 21 simple and testable.

### 3. Data Truncation Strategy for Large Results

**What we know:** Some queries return thousands of rows in `execution_result`. Embedding all rows as Python literals would exceed prompt token limits and produce huge chart code.

**What's unclear:** The optimal truncation threshold. Too aggressive truncation loses chart data; too lenient exceeds token limits.

**Recommendation:** Truncate `execution_result` to 8000 characters in the prompt (approximately 200 data rows for typical column widths). The prompt should instruct the LLM to aggregate if the data appears truncated. This is tunable via the `_MAX_DATA_CHARS` constant.

## Sources

### Primary (HIGH confidence)

- **Codebase analysis (direct inspection):**
  - `backend/app/agents/coding.py` -- Agent node pattern (lines 62-210), `extract_code_block()` (lines 26-59)
  - `backend/app/agents/config.py` -- Config loader pattern (lines 82-256)
  - `backend/app/agents/llm_factory.py` -- LLM factory pattern (lines 152-249), `validate_llm_response()` (lines 59-85)
  - `backend/app/agents/state.py` -- `ChatAgentState` with viz fields (lines 53-172)
  - `backend/app/agents/graph.py` -- Output parser with chart extraction (lines 453-508)
  - `backend/app/config/prompts.yaml` -- Agent YAML config pattern (all entries)
  - `backend/app/config/allowlist.yaml` -- Plotly in allowlist (line 12)
  - `backend/app/services/agent_service.py` -- Initial state with viz field defaults (lines 264-268, 521-525)
- `.planning/research/ARCHITECTURE.md` -- Visualization Agent design, data flow, graph topology
- `.planning/research/PITFALLS-v0.4-visualization.md` -- Pitfall 3 (wrong chart type), Pitfall 10 (prompt conflict)
- `.planning/phases/20-infrastructure-pipeline/20-VERIFICATION.md` -- Phase 20 complete (8/8 truths verified)

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` -- Technology stack decisions for v0.4
- [Plotly Python API: plotly.io.to_json](https://plotly.com/python-api-reference/generated/plotly.io.to_json.html) -- JSON serialization API
- [Plotly Express API](https://plotly.com/python-api-reference/plotly.express.html) -- px.bar, px.line, px.scatter, px.pie, px.histogram, px.box
- Academic research on LLM chart type error rates: arxiv 2412.02764v1, 2403.06158v1

### Tertiary (LOW confidence)

- Optimal model selection for chart code generation -- No published benchmarks comparing Claude models specifically for Plotly code. Recommendation is based on general code generation quality observations.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries are already installed and used by existing agents. No new dependencies.
- Architecture: HIGH -- Follows identical pattern to existing Coding Agent. Pattern verified by reading 6 agent source files.
- Pitfalls: HIGH -- Documented in pre-existing PITFALLS-v0.4-visualization.md with academic sources. Chart type heuristics are established practice.
- System prompt design: MEDIUM -- Prompt engineering is empirical. The heuristic rules are grounded in research, but optimal phrasing requires testing.
- Data truncation: MEDIUM -- The 8000-character threshold is an educated guess. Will need empirical tuning.

**Research date:** 2026-02-13
**Valid until:** 60 days (stable domain -- agent patterns are established, Plotly API is mature)
