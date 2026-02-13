# Technology Stack: v0.4 Data Visualization

**Project:** Spectra - AI-powered data analytics platform
**Researched:** 2026-02-12
**Confidence:** HIGH (backend: Plotly pre-installed in E2B; frontend: JSON approach avoids risky dependencies)

## Overview

This research focuses on stack additions needed for v0.4: AI-generated Plotly charts with interactive display and PNG/SVG export. The core architectural decision is **where chart rendering happens** -- in the E2B sandbox (server-side) or in the browser (client-side). This choice cascades into every other technology decision.

**Recommendation: Hybrid approach.** Generate Plotly figure JSON in the E2B sandbox, render interactively with plotly.js on the client, and export PNG/SVG client-side using plotly.js's built-in `Plotly.toImage()` / `Plotly.downloadImage()`. This avoids Kaleido's Chrome dependency problem in sandboxed environments entirely.

Key insight: **The E2B sandbox already has Plotly 6.0.1 pre-installed.** The Visualization Agent generates Python code that creates a Plotly figure and outputs its JSON via `fig.to_json()`. The frontend receives this JSON and renders it with plotly.js. No server-side image generation needed -- plotly.js handles PNG/SVG export natively in the browser.

---

## What Changes (and What Does Not)

### Does NOT Change
- FastAPI backend framework
- PostgreSQL database
- SQLAlchemy ORM / Alembic migrations
- LangGraph agent orchestration (graph topology adds a node, but framework unchanged)
- E2B sandbox execution (same `Sandbox.run_code()` pattern)
- All 5 LLM providers
- Next.js 16 / React 19 / TanStack Query / Zustand
- JWT authentication / SSE streaming
- Tailwind CSS 4 / shadcn/ui components

### Changes Required

| Layer | What Changes | Why |
|-------|-------------|-----|
| Backend: LangGraph State | Add `chart_json` field to `ChatAgentState` | Carry Plotly figure JSON through the pipeline |
| Backend: Agent Graph | Add `visualization_agent` node, modify routing from execute -> da_with_tools | Visualization Agent runs after execution when chart is appropriate |
| Backend: Sandbox Output | Parse `fig.to_json()` output from sandbox stdout alongside table data | Sandbox code now outputs both table JSON and chart JSON |
| Backend: Agent YAML Configs | New `visualization` agent config in `agents.yaml` | Per-agent LLM provider/model/prompt configuration |
| Backend: SSE Events | New `chart_data` event type in stream | Frontend needs chart JSON streamed separately from table data |
| Frontend: plotly.js | Add `plotly.js-dist-min` package | Client-side interactive chart rendering and image export |
| Frontend: DataCard | Add chart section above table in DataCard component | Chart + table display in the same card |
| Frontend: Chart Component | New `PlotlyChart` component wrapping `Plotly.newPlot()` | Renders chart JSON, handles resize, provides export buttons |
| Frontend: Export UI | PNG/SVG download buttons on chart | Uses `Plotly.downloadImage()` -- no server roundtrip |
| Frontend: Chart Type Switcher | Dropdown/buttons to change chart type | Modifies the `data[0].type` field in the Plotly JSON client-side |

---

## Recommended Stack Additions

### Backend: Python (Sandbox-Side) -- No New pip Installs

The E2B code interpreter sandbox has these visualization packages pre-installed (verified via DeepWiki/E2B documentation):

| Package | Pre-installed Version | Purpose | Notes |
|---------|----------------------|---------|-------|
| `plotly` | 6.0.1 | Chart generation in sandbox | Pre-installed. Agent code uses `plotly.express` and `plotly.graph_objects`. |
| `kaleido` | 1.0.0 | Static image export (server-side) | Pre-installed but **DO NOT USE** -- requires Chrome, unreliable in sandbox. See "Critical Decision" below. |
| `pandas` | 2.2.3 | Data manipulation | Pre-installed. Already used by existing agents. |

**No `pip install` needed at runtime.** The Visualization Agent's generated code uses only pre-installed packages. The code creates a Plotly figure and outputs `fig.to_json()` to stdout, which the existing sandbox result parsing captures.

### Backend: Python (Server-Side) -- No New pip Installs

