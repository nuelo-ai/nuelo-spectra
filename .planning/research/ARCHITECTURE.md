# Architecture Patterns: Visualization Agent Integration (v0.4)

**Domain:** Data Visualization Agent for existing LangGraph multi-agent system
**Researched:** 2026-02-12
**Confidence:** HIGH (based on direct codebase analysis + verified library documentation)

---

## Executive Summary

The Visualization Agent integrates into the existing LangGraph graph as a new node positioned after the Data Analysis Agent's response node. The architecture follows a **JSON-over-the-wire** pattern: Python generates Plotly figure JSON inside the E2B sandbox, the JSON flows through the agent state, and react-plotly.js renders it natively in the frontend DataCard. This avoids HTML/iframe injection entirely -- the chart is rendered as a first-class React component from structured data.

The key architectural insight is that the Visualization Agent does NOT execute code itself. It generates Plotly Python code, which then runs in the same E2B sandbox pipeline the system already uses. The agent's role is to decide chart type, map data columns to axes, and produce correct Plotly Express or Graph Objects code. The E2B sandbox returns chart JSON (via `plotly.io.to_json()`), which streams to the frontend alongside the existing table data and analysis text.

This approach requires changes to 4 backend files, 5 frontend files, and 2 config files. No existing component needs to be rewritten -- all changes are additive or extend existing interfaces.

---

## Current Architecture (Before -- v0.3)

```
User Query
    |
    v
[Manager Agent] --MEMORY_SUFFICIENT--> [da_with_tools] --> [da_response] --> END
    |
    +-CODE_MODIFICATION/NEW_ANALYSIS--> [coding_agent] --> [code_checker] --> [execute]
                                                                                |
                                                                                v
                                                                         [da_with_tools] --> [da_response] --> END
                                                                              ^    |
                                                                              |    v
                                                                         [search_tools]
```

**Key source files (current):**
- `backend/app/agents/graph.py` -- Graph assembly via `build_chat_graph()`
- `backend/app/agents/state.py` -- `ChatAgentState` TypedDict with 25+ fields
- `backend/app/agents/manager.py` -- Routes to `da_with_tools` or `coding_agent`
- `backend/app/agents/data_analysis.py` -- `da_with_tools_node()`, `da_response_node()`
- `backend/app/agents/coding.py` -- `coding_agent()` generates Python code
- `backend/app/agents/code_checker.py` -- AST + LLM validation
- `backend/app/services/sandbox/e2b_runtime.py` -- E2B execution
- `backend/app/config/prompts.yaml` -- Per-agent LLM config + system prompts
- `backend/app/config/allowlist.yaml` -- Allowed Python libraries for sandbox
- `frontend/src/components/chat/DataCard.tsx` -- Renders query brief / table / analysis
- `frontend/src/components/chat/ChatMessage.tsx` -- Routes to DataCard for structured responses
- `frontend/src/hooks/useSSEStream.ts` -- Processes SSE events from backend stream
- `frontend/src/types/chat.ts` -- TypeScript interfaces for stream events + messages

---

## Recommended Architecture (After -- v0.4)

```
User Query
    |
    v
[Manager Agent] --MEMORY_SUFFICIENT--> [da_with_tools] --> [da_response] --> END
    |                                                                         |
    +-CODE_MODIFICATION/NEW_ANALYSIS-->                                       |
         [coding_agent] --> [code_checker] --> [execute]                      |
                                                  |                           |
                                                  v                           |
                                           [da_with_tools] --> [da_response] -+
                                                ^    |              |
                                                |    v              v
                                           [search_tools]   {visualization_requested?}
                                                              |              |
                                                             NO            YES
                                                              |              |
                                                              v              v
                                                            END     [visualization_agent]
                                                                            |
                                                                            v
                                                                    [viz_execute]
                                                                            |
                                                                            v
                                                                    [viz_response] --> END
```

### Why this topology

**The Visualization Agent sits AFTER `da_response` as a conditional branch** because:

