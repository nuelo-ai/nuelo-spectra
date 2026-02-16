# Feature Research: Data Visualization (v0.4)

**Domain:** AI-powered data analytics platform -- AI-generated interactive charts with Plotly
**Researched:** 2026-02-12
**Confidence:** MEDIUM-HIGH
**Supersedes:** Previous FEATURES.md (v0.3 multi-file conversation features, 2026-02-11)

---

## Executive Summary

This research maps the feature landscape for Spectra v0.4 Data Visualization, which adds a 6th agent (Visualization Agent) that generates Plotly chart code in the E2B sandbox. The core architectural question is how to get chart specifications from the Python sandbox to the React frontend. Two approaches exist: **code generation** (LLM generates Python Plotly code, sandbox outputs figure JSON) and **JSON specification** (LLM generates chart spec directly, no code execution needed). Given Spectra's existing architecture -- where the Coding Agent already generates Python code executed in E2B -- the code generation approach is the natural fit: the Visualization Agent generates Python code that creates a Plotly figure and outputs `fig.to_json()`, which the frontend renders via `react-plotly.js`.

**Key findings from ecosystem research:**

- **The "generate Plotly code, output JSON spec" pattern is proven.** Plotly Python's `fig.to_json()` produces a JSON structure (`{data: [...], layout: {...}}`) that is directly consumable by Plotly.js / react-plotly.js in the browser. This is how Dash works internally. Spectra's sandbox already captures stdout; the figure JSON can be output alongside the existing `{"result": ...}` data.
- **Chart type selection is table stakes, not a differentiator.** ChatGPT, Julius AI, and every AI analytics tool auto-select chart types. The AI deciding "this data should be a bar chart" is expected. The differentiator is *when* to show a chart (Spectra's "err on side of showing" policy) and how seamlessly it integrates with the existing Data Card.
- **Bundle size is the main frontend concern.** Full Plotly.js is ~2MB minified. Using `react-plotly.js/factory` with `plotly.js-basic-dist-min` reduces this to ~999KB. A custom partial bundle with only needed chart types can reach ~410KB gzipped. For 7 chart types (bar, line, scatter, histogram, box, pie, donut), the basic bundle covers all of them.
- **PNG/SVG export is built into Plotly.js** via `Plotly.downloadImage()` and `Plotly.toImage()`. Both PNG and SVG are free (no subscription). This is a browser-side operation -- no backend involvement needed.
- **Chart type switching is straightforward in React.** Since Plotly.js renders from JSON spec, switching chart type means modifying `data[0].type` in the spec and re-rendering. The challenge is knowing which transformations are valid (you cannot turn a histogram into a pie chart without restructuring the data).
- **E2B sandbox does NOT natively extract Plotly figures.** E2B's chart extraction works with Matplotlib only. For Plotly, the code must explicitly output the figure JSON via `print()` or `fig.to_json()`. This means the Visualization Agent's code must be specifically structured to output JSON -- it cannot rely on E2B's built-in chart detection.

**Competitive context:** Julius AI supports 29+ chart types with theme selection and custom color palettes. ChatGPT supports 18+ chart types via Matplotlib (rendered as images, not interactive). Spectra v0.4's advantage is interactive Plotly charts (zoom, pan, hover tooltips) rendered in-browser, where competitors serve static images.

---

## Table Stakes

Features users expect from an AI analytics platform with visualization capabilities in 2026. Missing any of these makes the visualization feel half-baked.

| Feature | Why Expected | Complexity | Dependencies on Existing |
|---------|--------------|------------|--------------------------|
| **AI-selected chart type** | ChatGPT and Julius auto-select appropriate chart types. Users expect to say "show me sales trends" and get a line chart without specifying the type. This is the baseline for AI visualization. | MEDIUM | Visualization Agent prompt engineering. Must understand data shape (time series = line, categories = bar, distribution = histogram). Coding Agent's `data_profile` provides column types. |
| **Core chart types: bar, line, scatter** | These three cover ~80% of analytical visualization needs. Bar for comparisons, line for trends, scatter for relationships. Every charting tool supports these. | LOW | Direct mapping to Plotly trace types: `type: "bar"`, `type: "scatter"` (mode: "lines"), `type: "scatter"` (mode: "markers"). All supported by `plotly.js-basic-dist-min`. |
| **Distribution charts: histogram, box plot** | Expected for any data analysis tool. "Show distribution of salaries" and "show outliers in revenue" are common queries. | LOW | Plotly trace types: `type: "histogram"`, `type: "box"`. Both in basic bundle. |
| **Part-of-whole charts: pie, donut** | Standard for composition questions ("What percentage of sales comes from each region?"). Donut is just a pie with a hole. | LOW | Plotly trace type: `type: "pie"`. Donut = `pie` with `hole: 0.4`. Both in basic bundle. |
| **Chart rendered in Data Card** | Users see chart + table together as one analytical result. Chart above table is the natural reading order (insight first, detail second). This is how Julius and ChatGPT present results. | MEDIUM | Extends existing `DataCard` component. New section between Query Brief and Data Table. Must handle progressive rendering (chart appears while explanation still streaming). New `chartData` prop on DataCard. |
| **Automatic chart generation (AI decides when)** | The product rule "err on side of showing charts" means the AI proactively generates visualizations when data supports it, without the user asking. This is now expected -- Julius and ChatGPT both do this. | HIGH | Manager Agent must hint visualization intent. Data Analysis Agent must decide whether to delegate to Visualization Agent. Requires changes to agent pipeline: after execution, if data is chart-worthy, trigger visualization flow. Two-pass approach: analysis first, then visualization. |
| **Interactive charts (zoom, pan, hover)** | Plotly.js provides this out of the box. Users expect hover tooltips showing exact values, zoom on axes, and pan. Static image charts feel dated. | LOW | `react-plotly.js` provides interactivity by default. `config` prop controls which interactions are enabled. `layout.hovermode` controls tooltip behavior. No custom code needed. |
| **Chart titles and axis labels** | Charts without titles or axis labels are unreadable. The AI must generate meaningful titles like "Monthly Revenue (2024-2025)" and label axes with units. | LOW | Part of Visualization Agent prompt: instruct to always set `layout.title`, `layout.xaxis.title`, `layout.yaxis.title`. Low complexity but critical for usability. |
| **Plotly figure JSON output from sandbox** | The sandbox must output the Plotly figure JSON alongside existing data results. This is the data pipeline connecting backend chart generation to frontend rendering. | MEDIUM | Modify code generation pattern: Visualization Agent generates code that creates a Plotly figure and outputs `fig.to_json()`. Modify `execute_in_sandbox` to capture figure JSON. New field in `ChatAgentState`: `chart_data`. SSE stream must include chart JSON in `node_complete` event. |
| **PNG export** | Users need to download charts for presentations and reports. PNG is universal. This is standard in every charting tool. | LOW | `Plotly.downloadImage(gd, {format: 'png', width: 1200, height: 800})` -- entirely browser-side. Add a download button to the chart section of DataCard. No backend changes needed. |

---

## Differentiators

Features that set Spectra apart from competitors. Not expected, but create meaningful value.

| Feature | Value Proposition | Complexity | Dependencies on Existing |
|---------|-------------------|------------|--------------------------|
| **SVG export** | Higher quality than PNG for print and presentations. Scales without pixelation. ChatGPT only exports PNG. Julius exports PNG. Spectra offering SVG is a real differentiator for professional users. | LOW | `Plotly.downloadImage(gd, {format: 'svg'})` -- free in Plotly.js (despite what some docs suggest about subscriptions, the JS library supports SVG natively). Add as second export option next to PNG button. |
| **Chart type switcher** | Let users switch between compatible chart types after generation (e.g., bar to line to scatter for the same data). Reduces round-trips to the AI. Julius does not have this. ChatGPT requires re-prompting. | MEDIUM | UI: dropdown or button group in chart section of DataCard. Logic: modify `data[0].type` in the Plotly JSON spec and re-render. Must validate compatibility (only switch between types that share the same data shape). Map: bar/line/scatter are interchangeable; histogram is standalone; pie/donut are interchangeable. |
| **Dark mode chart theming** | Charts must respect Spectra's light/dark mode toggle (Nord palette). Most AI tools render charts with fixed white backgrounds that clash in dark mode. Spectra matching chart theme to app theme is polished. | MEDIUM | Plotly layout supports `paper_bgcolor`, `plot_bgcolor`, `font.color`, `gridcolor`. Visualization Agent prompt must generate theme-aware layouts. Frontend can also override layout colors based on current theme. Requires theme detection at render time. |
| **Chart + Table + Analysis as unified Data Card** | The three-part Data Card (chart + table + explanation) is more informative than competitors who show either a chart OR a table. Spectra shows both, letting users see the visual pattern and verify with raw numbers. | MEDIUM | DataCard component already has table + explanation sections. Add chart section above table. Progressive rendering: chart skeleton -> chart render -> table -> explanation. The unified card is the differentiator -- most tools separate charts and tables into different views. |
| **Visualization Agent as separate 6th agent** | Specialized agent focused solely on visualization. Better prompt quality than a general agent trying to do analysis + charting. Can be configured with different LLM/temperature for creative chart generation. | MEDIUM | New agent module: `visualization.py`. New YAML config entry. Integrated into LangGraph workflow as an optional node after `da_response`. Uses existing `llm_factory` and `config` infrastructure. |
| **Hover tooltips with formatted values** | Plotly hover templates can show "Revenue: $1,234,567" instead of raw "1234567". Formatting makes charts immediately readable. Few AI tools bother with this. | LOW | Plotly `hovertemplate` in trace config. Visualization Agent prompt instructs formatting (currency, percentage, date). Example: `hovertemplate: "Region: %{x}<br>Revenue: $%{y:,.0f}"`. |
| **Responsive chart sizing** | Charts resize with the Data Card container. No horizontal scrolling, no tiny charts on mobile. | LOW | `react-plotly.js` supports `useResizeHandler={true}` + `layout.autosize=true` + `style={{width: '100%'}}`. Standard responsive pattern, no custom code needed. |

---

## Anti-Features

Features to explicitly NOT build in v0.4. Building these would waste effort, add complexity, or create UX problems.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Full chart editor / chart builder** | "Let users customize every aspect of charts" | Building a chart editor (like Plotly's `react-chart-editor`) is a massive scope expansion. It is essentially a separate product. Users who need fine-grained control should re-prompt the AI or export the data and use a dedicated tool. The chart editor package itself is 500KB+ and adds significant UI complexity. | Offer chart type switcher (limited, controlled customization) and PNG/SVG export. Users can re-prompt: "Make the bars blue" or "Add a trend line." |
| **3D charts, geographic maps, Sankey diagrams** | "Support all Plotly chart types" | Each additional chart type increases the Plotly bundle size, the LLM prompt complexity, and the testing surface. 3D/geo/Sankey charts are niche and add ~500KB+ to the bundle each. They also require specialized data shapes that the AI often generates incorrectly. ChatGPT's LLM performance degrades significantly with complex Plotly types. | Start with 7 types (bar, line, scatter, histogram, box, pie, donut). These cover 95%+ of analytical use cases. Add types based on user demand in future milestones. |
| **Animated/time-series playback charts** | "Show data changing over time with animation" | Plotly supports animation via `frames`, but it is buggy in react-plotly.js, adds complexity to the figure JSON, and confuses most users. Animation is visual candy, not analytical insight. The LLM generates incorrect animation specs more often than correct ones. | Use static line charts for time series. If users need animation, they can export data and use dedicated animation tools. |
| **Real-time / auto-refreshing charts** | "Charts that update as new data arrives" | Spectra analyzes uploaded static files, not streaming data sources. There is no data to refresh. Building real-time infrastructure is a different product direction entirely. | Charts are generated per-query. Users can re-run queries to get updated charts if they upload new data. |
| **Multi-chart dashboards** | "Show multiple charts in a grid layout" | Dashboard builders (Superset, Metabase, Tableau) are dedicated products. Building a dashboard layout system is months of work and changes Spectra's identity from "AI chat analyst" to "dashboard builder." | One chart per query in the Data Card. Users can ask multiple questions to get multiple cards, each with its own chart. The chat history IS the dashboard. |
| **Chart annotation / drawing tools** | "Let users add arrows, text boxes, highlights to charts" | Plotly has annotation support, but building a UI for adding/editing annotations is complex and niche. Users who need annotations should export and annotate in presentation tools. | AI can add annotations in the generated code if asked ("highlight the peak value"). No manual annotation UI. |
| **Server-side chart rendering (Kaleido/Orca)** | "Generate chart images on the backend" | Adds a heavy dependency (Kaleido = headless browser). Unnecessary when Plotly.js renders client-side and `Plotly.toImage()` handles export. Server-side rendering is only needed for email reports or PDF generation -- not in v0.4 scope. | All chart rendering happens in the browser via Plotly.js. Export via `Plotly.downloadImage()`. |
| **Storing chart configurations in the database** | "Save charts for later viewing" | Currently, chat messages store analysis text. Adding chart JSON (which can be 50KB-500KB per chart) to the database significantly increases storage requirements and complicates the message schema. | Chart JSON is transient -- generated per query, rendered in the session. If needed later, the user re-asks the question. Consider persisting chart JSON in message `metadata_json` field as a later optimization, not v0.4 scope. |

---

## Feature Dependencies

```
                    Allowlist Update (add plotly)
                              |
                    Visualization Agent (new agent module)
                    /              |               \
                   /               |                \
        Sandbox Output         Agent Pipeline      Agent YAML Config
        (fig.to_json())        Integration         (prompts, provider)
              |                    |
              |              Manager + Analyst
              |              Route to Visualizer
              |                    |
         SSE Stream           Chart Decision
         (chart_data field)   Heuristic
              |                    |
              |                    |
        DataCard Update       "Err on Side of
        (chart section)       Showing Charts" Logic
        /          \
       /            \
  react-plotly.js   Chart Section
  (partial bundle)  UI Components
       |               |
  PNG Export       SVG Export
  Button           Button
       |
  Chart Type
  Switcher
       |
  Dark Mode
  Chart Theming
```

### Critical Path (must be sequential)

1. **Allowlist update** -- Add `plotly` to `allowlist.yaml` so the Coding Agent and Visualization Agent can import it in the sandbox. E2B sandbox has Plotly pre-installed.
2. **Visualization Agent module** -- New `visualization.py` agent that generates Plotly Python code and outputs figure JSON. System prompt with chart type selection heuristics.
3. **Sandbox output modification** -- Modify `execute_in_sandbox` to capture Plotly figure JSON from stdout (new output format: `{"result": ..., "chart": {...}}`).
4. **Agent pipeline integration** -- Wire Visualization Agent into LangGraph workflow. Data Analysis Agent decides when to delegate to Visualizer. Add `chart_data` to `ChatAgentState`.
5. **SSE stream extension** -- Add `chart_data` field to `node_complete` events. Frontend `useSSEStream` hook captures chart JSON.
6. **DataCard chart section** -- New chart section in `DataCard.tsx` rendering Plotly figure via `react-plotly.js`.
7. **Export buttons** -- PNG and SVG download buttons below chart.
8. **Chart type switcher** -- Dropdown to switch between compatible chart types.

### Can Be Parallelized

- `react-plotly.js` installation and basic `PlotlyChart` component (independent of backend)
- Dark mode chart theming (independent CSS/config work)
- Chart type switcher UI component (after basic chart rendering works)
- SVG export (same pattern as PNG, trivial addition)

### Dependency Notes

- **Visualization Agent requires allowlist update:** `plotly` must be in the allowed libraries before the agent can generate code that imports it.
- **DataCard chart section requires SSE stream extension:** The frontend cannot render charts until chart JSON flows through the streaming pipeline.
- **Chart type switcher requires chart rendering:** Switching types is a modification of the rendered chart spec.
- **Dark mode theming enhances chart rendering:** Can be added after basic chart rendering works, not a blocker.

---

## Feature Categories & Complexity Budget

### Category 1: Chart Generation (Backend)

| Feature | Complexity | Risk |
|---------|-----------|------|
| Visualization Agent module | MEDIUM | MEDIUM -- prompt engineering for chart type selection |
| Allowlist update for plotly | LOW | LOW -- config change |
| Sandbox output for figure JSON | MEDIUM | MEDIUM -- modifying stdout capture pipeline |
| Agent pipeline wiring (LangGraph) | HIGH | HIGH -- adding conditional node to existing graph |
| Chart decision heuristic ("when to chart") | HIGH | HIGH -- biggest UX risk; too many charts = noise, too few = missed value |
| Manager/Analyst visualization routing | MEDIUM | MEDIUM -- extending existing routing logic |

### Category 2: Chart Display (Frontend)

| Feature | Complexity | Risk |
|---------|-----------|------|
| react-plotly.js installation (partial bundle) | LOW | LOW -- npm package, factory pattern |
| PlotlyChart wrapper component | LOW | LOW -- standard React component |
| DataCard chart section | MEDIUM | MEDIUM -- progressive rendering integration |
| SSE stream chart_data handling | LOW | LOW -- extending existing pattern |
| Responsive chart sizing | LOW | LOW -- built-in Plotly.js feature |
| Dark mode chart theming | MEDIUM | LOW -- layout color overrides |

### Category 3: Chart Export

| Feature | Complexity | Risk |
|---------|-----------|------|
| PNG export button | LOW | LOW -- single Plotly API call |
| SVG export button | LOW | LOW -- same pattern as PNG |

### Category 4: Chart Customization

| Feature | Complexity | Risk |
|---------|-----------|------|
| Chart type switcher | MEDIUM | MEDIUM -- type compatibility mapping |
| Hover tooltip formatting | LOW | LOW -- prompt engineering |
| Chart titles/labels | LOW | LOW -- prompt engineering |

---

## MVP Recommendation

### Must Have (v0.4 Core)

Prioritize these features in this order:

1. **Allowlist update + Visualization Agent** -- Foundation: add `plotly` to allowed libraries, create new agent with prompt that selects chart types based on data shape and user intent. The prompt must include chart type heuristics (time series -> line, categorical comparison -> bar, distribution -> histogram, composition -> pie).

2. **Sandbox figure JSON output** -- Modify the code generation pattern so the Visualization Agent's code creates a Plotly figure and outputs `fig.to_json()`. Modify `execute_in_sandbox` to parse and extract chart JSON from stdout alongside existing `{"result": ...}` data.

3. **Agent pipeline integration** -- Add Visualization Agent as conditional node in LangGraph graph. Data Analysis Agent decides whether to trigger visualization. Add `chart_data` field to `ChatAgentState`. Implement the "err on side of showing charts" heuristic.

4. **SSE stream + frontend chart rendering** -- Extend SSE events to include chart JSON. Install `react-plotly.js` with partial bundle. Create `PlotlyChart` component. Add chart section to `DataCard`.

5. **PNG/SVG export** -- Two download buttons below chart in DataCard. Browser-side via `Plotly.downloadImage()`.

6. **Chart titles, labels, hover formatting** -- Prompt engineering in Visualization Agent to always include meaningful titles, axis labels, and formatted hover templates.

7. **Dark mode chart theming** -- Charts respect current light/dark theme.

### Defer to Later

- **Chart type switcher** -- Nice-to-have after core charts work. Ship in v0.4.1 or as a fast follow. The mapping of compatible chart types needs careful design.
- **Advanced chart types** -- Heatmap, area, treemap. Add based on user demand.
- **Chart persistence in database** -- Store chart JSON in `metadata_json`. Not needed for v0.4 launch.
- **Chart-specific follow-up suggestions** -- "Zoom into Q4" or "Switch to line chart." Requires understanding chart context.

---

## Detailed Feature Specifications

### 1. Visualization Agent

**Architecture decision: Separate agent vs. extending Coding Agent**

Use a separate Visualization Agent (not an extension of Coding Agent) because:
- Chart generation needs different prompt engineering than data analysis code
- The agent can be configured with a different LLM or temperature
- Clean separation of concerns: Coding Agent generates analysis code, Visualization Agent generates chart code
- Allows independent iteration on chart quality without risking analysis quality

**How it works:**
1. Coding Agent generates analysis code, sandbox executes, produces `{"result": data}`
2. Data Analysis Agent interprets results
3. Data Analysis Agent (or a heuristic in the graph) decides: "Does this benefit from visualization?"
4. If yes: Visualization Agent receives the execution result data + user query + data profile
5. Visualization Agent generates Python code that:
   - Creates a Plotly figure (`fig = go.Figure(...)` or `fig = px.bar(...)`)
   - Configures layout (title, axes, theme)
   - Outputs `print(fig.to_json())`
6. Sandbox executes the visualization code, outputs figure JSON
7. Frontend renders figure JSON via `react-plotly.js`

**Chart type selection heuristic in prompt:**
```
- Time series data (date/datetime column + numeric) -> Line chart
- Categorical x Numeric (< 15 categories) -> Bar chart
- Categorical x Numeric (> 15 categories) -> Horizontal bar chart
- Two numeric columns -> Scatter plot
- Single numeric column distribution -> Histogram
- Single numeric grouped by category -> Box plot
- Composition/percentage (< 8 categories) -> Pie/donut chart
- When in doubt and data has categories -> Bar chart (safest default)
```

**Complexity:** MEDIUM -- new agent module following existing patterns (llm_factory, config, prompts.yaml).

### 2. Sandbox Figure JSON Output

**What exists today:**
- Code outputs `print(json.dumps({"result": result}))` to stdout
- `execute_in_sandbox` parses stdout for JSON with `"result"` key
- `ExecutionResult` captures stdout, stderr, results

**What needs to change:**
- Visualization Agent code outputs figure JSON via `print(fig.to_json())`
- Two-pass execution: first pass for analysis code, second pass for chart code
- OR: Single pass where code generates both result and chart
- `execute_in_sandbox` must capture chart JSON separately from result JSON

**Recommended approach: Two-pass execution**
- Pass 1: Existing pipeline (Coding Agent -> Code Checker -> Execute -> result JSON)
- Pass 2: Visualization Agent generates chart code -> Execute -> figure JSON
- This keeps the existing pipeline untouched and adds visualization as an additive layer
- Cost: One extra sandbox execution per visualization (~150ms + LLM call time)

**Alternative: Single-pass combined output**
- Code outputs `{"result": data, "chart": figure_json}`
- Simpler, one sandbox call
- But: Coding Agent would need to handle both analysis AND chart generation in one prompt
- Risk: Increases prompt complexity, reduces reliability of both analysis and chart
- Verdict: NOT recommended. Two-pass is cleaner despite the extra sandbox call.

**Complexity:** MEDIUM -- modifying stdout parsing is straightforward; the two-pass architecture requires pipeline changes.

### 3. "When to Show Charts" Decision Heuristic

**Product rule:** "Err on side of showing charts. If data supports visualization, show it."

**Implementation options:**

**Option A: Visualization Agent always runs, decides internally**
- After every analysis, run Visualization Agent
- Agent examines results and decides: chart or no chart
- Pros: Simple pipeline (always run)
- Cons: Wasted LLM call + sandbox execution when no chart is appropriate (~40% of queries)

**Option B: Data Analysis Agent decides, conditionally routes**
- Data Analysis Agent's JSON response includes `"should_visualize": true/false`
- If true, graph routes to Visualization Agent
- Pros: No wasted calls
- Cons: Data Analysis Agent may be poor at judging visualization value

**Option C: Rule-based heuristic on execution result**
- After execution, check: Is result a list of dicts (table)? Are there numeric columns? Is there a categorical grouping?
- If heuristics pass, route to Visualization Agent
- Pros: Fast, deterministic, no extra LLM call for decision
- Cons: May miss edge cases, less nuanced than LLM judgment

**Recommended: Option B with aggressive defaults**
- Data Analysis Agent includes `"should_visualize"` in its JSON response
- Default bias: `true` unless result is:
  - A single scalar value ("The average is 42")
  - A text/error response
  - An empty result
- This aligns with "err on side of showing charts" while avoiding obviously inappropriate charts

**Complexity:** HIGH -- this is the most impactful UX decision. Too aggressive = chart noise. Too conservative = "why doesn't it show charts?"

### 4. Frontend Chart Rendering

**Bundle strategy:**
```javascript
// Use partial bundle to reduce from ~2MB to ~999KB
import Plotly from 'plotly.js-basic-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
const Plot = createPlotlyComponent(Plotly);
```

The `plotly.js-basic-dist-min` bundle includes: scatter, bar, pie, histogram -- which covers all 7 required chart types (line = scatter mode, donut = pie with hole, box = separate trace type that IS included in basic).

**Note on box plot:** Verify that `plotly.js-basic-dist-min` includes box plot trace type. If not, use `plotly.js-dist-min` (full bundle, ~2MB) or create a custom partial bundle. This needs validation during implementation.

**PlotlyChart component:**
```typescript
interface PlotlyChartProps {
  figureJson: string; // Raw JSON from sandbox
  theme: 'light' | 'dark';
  onChartReady?: () => void;
}
```

**DataCard integration:**
```
[Query Brief]
[Generated Code] (collapsible)
[Chart]              <-- NEW
[Data Table]
[Analysis]
[Follow-up Suggestions]
[Sources]
```

Chart appears above table in the collapsible content area. If no chart data exists, the section is hidden (existing behavior preserved).

**Complexity:** MEDIUM for DataCard integration (progressive rendering), LOW for PlotlyChart component.

### 5. Export (PNG/SVG)

**Implementation:**
```typescript
// In PlotlyChart component
const handleExport = (format: 'png' | 'svg') => {
  Plotly.downloadImage(plotRef.current, {
    format,
    width: 1200,
    height: 800,
    filename: `spectra-chart-${Date.now()}`,
  });
};
```

Two buttons below chart: "Download PNG" and "Download SVG", matching the existing CSV/Markdown download button pattern.

**Complexity:** LOW -- Plotly.js handles all the rendering.

### 6. Chart Type Switcher

**Compatibility mapping:**
```
Group A (x/y data): bar <-> line <-> scatter
Group B (distribution): histogram (standalone)
Group C (composition): pie <-> donut
Group D (statistical): box (standalone)
```

Users can only switch within a group. Switching between groups (e.g., bar -> pie) requires data restructuring and should trigger a re-prompt to the AI.

**UI:** Dropdown or segmented control showing only compatible types for the current chart.

**Implementation:** Modify `data[0].type` (and `data[0].mode` for scatter/line) in the figure JSON, then re-render. No backend call needed.

**Complexity:** MEDIUM -- the mapping logic is straightforward, but edge cases exist (what if the chart has multiple traces?).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| AI-selected chart type | HIGH | MEDIUM | P1 |
| Core chart types (bar, line, scatter) | HIGH | LOW | P1 |
| Distribution charts (histogram, box) | HIGH | LOW | P1 |
| Part-of-whole charts (pie, donut) | MEDIUM | LOW | P1 |
| Chart in DataCard | HIGH | MEDIUM | P1 |
| Automatic chart generation | HIGH | HIGH | P1 |
| Interactive charts (zoom, pan, hover) | HIGH | LOW | P1 |
| Chart titles and axis labels | HIGH | LOW | P1 |
| Figure JSON from sandbox | HIGH | MEDIUM | P1 |
| PNG export | HIGH | LOW | P1 |
| SVG export | MEDIUM | LOW | P1 |
| Dark mode chart theming | MEDIUM | MEDIUM | P2 |
| Chart type switcher | MEDIUM | MEDIUM | P2 |
| Hover tooltip formatting | MEDIUM | LOW | P2 |
| Responsive chart sizing | MEDIUM | LOW | P2 |
| Visualization Agent (separate module) | HIGH | MEDIUM | P1 |

**Priority key:**
- P1: Must have for v0.4 launch
- P2: Should have, add when possible (same milestone, after core)
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | ChatGPT | Julius AI | Spectra v0.3 | Spectra v0.4 Target |
|---------|---------|-----------|---------------|-------------------|
| Auto chart type selection | Yes | Yes | NO | Yes |
| Chart types available | 18+ (Matplotlib) | 29+ (Plotly) | NO | 7 (Plotly) |
| Interactive charts | No (static images) | Yes | NO | Yes (Plotly.js) |
| Chart + table together | No (one or other) | Limited | Table only | Yes (unified DataCard) |
| Auto-generate charts | Yes (always) | Yes (always) | NO | Yes (heuristic) |
| PNG export | Yes | Yes | NO | Yes |
| SVG export | No | No | NO | Yes |
| Chart type switching | No (re-prompt) | No (re-prompt) | NO | Yes (within groups) |
| Dark mode charts | Partial | Theme selection | NO | Yes (Nord palette) |
| Chart editor | No | No | NO | No (anti-feature) |
| 3D/geo charts | Yes | Yes | NO | No (future) |

**Key advantage:** Spectra's unified DataCard (chart + table + explanation) is more informative than any competitor's separated view. Combined with interactive Plotly.js charts (vs ChatGPT's static images) and SVG export, Spectra provides a more professional analytics experience.

---

## Architecture Decision: Code Generation vs JSON Specification

Two approaches exist for AI-generated charts:

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Code Generation** (recommended) | LLM generates Python Plotly code, sandbox executes, outputs `fig.to_json()` | Leverages existing sandbox infrastructure; full Plotly Express/Graph Objects power; consistent with Spectra's "generate code" paradigm | Extra sandbox execution; code may fail; needs Code Checker validation |
| **JSON Specification** | LLM generates Plotly JSON spec directly (like chat2plot) | No sandbox needed; safer (no code execution); faster | Limited expressiveness; LLM produces invalid JSON specs; loses Plotly Express convenience functions; diverges from Spectra's architecture |

**Decision: Code Generation** because:
1. Spectra already generates and executes Python code -- this is the core architecture
2. The existing Code Checker validates generated code
3. Plotly Express functions (`px.bar()`, `px.scatter()`) produce better defaults than hand-crafted JSON
4. E2B sandbox already has Plotly installed
5. `fig.to_json()` produces valid Plotly.js-compatible JSON reliably
6. Users can see the chart generation code in the DataCard (educational value)

---

## Sources

### High Confidence (Official docs, established patterns)
- Plotly JSON Chart Schema: https://plotly.com/chart-studio-help/json-chart-schema/
- Plotly Python Figure Structure: https://plotly.com/python/figure-structure/
- Plotly.js Static Image Export: https://plotly.com/javascript/static-image-export/
- react-plotly.js GitHub: https://github.com/plotly/react-plotly.js
- Plotly `to_json()` docs: https://plotly.github.io/plotly.py-docs/generated/plotly.io.to_json.html
- Plotly.js React Integration: https://plotly.com/javascript/react/
- E2B Chart Documentation: https://e2b.dev/docs/code-interpreting/create-charts-visualizations/interactive-charts

### Medium Confidence (Verified across multiple sources)
- Chat2Plot JSON spec approach: https://github.com/nyanp/chat2plot
- Julius AI visualization features: https://julius.ai/home/graph-maker
- Julius AI chart types: https://julius.ai/articles/types-of-charts-and-graphs
- ChatGPT data analysis: https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt
- AI visualization best practices: https://www.displayr.com/best-ai-data-visualization-chart-generators/
- PlotGen multi-agent pattern: https://arxiv.org/html/2502.00988v1
- react-plotly.js bundle optimization: https://community.plotly.com/t/how-can-i-reduce-bundle-size-of-plotly-js-in-react-app/89910
- Chart vs table decision heuristics: https://www.synergycodes.com/blog/chart-vs-table-vs-graph-which-one-to-use-and-when
- Plotly Python-to-JS JSON flow: https://community.plotly.com/t/how-to-convert-python-json-object-to-plot-in-plotly-js-in-react/68797

### Low Confidence (Single-source, verify during implementation)
- LLM visualization agent architecture: https://medium.com/firebird-technologies/building-an-agent-for-data-visualization-plotly-39310034c4e9
- Plotly.js SVG export free vs subscription: Verify that `Plotly.toImage(gd, {format:'svg'})` works without subscription in the open-source JS library (not Chart Studio)
- `plotly.js-basic-dist-min` includes box plot trace type: Verify during npm install
- E2B sandbox has Plotly pre-installed: Verify with E2B docs or test execution

---
*Feature research for: AI-generated data visualization (v0.4)*
*Researched: 2026-02-12*