No new Python dependencies on the backend server. The changes are:
1. New Visualization Agent node in LangGraph (uses existing `langchain-core`, `langgraph` patterns)
2. New agent config in `agents.yaml` (uses existing YAML config system)
3. Modified sandbox output parsing to extract chart JSON (Python `json` module, already used)
4. New SSE event type (uses existing `sse-starlette` streaming)

### Frontend: plotly.js -- 1 New npm Package

| Package | Version | Purpose | Why This Package |
|---------|---------|---------|-----------------|
| `plotly.js-dist-min` | ^3.3.1 | Client-side chart rendering + PNG/SVG export | Minified plotly.js bundle (~1MB gzipped). Provides `Plotly.newPlot()`, `Plotly.react()`, `Plotly.toImage()`, `Plotly.downloadImage()`. The `-dist-min` variant is the smallest full bundle -- no build tools needed, works as a drop-in. |

**Why NOT `react-plotly.js`?** The official React wrapper (v2.6.0) has not been updated in 3 years, has known prop mutation issues, and has unverified React 19 compatibility. Instead, use a thin custom wrapper component around the raw `Plotly.newPlot()` API with a `useRef` + `useEffect` pattern. This is 30 lines of code and gives full control.

**Why NOT `plotly.js-dist` (non-minified)?** The minified version is ~50% smaller with identical functionality. No reason to ship the non-minified bundle to production.

**Why NOT `plotly.js-basic-dist-min` (partial bundle)?** The basic bundle only includes scatter, bar, and pie traces. We need histogram, box, and potentially heatmap for data analytics use cases. The full bundle covers all chart types.

---

## Critical Decision: Server-Side vs Client-Side Image Export

### The Problem with Kaleido in E2B Sandbox

