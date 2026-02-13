# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-12)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 23 — Frontend Chart Rendering (v0.4 Data Visualization)

## Current Position

Phase: 23 of 25 (Frontend Chart Rendering)
Plan: 1 of 2 in Phase 23
Status: Executing Phase 23
Last activity: 2026-02-13 — Completed 23-01 (Chart Infrastructure: Plotly Components & SSE Types)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 [######░░░░] ~50%

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
- Total plans completed: 10 (as of Phase 23-01)
- Total execution time: ~3 days (Feb 12-13, 2026)
- Plans per day: ~3 plans/day

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
Stopped at: Completed 23-01-PLAN.md (Chart Infrastructure: Plotly Components & SSE Types)
Resume with: Execute 23-02-PLAN.md to integrate chart components into DataCards
