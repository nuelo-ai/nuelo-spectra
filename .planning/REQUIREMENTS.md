# Requirements: Spectra

**Defined:** 2026-02-12
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.4 Requirements — Data Visualization

Requirements for v0.4 Data Visualization milestone. Each maps to roadmap phases.

### Infrastructure

- [ ] **INFRA-01**: Plotly added to allowed libraries in allowlist.yaml
- [ ] **INFRA-02**: State schema extended with visualization fields (visualization_requested, chart_hint, chart_code, chart_specs, chart_error)
- [ ] **INFRA-03**: E2B sandbox Plotly 6.0.1 availability verified
- [ ] **INFRA-04**: Sandbox output parser modified to capture chart JSON from stdout

### Visualization Agent

- [ ] **AGENT-01**: Visualization Agent module created with LangGraph integration
- [ ] **AGENT-02**: Visualization Agent prompt configured in prompts.yaml with LLM settings
- [ ] **AGENT-03**: Agent generates Plotly Python code from execution results and user query
- [ ] **AGENT-04**: Agent embeds data as Python literal (no file uploads needed)
- [ ] **AGENT-05**: Agent includes chart type selection heuristics (categorical >8 → bar not pie)
- [ ] **AGENT-06**: Chart code outputs JSON via fig.to_json() to stdout

### Chart Generation

- [ ] **CHART-01**: System supports bar chart generation
- [ ] **CHART-02**: System supports line chart generation
- [ ] **CHART-03**: System supports scatter plot generation
- [ ] **CHART-04**: System supports histogram generation
- [ ] **CHART-05**: System supports box plot generation
- [ ] **CHART-06**: System supports pie chart generation
- [ ] **CHART-07**: System supports donut chart generation
- [ ] **CHART-08**: Data Analysis Agent decides when visualization adds value (sets visualization_requested flag)
- [ ] **CHART-09**: Manager Agent hints visualization intent during query routing
- [ ] **CHART-10**: Chart generation errors are non-fatal (preserve analysis and table on failure)
- [ ] **CHART-11**: Charts include meaningful titles and axis labels (not raw column names)

### Graph Integration

- [ ] **GRAPH-01**: Visualization Agent node added to LangGraph
- [ ] **GRAPH-02**: viz_execute node executes chart code in E2B sandbox
- [ ] **GRAPH-03**: viz_response node handles chart results
- [ ] **GRAPH-04**: should_visualize() conditional edge routes based on visualization_requested flag
- [ ] **GRAPH-05**: da_response modified from finish point to conditional routing
- [ ] **GRAPH-06**: Chart JSON streams to frontend via SSE events

### Chart Display

- [ ] **DISPLAY-01**: Frontend installs plotly.js-dist-min package (~1MB)
- [ ] **DISPLAY-02**: ChartRenderer component created with dynamic import (no SSR)
- [ ] **DISPLAY-03**: ChartRenderer uses Plotly.newPlot() with React useRef/useEffect
- [ ] **DISPLAY-04**: DataCard renders chart above table when chart_specs exists
- [ ] **DISPLAY-05**: Charts are interactive (zoom, pan, hover tooltips via Plotly.js)
- [ ] **DISPLAY-06**: Charts are responsive (resize with container)
- [ ] **DISPLAY-07**: Chart skeleton loader displays during generation

### Export & Customization

- [ ] **EXPORT-01**: User can download chart as PNG via Plotly.downloadImage()
- [ ] **EXPORT-02**: User can download chart as SVG via Plotly.downloadImage()
- [ ] **EXPORT-03**: Download buttons appear below chart in DataCard
- [ ] **EXPORT-04**: User can switch chart type after generation (bar ↔ line ↔ scatter)
- [ ] **EXPORT-05**: Chart type switcher only shows applicable types for data shape

### Theme & Polish

- [ ] **THEME-01**: Charts respect light/dark theme toggle
- [ ] **THEME-02**: Charts use transparent backgrounds in dark mode
- [ ] **THEME-03**: Chart colors match theme palette (Nord colors in dark mode)
- [ ] **THEME-04**: Chart text colors adjust for theme (readable in both modes)

## Future Requirements

Deferred to future milestones. Tracked but not in v0.4 roadmap.

