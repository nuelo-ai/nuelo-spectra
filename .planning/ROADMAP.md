# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** — Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** — Phases 7-13 (shipped 2026-02-10)
- ✅ **v0.3 Multi-file Conversation Support** — Phases 14-19 (shipped 2026-02-12)
- 🚧 **v0.4 Data Visualization** — Phases 20-25 (in progress)

## Phases

<details>
<summary>✅ v0.1 Beta MVP (Phases 1-6) — SHIPPED 2026-02-06</summary>

- [x] Phase 1: Foundation Setup (6/6 plans) — completed 2026-02-06
- [x] Phase 2: File Upload & AI Profiling (6/6 plans) — completed 2026-02-06
- [x] Phase 3: Multi-File Management (4/4 plans) — completed 2026-02-06
- [x] Phase 4: AI Agent System & Code Generation (8/8 plans) — completed 2026-02-06
- [x] Phase 5: Secure Code Execution & E2B (6/6 plans) — completed 2026-02-06
- [x] Phase 6: Interactive Data Cards & Frontend Polish (6/6 plans) — completed 2026-02-06

</details>

<details>
<summary>✅ v0.2 Intelligence & Integration (Phases 7-13) — SHIPPED 2026-02-10</summary>

- [x] Phase 7: Multi-LLM Provider Infrastructure (5/5 plans) — completed 2026-02-09
- [x] Phase 8: Session Memory with PostgreSQL Checkpointing (2/2 plans) — completed 2026-02-08
- [x] Phase 9: Manager Agent with Intelligent Query Routing (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Smart Query Suggestions (2/2 plans) — completed 2026-02-08
- [x] Phase 11: Web Search Tool Integration (3/3 plans) — completed 2026-02-09
- [x] Phase 12: Production Email Infrastructure (2/2 plans) — completed 2026-02-09
- [x] Phase 13: Migrate Web Search (Tavily) (2/2 plans) — completed 2026-02-09

</details>

<details>
<summary>✅ v0.3 Multi-file Conversation Support (Phases 14-19) — SHIPPED 2026-02-12</summary>

- [x] Phase 14: Database Foundation & Migration (4/4 plans) — completed 2026-02-11
- [x] Phase 15: Agent System Enhancement (3/3 plans) — completed 2026-02-11
- [x] Phase 16: Frontend Restructure (3/3 plans) — completed 2026-02-11
- [x] Phase 17: File Management & Linking (3/3 plans) — completed 2026-02-11
- [x] Phase 18: Integration & Polish (3/3 plans) — completed 2026-02-11
- [x] Phase 19: v0.3 Gap Closure (7/7 plans) — completed 2026-02-12

</details>

### 🚧 v0.4 Data Visualization (In Progress)

**Milestone Goal:** Enable intelligent data visualization with AI-generated interactive Plotly charts that automatically appear when analysis benefits from visual representation

- [x] **Phase 20: Infrastructure & Pipeline** — Allowlist, state schema, sandbox verification, and output parser for chart JSON
- [x] **Phase 21: Visualization Agent** — 6th AI agent that generates Plotly chart code from analysis results
- [ ] **Phase 22: Graph Integration & Chart Intelligence** — Wire agent into LangGraph with conditional routing and visualization discretion
- [ ] **Phase 23: Frontend Chart Rendering** — Plotly.js integration, ChartRenderer component, DataCard chart display
- [ ] **Phase 24: Chart Types & Export** — All 7 chart types validated end-to-end, PNG/SVG export, chart type switcher
- [ ] **Phase 25: Theme Integration** — Dark/light theme support for charts with Nord palette

## Phase Details

### Phase 20: Infrastructure & Pipeline

**Goal:** The platform is prepared for chart generation — Plotly is allowed, state carries visualization data, sandbox captures chart JSON

**Depends on:** Nothing (foundational for v0.4)

**Requirements:** INFRA-01, INFRA-02, INFRA-03, INFRA-04

**Success Criteria** (what must be TRUE):
  1. Plotly import passes Code Checker AST validation without rejection (allowlist updated)
  2. ChatAgentState carries visualization fields (visualization_requested, chart_hint, chart_code, chart_specs, chart_error) through the agent pipeline
  3. E2B sandbox can execute `import plotly; print(plotly.__version__)` and return version 6.x
  4. Sandbox output parser extracts chart JSON from stdout alongside existing result data

**Plans:** 2 plans

Plans:
- [x] 20-01-PLAN.md — Plotly allowlist + ChatAgentState visualization fields + initial_state defaults
- [x] 20-02-PLAN.md — Sandbox output parser chart JSON extraction + E2B Plotly verification tests

---

### Phase 21: Visualization Agent

**Goal:** A dedicated AI agent exists that generates correct Plotly Python code for charts based on analysis results and user intent

**Depends on:** Phase 20 (requires allowlist and state schema)

**Requirements:** AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-06

**Success Criteria** (what must be TRUE):
  1. Visualization Agent module exists with LangGraph-compatible invoke interface (same pattern as other agents)
  2. Agent is configurable via prompts.yaml with its own LLM provider, model, and system prompt
  3. Agent generates valid Plotly Python code that produces chart JSON via fig.to_json() to stdout
  4. Agent embeds data as Python literals in generated code (no file I/O or uploads needed in sandbox)
  5. Agent applies chart type selection heuristics (e.g., categorical >8 values triggers bar instead of pie)

**Plans:** 1 plan

Plans:
- [x] 21-01-PLAN.md -- Visualization Agent module + prompts.yaml config + unit tests

---

### Phase 22: Graph Integration & Chart Intelligence

**Goal:** The Visualization Agent is wired into the LangGraph pipeline with conditional routing — charts are generated only when the AI determines visualization adds value

**Depends on:** Phase 21 (requires Visualization Agent module)

**Requirements:** GRAPH-01, GRAPH-02, GRAPH-03, GRAPH-04, GRAPH-05, GRAPH-06, CHART-08, CHART-09, CHART-10

**Success Criteria** (what must be TRUE):
  1. Data Analysis Agent sets visualization_requested flag when it determines a chart would enhance the response
  2. Manager Agent includes visualization hints during query routing that inform downstream chart decisions
  3. When visualization_requested is true, the graph routes through Visualization Agent -> viz_execute -> viz_response nodes
  4. When visualization_requested is false, the graph skips visualization nodes entirely (existing tabular flow unchanged)
  5. Chart generation failure is non-fatal — the original analysis text and data table are preserved and displayed even when chart code errors occur

**Plans:** 2 plans

Plans:
- [ ] 22-01-PLAN.md — Chart intelligence: Manager chart_hint + DA visualization_requested flag + unit tests
- [ ] 22-02-PLAN.md — Graph pipeline: Visualization nodes, conditional routing, chart execution with retry, SSE events, metadata persistence + tests

---

### Phase 23: Frontend Chart Rendering

**Goal:** Users see interactive Plotly charts rendered in DataCards when chart data is available, with zoom, pan, and hover tooltips

**Depends on:** Phase 22 (requires chart JSON flowing via SSE)

**Requirements:** DISPLAY-01, DISPLAY-02, DISPLAY-03, DISPLAY-04, DISPLAY-05, DISPLAY-06, DISPLAY-07

**Success Criteria** (what must be TRUE):
  1. ChartRenderer component renders Plotly charts using dynamic import (no SSR, lazy-loaded only when chart data exists)
  2. DataCard displays chart above the data table when chart_specs is present in the response
  3. Charts are interactive — user can zoom, pan, and see hover tooltips on data points (Plotly.js defaults)
  4. Charts resize responsively when the browser window or container size changes
  5. A skeleton loader is visible while chart generation is in progress (before chart JSON arrives via SSE)

**Plans:** TBD

Plans:
- [ ] 23-01: TBD
- [ ] 23-02: TBD

---

### Phase 24: Chart Types & Export

**Goal:** All 7 chart types produce correct visualizations end-to-end, charts have meaningful labels, and users can export charts or switch chart types

**Depends on:** Phase 23 (requires chart rendering working)

**Requirements:** CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, CHART-06, CHART-07, CHART-11, EXPORT-01, EXPORT-02, EXPORT-03, EXPORT-04, EXPORT-05

**Success Criteria** (what must be TRUE):
  1. User can trigger generation of each chart type (bar, line, scatter, histogram, box plot, pie, donut) with appropriate queries and see correct output
  2. Charts display meaningful titles and human-readable axis labels (not raw column names like "col_revenue_2024")
  3. User can download any rendered chart as PNG via a download button below the chart
  4. User can download any rendered chart as SVG via a download button below the chart
  5. User can switch between applicable chart types (bar, line, scatter) after initial generation, and the chart re-renders with the same data

**Plans:** TBD

Plans:
- [ ] 24-01: TBD
- [ ] 24-02: TBD
- [ ] 24-03: TBD

---

### Phase 25: Theme Integration

**Goal:** Charts visually integrate with the platform's light and dark themes, using matching color palettes and readable text

**Depends on:** Phase 23 (requires chart rendering working)

**Requirements:** THEME-01, THEME-02, THEME-03, THEME-04

**Success Criteria** (what must be TRUE):
  1. Charts automatically switch appearance when the user toggles between light and dark mode
  2. Charts use transparent backgrounds in dark mode (no white rectangles breaking the dark UI)
  3. Chart colors use the Nord palette in dark mode, matching the rest of the platform's visual language
  4. Chart axis labels, titles, and legend text are readable in both light and dark modes (proper contrast)

**Plans:** TBD

Plans:
- [ ] 25-01: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 20 -> 21 -> 22 -> 23 -> 24 -> 25
Note: Phase 24 and Phase 25 can execute in parallel (both depend on Phase 23, not each other).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation Setup | v0.1 | 6/6 | Complete | 2026-02-06 |
| 2. File Upload & AI Profiling | v0.1 | 6/6 | Complete | 2026-02-06 |
| 3. Multi-File Management | v0.1 | 4/4 | Complete | 2026-02-06 |
| 4. AI Agent System & Code Generation | v0.1 | 8/8 | Complete | 2026-02-06 |
| 5. Secure Code Execution & E2B | v0.1 | 6/6 | Complete | 2026-02-06 |
| 6. Interactive Data Cards | v0.1 | 6/6 | Complete | 2026-02-06 |
| 7. Multi-LLM Infrastructure | v0.2 | 5/5 | Complete | 2026-02-09 |
| 8. Session Memory | v0.2 | 2/2 | Complete | 2026-02-08 |
| 9. Manager Agent Routing | v0.2 | 3/3 | Complete | 2026-02-08 |
| 10. Smart Query Suggestions | v0.2 | 2/2 | Complete | 2026-02-08 |
| 11. Web Search Integration | v0.2 | 3/3 | Complete | 2026-02-09 |
| 12. Production Email | v0.2 | 2/2 | Complete | 2026-02-09 |
| 13. Migrate Web Search (Tavily) | v0.2 | 2/2 | Complete | 2026-02-09 |
| 14. Database Foundation & Migration | v0.3 | 4/4 | Complete | 2026-02-11 |
| 15. Agent System Enhancement | v0.3 | 3/3 | Complete | 2026-02-11 |
| 16. Frontend Restructure | v0.3 | 3/3 | Complete | 2026-02-11 |
| 17. File Management & Linking | v0.3 | 3/3 | Complete | 2026-02-11 |
| 18. Integration & Polish | v0.3 | 3/3 | Complete | 2026-02-11 |
| 19. v0.3 Gap Closure | v0.3 | 7/7 | Complete | 2026-02-12 |
| 20. Infrastructure & Pipeline | v0.4 | 2/2 | Complete | 2026-02-13 |
| 21. Visualization Agent | v0.4 | 1/1 | Complete | 2026-02-13 |
| 22. Graph Integration & Chart Intelligence | v0.4 | 0/TBD | Not started | - |
| 23. Frontend Chart Rendering | v0.4 | 0/TBD | Not started | - |
| 24. Chart Types & Export | v0.4 | 0/TBD | Not started | - |
| 25. Theme Integration | v0.4 | 0/TBD | Not started | - |