Kaleido v1.0.0 (pre-installed in E2B) requires Chrome/Chromium to be installed on the machine. The E2B sandbox environment:
- Does NOT have Chrome pre-installed (verified: not listed in sandbox environment docs)
- Is a minimal Firecracker microVM optimized for Python code execution
- Has sandbox-within-sandbox issues (Kaleido spawns Chrome which has its own sandboxing, known to conflict with Docker/container environments -- [GitHub Issue #379](https://github.com/plotly/Kaleido/issues/379))
- Has a 50x performance regression in Kaleido v1 vs v0.2.1 ([GitHub Issue #400](https://github.com/plotly/Kaleido/issues/400))

Kaleido v0.2.1 (which bundled Chrome) is deprecated and incompatible with Plotly 6.x. Support was officially removed after September 2025.

### The Solution: Client-Side Export with plotly.js

plotly.js provides native image export functions that run entirely in the browser:
- `Plotly.toImage(graphDiv, {format: 'png', width: 1200, height: 800})` -- returns base64 data URL
- `Plotly.toImage(graphDiv, {format: 'svg', width: 1200, height: 800})` -- returns SVG string
- `Plotly.downloadImage(graphDiv, {format: 'png', filename: 'chart'})` -- triggers browser download

**Verified via plotly.js source code:** The `toImage` function supports `'png' | 'jpeg' | 'webp' | 'svg'` formats in the open-source library. The Plotly docs page is misleading -- it conflates Chart Studio (paid SaaS) features with the open-source JS library capabilities. The source at `plotly.js/src/snapshot/toimage.js` confirms all four formats are available without any subscription.

**This approach:**
- Requires zero server-side rendering infrastructure
- Works without Chrome, Kaleido, or any headless browser
- Produces high-quality PNG (canvas-based) and SVG (DOM-based) output
- Runs instantly (no 2-3 second Kaleido overhead)
- Allows user to customize chart (type, size) before exporting

**Confidence: HIGH** -- Verified via [plotly.js source code](https://github.com/plotly/plotly.js/blob/master/src/snapshot/toimage.js), [official JS docs](https://plotly.com/javascript/static-image-export/), and community usage.

---

## Architecture: Data Flow for Chart Rendering

```
1. User asks: "Show me sales by region"

2. Manager Agent -> routes to coding_agent (NEW_ANALYSIS)

3. Coding Agent generates Python code:
   - Data preparation (existing behavior)
   - Outputs table JSON via print(json.dumps({"result": table_data}))

4. Code Checker validates -> Execute in E2B sandbox

5. [NEW] Manager/routing decides: visualization appropriate?
   If yes -> Visualization Agent generates chart code

6. Visualization Agent generates Plotly code, executed in sandbox:
   ```python
   import plotly.express as px
   fig = px.bar(df, x="region", y="sales", title="Sales by Region")
   # Output chart JSON to stdout
   import json
   print(json.dumps({"chart": json.loads(fig.to_json())}))
   ```

7. Backend parses stdout -> extracts chart JSON
   Streams via SSE: {type: "chart_data", chart_json: {...}}

8. Frontend receives chart JSON -> PlotlyChart component renders:
   Plotly.newPlot(divRef, chartJson.data, chartJson.layout, {responsive: true})

9. User clicks "Download PNG" -> Plotly.downloadImage(divRef, {format: 'png'})
   User clicks "Download SVG" -> Plotly.downloadImage(divRef, {format: 'svg'})
```

### Alternative Considered: to_html() in Sandbox + iframe on Frontend

Generate `fig.to_html(full_html=False, include_plotlyjs='cdn')` in the sandbox, send the HTML string to the frontend, and render in an iframe with `srcdoc`.

**Why rejected:**
- HTML string is ~50-100KB per chart (includes plotly.js CDN reference + data + layout)
- iframe introduces CSS isolation issues (theming, dark mode won't penetrate)
- iframe resize handling is complex (no native responsive behavior)
- Export from iframe requires `postMessage` communication -- fragile
- Chart type switching requires re-generating HTML server-side (round-trip)
- JSON approach is ~5-10KB and enables all client-side interactivity natively

---

## Frontend: PlotlyChart Component Pattern

```typescript
// components/data/PlotlyChart.tsx
"use client";

import { useRef, useEffect, useCallback } from "react";
import Plotly from "plotly.js-dist-min";

interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  onChartReady?: (div: HTMLDivElement) => void;
  className?: string;
}

export function PlotlyChart({ data, layout, config, onChartReady, className }: PlotlyChartProps) {
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!divRef.current) return;

    const defaultLayout: Partial<Plotly.Layout> = {
      autosize: true,
      margin: { t: 40, r: 20, b: 40, l: 60 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      ...layout,
    };

    const defaultConfig: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ["sendDataToCloud", "lasso2d", "select2d"],
      displaylogo: false,
      ...config,
    };

    Plotly.newPlot(divRef.current, data, defaultLayout, defaultConfig)
      .then(() => {
        if (divRef.current && onChartReady) onChartReady(divRef.current);
      });

    return () => {
      if (divRef.current) Plotly.purge(divRef.current);
    };
  }, [data, layout, config]);

  return <div ref={divRef} className={className} />;
}
```

**Why NOT `react-plotly.js`?** This wrapper is 30 lines and avoids: (1) stale React wrapper (last updated 3 years ago, React 19 untested), (2) prop mutation issues (react-plotly.js mutates data/layout props), (3) unnecessary dependency. The `Plotly.react()` function can be used for efficient updates instead of full `newPlot()` re-renders.

**Next.js SSR Consideration:** plotly.js requires DOM access. The `"use client"` directive ensures this component only runs in the browser. No SSR issues with this approach.

---

## Frontend: Export Utility Functions

```typescript
// lib/chart-export.ts
import Plotly from "plotly.js-dist-min";

export async function downloadChartAsPNG(
  chartDiv: HTMLDivElement,
  filename: string = "chart",
  width: number = 1200,
  height: number = 800,
  scale: number = 2  // 2x for retina
) {
  await Plotly.downloadImage(chartDiv, {
    format: "png",
    width,
    height,
    scale,
    filename,
  });
}

export async function downloadChartAsSVG(
  chartDiv: HTMLDivElement,
  filename: string = "chart",
  width: number = 1200,
  height: number = 800
) {
  await Plotly.downloadImage(chartDiv, {
    format: "svg",
    width,
    height,
    filename,
  });
}
```

---

## Backend: LangGraph State Additions

```python
# Additions to ChatAgentState (backend/app/agents/state.py)
class ChatAgentState(TypedDict):
    # ... existing fields ...

    chart_json: str
    """Plotly figure JSON string from visualization agent code execution.
    Contains {data: [...], layout: {...}} structure. Empty string if no chart."""

    chart_type: str
    """Chart type hint from visualization agent: 'bar', 'line', 'scatter',
    'histogram', 'box', 'pie', 'donut'. Used by frontend for type switcher."""

    visualization_requested: bool
    """Whether the manager/analysis agent determined a chart is appropriate
    for this query. Drives routing to visualization agent."""
```

---

## Backend: SSE Event Schema for Charts

```python
# New SSE event emitted by visualization execution
writer({
    "type": "chart_data",
    "event": "chart_data",
    "chart_json": chart_json_string,  # Plotly figure JSON
    "chart_type": "bar",              # Chart type hint
    "message": "Chart generated",
})
```

The frontend event handler adds chart JSON to the DataCard state alongside existing table data, enabling the "chart above table" layout.

---

## Backend: Visualization Agent Config

```yaml
# Addition to agents.yaml
visualization:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  temperature: 0.1
  max_tokens: 2048
  prompt: |
    You are a data visualization expert. Given the user's query, data profile,
    and analysis results, generate Python code using Plotly Express to create
    an appropriate chart.

    **Rules:**
    - Use plotly.express (px) for simple charts, plotly.graph_objects (go) for complex
    - Always set a descriptive title
    - Use appropriate chart type: bar, line, scatter, histogram, box, pie
    - Limit data to top 20 items for readability (sort and slice)
    - Output the figure JSON: print(json.dumps({{"chart": json.loads(fig.to_json())}}))
    - Do NOT call fig.show() or fig.write_image()
    - Handle missing data gracefully (dropna or fillna)
    - Use professional color schemes (plotly defaults are fine)
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Chart rendering location | Client-side (plotly.js) | Server-side (Kaleido in sandbox) | Kaleido v1 requires Chrome (not in E2B), has 50x perf regression, Docker sandbox conflicts. Client-side is instant and avoids all these issues. |
| Chart data transport | JSON (`fig.to_json()`) | HTML (`fig.to_html()`) | HTML is 10x larger, iframe rendering breaks theming/dark mode, chart type switching requires server roundtrip. JSON enables full client-side interactivity. |
| React Plotly wrapper | Custom 30-line component | `react-plotly.js` (npm) | Last updated 3 years ago (v2.6.0), React 19 untested, mutates props (violates React rules). Custom wrapper is simpler and safer. |
| plotly.js bundle | `plotly.js-dist-min` (full, minified) | `plotly.js-basic-dist-min` (partial) | Basic bundle lacks histogram, box, heatmap -- needed for analytics. Full bundle is ~1MB gzipped, acceptable. |
| Image export | `Plotly.downloadImage()` (client) | Kaleido `write_image()` (server) | Client-side export requires no infrastructure, is instant, works offline. Kaleido requires Chrome in a headless sandbox -- unreliable. |
| SVG export | `Plotly.toImage({format:'svg'})` (client) | Server-side SVG rendering | plotly.js open-source supports SVG export natively. Verified in source code. No subscription needed. |
| Chart type switcher | Client-side JSON mutation | Re-run visualization agent | Changing chart type is a simple `data[0].type` swap in JSON. No server roundtrip needed for basic type changes. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `kaleido` (server-side export) | Requires Chrome in sandbox, 50x perf regression, Docker conflicts | `Plotly.downloadImage()` client-side |
| `react-plotly.js` | Stale (3yr), React 19 untested, prop mutation | Custom 30-line `PlotlyChart` component |
| `orca` (legacy Plotly export) | Officially deprecated, removed after Sept 2025 | Client-side plotly.js export |
| `puppeteer` / `playwright` | Headless browser for server-side rendering -- massive dependency, sandbox conflicts | Not needed. Client-side rendering handles everything. |
| `chart.js` / `recharts` / `d3` | Different charting libraries | Plotly already chosen. Adding another creates inconsistency. |
| `html2canvas` | Screenshot-based export | `Plotly.toImage()` produces higher quality, native vector SVG |
| Custom E2B sandbox template | Template with Chrome + Kaleido pre-configured | Unnecessary. JSON approach avoids all server-side rendering. |
| `plotly.js` (non-dist) | Requires build tooling (webpack config) | `plotly.js-dist-min` is pre-built, no config needed |
| `DOMPurify` / sanitizer | For sanitizing HTML in iframes | Not using iframes. JSON rendering is safe by design. |

---

## Installation

### Frontend (1 new package)

```bash
cd frontend
npm install plotly.js-dist-min
```

Optionally, add TypeScript types:

```bash
npm install -D @types/plotly.js
```

**Note:** `@types/plotly.js` provides types for the full `plotly.js` API including `Plotly.newPlot()`, `Plotly.react()`, `Plotly.toImage()`, `Plotly.downloadImage()`, `Plotly.purge()`, and all data/layout type definitions.

### Backend (0 new packages)

```bash
# No new pip installs needed for v0.4
# Plotly 6.0.1 is pre-installed in E2B sandbox
# No new server-side dependencies
```

### E2B Sandbox (0 changes)

```bash
# No custom sandbox template needed
# Plotly 6.0.1 pre-installed in default code-interpreter template
# No Chrome/Kaleido configuration needed
```

---

## Integration Points with Existing Stack

### 1. E2B Sandbox Result Parsing (Modified)

Currently, `execute_in_sandbox` in `graph.py` parses JSON from stdout looking for `{"result": ...}`. The visualization code will output `{"chart": ...}` in addition to or instead of `{"result": ...}`.

```python
# Current parsing (graph.py line ~458):
parsed = json.loads(line.strip())
if "result" in parsed:
    execution_result = json.dumps(parsed["result"])

# Extended parsing for v0.4:
parsed = json.loads(line.strip())
if "result" in parsed:
    execution_result = json.dumps(parsed["result"])
if "chart" in parsed:
    chart_json = json.dumps(parsed["chart"])
```

### 2. SSE Stream Event Handling (Extended)

The existing SSE stream (`chat.py` routers) passes events from LangGraph `get_stream_writer()`. The new `chart_data` event type flows through the same pipeline with zero changes to the streaming infrastructure.

### 3. DataCard Component (Extended)

The existing `DataCard.tsx` has sections: Query Brief -> Code Display -> Data Table -> Analysis. Charts insert between Code Display and Data Table:

```
Query Brief  (existing)
Code Display (existing)
Chart        (NEW - PlotlyChart component)
Data Table   (existing)
Analysis     (existing)
Export Row   (existing CSV/MD + NEW PNG/SVG buttons)
```

### 4. LangGraph Agent Graph (Extended)

The `build_chat_graph()` function adds a `visualization_agent` node. Routing:

```
execute -> [should_visualize?] -> visualization_agent -> da_with_tools
execute -> [no visualization]  -> da_with_tools  (existing path)
```

The conditional edge checks `state["visualization_requested"]`. The visualization agent is optional -- queries that don't warrant charts skip it entirely.

### 5. Frontend Zustand Store (Minimal Change)

The existing message/card state in the chat interface needs a `chartJson` field per data card. This is a small extension to the existing streaming state management, not a new store.

---

## Version Compatibility

| Package | Version | Compatibility | Notes |
|---------|---------|--------------|-------|
| `plotly.js-dist-min` | ^3.3.1 | Works with all browsers | No framework dependency. Pure JS. |
| `@types/plotly.js` | Latest | TypeScript 5.x | Type definitions only, dev dependency |
| Plotly (Python, E2B) | 6.0.1 (pre-installed) | `fig.to_json()` available since Plotly 4.x | Stable API, no version concerns |
| Next.js 16 | 16.1.6 | `"use client"` for plotly.js components | plotly.js needs DOM -- client components only |
| React 19 | 19.2.3 | Compatible via `useRef` + `useEffect` | No React wrapper needed, direct DOM manipulation |
| E2B Code Interpreter | >=1.0.2 | Pre-installs Plotly 6.0.1 | No custom template needed |

---

## Bundle Size Impact

| Package | Uncompressed | Gzipped | Notes |
|---------|-------------|---------|-------|
| `plotly.js-dist-min` | ~3.5 MB | ~1.0 MB | One-time load. Can be lazy-loaded only when charts are displayed. |

**Mitigation:** Use Next.js dynamic import to lazy-load plotly.js only when a DataCard with chart data is rendered:

```typescript
import dynamic from "next/dynamic";

const PlotlyChart = dynamic(() => import("@/components/data/PlotlyChart"), {
  ssr: false,
  loading: () => <div className="h-[400px] skeleton rounded-lg" />,
});
```

This ensures plotly.js is never loaded for users who haven't triggered a visualization query yet.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| plotly.js bundle increases page load | Medium | Low | Lazy-load with `next/dynamic`. Only loaded when chart renders. |
| E2B sandbox Plotly version drifts | Low | Low | Pin via `import plotly; assert plotly.__version__.startswith('6')` in agent code preamble. |
| `Plotly.toImage()` fails on some browsers | Very Low | Medium | Well-tested in all modern browsers. Fallback: hide export buttons if canvas unavailable. |
| Chart JSON too large for SSE event | Low | Medium | Plotly JSON for typical charts is 5-20KB. For large datasets, the agent should aggregate before charting (top 20 items rule). |
| Agent generates invalid Plotly JSON | Medium | Low | Code Checker already validates code. Add Plotly-specific validation: try `json.loads(chart_json)` and verify `data` key exists. |
| Dark mode chart theming | Medium | Low | Set `paper_bgcolor: 'transparent'`, `plot_bgcolor: 'transparent'`, and use CSS variables for font colors in layout config. |

---

## Sources

**Plotly Python (Sandbox-Side):**
- [Plotly PyPI -- v6.5.2 current](https://pypi.org/project/plotly/) -- Confirms latest version. E2B has 6.0.1.
- [fig.to_html() docs](https://plotly.com/python-api-reference/generated/plotly.io.to_html.html) -- `full_html`, `include_plotlyjs` parameters
- [fig.to_json() docs](https://plotly.github.io/plotly.py-docs/generated/plotly.io.to_json.html) -- JSON export API
- [Static image generation changes](https://plotly.com/python/static-image-generation-changes/) -- Kaleido v1 deprecation timeline

**Plotly.js (Frontend-Side):**
- [plotly.js-dist-min npm](https://www.npmjs.com/package/plotly.js-dist-min) -- v3.3.1 current
- [plotly.js static image export](https://plotly.com/javascript/static-image-export/) -- `Plotly.toImage()`, `Plotly.downloadImage()` API
- [plotly.js source: toimage.js](https://github.com/plotly/plotly.js/blob/master/src/snapshot/toimage.js) -- Confirms SVG support in open-source (format: 'png' | 'jpeg' | 'webp' | 'svg')
- [react-plotly.js GitHub](https://github.com/plotly/react-plotly.js) -- Last updated 3 years ago, v2.6.0

**Kaleido (NOT Recommended):**
- [Kaleido GitHub](https://github.com/plotly/Kaleido) -- v1.2.0 current, requires Chrome
- [Docker compatibility issue #379](https://github.com/plotly/Kaleido/issues/379) -- Sandbox-in-sandbox failures
- [Performance regression issue #400](https://github.com/plotly/Kaleido/issues/400) -- 50x slower than v0.2.1
- [Kaleido PyPI](https://pypi.org/project/kaleido/) -- Chrome dependency documented

**E2B Sandbox:**
- [E2B Code Interpreter Sandbox Environment](https://deepwiki.com/e2b-dev/code-interpreter/2.1-sandbox-environment) -- Pre-installed packages list (Plotly 6.0.1, Kaleido 1.0.0, pandas 2.2.3)
- [E2B Custom Packages](https://e2b.dev/docs/quickstart/install-custom-packages) -- Runtime vs template installation
- [E2B SDK Result Object](https://e2b.dev/docs/sdk-reference/code-interpreter-python-sdk/v1.2.1/sandbox) -- Result has `html`, `json`, `png` representations
- [Plotly Python to JSON for React](https://community.plotly.com/t/how-to-convert-python-json-object-to-plot-in-plotly-js-in-react/68797) -- Community pattern for Python->JSON->JS rendering

---

*Stack research for: Spectra v0.4 Data Visualization*
*Researched: 2026-02-12*
*Confidence: HIGH -- JSON rendering approach is well-established. Kaleido rejection based on verified sandbox limitations. plotly.js SVG export confirmed via source code. E2B pre-installed packages verified.*
