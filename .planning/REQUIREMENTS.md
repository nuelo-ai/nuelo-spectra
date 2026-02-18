# Requirements: Spectra

**Defined:** 2026-02-16
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.5 Requirements

Requirements for v0.5 Admin Portal. Each maps to roadmap phases.

### Admin Authentication

- [ ] **AUTH-01**: Admin accounts use `is_admin` flag on existing users table (separate from regular user signup flow)
- [ ] **AUTH-02**: Admin login page served by admin frontend (Tailscale-only in production)
- [ ] **AUTH-03**: Only users with `is_admin=True` can access admin API endpoints (403 for non-admins)
- [ ] **AUTH-04**: Admin uses email + password authentication (no self-signup for admin accounts)
- [ ] **AUTH-05**: First admin account seeded via CLI command (`python -m app.cli seed-admin`) or environment variable
- [ ] **AUTH-06**: Admin session timeout after inactivity (configurable, default 30 minutes)
- [ ] **AUTH-07**: All admin actions are audit-logged (admin_id, action, target, timestamp, details)

### Admin Dashboard

- [ ] **DASH-01**: Dashboard shows total registered users (active vs inactive count)
- [ ] **DASH-02**: Dashboard shows new user signups (today / this week / this month)
- [ ] **DASH-03**: Dashboard shows total chat sessions created (platform-wide)
- [ ] **DASH-04**: Dashboard shows total files uploaded (platform-wide)
- [ ] **DASH-05**: Dashboard shows total messages sent (platform-wide)
- [ ] **DASH-06**: Dashboard shows credit consumption summary (total used / total remaining across all users)
- [ ] **DASH-07**: Dashboard displays trend charts for signups over time and messages over time (Recharts)

### User Management

- [ ] **USER-01**: Admin can list all registered users with pagination
- [ ] **USER-02**: Admin can search users by email or name
- [ ] **USER-03**: Admin can filter users by active/inactive status, user class, and signup date
- [ ] **USER-04**: Admin can view user profile info (name, email, signup date, last login)
- [ ] **USER-05**: Admin can view user account status (active/inactive)
- [ ] **USER-06**: Admin can view user's current tier (user class)
- [ ] **USER-07**: Admin can view user's credit balance and usage history
- [ ] **USER-08**: Admin can view user's file count and chat session count
- [ ] **USER-09**: Admin can activate or deactivate a user account
- [ ] **USER-10**: Admin can trigger password reset for a user (sends reset email to user)
- [ ] **USER-11**: Admin can change a user's tier (user class)
- [ ] **USER-12**: Admin can adjust a user's credit balance (with reason/note)
- [ ] **USER-13**: Admin can delete a user account (with confirmation, proper cascade)

### Signup Control

- [ ] **SIGNUP-01**: Global toggle in platform settings: allow public signup (enabled/disabled)
- [ ] **SIGNUP-02**: When disabled, signup page shows "Registration is currently invite-only" message
- [ ] **SIGNUP-03**: When disabled, only users with a valid invite token can register
- [ ] **SIGNUP-04**: Toggle changes take effect immediately (no server restart, stored in platform_settings table)

### User Invitation

- [ ] **INVITE-01**: Admin can invite a user by entering their email address
- [ ] **INVITE-02**: System generates a unique, time-limited invite link (default 7 days, configurable)
- [ ] **INVITE-03**: Invite email sent via existing SMTP/email service with branded template
- [ ] **INVITE-04**: Invited user clicks link and sees registration form with pre-filled, locked email
- [ ] **INVITE-05**: Invited user completes registration (sets password, name) via separate invite signup endpoint
- [ ] **INVITE-06**: Admin can view list of pending invitations (email, date, expiry, status: pending/accepted/expired)
- [ ] **INVITE-07**: Admin can revoke or resend pending invitations
- [ ] **INVITE-08**: Invite links are single-use (invalidated after registration, token hashed in DB)

### User Class Management

