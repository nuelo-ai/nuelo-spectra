---
phase: 20-infrastructure-pipeline
plan: 02
subsystem: infra
tags: [plotly, e2b, sandbox, chart-json, output-parser, integration-test]

# Dependency graph
requires:
  - phase: 20-01
    provides: "Plotly allowlist + ChatAgentState visualization fields (chart_specs, chart_error)"
provides:
  - "execute_in_sandbox extracts optional chart JSON from dual-key stdout contract"
  - "chart_specs and chart_error fields populated in success/error return paths"
  - "2MB chart JSON size validation with user-friendly error message"
  - "E2B Plotly 6.0.1 verified via integration tests"
  - "fig.to_json() produces valid Plotly JSON with data and layout keys"
affects: [21-visualization-agent, 22-pipeline-integration, 24-chart-types]

# Tech tracking
tech-stack:
  added: []
  patterns: [dual-key-output-contract, chart-json-extraction, joined-stdout-fallback]

key-files:
  created:
    - backend/tests/test_plotly_availability.py
  modified:
    - backend/app/agents/graph.py

key-decisions:
  - "Single-line JSON parsing first (fast path), joined stdout fallback for large chart JSON spanning multiple list items"
  - "2MB chart JSON size limit -- exceeding triggers chart_error instead of silent discard"
  - "Plotly version acceptance: both 5.x and 6.x accepted (E2B confirmed 6.0.1)"

patterns-established:
  - "Dual-key output contract: {\"result\": ..., \"chart\": ...} for combined tabular + chart data"
  - "Chart error isolation: chart_error captures failures without breaking data pipeline"
  - "Integration test skip pattern: pytestmark skipif for tests requiring external API keys"

# Metrics
duration: 2min
completed: 2026-02-13
---

# Phase 20 Plan 02: Infrastructure & Pipeline - Output Parser + E2B Verification Summary

**Chart JSON extraction in execute_in_sandbox with 2MB size limit, E2B Plotly 6.0.1 verified via integration tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-13T12:56:15Z
- **Completed:** 2026-02-13T12:59:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- execute_in_sandbox now extracts optional `chart` key from stdout JSON and returns `chart_specs` + `chart_error` fields
- Chart JSON validated at 2MB limit -- oversized charts produce user-friendly error message instead of silent failure
- E2B sandbox confirmed Plotly 6.0.1 with working fig.to_json() producing valid data/layout JSON structure
- All 114 backend tests pass (111 existing + 3 new Plotly integration tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend execute_in_sandbox to extract chart JSON from stdout** - `63657a1` (feat)
2. **Task 2: Create E2B Plotly availability verification tests** - `0f023a8` (test)

## Files Created/Modified
- `backend/app/agents/graph.py` - Extended execute_in_sandbox success handler to extract chart JSON, added chart_specs/chart_error to return dicts in all paths (success, retry, halt)
- `backend/tests/test_plotly_availability.py` - 3 integration tests: version check (6.0.1), fig.to_json() validation, backward-compatible single-key output

## Decisions Made
- Single-line parsing first, joined stdout fallback: Fast path checks individual reversed stdout lines (existing behavior), then falls back to joining all stdout lines for chart JSON that may span multiple list items. This handles E2B stdout buffer splitting without impacting performance for normal-sized output.
- 2MB chart JSON size limit: Charts exceeding 2MB are discarded with `chart_error = "Chart data too large. Try aggregating data before charting."` rather than silently dropped. This aligns with the user constraint of transparent error visibility.
- Accept Plotly 5.x or 6.x: Tests accept both major versions (E2B confirmed 6.0.1). This provides forward compatibility if E2B updates their sandbox image.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required. E2B API key is already configured from previous phases.

## Next Phase Readiness
- Output parser ready to receive chart JSON from Visualization Agent code (Phase 21)
- chart_specs field flows through ChatAgentState to SSE streaming (configured in 20-01)
- E2B Plotly 6.0.1 confirmed -- Visualization Agent can use `plotly.express` and `plotly.io.to_json()`
- Backward compatibility verified -- existing tabular-only code execution unchanged
- All 114 tests pass without modification

## Self-Check: PASSED

- All 2 modified/created files exist on disk
- Commit `63657a1` (Task 1) verified in git log
- Commit `0f023a8` (Task 2) verified in git log
- 20-02-SUMMARY.md created at `.planning/phases/20-infrastructure-pipeline/`

---
*Phase: 20-infrastructure-pipeline*
*Completed: 2026-02-13*
