# Phase 20: Infrastructure & Pipeline - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Preparing the platform foundation for chart generation — allowlisting Plotly in code checker, extending ChatAgentState schema to carry visualization data, verifying E2B sandbox can execute Plotly code, and implementing output parser to extract chart JSON from sandbox stdout.

This phase delivers infrastructure only. Actual chart generation logic, UI rendering, and chart type implementations belong in later phases (21-25).

</domain>

<decisions>
## Implementation Decisions

### Chart Security Boundaries
- **External data fetching:** Block all external fetching — charts only use data passed from analysis results (no network calls, no remote APIs, no external images)
- **File system access:** Read-only access to temp directory for large datasets (no write access, prevents data leakage)
- **Chart types allowed:** All 7 required chart types from the start (bar, line, scatter, histogram, box, pie, donut)
- **Custom JavaScript:** Claude's discretion — determine if custom JS should be allowed based on security best practices

### Error Handling & User Experience
- **Error visibility:** Show error message to user when chart generation fails (transparent, not silent)
- **Data preservation:** Always preserve and display the original data table even if chart generation fails (users always get value)
- **Retry logic:** Auto-retry once on transient failures (improves success rate without requiring user re-query)
- **Error message detail:** Adaptive approach — simple user-friendly message with expandable technical details for debugging

### Validation Depth & Completeness
- **Testing level:** Claude's discretion — determine appropriate validation depth (version check vs sample chart generation)
- **Chart type verification:** Defer comprehensive chart type validation to Phase 24 (Chart Types & Export) — Phase 20 just proves infrastructure works
- **Performance benchmarks:** No performance benchmarks in Phase 20 — focus on functionality first, optimize later
- **Test data:** Claude's discretion — choose between synthetic test data or real data samples

### Output Structure & Flexibility
- **Multiple charts per response:** Claude's discretion — determine if infrastructure should support 2-3 charts per response from the start (requirements mention this capability)
- **Chart metadata:** Include basic metadata (title, caption, chart type) alongside chart JSON — data summary comes from analyst agent, not visualization output
- **JSON schema strictness:** Claude's discretion — balance between strict validation (catches errors early) and flexible parsing (more forgiving)
- **Backward compatibility:** Optimize for clean state schema design — breaking changes acceptable since there are no production users yet

### Claude's Discretion
- Custom JavaScript support in Plotly charts
- Validation testing depth (version check vs chart generation)
- Test data approach (synthetic vs real samples)
- Multiple charts per response support
- JSON schema validation strictness

</decisions>

<specifics>
## Specific Ideas

- The platform already has established patterns for state management (ChatAgentState), code validation (Code Checker with AST allowlists), and sandbox execution (E2B) — extend these rather than rebuild
- Research indicates Plotly 6.x with `fig.to_json()` for JSON output, client-side rendering via plotly.js-dist-min (~1MB), no server-side Kaleido needed
- Data table preservation on chart failure is critical — the analysis result is valuable even without visualization

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (infrastructure preparation only)

</deferred>

---

*Phase: 20-infrastructure-pipeline*
*Context gathered: 2026-02-13*