1. **Minimal disruption** -- `da_response` continues to work identically for non-visualization queries. The existing test suite and behavior are unaffected.
2. **Analysis context available** -- The Data Analysis Agent's interpretation text provides context for the Visualization Agent to select chart types and format labels.
3. **Clean separation of concerns** -- The Data Analysis Agent interprets meaning ("sales are highest in East region"), the Visualization Agent renders that meaning visually.
4. **No new Manager route needed** -- Adding a 4th route (VISUALIZATION) to the Manager would force visualization queries through a separate pipeline that duplicates coding -> checking -> executing. Instead, data computation happens normally, then visualization is applied as a post-processing step.

---

## Component Boundaries

### New Components (to create)

| Component | File Path | Responsibility | Reads From State | Writes To State |
|-----------|-----------|---------------|-----------------|-----------------|
| Visualization Agent | `backend/app/agents/visualization.py` | LLM generates Plotly Python code from execution results + user intent | `execution_result`, `analysis`, `user_query`, `chart_hint` | `chart_code` |
| Viz Execute Node | `backend/app/agents/graph.py` (function) | Runs chart code in E2B sandbox, parses chart JSON | `chart_code` | `chart_specs`, `chart_error` |
| Viz Response Node | `backend/app/agents/graph.py` (function) | Assembles final state with chart data for streaming | `chart_specs`, `analysis`, `final_response` | `final_response`, `chart_specs` |
| should_visualize | `backend/app/agents/graph.py` (function) | Conditional edge: routes to viz or END | `visualization_requested` | (routing only) |
| ChartRenderer | `frontend/src/components/data/ChartRenderer.tsx` | Renders Plotly JSON using react-plotly.js `<Plot>` | Props: `chartSpecs` | (UI only) |

### Modified Components (existing files that need changes)

| Component | File Path | What Changes | Risk Level |
|-----------|-----------|-------------|-----------|
| `ChatAgentState` | `backend/app/agents/state.py` | Add 5 new fields (additive TypedDict extension) | LOW |
| `build_chat_graph()` | `backend/app/agents/graph.py` | Add 3 nodes + 2 edges + 1 conditional edge; change `da_response` from finish point to conditional | MEDIUM |
| `da_response_node()` | `backend/app/agents/data_analysis.py` | Add visualization intent detection to return dict | LOW |
| `prompts.yaml` | `backend/app/config/prompts.yaml` | Add `visualization` agent config entry | LOW |
| `allowlist.yaml` | `backend/app/config/allowlist.yaml` | Add `plotly` to `allowed_libraries` | LOW |
| `agent_service.py` | `backend/app/services/agent_service.py` | Include `chart_specs` in metadata_json + node_complete event whitelist | LOW |
| `DataCard.tsx` | `frontend/src/components/chat/DataCard.tsx` | Add chart section between table and analysis | MEDIUM |
| `ChatMessage.tsx` | `frontend/src/components/chat/ChatMessage.tsx` | Pass `chart_specs` from `metadata_json` to DataCard | LOW |
| `chat.ts` (types) | `frontend/src/types/chat.ts` | Add `chart_specs` to `StreamEvent`; add new event types | LOW |
| `useSSEStream.ts` | `frontend/src/hooks/useSSEStream.ts` | Handle `visualization_started` event in switch | LOW |
| `ChatInterface.tsx` | `frontend/src/components/chat/ChatInterface.tsx` | Extract chart_specs from viz events in `getStreamingDataCard()` | LOW |

### Unchanged Components

| Component | Why Unchanged |
|-----------|--------------|
| Manager Agent (`manager.py`) | No new routing path -- visualization is post-processing, not routing |
| Coding Agent (`coding.py`) | Continues generating data-processing code only; chart code is separate |
| Code Checker (`code_checker.py`) | Validates data code only; chart code has simpler validation (no data access) |
| E2B Runtime (`e2b_runtime.py`) | Already supports arbitrary Python execution; no API changes needed |
| Onboarding Agent (`onboarding.py`) | No interaction with visualization |
| Chat Router (`chat.py`) | SSE streaming already forwards all node_complete events; no route changes |
| `useChatMessages.ts` | Message format unchanged; chart data stored in existing `metadata_json` |

---

## Detailed Data Flow

### Step-by-step for: "Show me a bar chart of sales by region"

