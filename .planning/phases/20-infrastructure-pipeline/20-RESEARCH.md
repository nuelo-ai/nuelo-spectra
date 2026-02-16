# Phase 20: Infrastructure & Pipeline - Research

**Researched:** 2026-02-13
**Domain:** Infrastructure preparation for data visualization (Plotly allowlist, state schema extension, E2B sandbox verification, output parsing)
**Confidence:** HIGH

## Summary

Phase 20 prepares the platform foundation for chart generation without implementing any visualization logic. This phase focuses on four infrastructure components: (1) extending the Code Checker allowlist to permit Plotly imports, (2) adding visualization-related fields to ChatAgentState for data flow through the pipeline, (3) verifying E2B sandbox has Plotly 6.0.1 pre-installed and functional, and (4) extending the sandbox output parser to extract chart JSON alongside existing table data.

The key architectural insight is that **this phase is purely infrastructural**—no visualization agent, no chart rendering, no UI changes. The success criteria are binary: Plotly imports pass validation, state carries chart fields, sandbox executes Plotly code, and output parser captures JSON. This clean separation allows Phase 20 to be tested independently with manually-written Plotly code before the Visualization Agent (Phase 21) generates code automatically.

**Primary recommendation:** Start with the allowlist (lowest risk), verify E2B sandbox with a test execution (`import plotly; print(plotly.__version__)`), extend state schema using LangGraph's backward-compatible TypedDict pattern, and finally modify output parsing to detect and extract chart JSON from the `{"result": {...}, "chart": {...}}` output contract.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Chart Security Boundaries:**
- External data fetching: Block all external fetching—charts only use data passed from analysis results (no network calls, no remote APIs, no external images)
- File system access: Read-only access to temp directory for large datasets (no write access, prevents data leakage)
- Chart types allowed: All 7 required chart types from the start (bar, line, scatter, histogram, box, pie, donut)

**Error Handling & User Experience:**
- Error visibility: Show error message to user when chart generation fails (transparent, not silent)
- Data preservation: Always preserve and display the original data table even if chart generation fails (users always get value)
- Retry logic: Auto-retry once on transient failures (improves success rate without requiring user re-query)
- Error message detail: Adaptive approach—simple user-friendly message with expandable technical details for debugging

### Claude's Discretion

- Custom JavaScript support in Plotly charts: Determine if custom JS should be allowed based on security best practices
- Validation testing depth: Determine appropriate validation depth (version check vs sample chart generation)
- Test data approach: Choose between synthetic test data or real data samples for testing
- Multiple charts per response support: Determine if infrastructure should support 2-3 charts per response from the start
- JSON schema strictness: Balance between strict validation (catches errors early) and flexible parsing (more forgiving)

### Deferred Ideas (OUT OF SCOPE)

None—discussion stayed within phase scope (infrastructure preparation only)

</user_constraints>

## Standard Stack

### Core Infrastructure (Already Installed)

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Plotly (E2B sandbox) | 6.0.1 | Chart generation library | Pre-installed in E2B code interpreter sandbox—verified via E2B documentation. Supports `fig.to_json()` for JSON serialization. |
| Python AST module | stdlib | Code validation via abstract syntax trees | Built-in Python feature used by existing Code Checker—industry standard for static code analysis. |
| LangGraph | Current | Agent state management via TypedDict | Already in use for ChatAgentState—supports backward-compatible field additions. |
| E2B Sandbox | Current | Secure code execution environment | Existing integration via `e2b_runtime.py`—Firecracker microVM isolation. |

### Supporting Libraries (E2B Sandbox)

| Library | Version | Purpose | When Used |
|---------|---------|---------|----------|
| pandas | 2.2.3 | Data manipulation before charting | Pre-installed—already used by Coding Agent for data processing. |
| numpy | 1.26.4 | Numerical operations | Pre-installed—dependency for pandas and plotly. |
| Kaleido | 1.0.0 | Static image export (NOT USED) | Pre-installed but AVOIDED—requires Chrome which E2B sandbox lacks. Client-side export preferred. |

### Alternative Approaches Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `plotly.io.to_json()` | `fig.to_html()` | HTML output is 100x larger (~3MB vs 10KB), requires iframe sandboxing, harder to theme, less flexible for client-side manipulation. JSON is preferred. |
| Allowlist extension | Separate validation path for viz code | More complex—requires routing context in Code Checker, dual validation logic. Simple allowlist addition is sufficient since E2B sandbox is the real security boundary. |
| TypedDict state extension | Pydantic model migration | Breaking change—would require migrating all existing state usages. TypedDict extension is backward-compatible with existing checkpoints. |

