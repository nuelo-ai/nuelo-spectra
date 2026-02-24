---
phase: 41-mcp-server
plan: 01
subsystem: api
tags: [mcp, fastmcp, httpx, asgi, tool-server]

# Dependency graph
requires:
  - phase: 40-rest-api-v1
    provides: REST API v1 endpoints (files, query, context) called by MCP tools via httpx
  - phase: 38-api-keys
    provides: API key infrastructure (spe_ prefix, Bearer token auth) used by MCP auth middleware
provides:
  - FastMCP server module with 6 curated tools (spectra_ prefix)
  - ApiKeyAuthMiddleware for per-request Bearer token validation
  - create_mcp_app() factory returning mountable ASGI application
  - Typed TextContent blocks in spectra_run_analysis response
affects: [41-02-mount-lifecycle, deployment, mcp-testing]

# Tech tracking
tech-stack:
  added: [fastmcp>=3.0.2, mcp>=1.26.0 (transitive)]
  patterns: [MCP middleware auth, httpx loopback for tool-to-API calls, ToolResult with typed TextContent blocks]

key-files:
  created: [backend/app/mcp_server.py]
  modified: [backend/pyproject.toml, backend/uv.lock, backend/app/config.py]

key-decisions:
  - "stateless_http passed to http_app() not FastMCP constructor -- API changed in fastmcp 3.0.2"
  - "on_list_tools auth enforced via middleware (hook exists in fastmcp 3.0.2) per CONTEXT.md decision"
  - "mcp_api_base_url setting added to config.py with localhost:8000 default for httpx loopback"
  - "API response field names used correctly: generated_code (not code), chart_specs (not chart_spec)"

patterns-established:
  - "MCP tool pattern: async def with ctx: Context, httpx call, ToolError on failure"
  - "Auth middleware pattern: extract Bearer token, validate spe_ prefix, store in context state"
  - "Error extraction pattern: _extract_error_message() parses API error envelope with fallback"

requirements-completed: [MCP-01, MCP-02, MCP-03, MCP-04, MCP-05]

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 41 Plan 01: MCP Server Core Summary

**FastMCP 3.0.2 server module with 6 curated tools (spectra_ prefix), Bearer token auth middleware, and typed content blocks for analysis responses**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T21:43:19Z
- **Completed:** 2026-02-24T21:47:00Z
- **Tasks:** 2
- **Files modified:** 4 (mcp_server.py created, pyproject.toml, uv.lock, config.py modified)

## Accomplishments
- Installed fastmcp>=3.0.2 with mcp>=1.26.0 pulled in transitively
- Created 426-line mcp_server.py with 6 tools, auth middleware, and factory function
- Auth middleware validates Bearer token on both tool calls (on_call_tool) and tool listing (on_list_tools)
- spectra_run_analysis returns ToolResult with separate TextContent blocks for analysis, generated code, chart specs, and credits
- All tools use httpx loopback to REST API -- no direct service imports

## Task Commits

Each task was committed atomically:

1. **Task 1: Install fastmcp dependency** - `f16fae7` (chore)
2. **Task 2: Create MCP server module with auth middleware and 6 tools** - `d77a0d8` (feat)

## Files Created/Modified
- `backend/app/mcp_server.py` - FastMCP instance, ApiKeyAuthMiddleware, 6 tool definitions, create_mcp_app() factory
- `backend/pyproject.toml` - Added fastmcp>=3.0.2 dependency
- `backend/uv.lock` - Updated lockfile with fastmcp and 31 transitive dependencies
- `backend/app/config.py` - Added mcp_api_base_url setting for httpx loopback URL

## Decisions Made
- **stateless_http location:** FastMCP 3.0.2 moved `stateless_http` from constructor to `http_app()` / `run_http_async()`. Passed to `http_app(stateless_http=True)` in create_mcp_app().
- **on_list_tools auth:** FastMCP 3.0.2 supports `on_list_tools` middleware hook. Implemented auth check on tools/list per CONTEXT.md requirement for per-request validation on all MCP requests.
- **API response field mapping:** REST API returns `generated_code` and `chart_specs` (not `code` and `chart_spec` as research examples showed). Used correct field names.
- **mcp_api_base_url config:** Added configurable base URL setting to Settings class (defaults to http://localhost:8000) for production flexibility.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed stateless_http parameter location for FastMCP 3.0.2**
- **Found during:** Task 2 (MCP server module creation)
- **Issue:** FastMCP 3.0.2 no longer accepts `stateless_http` in the constructor; raises TypeError
- **Fix:** Moved `stateless_http=True` to `mcp.http_app(path="/", stateless_http=True)` in create_mcp_app()
- **Files modified:** backend/app/mcp_server.py
- **Verification:** Module imports and create_mcp_app() returns StarletteWithLifespan
- **Committed in:** d77a0d8 (Task 2 commit)

**2. [Rule 2 - Missing Critical] Added mcp_api_base_url to Settings**
- **Found during:** Task 2 (MCP server module creation)
- **Issue:** Settings class had no mcp_api_base_url field; _get_base_url() would fail with AttributeError
- **Fix:** Added `mcp_api_base_url: str = "http://localhost:8000"` to Settings class
- **Files modified:** backend/app/config.py
- **Verification:** get_settings().mcp_api_base_url returns default value
- **Committed in:** d77a0d8 (Task 2 commit)

**3. [Rule 1 - Bug] Corrected API response field names in spectra_run_analysis**
- **Found during:** Task 2 (tool implementation)
- **Issue:** Research examples used `data.code` and `data.chart_spec` but actual REST API returns `data.generated_code` and `data.chart_specs`
- **Fix:** Used correct field names from actual API router implementation
- **Files modified:** backend/app/mcp_server.py
- **Verification:** Field names match query.py return statement
- **Committed in:** d77a0d8 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations.

## User Setup Required
None - no external service configuration required. The mcp_api_base_url defaults to http://localhost:8000 and only needs changing in production deployments.

## Next Phase Readiness
- MCP server module is complete and ready for mounting in main.py (Plan 02)
- create_mcp_app() factory returns the ASGI app to mount at /mcp/
- Plan 02 will handle lifespan coordination via combine_lifespans and mode-gating

## Self-Check: PASSED

- backend/app/mcp_server.py: FOUND (426 lines)
- backend/pyproject.toml: FOUND (fastmcp>=3.0.2 present)
- backend/app/config.py: FOUND (mcp_api_base_url added)
- Commit f16fae7: FOUND (chore: install fastmcp)
- Commit d77a0d8: FOUND (feat: create MCP server module)
- Tool count: 6 (verified via mcp._list_tools())
- ASGI app type: StarletteWithLifespan (verified)

---
*Phase: 41-mcp-server*
*Completed: 2026-02-24*
