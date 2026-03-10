---
phase: 47-data-foundation
plan: 01
subsystem: database
tags: [sqlalchemy, models, postgresql, uuid, json-columns]

requires:
  - phase: 46-api-system
    provides: "Base model, User model, File model, alembic env.py"
provides:
  - "Collection and CollectionFile SQLAlchemy models"
  - "Signal model with JSON evidence/chart_data columns"
  - "Report model with nullable pulse_run_id FK"
  - "PulseRun model with NUMERIC credit_cost and pulse_run_files junction table"
  - "All 5 new model classes registered in app.models and alembic env.py"
  - "User.collections relationship with cascade delete-orphan"
affects: [48-crud-api, 49-pulse-agent, 50-detection-api, 51-frontend-workspace]

tech-stack:
  added: []
  patterns:
    - "CollectionFile junction with own UUID PK (not composite) for metadata extensibility"
    - "JSON columns for flexible signal evidence and chart data"
    - "SET NULL ondelete for Report.pulse_run_id (reports survive PulseRun deletion)"

key-files:
  created:
    - backend/app/models/collection.py
    - backend/app/models/signal.py
    - backend/app/models/report.py
    - backend/app/models/pulse_run.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/models/user.py
    - backend/alembic/env.py

key-decisions:
  - "CollectionFile uses __tablename__ = 'collection_files' to avoid collision with existing File model"
  - "Report.pulse_run_id uses ondelete SET NULL so reports persist after PulseRun deletion"

patterns-established:
  - "TYPE_CHECKING guard for all cross-model imports in new Pulse models"
  - "pulse_run_files junction table follows session_files pattern (composite PK, CASCADE deletes)"

requirements-completed: [ADMIN-01]

duration: 2min
completed: 2026-03-06
---

# Phase 47 Plan 01: Data Foundation Models Summary

**5 SQLAlchemy model classes (Collection, CollectionFile, Signal, Report, PulseRun) and pulse_run_files junction table with full relationship graph and User.collections back-populates**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T17:04:31Z
- **Completed:** 2026-03-06T17:06:05Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created 4 new model files with all specified columns, types, constraints, and relationships
- Registered all new models in __init__.py exports, alembic env.py imports, and User.collections relationship
- CollectionFile.__tablename__ = "collection_files" verified no collision with existing File model

## Task Commits

Each task was committed atomically:

1. **Task 1: Create all model files** - `d6fe76d` (feat)
2. **Task 2: Register models in __init__.py, env.py, and user.py** - `be0c328` (feat)

## Files Created/Modified
- `backend/app/models/collection.py` - Collection and CollectionFile model classes
- `backend/app/models/signal.py` - Signal model with JSON evidence/chart_data
- `backend/app/models/report.py` - Report model with nullable pulse_run_id FK (SET NULL)
- `backend/app/models/pulse_run.py` - PulseRun model and pulse_run_files junction table
- `backend/app/models/__init__.py` - Added imports and __all__ entries for all new models
- `backend/app/models/user.py` - Added collections relationship and Collection TYPE_CHECKING import
- `backend/alembic/env.py` - Added collection, signal, report, pulse_run module imports

## Decisions Made
- CollectionFile uses `__tablename__ = "collection_files"` (not "files") to avoid collision with existing File model
- Report.pulse_run_id uses `ondelete="SET NULL"` so reports persist after PulseRun deletion
- PulseRun.credit_cost uses `NUMERIC(10,1)` matching CreditTransaction.amount pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All model classes importable and registered for alembic autogenerate
- Ready for 47-02 migration plan to create database tables
- Ready for Phase 48 CRUD API development against these models

---
*Phase: 47-data-foundation*
*Completed: 2026-03-06*