- [ ] **TIER-01**: User classes defined in `user_classes.yaml` config file (free, standard, premium)
- [ ] **TIER-02**: Admin can edit credit amounts and display names per tier (stored as overrides in platform_settings)
- [ ] **TIER-03**: Adding/removing tiers requires config change + redeployment (not dynamic via admin UI)
- [ ] **TIER-04**: Users table has `user_class` field (enum: free/standard/premium, default: free)
- [ ] **TIER-05**: Admin can view all tiers with current credit allocations (YAML defaults + DB overrides)
- [ ] **TIER-06**: Admin can assign or change a user's tier manually
- [ ] **TIER-07**: Admin can view how many users are in each tier

### Credit Management

- [ ] **CREDIT-01**: Credits use NUMERIC(10,1) precision (one decimal place, e.g., 0.5, 1.0, 2.0, 3.0)
- [ ] **CREDIT-02**: Default credit cost per message is configurable by admin in platform settings
- [ ] **CREDIT-03**: System deducts credits atomically before agent execution (SELECT FOR UPDATE to prevent race conditions)
- [ ] **CREDIT-04**: When credits reach 0 (or below cost of next message), user cannot send messages ("out of credits" message)
- [ ] **CREDIT-05**: Credits reset automatically based on tier allocation (configurable: weekly or monthly via APScheduler)
- [ ] **CREDIT-06**: Admin can view remaining credits for each user (NUMERIC balance)
- [ ] **CREDIT-07**: Admin can manually add or deduct credits for a specific user (with reason/note)
- [ ] **CREDIT-08**: Admin can view credit usage history per user (date, cost, remaining balance, admin note)
- [ ] **CREDIT-09**: Dashboard widget shows credit distribution across user classes
- [ ] **CREDIT-10**: Dashboard shows list of users with low credits (<10% of tier allocation remaining)
- [ ] **CREDIT-11**: Admin can bulk-adjust credits by user class (e.g., grant 50 extra credits to all Free-tier users)
- [ ] **CREDIT-12**: Admin can trigger manual credit reset for individual users or by class
- [ ] **CREDIT-13**: Credit reset is idempotent (tracks last_reset_at, prevents double-reset)

### Platform Settings

- [ ] **SETTINGS-01**: Centralized settings page for global platform configuration
- [ ] **SETTINGS-02**: Signup toggle setting (allow_public_signup: true/false)
- [ ] **SETTINGS-03**: Default user class for new signups setting
- [ ] **SETTINGS-04**: Invite link expiry duration setting (days)
- [ ] **SETTINGS-05**: Credit reset policy setting (manual / weekly auto-reset / monthly auto-reset)
- [ ] **SETTINGS-06**: Credit amount overrides per user class (overrides YAML config defaults)
- [ ] **SETTINGS-07**: Default credit cost per message setting (NUMERIC, e.g., 1.0)
- [ ] **SETTINGS-08**: Settings persisted in `platform_settings` table (key-value with JSON values, 30s TTL cache)

### Split-Horizon Architecture

- [ ] **ARCH-01**: `SPECTRA_MODE` env var controls router mounting (public/admin/dev)
- [ ] **ARCH-02**: Public mode mounts only user-facing routers (auth, chat, files, sessions, search, health)
- [ ] **ARCH-03**: Admin mode mounts only admin routers (admin auth, users, settings, invitations, credits, dashboard, health)
- [ ] **ARCH-04**: Dev mode mounts all routers (public + admin) for local development
- [ ] **ARCH-05**: Admin routers live under `app/routers/admin/` directory, prefixed `/api/admin/...`
- [ ] **ARCH-06**: Separate `admin-frontend/` Next.js application (not a route in existing frontend)
- [ ] **ARCH-07**: Admin frontend uses same stack as public frontend (Next.js, TanStack Query, Zustand, shadcn/ui, Recharts for charts)
- [ ] **ARCH-08**: CORS configuration is mode-aware (public origins in public mode, admin origin in admin mode, both in dev)
- [ ] **ARCH-09**: Local dev runs 3 processes (backend:8000 dev mode, frontend:3000, admin:3001)
- [ ] **ARCH-10**: Defense in depth: network isolation (Tailscale) + authentication + role enforcement (`CurrentAdmin` dependency) + audit logging