```
1. MANAGER AGENT
   Input:  user_query = "Show me a bar chart of sales by region"
   Output: Command(goto="coding_agent", route=NEW_ANALYSIS)
   Note:   Standard routing. Manager does NOT detect visualization intent.

2. CODING AGENT
   Input:  user_query, data_profile
   Output: generated_code = Python code that computes sales by region as JSON
   Note:   Produces DATA, not charts. Identical to any non-viz query.
   Example output:
     import json
     result = df.groupby('region')['sales'].sum().reset_index().to_dict('records')
     print(json.dumps({"result": result}))

3. CODE CHECKER
   Input:  generated_code, user_query
   Output: VALID -> Command(goto="execute")

4. EXECUTE (E2B Sandbox)
   Input:  generated_code + data files uploaded
   Output: execution_result = '[{"region":"East","sales":50000},{"region":"West","sales":35000}]'
   Note:   Standard sandbox execution, identical to current flow.

5. DA_WITH_TOOLS (Data Analysis Agent)
   Input:  execution_result, user_query
   Output: AIMessage with analysis JSON (may search web if enabled)
   Note:   Tool-calling loop unchanged.

6. DA_RESPONSE (Data Analysis Agent response)
   Input:  analysis from da_with_tools
   Output: {
     analysis: "Sales by region shows East leading at $50K...",
     final_response: "Sales by region shows East leading at $50K...",
     follow_up_suggestions: ["Break down by quarter", "Show customer count per region"],
     visualization_requested: true,    // <-- NEW: detected from user_query
     chart_hint: "bar",                // <-- NEW: extracted from "bar chart"
     messages: [AIMessage(content=analysis)]
   }

7. CONDITIONAL EDGE: should_visualize()
   Input:  state["visualization_requested"]
   Output: "visualization_agent"  (because True)

8. VISUALIZATION AGENT (NEW)
   Input:  execution_result, analysis, user_query, chart_hint
   LLM generates Plotly Python code:
     import plotly.express as px
     import plotly.io as pio
     import json

     data = [{"region":"East","sales":50000},{"region":"West","sales":35000},
             {"region":"North","sales":42000},{"region":"South","sales":28000}]
     fig = px.bar(data, x="region", y="sales", title="Sales by Region",
                  color_discrete_sequence=["#6366f1"])
     fig.update_layout(template="plotly_white", height=400,
                       margin=dict(l=40, r=40, t=50, b=40))
     chart_json = json.loads(pio.to_json(fig))
     print(json.dumps({"chart": chart_json}))

   Output: {"chart_code": <above code string>}
   Note:   Data is EMBEDDED in code (not re-read from files).
           This avoids a second file upload to E2B.

9. VIZ_EXECUTE (NEW - E2B Sandbox)
   Input:  chart_code (no data files needed)
   Execution: Creates fresh E2B sandbox, runs chart code, parses stdout JSON
   Output: {
     chart_specs: [{"data": [...], "layout": {...}}],
     chart_error: ""
   }
   Note:   Lightweight sandbox call (~1-2s). No file upload overhead.

10. VIZ_RESPONSE (NEW)
    Input:  chart_specs, analysis (from step 6)
    Output: {
      final_response: <analysis from step 6>,
      chart_specs: [{"data": [...], "layout": {...}}],
      messages: [AIMessage(content=analysis)]
    }
    Note:   Preserves the analysis text. Adds chart_specs to state.

11. FRONTEND receives via SSE stream:
    - node_complete: {node: "viz_execute", chart_specs: [...]}
    - node_complete: {node: "viz_response", chart_specs: [...], final_response: "..."}

12. DATACARD renders:
    [Query Brief]           -- "Show me a bar chart of sales by region"
    [Generated Code]        -- (collapsible, from step 2)
    [Data Table]            -- (from execution_result, step 4)
    [Chart]                 -- NEW: react-plotly.js renders from chart_specs
    [Analysis]              -- (from step 6)
    [Follow-ups]            -- (from step 6)
```

### Data format: chart_specs structure

