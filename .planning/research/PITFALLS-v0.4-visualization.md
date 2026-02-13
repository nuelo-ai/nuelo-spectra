# Domain Pitfalls: v0.4 Data Visualization (AI-Generated Charts)

**Domain:** AI-generated data visualization via Plotly, integrated into existing LangGraph agent pipeline
**Researched:** 2026-02-12
**Confidence:** HIGH (derived from direct codebase analysis, verified Plotly/E2B documentation, and academic research on LLM visualization generation)

**Context:** Spectra v0.4 adds a Visualization Agent that generates Plotly chart code. The system already has a working pipeline: Manager Agent routes queries to Coding Agent, Code Checker validates, E2B sandbox executes, Data Analysis Agent interprets results. The frontend renders DataCards with tables and explanations. Visualization must integrate into this existing pipeline without breaking the current tabular data flow. The key challenge: the system was designed for structured JSON output (`print(json.dumps({"result": result}))`), not for chart HTML/JSON artifacts.

---

## Critical Pitfalls

Mistakes at this level cause the visualization feature to be fundamentally broken, require rewrites of the output pipeline, or degrade the existing tabular analysis.

### Pitfall 1: Plotly Blocked by AST Code Checker Allowlist

**What goes wrong:**
The current `allowlist.yaml` (see `backend/app/config/allowlist.yaml`) only permits: `pandas`, `numpy`, `datetime`, `math`, `statistics`, `collections`, `itertools`, `functools`, `re`, `json`. Plotly is NOT in this list. When the Visualization Agent generates code like `import plotly.express as px`, the Code Checker's AST validation (see `code_checker.py` line 75-76) will reject it with "Module not in allowlist: plotly". The code will never reach the sandbox. The retry loop will attempt to regenerate code 3 times, each time including `import plotly`, and each time failing with the same allowlist error -- burning all retries on an impossible validation.

**Why it happens:**
The allowlist was designed for tabular data analysis where only pandas/numpy are needed. Adding visualization was not anticipated. The Code Checker does not have a concept of "visualization mode" where different imports are allowed.

**Consequences:**
- 100% failure rate for any chart generation request
- 3 wasted LLM calls (coding retries) plus 3 wasted LLM calls (code checker) per failed attempt = 6 LLM calls consumed with no result
- User sees cryptic error: "Unable to generate valid code after 3 attempts. Errors: Module not in allowlist: plotly"
- Users will think the feature is broken

**Prevention:**
1. Add `plotly` to `allowed_libraries` in `allowlist.yaml`
2. Do NOT add it as a blanket allowlist entry -- consider a scoped approach: the Code Checker should accept `plotly` imports only when the routing decision indicates visualization is requested
3. If scoped: extend the `RoutingDecision` model with a `requires_visualization: bool` field, and pass this to the code checker as context
4. If unscoped (simpler): just add `plotly` to the allowlist. The E2B sandbox is the real security boundary, and Plotly is safe (no filesystem/network access)

**Detection:**
- Ask "Show me a bar chart of sales by region". If the response is "Unable to generate valid code" with allowlist errors, this pitfall is active
- Check LangSmith traces: look for `code_checker` node returning INVALID with "Module not in allowlist: plotly"

**Severity:** CRITICAL
**Phase to address:** First phase -- allowlist update is a prerequisite for any visualization work

---

### Pitfall 2: Sandbox Output Pipeline Cannot Capture Chart Artifacts

**What goes wrong:**
The current `execute_in_sandbox` function (see `graph.py` lines 276-514) captures execution output by parsing JSON from stdout: it looks for `print(json.dumps({"result": result}))` output and returns the parsed `result` value as `execution_result`. Plotly charts are NOT stdout-friendly. A Plotly figure cannot be meaningfully represented as `json.dumps({"result": fig})` -- calling `json.dumps` on a Plotly Figure object will fail with `TypeError: Object of type Figure is not JSON serializable`.

The current output pipeline has exactly two capture paths:
1. **stdout parsing** (graph.py lines 454-470): Looks for JSON in last stdout line
2. **results list** (graph.py line 472): Falls back to `str(result.results)` -- but E2B's `results` only auto-detects matplotlib charts, NOT Plotly figures (confirmed in E2B documentation)

Neither path can capture a Plotly chart. The Visualization Agent must explicitly serialize the chart to a transmittable format (HTML string or JSON spec) and print it to stdout, which the sandbox capture pipeline must then handle differently than tabular results.

**Why it happens:**
The entire output contract was designed for `json.dumps({"result": tabular_data})`. Chart artifacts (HTML strings or JSON specs) are structurally different: they can be megabytes in size, contain nested objects, and represent visual layouts rather than data tables.

**Consequences:**
- Chart code executes successfully in the sandbox but produces no usable output
- The Data Analysis Agent receives empty or garbled `execution_result` and generates a confused interpretation
- The frontend DataCard receives no chart data to render
- Users see "Code executed successfully (no output)" or a mangled string representation of a Figure object

**Prevention:**
Two viable approaches (choose one):

**Option A: Plotly JSON spec via stdout (RECOMMENDED)**
1. The Visualization Agent's generated code must end with:
   ```python
   import plotly.io as pio
   chart_json = pio.to_json(fig)
   print(json.dumps({"result": result_data, "chart": json.loads(chart_json)}))
   ```
