# Phase 56: Trial Expiration & Conversion Pressure - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

New users get a time-limited trial that blocks access after expiration, creating conversion pressure to select a paid plan. Covers: trial middleware enforcement across all auth paths (web, API, MCP), trial banner UI on dashboard, blocking overlay on expiration, and trial-specific credit restrictions. Does NOT include Stripe integration (Phase 57), plan selection UI with payment (Phase 58), or admin billing tools (Phase 59).

</domain>

<decisions>
## Implementation Decisions

### Trial banner design
- Sticky banner at the top of the page, above all content (pushes content down)
- Shows both days remaining AND credit balance, plus a "Choose Plan" CTA button
- Appears on ALL authenticated pages (dashboard, workspace, settings)
- Dismissible per session — user can close it, returns on next page load/session
- Amber urgency at 3 days remaining or 10 credits remaining — stays dismissible even when urgent (no lock)
- Only shown to `free_trial` tier users

### Blocking overlay UX
- Full-page semi-transparent overlay on top of the dashboard when trial expires
- User can see their data behind it but cannot interact
- Overlay shows "Your trial has expired" message with two actions: "View Plans" and "Log Out"
- "View Plans" links to a placeholder `/settings/plan` page (simple tier cards with "Coming soon" — Phase 58 replaces with real Stripe checkout)
- Overlay triggered by `trial_expires_at` date only — zero credits alone does NOT trigger overlay (banner warns about low credits instead)
- Expired trial users CAN still access `/settings` pages (profile, account, plan placeholder) — overlay only blocks core features (chat, workspace)

### Backend enforcement
- Trial expiration check added directly in `get_current_user` and `get_authenticated_user` dependencies — single enforcement point covering web, API, and MCP (MCP uses httpx loopback to API)
- HTTP 402 Payment Required response with `trial_expired` code and metadata:
  ```json
  {
    "detail": "Trial expired",
    "code": "trial_expired",
    "trial_expires_at": "2026-03-25T00:00:00Z",
    "days_overdue": 3
  }
  ```
- Exempt endpoints: Claude's discretion to determine minimal set needed for overlay + logout + settings access to work
- Frontend global 402 handling: Claude's discretion on best approach (axios interceptor vs per-query) based on existing frontend patterns

### Trial credit restrictions
- Backend-only enforcement — no frontend changes this phase (top-up UI doesn't exist until Phase 58)
- Trial users attempting top-up get HTTP 403 with specific error:
  ```json
  {
    "detail": "Credit top-ups not available during free trial",
    "code": "trial_topup_blocked"
  }
  ```
- When Phase 58 builds the top-up UI, it will check tier and hide the option for trial users

### Claude's Discretion
- Exact set of exempt API routes for trial enforcement (minimal set for overlay + logout + settings to work)
- Frontend 402 handling approach (axios interceptor vs React Query error boundary vs other pattern)
- Placeholder plan page design details (tier card layout, copy, styling)
- Trial banner component styling details (colors, spacing, icon)
- Loading skeleton for trial state check

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Trial Requirements
- `.planning/REQUIREMENTS.md` — TRIAL-01 through TRIAL-07 (all Phase 56 requirements)

### Phase 55 Context (prior decisions)
- `.planning/phases/55-tier-restructure-data-foundation/55-CONTEXT.md` — Trial: 100 credits, 7 days; `trial_expires_at` on User model; `free_trial` tier in YAML; dual-balance credit system

### Auth & Dependencies
- `backend/app/dependencies.py` — `get_current_user`, `get_authenticated_user`, `get_current_admin_user`, `require_workspace_access` dependencies (trial check goes here)
- `backend/app/mcp_server.py` — MCP auth via httpx loopback (inherits API enforcement)

### User Model & Registration
- `backend/app/models/user.py` — User model with `trial_expires_at`, `user_class` fields
- `backend/app/services/auth.py` — Registration flow sets `free_trial` and `trial_expires_at`

### Frontend Layouts
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard layout (banner + overlay injection point)
- `frontend/src/app/(workspace)/layout.tsx` — Workspace layout (banner + overlay injection point)
- `frontend/src/components/workspace/detection-progress-banner.tsx` — Existing banner pattern reference

### Roadmap
- `.planning/ROADMAP.md` — Phase 56 success criteria, dependency chain

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DetectionProgressBanner` (`frontend/src/components/workspace/detection-progress-banner.tsx`): Banner pattern with rounded card, border, icon + text — adapt for trial banner
- `get_current_user` / `get_authenticated_user` (`backend/app/dependencies.py`): Auth dependencies where trial check will be injected
- `useAuth` hook (`frontend/src/hooks/useAuth.tsx`): Auth state hook — can be extended to expose trial state
- `get_class_config()` (`backend/app/services/user_class.py`): YAML tier config reader — already knows about `free_trial` tier
- `platform_settings` service: Already supports `trial_duration_days` setting

### Established Patterns
- `OAuth2PasswordBearer` + dependency injection for all auth checks
- MCP auth via httpx loopback to REST API — no separate enforcement needed
- Client-side auth redirect in layout components (`useAuth` + `router.push`)
- `SidebarProvider` wrapping layout with sidebar + main content
- Tailwind CSS + shadcn/ui component patterns

### Integration Points
- `backend/app/dependencies.py` — Add trial check after `is_active` check in both `get_current_user` and `get_authenticated_user`
- `frontend/src/app/(dashboard)/layout.tsx` — Inject trial banner above `<main>` content area
- `frontend/src/app/(workspace)/layout.tsx` — Same banner injection
- `frontend/src/app/(auth)/layout.tsx` — No changes (auth pages not affected)
- `frontend/src/app/settings/` — New placeholder `/settings/plan` page

</code_context>

<specifics>
## Specific Ideas

- Owner chose 402 Payment Required over 403 for expired trials — semantically indicates payment is needed
- Overlay shows dashboard content behind semi-transparent backdrop — user sees what they're missing
- Settings pages remain accessible for expired trial users (they need to reach the plan page)
- Banner is informational, not blocking — conversion pressure escalates gradually: banner (normal) -> banner (amber) -> overlay (expired)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 56-trial-expiration-conversion-pressure*
*Context gathered: 2026-03-18*