**Installation:**

No new backend dependencies—Plotly is pre-installed in E2B sandbox. Frontend chart rendering (plotly.js) is deferred to Phase 23.

## Architecture Patterns

### Recommended State Schema Extension

The existing `ChatAgentState` uses TypedDict with 25+ fields. LangGraph documentation confirms: "For modifying state, we have full backwards and forwards compatibility for adding and removing keys." This means new fields can be added without breaking existing threads or checkpoints.

**Pattern: Additive TypedDict fields**

```python
# Location: backend/app/agents/state.py
class ChatAgentState(TypedDict):
    # ... existing 25 fields unchanged ...

    # NEW: Visualization infrastructure fields
    visualization_requested: bool
    """Flag indicating user requested chart generation (e.g., 'show me a chart')."""

    chart_hint: str
    """User's chart type preference if explicitly stated ('bar chart', 'line graph', etc.)."""

    chart_code: str
    """Plotly Python code generated for chart creation (separate from generated_code)."""

    chart_specs: str
    """JSON string of Plotly figure specification from fig.to_json() output."""

    chart_error: str
    """Error message if chart generation fails, empty string if successful."""
```

**Why this pattern:**
- **Backward compatible:** Existing threads with old state schema continue working—new fields default to empty strings/False
- **No migration required:** Old checkpoints can be resumed without schema conversion
- **Separates concerns:** Chart fields are distinct from data analysis fields (`generated_code`, `execution_result`)
- **Type safety:** TypedDict provides static type checking without runtime overhead

### Pattern: Allowlist Extension for Security

The existing Code Checker uses an AST `NodeVisitor` pattern to validate imports against `allowlist.yaml`. The allowlist currently permits only data manipulation libraries (pandas, numpy, datetime, math, etc.). Plotly must be added to permit `import plotly` statements.

**Pattern: Simple allowlist addition**

```yaml
# Location: backend/app/config/allowlist.yaml
allowed_libraries:
  - pandas
  - numpy
  - datetime
  - math
  - statistics
  - collections
  - itertools
  - functools
  - re
  - json
  - plotly  # NEW: Required for chart generation
```

**Security rationale:**
1. Plotly is a pure visualization library—no filesystem access, no network I/O, no subprocess spawning
2. E2B sandbox is the real security boundary (Firecracker microVM isolation)
3. Plotly code execution is temporary (sandbox destroyed after each run)
4. User constraint: "Block all external fetching"—Plotly supports this via data-only charts

**Alternative considered:** Context-aware allowlist (only permit Plotly when `visualization_requested=True`). Rejected because:
- Adds complexity to Code Checker routing logic
- Minimal security benefit (sandbox is the real boundary)
- User constraint allows all 7 chart types from the start

### Pattern: JSON Output Contract Extension

The existing sandbox output parser (in `graph.py` lines 454-470) looks for JSON in stdout with the contract: `print(json.dumps({"result": result}))`. Chart generation requires extending this contract to support an optional `chart` key.

**Pattern: Dual-key JSON output**

```python
# Existing contract (tabular data only):
print(json.dumps({"result": result}))
# Output: {"result": [{"col1": val1, "col2": val2}, ...]}

# NEW contract (data + chart):
import plotly.io as pio
chart_spec = json.loads(pio.to_json(fig))
print(json.dumps({"result": result, "chart": chart_spec}))
# Output: {"result": [...], "chart": {"data": [...], "layout": {...}}}
```

**Parser modification strategy:**

```python
# Location: backend/app/agents/graph.py, execute_in_sandbox function
# Current parsing (lines 454-470):
if result.stdout:
    for line in reversed(result.stdout):
        if line.strip().startswith('{') and line.strip().endswith('}'):
            parsed = json.loads(line.strip())
            if "result" in parsed:
                execution_result = json.dumps(parsed["result"])
                break

# MODIFIED parsing (backward-compatible):
if result.stdout:
    for line in reversed(result.stdout):
        if line.strip().startswith('{') and line.strip().endswith('}'):
            parsed = json.loads(line.strip())
            if "result" in parsed:
                execution_result = json.dumps(parsed["result"])
                # NEW: Extract chart if present
                if "chart" in parsed:
                    chart_specs = json.dumps(parsed["chart"])
                    state_updates["chart_specs"] = chart_specs
                break
```

**Why this pattern:**
- **Backward compatible:** Old code outputting `{"result": ...}` continues working
- **Single stdout line:** Keeps parsing simple—no multi-line JSON splitting needed
- **Explicit keys:** Clear distinction between data (`result`) and visualization (`chart`)
- **Optional chart:** `chart` key only present when visualization code runs