```typescript
// Each chart spec follows the Plotly JSON schema
interface ChartSpec {
  data: Array<{
    type: string;        // "bar", "scatter", "pie", etc.
    x?: any[];           // x-axis values
    y?: any[];           // y-axis values
    values?: any[];      // for pie charts
    labels?: any[];      // for pie charts
    marker?: object;     // styling
    mode?: string;       // for scatter: "markers", "lines+markers"
    name?: string;       // trace name (for legends)
    [key: string]: any;  // other Plotly trace properties
  }>;
  layout: {
    title?: { text: string };
    template?: string;
    height?: number;
    width?: number;       // omitted for responsive
    margin?: { l: number; r: number; t: number; b: number };
    xaxis?: { title?: { text: string } };
    yaxis?: { title?: { text: string } };
    [key: string]: any;   // other Plotly layout properties
  };
}

// State carries an array (milestone says "2-3 charts" possible)
chart_specs: ChartSpec[]   // typically length 1, sometimes 2-3
```

---

## State Schema Changes

### New fields added to ChatAgentState (state.py)

```python
class ChatAgentState(TypedDict):
    # ... all existing 25+ fields unchanged ...

    # NEW: Visualization Agent fields (v0.4)
    visualization_requested: bool
    """Whether da_response determined a chart should be generated.
    Set by da_response_node based on user intent + data suitability.
    Defaults to False. Read by should_visualize() conditional edge."""

    chart_hint: str
    """Optional chart type hint extracted from user query.
    Examples: 'bar', 'line', 'pie', 'scatter', '' (empty = auto-select).
    Set by da_response_node. Read by visualization_agent."""

    chart_code: str
    """Plotly Python code string generated by Visualization Agent.
    Executed in E2B sandbox by viz_execute to produce chart_specs.
    Empty string when no visualization is requested."""

    chart_specs: list[dict]
    """List of Plotly figure JSON objects: [{"data": [...], "layout": {...}}].
    Each entry is one chart. Usually 1, sometimes 2-3 per milestone req.
    Empty list when no visualization. Passed to frontend via SSE."""

    chart_error: str
    """Error from chart generation or execution. Empty string on success.
    Non-fatal: analysis still returns even if chart fails."""
```

**Backward compatibility:** All new fields use optional semantics via `.get()` with defaults in node functions. Existing checkpoints without these fields work because `state.get("visualization_requested", False)` returns `False`, skipping visualization entirely.

---

## Graph Topology Changes

### Changes to build_chat_graph() in graph.py

```python
def build_chat_graph(checkpointer=None):
    graph = StateGraph(ChatAgentState)

    # === EXISTING NODES (unchanged) ===
    graph.add_node("manager", manager_node)
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("halt", halt_node)
    graph.add_node("da_with_tools", da_with_tools_node)
    graph.add_node("search_tools", ToolNode([search_web], handle_tool_errors=True))
    graph.add_node("da_response", da_response_node)

    # === NEW NODES (v0.4 visualization) ===
    graph.add_node("visualization_agent", visualization_agent_node)
    graph.add_node("viz_execute", viz_execute_node)
    graph.add_node("viz_response", viz_response_node)

    # === EXISTING EDGES (unchanged) ===
    graph.set_entry_point("manager")
    graph.add_edge("coding_agent", "code_checker")
    # code_checker routes via Command (no explicit edge needed)
    graph.add_edge("execute", "da_with_tools")
    graph.add_conditional_edges("da_with_tools", tools_condition, {
        "tools": "search_tools",
        "__end__": "da_response",
    })
    graph.add_edge("search_tools", "da_with_tools")

    # === CHANGED: da_response routing (was finish point, now conditional) ===
    # Previously: graph.set_finish_point("da_response")
    # Now: conditionally route to visualization or end
    graph.add_conditional_edges(
        "da_response",
        should_visualize,
        {
            "visualization_agent": "visualization_agent",
            "__end__": "__end__",
        },
    )

    # === NEW EDGES (v0.4 visualization pipeline) ===
    graph.add_edge("visualization_agent", "viz_execute")
    graph.add_edge("viz_execute", "viz_response")

    # === FINISH POINTS ===
    graph.set_finish_point("viz_response")  # NEW
    graph.set_finish_point("halt")          # unchanged

    return graph.compile(checkpointer=checkpointer)


def should_visualize(state: ChatAgentState) -> str:
    """Conditional edge: route to visualization agent or end.

    Returns 'visualization_agent' if da_response flagged visualization_requested.
    Returns '__end__' otherwise (normal analysis-only response).
    """
    if state.get("visualization_requested", False):
        return "visualization_agent"
    return "__end__"
```

