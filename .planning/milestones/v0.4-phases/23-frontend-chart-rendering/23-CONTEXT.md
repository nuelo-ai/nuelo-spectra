# Phase 23: Frontend Chart Rendering - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Display AI-generated Plotly charts in DataCards when chart JSON is available from the backend. Users see interactive visualizations alongside their data tables with zoom, pan, and hover tooltips. Chart generation and intelligence was completed in Phase 22 - this phase handles frontend rendering only.

</domain>

<decisions>
## Implementation Decisions

### Chart Placement & Data Relationship
- Chart appears **below the data table** (table first priority, chart as supplementary visual)
- Chart is **always visible when present** - no collapse/hide controls, simpler UI
- Table scrolls independently with max height - chart stays visible above scrolling table
- Full design discretion to **revamp DataCard design** for visual appeal (using frontend design best practices)

### Loading States & Progression
- Loading visual: **Spinner with text** ("Generating visualization...")
- Progress indication: **Stage indicators** showing progression ("Analyzing data..." → "Creating chart...")
- Chart transition: **Fade in smoothly** when loading completes
- Charts are interactive by default (zoom, pan, hover tooltips via Plotly.js)

### Failure States & Recovery
- Failure display: **Subtle notification only** (small dismissible alert at top of DataCard, doesn't take chart space)
- Notification: **Persistent but dismissible** - stays until user clicks X to close
- **No retry in frontend** - Phase 22 backend handles retry logic (max 1 retry = 2 attempts). If frontend receives error, it's final.
- Error details: **Helpful context** - brief user-friendly explanation (e.g., "Chart couldn't be generated for this data type")

### Chart Sizing & Responsiveness
- Height: **Dynamic based on data** - adjusts to data complexity (more data points = taller chart)
- Width: **Full container width** - chart spans entire DataCard width
- **Responsive to future changes** - if DataCard width increases later, chart follows responsively

### Claude's Discretion
- DataCard visual design and layout styling (open to full redesign)
- Loading state timing (when to show, perceived performance optimization)
- Mobile chart behavior (responsive design patterns)
- Resize event handling (performance/UX balance)

</decisions>

<specifics>
## Specific Ideas

- User is open to **revamping the entire DataCard design** to make it more visually appealing - use creative frontend design judgment
- Chart must **responsively adapt** if DataCard container width changes in the future
- Backend retry is already handled (Phase 22) - frontend just displays final result or error

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 23-frontend-chart-rendering*
*Context gathered: 2026-02-13*