2. Modify `execute_in_sandbox` to detect and extract the `chart` key from the output JSON
3. Store chart JSON in a new `chart_data` field on `ChatAgentState`
4. The frontend renders chart JSON using `react-plotly.js` (pure client-side rendering)

**Option B: Plotly HTML via stdout**
1. Generate HTML fragment with `fig.to_html(full_html=False, include_plotlyjs=False)`
2. Print HTML as part of the JSON output: `print(json.dumps({"result": result_data, "chart_html": html_string}))`
3. Frontend renders in a sandboxed iframe with `srcDoc`

**Why Option A is better:**
- JSON spec is smaller than HTML (no embedded data duplication)
- `react-plotly.js` provides native React integration (responsive, interactive, themeable)
- No iframe security concerns (CSP, sandbox attributes)
- Chart can be re-themed to match dark/light mode
- Chart data can be inspected/modified by the frontend

**Detection:**
- Generate a chart and inspect the `execution_result` field in the database `chat_messages.metadata_json`. If it contains a stringified Figure object or is empty, the capture pipeline is broken
- Check E2B execution logs: the stdout should contain valid JSON with a `chart` key

**Severity:** CRITICAL
**Phase to address:** Pipeline modification phase -- must be designed before the Visualization Agent can produce any output

---

### Pitfall 3: LLM Generates Wrong Chart Type for Data Shape

**What goes wrong:**
Academic research confirms this is the most common LLM visualization failure. Studies show LLMs produce incorrect chart types in 15-30% of cases (Drawing Pandas benchmark, 2024). Specific failure modes observed in research:

- **Pie chart for too many categories:** LLM generates a pie chart with 20+ slices, making it unreadable (should be a bar chart)
- **Line chart for unordered categorical data:** LLM draws a line chart connecting categorical values ("North", "South", "East") as if they are a time series
- **Scatter plot when data has only 2-3 points:** LLM generates a scatter plot with 3 dots, which conveys no information (should be a bar chart or table)
- **Stacked bar for unrelated categories:** LLM stacks values that should not be compared (e.g., revenue and customer count)
- **Time series without sorting by date:** Line chart connects points in arbitrary order, creating a zigzag

**Why it happens:**
LLMs are pattern-matching from training data. They associate keywords with chart types ("trend" -> line chart, "distribution" -> histogram) without analyzing whether the data actually fits. The LLM does NOT see the actual data values -- it only sees column names, types, and sample rows from `data_profile`. This metadata is insufficient to make correct chart type decisions in ambiguous cases.

Additionally, research confirms LLMs perform worse with Plotly than with Matplotlib/Seaborn because Plotly is less represented in training data (arxiv: 2403.06158v1, arxiv: 2412.02764v1).

**Consequences:**
- Misleading visualizations that misrepresent data patterns
- User trust erosion: a single bad chart makes users doubt all subsequent charts
- Users must manually request corrections ("No, show this as a bar chart instead")
- Over time, users may stop using the visualization feature

**Prevention:**
1. **Chart type recommendation in two stages:** First, the Visualization Agent proposes a chart type with reasoning. Second, it generates the code. This allows the Data Analysis Agent to sanity-check the choice
2. **Heuristic guardrails before LLM code generation:**
   - Categorical columns with >8 unique values: bar chart (not pie)
   - Exactly 2 numeric columns: scatter plot
   - One date/time column + one numeric: line chart (ensure date sorting)
   - Single numeric column: histogram
   - Fewer than 3 data points: suggest table instead of chart
3. **Include data shape hints in the prompt:** "This column has 45 unique values" is more useful than just "dtype: string". Add unique value counts from `data_profile` to the Visualization Agent's context
4. **Provide chart type override:** Allow users to say "show as bar chart" to correct wrong selections

**Detection:**
- Create a test suite of 10 common data shapes (2 categories, 20 categories, time series, single values) and verify correct chart type selection
- Log chart types chosen by the LLM and review for patterns of misselection

**Severity:** CRITICAL
**Phase to address:** Visualization Agent prompt engineering phase -- chart type selection logic must be embedded in the prompt and optionally backed by heuristic pre-processing

---

### Pitfall 4: plotly.js Bundle Size Bloats Frontend (~3MB)

**What goes wrong:**
The full `plotly.js` library is approximately 3.5MB minified (6MB unminified). If using `react-plotly.js` with the default import, Webpack/Next.js bundles the entire library into the client-side JavaScript bundle. This means:

- First page load increases by 3MB+ of JavaScript
- Time to Interactive (TTI) increases by 2-4 seconds on average connections
- Mobile users on slow networks may wait 5-10 seconds for the page to become interactive
- This happens even if the user never views a chart -- the library loads on every page visit

The existing Spectra frontend uses Next.js, which does code splitting by default at the page level. But if `react-plotly.js` is imported in `DataCard.tsx` (which renders on every chat message), Plotly will be loaded for every user on every page.

**Why it happens:**
`react-plotly.js` defaults to importing the full `plotly.js` bundle. The library supports partial bundles (e.g., `plotly.js-basic-dist-min` at ~1MB with bar, scatter, pie), but this is not the default behavior and requires explicit configuration.

**Consequences:**
- 3MB+ increase in initial page load for ALL users (not just those viewing charts)
- Lighthouse performance score drops significantly
- Mobile users experience noticeable delay
- Existing table-only DataCards load slower due to the chart library being in the same bundle

