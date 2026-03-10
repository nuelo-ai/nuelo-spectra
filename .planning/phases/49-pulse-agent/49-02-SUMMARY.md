---
phase: 49-pulse-agent
plan: 02
subsystem: agents
tags: [pulse, langgraph, pipeline, credit, service, e2b, fan-out]

requires:
  - phase: 49-pulse-agent
    provides: PulseAgentOutput schemas, pulse_config.yaml, profile_files_in_sandbox, pulse_agent prompts entry

provides:
  - LangGraph StateGraph pipeline (profile -> analyze -> generate)
  - PulseService with run_detection, _run_pipeline, get_pulse_run
  - Credit pre-check (402) and atomic deduction with refund on failure
  - Fan-out parallel signal validation via asyncio.gather
  - Active run conflict detection (409 with refund)
  - Signal and Report persistence after pipeline success

affects: [50-pulse-api, pulse-routes, frontend-detection]

tech-stack:
  added: []
  patterns:
    - "Stateless LangGraph pipeline -- no message history between Pulse runs"
    - "Fan-out validation via asyncio.gather with return_exceptions=True"
    - "Credit lifecycle: deduct before background task, refund in except block"
    - "Status transitions: pending -> profiling -> analyzing -> completed/failed"

key-files:
  created:
    - backend/app/agents/pulse.py
    - backend/app/services/pulse.py
    - backend/tests/test_pulse_service.py
  modified:
    - backend/tests/test_pulse_agent.py
    - backend/app/models/__init__.py

key-decisions:
  - "Stateless pipeline: each ainvoke() starts fresh, no message history between runs"
  - "Credit deduction before background task launch, refund in except block"
  - "Import models via app.models (registry) not individual model files"

patterns-established:
  - "PulseAgentState TypedDict: flat state for LangGraph, no nested messages list"
  - "PulseService static methods matching CollectionService pattern"
  - "_validate_single_candidate: isolated Coder -> Checker -> E2B per signal candidate"

requirements-completed: [PULSE-02, PULSE-03]

duration: 9min
completed: 2026-03-07
---

# Phase 49 Plan 02: Pulse Agent Pipeline & Service Summary

**LangGraph StateGraph pipeline (profile -> analyze -> generate) with PulseService credit lifecycle, fan-out validation, and signal/report persistence**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-07T02:41:08Z
- **Completed:** 2026-03-07T02:50:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- LangGraph Pulse Agent pipeline with 3 nodes (profile_data, run_analyses, generate_signals) compiles and runs end-to-end
- PulseService.run_detection implements credit pre-check (402), atomic deduction, active run conflict (409 with refund)
- Fan-out parallel validation handles partial failures gracefully (3/5 succeed = completed)
- Background pipeline refunds credits on any exception via try/except
- Signal and Report rows persisted after successful pipeline execution
- PulseRun status transitions through all 5 states (pending -> profiling -> analyzing -> completed/failed)
- All 29 tests pass (21 agent pipeline + 8 service lifecycle)

## Task Commits

Each task was committed atomically:

1. **Task 1: LangGraph Pulse Agent pipeline**
   - `265d99f` (test: failing tests for pipeline nodes and end-to-end)
   - `ce58bb5` (feat: implement LangGraph pipeline with 3 nodes + build_pulse_graph)
2. **Task 2: PulseService lifecycle orchestration**
   - `877b7e9` (test: failing tests for credit pre-check, deduction, refund, persistence)
   - `02143ac` (feat: implement PulseService with credit logic + model import fix)

_TDD tasks have RED (test) + GREEN (feat) commits._

## Files Created/Modified
- `backend/app/agents/pulse.py` - LangGraph pipeline: PulseAgentState, profile_data_node, run_analyses_node, generate_signals_node, build_pulse_graph, _validate_single_candidate
- `backend/app/services/pulse.py` - PulseService: run_detection, _run_pipeline, get_pulse_run
- `backend/tests/test_pulse_agent.py` - Added 10 pipeline tests (21 total with Plan 01 foundation tests)
- `backend/tests/test_pulse_service.py` - 8 unit tests for credit lifecycle, persistence, status transitions
- `backend/app/models/__init__.py` - Added ApiKey to model registry (missing registration)

## Decisions Made
- Stateless pipeline: each `ainvoke()` starts with fresh `PulseAgentState` -- no `messages[]` list, no prior run context
- Credit deduction happens synchronously before `asyncio.create_task()`, refund in except block within `_run_pipeline`
- Import models via `app.models` registry (not individual model files) to ensure SQLAlchemy relationship resolution

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added ApiKey to models/__init__.py**
- **Found during:** Task 2 (PulseService tests)
- **Issue:** Importing PulseRun triggered SQLAlchemy mapper resolution which failed because User -> ApiKey relationship couldn't find the ApiKey class (not registered in models/__init__.py)
- **Fix:** Added `from app.models.api_key import ApiKey` and included in `__all__`
- **Files modified:** backend/app/models/__init__.py
- **Verification:** All 29 tests pass without mapper errors
- **Committed in:** `02143ac` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix necessary for model imports. No scope creep.

## Issues Encountered
None beyond the auto-fixed model registration issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pipeline and service ready for API endpoint wiring in Phase 50
- `PulseService.run_detection()` ready to be called from router
- `PulseService.get_pulse_run()` ready for status polling endpoint
- All contracts (schemas, models, service methods) fully implemented

---
*Phase: 49-pulse-agent*
*Completed: 2026-03-07*
