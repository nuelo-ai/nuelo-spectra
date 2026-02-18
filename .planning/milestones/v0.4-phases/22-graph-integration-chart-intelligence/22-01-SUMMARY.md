---
phase: 22-graph-integration-chart-intelligence
plan: 01
subsystem: backend-agents
tags: [chart-intelligence, ai-decisions, visualization-flags]
dependencies:
  requires:
    - phase: 21
      plan: 01
      artifact: "Visualization Agent module"
  provides:
    - "chart_hint routing flag in Manager Agent"
    - "visualization_requested evaluation in DA Agent"
  affects:
    - path: "backend/app/agents/state.py"
      change: "Added chart_hint field to RoutingDecision"
    - path: "backend/app/agents/manager.py"
      change: "Propagates chart_hint to state via Command updates"
    - path: "backend/app/agents/data_analysis.py"
      change: "LLM-based visualization need evaluation"
tech_stack:
  added: []
  patterns:
    - "Two-phase visualization flags (chart_hint -> visualization_requested)"
    - "LLM-based decision making (no hardcoded triggers)"
    - "Advisory hints pattern (chart_hint is non-binding)"
key_files:
  created:
    - path: "backend/tests/test_chart_intelligence.py"
      purpose: "Unit tests for chart intelligence logic"
      lines: 215
  modified:
    - path: "backend/app/agents/state.py"
      purpose: "Added chart_hint field to RoutingDecision model"
      key_changes: ["chart_hint: str = Field(default='', description='...')"]
    - path: "backend/app/agents/manager.py"
      purpose: "Propagate chart_hint to state in all three routes"
      key_changes: ["update={'routing_decision': decision, 'chart_hint': decision.chart_hint}"]
    - path: "backend/app/agents/data_analysis.py"
      purpose: "Evaluate visualization need and set visualization_requested"
      key_changes: ["_evaluate_visualization_need() helper", "visualization_requested in return dict"]
    - path: "backend/app/config/prompts.yaml"
      purpose: "Updated Manager prompt with visualization hint rules"
      key_changes: ["Visualization Hint section with chart type suggestions"]
decisions:
  - choice: "LLM-based evaluation only (no hardcoded keyword triggers)"
    rationale: "Per user CONTEXT.md: 'No hardcoded triggers, AI judgment only'"
    impact: "More flexible but requires LLM call on every query"
  - choice: "chart_hint is advisory, not binding"
    rationale: "Visualization Agent has final say based on actual data shape"
    impact: "Manager can suggest but DA/Viz agents can override"
  - choice: "MEMORY_SUFFICIENT always skips visualization"
    rationale: "No code execution means no data to chart"
    impact: "Fast-path optimization, no unnecessary LLM calls"
  - choice: "Strong preference for showing charts when data supports it"
    rationale: "Per user guidance: 'Balanced discretion with strong preference for showing charts'"
    impact: "LLM prompt biases toward YES when 3+ comparable data points exist"
metrics:
  duration_minutes: 3
  tasks_completed: 2
  files_created: 1
  files_modified: 4
  tests_added: 9
  tests_total: 134
  completed_date: "2026-02-13"
---

# Phase 22 Plan 01: Chart Intelligence Summary

**One-liner:** LLM-based chart intelligence with two-phase flags (Manager sets advisory chart_hint, DA evaluates visualization_requested) using pure AI judgment without hardcoded triggers

## Objective Achievement

Added chart intelligence to Manager Agent and Data Analysis Agent so the pipeline can decide when visualization adds value. Implemented two-phase flag setting: Manager predicts (chart_hint), DA confirms (visualization_requested) using LLM judgment only.

## Tasks Completed

### Task 1: Add chart_hint generation to Manager Agent and visualization_requested evaluation to DA response

**Status:** ✅ Complete
**Commit:** 48165df
**Files:** backend/app/agents/state.py, backend/app/agents/manager.py, backend/app/agents/data_analysis.py, backend/app/config/prompts.yaml

**What was done:**

1. Updated RoutingDecision model to include optional chart_hint field (bar, line, scatter, pie, histogram, box, or empty string)
2. Modified Manager Agent to propagate chart_hint to state via Command updates for all three routes (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS)
3. Updated Manager system prompt in prompts.yaml with visualization hint rules:
   - Suggests chart type based on query intent (trend, comparison, distribution, relationship, breakdown)
   - Advisory only, strong preference for charts when data supports it
   - Empty string for queries like "what is the average?" or "explain the data"
4. Added _evaluate_visualization_need() helper in Data Analysis Agent:
   - LLM-based evaluation using lightweight call (max_tokens: 50)
   - Examines execution_result, user_query, chart_hint, and analysis text
   - Returns False for MEMORY_SUFFICIENT route (no data to chart)
   - Returns False for empty/error results
   - Uses LLM to evaluate if chart would enhance response (YES/NO only)
   - Non-fatal fallback: logs warning and returns False on LLM failure
5. Updated da_response_node to call _evaluate_visualization_need and include visualization_requested in return dict

**Verification:**
- All imports successful
- chart_hint field works in RoutingDecision model
- All 125 existing tests pass (no regressions)

### Task 2: Add unit tests for chart intelligence decisions