**Prevention:**
1. **Use a partial bundle:** Import `plotly.js-basic-dist-min` (~1MB) instead of full `plotly.js`. This includes bar, scatter, pie, and line -- exactly the chart types in milestone-04-req.md. Use `createPlotlyComponent` from `react-plotly.js` to wire the partial bundle:
   ```typescript
   import Plotly from 'plotly.js-basic-dist-min';
   import createPlotlyComponent from 'react-plotly.js/factory';
   const Plot = createPlotlyComponent(Plotly);
   ```
2. **Lazy load the chart component:** Use Next.js `dynamic()` with `ssr: false` to load the chart component only when a chart is actually present in a DataCard:
   ```typescript
   const PlotlyChart = dynamic(() => import('./PlotlyChart'), { ssr: false });
   ```
3. **Never import plotly.js at the top level of DataCard.tsx** -- only import it conditionally when `chart_data` exists in the message metadata
4. **Verify bundle size:** After integration, run `npx next build --analyze` and check that plotly.js is in a separate chunk, not in the main bundle

**Detection:**
- Run `npx next build` and check `.next/static/chunks` for plotly-related chunks larger than 1.5MB
- Compare Lighthouse scores before and after adding Plotly

**Severity:** CRITICAL
**Phase to address:** Frontend chart rendering phase -- lazy loading must be configured from the start, not retrofitted

---

## Moderate Pitfalls

### Pitfall 5: Over-Visualization -- Generating Charts When Tables Are More Appropriate

**What goes wrong:**
Once the Visualization Agent exists, the system may default to generating charts for every query, including ones where a simple table is more appropriate. Specific cases where charts are worse than tables:

- **Exact value lookup:** "What was the revenue for Q3?" -- a single number needs no chart
- **Precise comparisons:** "Show me the top 5 products by sales" -- a table with exact values is more useful than a bar chart where values must be estimated by eye
- **Many columns, few rows:** A table with 8 columns and 3 rows is clearer than any chart
- **Boolean or status data:** "Which files have been processed?" -- a status table, not a pie chart

If the system shows a chart for every query, users will experience "chart fatigue" and lose trust in the AI's judgment.

**Why it happens:**
The Visualization Agent's existence biases the system toward visualization. Without explicit "when NOT to visualize" rules, the Manager Agent or Visualization Agent will default to its primary function: making charts.

**Prevention:**
1. **Add a VISUALIZATION routing decision to the Manager Agent:** Extend the routing to include `VISUALIZATION` as a fourth route, separate from `NEW_ANALYSIS`. The Manager Agent decides whether visualization is appropriate based on query intent:
   - "Show me a chart of..." -> VISUALIZATION
   - "What is the total..." -> NEW_ANALYSIS (tabular)
   - "Compare trends..." -> VISUALIZATION (but only if temporal data exists)
2. **Default to tables, opt-in to charts:** The system should generate tables by default and only add charts when:
   - User explicitly requests a chart ("chart", "plot", "visualize", "graph")
   - The data shape strongly suggests visualization (time series, distribution, comparison of 3-7 categories)
3. **Allow both:** For queries that benefit from visualization, return BOTH the table AND the chart in the DataCard. Let the user see exact numbers in the table and patterns in the chart
4. **Never chart scalar results:** If the execution result is a single value, dictionary with <3 keys, or a list with <2 items, never generate a chart

**Detection:**
- Ask "What is the average revenue?" -- if a chart appears, the system is over-visualizing
- Ask "Show me sales by region" with only 2 regions -- a table is arguably better than a bar chart with 2 bars

**Severity:** MODERATE
**Phase to address:** Manager Agent routing update phase -- must be decided before the Visualization Agent's prompt is written

---

### Pitfall 6: Chart HTML/JSON Output Exceeds stdout Capture Buffer

**What goes wrong:**
The current stdout parsing in `execute_in_sandbox` (graph.py lines 454-470) iterates through `result.stdout` (a list of strings) and tries to find JSON. A Plotly figure serialized to JSON via `pio.to_json(fig)` can be 50KB-500KB+ depending on data points. When printed to stdout in the E2B sandbox, this large JSON blob is captured as one or more stdout lines. Potential issues:

- E2B may split large stdout across multiple list items, breaking JSON parsing
- The reverse iteration looking for JSON (graph.py line 459: `for line in reversed(result.stdout)`) may not find the complete JSON if it is split
- Very large charts with many data points (e.g., scatter plot with 10,000 points) produce JSON that is 5MB+, which may exceed E2B's stdout buffer or cause timeout during serialization

**Why it happens:**
The stdout capture was designed for small JSON payloads (tabular results are typically <10KB). Chart JSON is 10-100x larger because it includes all data points duplicated in the figure specification (once in the data traces, once in layout annotations).

**Prevention:**
1. **Limit chart data points:** In the Visualization Agent's prompt, instruct the LLM to aggregate or sample data before charting. A bar chart of "sales by region" needs 5-10 data points, not 50,000 raw rows
2. **Use Plotly JSON spec, not HTML:** `pio.to_json(fig)` is significantly smaller than `fig.to_html()`. A JSON spec for a bar chart with 10 bars is ~5-10KB. The equivalent HTML with embedded plotly.js is ~3MB
3. **Cap the output:** Add a size check in `execute_in_sandbox` -- if stdout exceeds 1MB, truncate and return an error suggesting data aggregation
4. **Separate chart and data output:** Instead of embedding chart JSON inside the result JSON, write the chart spec to a file in the sandbox and read it back via `sandbox.files.read()`. This avoids stdout buffer issues entirely
5. **Verify E2B stdout behavior:** Test with a sandbox that prints 500KB to stdout and confirm all content is captured in `execution.logs.stdout`