### Database Changes

- [ ] **DB-01**: `is_admin` boolean field added to users table (default: false, backfill existing users)
- [ ] **DB-02**: `user_class` enum field added to users table (free/standard/premium, default: free, backfill existing users)
- [ ] **DB-03**: `platform_settings` table created (key VARCHAR PK, value TEXT JSON-encoded, updated_at, updated_by)
- [ ] **DB-04**: `user_credits` table created (user_id FK, balance NUMERIC(10,1), last_reset_at, created_at)
- [ ] **DB-05**: `credit_transactions` table created (id, user_id, amount NUMERIC(10,1), type enum, reason, admin_id nullable, balance_after, created_at)
- [ ] **DB-06**: `invitations` table created (id, email, token_hash, status enum, expires_at, invited_by, accepted_at, created_at)
- [ ] **DB-07**: `admin_audit_log` table created (id, admin_id, action, target_type, target_id, details JSON, ip_address, created_at)
- [ ] **DB-08**: All tables managed via single Alembic migration with three-step pattern for NOT NULL columns (add nullable, backfill, alter NOT NULL)
- [ ] **DB-09**: Existing users backfilled with credit records (user_credits row with tier-default balance) in migration

## v0.6+ Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Monetization & Billing

- **BILLING-01**: Stripe payment integration for self-service tier upgrades
- **BILLING-02**: Per-model credit costs (Opus = 3.0, Sonnet = 1.0, Haiku = 0.5)
- **BILLING-03**: User self-service credit purchase
- **BILLING-04**: Subscription lifecycle management (upgrade, downgrade, cancellation webhooks)

### Advanced Admin

- **ADM-01**: Multi-admin role hierarchy (super admin, billing admin, support admin)
- **ADM-02**: Audit log CSV/SIEM export
- **ADM-03**: Email notification for credit depletion
- **ADM-04**: Invitation with pre-assigned tier

### Deployment

