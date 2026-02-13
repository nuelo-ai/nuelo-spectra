# Project Research Summary

**Project:** Spectra - AI-powered data analytics platform
**Domain:** Data Visualization (v0.4) - AI-generated interactive Plotly charts
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Spectra v0.4 adds AI-generated data visualization by introducing a 6th agent (Visualization Agent) that generates Plotly chart code executed in the E2B sandbox. The architecture leverages the existing code generation pipeline: the Visualization Agent produces Python code that creates Plotly figures and outputs JSON via `fig.to_json()`, which streams to the frontend for client-side rendering with plotly.js. This JSON-over-the-wire pattern avoids server-side image generation entirely—no Kaleido, no Chrome dependencies, no iframe security concerns.

The recommended approach is a **two-pass execution model**: first, the Coding Agent generates data analysis code (existing flow unchanged), then the Visualization Agent conditionally generates chart code if appropriate. The Data Analysis Agent determines visualization intent based on user queries and data suitability, following an "err on the side of showing charts" policy. Charts render as interactive Plotly.js components within the existing DataCard structure, positioned between the data table and analysis explanation.

The critical risk is **over-engineering the integration**. The existing pipeline (Manager → Coding → Code Checker → Execute → Data Analysis → Response) works well. Visualization must extend, not rewrite. The allowlist needs `plotly` added (1-line change), the sandbox output parser needs to capture chart JSON (20 lines), and the frontend needs a lazy-loaded PlotlyChart component (30 lines). The complexity is in prompt engineering—ensuring the LLM selects appropriate chart types and handles edge cases—not in architectural rewrites.

## Key Findings

### Recommended Stack

**Backend additions:** Zero new Python dependencies. Plotly 6.0.1 is pre-installed in E2B sandbox. The Visualization Agent uses existing `langchain-core` and `langgraph` patterns. The only change is adding `plotly` to `allowlist.yaml`.

**Frontend additions:** One new npm package (`plotly.js-dist-min` ~1MB gzipped). Avoid the outdated `react-plotly.js` wrapper (last updated 3 years ago); instead, use a custom 30-line component with `Plotly.newPlot()` and React `useRef`/`useEffect`.

**Core technologies:**
- **Plotly (Python)**: Chart generation in sandbox—pre-installed, no pip install needed
- **plotly.js (JavaScript)**: Client-side rendering + PNG/SVG export—`Plotly.downloadImage()` handles image export without server involvement
- **JSON transport**: `fig.to_json()` produces 5-10KB payloads vs 3MB HTML strings—enables interactivity, theming, and type safety

**Critical decision:** Client-side export via `Plotly.downloadImage()` instead of server-side Kaleido. Kaleido v1.0 requires Chrome (not in E2B sandbox), has 50x performance regression, and Docker sandbox conflicts. Client-side export is instant, works offline, and requires no infrastructure.

### Expected Features

**Must have (table stakes):**
- AI-selected chart types (bar, line, scatter, histogram, box, pie, donut)—users expect "show me sales trends" to produce a line chart without specifying type
- Charts rendered in DataCard above table—visual insight first, exact values in table second
- Interactive charts (zoom, pan, hover tooltips)—Plotly.js provides this by default, static images feel dated
- PNG/SVG export—download buttons below chart, browser-side via `Plotly.downloadImage()`
- Chart titles and axis labels—prompt engineering ensures meaningful labels, not raw column names
- Automatic chart generation—AI decides when visualization adds value (not every query needs a chart)

**Should have (competitive):**
- SVG export—higher quality than PNG for print and presentations (ChatGPT only exports PNG)
- Dark mode chart theming—charts respect Spectra's light/dark toggle with transparent backgrounds and theme-aware colors
- Chart + table + analysis unified in one DataCard—competitors show either chart OR table, Spectra shows both
- Visualization Agent as separate 6th agent—specialized prompt for chart quality without polluting the Coding Agent's analysis focus

**Defer (v2+):**
- Chart type switcher (bar ↔ line ↔ scatter)—nice-to-have after core charts work
- Advanced chart types (heatmap, 3D, geo maps)—add based on user demand, each adds ~500KB to bundle
- Chart persistence in database—currently transient (regenerated on query re-run), defer to `metadata_json` storage optimization

