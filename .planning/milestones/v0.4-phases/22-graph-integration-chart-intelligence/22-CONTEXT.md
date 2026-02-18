# Phase 22: Graph Integration & Chart Intelligence - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the Visualization Agent into the LangGraph pipeline with intelligent routing — charts generate only when the AI determines they add value, and failures don't break the user experience.

This phase is about orchestration and decision logic — connecting the pieces built in Phase 20-21 into a working flow with smart conditional routing.

</domain>

<decisions>
## Implementation Decisions

### Routing Triggers & Chart Discretion

- **Discretion level:** Balanced with strong preference for showing charts — when in doubt, show the chart if data supports visualization
- **No hardcoded triggers:** Case-by-case AI judgment only, no pattern matching or keyword heuristics
- **Holistic evaluation:** AI decides based on full context, not specific data characteristics (volume, types, temporal patterns)
- **Two-phase flag setting:** Prediction + confirmation
  - Manager Agent predicts visualization likelihood early in pipeline
  - Data Analysis Agent confirms and sets final `visualization_requested` flag after seeing actual results

### Manager Agent Involvement

- **Provides chart type suggestions:** Manager hints at likely chart types (bar, line, scatter) during query routing
- **Flow via state:** Suggestions stored in `ChatAgentState.chart_hint` field
- **Advisory, not binding:** Visualization Agent can override Manager's suggestions based on actual data
- **Conditional generation:** Manager only provides chart type suggestions when visualization seems likely (not for every query)

### Failure Handling & Degradation

- **User experience:** Subtle notification — inform user chart is unavailable but don't alarm (e.g., small "Chart unavailable" notice)
- **Error logging:** Server-side only — don't expose error details to frontend, keep state clean
- **Retry logic:** Retry with error context, max 1 retry (2 total attempts)
  - Feed error back to Visualization Agent to fix code and regenerate
  - Similar to existing code retry pattern
- **Analysis preservation:** Always preserve — chart is additive
  - Analysis text and data table generated first
  - Chart generation happens after, failure never affects core results

### Graph Flow & Node Structure

- **Architecture:** LangGraph-managed separate nodes (for scalability and future flexibility)
  - Data Analysis Agent completes and emits SSE with analysis results
  - LangGraph conditionally routes to Visualization node if `visualization_requested` is true
  - Visualization node generates chart and emits separate SSE event
- **Non-blocking execution:** Analysis returns first, chart streams separately
  - User sees analysis text + table immediately
  - Chart appears below table when ready (via separate SSE event)
- **Conditional routing:** Skip visualization entirely when `visualization_requested` is false
  - Don't call Visualization Agent at all if flag is false
  - Fastest path for non-visual queries
- **Backward compatibility:** Identical behavior when visualization is skipped
  - Existing tabular flow must be byte-for-byte identical when `visualization_requested` is false
  - Zero impact on current queries

### Claude's Discretion

- Exact SSE event structure for chart data
- LangGraph node naming conventions
- Retry backoff timing
- Subtle notification message wording
- Server-side error log format

</decisions>

<specifics>
## Specific Ideas

- "LangGraph-managed flow ensures scalability and reusability of Visualization Agent for future use cases"
- Start with simple implementation (internal steps within nodes), refactor to more granular nodes (viz_execute, viz_response) if testing reveals need for better separation
- Keep trigger logic independent and modular so flow can be easily changed based on test results

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 22-graph-integration-chart-intelligence*
*Context gathered: 2026-02-13*