- **DEPLOY-01**: Docker Compose deployment package (Dokploy)
- **DEPLOY-02**: Production Tailscale configuration for admin services

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Stripe/payment integration | Entire milestone of work (webhooks, subscription lifecycle, tax, PCI). Build tier + credit plumbing now, add payments later. |
| Per-model credit costs | User-facing model selection not yet built. Flat cost sufficient for v0.5. |
| Dynamic tier creation via admin UI | Over-engineering for 3-5 tiers. YAML config is version-controlled, reviewed in PRs. |
| Self-service tier upgrade | Without payment integration, self-service upgrade is either free or requires manual admin approval. |
| Real-time credit balance WebSocket | Low-frequency changes (one per message). Frontend can re-fetch after each message. |
| Multi-admin role hierarchy | Binary admin/non-admin check sufficient for 1-3 admins. Add RBAC when team grows. |
| User self-service credit purchase | Requires Stripe. Monetization is a separate milestone. |
| Email notifications for credit depletion | In-app "out of credits" message sufficient. Email adds volume and opt-out complexity. |
| Invitation with pre-assigned tier | All invites start at default tier. Admin changes tier after registration. |
| Audit log export/SIEM integration | Enterprise feature. Direct DB query for now. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 26 | Pending |
| AUTH-02 | Phase 26 | Pending |
| AUTH-03 | Phase 26 | Pending |
| AUTH-04 | Phase 26 | Pending |
| AUTH-05 | Phase 26 | Pending |
| AUTH-06 | Phase 26 | Pending |
| AUTH-07 | Phase 26 | Pending |
| DASH-01 | Phase 31 | Pending |
| DASH-02 | Phase 31 | Pending |
| DASH-03 | Phase 31 | Pending |
| DASH-04 | Phase 31 | Pending |
| DASH-05 | Phase 31 | Pending |
| DASH-06 | Phase 31 | Pending |
| DASH-07 | Phase 31 | Pending |
| USER-01 | Phase 29 | Pending |
| USER-02 | Phase 29 | Pending |
| USER-03 | Phase 29 | Pending |
| USER-04 | Phase 29 | Pending |
| USER-05 | Phase 29 | Pending |
| USER-06 | Phase 29 | Pending |
| USER-07 | Phase 29 | Pending |
| USER-08 | Phase 29 | Pending |
| USER-09 | Phase 29 | Pending |
| USER-10 | Phase 29 | Pending |
| USER-11 | Phase 29 | Pending |
| USER-12 | Phase 29 | Pending |
| USER-13 | Phase 29 | Pending |
| SIGNUP-01 | Phase 28 | Pending |
| SIGNUP-02 | Phase 28 | Pending |
| SIGNUP-03 | Phase 28 | Pending |
| SIGNUP-04 | Phase 28 | Pending |
| INVITE-01 | Phase 30 | Pending |
| INVITE-02 | Phase 30 | Pending |
| INVITE-03 | Phase 30 | Pending |
| INVITE-04 | Phase 30 + Phase 32 | Pending |
| INVITE-05 | Phase 30 + Phase 32 | Pending |
| INVITE-06 | Phase 30 | Pending |
| INVITE-07 | Phase 30 | Pending |
| INVITE-08 | Phase 30 | Pending |
| TIER-01 | Phase 28 | Pending |
| TIER-02 | Phase 28 | Pending |
| TIER-03 | Phase 28 | Pending |
| TIER-04 | Phase 28 | Pending |
| TIER-05 | Phase 28 | Pending |
| TIER-06 | Phase 28 | Pending |
| TIER-07 | Phase 28 | Pending |
| CREDIT-01 | Phase 27 | Pending |
| CREDIT-02 | Phase 27 | Pending |
| CREDIT-03 | Phase 27 | Pending |
| CREDIT-04 | Phase 27 | Pending |
| CREDIT-05 | Phase 27 | Pending |
| CREDIT-06 | Phase 27 | Pending |
| CREDIT-07 | Phase 27 | Pending |
| CREDIT-08 | Phase 27 | Pending |
| CREDIT-09 | Phase 27 | Pending |
| CREDIT-10 | Phase 27 | Pending |
| CREDIT-11 | Phase 27 | Pending |
| CREDIT-12 | Phase 27 | Pending |
| CREDIT-13 | Phase 27 | Pending |
| SETTINGS-01 | Phase 28 | Pending |
| SETTINGS-02 | Phase 28 | Pending |
| SETTINGS-03 | Phase 28 | Pending |
| SETTINGS-04 | Phase 28 | Pending |
| SETTINGS-05 | Phase 28 + Phase 32 | Pending |
| SETTINGS-06 | Phase 28 | Pending |
| SETTINGS-07 | Phase 28 | Pending |
| SETTINGS-08 | Phase 28 | Pending |
| ARCH-01 | Phase 26 | Pending |
| ARCH-02 | Phase 26 | Pending |
| ARCH-03 | Phase 26 | Pending |
| ARCH-04 | Phase 26 | Pending |
| ARCH-05 | Phase 26 | Pending |
| ARCH-06 | Phase 31 | Pending |
| ARCH-07 | Phase 31 | Pending |
| ARCH-08 | Phase 26 | Pending |
| ARCH-09 | Phase 31 | Pending |
| ARCH-10 | Phase 26 | Pending |
| DB-01 | Phase 26 | Pending |
| DB-02 | Phase 26 | Pending |
| DB-03 | Phase 26 | Pending |
| DB-04 | Phase 26 | Pending |
| DB-05 | Phase 26 | Pending |
| DB-06 | Phase 26 | Pending |
| DB-07 | Phase 26 | Pending |
| DB-08 | Phase 26 | Pending |
| DB-09 | Phase 26 | Pending |

**Coverage:**
- v0.5 requirements: 86 total
- Mapped to phases: 86
- Unmapped: 0

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after roadmap creation*
