---
phase: 50-pulse-endpoint-wire-up
plan: "01"
subsystem: backend-pulse
tags: [schemas, service, config, tdd, wave-1]
dependency_graph:
  requires: []
  provides:
    - PulseRunTriggerResponse schema
    - SignalDetailResponse schema
    - PulseRunDetailResponse.signals field
    - PulseService 402/409 dict detail bodies
    - Settings.pulse_orphan_timeout_minutes
    - Wave 0 test stub files
  affects:
    - backend/app/routers/collections.py (Plan 02 consumer)
    - backend/app/scheduler.py (Plan 02 consumer)
tech_stack:
  added: []
  patterns:
    - TDD red-green cycle for schema + service behavior
    - Pre-fetch balance before credit deduction for rich 402 body
key_files:
  created:
    - backend/tests/test_pulse_endpoints.py
    - backend/tests/test_orphan_refund.py
    - backend/tests/test_pulse_schemas_config.py
  modified:
    - backend/app/schemas/pulse.py
    - backend/app/services/pulse.py
    - backend/app/config.py
    - backend/tests/test_pulse_service.py
decisions:
  - UserCredit pre-fetch placed before CreditService.deduct_credit so available_balance is accurate at 402 raise time
  - PulseRunDetailResponse retains signal_count field alongside new signals list for backward compat
metrics:
  duration_seconds: 361
  completed_date: "2026-03-07"
  tasks_completed: 2
  files_changed: 7
---

# Phase 50 Plan 01: Schemas, Service Errors, Config, and Test Stubs Summary

**One-liner:** Extended pulse schemas with SignalDetailResponse/PulseRunTriggerResponse, enriched 402/409 error bodies with balance context and active_run_id, wired PULSE_ORPHAN_TIMEOUT_MINUTES into Settings, and created Wave 0 pytest stub files.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Wave 0 — Create test stub files | 4737f78 | test_pulse_endpoints.py, test_orphan_refund.py |
| 2 (RED) | TDD failing tests for schemas/service/config | 6d259d5 | test_pulse_schemas_config.py |
| 2 (GREEN) | Extend schemas, enhance service errors, add config | 0f56ac8 | schemas/pulse.py, services/pulse.py, config.py, test_pulse_service.py |

## Verification Results

1. `from app.schemas.pulse import PulseRunTriggerResponse, SignalDetailResponse, PulseRunDetailResponse` — import succeeds
2. `s.pulse_orphan_timeout_minutes == 10` — passes
3. `pytest --collect-only test_pulse_endpoints.py test_orphan_refund.py` — 6 tests collected, all skipped
4. Full `test_pulse_schemas_config.py` suite — 13 tests pass (GREEN)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_pulse_service.py mocks for new UserCredit pre-fetch**
- **Found during:** Task 2 (GREEN)
- **Issue:** Adding a UserCredit `db.execute` call before credit deduction changed the call sequence in `_mock_db_for_run_detection`. The helper was wired for 2 calls (active run check + files); now 3 calls are needed (UserCredit + active run + files).
- **Fix:** Updated `_mock_db_for_run_detection` helper to add UserCredit mock as first call; also updated `test_credit_precheck_insufficient` which used plain `_make_mock_db()` without the configured execute.
- **Files modified:** `backend/tests/test_pulse_service.py`
- **Commit:** 0f56ac8

## Pre-existing Failures (not introduced by this plan)

The following test failures were present before this plan's changes and are out of scope:
- `test_graph_visualization.py::TestVizResponseNode` — 2 tests (pre-existing)
- `test_llm_providers.py::TestHealthEndpoint` — 1 test (pre-existing)
- `test_pulse_agent.py` — 9 tests (pre-existing event loop/mock issue)
- `test_routing.py::TestRoutingConfig` — 1 test (YAML config mismatch, pre-existing)
- `test_pulse_service.py` full-suite run — event loop contamination when run after pytest-asyncio tests (pre-existing; tests pass in isolation)

## Self-Check: PASSED