---

## Visualization Agent Design

### Agent Node: visualization.py

```python
async def visualization_agent_node(state: ChatAgentState) -> dict:
    """Generate Plotly Python code from execution results.

    The agent receives:
    - execution_result: JSON data from the Coding Agent's code
    - analysis: Data Analysis Agent's interpretation
    - user_query: Original user question (contains chart type hints)
    - chart_hint: Extracted chart type ('bar', 'line', 'pie', 'scatter', '')

    The agent generates Plotly Python code that:
    1. Embeds the execution_result data as a Python literal
    2. Creates appropriate Plotly figure(s)
    3. Serializes to JSON via plotly.io.to_json()
    4. Prints JSON to stdout for sandbox capture

    Returns: {"chart_code": str}
    """
```

### Key prompt design principles for the Visualization Agent

1. **Data is embedded, not loaded from files** -- The execution_result JSON is small (aggregated data). The agent writes it as a Python literal in the generated code. No file I/O needed.

2. **Auto-select chart type unless user specifies** -- If chart_hint is empty, the agent infers from data shape:
   - Categorical x + numeric y = bar chart
   - Time series x + numeric y = line chart
   - Parts of a whole = pie chart
   - Two numeric columns = scatter plot

3. **Multiple charts when appropriate** -- The milestone says "2-3 charts to show different perspectives." The agent decides when multiple views add value (e.g., bar chart + pie chart for the same data).

4. **Consistent styling** -- The prompt specifies a standard template (`plotly_white`), consistent margins, and brand-aligned color palette.

5. **Output format is strict** -- The code MUST end with:
   ```python
   chart_json = json.loads(pio.to_json(fig))
   print(json.dumps({"chart": chart_json}))
   ```
   For multiple charts:
   ```python
   charts = [json.loads(pio.to_json(fig)) for fig in [fig1, fig2]]
   print(json.dumps({"charts": charts}))
   ```

### Viz Execute Node

The viz_execute node reuses the existing `E2BSandboxRuntime` with a lightweight call:

```python
async def viz_execute_node(state: ChatAgentState) -> dict:
    """Execute Plotly chart code in E2B sandbox.

    Key differences from the main execute_in_sandbox:
    - No data files uploaded (data is embedded in code)
    - Shorter timeout (chart generation is fast, ~5-10s)
    - Parses chart JSON from stdout instead of execution_result
    - Non-fatal: chart_error is set but does NOT halt the pipeline
    """
```

**Non-fatal error handling:** If chart generation fails (LLM produces bad Plotly code, sandbox timeout), the response still includes the analysis text and data table. The chart section simply does not appear. This is critical -- a chart failure should never lose the analysis that was already computed.

### Viz Response Node

```python
async def viz_response_node(state: ChatAgentState) -> dict:
    """Assemble final response with chart data.

    Emits the chart_specs alongside the existing analysis.
    The final_response text is preserved from da_response (not overwritten).
    """
    writer = get_stream_writer()

    chart_specs = state.get("chart_specs", [])
    chart_error = state.get("chart_error", "")

    if chart_error:
        writer({
            "type": "visualization_error",
            "message": f"Chart generation failed: {chart_error}",
        })

    return {
        "chart_specs": chart_specs,
        # Preserve existing analysis and response
        "final_response": state.get("final_response", state.get("analysis", "")),
        "messages": state.get("messages", []),  # preserve existing messages
    }
```

---

## Frontend Integration

### DataCard.tsx -- New Chart Section

The chart section sits between Data Table and Analysis:

```
[Query Brief]           -- existing, unchanged
[Generated Code]        -- existing, unchanged (collapsible)
[Data Table]            -- existing, unchanged
[Chart(s)]              -- NEW
[Analysis]              -- existing, unchanged
[Follow-ups]            -- existing, unchanged
[Sources]               -- existing, unchanged
```

