---
phase: 11-web-search-tool-integration
plan: 01
subsystem: api
tags: [serper, httpx, web-search, search-quota, sqlalchemy, alembic, fastapi]

# Dependency graph
requires:
  - phase: 07-multi-llm-provider-infrastructure
    provides: Settings pattern, config.py structure
  - phase: 08-session-memory-with-postgresql-checkpointing
    provides: Alembic migration pattern, checkpoint table cleanup precedent
provides:
  - SearchService HTTP client for Serper.dev API
  - SearchQuota model for daily per-user search tracking
  - Search configuration (YAML defaults + Settings fields)
  - ChatAgentState extended with web_search_enabled and search_sources
  - ChatQueryRequest with web_search_enabled field
  - StreamEventType search event types (started, completed, failed, quota_exceeded)
  - GET /search/config endpoint for frontend configuration check
affects: [11-02-agent-integration, 11-03-frontend, future-tool-infrastructure]

# Tech tracking
tech-stack:
  added: []
  patterns: [SearchService factory pattern (from_settings classmethod), composite PK model, YAML config for feature defaults]

key-files:
  created:
    - backend/app/services/search.py
    - backend/app/models/search_quota.py
    - backend/app/config/search.yaml
    - backend/app/routers/search.py
    - backend/alembic/versions/e49613642cfe_add_search_quotas_table.py
  modified:
    - backend/app/config.py
    - backend/app/models/__init__.py
    - backend/app/agents/state.py
    - backend/app/schemas/chat.py
    - backend/app/main.py
    - backend/alembic/env.py

key-decisions:
  - "SearchService uses httpx.AsyncClient for Serper.dev API calls with structured JSON logging"
  - "SearchQuota uses composite PK (user_id, search_date) for daily tracking without auto-increment"
  - "Alembic migration manually cleaned to exclude LangGraph checkpoint table references"
  - "Routing event types formalized in StreamEventType enum (were raw strings before)"

patterns-established:
  - "SearchService.from_settings() factory: Returns None when not configured, enabling graceful degradation"
  - "Search YAML config: Externalized feature defaults alongside existing prompts.yaml and llm_providers.yaml"
  - "Composite PK model pattern: (user_id, date) for per-user daily tracking tables"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 11 Plan 01: Backend Search Infrastructure Summary

**SearchService HTTP client for Serper.dev with SearchQuota daily tracking, search config YAML, state/schema extensions, and search config API endpoint**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T13:12:05Z
- **Completed:** 2026-02-09T13:15:30Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- SearchService class with async Serper.dev HTTP client, domain blocking, timeout handling, and structured JSON logging
- SearchQuota model with composite primary key (user_id, search_date) tracking daily search count per user
- ChatAgentState extended with web_search_enabled and search_sources fields for agent integration
- ChatQueryRequest accepts web_search_enabled boolean from frontend (default: False)
- StreamEventType extended with search events (started, completed, failed, quota_exceeded) and routing events
- GET /search/config endpoint returns configuration status and quota info for authenticated users
- All 99 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: SearchService, SearchQuota model, config, and migration** - `5703f72` (feat)
2. **Task 2: State extension, schema update, and search config router** - `cc6f619` (feat)

## Files Created/Modified
- `backend/app/services/search.py` - SearchService class with Serper.dev API client, SearchResult/SearchResponse dataclasses
- `backend/app/models/search_quota.py` - SearchQuota SQLAlchemy model with composite PK (user_id, search_date)
- `backend/app/config/search.yaml` - Search feature configuration defaults (quota, results count, timeout, blocklist)
- `backend/app/routers/search.py` - Search config endpoint returning configured/enabled/quota status
- `backend/alembic/versions/e49613642cfe_add_search_quotas_table.py` - Migration creating search_quotas table
- `backend/app/config.py` - Added serper_api_key, search_max_per_query, search_daily_quota, search_num_results, search_timeout
- `backend/app/models/__init__.py` - Added SearchQuota import for Alembic discovery
- `backend/app/agents/state.py` - Added web_search_enabled and search_sources fields to ChatAgentState
- `backend/app/schemas/chat.py` - Added web_search_enabled to ChatQueryRequest, search/routing events to StreamEventType
- `backend/app/main.py` - Wired search router into FastAPI app
- `backend/alembic/env.py` - Added search_quota model import

## Decisions Made
- SearchService uses `httpx.AsyncClient` with configurable timeout (default 10s) for Serper.dev API calls
- Structured JSON logging via `json.dumps()` for all search operations (success, timeout, error)
- SearchQuota uses composite primary key (user_id, search_date) rather than auto-increment ID for efficient daily lookups
- Alembic migration cleaned of checkpoint table references (same pattern as Phase 10 Plan 1)
- Routing event types (routing_started, routing_decided) formalized in StreamEventType enum -- previously only existed as raw strings in manager.py

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

**External services require manual configuration.** The Serper.dev API key must be configured:
- Set `SERPER_API_KEY` environment variable in backend `.env` file
- Get key from https://serper.dev (Dashboard -> API Key)
- Without this key, SearchService.from_settings() returns None and search toggle will be grayed out in frontend

## Next Phase Readiness
- SearchService, SearchQuota, and config are ready for Plan 02 (agent integration with bind_tools/ToolNode)
- State fields (web_search_enabled, search_sources) ready for graph topology changes
- Search config endpoint ready for Plan 03 (frontend toggle and sources display)
- All building blocks in place -- Plan 02 creates no new models/services, only wires them into the agent graph

## Self-Check: PASSED

All 5 created files verified on disk. Both task commits (5703f72, cc6f619) verified in git log. 99/99 existing tests pass.

---
*Phase: 11-web-search-tool-integration*
*Completed: 2026-02-09*