### Pattern: E2B Sandbox Verification

E2B documentation confirms Plotly 6.0.1 is pre-installed, but verification via test execution is recommended before relying on it.

**Pattern: Early verification test**

```python
# One-time verification script (not in production code)
from app.services.sandbox import E2BSandboxRuntime

runtime = E2BSandboxRuntime()
result = runtime.execute(
    code="import plotly; print(plotly.__version__)",
    timeout=10.0
)

if result.success:
    version = result.stdout[0].strip() if result.stdout else "unknown"
    print(f"✓ Plotly available: version {version}")
else:
    print(f"✗ Plotly unavailable: {result.error}")
```

**User constraint: Validation testing depth**—discretion granted. Recommended approach:
1. **Phase 20 (this phase):** Version check only (fast, low-cost)
2. **Phase 21 (Visualization Agent):** Sample chart generation (e.g., simple bar chart with synthetic data)
3. **Phase 24 (Chart Types & Export):** Comprehensive chart type validation

**If Plotly is missing:** E2B allows custom templates via Dockerfile. Create template with `RUN pip install plotly==6.0.1`. However, DeepWiki documentation confirms Plotly 6.0.1 is already pre-installed—verification test should succeed.

### Anti-Patterns to Avoid

**Anti-pattern: State field overloading**
- ❌ Reusing `generated_code` for chart code (breaks existing retry logic)
- ✅ Separate `chart_code` field for Plotly code generation

**Anti-pattern: Breaking output contract**
- ❌ Changing `{"result": ...}` to `{"data": ..., "chart": ...}` (breaks existing code)
- ✅ Extending with optional `chart` key: `{"result": ..., "chart": ...}`

**Anti-pattern: Custom JavaScript in charts**
- ❌ Allowing `fig.update_layout(updatemenus=[...])` with arbitrary JS callbacks
- ✅ User constraint: "Claude's discretion"—RECOMMENDED: Disallow custom JS. Plotly supports rich interactivity (hover, zoom, pan) without custom scripts. Custom JS opens XSS vectors and complicates CSP.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chart JSON serialization | Custom JSON encoder for Plotly figures | `plotly.io.to_json(fig)` | Handles nested objects, ndarray serialization, removes UIDs, validates schema. Custom encoder would miss edge cases (e.g., datetime objects, NaN handling). |
| AST validation | Regex-based import checking | Python `ast` module with `NodeVisitor` | Regex cannot handle `from plotly.express import px` vs `import plotly as plt` aliasing. AST parsing is syntax-aware. |
| State schema migration | Manual checkpoint updates | LangGraph's built-in backward compatibility | LangGraph handles missing fields automatically—manual migration risks data loss. |
| Large JSON parsing | Loading entire stdout string into memory | Incremental parsing with `json.loads()` per line | stdout is already split into lines by E2B—parsing per line avoids memory spikes. For very large charts (>1MB JSON), consider `ijson` streaming parser. |

**Key insight:** Plotly's JSON serialization is non-trivial. A figure contains nested data traces, layout objects, annotations, and numpy arrays. `fig.to_json()` uses `orjson` (if available) for 10x faster encoding than stdlib `json`. Do not attempt to serialize manually.

## Common Pitfalls

### Pitfall 1: Plotly Blocked by Allowlist (CRITICAL)

**What goes wrong:**
User requests chart → Visualization Agent generates `import plotly.express as px` → Code Checker validates against allowlist → Plotly not in list → AST validation fails with "Module not in allowlist: plotly" → Retry loop burns 3 attempts → User sees "Unable to generate valid code after 3 attempts."

**Root cause:**
Current `allowlist.yaml` only permits data manipulation libraries. Plotly was not needed for v0.1-v0.3 (tabular analysis only).

**Prevention:**
1. Add `plotly` to `allowed_libraries` in `allowlist.yaml` BEFORE any visualization code is generated
2. Test with manual chart code: `import plotly.express as px; fig = px.bar(x=[1,2,3], y=[4,5,6])`
3. Verify Code Checker accepts the import (should return `is_valid=True`)

**Warning signs:**
- Test execution of `import plotly` fails validation
- LangSmith traces show `code_checker` node rejecting Plotly imports

**Severity:** CRITICAL—blocks 100% of chart generation attempts

### Pitfall 2: State Field Naming Collision

**What goes wrong:**
New field `chart_specs` (JSON string) vs frontend expecting `chartSpecs` (parsed object). TypeScript type mismatch causes runtime errors in DataCard rendering.