### New DataCard prop

```typescript
interface DataCardProps {
  // ... existing props unchanged ...
  chartSpecs?: Array<{ data: any[]; layout: any }>;  // NEW
}
```

### ChartRenderer Component

```tsx
// frontend/src/components/data/ChartRenderer.tsx
"use client";

import dynamic from "next/dynamic";

// Dynamic import: plotly.js requires window object, breaks SSR
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface ChartRendererProps {
  chartSpecs: Array<{ data: any[]; layout: any }>;
}

export function ChartRenderer({ chartSpecs }: ChartRendererProps) {
  return (
    <div className="space-y-4">
      {chartSpecs.map((spec, idx) => (
        <div key={idx} className="rounded-lg border bg-background p-2 overflow-hidden">
          <Plot
            data={spec.data}
            layout={{
              ...spec.layout,
              autosize: true,
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ["lasso2d", "select2d"],
              toImageButtonOptions: {
                format: "png",
                filename: `spectra-chart-${idx}`,
                height: 600,
                width: 800,
                scale: 2,
              },
            }}
            useResizeHandler={true}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      ))}
    </div>
  );
}
```

Architecture decisions for ChartRenderer:
- **`dynamic(() => import(...), { ssr: false })`** -- Plotly.js accesses `window` and `document`. Without dynamic import, Next.js SSR fails with "window is not defined."
- **`useResizeHandler={true}` + `autosize: true`** -- Chart resizes when DataCard or browser window resizes.
- **`config.toImageButtonOptions`** -- Satisfies milestone requirement "user should be able to download the visualization as an image." The Plotly modebar includes a camera icon for PNG download.
- **`paper_bgcolor: "transparent"`** -- Chart background inherits from DataCard's theme (light/dark mode compatible).
- **`displayModeBar: true`** -- Shows hover/zoom/pan/download toolbar. Satisfies "interactive" requirement.

### SSE Stream Integration

The existing `node_complete` event forwarding in `agent_service.py` already passes any key present in the node's state update. The whitelist in `run_chat_query_stream` needs `chart_specs` added:

```python
# In agent_service.py, run_chat_query_stream():
yield {
    "type": "node_complete",
    "node": node_name,
    **{k: v for k, v in update.items()
       if k in ("generated_code", "execution_result",
                "analysis", "final_response", "error",
                "routing_decision", "follow_up_suggestions",
                "search_sources",
                "chart_specs")}  # <-- ADD THIS
}
```

Frontend `useSSEStream.ts` needs one new event handler:

```typescript
case "visualization_started":
  newState.currentStatus = "Generating visualization...";
  break;
```

Frontend `ChatInterface.tsx` `getStreamingDataCard()` extracts chart data:

```typescript
let chartSpecs: ChartSpec[] | undefined = undefined;
const vizEvent = events.find(
  (e) => e.type === "node_complete" && e.node === "viz_response"
);
if (vizEvent?.chart_specs && vizEvent.chart_specs.length > 0) {
  chartSpecs = vizEvent.chart_specs;
}
```

---

## Patterns to Follow

### Pattern 1: Agent as Code Generator, Not Code Executor

**What:** The Visualization Agent generates Plotly Python code but does NOT execute it. A separate `viz_execute` node runs the code in E2B. This mirrors the existing Coding Agent -> Code Checker -> Execute pattern.

**When:** Always. This maintains the security boundary.

**Why:** The existing architecture separates code generation from code execution for security (sandbox isolation) and debuggability (code is visible in DataCard). The Visualization Agent follows the same contract.

### Pattern 2: JSON-over-the-wire for Charts

**What:** Charts are serialized as Plotly JSON (`{data: [...], layout: {...}}`) and passed through the state/SSE stream. The frontend renders with react-plotly.js `<Plot>` component using native `data` and `layout` props.

**When:** Always. Never send HTML, SVG, or base64 images.

