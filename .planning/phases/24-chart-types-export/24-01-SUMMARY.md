---
phase: 24-chart-types-export
plan: 01
subsystem: ai-prompts
tags: [plotly, visualization, llm-prompts, chart-types]

# Dependency graph
requires:
  - phase: 23-frontend-chart-rendering
    provides: Frontend chart rendering infrastructure with ChartRenderer component
provides:
  - Enhanced visualization agent prompt with explicit code patterns for 7 chart types
  - Label formatting rules for human-readable chart titles and axis labels
  - Chart type selection heuristics including donut chart support
affects: [24-chart-types-export, visualization, data-visualization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Explicit Plotly code pattern examples in LLM system prompts"
    - "Label formatting rules with unit inference (revenue->$, count->Count, percent->%)"
    - "Chart type selection rules with data shape heuristics"

key-files:
  created: []
  modified:
    - backend/app/config/prompts.yaml

key-decisions:
  - "Provide explicit Plotly Express code patterns for all 7 chart types to reduce LLM code generation errors"
  - "Include label formatting rules requiring human-readable titles (max 8 words) and axis labels with inferred units"
  - "Clarify histogram vs bar chart distinction (histogram for distributions, bar for categorical comparisons)"
  - "Add donut chart pattern (pie with hole=0.4) for part-to-whole visualizations"

patterns-established:
  - "LLM prompt engineering: Include explicit code patterns, not just descriptions"
  - "Label formatting: Convert snake_case to Title Case, add units based on column semantics"
  - "Chart selection: Query-driven selection (e.g., 'distribution' keyword triggers box plot)"

# Metrics
duration: 2min
completed: 2026-02-13
---

# Phase 24 Plan 01: Visualization Prompt Enhancement Summary

**Enhanced visualization agent system prompt with 7 explicit Plotly code patterns, label formatting rules, and chart type selection heuristics to improve LLM chart generation accuracy**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-13T22:02:41Z
- **Completed:** 2026-02-13T22:04:40Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added explicit Plotly Express code patterns for all 7 chart types (bar, line, scatter, histogram, box, pie, donut) with labels parameter usage
- Defined label formatting rules requiring human-readable titles (max 8 words) and axis labels with units (revenue->$, count->Count, percent->%)
- Clarified chart type selection rules including histogram for distributions (>8 unique values), donut charts (pie with hole=0.4), and query-driven box plots
- Added common pitfall warnings (don't use bar for distributions, limit pie charts to 8 categories, sort line charts by date)

## Task Commits

Each task was committed atomically:

1. **Task 1: Enhance Visualization Agent prompt with chart type patterns and label rules** - `5dbd9ad` (feat)

## Files Created/Modified
- `backend/app/config/prompts.yaml` - Enhanced visualization agent system_prompt with chart type code patterns, label formatting rules, and selection heuristics

## Decisions Made
- Explicit Plotly code patterns reduce ambiguity for LLM code generation (e.g., showing hole=0.4 for donut prevents omission)
- Label formatting rules enforce human-readable output with unit inference based on column name semantics
- Chart type selection rules expanded from 9 to 10, clarifying histogram (distributions) vs bar (categorical) distinction
- Query-driven selection for box plots ("distribution"/"spread"/"variance" keywords) and donut charts ("donut" keyword)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failure in tests/test_graph_visualization.py::TestVizResponseNode::test_viz_response_success (unrelated to prompts.yaml changes). This is a known issue from Phase 23-02 where viz_response_node was updated to return chart data in node output. The test expects empty return `{}` but now returns `{'chart_error': '', 'chart_specs': '...'}`. This does not block plan completion as it predates this change and is not caused by the visualization prompt enhancement.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Visualization agent system prompt now comprehensively covers all 7 chart types (CHART-01 through CHART-07) and label formatting guidance (CHART-11). Ready for Plans 02-03 to implement frontend chart type validation and client-side export functionality.

## Self-Check

Verifying claims made in this summary:

**Files modified:**
- FOUND: backend/app/config/prompts.yaml

**Commits:**
- FOUND: 5dbd9ad

**Result:** PASSED - All claims verified.
