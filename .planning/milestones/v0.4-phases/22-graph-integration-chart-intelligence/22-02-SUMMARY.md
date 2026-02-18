---
phase: 22-graph-integration-chart-intelligence
plan: 02
subsystem: backend/graph-visualization-pipeline
tags: [langgraph, visualization, e2b-sandbox, sse-streaming, error-handling, conditional-routing]
dependency_graph:
  requires:
    - 22-01 (Chart Intelligence in Manager and DA agents)
    - 21-01 (Visualization Agent implementation)
    - 20-02 (E2B Sandbox Runtime)
  provides:
    - End-to-end chart generation pipeline
    - Conditional routing based on visualization_requested flag
    - Chart execution with retry logic (max 1 retry, 2 total attempts)
    - SSE events for chart progress (chart_completed, chart_failed)
    - Chart metadata persistence in message history
  affects:
    - backend/app/agents/graph.py (3 new nodes + conditional routing)
    - backend/app/services/agent_service.py (metadata persistence)
    - Frontend (when integrated) will receive chart_specs via SSE
tech_stack:
  added:
    - Conditional edge routing in LangGraph (should_visualize function)
    - Chart code retry mechanism with error context feedback
  patterns:
    - Non-fatal chart failures (analysis and data table always preserved)
    - Graceful degradation (subtle notification on chart failure)
    - Identical behavior when visualization is skipped (backward compatible)
key_files:
  created:
    - backend/tests/test_graph_visualization.py (10 unit tests)
  modified:
    - backend/app/agents/graph.py (218 lines added: 3 nodes + routing + retry logic)
    - backend/app/services/agent_service.py (8 lines added: chart metadata persistence)
decisions:
  - "Max 1 retry (2 total attempts) for chart execution failures"
  - "Feed error context back to Visualization Agent for targeted code fixes"
  - "Subtle frontend notification on chart failure (don't alarm user)"
  - "Server-side only error logging (don't expose internal errors to frontend)"
  - "Chart failure is non-fatal (analysis text and data table always preserved)"
metrics:
  duration_minutes: 5.4
  completed_date: 2026-02-13
  tasks_completed: 2
  files_modified: 2
  files_created: 1
  tests_added: 10
  tests_passing: 144
---

# Phase 22 Plan 02: Graph Integration for Visualization Pipeline Summary

Wire the Visualization Agent into the LangGraph pipeline with conditional routing, chart execution, error handling, and SSE streaming.

## Deviations from Plan

None - plan executed exactly as written.

## Implementation Details

### Task 1: Visualization Pipeline Nodes and Conditional Routing

**Added to `backend/app/agents/graph.py`:**

1. **`should_visualize()` conditional edge function** - Routes to visualization pipeline when `visualization_requested` is true, otherwise routes to END (preserves existing tabular flow)

2. **`viz_execute_node()` async function** - Executes chart code in E2B sandbox with retry logic:
   - Parses chart JSON from stdout (fast path: single line, fallback: joined stdout for large JSON)
   - Validates chart JSON size (2MB limit)
   - Max 1 retry (2 total attempts) on failure
   - Feeds error context back to Visualization Agent for targeted fixes via `_retry_chart_code()`

3. **`_retry_chart_code()` helper function** - Calls `visualization_agent_node` with error context to regenerate code

4. **`viz_response_node()` async function** - Handles visualization results and emits SSE events:
   - Success: emits `chart_completed` with chart_specs
   - Failure: emits `chart_failed` with subtle notification (server-side error logging only)

5. **Modified `build_chat_graph()`** - Wired visualization pipeline:
   - Added 3 new nodes: `visualization_agent`, `viz_execute`, `viz_response`
   - Replaced `da_response` finish point with conditional routing via `should_visualize`
   - Added linear edges: `visualization_agent` -> `viz_execute` -> `viz_response`
   - Set `viz_response` as finish point

6. **Updated module docstring** - Documented visualization pipeline flow

**Verification:** Graph compiles without errors, all existing tests pass (134 tests).

**Commit:** `f96c3cc` - feat(22-02): add visualization pipeline nodes and conditional routing to graph

### Task 2: Chart Metadata Persistence and Tests

**Modified `backend/app/services/agent_service.py`:**