**Detection:**
- Generate a scatter chart with 5,000+ data points. If the chart JSON is truncated or missing, the buffer is overflowing
- Check E2B execution logs for incomplete stdout capture

**Severity:** MODERATE
**Phase to address:** Pipeline modification phase -- the output contract must handle large payloads

---

### Pitfall 7: Frontend DataCard Has No Chart Section -- Visual Integration Gap

**What goes wrong:**
The current `DataCard` component (see `frontend/src/components/chat/DataCard.tsx`) has three sections:
1. Query Brief (header, always visible)
2. Data Table (via `DataTable` component)
3. AI Explanation (markdown-rendered analysis)

There is no fourth section for charts. The `DataCardProps` interface does not include any chart-related props. The `ChatMessage.tsx` component passes `tableData` and `explanation` to DataCard but has no concept of chart data.

Adding a chart section requires:
- New prop on `DataCardProps` (e.g., `chartData?: PlotlyJSON`)
- New rendering section between table and explanation (or between query brief and table)
- Conditional rendering: show chart section only when chart data exists
- The chart must be responsive and fit within the DataCard's constrained width
- Skeleton loader for chart during streaming (like the existing table/explanation skeletons)
- Chart + table + explanation must coexist without the DataCard becoming excessively tall

**Why it happens:**
The DataCard was designed for tabular output. Visualization was a future milestone (v0.4) and was not architecturally accommodated in the component.

**Prevention:**
1. Add `chartData` prop to `DataCardProps` with type matching Plotly's JSON spec (`{ data: PlotlyData[]; layout: Partial<PlotlyLayout> }`)
2. Place the chart section between "Data Results" and "Analysis" -- this matches the natural reading order: see the data, see the visual, read the interpretation
3. Wrap the chart in a responsive container that respects DataCard's max width
4. Add a chart-specific skeleton loader for streaming state
5. When both table and chart are present, consider adding toggle tabs: "Table | Chart" to reduce vertical height
6. Add a "Download as Image" button below the chart (milestone-04-req.md requirement)

**Detection:**
- Render a DataCard with chart data. If the chart overflows the card boundaries, is not responsive, or crashes the component, the integration is incomplete

**Severity:** MODERATE
**Phase to address:** Frontend chart rendering phase

---

### Pitfall 8: Chart Theme Mismatch with Dark Mode

**What goes wrong:**
Plotly charts have their own theming system (`plotly`, `plotly_dark`, `plotly_white`, `ggplot2`, etc.). If the Visualization Agent generates a chart with the default Plotly theme (white background, blue traces) and the user is in dark mode, the chart will be a jarring white rectangle inside a dark DataCard. Conversely, if the LLM generates a dark-themed chart and the user is in light mode, it will look wrong.

The problem is compounded because the chart theme is set at code generation time (in the sandbox), but the display theme is a frontend concern that changes dynamically. The LLM cannot know the user's current theme.

**Why it happens:**
Plotly themes are embedded in the figure specification. Once the chart JSON is generated, the background color, text color, grid color, and trace colors are fixed. The frontend cannot override these without modifying the Plotly JSON spec.

**Prevention:**
1. **Generate theme-agnostic charts:** Instruct the Visualization Agent to always use `template="plotly_white"` with transparent background (`paper_bgcolor='rgba(0,0,0,0)'`, `plot_bgcolor='rgba(0,0,0,0)'`). This produces charts that work in both light and dark backgrounds
2. **Apply theme on the frontend:** When rendering with `react-plotly.js`, merge the chart JSON's layout with theme-appropriate overrides:
   ```typescript
   const themedLayout = {
     ...chartData.layout,
     paper_bgcolor: 'transparent',
     plot_bgcolor: 'transparent',
     font: { color: isDark ? '#e5e7eb' : '#1f2937' },
     xaxis: { ...chartData.layout.xaxis, gridcolor: isDark ? '#374151' : '#e5e7eb' },
     yaxis: { ...chartData.layout.yaxis, gridcolor: isDark ? '#374151' : '#e5e7eb' },
   };
   ```
3. **Never let the LLM hardcode colors:** The prompt should instruct the agent to NOT set explicit colors for traces -- let Plotly's default color sequence apply, and the frontend can override the sequence based on the theme
4. **Test both modes:** Every chart must be tested in both light and dark mode before the feature is considered complete

**Detection:**
- Switch to dark mode and view a chart. If the chart has a white background or unreadable text, the theme integration is broken

**Severity:** MODERATE
**Phase to address:** Frontend chart rendering phase -- must be part of the initial chart component design, not a post-hoc fix

---

### Pitfall 9: Kaleido (Image Export) Requires Chrome -- Breaks E2B Sandbox

