---
phase: 40-rest-api-v1-endpoints
plan: 03
subsystem: api
tags: [fastapi, langgraph, credits, middleware, logging, starlette]

# Dependency graph
requires:
  - phase: 40-01
    provides: "Shared foundation (schemas, dependencies, health, api_keys endpoints)"
provides:
  - "POST /v1/chat/query synchronous analysis endpoint with credit handling"
  - "run_api_query() stateless agent function (no checkpointer)"
  - "ApiUsageMiddleware structured logging for all /v1/ requests"
  - "DB usage logging via ApiUsageService in credit-consuming endpoints"
affects: [41-mcp-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Stateless graph compilation (checkpointer=None) for API queries", "Hybrid logging: middleware for structured logs + explicit DB logging for credit tracking"]

key-files:
  created:
    - backend/app/routers/api_v1/query.py
    - backend/app/middleware/api_usage.py
  modified:
    - backend/app/services/agent_service.py
    - backend/app/routers/api_v1/__init__.py
    - backend/app/main.py

key-decisions:
  - "Hybrid logging approach: middleware does structured Python logging, DB logging done explicitly in query endpoint to avoid session lifecycle issues"
  - "build_chat_graph(checkpointer=None) instead of get_or_create_graph() to avoid polluting cached graph instance"
  - "Messages included directly in initial_state (not via aupdate_state) since no checkpointer exists"

patterns-established:
  - "Stateless API queries: build_chat_graph(checkpointer=None) + random thread_id"
  - "Credit flow: deduct -> commit -> execute -> refund on failure"

requirements-completed: [APIQ-01, APISEC-03, APISEC-04, APIINFRA-04]

# Metrics
duration: 3min
completed: 2026-02-24
---

# Phase 40 Plan 03: Query Endpoint and Usage Logging Summary

**POST /v1/chat/query with credit deduction/refund, stateless LangGraph agent invocation, and structured API usage logging middleware**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-24T16:35:01Z
- **Completed:** 2026-02-24T16:38:04Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- POST /v1/chat/query endpoint accepts query + file_ids, validates ownership, deducts credits, runs stateless analysis, refunds on failure
- run_api_query() compiles graph with checkpointer=None for zero-persistence API invocation
- ApiUsageMiddleware logs all /v1/ requests with timing/status via structured Python logging
- DB usage logging in query endpoint captures user_id, api_key_id, credits_used, response_time_ms
- api_key.total_credits_used incremented per successful query

## Task Commits

Each task was committed atomically:

1. **Task 1: Create run_api_query() and query endpoint with credit handling** - `49caa2c` (feat)
2. **Task 2: Create API usage logging middleware and wire into application** - `750ec62` (feat)

## Files Created/Modified
- `backend/app/routers/api_v1/query.py` - POST /chat/query endpoint with credit deduction, file validation, refund on failure
- `backend/app/services/agent_service.py` - Added run_api_query() stateless agent function
- `backend/app/routers/api_v1/__init__.py` - Registered query router in api_v1_router
- `backend/app/middleware/api_usage.py` - ApiUsageMiddleware with structured logging for /v1/ requests
- `backend/app/main.py` - Wired ApiUsageMiddleware for api/dev modes

## Decisions Made
- Hybrid logging approach: middleware does structured Python logging (lightweight, no DB dependency), while DB-level usage logging with credits is done explicitly in the query endpoint. This avoids BaseHTTPMiddleware running before FastAPI dependencies and the associated session lifecycle complications.
- Used build_chat_graph(checkpointer=None) directly instead of get_or_create_graph() to avoid replacing the cached graph instance with a checkpointer-less version.
- Messages included directly in initial_state dict rather than via graph.aupdate_state() since there is no checkpointer to persist state.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All API v1 endpoints complete (health, keys, files, context, query)
- Ready for Phase 41 MCP integration which calls these endpoints via httpx loopback

---
*Phase: 40-rest-api-v1-endpoints*
*Completed: 2026-02-24*