1. **`run_chat_query()`** - Added `chart_specs` and `chart_error` to:
   - Message metadata (both session and file flows)
   - Return dict

2. **`run_chat_query_stream()`** - Added `chart_specs` and `chart_error` to:
   - Message metadata (both session and file flows)
   - SSE event filter already included them (line 567)

**Created `backend/tests/test_graph_visualization.py`:**

10 unit tests covering:

1. **`TestShouldVisualizeRouting` (3 tests):**
   - `test_should_visualize_true` - Returns "visualization_agent" when flag is true
   - `test_should_visualize_false` - Returns "finish" when flag is false
   - `test_should_visualize_missing_field` - Returns "finish" when field missing (default)

2. **`TestVizExecuteNode` (4 tests):**
   - `test_viz_execute_empty_code` - Returns chart_error when chart_code is empty
   - `test_viz_execute_success` - Extracts chart JSON on successful execution
   - `test_viz_execute_failure_max_retries` - Returns chart_error after max retries exhausted
   - `test_viz_execute_chart_too_large` - Discards chart JSON > 2MB

3. **`TestVizResponseNode` (2 tests):**
   - `test_viz_response_success` - Emits chart_completed SSE event when chart_specs present
   - `test_viz_response_failure` - Emits chart_failed SSE event when chart_error present

4. **`TestGraphCompilation` (1 test):**
   - `test_graph_compiles_with_viz_nodes` - Verifies graph compiles without error

**Verification:** All 144 tests pass (134 existing + 10 new), no regressions.

**Commit:** `9417128` - feat(22-02): add chart metadata persistence and visualization pipeline tests

## Success Criteria Met

- [x] Graph compiles with 3 new nodes: visualization_agent, viz_execute, viz_response
- [x] should_visualize conditional edge routes to visualization_agent when flag is true, to END when false
- [x] da_response is no longer a terminal node -- it routes conditionally
- [x] viz_execute runs chart code in E2B sandbox with retry (max 1 retry, 2 total attempts)
- [x] viz_response emits chart_completed or chart_failed SSE events
- [x] Chart failure is non-fatal -- analysis and data table are always preserved
- [x] agent_service.py saves chart_specs and chart_error in message metadata
- [x] 10 unit tests pass for the visualization pipeline
- [x] All existing tests pass without modification (backward compatible)

## Key Links Verified

1. **graph.py -> visualization.py:**
   - Import: `from app.agents.visualization import visualization_agent_node`
   - Usage: `graph.add_node("visualization_agent", visualization_agent_node)`

2. **graph.py -> sandbox:**
   - Import: `from app.services.sandbox import E2BSandboxRuntime, ExecutionResult`
   - Usage: `E2BSandboxRuntime` in `viz_execute_node` for chart code execution

3. **graph.py -> state.py:**
   - Usage: `state.get("visualization_requested", False)` in `should_visualize`
   - Usage: `state.get("chart_code", "")` in `viz_execute_node`

## Backward Compatibility

When `visualization_requested` is false (default):
- `should_visualize` routes to END (skips visualization entirely)
- Produces byte-for-byte identical behavior to previous flow
- No performance impact on existing tabular queries

## Next Steps

Phase 23 (Frontend Integration):
- Add ChartRenderer component to display chart_specs
- Handle SSE events: chart_completed, chart_failed
- Display subtle notification on chart failure
- Export chart as PNG/SVG via client-side Plotly.downloadImage()

## Self-Check: PASSED

**Created files exist:**
```
FOUND: backend/tests/test_graph_visualization.py
```

**Modified files exist:**
```
FOUND: backend/app/agents/graph.py
FOUND: backend/app/services/agent_service.py
```

**Commits exist:**
```
FOUND: f96c3cc - feat(22-02): add visualization pipeline nodes and conditional routing to graph
FOUND: 9417128 - feat(22-02): add chart metadata persistence and visualization pipeline tests
```

**Tests pass:**
```
✓ 144 tests passing (134 existing + 10 new)
✓ No regressions
```

**Graph verification:**
```
✓ Graph compiles without errors
✓ should_visualize function exists
✓ visualization_agent node registered
✓ chart_specs in agent_service.py metadata
```
