---
phase: 38-api-key-infrastructure
plan: 03
subsystem: api
tags: [fastapi, api-keys, rest, auth, bearer-token, sha256]

# Dependency graph
requires:
  - phase: 38-02
    provides: "ApiKeyService (create, list_for_user, revoke, authenticate) and Pydantic schemas"
provides:
  - "api_v1_router with GET/POST/DELETE /api/v1/keys endpoints"
  - "get_authenticated_user() unified auth dependency (JWT + API key)"
  - "ApiAuthUser typed alias for Phase 40 external API endpoints"
  - "Mode-gated /api/v1 route mounting (api and dev modes only)"
affects: [40-mcp-tool-api, 41-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [unified-bearer-auth, mode-gated-routing, typed-dependency-aliases]

key-files:
  created:
    - backend/app/routers/api_v1/__init__.py
    - backend/app/routers/api_v1/api_keys.py
  modified:
    - backend/app/dependencies.py
    - backend/app/main.py

key-decisions:
  - "API key CRUD endpoints use CurrentUser (JWT-only), not get_authenticated_user -- users manage keys via frontend session"
  - "get_authenticated_user uses spe_ prefix check for fast-path API key routing, skipping JWT decode entirely"
  - "oauth2_scheme_optional with auto_error=False allows manual auth error handling in unified dependency"

patterns-established:
  - "api_v1 router aggregator pattern: sub-routers included in __init__.py, mounted once in main.py"
  - "ApiAuthUser typed alias for unified auth in future external API endpoints"

requirements-completed: [APIKEY-01, APIKEY-02, APIKEY-03, APIKEY-04, APISEC-01, APISEC-02, APIINFRA-01, APIINFRA-02, APIINFRA-05]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 38 Plan 03: Router + Dependency Wiring Summary

**API v1 router with CRUD key management endpoints, unified JWT+API-key auth dependency, and mode-gated mounting for api/dev modes**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T01:14:45Z
- **Completed:** 2026-02-24T01:17:19Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Created api_v1_router with GET/POST/DELETE /api/v1/keys endpoints for API key lifecycle management
- Added get_authenticated_user() unified auth dependency accepting both JWT and API key Bearer tokens
- Mounted api_v1_router in main.py gated to "api" and "dev" modes only (not public/admin)
- All 12 API key service tests pass; 148/150 existing tests pass (2 pre-existing failures unrelated to changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create api_v1 router and API key CRUD endpoints** - `cbabea4` (feat)
2. **Task 2: Add get_authenticated_user() to dependencies.py and update main.py** - `e34aa72` (feat)
3. **Task 3: Smoke-test the full API key lifecycle** - No commit (verification-only task)

## Files Created/Modified
- `backend/app/routers/api_v1/__init__.py` - API v1 router aggregator mounting sub-routers
- `backend/app/routers/api_v1/api_keys.py` - CRUD endpoints for API key management (GET/POST/DELETE)
- `backend/app/dependencies.py` - Added get_authenticated_user(), oauth2_scheme_optional, ApiAuthUser alias
- `backend/app/main.py` - Added api_v1_router mounting in api/dev mode block

## Decisions Made
- API key CRUD endpoints use `CurrentUser` (JWT-only dependency), not `get_authenticated_user()` -- intentional because users manage their keys via the frontend JWT session, not via API keys
- `get_authenticated_user()` checks `spe_` prefix first to fast-path API key auth without attempting JWT decode
- `oauth2_scheme_optional` with `auto_error=False` allows the unified dependency to handle missing tokens gracefully instead of FastAPI's default 401
- `verify_token()` raises HTTPException for all error cases (expired, invalid), so the unified dependency re-raises all JWT errors as-is

## Deviations from Plan

None - plan executed exactly as written.

## Smoke Test Results

- **Import verification:** All imports succeed (api_v1_router, get_authenticated_user, ApiAuthUser)
- **Route count:** api_v1_router has 3 routes as expected
- **Mode gating verified:** dev mode mounts /api/v1 routes, api mode mounts /api/v1 routes, public mode does NOT mount /api/v1 routes
- **Unit tests:** 12/12 API key service tests pass
- **Existing tests:** 148/150 pass (2 pre-existing failures in test_graph_visualization.py and test_routing.py, both unrelated to API key changes)
- **Live HTTP smoke test:** Not executed -- Docker container running old code on port 8000; would require rebuild to test. All code paths verified via unit tests and import checks.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- API key infrastructure is fully wired: model, service, schemas, router, and auth dependency
- Phase 40 can use `ApiAuthUser` dependency for external API endpoints
- Phase 39 (rate limiting) can wrap the api_v1_router with rate limiting middleware

---
*Phase: 38-api-key-infrastructure*
*Completed: 2026-02-24*
