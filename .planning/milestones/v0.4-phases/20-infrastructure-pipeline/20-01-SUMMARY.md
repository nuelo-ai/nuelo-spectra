---
phase: 20-infrastructure-pipeline
plan: 01
subsystem: infra
tags: [plotly, visualization, typeddict, allowlist, langgraph, sse]

# Dependency graph
requires: []
provides:
  - "Plotly in Code Checker allowlist (all submodules pass AST validation)"
  - "ChatAgentState with 5 visualization fields (visualization_requested, chart_hint, chart_code, chart_specs, chart_error)"
  - "Default initialization for visualization fields in both invoke and stream flows"
  - "chart_specs and chart_error forwarded to frontend via SSE streaming events"
affects: [21-visualization-agent, 22-pipeline-integration, 23-frontend-renderer]

# Tech tracking
tech-stack:
  added: [plotly]
  patterns: [state-field-initialization-pattern, sse-field-forwarding]

key-files:
  created: []
  modified:
    - backend/app/config/allowlist.yaml
    - backend/app/agents/state.py
    - backend/app/services/agent_service.py

key-decisions:
  - "Disallow custom JavaScript in Plotly charts -- Plotly built-in interactivity sufficient, custom JS opens XSS via prompt injection"
  - "Plotly NOT added to unsafe_modules or unsafe_operations -- pure visualization library, E2B sandbox is security boundary"
  - "Explicit field initialization over LangGraph implicit defaults -- documents contract and prevents KeyError"

patterns-established:
  - "Visualization field pattern: all viz fields initialized in both invoke and stream initial_state dicts identically"
  - "SSE forwarding pattern: new user-visible state fields must be added to stream event filter tuple"

# Metrics
duration: 2min
completed: 2026-02-13
---

# Phase 20 Plan 01: Infrastructure & Pipeline - Allowlist + State Summary

**Plotly added to Code Checker allowlist, ChatAgentState extended with 5 visualization fields, defaults initialized in both agent flows**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-13T12:51:32Z
- **Completed:** 2026-02-13T12:53:50Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Plotly imports (`import plotly`, `import plotly.express as px`, `from plotly.io import to_json`) pass Code Checker AST validation
- ChatAgentState TypedDict extended with visualization_requested (bool), chart_hint (str), chart_code (str), chart_specs (str), chart_error (str)
- Both invoke and stream initial_state dicts initialize visualization field defaults
- chart_specs and chart_error added to SSE streaming event filter for frontend delivery

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Plotly to allowlist and extend ChatAgentState** - `32a3f86` (feat)
2. **Task 2: Initialize visualization field defaults in agent_service.py** - `12ef1c8` (feat)

## Files Created/Modified
- `backend/app/config/allowlist.yaml` - Added plotly to allowed_libraries list
- `backend/app/agents/state.py` - Added 5 visualization fields to ChatAgentState TypedDict, updated docstring
- `backend/app/services/agent_service.py` - Added visualization defaults to both initial_state dicts, added chart_specs/chart_error to SSE stream filter

## Decisions Made
- Disallow custom JavaScript in Plotly charts: Plotly built-in interactivity (hover, zoom, pan, legend toggle) is sufficient; custom JS opens XSS vectors via prompt injection. Enforced in Visualization Agent prompt (Phase 21), not infrastructure code.
- Plotly NOT added to unsafe_modules or unsafe_operations: pure visualization library with no filesystem or network access; E2B sandbox is the real security boundary.
- Explicit initialization over implicit defaults: documents the contract and prevents KeyError when nodes access visualization state fields.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plotly allowlist ready for Visualization Agent code generation (Phase 21)
- ChatAgentState schema ready to carry chart data through the pipeline (Phase 22)
- SSE streaming ready to deliver chart_specs to frontend ChartRenderer (Phase 23)
- All 111 existing tests pass without modification

## Self-Check: PASSED

- All 3 modified files exist on disk
- Commit `32a3f86` (Task 1) verified in git log
- Commit `12ef1c8` (Task 2) verified in git log
- 20-01-SUMMARY.md created at `.planning/phases/20-infrastructure-pipeline/`

---
*Phase: 20-infrastructure-pipeline*
*Completed: 2026-02-13*
