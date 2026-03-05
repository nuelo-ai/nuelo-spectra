# Phase 43: Collections & Reports - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the full Collections lifecycle within the `pulse-mockup/` app — redesign the collection detail page as a tabbed hub (Overview, Files, Signals, Reports), add report viewer with document-style reading experience and download options, build a minimal Chat page to demonstrate the Chat-to-Collection bridge, and display running credit totals. Archive/unarchive and collection limits are deferred.

</domain>

<decisions>
## Implementation Decisions

### Collection Detail — Tabbed Layout
- Redesign `/workspace/collections/[id]` from single-view to tabbed layout: **Overview | Files | Signals | Reports**
- Overview is the default landing tab — the collection "home page"
- Files tab contains the existing file table, upload zone, and sticky action bar from Phase 42
- Signals tab shows signal list (compact view, or links to full `/signals` page)
- Reports tab shows report list with clickable entries

### Collection Detail — Overview Tab
- **Summary stat cards** at top: files count, signals count, reports count, credits used
- **Signals section** (hero position, right after stats): shows signals with severity badges — this is the most important section. Clicking a signal navigates to `/workspace/collections/[id]/signals` with that signal pre-selected
- **Files table** below signals: compact table showing file names, types, status — clickable to open the data summary modal (FileContextModal-style)
- **Recent activity feed** at the bottom: timeline of events (e.g., "Detection ran — 6 signals found", "2 files added", "Investigation completed")

### Run Detection — Contextual Placement
- **Overview tab**: contextual CTA banner appears ONLY when new/changed files exist — e.g., "You have 2 new files — Run Detection"
- **Files tab**: full sticky action bar with file selection, credit estimate, and Run Detection button (existing Phase 42 behavior)
- Run Detection is NOT available when there are no new/changed files (user feedback from Phase 42)

### Empty States — Progressive
- **Brand new collection (no files)**: stat cards all show 0, signals section shows "No signals yet — upload files and run detection to discover insights", files section shows upload zone
- **Files uploaded, no detection**: files stat populated, signals/reports show 0, signals section shows "Run Detection to discover signals in your data" with CTA, Overview CTA banner appears
- **Detection run, no reports**: files and signals populated, reports show 0, reports section shows "Reports will appear here after investigation is complete"

### Report Viewer & Download
- Reports tab shows a list of reports: type, title, generated date
- Clicking a report navigates to a **full-page route**: `/workspace/collections/[id]/reports/[reportId]`
- **Document-style reader**: paper-white background, centered content column, clean typography — like Google Docs or Microsoft Word read-only view. Stands out against the dark app shell
- **Sticky header bar** on the report page: report title + "Download as Markdown" and "Download as PDF" buttons, always visible while scrolling
- **Report types** (mock multiple): Detection Summary, Investigation Report, What-If Scenario Report, Chat Report (from Chat-to-Collection bridge), Custom Report

### Chat-to-Collection Bridge
- **Minimal mock Chat page** at `/chat`: one static conversation with 2-3 data result cards (table, chart, analysis text)
- Each data card has an **"Add to Collection" button**
- Clicking opens a **simple list picker modal**: searchable list of existing collections, option to create new collection inline
- **Content saved**: everything from the Chat result — visualizations, tables, analysis text — but NOT code blocks
- **Saved as a report**: the Chat content appears as a "Chat Report" in the Collection's Reports tab, viewable in the same document-style reader

### Credit Display
- Running credit total displayed in the collection header: "Credits used: 14" (COLL-07)
- Existing credit balance indicator in the app shell header remains (from Phase 42)

### Claude's Discretion
- Exact tab component styling and transitions
- Activity feed item formatting and icons
- CTA banner design for "new files available" state
- Report list card design within the Reports tab
- Mock Chat page conversation layout (keep minimal)
- How signals are displayed in the Overview tab (cards vs. compact list vs. table)
- Report markdown content for mock reports

</decisions>

<specifics>
## Specific Ideas

- Report viewer should look like Google Docs / Microsoft Word — paper-white document against the dark app shell, centered content column, proper typography
- Signals are the hero of the Pulse feature — they must be prominent and immediately visible on the Overview tab so users know at a glance what actions to take
- Chat-to-Collection saves everything as-is from the Chat (visualizations, tables, analysis) except code — and it appears as a report in the Collection
- The Overview tab is a command center: stats, signals (hero), files, activity — not just a summary page

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pulse-mockup/src/components/workspace/signal-card.tsx`: Signal card with severity badge — reuse on Overview tab signals section
- `pulse-mockup/src/components/workspace/file-table.tsx`: File table with checkboxes — reuse in Files tab and compact version in Overview
- `pulse-mockup/src/components/workspace/data-summary-panel.tsx`: FileContextModal-style dialog — reuse for file click on Overview tab
- `pulse-mockup/src/components/workspace/sticky-action-bar.tsx`: Run Detection bar — reuse in Files tab
- `pulse-mockup/src/components/workspace/detection-loading.tsx`: Loading animation — reuse as-is
- `pulse-mockup/src/components/ui/tabs.tsx`: shadcn/ui tabs component already installed
- `pulse-mockup/src/lib/mock-data.ts`: Existing mock collections, files, signals — extend with reports and chat data

### Established Patterns
- Dark Hex.tech-inspired design system with shadcn/ui components
- Dialog/Modal pattern for data summary (large centered modal, single column)
- Full-page routes for detail views (signals page pattern)
- Sticky bars for actions (action bar pattern)

### Integration Points
- `/workspace/collections/[id]` page needs full redesign from single-view to tabbed layout
- New routes: `/workspace/collections/[id]/reports/[reportId]` for report reader
- New route: `/chat` for minimal mock Chat page
- Sidebar nav: "Chat" item currently links to `#` — update to `/chat`
- `mock-data.ts` needs new types/data: reports, chat messages, chat data cards

</code_context>

<deferred>
## Deferred Ideas

- **COLL-01: Archive/unarchive actions and status indicators** — not critical at this point, defer to future phase
- **COLL-02: Collection limit display ("3 of 5 active collections") and upgrade prompt** — depends on archive feature, deferred together
- Full Chat implementation — only minimal mock needed for bridge demo

</deferred>

---

*Phase: 43-collections-reports*
*Context gathered: 2026-03-04*