### Advanced Visualization

- **VIZ-ADV-01**: Multi-chart display (2-3 charts per response with tabs/carousel)
- **VIZ-ADV-02**: Advanced chart types (heatmap, 3D scatter, geo maps)
- **VIZ-ADV-03**: Chart annotations with AI-generated insights (trend lines, outliers)
- **VIZ-ADV-04**: Chart templates/presets (corporate, colorblind-friendly color schemes)

### Persistence & Sharing

- **PERSIST-01**: Chart configurations saved to database metadata_json
- **PERSIST-02**: User can bookmark specific charts
- **PERSIST-03**: User can share chart links with collaborators

### Production Hardening (from v0.3)

- **PROD-01**: Query safety filter in Manager Agent (block PII extraction, prompt injection)
- **PROD-02**: Pydantic structured output for agent JSON responses
- **PROD-03**: Dokploy Docker deployment package

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full chart editor UI | Over-engineering - basic type switcher sufficient for v0.4 |
| Server-side chart rendering (Kaleido) | Kaleido requires Chrome (not in E2B), 50x slower, client-side works well |
| Chart persistence in database | Transient regeneration acceptable, defer to post-v0.4 based on usage |
| Animation/transitions in charts | Not core to value, adds bundle size |
| Dashboard creation | Out of product scope - focus is query-response, not dashboards |
| Custom Plotly config UI | Too complex - sensible defaults from AI sufficient |
| Chart collaboration/comments | No real-time collab in v0.4 |
| Database-direct chart generation | File upload only, no live data connections |
| react-plotly.js wrapper | Unmaintained (3 years old), custom component more reliable |
| Multi-chart in v0.4 | Deferred to v0.5+ for UX validation |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 20 | Pending |
| INFRA-02 | Phase 20 | Pending |
| INFRA-03 | Phase 20 | Pending |
| INFRA-04 | Phase 20 | Pending |
| AGENT-01 | Phase 21 | Pending |
| AGENT-02 | Phase 21 | Pending |
| AGENT-03 | Phase 21 | Pending |
| AGENT-04 | Phase 21 | Pending |
| AGENT-05 | Phase 21 | Pending |
| AGENT-06 | Phase 21 | Pending |
| GRAPH-01 | Phase 22 | Pending |
| GRAPH-02 | Phase 22 | Pending |
| GRAPH-03 | Phase 22 | Pending |
| GRAPH-04 | Phase 22 | Pending |
| GRAPH-05 | Phase 22 | Pending |
| GRAPH-06 | Phase 22 | Pending |
| CHART-08 | Phase 22 | Pending |
| CHART-09 | Phase 22 | Pending |
| CHART-10 | Phase 22 | Pending |
| DISPLAY-01 | Phase 23 | Pending |
| DISPLAY-02 | Phase 23 | Pending |
| DISPLAY-03 | Phase 23 | Pending |
| DISPLAY-04 | Phase 23 | Pending |
| DISPLAY-05 | Phase 23 | Pending |
| DISPLAY-06 | Phase 23 | Pending |
| DISPLAY-07 | Phase 23 | Pending |
| CHART-01 | Phase 24 | Pending |
| CHART-02 | Phase 24 | Pending |
| CHART-03 | Phase 24 | Pending |
| CHART-04 | Phase 24 | Pending |
| CHART-05 | Phase 24 | Pending |
| CHART-06 | Phase 24 | Pending |
| CHART-07 | Phase 24 | Pending |
| CHART-11 | Phase 24 | Pending |
| EXPORT-01 | Phase 24 | Pending |
| EXPORT-02 | Phase 24 | Pending |
| EXPORT-03 | Phase 24 | Pending |
| EXPORT-04 | Phase 24 | Pending |
| EXPORT-05 | Phase 24 | Pending |
| THEME-01 | Phase 25 | Pending |
| THEME-02 | Phase 25 | Pending |
| THEME-03 | Phase 25 | Pending |
| THEME-04 | Phase 25 | Pending |

**Coverage:**
- v0.4 requirements: 43 total (note: previously listed as 44, actual count is 43)
- Mapped to phases: 43
- Unmapped: 0

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after roadmap creation*
