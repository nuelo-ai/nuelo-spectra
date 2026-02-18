---
phase: 11-web-search-tool-integration
plan: 03
subsystem: frontend
tags: [react, search-ui, search-toggle, sse-events, sources-display, useSearchToggle, ChatInput, DataCard]

# Dependency graph
requires:
  - phase: 11-web-search-tool-integration
    plan: 01
    provides: GET /search/config endpoint, SearchConfig types
  - phase: 11-web-search-tool-integration
    plan: 02
    provides: SSE search events, search_sources in metadata, tool-calling loop
provides:
  - "useSearchToggle hook with config fetch and quota checking"
  - "Search toggle UI below ChatInput with Globe icon"
  - "Real-time search activity indicator showing actual query text"
  - "DataCard Sources section with clickable page title links"
  - "Full search integration in ChatInterface with SSE event handling"
affects: [future-ui-enhancements]

# Tech tracking
tech-stack:
  added: []
  patterns: [custom toggle button (shadcn Switch not installed), search activity with pulsing animation, sources section in DataCard, toggle reset after query]

key-files:
  created:
    - frontend/src/hooks/useSearchToggle.ts
  modified:
    - frontend/src/components/chat/ChatInput.tsx
    - frontend/src/components/chat/DataCard.tsx
    - frontend/src/components/chat/ChatInterface.tsx
    - frontend/src/hooks/useSSEStream.ts
    - frontend/src/types/chat.ts
    - backend/app/agents/data_analysis.py
    - backend/app/services/agent_service.py
    - backend/app/routers/search.py

key-decisions:
  - "Used custom toggle button instead of shadcn Switch (not installed in project)"
  - "Search activity indicator shows actual query text with pulsing animation"
  - "Sources section displays page titles as clickable links (no snippets per CONTEXT.md)"
  - "Toggle resets to OFF after each query to prevent accidental quota consumption"
  - "da_response_node makes fresh LLM call when search was used (bind_tools mode unreliable for JSON)"

patterns-established:
  - "Search toggle pattern: config check on mount, quota validation before enable, reset after send"
  - "SSE search event handling: search_started -> activity indicator, search_completed -> clear, sources from node_complete"
  - "DataCard conditional sections: sources only show when search was used and streaming complete"
  - "Fresh LLM call pattern: When bind_tools mode is used, final response requires separate LLM call for reliable JSON output"

# Metrics
duration: 10min
completed: 2026-02-09
---

# Phase 11 Plan 03: Frontend Search UI Summary

**Search toggle below chat input with config checking, real-time search activity indicators, DataCard sources section with clickable links, and human-verified end-to-end integration**

## Performance

- **Duration:** 10 min (2 auto tasks + UAT checkpoint + 3 bug fix rounds)
- **Started:** 2026-02-09T13:27:00Z
- **Completed:** 2026-02-09T21:07:00Z
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 10