**What goes wrong:**
Milestone-04-req.md requires: "User should be able to download the visualization as an image." The standard approach is Kaleido, Plotly's static image export library. However, Kaleido v1.0.0+ (released late 2025) requires Chrome to be installed. The E2B sandbox uses a minimal Firecracker microVM that does NOT include Chrome. If the Visualization Agent generates code using `fig.write_image("chart.png")`, it will fail with a Kaleido error about missing Chrome binary.

Even if Chrome were available in the sandbox, server-side image generation adds 2-5 seconds of execution time per chart, doubles E2B compute costs, and creates a binary file output that the current stdout-based pipeline cannot handle.

**Why it happens:**
Kaleido v1.0.0 dropped the bundled Chromium approach in favor of requiring system-installed Chrome. This is a breaking change from earlier versions that shipped with their own Chromium binary. The E2B sandbox does not have Chrome.

**Prevention:**
1. **Do NOT generate images in the sandbox.** This is not a sandbox concern -- it is a frontend concern
2. **Use client-side image export:** Plotly.js has built-in `Plotly.downloadImage()` and `Plotly.toImage()` functions that render to PNG/SVG directly in the browser using the Canvas API. No server-side rendering needed
3. **Add a "Download as PNG" button** to the chart section of the DataCard that calls:
   ```typescript
   import Plotly from 'plotly.js-basic-dist-min';
   Plotly.downloadImage(chartDiv, { format: 'png', width: 1200, height: 800, filename: 'chart' });
   ```
4. **Also offer SVG download** for users who need vector graphics
5. **Remove any Kaleido-related instructions from the Visualization Agent's prompt** -- the LLM should never generate `write_image()` code

**Detection:**
- If the generated code includes `fig.write_image()` or `import kaleido`, the prompt is wrong
- Test the frontend "Download as PNG" button and verify it produces a crisp image at 2x resolution

**Severity:** MODERATE
**Phase to address:** Frontend chart rendering phase (download button) + Visualization Agent prompt engineering (do not generate write_image code)

---

### Pitfall 10: Visualization Agent and Coding Agent Prompt Conflict

**What goes wrong:**
The current Coding Agent's system prompt (see `prompts.yaml` lines 62-113) enforces strict output rules:
- "End with: `print(json.dumps({"result": result}))`"
- "Use `.to_dict('records')` to get list of row dicts"
- "Return only code, no explanations"

These rules are designed for tabular analysis. If the Visualization Agent reuses or extends the Coding Agent, the output rules conflict:
- Chart code needs to serialize a Plotly figure, not a pandas DataFrame
- The output format needs a `chart` key alongside `result`
- Chart code often does NOT have a `result` variable -- the primary output IS the chart

If the Visualization Agent inherits the Coding Agent's prompt, the Code Checker (which validates against the coding prompt's rules) will reject chart code that does not end with `print(json.dumps({"result": result}))`.

**Why it happens:**
The Coding Agent's prompt and the Code Checker's validation rules are tightly coupled. Both assume tabular output. A visualization agent operating within the same pipeline will violate these assumptions.

**Consequences:**
- Code Checker rejects valid chart code because it does not have `print(json.dumps({"result": result}))`
- If the LLM tries to satisfy both chart generation AND the JSON output requirement, it produces convoluted code that wraps a figure in JSON incorrectly
- Retry loops burn through attempts trying to satisfy contradictory requirements

**Prevention:**
1. **Create a separate Visualization Agent** with its own system prompt and output contract. Do NOT extend the Coding Agent's prompt
2. **Define a visualization-specific output contract:**
   ```python
   # Visualization output contract:
   import json
   import plotly.io as pio
   chart_spec = json.loads(pio.to_json(fig))
   print(json.dumps({"result": result_data, "chart": chart_spec, "chart_type": "bar"}))
   ```
3. **Update the Code Checker to recognize visualization code:** The LLM logical check (stage 2 of code_checker_node) must know that visualization code has a different output format. Pass the routing decision to the Code Checker so it validates against the correct contract
4. **Consider two separate code checker prompts:** one for tabular analysis, one for visualization analysis

**Detection:**
- Generate chart code and check if the Code Checker rejects it with "Does not end with print(json.dumps(...))" -- if so, the prompt conflict is active

**Severity:** MODERATE
**Phase to address:** Visualization Agent creation phase -- the prompt and validation rules must be designed together

---

### Pitfall 11: Data Analysis Agent Misinterprets Chart Execution Results

**What goes wrong:**
The Data Analysis Agent (see `data_analysis.py`) receives `execution_result` (the stdout JSON) and interprets it. Its prompt (see `prompts.yaml` lines 190-234) is designed to interpret tabular data: "Interpret the code execution results." When the execution result contains a chart JSON spec alongside tabular data, the Data Analysis Agent may:

- Try to describe the chart spec as data ("The result contains 'data' with type 'bar' and x values...")
- Ignore the chart entirely and only analyze the tabular `result` key
- Generate analysis that contradicts what the chart shows (because it cannot "see" the chart)
- Produce follow-up suggestions for tabular operations ("Sort by X", "Filter by Y") when chart-specific suggestions would be better ("Change to line chart", "Add a trend line")

**Why it happens:**
The Data Analysis Agent has no concept of charts. Its prompt says "Interpret the code execution results" and provides the raw JSON output, which now includes a large chart spec object that is not human-readable tabular data.