### Architecture Approach

The Visualization Agent integrates as a **conditional post-processing node** after `da_response` in the LangGraph graph. It does NOT execute code itself—it generates Plotly Python code, which the `viz_execute` node runs in E2B sandbox. This mirrors the existing Coding Agent → Code Checker → Execute pattern, maintaining separation of code generation from code execution.

**Major components:**
1. **Visualization Agent** (`visualization.py`)—LLM generates Plotly code from `execution_result`, user query, and chart hint; embeds data as Python literal (no file upload needed)
2. **Viz Execute Node** (`viz_execute_node` in `graph.py`)—lightweight E2B sandbox call (~1-2s); parses chart JSON from stdout; non-fatal errors (chart failure doesn't lose analysis)
3. **ChartRenderer Component** (`ChartRenderer.tsx`)—dynamic import (no SSR), custom wrapper with `Plotly.newPlot()`, responsive sizing, theme overrides

**Data flow:** Coding Agent produces tabular data → Data Analysis Agent interprets → decides visualization appropriate → Visualization Agent generates chart code → E2B executes → chart JSON streams via SSE → DataCard renders Plotly.js chart above table.

**State schema changes:** 5 new fields on `ChatAgentState` (all additive, backward compatible): `visualization_requested`, `chart_hint`, `chart_code`, `chart_specs`, `chart_error`.

### Critical Pitfalls

1. **Plotly blocked by AST allowlist**—Current `allowlist.yaml` only permits pandas/numpy. The Code Checker rejects `import plotly` with "Module not in allowlist." This causes 100% failure rate for chart generation. **Prevention:** Add `plotly` to `allowed_libraries` in `allowlist.yaml` before any visualization work.

2. **Sandbox output pipeline cannot capture chart artifacts**—Current pipeline parses `{"result": ...}` from stdout. Plotly Figure objects are not JSON serializable. **Prevention:** Visualization Agent code must end with `print(json.dumps({"chart": json.loads(fig.to_json())}))`. Modify `execute_in_sandbox` to extract `chart` key from stdout JSON.

3. **LLM generates wrong chart type for data shape**—Research shows 15-30% of LLM-generated charts use incorrect types (pie chart for 20+ categories, line chart for unordered categorical data). **Prevention:** Heuristic guardrails in prompt (categorical >8 values → bar not pie; <3 data points → table not chart). Include unique value counts in agent context.

4. **plotly.js bundle bloats frontend (~3MB)**—Full Plotly.js adds 3MB to every page load. **Prevention:** Use `plotly.js-dist-min` partial bundle (~1MB). Lazy load with `dynamic(() => import('./PlotlyChart'), { ssr: false })`. Only load when chart data exists.

5. **Over-visualization**—Showing charts for every query creates "chart fatigue." A single scalar ("What is average revenue?") doesn't need a chart. **Prevention:** Data Analysis Agent decides `visualization_requested` based on query intent and data shape. Default to tables, opt-in to charts.

## Implications for Roadmap

Based on research, suggested phase structure follows a **dependency-aware build order**: state schema → output pipeline → agent integration → frontend rendering → polish.

### Phase 1: Infrastructure Preparation
**Rationale:** Allowlist and state schema are prerequisites for all other work. Cannot generate chart code if Plotly is blocked, cannot store chart data if state has no `chart_specs` field.

**Delivers:**
- `plotly` added to `allowlist.yaml`
- 5 new fields in `ChatAgentState` (`visualization_requested`, `chart_hint`, `chart_code`, `chart_specs`, `chart_error`)
- E2B Plotly verification (confirm 6.0.1 pre-installed)

**Addresses:** Pitfall #1 (allowlist blocking)

**Complexity:** LOW—config changes only, no code logic

### Phase 2: Output Pipeline Extension
**Rationale:** Chart JSON must flow from sandbox to frontend before any agent can produce it. The output contract dictates what the Visualization Agent generates.

**Delivers:**
- Modify `execute_in_sandbox` (graph.py) to parse `{"result": ..., "chart": ...}` from stdout
- Add `chart_specs` to SSE stream whitelist (agent_service.py)
- New `viz_execute_node` function (lightweight E2B sandbox call, non-fatal error handling)

**Addresses:** Pitfall #2 (output capture), Pitfall #6 (large JSON)

**Complexity:** MEDIUM—modifying existing stdout parsing requires careful testing

### Phase 3: Visualization Agent
**Rationale:** With infrastructure ready and output pipeline extended, the agent can generate chart code that will be captured correctly.

**Delivers:**
- New `visualization.py` agent module with chart type selection heuristics
- New `visualization` entry in `prompts.yaml` (LLM config + system prompt)
- Chart code generation with embedded data (no file uploads)

**Addresses:** Pitfall #3 (wrong chart type), Pitfall #10 (prompt conflicts)

**Complexity:** HIGH—prompt engineering for chart type selection is the core UX challenge

### Phase 4: Graph Integration
**Rationale:** Wire the Visualization Agent into LangGraph as conditional post-processing after `da_response`.

**Delivers:**
- Add `visualization_agent`, `viz_execute`, `viz_response` nodes to graph
- Add `should_visualize()` conditional edge function
- Modify `da_response_node` to detect visualization intent (set `visualization_requested` flag)
- Change `da_response` from finish point to conditional routing

**Addresses:** Pitfall #5 (over-visualization), Pitfall #11 (DA Agent misinterprets chart JSON)

**Complexity:** MEDIUM—routing changes in existing graph, but non-breaking (tabular flow unchanged)

### Phase 5: Frontend Chart Rendering
**Rationale:** Backend produces chart JSON; frontend must render it interactively in DataCard.

**Delivers:**
- `npm install plotly.js-dist-min` (~1MB partial bundle)
- `ChartRenderer.tsx` component with dynamic import (no SSR)
- Add `chartSpecs` prop to `DataCard.tsx`, render chart section between table and analysis
- PNG/SVG download buttons via `Plotly.downloadImage()`

**Addresses:** Pitfall #4 (bundle size), Pitfall #7 (no chart section), Pitfall #9 (Kaleido fails)

**Complexity:** MEDIUM—lazy loading and dynamic import configuration

### Phase 6: Theme & UX Polish
**Rationale:** Core functionality works end-to-end; now refine visual integration.

**Delivers:**
- Dark mode chart theming (transparent backgrounds, theme-aware colors)
- Chart skeleton loader during streaming
- Responsive chart sizing (`useResizeHandler`)
- Chart-specific streaming events (`visualization_started`)

**Addresses:** Pitfall #8 (dark mode mismatch), Pitfall #14 (interactivity conflicts)

**Complexity:** LOW—CSS and config tweaks

### Phase 7: Multi-Chart & Edge Cases (Optional)
**Rationale:** Single chart is MVP; multi-chart (2-3 charts per response) is enhancement.

**Delivers:**
- Multi-chart output contract (`{"charts": [chart1, chart2]}`)
- Tabbed or carousel layout in DataCard for multiple charts
- Chart type switcher (bar ↔ line ↔ scatter within same data shape)

**Addresses:** Pitfall #13 (layout chaos)

**Complexity:** MEDIUM—UI design for multi-chart layout

### Phase Ordering Rationale

- **Infrastructure before agents:** Cannot generate code if allowlist blocks it; cannot store data if state lacks fields
- **Output pipeline before agent creation:** The agent generates what the pipeline expects; pipeline design dictates agent output format
- **Backend before frontend:** Frontend needs SSE events with chart JSON; those events must exist before frontend can consume them
- **Core features before polish:** Dark mode and multi-chart are enhancements on top of single-chart functionality
- **Non-blocking phases:** Phase 6 (polish) and Phase 7 (multi-chart) can be deferred if timeline is tight—core value is in Phases 1-5

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (Visualization Agent):** Chart type selection heuristics need validation with real user queries. The prompt must handle ambiguous cases ("show me sales" could be bar, line, or pie depending on data). Consider A/B testing different prompt strategies.
- **Phase 7 (Multi-Chart):** UI/UX for multi-chart layout is underspecified. Tabs vs. carousel vs. vertical stack needs user testing.

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Config changes follow existing patterns (allowlist has precedent, state schema is TypedDict extension)
- **Phase 2:** Stdout parsing modification uses existing `execute_in_sandbox` patterns
- **Phase 5:** Dynamic import and lazy loading are well-documented Next.js patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Plotly 6.0.1 verified pre-installed in E2B via DeepWiki. plotly.js bundle sizes confirmed via npm. Client-side export verified in plotly.js source code. |
| Features | MEDIUM-HIGH | Table stakes derived from ChatGPT/Julius AI competitive analysis. Chart type list (7 types) confirmed supported by `plotly.js-basic-dist-min`. SVG export confirmed in plotly.js source (despite misleading docs). |
| Architecture | HIGH | JSON-over-the-wire pattern is proven (Dash uses it internally). Two-pass execution aligns with existing Coding Agent → Execute flow. Direct codebase analysis with line-number references confirms integration points. |
| Pitfalls | HIGH | Allowlist blocking verified in `code_checker.py` AST validation. stdout capture limitations confirmed in `graph.py`. LLM chart type errors validated by academic research (Drawing Pandas benchmark, 15-30% failure rate). Bundle size verified via plotly.js releases. |

**Overall confidence:** HIGH

### Gaps to Address

- **Chart type selection prompt quality:** The heuristics (categorical >8 values → bar not pie) are derived from research, but need validation with real Spectra queries. Plan for prompt iteration in Phase 3.
- **Multi-chart UI/UX:** Milestone says "2-3 charts to show different perspectives," but does not specify layout. Tabs? Carousel? Vertical stack? This needs product decision before Phase 7 implementation.
- **Chart persistence:** Currently chart JSON is transient (regenerated on query re-run). If users want to bookmark/share specific charts, `metadata_json` storage is needed. Defer decision to post-v0.4 based on usage patterns.
- **Edge case handling:** What if execution_result has 10,000 rows? The Visualization Agent prompt must include data aggregation instructions ("limit to top 20 items"). This is addressed in STACK.md but needs enforcement in prompt.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `graph.py`, `state.py`, `coding.py`, `code_checker.py`, `data_analysis.py`, `allowlist.yaml`, `prompts.yaml`, `DataCard.tsx` (line-number references throughout research files)
- [E2B Code Interpreter Sandbox Environment](https://deepwiki.com/e2b-dev/code-interpreter/2.1-sandbox-environment)—Pre-installed packages list confirms Plotly 6.0.1
- [plotly.js source: toimage.js](https://github.com/plotly/plotly.js/blob/master/src/snapshot/toimage.js)—Confirms SVG export in open-source (format: 'png' | 'jpeg' | 'webp' | 'svg')
- [Plotly Python to_json docs](https://plotly.github.io/plotly.py-docs/generated/plotly.io.to_json.html)—JSON export API
- [react-plotly.js GitHub](https://github.com/plotly/react-plotly.js)—Factory pattern for partial bundles

### Secondary (MEDIUM confidence)
- [Drawing Pandas: LLM Plotting Code Benchmark (arxiv 2412.02764)](https://arxiv.org/html/2412.02764v1)—15-30% chart type selection errors, LLMs underperform with Plotly vs Matplotlib
- [Are LLMs Ready for Visualization? (arxiv 2403.06158)](https://arxiv.org/html/2403.06158v1)—LLMs struggle with Plotly, chart type selection heuristics needed
- [Building a Data Visualization Agent with LangGraph](https://blog.langchain.com/data-viz-agent/)—Multi-agent patterns for visualization
- [Kaleido GitHub Issue #379](https://github.com/plotly/Kaleido/issues/379)—Docker sandbox-in-sandbox failures
- [Kaleido GitHub Issue #400](https://github.com/plotly/Kaleido/issues/400)—50x performance regression in v1.0

### Tertiary (LOW confidence, verify during implementation)
- [plotly.js-basic-dist-min bundle composition](https://community.plotly.com/t/how-can-i-reduce-bundle-size-of-plotly-js-in-react-app/89910)—Community forum confirms basic bundle includes bar, scatter, pie, line; verify box plot inclusion during npm install
- [E2B auto-detection for charts](https://e2b.dev/docs/code-interpreting/create-charts-visualizations/interactive-charts)—E2B only auto-detects matplotlib, NOT Plotly (Plotly requires explicit JSON output)

---
*Research completed: 2026-02-12*
*Ready for roadmap: yes*
