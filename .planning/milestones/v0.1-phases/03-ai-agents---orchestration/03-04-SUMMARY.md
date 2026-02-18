---
phase: 03-ai-agents---orchestration
plan: 04
subsystem: ai-agents
tags: [langgraph, llm, code-generation, validation, orchestration, postgres]

# Dependency graph
requires:
  - phase: 03-01
    provides: LangGraph foundation, multi-provider LLM factory, YAML configs
  - phase: 03-02
    provides: Onboarding Agent data context for Coding Agent
  - phase: 03-03
    provides: AST-based code validation for Code Checker node

provides:
  - Coding Agent: generates Python code from natural language queries
  - Data Analysis Agent: interprets execution results in natural language
  - Code Checker node: AST + LLM logical validation with conditional routing
  - LangGraph chat workflow: complete pipeline with retry loops and circuit breaker
  - Execute stub: restricted namespace code execution (Phase 5 replaces with sandbox)

affects: [03-05-agent-service-integration, 03-06-chat-api-endpoints, phase-5-sandbox-execution]

# Tech tracking
tech-stack:
  added:
    - psycopg-binary (PostgresSaver dependency)
  patterns:
    - LangGraph Command routing for conditional edges
    - Two-stage code validation (AST syntax + LLM logical)
    - Bounded retry loops with max_steps circuit breaker
    - Code block extraction from markdown-formatted LLM responses
    - Restricted namespace execution pattern (stub for Phase 5)

key-files:
  created:
    - backend/app/agents/coding.py
    - backend/app/agents/data_analysis.py
    - backend/app/agents/graph.py
  modified: []

key-decisions:
  - "Code Checker uses two-stage validation: AST first (fast syntax/security), then LLM (logical correctness)"
  - "Command routing pattern for conditional edges (cleaner than add_conditional_edges)"
  - "Execute stub uses restricted namespace with empty __builtins__ (Phase 5 adds OS-level isolation)"
  - "max_steps=3 default circuit breaker prevents infinite retry loops"
  - "Code extraction handles markdown formatting from LLM responses"
  - "psycopg-binary installed for PostgresSaver compatibility"

patterns-established:
  - "Agent node functions: async, accept state dict, return state update dict"
  - "Code Checker returns Command[Literal[...]] for routing"
  - "Retry feedback: validation_errors list passed back to Coding Agent"
  - "Halt node: user-friendly error messages on max retries"

# Metrics
duration: 3min
completed: 2026-02-03
---

# Phase 3 Plan 4: Coding Agent & Chat Workflow Summary

**Complete LangGraph chat pipeline with Coding/Data Analysis agents, two-stage code validation, conditional routing, and bounded retry loops**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-03T15:21:40Z
- **Completed:** 2026-02-03T15:25:11Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments

- Coding Agent generates Python code from natural language using data context from Onboarding Agent
- Data Analysis Agent interprets execution results and provides conversational explanations
- Code Checker node combines AST validation + LLM logical check with conditional routing
- LangGraph workflow connects all nodes with retry loops and circuit breaker (max_steps=3)
- Execute stub provides development-time code execution in restricted namespace
- PostgreSQL checkpointing for thread-scoped state isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Coding and Data Analysis agents** - `ad0c6fa` (feat)
2. **Task 2: LangGraph chat workflow** - `059a37b` (feat)

## Files Created/Modified

- `backend/app/agents/coding.py` - Coding Agent: generates Python code from queries, handles retry feedback
- `backend/app/agents/data_analysis.py` - Data Analysis Agent: interprets execution results
- `backend/app/agents/graph.py` - LangGraph workflow: code checker, execute stub, halt node, graph assembly

## Decisions Made

1. **Two-stage validation in Code Checker**: AST validation first (fast, catches syntax/security), then LLM logical check (slow, catches semantic issues). This sequence optimizes for speed while ensuring correctness.

2. **Command routing pattern**: Using LangGraph Command return type for conditional edges (goto="execute"|"coding_agent"|"halt"). Cleaner than add_conditional_edges callback pattern.

3. **Execute stub with restricted namespace**: Development stub uses exec() with empty __builtins__ and only pd/np available. NOT production-safe but unblocks development. Phase 5 replaces with E2B/gVisor sandbox.

4. **max_steps=3 circuit breaker**: Default limit prevents infinite retry loops and runaway LLM costs. Configurable via state["max_steps"].

5. **Code block extraction**: Coding Agent extracts code from markdown-formatted LLM responses (```python blocks). Handles LLMs that wrap code vs those that return raw code.

6. **psycopg-binary dependency**: Installed to fix PostgresSaver import error (missing libpq). LangGraph checkpoint requires psycopg3 with binary components.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed psycopg-binary package**
- **Found during:** Task 2 (graph.py import verification)
- **Issue:** PostgresSaver import failed with "no pq wrapper available". langgraph-checkpoint-postgres was installed but missing psycopg binary implementation.
- **Fix:** Installed psycopg-binary package using uv pip install
- **Files modified:** .venv dependencies
- **Verification:** Graph module imports succeeded after installation
- **Committed in:** 059a37b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix to unblock graph compilation. No scope changes.

## Issues Encountered

None beyond the auto-fixed psycopg-binary dependency.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 3 Plan 5 (Agent Service Integration):**
- All agent nodes implemented and importable
- Graph assembly function tested (import verification)
- State schema defined with all required fields
- Retry loop logic validated
- Circuit breaker mechanism in place

**Blockers:** None

**Next steps:**
- Create agent service functions (run_chat_query wrapper)
- Add graph invocation with thread_id management
- Integrate with Chat API endpoints
- Load file data for code execution context

---
*Phase: 03-ai-agents---orchestration*
*Completed: 2026-02-03*
