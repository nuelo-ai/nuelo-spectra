---
phase: 41-mcp-server
plan: 02
subsystem: api
tags: [mcp, fastmcp, fastapi, lifespan, asgi-mount]

# Dependency graph
requires:
  - phase: 41-mcp-server
    plan: 01
    provides: MCP server module with create_mcp_app() factory and 6 tools
  - phase: 40-rest-api-v1
    provides: REST API v1 endpoints called by MCP tools via httpx loopback
provides:
  - MCP server mounted at /mcp/ on FastAPI app in api and dev modes
  - Combined lifespans via combine_lifespans (FastAPI + MCP)
  - Trailing slash middleware exclusion for /mcp paths
  - CORS headers for MCP protocol (mcp-protocol-version, mcp-session-id)
affects: [deployment, mcp-testing, uat]

# Tech tracking
tech-stack:
  added: []
  patterns: [combine_lifespans for multi-app lifespan coordination, conditional ASGI mount by mode]

key-files:
  created: []
  modified: [backend/app/main.py, backend/app/mcp_server.py]

key-decisions:
  - "Mode determination moved before FastAPI() creation to enable lifespan coordination"
  - "combine_lifespans(lifespan, _mcp_app.lifespan) merges FastAPI and MCP lifespans"
  - "MCP app created early (module level) and stored in _mcp_app for both lifespan merging and mounting"
  - "CORS expose_headers includes mcp-session-id for API mode"

patterns-established:
  - "Conditional ASGI mount pattern: create app early, combine lifespans, mount later in mode block"

requirements-completed: [MCP-05]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 41 Plan 02: Mount & Lifecycle Summary

**MCP server mounted at /mcp/ with combined lifespans via combine_lifespans, mode-gated to api/dev only, with trailing slash exclusion and MCP CORS headers**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T21:49:33Z
- **Completed:** 2026-02-24T21:51:26Z
- **Tasks:** 2
- **Files modified:** 2 (main.py, mcp_server.py)

## Accomplishments
- MCP server mounted at /mcp/ in api and dev modes with lifespan coordination
- Trailing slash middleware excludes /mcp paths to avoid breaking MCP Streamable HTTP transport
- CORS headers updated for MCP protocol (mcp-protocol-version request header, mcp-session-id response header)
- Claude Desktop configuration and security warnings documented in mcp_server.py
- Verified MCP is NOT mounted in public mode

## Task Commits

Each task was committed atomically:

1. **Task 1: Mount MCP server and coordinate lifespans** - `6dfdb81` (feat)
2. **Task 2: Verify MCP server starts and add documentation** - `82a485c` (docs)

## Files Created/Modified
- `backend/app/main.py` - Moved mode determination before app creation, combined lifespans, mounted MCP at /mcp/, excluded /mcp from trailing slash middleware, added MCP CORS headers
- `backend/app/mcp_server.py` - Added Claude Desktop configuration comment and security warnings (prompt injection, tool confirmation)

## Decisions Made
- **Mode determination timing:** Moved `mode = settings.spectra_mode` and validation before `app = FastAPI()` to enable lifespan combination. Previously mode was set after app creation (line 331). This is a structural change but does not alter behavior -- mode was already deterministic from settings.
- **Early MCP app creation:** `_mcp_app = create_mcp_app()` is called at module level (in mode block) so both its lifespan can be combined and the app can be mounted later. Stored in `_mcp_app` module variable.
- **CORS headers:** Added `mcp-protocol-version` to allow_headers and `mcp-session-id` to expose_headers only in API mode CORS config. Dev mode uses wildcard headers already.

## Deviations from Plan

None - plan executed exactly as written. The `mcp_api_base_url` setting was already added during Plan 01 (noted in 41-01-SUMMARY.md deviation #2).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. MCP server is automatically available at /mcp/ when running in api or dev mode.

## Next Phase Readiness
- Phase 41 (MCP Server Integration) is complete
- MCP server is accessible at http://host/mcp/ in api and dev modes
- Full E2E testing requires a running backend with database (UAT concern)
- Production deployment needs MCP_API_BASE_URL set to internal API service URL

## Self-Check: PASSED

- backend/app/main.py: FOUND
- backend/app/mcp_server.py: FOUND
- Commit 6dfdb81: FOUND (feat: mount MCP server)
- Commit 82a485c: FOUND (docs: Claude Desktop config)
- MCP mounted in dev mode: verified (routes contain /mcp)
- MCP NOT mounted in public mode: verified (no /mcp routes)

---
*Phase: 41-mcp-server*
*Completed: 2026-02-24*
