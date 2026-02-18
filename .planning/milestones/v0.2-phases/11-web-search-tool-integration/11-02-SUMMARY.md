---
phase: 11-web-search-tool-integration
plan: 02
subsystem: api
tags: [langgraph, bind-tools, toolnode, tools-condition, web-search, tool-calling-loop, sse-streaming]

# Dependency graph
requires:
  - phase: 11-web-search-tool-integration
    plan: 01
    provides: SearchService, SearchQuota, ChatAgentState extensions, StreamEventType search events
  - phase: 09-manager-agent-with-intelligent-query-routing
    provides: Manager Agent Command-based routing, RoutingDecision model
provides:
  - "@tool search_web definition with SSE streaming via get_stream_writer"
  - "Tool-calling loop: da_with_tools <-> search_tools (via tools_condition) -> da_response"
  - "web_search_enabled flows from ChatQueryRequest -> router -> agent_service -> initial_state -> da_with_tools_node"
  - "Search quota tracking per user query in database"
  - "Search sources included in SSE node_complete events and chat metadata_json"
affects: [11-03-frontend, future-tool-infrastructure]

# Tech tracking
tech-stack:
  added: []
  patterns: [bind_tools/ToolNode tool-calling loop, @tool with get_stream_writer for SSE, conditional tool binding based on state, source extraction from ToolMessages]

key-files:
  created:
    - backend/app/agents/tools/__init__.py
    - backend/app/agents/tools/web_search.py
  modified:
    - backend/app/agents/data_analysis.py
    - backend/app/agents/graph.py
    - backend/app/agents/manager.py
    - backend/app/services/agent_service.py
    - backend/app/routers/chat.py
    - backend/tests/test_routing.py

key-decisions:
  - "Split data_analysis_agent into da_with_tools_node + da_response_node for tool-calling loop"
  - "Search instructions appended dynamically in code (not baked into YAML) for conditional behavior"
  - "Quota tracked per user query (not per Serper API call) per CONTEXT.md decision"
  - "ToolMessage source extraction uses regex pattern matching on tool response format"
  - "bind_tools wrapped in try/except for graceful fallback on unsupported providers"

patterns-established:
  - "Tool-calling loop pattern: LLM node -> ToolNode -> LLM node (via tools_condition)"
  - "@tool with get_stream_writer(): Emit SSE events from inside tool execution"
  - "Conditional tool binding: bind_tools only when feature flag (web_search_enabled) is True"
  - "Source extraction pattern: Parse ToolMessage content for structured data in da_response"

# Metrics
duration: 7min
completed: 2026-02-09
---

# Phase 11 Plan 02: Agent Integration with bind_tools/ToolNode Summary

**Tool-calling loop with da_with_tools/search_tools/da_response nodes, @tool search_web with SSE streaming, manager routing to da_with_tools, end-to-end web_search_enabled wiring with quota tracking**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-09T13:18:18Z
- **Completed:** 2026-02-09T13:25:04Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Established the first tool-calling pattern in the project using LangGraph's bind_tools/ToolNode infrastructure
- Split monolithic data_analysis_agent into three-node pipeline: da_with_tools (LLM decision), search_tools (ToolNode execution), da_response (final formatting)
- Tool-calling loop via tools_condition allows the LLM to autonomously decide number of searches (0 to max_searches)
- web_search_enabled flows end-to-end from frontend request through chat router, agent_service, to agent state
- Search quota tracked per user query (not per API call) with graceful failure handling
- All 100 existing tests pass with zero regressions (routing tests updated for node name changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: @tool definition, graph topology, and data analysis node split** - `55c6bb7` (feat)
2. **Task 2: Service layer wiring, chat router, and quota tracking** - `5d1deed` (feat)

## Files Created/Modified
- `backend/app/agents/tools/__init__.py` - Tool registry exporting search_web
- `backend/app/agents/tools/web_search.py` - @tool search_web with SSE streaming via get_stream_writer, uses SearchService
- `backend/app/agents/data_analysis.py` - Rewritten: da_with_tools_node (LLM with conditional bind_tools), da_response_node (source extraction, JSON parsing), memory/analysis prompt builders
- `backend/app/agents/graph.py` - New topology: da_with_tools, search_tools (ToolNode), da_response with tool-calling loop via tools_condition
- `backend/app/agents/manager.py` - MEMORY_SUFFICIENT routes to da_with_tools (was data_analysis), updated type annotation and docstring
- `backend/app/services/agent_service.py` - web_search_enabled parameter, search_sources in metadata, _track_search_quota helper
- `backend/app/routers/chat.py` - Passes body.web_search_enabled to both sync and stream service functions
- `backend/tests/test_routing.py` - Updated for da_with_tools node name, added da_response_node test, updated graph topology assertions

## Decisions Made
- Split `data_analysis_agent` into `da_with_tools_node` + `da_response_node` to enable the tool-calling loop while preserving all existing behavior (memory mode, standard analysis, JSON parsing)
- Search-aware system prompt instructions are appended dynamically in `_build_analysis_prompt()` rather than baked into prompts.yaml -- this allows conditional behavior based on `web_search_enabled` state
- Quota is tracked per user query (not per Serper API call) per CONTEXT.md decision -- one query with 3 search calls counts as 1 of 7 daily quota
- `bind_tools` is wrapped in try/except to gracefully fall back when the configured LLM provider doesn't support tool calling
- `handle_tool_errors=True` on ToolNode ensures Serper API failures become ToolMessages that the LLM handles gracefully, not graph crashes
- Source extraction from ToolMessages uses regex pattern matching on the `"- {title}: {url}"` format produced by the search_web tool

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Tool-calling infrastructure is complete and ready for Plan 03 (frontend toggle and sources display)
- Search events (search_started, search_completed, search_failed) are emitted via SSE for frontend to consume
- search_sources included in node_complete events and chat metadata for frontend rendering
- All 100 tests pass -- routing, LLM provider, code checker suites all green

## Self-Check: PASSED

All created files verified on disk. Both task commits (55c6bb7, 5d1deed) verified in git log. 100/100 existing tests pass.

---
*Phase: 11-web-search-tool-integration*
*Completed: 2026-02-09*
