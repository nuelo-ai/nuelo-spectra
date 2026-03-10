# Phase 51: Frontend Migration - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Migrate pulse-mockup workspace pages into the main frontend app with live API data. Apply Hex.tech dark palette to globals.css, build (workspace) route group with its own layout, replace shared UI components with mockup versions (full UI refresh), connect all workspace pages to real backend APIs. Requirements: NAV-01-04, SIGNAL-01-04.

</domain>

<decisions>
## Implementation Decisions

### Component migration strategy
- Replace ALL shared UI components (button, card, badge, dialog, etc.) with pulse-mockup versions — this is a deliberate full UI refresh, not just workspace
- Copy-and-adapt workspace-specific components from mockup (signal-card, detection-loading, file-table, etc.) — rewire imports and replace mock data with API calls
- Skip v0.9+ components entirely (add-to-collection-modal, investigation-qa-thread, whatif-refinement-chat) — bring them when their phases arrive
- Plan MUST include regression verification for existing pages (/my-files, /sessions/*, /settings, /dashboard) after component swap — existing functionality must keep working
- UI refresh cascades to all existing pages via component + palette swap — plan includes per-page verification pass

### Chart library
- Plotly everywhere — no Recharts in the final app
- Rewrite mockup's Recharts signal charts in Plotly since backend Visualization Agent already outputs Plotly JSON (fig.to_json())
- Signal charts must match mockup's visual style (area fills, gradient backgrounds, color scheme) using Plotly equivalents
- Existing ChartRenderer component can be reused/adapted for signal charts

### Sidebar & navigation
- Build ONE unified sidebar for the entire app, replacing the current ChatSidebar
- Based on mockup's sidebar.tsx design — nav links for Pulse Analysis, Chat, Files, Settings, Admin Panel
- Chat history list becomes a context section within the sidebar (only visible on chat routes), not the whole sidebar
- Both (workspace) and (dashboard) route groups use the unified sidebar
- Migration must be careful to avoid breaking existing chat/dashboard functionality
- Keep current sidebar structure for existing items (e.g., API stays under Settings as it is now)
- Link nav entries to existing pages: Files -> /my-files, Settings -> /settings (with API keys tab)
- Admin Panel nav entry only visible to admin users, opens admin-frontend
- Refresh visual look of all sidebar elements to match Hex.tech palette

### Signal display & interaction
- Split-panel layout migrated as-is from mockup: SignalListPanel (left) + SignalDetailPanel (right)
- Signals sorted by severity (critical -> warning -> info) per SIGNAL-01
- Highest-severity signal auto-selected on page load per SIGNAL-02
- Investigation + What-If buttons visible but grayed out (opacity-50) with hover tooltip "Coming in a future update" per SIGNAL-03
- Signal chart type driven by chartType field, rendered via Plotly per SIGNAL-04
- Empty signals state: friendly message + "Run Detection" CTA directing to Files tab

### Data fetching & state
- TanStack Query hooks for all workspace API calls (collections, signals, reports), following existing frontend patterns
- Zustand for client-only workspace state (selected signal, selected files for detection)
- Skeleton loaders for all workspace page loading states (card skeletons for collection list, panel skeletons for signals)
- Inline error display with "Try again" retry button for API failures — page layout stays intact
- TanStack Query refetchInterval (~3s) for Pulse detection polling, stop when status changes to complete/failed

### Claude's Discretion
- Exact migration order within each plan (which components first)
- Skeleton loader layout shapes per page
- Plotly configuration details for matching mockup chart aesthetics
- Query key naming conventions for workspace hooks
- Zustand store structure for workspace state

</decisions>

<specifics>
## Specific Ideas

- The UI refresh is intentional — mockup versions of shared components become the new standard for the entire app, not just workspace pages
- Unified sidebar is a long-term investment — one sidebar component to maintain as new features (v0.9 reports, v0.10 investigation) get added
- Signal charts should replicate the mockup's area fills and gradient backgrounds in Plotly — not just "Plotly defaults with colors"
- Per-page regression verification is non-negotiable after UI component swap — chat interface, data cards, file upload, settings forms must all work

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/` — 20+ shadcn/ui components to be REPLACED with mockup versions
- `frontend/src/components/chart/ChartRenderer.tsx` — custom Plotly component, reuse/adapt for signal charts
- `frontend/src/components/sidebar/ChatSidebar.tsx` — to be replaced by unified sidebar
- `pulse-mockup/src/components/workspace/` — ~20 workspace components to copy-and-adapt
- `pulse-mockup/src/components/layout/sidebar.tsx` — basis for unified sidebar
- `pulse-mockup/src/components/ui/` — replacement UI components

### Established Patterns
- Route groups: `(dashboard)` layout wraps chat pages — new `(workspace)` route group follows same pattern
- TanStack Query: `useQuery`/`useMutation` with typed API functions in existing hooks
- Zustand: stores in `frontend/src/stores/` for client state
- shadcn/ui: all UI primitives from `@/components/ui/`

### Integration Points
- `frontend/src/app/(workspace)/` — new route group to create
- `frontend/src/app/(dashboard)/layout.tsx` — refactor to use unified sidebar
- `frontend/src/app/globals.css` — Hex.tech palette tokens
- `frontend/src/app/providers.tsx` — ThemeProvider addition
- Backend API: `/collections`, `/collections/{id}/pulse`, `/collections/{id}/signals` endpoints (Phase 48-50)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 51-frontend-migration*
*Context gathered: 2026-03-07*