**Prevention:**
1. **Strip chart spec from the Data Analysis Agent's input:** Before passing `execution_result` to the DA Agent, extract and remove the `chart` key. Pass only the `result` (tabular data) for interpretation
2. **Add chart awareness to the DA Agent's prompt:** Include a note like "A chart was generated of type [bar/line/pie/scatter]. Mention the visualization in your analysis and suggest chart-related follow-ups alongside data follow-ups"
3. **Pass chart metadata, not chart spec:** Tell the DA Agent "A bar chart showing sales by region was generated" rather than dumping the entire Plotly JSON
4. **Generate visualization-specific follow-up suggestions:** "Show this as a line chart instead", "Add a trend line", "Break down by quarter"

**Detection:**
- Generate a chart and read the analysis. If it says "The result contains data traces with x=[...] and y=[...]" instead of interpreting the actual data, the DA Agent is reading the chart spec

**Severity:** MODERATE
**Phase to address:** Data Analysis Agent update phase -- must be coordinated with the output pipeline changes

---

## Minor Pitfalls

### Pitfall 12: Generated Chart Code Uses Hardcoded Colors That Clash

**What goes wrong:**
LLMs frequently hardcode specific hex colors in Plotly code (`color='#FF5733'`, `marker_color=['red', 'blue', 'green']`). These colors may:
- Clash with Spectra's design system
- Be invisible or low-contrast in dark mode
- Not be colorblind-accessible
- Create inconsistent visual identity across different charts

**Prevention:**
1. Instruct the Visualization Agent to NEVER hardcode colors -- let Plotly's default color sequence apply
2. If custom colors are needed, define a Spectra color palette constant in the prompt and instruct the agent to use it
3. On the frontend, override `colorway` in the layout to use Spectra's brand colors:
   ```typescript
   layout.colorway = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'];
   ```

**Severity:** MINOR
**Phase to address:** Visualization Agent prompt engineering + frontend chart component

---

### Pitfall 13: Multiple Charts Per Response Creates Layout Chaos

**What goes wrong:**
Milestone-04-req.md states: "If needed, the agent can generate 2-3 charts to show different perspectives of the data." If the output contract supports only one chart, the Visualization Agent cannot return multiple charts. If it supports multiple charts, the DataCard must accommodate 2-3 charts stacked vertically, which makes the card excessively tall (each Plotly chart is ~300-400px tall). Three charts = 900-1200px of charts alone, plus table and analysis.

**Prevention:**
1. **Start with single chart per response.** Get the single-chart pipeline working first
2. **For multiple charts, use a tabbed or carousel layout** inside the DataCard: "Chart 1 of 3", with navigation arrows
3. **Define the multi-chart output contract** early even if you implement single chart first:
   ```python
   print(json.dumps({"result": data, "charts": [chart1_spec, chart2_spec]}))
   ```
4. **Limit to max 3 charts per response** in the prompt to prevent chart overload

**Severity:** MINOR
**Phase to address:** Later phase -- get single chart working first, then extend to multi-chart

---

### Pitfall 14: Chart Interactivity Conflicts with DataCard Collapse/Expand

**What goes wrong:**
DataCards use a `Collapsible` component with a `CollapsibleTrigger` (see `DataCard.tsx` lines 60-93). Clicking anywhere on the trigger area collapses/expands the card. If a Plotly chart is inside the collapsible content and the user hovers over it (to see tooltips), mouse events may bubble up to the Collapsible component and cause unexpected expand/collapse behavior. Additionally, Plotly's built-in toolbar (zoom, pan, save) creates clickable elements inside the card that may interfere with the card's own event handlers.

