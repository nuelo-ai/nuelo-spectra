---
phase: 09-manager-agent-with-intelligent-query-routing
plan: 01
subsystem: agents
tags: [langgraph, pydantic, routing, structured-output, command-routing, yaml-config]

# Dependency graph
requires:
  - phase: 07-multi-llm-provider-infrastructure
    provides: "get_llm factory, per-agent YAML config helpers, provider registry"
  - phase: 08-session-memory-with-postgresql-checkpointing
    provides: "Conversation history via messages field with add_messages reducer"
provides:
  - "Manager Agent node (manager_node) as graph entry point"
  - "RoutingDecision Pydantic model with 3 route types"
  - "Command-based routing to data_analysis or coding_agent"
  - "Manager agent YAML config with system prompt and routing_context_messages"
  - "routing_decision and previous_code state fields"
  - "Routing decision in stream events and chat history metadata"
affects: [09-02, 09-03, data-analysis-agent, coding-agent, frontend-events]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Command-based routing (LangGraph Command with goto+update)"
    - "Structured LLM output via with_structured_output(Pydantic model)"
    - "Fallback routing on LLM failure (NEW_ANALYSIS default)"
    - "Routing decision logging with JSON structured metadata"

key-files:
  created:
    - "backend/app/agents/manager.py"
  modified:
    - "backend/app/agents/state.py"
    - "backend/app/agents/graph.py"
    - "backend/app/config/prompts.yaml"
    - "backend/app/services/agent_service.py"

key-decisions:
  - "RoutingDecision defined in state.py to avoid circular imports (manager.py imports from state.py)"
  - "Uses with_structured_output for reliable JSON parsing instead of raw json.loads"
  - "Manager routes via Command (same pattern as code_checker_node) - no explicit edges needed"
  - "Routing decision serialized to dict before yielding in stream events for JSON compatibility"
  - "routing_context_messages configurable in YAML (default: 10)"

patterns-established:
  - "Command-based routing: nodes return Command(goto=target, update=state_delta) for dynamic routing"
  - "Structured LLM output: llm.with_structured_output(PydanticModel) for reliable classification"
  - "Pydantic model serialization guard: hasattr(rd, 'model_dump') for safe dict conversion"

# Metrics
duration: 4min
completed: 2026-02-08
---

# Phase 9 Plan 1: Manager Agent Core Implementation Summary

**Manager Agent as graph entry point with Command-based routing to 3 paths (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS) using structured LLM output**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-08T00:29:23Z
- **Completed:** 2026-02-08T00:33:24Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Manager Agent node created as the new graph entry point, classifying queries using structured LLM output
- Three routing paths implemented via LangGraph Command: MEMORY_SUFFICIENT -> data_analysis, CODE_MODIFICATION/NEW_ANALYSIS -> coding_agent
- Routing decisions logged with reasoning and context for monitoring (ROUTING-08)
- Fallback to NEW_ANALYSIS on any routing failure ensures resilience (ROUTING-04)
- RoutingDecision Pydantic model with validation for all three route types
- Routing decision included in stream events and chat history metadata for frontend visibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Manager Agent with RoutingDecision schema and update state** - `2dcc2f1` (feat)
2. **Task 2: Wire Manager Agent into graph and update agent service** - `40ecded` (feat)

## Files Created/Modified
- `backend/app/agents/manager.py` - Manager Agent node with structured LLM routing and Command-based dispatch
- `backend/app/agents/state.py` - RoutingDecision Pydantic model, routing_decision and previous_code fields added to ChatAgentState
- `backend/app/agents/graph.py` - Manager node added as entry point, replaces direct coding_agent entry
- `backend/app/config/prompts.yaml` - Manager agent config with provider, model, temperature, system_prompt, routing_context_messages, max_tokens
- `backend/app/services/agent_service.py` - Initial state includes routing fields, stream events include routing_decision, chat history metadata includes routing_decision

## Decisions Made
- **RoutingDecision location:** Defined in `state.py` (not `manager.py`) to avoid circular imports since both manager.py and potentially other agents need the model
- **Structured output over raw JSON:** Used `llm.with_structured_output(RoutingDecision)` for reliable parsing instead of raw `json.loads` on LLM text output
- **Command routing pattern:** Manager uses the same `Command(goto=..., update=...)` pattern as the existing `code_checker_node`, maintaining consistency
- **Pydantic serialization guard:** Used `hasattr(rd, 'model_dump')` pattern for safe serialization since routing_decision can be either a Pydantic model or already-serialized dict depending on code path

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Manager Agent is wired as graph entry point and routes correctly
- Plans 09-02 (Data Analysis memory mode) and 09-03 (testing) can proceed
- The data_analysis agent currently does not have memory-only mode -- Plan 09-02 will add this capability
- The coding_agent does not yet use the `previous_code` state field for modification mode -- Plan 09-02 will address this

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 09-manager-agent-with-intelligent-query-routing*
*Completed: 2026-02-08*