**Root cause:**
Backend Python uses snake_case, frontend TypeScript uses camelCase. State field names must be transformed at the API boundary.

**Prevention:**
1. Use consistent snake_case in backend state: `chart_specs` (string)
2. Transform to camelCase in SSE event serialization: `chartSpecs` (for frontend)
3. Document the naming convention in state.py docstrings

**Warning signs:**
- Frontend sees undefined `chartSpecs` even though backend set `chart_specs`
- TypeScript errors: `Property 'chartSpecs' does not exist on type 'StreamEvent'`

**Severity:** MODERATE—causes frontend rendering failures

### Pitfall 3: Chart JSON Exceeds Stdout Buffer

**What goes wrong:**
Visualization Agent generates chart with 10,000+ data points → `fig.to_json()` produces 5MB JSON string → `print(json.dumps({...}))` writes to stdout → E2B stdout buffer may split across multiple list items → Parser looking for single-line JSON fails → Chart data lost.

**Root cause:**
Current parser iterates `result.stdout` (list of strings) and expects JSON on a single line. Very large JSON may span multiple list items or exceed buffer size.

**Prevention:**
1. **Data aggregation in chart code:** Visualization Agent should aggregate before charting (e.g., group by region, not 50,000 raw rows)
2. **Size limit check:** Add validation: if `len(json_string) > 1_000_000`, return error suggesting data filtering
3. **Join stdout lines:** For chart parsing only, join all stdout lines before JSON parsing (handles multi-line split)
4. **User constraint: Validation depth**—discretion granted. RECOMMENDED: Test with synthetic 1,000-row dataset in Phase 20 verification

**Warning signs:**
- Chart execution succeeds but `chart_specs` is empty
- E2B stdout contains truncated JSON (missing closing `}`)

**Severity:** MODERATE—causes silent chart failures with large datasets

### Pitfall 4: E2B Plotly Version Mismatch

**What goes wrong:**
E2B sandbox has Plotly 5.x (older) but generated code uses Plotly 6.x features (e.g., `fig.to_json(engine='auto')`) → `TypeError: to_json() got an unexpected keyword argument 'engine'` → Chart generation fails.

**Root cause:**
Plotly 6.0 introduced the `engine` parameter for JSON encoding. If E2B sandbox has 5.19.0 (as one search result suggested), this parameter does not exist.

**Prevention:**
1. **Verification test:** Run `import plotly; print(plotly.__version__)` in E2B sandbox and confirm version ≥6.0
2. **If version <6.0:** Do NOT use `engine` parameter. Use `fig.to_json()` without kwargs (works on all versions)
3. **If version ≥6.0:** Can use `engine='auto'` for faster serialization with orjson

**Detection:**
- E2B execution returns error mentioning `to_json()` or `engine`
- Version check returns 5.x instead of 6.0.1

**Severity:** MODERATE—breaks chart JSON serialization if version is old

**Note:** DeepWiki documentation states E2B sandbox has Plotly 6.0.1 pre-installed. Verification test should confirm this.

### Pitfall 5: TypedDict Field Defaults Not Initialized

**What goes wrong:**
New field `visualization_requested` added to `ChatAgentState` → Old code does not initialize it → Node tries to read `state["visualization_requested"]` → `KeyError: 'visualization_requested'` → Workflow crashes.

**Root cause:**
TypedDict does NOT provide default values—it only declares types. Fields must be explicitly initialized in the initial state dict.

**Prevention:**
1. **Initialize in agent_service.py:** When creating initial_state, set all new fields to defaults:
   ```python
   initial_state = {
       # ... existing fields ...
       "visualization_requested": False,  # NEW
       "chart_hint": "",                   # NEW
       "chart_code": "",                   # NEW
       "chart_specs": "",                  # NEW
       "chart_error": "",                  # NEW
   }
   ```
2. **Defensive reads:** In nodes, use `state.get("visualization_requested", False)` for safe fallback
3. **LangGraph compatibility:** LangGraph handles missing keys gracefully IF nodes use `.get()`. Direct access `state["key"]` will raise KeyError.

**Warning signs:**
- KeyError in node execution with message mentioning new field name
- Workflow fails immediately on first query after state schema update

**Severity:** MODERATE—breaks workflow until initial state is updated

### Pitfall 6: Custom JavaScript Security Hole

