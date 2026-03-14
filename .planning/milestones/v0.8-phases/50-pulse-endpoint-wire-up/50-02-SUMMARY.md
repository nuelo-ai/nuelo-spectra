---
phase: 50-pulse-endpoint-wire-up
plan: 02
subsystem: api
tags: [fastapi, pulse, scheduler, apscheduler, credits, sqlalchemy]

requires:
  - phase: 50-01
    provides: PulseRunCreate/PulseRunTriggerResponse/PulseRunDetailResponse schemas and PulseService.run_detection/get_pulse_run methods
  - phase: 49
    provides: PulseService lifecycle orchestration (credit deduction, background pipeline, signal persistence)

provides:
  - POST /collections/{collection_id}/pulse — 202 trigger endpoint with 402/409 error handling
  - GET /collections/{collection_id}/pulse-runs/{run_id} — polling endpoint with collection_id cross-check
  - process_orphan_refunds() scheduler job at 5-minute interval
  - 10 passing integration and unit tests covering all endpoint behaviors

affects:
  - Phase 51 (frontend polling loop)
  - Phase 52 (end-to-end smoke tests)

tech-stack:
  added: []
  patterns:
    - Pulse endpoints added to existing collections router (not a new router file)
    - Ownership verification via CollectionService.get_user_collection before PulseService calls
    - collection_id cross-check on PulseRun prevents horizontal ownership bypass
    - Orphan scheduler uses FOR UPDATE SKIP LOCKED to prevent double-refund on concurrent instances
    - Signal count check before refund preserves partially-completed runs

key-files:
  created:
    - backend/tests/test_pulse_endpoints.py
    - backend/tests/test_orphan_refund.py
  modified:
    - backend/app/routers/collections.py
    - backend/app/scheduler.py

key-decisions:
  - "Pulse endpoints added to collections.py (not new router) — matches existing file/report endpoint pattern"
  - "PulseRunDetailResponse built via dict merge (pulse_run.__dict__ + signal_count) to avoid ORM __dict__ pollution from SQLAlchemy internals"
  - "Orphan refund skips runs with signal_count > 0 to avoid refunding partially-completed runs where pipeline crashed after signals were written"
  - "process_orphan_refunds() imports get_settings() lazily inside function body (same pattern as other scheduler functions)"

patterns-established:
  - "Plain Python class for ORM mock objects in tests (not MagicMock) when __dict__ access is needed for model_validate"
  - "Patch app.config.get_settings (not app.scheduler.get_settings) for lazy imports inside scheduler functions"

requirements-completed:
  - PULSE-04
  - PULSE-05

duration: 25min
completed: 2026-03-07
---

# Phase 50 Plan 02: Pulse Endpoint Wire-up Summary

**POST /collections/{id}/pulse and GET /collections/{id}/pulse-runs/{id} endpoints live with orphan-refund scheduler job at 5-minute interval and 10 passing tests**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-07T15:35:00Z
- **Completed:** 2026-03-07T16:00:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Two pulse endpoints wired into existing collections router: trigger (202) and polling (200 with signals on completion)
- Ownership bypass prevention: polling endpoint cross-checks pulse_run.collection_id == collection_id in URL
- Orphan-refund scheduler job registered at 5-minute interval with FOR UPDATE SKIP LOCKED for safe concurrent execution
- 10 tests: 7 endpoint tests (202/402/409/404/poll-pending/poll-completed/ownership-bypass) + 3 orphan job tests (refund/skip-with-signals/rollback-on-error)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pulse trigger and polling endpoints** - `f5d6fcf` (feat)
2. **Task 2: Add orphan-refund scheduler job** - `47c4bf0` (feat)
3. **Task 3: Implement endpoint and orphan tests** - `755290c` (test)

## Files Created/Modified

- `backend/app/routers/collections.py` - Added trigger_pulse and get_pulse_run endpoints plus pulse schema/service imports
- `backend/app/scheduler.py` - Added process_orphan_refunds() function and registered pulse_orphan_refund_job at 5-min interval; added timedelta, func, PulseRun, Signal, Collection imports
- `backend/tests/test_pulse_endpoints.py` - 7 integration tests for trigger and polling endpoints using unittest.mock
- `backend/tests/test_orphan_refund.py` - 3 unit tests for orphan refund job logic

## Decisions Made

- Used plain Python class (not MagicMock) for fake PulseRun objects in polling tests because model_validate accesses `__dict__` and MagicMock's `__dict__` override breaks attribute assignment after creation.
- Patched `app.config.get_settings` (not `app.scheduler.get_settings`) in orphan tests because `get_settings` is a lazy import inside the function body — it resolves from `app.config` module at call time.

## Deviations from Plan

None - plan executed exactly as written. The `signal_count` field was handled via dict merge as suggested in the plan's note.

## Issues Encountered

- MagicMock `__dict__` override broke attribute assignment in polling tests (post-creation `mock_run.id = run_id` raised AttributeError). Fixed by switching mock PulseRun to a plain Python class. No scope change.
- `get_settings` lazy import in scheduler could not be patched at `app.scheduler.get_settings` — patched at `app.config.get_settings` instead. Tests pass.

## Next Phase Readiness

- Both Pulse HTTP endpoints are live and tested — frontend can wire up POST trigger and GET polling loop
- Orphan-refund job protects against silent credit loss for stuck runs
- Full backend test suite passes (pre-existing `test_graph_visualization` failure is unrelated to this phase)

---
*Phase: 50-pulse-endpoint-wire-up*
*Completed: 2026-03-07*
