---
phase: 13-migrate-web-search-from-serper-dev-to-tavily
plan: 01
subsystem: api
tags: [tavily, web-search, search-api, langchain-tools, async]

# Dependency graph
requires:
  - phase: 11-web-search-tool-integration
    provides: SearchService, search_web tool, SearchQuota, /search/config endpoint, agent tool-calling loop
provides:
  - Tavily-backed SearchService with AsyncTavilyClient and synthesized answer field
  - search_web tool returning Tavily answer + source URLs for richer agent context
  - tavily_api_key and search_depth settings replacing serper_api_key
  - credits_used cost tracking in search success log (SEARCH-07)
affects: []

# Tech tracking
tech-stack:
  added: [tavily-python]
  patterns: [SDK-based search client with AsyncTavilyClient]

key-files:
  created: []
  modified:
    - backend/app/services/search.py
    - backend/app/agents/tools/web_search.py
    - backend/app/config.py
    - backend/app/routers/search.py
    - backend/app/services/agent_service.py
    - backend/.env.example
    - backend/pyproject.toml

key-decisions:
  - "Use tavily-python SDK (AsyncTavilyClient) instead of raw httpx -- handles auth, errors, connection pooling"
  - "search_num_results default changed from 5 to 3 for focused results (user decision)"
  - "SearchResult.link renamed to SearchResult.url, SearchResult.position removed"
  - "SearchResponse gains answer field for Tavily synthesized answer"
  - "credits_used logged as 1 (basic) or 2 (advanced) for cost tracking"

patterns-established:
  - "SDK client pattern: AsyncTavilyClient instantiated in SearchService.__init__ for connection pooling"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 13 Plan 01: Migrate Web Search from Serper.dev to Tavily Summary

**Tavily API migration with AsyncTavilyClient, synthesized answer injection into agent LLM context, and complete Serper.dev removal**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T22:46:50Z
- **Completed:** 2026-02-09T22:49:45Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- SearchService fully rewritten with Tavily AsyncTavilyClient (include_answer=True, max_results=3, configurable search_depth)
- search_web tool returns Tavily synthesized answer followed by source URLs, flowing through existing search_results_text into agent LLM context
- All Serper.dev references removed from entire backend codebase (zero grep matches)
- Source URL format "- Title: URL" preserved for _extract_sources_from_tool_response regex compatibility
- All 100 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite SearchService for Tavily and update config/dependencies** - `42872c8` (feat)
2. **Task 2: Update tool output format, router key check, and remove all Serper references** - `5ae3726` (feat)

**Plan metadata:** (pending) (docs: complete plan)

## Files Created/Modified
- `backend/app/services/search.py` - Tavily-backed SearchService with AsyncTavilyClient, SearchResult(title, url), SearchResponse with answer field
- `backend/app/agents/tools/web_search.py` - search_web tool returning Tavily answer + source URLs
- `backend/app/config.py` - tavily_api_key, search_depth settings (replaces serper_api_key)
- `backend/app/routers/search.py` - /search/config checks tavily_api_key
- `backend/app/services/agent_service.py` - Cleaned Serper references from comments
- `backend/.env.example` - TAVILY_API_KEY and SEARCH_DEPTH replacing SERPER_API_KEY
- `backend/pyproject.toml` - Added tavily-python>=0.7.0 dependency

## Decisions Made
- Used tavily-python SDK (AsyncTavilyClient) for HTTP layer -- handles Bearer auth, error mapping, connection pooling internally via httpx
- Changed search_num_results default from 5 to 3 (user locked decision: focused results)
- Renamed SearchResult.link to SearchResult.url and removed position field (Tavily response uses url key)
- Added credits_used field to search success log (1 for basic depth, 2 for advanced) satisfying SEARCH-07 cost tracking requirement
- Single except Exception block replaces separate timeout/HTTP/generic handlers (SDK handles HTTP errors internally)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated .env to replace SERPER_API_KEY with TAVILY_API_KEY**
- **Found during:** Task 1 (verification step)
- **Issue:** Pydantic Settings validation failed with "Extra inputs are not permitted" for serper_api_key because the .env file still contained SERPER_API_KEY after removing the field from config.py
- **Fix:** Replaced SERPER_API_KEY line in .env with TAVILY_API_KEY= (empty, for user to configure)
- **Files modified:** backend/.env (not committed, gitignored)
- **Verification:** Config loads successfully, prints tavily_key=False, depth=basic, num=3
- **Committed in:** Not committed (.env is gitignored)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for Settings to load. The .env file is gitignored so this is a local-only change. .env.example was already updated as planned.

## Issues Encountered
None - plan executed cleanly after the .env deviation fix.

## User Setup Required

Users must update their `.env` file:
- Replace `SERPER_API_KEY=...` with `TAVILY_API_KEY=your-tavily-api-key`
- Add `SEARCH_DEPTH=basic` (or `advanced` for 2x credit cost)
- Get a Tavily API key from https://tavily.com (free tier: 1000 credits/month)

## Next Phase Readiness
- Tavily migration complete -- web search fully operational with richer agent context
- Phase 13 has only 1 plan, so this completes the phase
- Ready for v0.2 milestone completion (Phase 12 Production Email is the remaining phase)

## Self-Check: PASSED

All 8 files verified on disk. Both task commits (42872c8, 5ae3726) verified in git log. 100 tests pass.

---
*Phase: 13-migrate-web-search-from-serper-dev-to-tavily*
*Completed: 2026-02-09*
