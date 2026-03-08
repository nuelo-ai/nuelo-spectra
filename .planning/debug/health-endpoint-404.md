---
status: diagnosed
trigger: "Diagnose why GET /api/v1/health returns 404"
created: 2026-02-24T00:00:00Z
updated: 2026-02-24T00:00:00Z
---

## Current Focus

hypothesis: Router prefix is /v1, not /api/v1. No prefix added at include time. Actual route is /v1/health.
test: Read router definition and include_router call
expecting: Missing /api prefix
next_action: Report diagnosis

## Symptoms

expected: GET /api/v1/health returns 200 with health status
actual: GET /api/v1/health returns 404
errors: 404 Not Found
reproduction: curl /api/v1/health
started: Since router was created with prefix="/v1"

## Eliminated

(none needed - root cause confirmed on first pass)

## Evidence

- timestamp: 2026-02-24
  checked: backend/app/routers/api_v1/__init__.py line 8
  found: APIRouter(prefix="/v1", tags=["API v1"])
  implication: Router only contributes /v1 prefix

- timestamp: 2026-02-24
  checked: backend/app/routers/api_v1/health.py line 17
  found: @router.get("/health") with no prefix on sub-router
  implication: Health endpoint is at /health relative to parent router

- timestamp: 2026-02-24
  checked: backend/app/main.py line 350
  found: app.include_router(api_v1_router) with NO prefix argument
  implication: No /api prefix added at mount time

- timestamp: 2026-02-24
  checked: Docstring in __init__.py line 1
  found: "Mounted at /api/v1 in api and dev modes" — intent was /api/v1
  implication: The docstring documents intended behavior but code doesn't match

## Resolution

root_cause: |
  The api_v1_router is created with prefix="/v1" (line 8 of __init__.py).
  It is included in main.py at line 350 with app.include_router(api_v1_router)
  and NO prefix argument. The resulting route is /v1/health, not /api/v1/health.
  The docstring says "Mounted at /api/v1" but the code only produces /v1.

fix: |
  Option A (preferred): Change the router prefix from "/v1" to "/api/v1" in __init__.py line 8:
    api_v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])

  Option B: Add prefix at include time in main.py line 350:
    app.include_router(api_v1_router, prefix="/api")

files_changed:
  - backend/app/routers/api_v1/__init__.py (Option A)
  - OR backend/app/main.py (Option B)