**Status:** ✅ Complete
**Commit:** 778c809
**Files:** backend/tests/test_chart_intelligence.py

**What was done:**

Created comprehensive test suite with 9 tests covering:

1. **RoutingDecision chart_hint tests (3 tests):**
   - test_routing_decision_chart_hint_default: Defaults to empty string
   - test_routing_decision_chart_hint_bar: Preserves 'bar' value
   - test_routing_decision_chart_hint_empty: Empty string is valid

2. **_evaluate_visualization_need tests (6 tests):**
   - test_viz_need_memory_sufficient_returns_false: MEMORY_SUFFICIENT skips viz (no LLM call)
   - test_viz_need_no_execution_result_returns_false: Empty result returns False
   - test_viz_need_error_result_returns_false: Error result returns False
   - test_viz_need_llm_yes_returns_true: Mock LLM YES produces True
   - test_viz_need_llm_no_returns_false: Mock LLM NO produces False
   - test_viz_need_llm_failure_returns_false: LLM exception falls back to False (non-fatal)

**Verification:**
- All 9 new tests pass
- Full test suite passes (134 tests total: 9 new + 125 existing)
- All tests use mocking for LLM calls (no real API calls, fast execution)

## Deviations from Plan

None - plan executed exactly as written. All tasks completed, all verification checks passed, no issues encountered.

## Key Implementation Details

**Two-phase visualization flag pattern:**
1. **Phase 1 - Manager Agent (chart_hint):** Analyzes query intent and suggests chart type if visualization seems likely. Advisory only, propagated through state.
2. **Phase 2 - Data Analysis Agent (visualization_requested):** Evaluates execution results and analysis to confirm if chart would add value. Uses lightweight LLM call for judgment.

**LLM-based evaluation rules:**
- YES if: data has multiple values, shows trends/distributions/proportions, or chart_hint is provided
- NO if: result is single number, text explanation, error, or fewer than 2 data points
- When in doubt with 3+ comparable values: say YES (strong chart preference)

**Fast-path optimizations:**
- MEMORY_SUFFICIENT route skips visualization evaluation (no code execution = no data to chart)
- Error results and empty execution_result skip evaluation
- LLM failures are non-fatal (log warning, return False, continue)

**No hardcoded triggers:**
Per user decision: "No hardcoded triggers or keyword matching -- pure LLM judgment." All decisions go through LLM evaluation. No "if query contains 'trend'" logic.

## Success Criteria Met

- [x] Manager Agent adds chart_hint to state during routing via RoutingDecision structured output
- [x] Data Analysis Agent evaluates visualization need and sets visualization_requested boolean in da_response_node
- [x] Manager prompt updated with chart type suggestion instructions
- [x] MEMORY_SUFFICIENT queries always skip visualization (no chart for history-only answers)
- [x] LLM evaluation failures are non-fatal (default to False, log warning)
- [x] 9+ unit tests pass covering all decision paths
- [x] All existing tests pass without modification (134 total tests pass)

## Integration Points

**Upstream dependencies:**
- Phase 20: Pipeline infrastructure with visualization fields in ChatAgentState
- Phase 21: Visualization Agent module ready to consume visualization_requested flag

**Downstream impacts:**
- Phase 22-02: Pipeline will read visualization_requested to conditionally invoke Visualization Agent
- Frontend: Will eventually display charts when chart_specs field is populated (Phase 23)

## Testing Coverage

**Unit tests (9 new tests):**
- RoutingDecision model: chart_hint defaults, value preservation, empty string
- _evaluate_visualization_need: MEMORY_SUFFICIENT, empty results, errors, LLM YES/NO, LLM failure

**Integration tests:**
- All existing tests pass (125 tests covering manager routing, DA response, code generation)

**Test execution time:** 0.15s for chart intelligence tests, 1.83s for full suite

## Performance Impact

**Manager Agent:** Negligible (chart_hint populated as part of existing structured LLM call, no extra API request)

**Data Analysis Agent:** +1 lightweight LLM call per query (max_tokens: 50, temperature: 0.0)
- Estimated latency: ~200-500ms depending on provider
- Skipped for MEMORY_SUFFICIENT (fast path), empty results, and errors
- Acceptable overhead for improved UX (only show charts when they add value)

## Self-Check: PASSED

**Created files exist:**
```bash
FOUND: backend/tests/test_chart_intelligence.py
```

**Modified files exist:**
```bash
FOUND: backend/app/agents/state.py
FOUND: backend/app/agents/manager.py
FOUND: backend/app/agents/data_analysis.py
FOUND: backend/app/config/prompts.yaml
```

**Commits exist:**
```bash
FOUND: 48165df (feat: add chart intelligence to Manager and DA agents)
FOUND: 778c809 (test: add unit tests for chart intelligence)
```

**Verification commands:**
```bash
# chart_hint field works
✅ RoutingDecision(chart_hint='line').chart_hint == 'line'

# All chart intelligence tests pass
✅ 9 passed in 0.15s

# chart_hint in manager.py Command updates (3 occurrences)
✅ Lines 182, 189, 199

# visualization_requested in da_response_node return
✅ Line 240
```

## Next Steps

Ready for Phase 22 Plan 02: Integrate Visualization Agent into main pipeline with conditional invocation based on visualization_requested flag.