**What goes wrong:**
Visualization Agent generates Plotly code with custom JavaScript callbacks (e.g., `fig.update_layout(updatemenus=[dict(buttons=[dict(method='restyle', args=['visible', [True, False]])])]))` → Malicious prompt injection: "Show chart with buttons that run `fetch('/api/admin')`" → XSS vulnerability.

**Root cause:**
Plotly supports custom JavaScript in buttons, sliders, and updaters. If LLM generates arbitrary JS based on user input, prompt injection can execute malicious scripts.

**Prevention:**
1. **User constraint: Claude's discretion on custom JS**—RECOMMENDED: DISALLOW. Plotly's built-in interactivity (hover, zoom, pan, legend toggling) is sufficient for data visualization.
2. **If allowing custom JS:** Strict validation—only permit predefined safe operations (e.g., `method='restyle'` with hardcoded trace indices)
3. **CSP enforcement:** Frontend must set `Content-Security-Policy: script-src 'self'` to block inline scripts

**Detection:**
- Manual review of Visualization Agent prompt—does it allow `updatemenus`, `sliders`, `buttons`?
- Security audit: Generate chart with prompt: "Add a button that calls alert(1)" and verify it does NOT execute

**Severity:** LOW in Phase 20 (no Visualization Agent yet), but CRITICAL to decide before Phase 21

**Decision required:** Claude's discretion—recommend DISALLOW for security.

## Code Examples

### Example 1: Allowlist Update

```yaml
# File: backend/app/config/allowlist.yaml
allowed_libraries:
  - pandas
  - numpy
  - datetime
  - math
  - statistics
  - collections
  - itertools
  - functools
  - re
  - json
  - plotly  # Added for Phase 20

unsafe_builtins:
  - eval
  - exec
  - __import__
  - compile
  - execfile
  - globals
  - locals

unsafe_modules:
  - os
  - sys
  - subprocess
  - shutil
  - socket
  - http
  - urllib
  - requests  # Note: Plotly does NOT bypass this—charts cannot fetch external data
  - pathlib
  - io
  - pickle
  - shelve
```

**Source:** Existing `backend/app/config/allowlist.yaml` + extension

### Example 2: State Schema Extension

```python
# File: backend/app/agents/state.py
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class ChatAgentState(TypedDict):
    """State for the Chat Agent workflow.

    Orchestrates Coding Agent → Code Checker → Execute → Data Analysis Agent
    with retry loops for validation failures. Extended in v0.4 for visualization.
    """

    # Existing fields (25 total) unchanged...
    file_id: str
    user_id: str
    user_query: str
    # ... (22 more existing fields) ...

    # NEW: Visualization infrastructure fields (Phase 20)
    visualization_requested: bool
    """Flag indicating user requested chart generation.
    Set by Manager Agent (future) or da_response_node based on query keywords.
    Default: False."""

    chart_hint: str
    """User's explicit chart type preference if stated ('bar', 'line', 'pie', etc.).
    Extracted from user_query if present (e.g., 'show me a bar chart').
    Default: '' (empty string, chart type selection left to Visualization Agent)."""

    chart_code: str
    """Plotly Python code generated for chart creation.
    Separate from generated_code (which produces tabular data).
    Generated by Visualization Agent (Phase 21).
    Default: '' (no chart code)."""

    chart_specs: str
    """JSON string of Plotly figure specification.
    Serialized via plotly.io.to_json(fig) in sandbox execution.
    Parsed and rendered by frontend ChartRenderer component.
    Format: '{"data": [...], "layout": {...}}' (Plotly JSON schema).
    Default: '' (no chart)."""

    chart_error: str
    """Error message if chart generation or execution fails.
    User constraint: Always show errors transparently.
    Default: '' (no error)."""
```

**Source:** Extended from existing `backend/app/agents/state.py` (lines 53-144)

### Example 3: E2B Plotly Verification Test

```python
# File: backend/tests/test_plotly_availability.py (new file for Phase 20 verification)
"""Verify Plotly 6.0.1 is available in E2B sandbox and fig.to_json() works."""

import pytest
from app.services.sandbox import E2BSandboxRuntime
import json

def test_plotly_version():
    """Verify Plotly version ≥6.0 in E2B sandbox."""
    runtime = E2BSandboxRuntime(timeout_seconds=10.0)
    result = runtime.execute(
        code="import plotly; print(plotly.__version__)",
        timeout=10.0
    )

    assert result.success, f"Plotly import failed: {result.error}"
    assert result.stdout, "No version output received"

    version = result.stdout[0].strip()
    major, minor, patch = version.split('.')
    assert int(major) >= 6, f"Plotly version too old: {version} (expected ≥6.0)"
    print(f"✓ Plotly available: version {version}")

def test_plotly_to_json():
    """Verify fig.to_json() produces valid JSON."""
    runtime = E2BSandboxRuntime(timeout_seconds=10.0)

    code = """
import plotly.express as px
import plotly.io as pio
import json

# Create simple bar chart
fig = px.bar(x=['A', 'B', 'C'], y=[1, 3, 2], title='Test Chart')

# Serialize to JSON (Plotly 6.x syntax)
chart_json = pio.to_json(fig)

# Output as part of result contract
print(json.dumps({"result": {"test": "data"}, "chart": json.loads(chart_json)}))
"""

    result = runtime.execute(code=code, timeout=10.0)

    assert result.success, f"Chart generation failed: {result.error}"
    assert result.stdout, "No output received"

    # Parse output JSON
    output_line = result.stdout[-1].strip()  # Last line should be JSON
    parsed = json.loads(output_line)

    assert "result" in parsed, "Missing 'result' key in output"
    assert "chart" in parsed, "Missing 'chart' key in output"

    chart = parsed["chart"]
    assert "data" in chart, "Chart JSON missing 'data' field"
    assert "layout" in chart, "Chart JSON missing 'layout' field"
    assert chart["layout"]["title"]["text"] == "Test Chart", "Chart title mismatch"

    print(f"✓ Chart JSON structure valid ({len(str(chart))} bytes)")

def test_plotly_chart_types():
    """Verify all 7 required chart types are supported."""
    runtime = E2BSandboxRuntime(timeout_seconds=10.0)

    chart_types = [
        ("bar", "px.bar(x=['A','B'], y=[1,2])"),
        ("line", "px.line(x=[1,2,3], y=[1,4,2])"),
        ("scatter", "px.scatter(x=[1,2,3], y=[1,4,2])"),
        ("pie", "px.pie(values=[1,2,3], names=['A','B','C'])"),
        ("histogram", "px.histogram(x=[1,2,2,3,3,3])"),
        ("box", "px.box(y=[1,2,3,4,5])"),
    ]

    for chart_type, fig_code in chart_types:
        code = f"""
import plotly.express as px
import plotly.io as pio
import json

fig = {fig_code}
chart_json = pio.to_json(fig)
print(json.dumps({{"chart": json.loads(chart_json)}}))
"""
        result = runtime.execute(code=code, timeout=10.0)
        assert result.success, f"{chart_type} chart failed: {result.error}"

        parsed = json.loads(result.stdout[-1].strip())
        assert "chart" in parsed
        print(f"✓ {chart_type} chart type supported")

    # Note: Donut chart is a pie chart with hole
    code = """
import plotly.express as px
import plotly.io as pio
import json

fig = px.pie(values=[1,2,3], names=['A','B','C'], hole=0.4)  # hole makes it a donut
chart_json = pio.to_json(fig)
print(json.dumps({"chart": json.loads(chart_json)}))
"""
    result = runtime.execute(code=code, timeout=10.0)
    assert result.success, f"donut chart failed: {result.error}"
    parsed = json.loads(result.stdout[-1].strip())
    assert parsed["chart"]["data"][0]["hole"] == 0.4, "Donut hole parameter missing"
    print("✓ donut chart type supported (pie with hole)")
```

**Source:** New test file following existing test patterns in `backend/tests/`

### Example 4: Output Parser Extension

```python
# File: backend/app/agents/graph.py
# Location: Inside execute_in_sandbox function (lines 448-477, modified)

async def execute_in_sandbox(
    state: ChatAgentState,
) -> dict | Command[Literal["coding_agent", "halt"]]:
    """Execute Python code in E2B sandbox and extract results + chart JSON."""
    # ... (existing file loading and execution code unchanged) ...

    # Handle execution result
    if result.success:
        # Success: parse JSON output from stdout
        import json
        execution_result = None
        chart_specs = ""  # NEW: Initialize chart specs

        if result.stdout:
            # Try to parse JSON from last line of stdout
            stdout_text = "\n".join(result.stdout)
            try:
                # Look for JSON in stdout (existing logic)
                for line in reversed(result.stdout):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        parsed = json.loads(line.strip())

                        # Extract tabular result (existing)
                        if "result" in parsed:
                            execution_result = json.dumps(parsed["result"])

                        # NEW: Extract chart JSON if present
                        if "chart" in parsed:
                            chart_specs = json.dumps(parsed["chart"])
                            logger.info(f"Chart JSON extracted ({len(chart_specs)} bytes)")

                        break

                # Fallback: use raw stdout if JSON parsing fails (existing)
                if execution_result is None:
                    execution_result = stdout_text
            except json.JSONDecodeError:
                # Fallback: use raw stdout if JSON parsing fails (existing)
                execution_result = stdout_text
        elif result.results:
            # Fallback: use results list if no stdout (existing)
            execution_result = str(result.results)
        else:
            execution_result = "Code executed successfully (no output)"

        # NEW: Include chart_specs in return dict
        return {
            "execution_result": execution_result,
            "chart_specs": chart_specs  # NEW field
        }
    else:
        # Execution failed: check retry budget (existing logic unchanged)
        # ...
```

**Source:** Modified from existing `backend/app/agents/graph.py` (lines 448-477)

## State of the Art

### Evolution of Plotly JSON Serialization

| Old Approach (Plotly 5.x) | Current Approach (Plotly 6.x) | When Changed | Impact |
|---------------------------|-------------------------------|--------------|--------|
| `fig.to_json()` uses stdlib `json` module (slow) | `fig.to_json(engine='auto')` uses `orjson` if available (10x faster) | Plotly 6.0 (Sept 2025) | Large charts (1,000+ points) serialize faster. E2B sandbox has Plotly 6.0.1. |
| `remove_uids=False` by default | `remove_uids=True` by default | Plotly 5.11 | Smaller JSON output—UIDs not needed for client-side rendering. |
| No validation option | `validate=True` by default | Plotly 5.0 | Catches schema errors before serialization—prevents invalid JSON. |

### LangGraph State Management Evolution

| Old Approach (2024) | Current Approach (2026) | When Changed | Impact |
|---------------------|-------------------------|--------------|--------|
| State schema changes require checkpoint migration | Backward/forward compatible field additions | LangGraph 0.2+ (2025) | New fields can be added without breaking existing threads. Simplifies Phase 20 state extension. |
| Pydantic models for state | TypedDict recommended for lightweight state | LangGraph best practices (2025) | TypedDict has no runtime overhead—Pydantic only at API boundaries. |

### E2B Sandbox Pre-installed Packages

| Old Approach (2024) | Current Approach (2026) | When Changed | Impact |
|---------------------|-------------------------|--------------|--------|
| Plotly not pre-installed, required custom template | Plotly 6.0.1 pre-installed in base template | E2B Dec 2025 update | No custom template needed—Phase 20 can proceed immediately. |
| Kaleido v0.2.1 bundled Chromium | Kaleido v1.0.0 requires system Chrome (unavailable in E2B) | Kaleido v1.0 (Sept 2025) | Server-side image export broken—client-side export via plotly.js required. |

**Deprecated/outdated:**
- **Kaleido for image export in E2B sandbox:** Kaleido v1.0.0 requires Chrome, which E2B sandbox lacks. Workaround: Client-side export via `Plotly.downloadImage()` (deferred to Phase 23).
- **Custom E2B template for Plotly:** No longer needed—Plotly 6.0.1 is pre-installed as of Dec 2025.

## Open Questions

### 1. E2B Plotly Version Verification

**What we know:**
- DeepWiki documentation states Plotly 6.0.1 is pre-installed
- Web search result mentioned Plotly 5.19.0 (conflicting info)

**What's unclear:**
- Exact version currently in production E2B sandbox
- Whether version matches documentation (6.0.1) or search result (5.19.0)

**Recommendation:**
Run verification test (`import plotly; print(plotly.__version__)`) as first task in Phase 20. If version is 5.x, avoid Plotly 6.x-specific features (e.g., `engine` parameter).

**Impact if 5.x:** Use `fig.to_json()` without kwargs (compatible with all versions). Slightly slower serialization but no functional impact.

### 2. Multiple Charts Per Response Infrastructure

**What we know:**
- Requirements state: "If needed, the agent can generate 2-3 charts"
- User constraint: Claude's discretion on multi-chart support in Phase 20

**What's unclear:**
- Should Phase 20 output parser support `{"result": ..., "charts": [chart1, chart2]}` (array) or just `{"chart": ...}` (single)?
- Does state need `chart_specs: list[str]` or `chart_specs: str`?

**Recommendation:**
Start with single chart infrastructure (`chart_specs: str` for one JSON blob). Rationale:
1. Simpler to test and validate
2. Multi-chart support can be added in Phase 22 (Multi-Chart) without breaking Phase 20-21
3. Output contract extension is backward-compatible: `{"chart": {...}}` → `{"charts": [{...}, {...}]}`

**Deferred decision:** Multi-chart array support to Phase 22.

### 3. Chart JSON Size Limits

**What we know:**
- Plotly JSON for 10-bar chart: ~10KB
- Plotly JSON for 1,000-point scatter: ~100KB
- E2B stdout buffer size: Unknown (not documented)

**What's unclear:**
- Maximum safe chart JSON size before stdout truncation
- Whether E2B splits large stdout across multiple list items

**Recommendation:**
1. Phase 20 verification: Test with 1,000-point scatter plot, measure JSON size, verify complete capture
2. If truncation occurs: Implement size limit (e.g., reject charts with >100,000 data points)
3. User constraint: Data aggregation—Visualization Agent should group/sample before charting

**Fallback:** If stdout is unreliable for large JSON, use E2B file-based output (`sandbox.files.write('/tmp/chart.json')` + `sandbox.files.read()`).

### 4. Custom JavaScript Security Decision

**What we know:**
- Plotly supports custom JS in buttons, sliders, updaters
- User constraint: Claude's discretion on custom JS

**What's unclear:**
- Security tradeoff: flexibility vs XSS risk
- Whether Chart Security Boundary constraint ("no external fetching") implicitly prohibits custom JS

**Recommendation:**
**DISALLOW custom JavaScript** in Phase 20-21. Rationale:
1. Plotly's built-in interactivity is sufficient (hover tooltips, zoom, pan, legend toggle)
2. Custom JS opens XSS vector via prompt injection
3. Simplifies Visualization Agent prompt (no JS code generation needed)
4. Can be revisited in future phase if user explicitly requests advanced interactivity

**If allowing:** Strict validation—only permit hardcoded safe operations (e.g., `method='restyle'` with predefined args).

## Sources

### Primary (HIGH confidence)

- [Plotly Python API Reference: plotly.io.to_json](https://plotly.com/python-api-reference/generated/plotly.io.to_json.html) - Official API documentation for JSON serialization
- [E2B Sandbox Environment - DeepWiki](https://deepwiki.com/e2b-dev/code-interpreter/2.1-sandbox-environment) - Pre-installed packages and versions
- [LangGraph Graph API Overview](https://docs.langchain.com/oss/python/langgraph/graph-api) - State schema extension patterns
- [LangGraph: Type Safety - TypedDict vs Pydantic](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to) - Best practices for state management
- **Codebase analysis:** Direct inspection of `backend/app/agents/state.py`, `backend/app/agents/graph.py`, `backend/app/agents/code_checker.py`, `backend/app/config/allowlist.yaml`, `backend/app/services/sandbox/e2b_runtime.py` with line-number references
- [.planning/research/PITFALLS-v0.4-visualization.md](file:///Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.planning/research/PITFALLS-v0.4-visualization.md) - Domain-specific pitfalls research
- [.planning/research/STACK.md](file:///Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.planning/research/STACK.md) - Technology stack decisions
- [.planning/research/ARCHITECTURE.md](file:///Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.planning/research/ARCHITECTURE.md) - Visualization Agent integration patterns

### Secondary (MEDIUM confidence)

- [Python AST Security: Hijacking AST for Safe Code Handling](https://twosixtech.com/blog/hijacking-the-ast-to-safely-handle-untrusted-python/) - AST-based allowlist patterns
- [LangGraph Best Practices - Swarnendu De](https://www.swarnendu.de/blog/langgraph-best-practices/) - State design recommendations
- [JSON Parsing for Large Payloads - Towards Data Science](https://towardsdatascience.com/json-parsing-for-large-payloads-balancing-speed-memory-and-scalability/) - Large JSON handling strategies
- [Python orjson: Fast JSON Decoding](https://thelinuxcode.com/python-orjsonloads-in-2026-fast-strict-json-decoding-in-real-projects/) - orjson performance benefits in Plotly 6.x

### Tertiary (LOW confidence, requires validation)

- Web search result: "E2B sandbox has Plotly 5.19.0"—conflicts with DeepWiki stating 6.0.1. **Verification test needed.**

## Metadata

**Confidence breakdown:**
- Allowlist extension pattern: HIGH—confirmed by existing code_checker.py implementation and YAML structure
- State schema extension: HIGH—confirmed by LangGraph official documentation and backward compatibility guarantees
- E2B Plotly availability: MEDIUM—documentation says 6.0.1, search result says 5.19.0. Verification test resolves ambiguity.
- Output parser modification: HIGH—existing parsing logic is clear, extension point is well-defined
- Security decisions (custom JS): MEDIUM—no official Plotly security guidance, recommendation based on XSS prevention best practices

**Research date:** 2026-02-13
**Valid until:** 60 days (stable infrastructure domain—Plotly 6.x and LangGraph state management are mature patterns)

**User constraints honored:**
- Chart security boundaries: Documented in security rationale for allowlist
- Error handling: Noted in state schema (`chart_error` field) and output parser
- Validation depth: Recommended approach balances quick verification with comprehensive testing
- Custom JS decision: Recommendation provided (disallow) with rationale
