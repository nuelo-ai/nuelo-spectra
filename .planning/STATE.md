# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-12)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 24 — Chart Types & Export (v0.4 Data Visualization)

## Current Position

Phase: 24 of 25 (Chart Types & Export)
Plan: 3 of 3 in Phase 24
Status: Phase 24 Complete
Last activity: 2026-02-13 — Completed Plan 24-03 (Chart Type Switching)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 [##########] ~80%

## Performance Metrics

**Velocity (v0.1):**
- Total plans completed: 36
- Total execution time: ~5 days (Feb 1-6, 2026)
- Plans per day: ~7 plans/day

**Velocity (v0.2):**
- Total plans completed: 19
- Total execution time: ~4 days (Feb 7-10, 2026)
- Plans per day: ~5 plans/day

**Velocity (v0.3):**
- Total plans completed: 23
- Total execution time: ~3 days (Feb 10-12, 2026)
- Plans per day: ~8 plans/day

**Velocity (v0.4):**
- Total plans completed: 14 (Phases 20-24 complete)
- Total execution time: ~3 days (Feb 12-13, 2026)
- Plans per day: ~5 plans/day

| Phase-Plan | Duration | Tasks | Files | Date       |
|------------|----------|-------|-------|------------|
| 24-01      | 2min     | 1     | 1     | 2026-02-13 |
| 24-02      | 152s     | 2     | 3     | 2026-02-13 |
| 24-03      | 130s     | 2     | 4     | 2026-02-13 |

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

Recent decisions for v0.4:
- Client-side export via Plotly.downloadImage() instead of server-side Kaleido (Kaleido requires Chrome, 50x slower)
- plotly.js-dist-min partial bundle (~1MB) instead of full plotly.js (~3MB)
- Custom ChartRenderer component instead of outdated react-plotly.js wrapper
- JSON-over-the-wire pattern (fig.to_json()) instead of HTML string transport
- Disallow custom JavaScript in Plotly charts (XSS via prompt injection risk)
- Plotly NOT in unsafe_modules -- E2B sandbox is security boundary
- Explicit visualization field initialization over LangGraph implicit defaults
- Single-line JSON fast path, joined stdout fallback for large chart JSON
- 2MB chart JSON size limit with transparent error messaging
- Accept Plotly 5.x or 6.x (E2B confirmed 6.0.1)
- Reuse extract_code_block from coding.py in visualization agent (no duplication)
- 8000 char execution_result truncation limit; data shape hints built on full data before truncation
- Visualization agent generates code only; does not execute (execution is Phase 22)
- [Phase 22-01]: LLM-based chart intelligence with two-phase flags (chart_hint advisory, visualization_requested confirmation)
- [Phase 22-02]: Max 1 retry (2 total attempts) for chart execution failures with error context feedback
- [Phase 22-02]: Chart failure is non-fatal (analysis and data table always preserved)
- [Phase 22-02]: Subtle frontend notification on chart failure (don't alarm user)
- [Phase 23-01]: Direct Plotly import in ChartRenderer; next/dynamic ssr:false wrapping deferred to Plan 02
- [Phase 23-01]: Dynamic chart height: 400px base + 10px/100pts, 700px cap, backend layout.height override
- [Phase 23-01]: Dual-path chart data extraction (direct SSE events + node_complete fields) for robustness
- [Phase 23-02]: viz_response_node must return chart data in node output (not just custom writer events)
- [Phase 23-02]: run_chat_query_stream needs try/finally with _save_stream_result() for DB persistence on GeneratorExit
- [Post-23]: Removed plotly from Coder Agent allowlist — Coder must produce tabular data only, Visualization Agent handles charts
- [Phase 24-01]: Explicit Plotly code patterns in LLM prompts reduce code generation errors (show hole=0.4 for donut, labels parameter usage)
- [Phase 24-01]: Label formatting rules enforce human-readable output with unit inference (revenue->$, count->Count, percent->%)
- [Phase 24-01]: Histogram vs bar distinction clarified (histogram for distributions >8 unique values, bar for categorical comparisons)
- [Phase 24-01]: Query-driven chart selection (keywords like "distribution"/"donut" influence chart type choice)
- [Phase 24-02]: Client-side Plotly.downloadImage() for chart export (instant, no server round-trip)
- [Phase 24-02]: Ref forwarding via forwardRef/useImperativeHandle to expose chart DOM element
- [Phase 24-03]: Client-side chart type switching via Plotly.restyle() (instant, no backend round-trip)
- [Phase 24-03]: Data shape analysis determines compatible chart types (numeric x-axis = all 3 types, categorical = bar+line only)
- [Phase 24-03]: Fixed .gitignore pattern from 'lib/' to '/lib/' to not ignore frontend/src/lib/

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment)
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)

### Blockers/Concerns

- E2B sandboxes created per-execution (no warm pools) — acceptable for now
- LLM chart type selection has 15-30% error rate per research — mitigate with prompt heuristics

## Session Continuity

Last session: 2026-02-13
Stopped at: Completed Phase 24 (Chart Types & Export). All 3 plans complete.
Resume with: Next phase or milestone completion