## Accomplishments
- useSearchToggle hook with GET /search/config integration, quota checking, and reset functionality
- Search toggle UI below ChatInput with Globe icon, disabled states, and quota exceeded warning
- Real-time search activity indicator showing actual query text during search operations
- DataCard Sources section with clickable page title links (no snippets per CONTEXT.md)
- Full ChatInterface integration: toggle state, web_search_enabled in POST body, SSE event handling
- Search sources extracted from both live stream events and historical metadata_json
- Toggle auto-resets to OFF after each query to prevent accidental quota consumption
- Human verification passed: all 5 test scenarios (toggle visibility, end-to-end search, toggle persistence, memory mode, graceful degradation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Search toggle hook, ChatInput toggle, type definitions, and SSE events** - `b6e8dae` (feat)
2. **Task 2: DataCard sources section, ChatInterface integration, and search activity** - `71bbe18` (feat)
3. **Task 3: Human verification checkpoint** - UAT passed with 3 bug fix rounds:
   - `7ce0fda` (fix) - Fixed search toggle reset, source leaking between queries, and missing follow-up suggestions
   - `5d41144` (fix) - Prepended system prompt in tool-calling loop for reliable JSON output
   - `e55ec00` (fix) - Fresh LLM call in da_response when search was used (bind_tools mode unreliable)

## Files Created/Modified
- `frontend/src/hooks/useSearchToggle.ts` - Search toggle state management hook with config fetch, quota checking, reset
- `frontend/src/types/chat.ts` - Added SearchSource, SearchConfig interfaces, search event types (search_started, search_completed, search_failed, search_quota_exceeded)
- `frontend/src/components/chat/ChatInput.tsx` - Search toggle below input with custom button (shadcn Switch not installed), Globe icon, disabled states, tooltip messages
- `frontend/src/components/chat/DataCard.tsx` - Sources section with clickable links, border-t separator, text-xs compact styling
- `frontend/src/components/chat/ChatInterface.tsx` - Full search integration: useSearchToggle, toggle props to ChatInput, web_search_enabled in POST body, SSE event handling, search activity indicator, sources extraction from stream and metadata
- `frontend/src/hooks/useSSEStream.ts` - Search event handling: search_started, search_completed, search_failed, search_quota_exceeded
- `backend/app/agents/data_analysis.py` - Fresh LLM call in da_response_node when search was used, _parse_analysis_json helper for reliable JSON parsing
- `backend/app/services/agent_service.py` - Reset search_sources to empty list in initial_state
- `backend/app/routers/search.py` - Fixed double prefix bug (/search/search/config -> /search/config)

## Decisions Made
- Used custom toggle button instead of shadcn Switch component (not installed in project, avoided adding new dependency)
- Search activity indicator shows the actual query text with pulsing animation (more informative than generic "Searching..." message)
- Sources section displays page titles as clickable links without snippets (per CONTEXT.md design decision)
- Toggle resets to OFF after each query send to prevent accidental quota consumption
- da_response_node makes fresh LLM call when search was used because bind_tools mode produces unreliable JSON output (system prompt lost in tool-calling loop)
- _parse_analysis_json helper with markdown fence stripping for robust JSON extraction

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed search router double prefix bug**
- **Found during:** Task 1 implementation
- **Issue:** Search router was mounted at `/search/search/config` instead of `/search/config` due to double prefix in backend routing
- **Fix:** Corrected router mounting in backend/app/routers/search.py
- **Files modified:** backend/app/routers/search.py
- **Commit:** 7ce0fda (included in UAT fixes)

**2. [Rule 1 - Bug] Fixed search toggle not resetting after query**
- **Found during:** Task 3 UAT - Test 3 (toggle reset behavior)
- **Issue:** Toggle remained ON after query sent, causing next query to unexpectedly use search
- **Fix:** Added resetToggle() call after successful message send in ChatInterface
- **Files modified:** frontend/src/components/chat/ChatInterface.tsx
- **Commit:** 7ce0fda

**3. [Rule 1 - Bug] Fixed source leaking between queries**
- **Found during:** Task 3 UAT - Test 3 (non-search queries showing old sources)
- **Issue:** search_sources persisted in state across queries, showing stale sources on non-search responses
- **Fix:** Reset search_sources to empty list in agent_service initial_state
- **Files modified:** backend/app/services/agent_service.py
- **Commit:** 7ce0fda

**4. [Rule 1 - Bug] Fixed missing follow-up suggestions**
- **Found during:** Task 3 UAT - DataCard not showing follow-ups after fixes
- **Issue:** follow_up_suggestions was None instead of empty list, breaking conditional rendering
- **Fix:** Ensured follow_up_suggestions defaults to empty list in all response paths
- **Files modified:** backend/app/agents/data_analysis.py
- **Commit:** 7ce0fda

**5. [Rule 1 - Bug] Fixed unreliable JSON output in tool-calling loop**
- **Found during:** Task 3 UAT - da_response sometimes returning raw text instead of JSON
- **Issue:** System prompt lost after bind_tools/ToolNode loop, LLM not consistently returning JSON
- **Fix:** Prepended system prompt message before final response generation
- **Files modified:** backend/app/agents/data_analysis.py
- **Commit:** 5d41144

**6. [Rule 1 - Bug] Fixed analysis quality degradation when search used**
- **Found during:** Task 3 UAT - responses lacked data-backed insights when search was used
- **Issue:** bind_tools mode system prompt insufficient for full analysis structure
- **Fix:** da_response_node makes fresh LLM call with full system prompt when search was used
- **Files modified:** backend/app/agents/data_analysis.py
- **Commit:** e55ec00

## Issues Encountered

**Three rounds of UAT bug fixes were required:**

1. **First round (7ce0fda):** Toggle persistence, source leaking, follow-up suggestions reliability
2. **Second round (5d41144):** JSON output reliability in tool-calling loop
3. **Third round (e55ec00):** Analysis quality when search was used

**Root cause:** The bind_tools/ToolNode pattern introduced in Plan 02 created system prompt context loss after tool execution. Initial implementation assumed the same LLM state would persist through the tool-calling loop, but in practice the system prompt needed to be:
- Re-prepended before final response (fix #5)
- OR completely bypassed with a fresh LLM call (fix #6, final solution)

**Resolution:** da_response_node now makes a fresh LLM call with full system prompt when search was used, ensuring consistent JSON output and high-quality analysis.

## User Setup Required

**SERPER_API_KEY must be configured for search to work:**
- Set `SERPER_API_KEY` environment variable in backend `.env` file
- Get key from https://serper.dev (Dashboard -> API Key)
- Without this key, search toggle will be grayed out with "(not configured)" tooltip
- Free tier: 2,500 searches/month, sufficient for testing and light usage

## Next Phase Readiness
- Phase 11 (Web Search Tool Integration) is now COMPLETE - all 3 plans done
- Search feature fully functional: backend infrastructure, agent integration, frontend UI
- Daily quota tracking per user operational (default: 7 searches/day)
- Ready to proceed to Phase 12 (Production Email Infrastructure)
- Web search establishes the tool-calling pattern for future tool integrations

## Self-Check: PASSED

All created files verified on disk:
- FOUND: frontend/src/hooks/useSearchToggle.ts

All 5 task commits verified in git log:
- FOUND: b6e8dae (feat: Task 1)
- FOUND: 71bbe18 (feat: Task 2)
- FOUND: 7ce0fda (fix: UAT round 1)
- FOUND: 5d41144 (fix: UAT round 2)
- FOUND: e55ec00 (fix: UAT round 3)

All key files modified confirmed:
- frontend/src/components/chat/ChatInput.tsx
- frontend/src/components/chat/DataCard.tsx
- frontend/src/components/chat/ChatInterface.tsx
- frontend/src/hooks/useSSEStream.ts
- frontend/src/types/chat.ts
- backend/app/agents/data_analysis.py
- backend/app/services/agent_service.py
- backend/app/routers/search.py

Frontend builds successfully. All 5 UAT test scenarios passed.

---
*Phase: 11-web-search-tool-integration*
*Completed: 2026-02-09*
