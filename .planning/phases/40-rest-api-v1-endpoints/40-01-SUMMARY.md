---
phase: 40-rest-api-v1-endpoints
plan: 01
subsystem: api
tags: [pydantic, sqlalchemy, alembic, fastapi, credit-system, usage-logging]

# Dependency graph
requires:
  - phase: 38-deployment-mode
    provides: "get_authenticated_user() dependency, ApiKeyService, api_keys model"
  - phase: 39-api-key-management-ui
    provides: "API key CRUD endpoints, admin revoke, frontend key management"
provides:
  - "ApiResponse/ApiErrorResponse envelope schemas for all API v1 endpoints"
  - "ERROR_CODES catalog with 13 machine-readable error codes"
  - "api_error() helper for consistent error responses"
  - "ApiUsageLog model + migration for per-request usage tracking"
  - "ApiUsageService.log_request() for usage logging"
  - "CreditService.refund() for credit return on failed API queries"
  - "get_authenticated_user() stores api_key_id on request.state"
  - "ApiKeyService.authenticate() returns (User, api_key_id) tuple"
affects: [40-02, 40-03, 41-mcp-server]

# Tech tracking
tech-stack:
  added: []
  patterns: [api-envelope-response, usage-logging-service, credit-refund-pattern, request-state-api-key-tracking]

key-files:
  created:
    - backend/app/routers/api_v1/schemas.py
    - backend/app/models/api_usage_log.py
    - backend/app/services/api_usage.py
    - backend/alembic/versions/b23105e2d79f_add_api_usage_logs_table.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/services/credit.py
    - backend/app/services/api_key.py
    - backend/app/dependencies.py
    - backend/tests/test_api_key_service.py

key-decisions:
  - "CreditService.refund() uses SELECT FOR UPDATE pattern matching deduct_credit for atomicity"
  - "ApiKeyService.authenticate() returns tuple (User, api_key_id) instead of just User — enables downstream api_key_id tracking"
  - "Cleaned Alembic migration of unrelated checkpoint/chat_messages schema drift — only api_usage_logs changes kept"
  - "CreditTransaction with transaction_type='api_refund' for audit trail on refunded credits"

patterns-established:
  - "API envelope pattern: all v1 responses use ApiResponse or ApiErrorResponse wrappers"
  - "Error code catalog: ERROR_CODES dict maps machine-readable codes to default human messages"
  - "Usage logging: ApiUsageService.log_request() called per API v1 request with timing and credit data"
  - "request.state.api_key_id: available on all authenticated API v1 requests for usage tracking"

requirements-completed: [APISEC-03, APISEC-04, APIINFRA-04]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 40 Plan 01: Shared Foundation Summary

**API v1 envelope schemas, ApiUsageLog model with migration, CreditService.refund(), and auth dependency api_key_id tracking**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T16:29:09Z
- **Completed:** 2026-02-24T16:32:25Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- API v1 envelope schemas (ApiResponse, ApiErrorResponse, ApiErrorDetail) with 13-code error catalog and api_error() helper
- ApiUsageLog model + clean Alembic migration for per-request usage tracking with user, key, endpoint, timing, credits, and error code
- CreditService.refund() with atomic SELECT FOR UPDATE pattern for credit return on failed API queries
- Enhanced auth: ApiKeyService.authenticate() returns (User, api_key_id) tuple; get_authenticated_user() stores api_key_id on request.state

## Task Commits

Each task was committed atomically:

1. **Task 1: Create API v1 envelope schemas and error code catalog** - `92ca56d` (feat)
2. **Task 2: Create ApiUsageLog model, migration, and ApiUsageService** - `f71e5ad` (feat)
3. **Task 3: Add CreditService.refund(), enhance auth with api_key_id tracking** - `6699359` (feat)

## Files Created/Modified
- `backend/app/routers/api_v1/schemas.py` - API v1 envelope schemas, error codes, api_error helper
- `backend/app/models/api_usage_log.py` - ApiUsageLog SQLAlchemy model for usage tracking
- `backend/app/services/api_usage.py` - ApiUsageService with log_request() static method
- `backend/alembic/versions/b23105e2d79f_add_api_usage_logs_table.py` - Migration for api_usage_logs table
- `backend/app/models/__init__.py` - Added ApiUsageLog to model registry
- `backend/app/services/credit.py` - Added CreditService.refund() method
- `backend/app/services/api_key.py` - authenticate() now returns (User, api_key_id) tuple
- `backend/app/dependencies.py` - get_authenticated_user() accepts Request, stores api_key_id on state
- `backend/tests/test_api_key_service.py` - Updated test for authenticate() tuple return

## Decisions Made
- CreditService.refund() uses SELECT FOR UPDATE pattern matching deduct_credit for atomicity
- ApiKeyService.authenticate() returns tuple (User, api_key_id) instead of just User to enable downstream api_key_id tracking
- Cleaned Alembic migration of unrelated checkpoint/chat_messages schema drift - only api_usage_logs changes kept
- CreditTransaction with transaction_type='api_refund' for audit trail on refunded credits

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test for authenticate() return type change**
- **Found during:** Task 3 (CreditService.refund, auth enhancement)
- **Issue:** Existing test asserted `result is mock_user` but authenticate() now returns `(user, api_key_id)` tuple
- **Fix:** Updated test to unpack tuple and assert both user and api_key_id
- **Files modified:** backend/tests/test_api_key_service.py
- **Verification:** All 12 tests pass
- **Committed in:** `6699359` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test update was necessary consequence of authenticate() return type change. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Shared foundation complete: Plans 02 (file endpoints) and 03 (analysis endpoints) can use envelope schemas, usage logging, credit refund, and api_key_id tracking
- All existing tests pass (12/12 in test_api_key_service.py)
- Alembic migration ready to apply on deployment

---
*Phase: 40-rest-api-v1-endpoints*
*Completed: 2026-02-24*
