# Phase 42: Analysis Workspace & Pulse Detection - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the `pulse-mockup/` standalone Next.js app (from scratch) covering the Analysis Workspace entry, Collection management, and the full Pulse Detection flow — from Collection list through file selection, Run Detection with loading state, through to Signal results. Credit balance and pre-action cost display are included. This is a static mockup only — no real API calls, no live backend.

</domain>

<decisions>
## Implementation Decisions

### Visual Design
- Fresh design direction — NOT the existing Nord/dark theme from `frontend/`
- This mockup can serve as the visual design reference/influence for future Spectra milestones (v0.8+)
- Aesthetic: dark, data-dense, analytical — Hex.tech as the primary reference (clean card layouts, dark palette, accent-colored status indicators)
- Fidelity: production-quality polish — presentable to a client or investor as-is
- Theme: dark + light theme toggle supported (shadcn/ui theming)

### Navigation & App Shell
- Shell: left sidebar + top header
- Sidebar: full Spectra nav mocked — Chat, Analysis Workspace (active), Files, API, Settings
- Routing: real Next.js routes (not single-page state)
  - `/workspace` — Collection list (entry point)
  - `/workspace/collections/[id]` — Collection detail
  - `/workspace/collections/[id]/signals` — Signal results
- Entry point: `/workspace` goes directly to the Collection list — no separate dashboard or welcome screen

### Collection List Page
- "Create New Collection" entry: empty state CTA (when no collections) + header button (always)
- Collection cards show: name, status badge (active/archived), created date, signal count

### Collection Creation Flow
- Triggered via: empty state CTA or header button
- Form: inline modal/dialog (not a separate page)
- Fields: collection name (required) + optional description
- Post-create: user is redirected to the Collection detail page with the file selection area in focus — at least 1 file must be linked or uploaded before detection can run

### Collection Detail — File Management
- Layout: combined view — dropzone/upload area at top, existing files list below (no tabs)
- File list: table rows with checkboxes — columns: file name, type icon, size, upload date
- Uploading a new file triggers the existing Spectra file onboarding process (AI profiling → initial data summary)
- Profiling state shown inline in the file list row: "Profiling..." status badge + progress indicator
- When profiling completes: status changes to "Ready"; clicking the file row opens a data summary side panel on the right

### Run Detection — Button & Credit Display
- Run Detection button lives in a sticky action bar pinned to the page bottom
- Sticky bar shows: files selected count + estimated credit cost + Run Detection button
- Button is disabled (with hint text) when no files are selected: "Select at least 1 file to run detection"
- Credit estimate shown inline in the bar: "~5 credits for 3 files selected"

### Run Detection — Loading State
- Style: animated step stages with status text (3–5 labeled steps)
  - Example steps: "Analyzing files" → "Detecting patterns" → "Scoring signals" → "Finalizing results"
- Loading replaces the Collection detail page content (full-page transition, not an overlay)
- Estimated time indicator visible (15–30s range)

### Signal Results — Transition & Layout
- After detection completes: auto-navigate to `/workspace/collections/[id]/signals` — no user action required
- Layout: 3-column — main sidebar (~240px) + signal list panel (~280px, fixed width) + signal detail (remaining)
- On page load: highest severity signal is auto-selected and shown in the detail panel
- Signal list cards: title + severity badge + category tag (compact, no description snippet)

### Signal Severity Color Scheme
- Red = Critical
- Amber = Warning
- Green = Informational / Opportunity

### Signal Detail Panel
- Shows: title, description, severity badge, category tag, statistical evidence summary
- Chart area: rendered Recharts or Plotly chart with realistic mock data (not a placeholder box)

### Credit System
- Credit balance indicator visible in the app shell (header or sidebar)
- Pre-action cost estimate shown in the sticky action bar before running detection (PULSE-08)

### Claude's Discretion
- Exact color palette values within the dark Hex.tech-inspired direction
- Typography choices (font family, weights, sizing scale)
- Exact spacing and component padding
- Skeleton loading design for the signal list while results are arriving
- Error state handling (failed detection, profiling errors)
- Specific chart types used in signal detail mock data (line, bar, scatter — choose based on signal category)
- Credit balance placement (header vs. sidebar)

</decisions>

<specifics>
## Specific Ideas

- Design should feel like Hex.tech — dark analytical, clean card layouts, accent-colored severity/status indicators
- The mockup is a design reference for v0.8+ implementation — it should look like the real product will look
- File onboarding follows the existing Spectra flow: upload → AI profiling → data summary (same behavior, mocked as static states)
- Sticky bottom action bar pattern for Run Detection — always visible regardless of scroll position
- After detection: auto-navigate to results, highest severity signal pre-selected so the user immediately sees the most important finding

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/badge.tsx` — badge component for severity and status badges; severity color variants (red/amber/green) align with existing badge patterns
- `frontend/src/components/ui/card.tsx` — card component for collection cards and signal cards
- `frontend/src/components/ui/progress.tsx` — progress bar for file profiling inline row indicator
- `frontend/src/components/ui/skeleton.tsx` — skeleton loading component for list states
- `frontend/src/components/ui/button.tsx` — button component
- `frontend/src/components/ui/dialog.tsx` — dialog for Create Collection modal
- `frontend/src/components/ui/sheet.tsx` — sheet/drawer for data summary side panel (triggered on file row click)
- `frontend/src/components/ui/table.tsx` — table for file list rows with checkboxes
- `frontend/src/components/ui/scroll-area.tsx` — scroll area for signal list panel
- `frontend/src/components/ui/input.tsx` + `frontend/src/components/ui/textarea.tsx` — form fields for Create Collection dialog

### Established Patterns
- shadcn/ui component library — use the same component primitives across the new mockup app for consistency
- Dark theme + light theme toggle — shadcn/ui theming system supports this natively via CSS variables

### Integration Points
- `pulse-mockup/` is a completely standalone Next.js app at the repo root — no imports from `frontend/` or `admin-frontend/`
- Components from `frontend/src/components/ui/` are reference only — re-install shadcn/ui in `pulse-mockup/` independently
- No backend integration — all data is static mock data defined in the mockup

</code_context>

<deferred>
## Deferred Ideas

- Final Report view — user mentioned this during discussion; belongs in Phase 43 (Collections & Reports)

</deferred>

---

*Phase: 42-analysis-workspace-pulse-detection*
*Context gathered: 2026-03-04*