**Why:**
- Interactive: hover, zoom, pan are native Plotly features
- Type-safe: Plotly JSON has a well-defined schema
- Lightweight: ~5KB JSON vs ~100KB image or ~3MB embedded-HTML
- Secure: no XSS risk -- react-plotly.js renders from structured data, not innerHTML
- Themeable: layout properties can be overridden client-side for dark mode

### Pattern 3: Conditional Post-Processing (not Routing)

**What:** Visualization is a conditional post-processing step after `da_response`, controlled by a `should_visualize()` edge function.

**When:** Every query that flows through the code generation path.

**Why:** Visualization always needs data first. It is not an alternative path -- it is an extension of the analysis path. Keeping it after `da_response` means the analysis is always available even if chart generation fails.

### Pattern 4: Embed Data in Chart Code

**What:** The Visualization Agent embeds `execution_result` data directly into the generated Plotly code as a Python literal. The viz_execute sandbox does NOT re-upload data files.

**When:** Always. Chart data is already computed and small (aggregated/processed).

**Why:**
- Avoids ~2-3 second file upload overhead per query
- Simpler error handling (no file-not-found for charts)
- execution_result is typically <100 rows of aggregated data
- Chart code is self-contained and reproducible

### Pattern 5: Non-Fatal Visualization Errors

**What:** If chart generation or execution fails, the response still includes the analysis text and data table. The chart section simply does not render.

**When:** Any chart-related failure (LLM generates invalid Plotly code, sandbox timeout, Plotly import error).

**Why:** The user asked a question and got a complete answer (data + analysis). The chart is a bonus. Losing the entire response because a chart failed would be a poor user experience.

**Implementation:** `viz_execute` writes to `chart_error` on failure instead of routing to `halt`. `viz_response` checks `chart_error` and emits a warning event but still returns the existing analysis.

### Pattern 6: YAML-Configured Agent

**What:** The Visualization Agent follows the established per-agent config pattern in `prompts.yaml`.

**When:** Always. All 5 existing agents use this pattern.

**Why:** Consistency. Enables using a cheaper/faster model for chart code generation since Plotly code is structurally simpler than data analysis code.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: HTML Injection via dangerouslySetInnerHTML or iframe

**What:** Having the LLM generate a complete HTML page with embedded Plotly.js and injecting it into React.

**Why bad:** XSS attack surface, no React integration (chart outside component tree), 3MB+ payload size (embedded plotly.js library), poor responsiveness (iframe sizing), no theme support.

**Instead:** JSON-over-the-wire with react-plotly.js (Pattern 2).

### Anti-Pattern 2: Combining Data Code and Chart Code in Coding Agent

**What:** Having the Coding Agent generate both data processing AND Plotly chart code in a single block.

**Why bad:** Doubles prompt complexity. Chart errors trigger data retry loops (coupled failures). Code Checker must validate Plotly API. Violates single-responsibility.

**Instead:** Coding Agent handles data. Visualization Agent handles charts. Separate concerns.

### Anti-Pattern 3: Manager Agent Routing to Visualization

**What:** Adding a 4th route "VISUALIZATION" to the Manager that bypasses data analysis.

**Why bad:** Visualization ALWAYS needs computed data. A separate route would duplicate the coding->checking->executing pipeline. Manager's 3-route logic is well-tested; a 4th route reduces routing accuracy.

**Instead:** Visualization as post-processing after analysis (Pattern 3).

### Anti-Pattern 4: Storing Chart Images

**What:** Using `fig.write_image()` in E2B and returning base64 PNG/SVG.

**Why bad:** Static (no hover/zoom/pan), larger payload, not responsive, not themeable. The milestone explicitly requires "interactive" charts.

**Instead:** `plotly.io.to_json()` + react-plotly.js rendering.

### Anti-Pattern 5: Re-running Data Code for Visualization

**What:** Having the Visualization Agent re-execute the original data query to get fresh data for charting.

**Why bad:** Doubles E2B sandbox cost and latency. Data is already in `execution_result`. Risk of different results if data changed between calls.

**Instead:** Embed `execution_result` in chart code (Pattern 4).

---

## Scalability Considerations

