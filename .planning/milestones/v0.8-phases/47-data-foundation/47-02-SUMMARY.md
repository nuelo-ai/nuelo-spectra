---
phase: 47-data-foundation
plan: 02
subsystem: database
tags: [alembic, migration, yaml-config, platform-settings, tdd]

requires:
  - phase: 47-01
    provides: "SQLAlchemy models for Collection, CollectionFile, PulseRun, Signal, Report"
provides:
  - "Alembic migration creating 6 Pulse workspace tables"
  - "Workspace tier config (workspace_access, max_active_collections) in user_classes.yaml"
  - "workspace_credit_cost_pulse platform setting with validation"
  - "20 passing tests covering ADMIN-01 and ADMIN-02 requirements"
affects: [48-workspace-crud, 49-pulse-agent, 50-detection-signals, 51-reports]

tech-stack:
  added: []
  patterns: ["Hand-written Alembic migrations for FK-dependency ordering", "TDD for config changes"]

key-files:
  created:
    - backend/alembic/versions/f47a0001b000_add_pulse_workspace_tables.py
    - backend/tests/test_user_classes_workspace.py
    - backend/tests/test_platform_settings_pulse.py
    - backend/tests/test_models_import.py
  modified:
    - backend/app/config/user_classes.yaml
    - backend/app/services/platform_settings.py

key-decisions:
  - "Hand-written migration over autogenerate for correct FK ordering"
  - "workspace_credit_cost_pulse stored as JSON string '5.0' matching default_credit_cost pattern"

patterns-established:
  - "Workspace tier config: workspace_access (bool) and max_active_collections (int, -1=unlimited)"

requirements-completed: [ADMIN-01, ADMIN-02]

duration: 2min
completed: 2026-03-06
---

# Phase 47 Plan 02: Migration & Config Summary

**Alembic migration for 6 Pulse workspace tables, workspace tier config with access controls, and workspace_credit_cost_pulse platform setting with TDD validation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T17:08:27Z
- **Completed:** 2026-03-06T17:10:26Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created Alembic migration (f47a0001b000) that creates collections, collection_files, pulse_runs, pulse_run_files, signals, and reports tables in correct FK-dependency order
- Added workspace_access (boolean) and max_active_collections (integer) to all 5 tiers in user_classes.yaml with correct defaults
- Added workspace_credit_cost_pulse to platform_settings DEFAULTS (5.0) with positive-number validation
- 20 tests passing across 3 test files verifying ADMIN-01 and ADMIN-02 requirements

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Tests for ADMIN-01 and ADMIN-02** - `d4bdffe` (test)
2. **Task 1 (GREEN): Implement config changes** - `0ef934e` (feat)
3. **Task 2: Alembic migration** - `171108b` (feat)

## Files Created/Modified
- `backend/alembic/versions/f47a0001b000_add_pulse_workspace_tables.py` - Migration creating all 6 Pulse workspace tables
- `backend/app/config/user_classes.yaml` - Added workspace_access and max_active_collections to all 5 tiers
- `backend/app/services/platform_settings.py` - Added workspace_credit_cost_pulse default and validation
- `backend/tests/test_user_classes_workspace.py` - 4 tests for ADMIN-01 tier config
- `backend/tests/test_platform_settings_pulse.py` - 9 tests for ADMIN-02 platform setting
- `backend/tests/test_models_import.py` - 7 smoke tests for model imports

## Decisions Made
- Hand-written migration over autogenerate to guarantee correct FK-dependency ordering (collections first, then dependents)
- workspace_credit_cost_pulse stored as JSON string "5.0" matching the existing default_credit_cost pattern in DEFAULTS

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 47 (Data Foundation) is now complete: all models (Plan 01) and migration + config (Plan 02) are in place
- Phase 48 (Workspace CRUD) and Phase 49 (Pulse Agent) are both unblocked
- Migration file ready for `alembic upgrade head` on deployment

## Self-Check: PASSED

All 7 files found. All 3 commits verified (d4bdffe, 0ef934e, 171108b).

---
*Phase: 47-data-foundation*
*Completed: 2026-03-06*
