# Phase 46: Admin Workspace Management - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Add admin-facing screens to the existing `pulse-mockup/` app — a new `/admin/*` route section with its own sidebar layout, covering the Workspace Activity Dashboard, per-user Workspace tab extension on user detail pages, and Workspace Credit Costs + Alerts settings. All static mockup pages with hardcoded mock data. No real backend, no API calls.

</domain>

<decisions>
## Implementation Decisions

### Admin Shell

- New `/admin/*` route prefix with its own sidebar layout — completely separate from the `/workspace` user area
- Admin sidebar nav items: Dashboard, Users, Settings. Other items (API Keys, Audit Log) appear in the sidebar as placeholders (link to a placeholder page or show "Coming soon")
- Same dark Hex.tech design system as the rest of the mockup — no different admin aesthetic
- Admin shell routes:
  - `/admin` or `/admin/dashboard` — Workspace Activity Dashboard
  - `/admin/users` — Users list
  - `/admin/users/[id]` — User detail with tabs
  - `/admin/settings` — Settings page

### Activity Dashboard

- **Page layout**: sectioned scroll page — not a tight grid. Charts grouped into labeled sections with headings:
  1. **KPI row** at the very top: 4 stat cards (Total Collections, Active Users, Credits Used This Month, Avg Credits per Collection)
  2. **Workspace Activity section**: line chart (Collections created over time) + donut chart (active vs. archived) + bar charts (Pulse / Investigation / What-If / Report activity counts)
  3. **Pipeline Adoption section**: funnel chart showing drop-off across Pulse → Explain → What-If pipeline stages
  4. **Credit Usage section**: credit consumption chart (by activity type over time) + KPI card (average credits per Collection)
- **Chart library**: Recharts (already in the mockup, shadcn/ui chart components wrap it)

### Settings Page

- Single `/admin/settings` page — not split into sub-routes
- Two sections on the page, scrollable:
  1. **Workspace Credit Costs** section: 8 labeled input fields (one per activity type, e.g., Pulse Detection, Investigation, What-If, Report Generation, Chat Analysis, etc.). Section-level "Save Changes" button at the bottom — one save for all 8 fields at once.
  2. **Workspace Alerts** section: threshold configuration inputs (e.g., "Alert when user exceeds X credits in Y days") + an active alert list below
- **Active alert list**: 2–3 pre-populated mock alert cards. Each card shows: severity icon (warn/critical) + alert message + timestamp + "Dismiss" button. Clicking Dismiss removes the card from the list (client-side state toggle in the mockup).

### Per-user Workspace Tab

- **Users list page** (`/admin/users`): minimal — 3–4 mock users in a simple table (columns: name, email, tier, status, credits). Clickable rows navigate to user detail. No search, filter, or pagination.
- **User detail page** (`/admin/users/[id]`): header card (avatar placeholder, name, email, status badge, tier badge) + tabs: Overview | Workspace | API Keys
  - **Overview tab**: placeholder — basic stat cards (credits, files, sessions) with static numbers. Not fully built.
  - **API Keys tab**: placeholder — "API key management coming soon" or simple empty state.
  - **Workspace tab**: fully built — two-column layout:
    - **Left column**: Collections list (compact table — name, status badge, signal count, credits used) + activity timeline below (list of timestamped events: "Detection ran — 6 signals", "Investigation completed", etc.)
    - **Right column**: Credit breakdown chart (donut or bar showing credits by activity type) + limit usage progress bar (e.g., "142 / 500 credits used this month")

### Claude's Discretion

- Exact mock data values (chart data, user names, alert messages, credit amounts)
- Specific chart dimensions and spacing within each section
- How many bar charts appear side-by-side vs. stacked in the Workspace Activity section
- Exact wording of alert messages and threshold field labels for the 8 activity types
- Whether the funnel chart is implemented with a Recharts custom shape or a CSS-based approximation
- Activity timeline event styling (icons, colors, timestamp format)
- Placeholder content for Overview and API Keys tabs on user detail

</decisions>

<specifics>
## Specific Ideas

- The admin area feels like a natural extension of the same mockup — same dark Hex.tech system, same sidebar-based navigation pattern, just with admin nav items
- Activity Dashboard is the flagship screen of this phase — it should be visually impressive with multiple chart types visible on a single scrolling page
- The funnel chart is a unique chart type not seen in prior phases — it visually communicates Pulse → Explain → What-If adoption drop-off at a glance
- Alert cards should feel like real operational alerts (not banners) — data-dense, dismissable, with clear severity signaling
- The per-user Workspace tab is an extension of the admin's user management workflow — it should feel like a natural drill-down into one user's workspace activity from the user detail page

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `pulse-mockup/src/components/workspace/overview-stat-cards.tsx` — stat card component from Phase 42/43; reuse pattern for both dashboard KPI cards and user detail credit/session stats
- `pulse-mockup/src/components/workspace/activity-feed.tsx` — activity feed/timeline component (Phase 43); reuse directly for the per-user activity timeline in the Workspace tab
- `pulse-mockup/src/components/workspace/signal-card.tsx` — compact card pattern; reference for compact collection rows in the per-user Workspace tab
- `pulse-mockup/src/components/ui/tabs.tsx` — shadcn/ui tabs (already installed); use for user detail page tabs and any tabbed sections
- `pulse-mockup/src/components/ui/badge.tsx` — severity/status badges for alert cards and user detail header
- `pulse-mockup/src/components/ui/progress.tsx` — progress bar for limit usage display in Workspace tab
- `pulse-mockup/src/lib/mock-data.ts` — extend with admin mock data: users array, workspace activity stats, alert items, credit cost config

### Established Patterns

- Dark Hex.tech-inspired design system with shadcn/ui components — all admin screens follow this
- KPI stat cards row (Phase 42 `overview-stat-cards.tsx`) — used at top of dashboard and user detail
- Tabbed detail pages (Phase 43 collection detail) — same pattern for user detail tabs
- Recharts via shadcn/ui chart components — already the chart library of choice in the mockup
- Full-page routes for detail views — user detail follows the same pattern as collection detail

### Integration Points

- New `/admin` route section needs its own `layout.tsx` with admin sidebar — parallel to `/workspace/layout.tsx`
- Admin sidebar should NOT appear on the `/workspace/*` or `/chat` routes — handled by the separate layout
- `mock-data.ts` — add admin-specific mock data: `adminUsers`, `workspaceActivityStats`, `alertItems`, `creditCostConfig`
- Root `page.tsx` (or a nav link from the workspace sidebar) should include a visible link to `/admin` so reviewers can navigate there
- No changes to existing `/workspace/*` routes — admin is purely additive

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 46-admin-workspace-management*
*Context gathered: 2026-03-05*
