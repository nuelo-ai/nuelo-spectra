# Phase 39: API Key Management UI + Deployment Mode - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

API key management accessible from the public frontend Settings page (new "API Keys" tab), admin can manage keys for any user from User Management, and `SPECTRA_MODE=api` backend is deployable as a standalone 5th Dokploy service with its own subdomain. Phase 38 provided the backend infrastructure (model, service, endpoints, basic frontend hook); this phase delivers the polished UI and deployment configuration.

</domain>

<decisions>
## Implementation Decisions

### Key management UX
- Create key flow: user enters a required name → modal dialog displays the full key once with copy button and "won't be shown again" warning → user must explicitly dismiss
- Key list shows per row: name, key prefix (sk-...xxxx), created date, last used timestamp, total credit usage
- All users see last used and credit usage for their own keys (not admin-only)
- Revoke flow: click revoke → confirmation dialog showing key name → confirm to revoke
- Key name is required when creating (e.g., "Production server", "CI pipeline")

### Admin key management
- Admin key management lives inside the user detail panel in User Management (not a separate tab)
- Admin clicks a user → sees their details → API Keys section within that view
- Admin sees all keys for a user: active and revoked, with visual status (revoked keys dimmed/struck-through with revocation date)
- Keys created by admin show a "Created by admin" badge/tag for transparency
- Admin can create and revoke keys on behalf of any user
- Admin uses the same confirmation dialog flow when revoking (no streamlined bypass)

### Settings page layout
- New "API Keys" tab added as the 5th tab (last position): Overview | Credit | Activity | Session | API Keys
- API Keys tab uses the same card/section style as existing tabs (consistent spacing, typography, containers)
- API Keys tab is visible to all users (no gating by role or feature flag)

### Deployment configuration
- API service uses subdomain pattern: api.spectra.domain (not path-based)
- Dedicated GET /api/v1/health endpoint returning 200 + JSON with service status and DB connectivity
- In SPECTRA_MODE=api, only mount /api/v1/ routes + health check — no static files, no WebSocket, no frontend routes, no non-API backend routes
- Dokploy Application settings documented (not a separate docker-compose file) — matches how existing 4 services are configured

### Claude's Discretion
- Exact modal/dialog component implementation (reuse existing UI library patterns)
- Loading states and error handling within the API Keys tab
- Health check response schema details
- Exact styling of "Created by admin" badge
- How revoked keys are visually distinguished (dimmed, struck-through, or grayed)

</decisions>

<specifics>
## Specific Ideas

- Current Settings page already has 4 tabs (Overview, Credit, Activity, Session) — API Keys appends as 5th
- Admin key table should include Last Used and Credit Usage columns alongside the standard fields
- User confirmed they want the same data richness (last used, credit usage) for regular users viewing their own keys

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 39-api-key-management-ui-deployment-mode*
*Context gathered: 2026-02-24*
