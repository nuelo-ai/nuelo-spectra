---
phase: 38-api-key-infrastructure
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, postgresql, api-key, pydantic]

# Dependency graph
requires: []
provides:
  - ApiKey SQLAlchemy model with 11 columns
  - Alembic migration b3f8a1c2d4e5 creating api_keys table
  - User.api_keys relationship with cascade delete-orphan
  - SPECTRA_MODE=api accepted by Settings and main.py
affects: [38-02, 38-03, 38-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PG_ARRAY(String) for forward-compatible scopes column"
    - "field_validator on spectra_mode for early rejection of unknown modes"

key-files:
  created:
    - backend/app/models/api_key.py
    - backend/alembic/versions/b3f8a1c2d4e5_add_api_keys_table.py
  modified:
    - backend/app/models/user.py
    - backend/alembic/env.py
    - backend/app/config.py
    - backend/app/main.py

key-decisions:
  - "Manual Alembic migration (no local DB for autogenerate) — verified via script loading and Alembic HEAD detection"
  - "Added field_validator on spectra_mode to reject unknown modes at Settings level before main.py check"

patterns-established:
  - "ApiKey model follows Invitation/PasswordResetToken pattern: UUID PK, ForeignKey to users, DateTime(timezone=True)"
  - "TYPE_CHECKING guard for bidirectional model imports (ApiKey<->User)"

requirements-completed: [APIKEY-04, APIKEY-05, APIINFRA-01, APIINFRA-02, APIINFRA-05]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 38 Plan 01: Data Foundation Summary

**ApiKey SQLAlchemy model with 11 columns, Alembic migration, User relationship cascade, and SPECTRA_MODE=api config acceptance**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T01:05:42Z
- **Completed:** 2026-02-24T01:08:22Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Created ApiKey model with all 11 columns (id, user_id, name, description, key_prefix, token_hash, is_active, scopes, expires_at, last_used_at, created_at)
- Added User.api_keys relationship with cascade delete-orphan for automatic cleanup
- Created Alembic migration b3f8a1c2d4e5 with api_keys table, unique token_hash index, and user_id index
- Added SPECTRA_MODE=api support in config.py (with field_validator) and main.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ApiKey model and update User relationship** - `c73b063` (feat)
2. **Task 2: Add api_key model to alembic env.py and generate migration** - `9491bae` (feat)
3. **Task 3: Accept SPECTRA_MODE=api in config.py** - `c19dbb4` (feat)

## Files Created/Modified
- `backend/app/models/api_key.py` - ApiKey SQLAlchemy model with 11 columns and User relationship
- `backend/app/models/user.py` - Added api_keys relationship with cascade delete-orphan
- `backend/alembic/env.py` - Added api_key to model imports for autogenerate
- `backend/alembic/versions/b3f8a1c2d4e5_add_api_keys_table.py` - Migration creating api_keys table with indexes
- `backend/app/config.py` - Added "api" to spectra_mode allowed values with field_validator
- `backend/app/main.py` - Updated mode validation to include "api"

## Decisions Made
- Wrote Alembic migration manually since no local PostgreSQL database was running for autogenerate; verified correctness via module loading and Alembic HEAD detection
- Added field_validator on spectra_mode in Settings to reject unknown modes at construction time (earlier than main.py runtime check)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated main.py mode validation to include "api"**
- **Found during:** Task 3 (Accept SPECTRA_MODE=api in config.py)
- **Issue:** main.py line 291 had a hard-coded mode check `if mode not in ("public", "admin", "dev")` that would raise ValueError even after config.py accepts "api"
- **Fix:** Added "api" to the allowed modes tuple in main.py
- **Files modified:** backend/app/main.py
- **Verification:** Settings(spectra_mode='api') constructs without error
- **Committed in:** c19dbb4 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for "api" mode to work end-to-end. No scope creep.

## Issues Encountered
- No local PostgreSQL database running, so `alembic revision --autogenerate` failed with connection error. Wrote migration manually following existing codebase patterns (e49613642cfe_add_search_quotas_table.py). Verified via Alembic script directory HEAD detection.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ApiKey model and migration ready for Plan 02 (API key service layer with SHA-256 hashing)
- User.api_keys relationship enables cascade operations in service layer
- SPECTRA_MODE=api accepted, ready for Plan 03 mode-gated routing

## Self-Check: PASSED

All 7 files verified present. All 3 task commits verified in git log.

---
*Phase: 38-api-key-infrastructure*
*Completed: 2026-02-24*
