# Phase 31: Dashboard & Admin Frontend - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

A separate admin Next.js application (`admin-frontend/`) providing visual interface for all admin operations built in Phases 26-30. Includes login page, dashboard with metrics and trend charts, user management (list + detail), platform settings, invitations, credit management, and audit log viewing. Uses same stack as public frontend (TanStack Query, Zustand, shadcn/ui, Recharts). Local dev runs 3 processes (backend:8000 dev mode, frontend:3000, admin:3001).

</domain>

<decisions>
## Implementation Decisions

### Dashboard layout
- Hero section: row of 6 metric cards at the top (total users, active today, new signups, total sessions, messages sent, credit balance)
- Below cards: 2 trend charts side-by-side (signups over time on left, messages over time on right), equal width
- Below charts: credit section with credit distribution by tier (pie/bar chart) + low-credit users table
- Dashboard is a single-page overview — admin sees the full platform health at a glance

### Navigation & pages
- Fixed left sidebar with icons + labels, collapsible to icon-only
- Pages grouped into sections:
  - **Overview:** Dashboard
  - **People:** Users, Invitations
  - **Platform:** Credits, Settings, Audit Log
- User detail view: separate page at `/users/:id` (not slide-over panel)
- User detail page uses tabbed sections: Overview | Credits | Activity | Sessions

### Data tables & actions
- Comfortable row spacing (medium density) with avatar + name in first column
- Row-level actions via three-dot dropdown menu at end of each row
- Bulk operations supported: checkbox column on left, bulk action bar appears at top when rows selected (activate, deactivate, tier change, credit adjust, delete)
- Search bar at top with filter dropdowns (status, tier, date range) shown as removable chips when active

### Confirmation patterns
- Destructive actions (delete user, bulk delete): 6-character alphanumeric challenge code with paste disabled on confirmation input (per Phase 29 context)
- Less severe actions (deactivate, revoke invite): standard confirm modal

### Visual style
- Theme: follows public Spectra frontend pattern — system preference as default, overridable with user preference (dark/light toggle)
- Visual mood: professional & structured (clear section dividers, color badges, status indicators — Stripe dashboard style)
- Distinct admin look: different accent color/styling from public frontend to visually separate admin from consumer app
- **MANDATORY: Use `/frontend-design` skill for all layout and design implementation** — distinctive, production-grade design quality required

### Claude's Discretion
- Specific accent color palette for admin portal
- Exact sidebar width and collapse breakpoint
- Chart time range selectors (7d/30d/90d)
- Loading states and skeleton patterns
- Toast notification style for action confirmations
- Responsive behavior (if any — may be desktop-only)
- Audit log page layout and filtering

</decisions>

<specifics>
## Specific Ideas

- Dashboard should feel like Stripe's dashboard — professional, structured, information-dense but organized
- Same theme system as public frontend (system preference default + user override) to maintain consistency in architecture
- Admin portal must feel like a separate internal tool, not a section of the public app
- `/frontend-design` skill MUST be used for all design work — this is a firm requirement from the user, not optional

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 31-dashboard-admin-frontend*
*Context gathered: 2026-02-16*