| Concern | At Current Scale | At 10K Users | At 1M Users |
|---------|-----------------|--------------|-------------|
| E2B cost | +1 lightweight sandbox per viz query (~$0.001) | Cache chart code for repeated patterns | Pre-compute charts for common aggregations |
| Chart JSON size | ~5KB per chart, negligible | Stream separately if >100KB | Paginate multi-chart responses |
| Plotly.js bundle | ~3.5MB loaded once, browser-cached | Use `plotly.js-basic-dist` (~1MB) | Lazy-load chart type modules |
| LLM calls | +1 per viz query (Visualization Agent) | Use cheaper model (e.g., haiku) for chart code | Template-based chart generation (no LLM) |
| Render perf | Single `<Plot>`, <100ms render | Virtualize charts in long conversations | IntersectionObserver for deferred rendering |

---

## Suggested Build Order (Dependency-Aware)

### Phase 1: Backend State + Agent (no frontend changes)
1. `state.py` -- Add 5 new fields to `ChatAgentState`
2. `allowlist.yaml` -- Add `plotly` to allowed_libraries
3. `prompts.yaml` -- Add `visualization` agent config
4. `visualization.py` -- New visualization agent node (LLM code generation)
5. `graph.py` -- Add `viz_execute_node` function (E2B chart execution)
6. `graph.py` -- Add `viz_response_node` function
7. `graph.py` -- Add `should_visualize()` conditional edge function
8. `graph.py` -- Wire nodes into `build_chat_graph()`, change `da_response` routing

### Phase 2: Backend Integration (connects to existing pipeline)
9. `data_analysis.py` -- Modify `da_response_node` to detect visualization intent
10. `agent_service.py` -- Add `chart_specs` to metadata_json and node_complete whitelist
11. Backend testing -- End-to-end test: query with viz intent produces chart_specs in state

### Phase 3: Frontend Rendering
12. `npm install react-plotly.js plotly.js` -- Install Plotly dependencies
13. `ChartRenderer.tsx` -- New component with dynamic import
14. `DataCard.tsx` -- Add `chartSpecs` prop, render ChartRenderer between table and analysis
15. `chat.ts` -- Add `chart_specs` to `StreamEvent` type, add `visualization_started` event type
16. `ChatMessage.tsx` -- Pass `metadata_json.chart_specs` to DataCard
17. `useSSEStream.ts` -- Handle `visualization_started` event
18. `ChatInterface.tsx` -- Extract `chart_specs` from viz events in `getStreamingDataCard()`

### Phase 4: Polish + Edge Cases
19. Dark mode -- Chart theme adaptation (detect theme, swap `plotly_white` / `plotly_dark`)
20. Multi-chart support -- Test 2-3 charts per response, layout spacing
21. Download as image -- Verify Plotly modebar PNG download works in DataCard context
22. Responsive -- Chart resizes on window/panel toggle
23. Error handling -- Chart failure shows warning, analysis still renders
24. Chart skeleton -- Loading skeleton while viz_execute runs

### Rationale
- State schema first: everything reads/writes it
- Backend before frontend: frontend needs SSE events to consume
- Single chart working end-to-end before multi-chart or dark mode
- Error handling after happy path is validated
- Polish after core functionality is solid

---

## Sources

- [plotly.io.to_json documentation (v6.5.0)](https://plotly.github.io/plotly.py-docs/generated/plotly.io.to_json.html) -- HIGH confidence
- [react-plotly.js GitHub](https://github.com/plotly/react-plotly.js) -- HIGH confidence
- [React plotly.js official docs](https://plotly.com/javascript/react/) -- HIGH confidence
- [Plotly JSON chart schema](https://plotly.com/chart-studio-help/json-chart-schema/) -- HIGH confidence
- [E2B Code Interpreter](https://github.com/e2b-dev/code-interpreter) -- HIGH confidence
- [Generating Plotly JSON in Python for React](https://community.plotly.com/t/generating-plotly-json-in-python-and-displaying-in-react-clientside/59238) -- MEDIUM confidence
- [LangGraph multi-agent workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/) -- MEDIUM confidence
- Direct codebase analysis of all 15+ source files -- HIGH confidence
- Milestone requirements: `requirements/milestone-04-req.md` -- HIGH confidence