**Prevention:**
1. **Stop event propagation** on the chart container: `onClick={(e) => e.stopPropagation()}`
2. **Place the chart INSIDE CollapsibleContent** (not in the trigger area) so hover events do not conflict with collapse behavior
3. **Configure Plotly's modebar** to show only essential buttons: `config={{ displayModeBar: true, modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'] }}`
4. **Test touch interactions** on mobile: pinch-to-zoom on a chart should not trigger card collapse on mobile devices

**Severity:** MINOR
**Phase to address:** Frontend chart rendering phase

---

### Pitfall 15: E2B Sandbox Does Not Have Plotly Installed

**What goes wrong:**
The E2B sandbox uses a base image (`e2b-code-interpreter` template) that may or may not include Plotly. If Plotly is not installed in the sandbox, `import plotly` will fail with `ModuleNotFoundError`, even though the allowlist permits it. The error would appear as a sandbox execution failure, not a validation failure, and the retry loop would burn 3 attempts on the same import error.

**Why it happens:**
The E2B base image includes common data science libraries (pandas, numpy, matplotlib, seaborn) but Plotly is not guaranteed to be in the base image. Custom E2B templates can include additional packages, but the current Spectra configuration uses the default template (see `e2b_runtime.py` line 64-67: `Sandbox.create()` with no `template` argument).

**Prevention:**
1. **Verify Plotly availability** in the E2B sandbox by running a test execution: `sandbox.run_code("import plotly; print(plotly.__version__)")`
2. **If not available:** Create a custom E2B template with Plotly pre-installed. This requires E2B Pro plan and a Dockerfile/toml configuration
3. **Alternatively:** Add `pip install plotly` to the beginning of chart code. This adds ~5-10 seconds per execution but avoids custom template requirements
4. **Best approach:** Test once, and if Plotly is already available (likely in recent E2B images), document the version. If not, create a custom template

**Detection:**
- Run a test sandbox execution with `import plotly` and check the result

**Severity:** MINOR (likely already available, but must be verified)
**Phase to address:** First phase -- quick verification test before building any visualization code

---

### Pitfall 16: Streaming Events Pipeline Missing Chart-Specific Events

**What goes wrong:**
The current SSE streaming pipeline emits events at each stage: `coding_started`, `validation_started`, `execution_started`, `analysis_started`, `code_display`, `retry`, `completed`, `error`. There are no visualization-specific events. When a chart is being generated, the user sees the same generic status messages as for tabular analysis:

- "Generating code..." (user does not know it is chart code)
- "Executing..." (user does not know a chart is being rendered)
- "Analyzing..." (user does not know a chart will appear)

Without chart-specific streaming events, the DataCard skeleton loader shows the table skeleton when it should show a chart skeleton, and the user has no visual indication that a chart is coming.

**Prevention:**
1. Add `visualization_started` event emitted by the Visualization Agent node
2. Add `chart_generated` event in the execution node when chart output is detected
3. The frontend should show a chart-shaped skeleton loader when it receives `visualization_started`
4. The DataCard should conditionally show chart skeleton vs table skeleton based on the streaming event type
5. Include chart type in the event: `{"type": "visualization_started", "chart_type": "bar"}` so the skeleton can approximate the expected shape

**Severity:** MINOR (UX polish, not functional)
**Phase to address:** Final integration phase -- after the core pipeline works

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Severity | Mitigation |
|---|---|---|---|
| Allowlist + Sandbox Prep | Pitfall 1: Plotly blocked by AST allowlist | CRITICAL | Add plotly to allowlist.yaml |
| Allowlist + Sandbox Prep | Pitfall 15: Plotly not installed in E2B | MINOR | Verify with test execution |
| Output Pipeline | Pitfall 2: Cannot capture chart artifacts from sandbox | CRITICAL | New output contract with chart JSON key |
| Output Pipeline | Pitfall 6: Large chart JSON exceeds stdout buffer | MODERATE | Aggregate data before charting, cap output size |
| Visualization Agent | Pitfall 3: Wrong chart type selection | CRITICAL | Heuristic guardrails + two-stage chart type proposal |
| Visualization Agent | Pitfall 10: Prompt conflicts with Coding Agent | MODERATE | Separate prompt + validation rules for viz code |
| Visualization Agent | Pitfall 5: Over-visualization | MODERATE | Default to tables, opt-in to charts via routing |
| Frontend Chart Component | Pitfall 4: plotly.js 3MB bundle bloat | CRITICAL | Partial bundle + lazy loading + dynamic import |
| Frontend Chart Component | Pitfall 7: No chart section in DataCard | MODERATE | Add chartData prop and rendering section |
| Frontend Chart Component | Pitfall 8: Dark mode theme mismatch | MODERATE | Transparent background + frontend theme override |
| Frontend Chart Component | Pitfall 9: Kaleido fails in sandbox for image export | MODERATE | Client-side export via Plotly.downloadImage() |
| Frontend Chart Component | Pitfall 14: Chart interactivity vs collapse | MINOR | stopPropagation on chart container |
| Data Analysis Agent Update | Pitfall 11: DA Agent misinterprets chart JSON | MODERATE | Strip chart spec from DA input, pass metadata only |
| Multi-Chart Support | Pitfall 13: Multiple charts layout chaos | MINOR | Tabbed/carousel layout, start with single chart |
| Streaming/UX Polish | Pitfall 16: Missing chart-specific streaming events | MINOR | Add visualization_started and chart_generated events |
| All Phases | Pitfall 12: Hardcoded colors | MINOR | Prompt instructions + frontend colorway override |

---

## Integration Risk Assessment

The v0.4 visualization feature touches every layer of the stack, but unlike v0.3 (which restructured the foundation), v0.4 **extends** the existing pipeline. The core flow (Manager -> Coding -> Checker -> Execute -> DA -> Response) remains intact. The risk is in the **extension points**: new output formats, new agent prompts, new frontend components, and new validation rules.

| Layer | Current State | v0.4 Change | Risk Level |
|---|---|---|---|
| Allowlist | Plotly not permitted | Add plotly to allowlist | LOW -- simple config change |
| Agent State | No chart fields | Add chart_data, chart_type fields | LOW -- additive, no breaking changes |
| Output Pipeline | JSON tabular only | JSON tabular + chart spec | HIGH -- stdout parsing must handle both formats |
| Coding Agent | Generates table code | New Visualization Agent generates chart code | MODERATE -- separate agent, but shares pipeline |
| Code Checker | Validates table output rules | Must validate chart output rules too | MODERATE -- routing-aware validation needed |
| Data Analysis Agent | Interprets tables | Must handle chart context in analysis | MODERATE -- prompt update, strip chart spec |
| Manager Agent | 3 routes (MEMORY/CODE/NEW) | 4th route: VISUALIZATION (or flag) | MODERATE -- routing logic change |
| E2B Sandbox | Executes pandas code | Executes plotly code | LOW -- plotly is a safe library |
| Frontend DataCard | Table + Explanation | Table + Chart + Explanation | MODERATE -- new component section |
| Frontend Bundle | No plotly.js | +1-3MB plotly.js | HIGH if not lazy loaded |
| SSE Streaming | No chart events | Chart-specific events | LOW -- additive events |

**Recommended phase ordering:**
1. **Infrastructure prep:** Allowlist update + E2B Plotly verification + state schema extension
2. **Output pipeline:** Modify execute_in_sandbox to handle chart JSON, add chart_data to state
3. **Visualization Agent:** Create new agent with chart-specific prompt + routing update
4. **Code Checker update:** Visualization-aware validation
5. **Data Analysis Agent update:** Chart-aware analysis + follow-up suggestions
6. **Frontend chart component:** Lazy-loaded Plotly rendering, theme support, download
7. **Integration + polish:** Streaming events, multi-chart, edge cases

Each phase should be independently testable. Phase 1-2 can be tested with manually written chart code. Phase 3-5 can be tested via API without frontend. Phase 6-7 connects everything end-to-end.

---

## Regression Risk: v0.1-v0.3 Requirements

The visualization feature is additive -- it should NOT break existing tabular analysis. However, these regressions are possible:

| Existing Behavior | Why At Risk | Regression Test |
|---|---|---|
| Tabular analysis returns JSON results | Output pipeline changes may break JSON parsing for non-chart results | Send a tabular query and verify DataCard renders table correctly |
| Code Checker validates tabular code | Allowlist/prompt changes may become overly permissive or create false positives | Run existing test suite of tabular validation scenarios |
| DataCard renders tables correctly | New chart section may break existing CSS layout or component structure | Render a table-only DataCard and verify layout matches pre-v0.4 |
| SSE streaming works end-to-end | New streaming events may break existing event parsing in frontend | Run a tabular query through the stream and verify all events parse correctly |
| Manager Agent routing accuracy | Adding VISUALIZATION route may confuse the router for borderline queries | Test existing routing scenarios (MEMORY, CODE_MOD, NEW) and verify they still route correctly |

---

## Sources

- **Codebase analysis:** Direct inspection of `graph.py`, `state.py`, `coding.py`, `code_checker.py`, `data_analysis.py`, `manager.py`, `e2b_runtime.py`, `models.py`, `allowlist.yaml`, `prompts.yaml`, `DataCard.tsx`, `ChatMessage.tsx` -- with line-number references throughout
- [Drawing Pandas: A Benchmark for LLMs in Generating Plotting Code (arxiv 2412.02764)](https://arxiv.org/html/2412.02764v1) -- LLM chart generation accuracy benchmarks, Plotly underperformance
- [Are LLMs Ready for Visualization? (arxiv 2403.06158)](https://arxiv.org/html/2403.06158v1) -- LLMs struggle with Plotly vs Matplotlib, chart type selection errors
- [Evaluating LLMs for Visualization Generation (Springer 2025)](https://link.springer.com/article/10.1007/s44248-025-00036-4) -- evaluation framework for LLM-generated visualizations
- [Building a Data Visualization Agent with LangGraph Cloud](https://blog.langchain.com/data-viz-agent/) -- architecture patterns for LangGraph-based viz agents
- [Plotly Performance Documentation](https://plotly.com/python/performance/) -- WebGL rendering, data point limits, performance optimization
- [Plotly.io.to_html API Reference](https://plotly.com/python-api-reference/generated/plotly.io.to_html.html) -- full_html, include_plotlyjs parameters, 3MB size impact
- [Plotly.io.to_json API Reference](https://plotly.github.io/plotly.py-docs/generated/plotly.io.to_json.html) -- JSON serialization for client-side rendering
- [react-plotly.js GitHub](https://github.com/plotly/react-plotly.js) -- createPlotlyComponent factory, partial bundle support
- [plotly.js Bundle Size (GitHub Issue #1802)](https://github.com/plotly/plotly.js/issues/1802) -- full bundle ~3.5MB, basic partial ~1MB
- [plotly.js-basic-dist-min (Community Forum)](https://community.plotly.com/t/how-can-i-reduce-bundle-size-of-plotly-js-in-react-app/89910) -- partial bundle for bar, scatter, pie, line
- [Kaleido v1.0.0 (GitHub)](https://github.com/plotly/Kaleido) -- Chrome requirement, breaking change from bundled Chromium
- [Plotly Static Image Export](https://plotly.com/python/static-image-export/) -- Kaleido vs client-side export
- [E2B Code Interpreter - Interactive Charts Documentation](https://e2b.dev/docs/code-interpreting/create-charts-visualizations/interactive-charts) -- E2B only auto-detects matplotlib, not Plotly
- [E2B Code Interpreter PyPI](https://pypi.org/project/e2b-code-interpreter/) -- sandbox execution model, stdout capture
- [Content Security Policy in Next.js](https://nextjs.org/docs/pages/guides/content-security-policy) -- CSP considerations for iframe embedding
- [Plotly Community: Large HTML file size](https://community.plotly.com/t/plotly-huge-html-file-size/64342) -- size challenges with embedded data
- [Cutting Render Times: Plotly Performance Update](https://plotly.com/blog/cutting-render-times-plotly-performance-update/) -- WebGL auto-detection for large datasets

---

*Pitfalls research for: Spectra v0.4 Data Visualization*
*Researched: 2026-02-12*
*Confidence: HIGH -- All critical pitfalls verified against actual codebase with line-number references and corroborated by official documentation and academic research*
