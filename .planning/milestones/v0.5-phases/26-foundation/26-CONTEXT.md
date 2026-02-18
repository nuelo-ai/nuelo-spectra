# Phase 26: Foundation - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Database schema (5 new tables, is_admin + user_class on users), split-horizon architecture (SPECTRA_MODE env var for public/admin/dev), admin authentication (JWT with admin claim), and audit logging. This is the infrastructure layer all other v0.5 phases build on.

</domain>

<decisions>
## Implementation Decisions

### Admin bootstrap
- Seed admin via CLI: `python -m app.cli seed-admin` reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`
- Auto-creates a new user account if email doesn't exist (works on empty DB), sets `is_admin=true`
- Idempotent: if admin already exists, re-running resets password from current `.env` value (doubles as password recovery for seeded admin)
- Additional admins created via admin API — first admin promotes existing users through an admin endpoint
- Non-seeded admins recover passwords through existing email reset flow (Phase 12 SMTP)

### Audit logging
- Mutations only — log creates, updates, deletes, promotions, credit adjustments. Skip read-only GET requests
- Details field captures before + after values: `{before: {credits: 100}, after: {credits: 50}, reason: "manual deduction"}`
- Capture admin's IP address alongside admin_id per audit entry
- Retention: Claude's discretion (admin actions are low-volume, likely keep forever)

### Mode behavior
- Default `SPECTRA_MODE` is `dev` when env var is not set (exposes both public + admin routes for local development)
- Production: two separate backend instances — public backend on main network, admin backend on Tailscale VPN
- Routes not available in current mode return 404 (not 403) — hides existence of admin routes from public backend
- Log a WARNING when requests hit routes outside current mode (detect misconfiguration or scanning)

### Auth responses
- Reuse existing JWT system with added `is_admin` claim — one auth system, admin check is a middleware layer
- 30-minute inactivity timeout with sliding window — each admin API call resets the timer
- In dev mode, non-admin user hitting admin endpoint gets 403 Forbidden (clear error for development)
- In public mode, admin routes simply don't exist (404, routes aren't registered)
- Lockout policy: Claude's discretion (admin backend is VPN-isolated, brute force risk is low)

### Claude's Discretion
- Audit log retention policy (keep forever vs auto-purge — low volume makes forever reasonable)
- Lockout after failed admin login attempts (Tailscale isolation reduces brute force risk)
- Exact JWT claim structure and middleware implementation
- Database migration strategy for backfilling existing users

</decisions>

<specifics>
## Specific Ideas

- Admin password recovery via re-running `seed-admin` with new `.env` password — simple, no extra infrastructure
- Two-instance production deployment: public backend on main network, admin backend behind Tailscale VPN
- 404 for wrong-mode routes is a deliberate security choice — don't reveal admin endpoint existence

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-foundation*
*Context gathered: 2026-02-16*
