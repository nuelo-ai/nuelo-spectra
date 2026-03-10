---
phase: 54-pulse-analysis-fixes
plan: "01"
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, typescript, react-query, collections, pulse]

# Dependency graph
requires:
  - phase: 48-collections-router
    provides: CollectionService.get_collection_detail + CollectionDetailResponse schema
  - phase: 52-pulse-detection
    provides: PulseRun model with credit_cost and status fields
provides:
  - credits_used aggregate subquery in CollectionService.get_collection_detail
  - credits_used: float field on CollectionDetailResponse schema
  - credits_used passed through router GET /collections/{id}
  - credits_used: number on CollectionDetail TypeScript interface
  - Collection Overview Credits Used stat card wired to actual cumulative spend
affects: [workspace-frontend, collection-detail-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - COALESCE(SUM(credit_cost), 0.0) correlated scalar_subquery for safe aggregate with null guard
    - Pydantic field with default (credits_used: float = 0.0) for backward compat
    - TDD RED→GREEN on new API field: write failing test first, then implement

key-files:
  created: []
  modified:
    - backend/app/services/collection.py
    - backend/app/schemas/collection.py
    - backend/app/routers/collections.py
    - backend/tests/test_collections.py
    - frontend/src/types/workspace.ts
    - frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx

key-decisions:
  - "Use COALESCE(SUM(credit_cost), 0.0) correlated subquery to return 0.0 when no completed runs exist (not null)"
  - "float(row[4]) cast in service to ensure Python float regardless of SQLAlchemy NUMERIC return type"
  - "credits_used: float = 0.0 default in schema for backward compatibility with create_collection response (no runs at creation)"
  - "Pre-existing test failures in test_code_checker.py, test_pulse_agent.py, test_pulse_service.py, test_routing.py, test_user_classes_workspace.py are out of scope — confirmed pre-existing before this plan"

patterns-established:
  - "New aggregate field pattern: add correlated scalar_subquery to service SELECT, update return dict, add to schema, pass through router"

requirements-completed: [PULSE-01]

# Metrics
duration: 5min
completed: 2026-03-10
---

# Phase 54 Plan 01: Credits Used Aggregate Summary

**COALESCE(SUM(credit_cost)) correlated subquery added to Collection Detail API; Collection Overview Credits Used card now shows actual cumulative spend instead of cost-per-run config value**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-10T16:17:23Z
- **Completed:** 2026-03-10T16:22:22Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Backend service adds `credits_used` aggregate via correlated scalar_subquery on `PulseRun` with `status == "completed"`, guarded by `COALESCE(..., 0.0)` so collections with no completed runs return `0.0` not null
- Pydantic schema `CollectionDetailResponse` gains `credits_used: float = 0.0` field; router passes it through in both `get_collection` and `update_collection` endpoints
- Frontend `CollectionDetail` TypeScript interface gains `credits_used: number`; Collection Overview `OverviewStatCards` now reads `collection?.credits_used` (real spend) instead of `creditCosts?.pulse_run` (cost-per-run platform config)
- Two new TDD tests verify zero-spend and nonzero-spend cases; all 22 collection tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add credits_used test (RED)** - `8bd1e18` (test)
2. **Task 2: Backend service + schema + router (GREEN)** - `b8e140e` (feat)
3. **Task 3: Frontend TS type + page wiring** - `2532c5c` (feat)

**Plan metadata:** _(final docs commit below)_

_Note: TDD tasks have separate test and implementation commits (RED → GREEN)_

## Files Created/Modified

- `backend/app/services/collection.py` - Added PulseRunModel import and credits_used correlated subquery; updated return dict
- `backend/app/schemas/collection.py` - Added `credits_used: float = 0.0` to `CollectionDetailResponse`
- `backend/app/routers/collections.py` - Pass `credits_used=detail["credits_used"]` in get_collection and update_collection responses
- `backend/tests/test_collections.py` - Two new `TestCreditsUsed` tests; existing mocks updated with `credits_used` key
- `frontend/src/types/workspace.ts` - Added `credits_used: number` to `CollectionDetail` interface
- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` - `creditsUsed={collection?.credits_used ?? 0}` replaces `creditsUsed={creditCosts?.pulse_run ?? 0}`

## Decisions Made

- COALESCE(SUM(credit_cost), 0.0) pattern chosen over post-query None check to keep aggregate logic in SQL and guarantee float output from DB
- Explicit `float(row[4])` cast in service to handle SQLAlchemy NUMERIC returning Decimal in some DB configurations
- Schema default `= 0.0` ensures `create_collection` response (which constructs `CollectionDetailResponse` directly with no runs) remains valid without passing `credits_used`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated pre-existing test mock fixtures to include credits_used key**
- **Found during:** Task 3 (full test suite run)
- **Issue:** `test_get_collection_detail` and `test_update_collection` mocked `get_collection_detail` return without `credits_used` key; router now accesses `detail["credits_used"]` causing KeyError
- **Fix:** Added `"credits_used": 0.0` to both mock `return_value` dicts
- **Files modified:** `backend/tests/test_collections.py`
- **Verification:** All 22 tests in `test_collections.py` pass
- **Committed in:** `2532c5c` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug: test mock missing new key)
**Impact on plan:** Necessary correctness fix — tests broke because router now accesses credits_used. No scope creep.

## Issues Encountered

Pre-existing test failures confirmed out of scope (failed before this plan's changes):
- `test_code_checker.py::TestDisallowedImports::test_disallowed_plotly_express`
- Multiple `test_pulse_agent.py`, `test_pulse_service.py`, `test_routing.py`, `test_user_classes_workspace.py` failures

All logged to deferred-items for separate follow-up.

## Next Phase Readiness

- Collection Detail API now returns correct `credits_used` cumulative spend value
- Collection Overview UI displays actual spend instead of config cost-per-run
- Ready for further Pulse Analysis Fixes (Phase 54 subsequent plans if any)

---
*Phase: 54-pulse-analysis-fixes*
*Completed: 2026-03-10*

## Self-Check: PASSED

- All 5 modified/created files exist on disk
- All 3 task commits (8bd1e18, b8e140e, 2532c5c) present in git log
- 22/22 test_collections.py tests pass
