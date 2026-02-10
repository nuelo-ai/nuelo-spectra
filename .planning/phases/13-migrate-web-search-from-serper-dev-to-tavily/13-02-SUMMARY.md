---
phase: 13-migrate-web-search-from-serper-dev-to-tavily
plan: 02
subsystem: ui, api
tags: [follow-up-suggestions, memory-route, streaming, metadata, json-prompt]

# Dependency graph
requires:
  - phase: 13-01
    provides: "Tavily search integration, da_response_node with JSON parsing"
  - phase: 10
    provides: "Follow-up suggestions infrastructure (DataCard chips, stream events)"
  - phase: 9
    provides: "Manager Agent routing with MEMORY_SUFFICIENT route"
provides:
  - "Follow-up suggestion chips on MEMORY_SUFFICIENT route responses (streaming + persisted)"
  - "JSON-structured memory prompt matching data_analysis prompt pattern"
  - "Non-streaming metadata_json includes follow_up_suggestions"
affects: [data-analysis, chat-interface, memory-route]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Memory prompt uses same JSON output format as analysis prompt for consistent _parse_analysis_json() parsing"
    - "Follow-up chips rendered outside DataCard for plain text memory responses"

key-files:
  created: []
  modified:
    - "backend/app/agents/data_analysis.py"
    - "backend/app/services/agent_service.py"
    - "frontend/src/components/chat/ChatInterface.tsx"
    - "frontend/src/components/chat/ChatMessage.tsx"

key-decisions:
  - "Memory prompt uses f-string with escaped braces for JSON schema example"
  - "Streaming cursor tied to analysisEvent presence (isStreaming={!analysisEvent})"
  - "Follow-up chips for persisted messages rendered inside ChatMessage flex-col container after timestamp"

patterns-established:
  - "Memory prompt JSON output: matching data_analysis YAML pattern ensures _parse_analysis_json() consistency across all routes"

# Metrics
duration: 4min
completed: 2026-02-09
---

# Phase 13 Plan 02: Fix MEMORY_SUFFICIENT Follow-Up Suggestions Summary

**Fix 4 compounding defects preventing follow-up suggestion chips on MEMORY_SUFFICIENT route: JSON memory prompt, streaming extraction, persisted rendering, non-streaming metadata**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T01:42:24Z
- **Completed:** 2026-02-10T01:46:22Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Backend memory prompt now instructs JSON output with "analysis" and "follow_up_suggestions" keys, enabling `_parse_analysis_json()` to return real suggestions
- Frontend streaming branch extracts follow_up_suggestions from da_response event and renders chips below memory route messages
- Frontend persisted messages render follow-up chips for non-DataCard assistant messages with follow_up_suggestions in metadata_json
- Non-streaming `run_chat_query()` includes follow_up_suggestions in metadata_json, matching the streaming path

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix backend - memory prompt JSON output and non-streaming metadata** - `a5193ab` (fix)
2. **Task 2: Fix frontend - streaming and persisted follow-up chips for memory responses** - `21d5948` (fix)

## Files Created/Modified
- `backend/app/agents/data_analysis.py` - Rewrote `_build_memory_prompt()` to instruct JSON output with "analysis" and "follow_up_suggestions" keys
- `backend/app/services/agent_service.py` - Added `follow_up_suggestions` to non-streaming `run_chat_query()` metadata_json
- `frontend/src/components/chat/ChatInterface.tsx` - Memory route streaming branch extracts and renders follow-up suggestion chips from da_response event
- `frontend/src/components/chat/ChatMessage.tsx` - Renders follow-up chips for persisted non-DataCard assistant messages with follow_up_suggestions

## Decisions Made
- Memory prompt uses f-string with `{{` / `}}` for literal braces in JSON schema example (Python f-string escaping)
- Streaming cursor now tied to `analysisEvent` presence (`isStreaming={!analysisEvent}`) so cursor disappears when stream completes
- Follow-up chips for persisted messages placed inside the flex-col container after timestamp span, keeping them aligned with the message column

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Backend tests: 22 async tests fail due to missing pytest-asyncio dependency (pre-existing, not caused by this plan). All 73 synchronous tests pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 4 MEMORY_SUFFICIENT follow-up suggestion defects are fixed
- Phase 13 is fully complete (Plan 1: Tavily migration, Plan 2: follow-up suggestions fix)
- Ready for v0.2 milestone wrap-up

---
*Phase: 13-migrate-web-search-from-serper-dev-to-tavily*
*Completed: 2026-02-09*
