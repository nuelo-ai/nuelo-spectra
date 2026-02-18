# Feature Research: Admin Portal, Credit System, Invitation Flow (v0.5)

**Domain:** SaaS admin portal with user management, credit-based usage control, invitation system
**Researched:** 2026-02-16
**Confidence:** HIGH
**Supersedes:** Previous FEATURES.md (v0.4 Data Visualization features, 2026-02-12)

---

## Executive Summary

Spectra v0.5 adds the operational backbone needed to transition from a developer prototype to a commercially viable SaaS product. The feature set spans four distinct domains: admin authentication and dashboard, user lifecycle management, credit-based usage metering, and controlled signup via invitations. These are well-understood SaaS patterns with established best practices -- the risk is not in "can we build this?" but in "do we build too much or too little?"

The requirements document is already well-scoped. The key insight from research is that the credit system is the most technically complex feature (concurrency, atomicity, audit trails) while appearing deceptively simple on the surface. The invitation system and signup toggle are straightforward but must be wired carefully into the existing auth flow without breaking it. The admin dashboard is high-visibility but low-risk -- it is read-only queries against existing data.

**Scope alignment:** The requirements deliberately defer Stripe integration, per-model credit costs, and self-service tier upgrades. This is the correct call. The v0.5 scope builds the internal plumbing (credit ledger, tier assignment, admin controls) that future monetization will plug into. Attempting to add payment processing in the same milestone would double the complexity.

---

## Table Stakes

Features that any SaaS admin portal must have. Missing these makes the admin experience frustrating or dangerous.

| Feature | Why Expected | Complexity | Dependencies on Existing |
|---------|--------------|------------|--------------------------|
| **Admin login with role enforcement** | Every admin portal requires authentication. Without `is_admin` check on every endpoint, any authenticated user could access admin functions. This is security-critical, not optional. | LOW | Extends existing `User` model with `is_admin` boolean. Existing JWT auth infrastructure reused. New `AdminCurrentUser` dependency that checks the flag. |
| **CLI seed for first admin** | Chicken-and-egg problem: you need an admin to create admins, but you need to create the first admin somehow. CLI seeding is the standard pattern (Django's `createsuperuser`, Rails seeds). | LOW | New CLI command using existing database connection. Creates user record with `is_admin=True`. No frontend dependency. |
| **Session timeout for admin** | Admin sessions with indefinite lifetime are a security liability. 30-minute inactivity timeout is industry standard for internal tools. NIST SP 800-63B recommends 15-30 minutes for privileged sessions. | LOW | Configurable JWT expiry for admin tokens (separate from user tokens) or frontend-side inactivity timer that clears the session. |
| **User list with search and filter** | The first thing any admin does is find a specific user. Without search/filter, admin managing 100+ users is unusable. Every SaaS admin panel (Stripe Dashboard, Auth0, Firebase) has this. | MEDIUM | New admin router querying existing `users` table. Paginated endpoint with `?search=email&status=active&tier=free` query params. Needs index on `email` (already exists) and new `user_class` column. |
| **User activate/deactivate** | Ability to disable a user without deleting their data is fundamental. Deactivation should immediately prevent login (existing `is_active` check in auth already handles this). | LOW | Existing `is_active` field on `User` model. Admin endpoint flips the boolean. Existing auth middleware already checks `is_active` on token refresh. |
| **Admin-triggered password reset** | Users lock themselves out. Admin must be able to trigger a reset email without knowing or setting the password directly. Standard in every user management system. | LOW | Reuses existing password reset email infrastructure. Admin endpoint creates a reset token and triggers the same email flow. No new email template needed. |
| **User deletion with confirmation** | GDPR and general data hygiene require the ability to delete users. Must cascade-delete files, sessions, messages, and credit records. Two-step confirmation prevents accidents. | MEDIUM | Existing `cascade="all, delete-orphan"` on User relationships handles files, messages, sessions. New credit tables must also cascade. Admin frontend should require typed confirmation (e.g., "type user email to confirm"). |
| **Credit balance per user** | The core of usage control. Each user has a float credit balance that decreases with each message. When balance hits zero, user cannot send messages. This is the fundamental gate for commercial operation. | HIGH | New `user_credits` table with `user_id`, `balance` (float), `last_reset`. Credit deduction integrated into existing chat message creation flow. Must be atomic -- deduct BEFORE sending to LLM, not after. |
| **Credit deduction on message send** | Each message costs credits (configurable float, default 1.0). Deduction must happen synchronously, before the AI processes the query. If credits insufficient, return error immediately -- do not waste LLM API costs. | HIGH | Modifies existing `chat` router/service. Before calling agent pipeline, check balance >= cost, deduct atomically, then proceed. Race condition risk if user sends multiple messages simultaneously -- needs database-level locking or SELECT FOR UPDATE. |
| **"Out of credits" blocking** | When credits reach zero, user sees a clear message explaining why they cannot send messages and what to do (wait for reset, contact admin, upgrade tier). Silently failing or showing generic errors is unacceptable. | LOW | Frontend check: if credit balance < message cost, disable send button and show message. Backend enforcement: reject message endpoint with 402/403 and descriptive error. Both are needed (defense in depth). |
| **Credit transaction history** | Every credit movement (deduction, admin adjustment, reset, bonus) must be recorded as an immutable append-only log. This is both an audit requirement and essential for debugging "where did my credits go?" support tickets. | MEDIUM | New `credit_transactions` table: `id`, `user_id`, `amount` (positive=grant, negative=deduction), `type` (enum: message, admin_adjustment, reset, bonus), `reason` (text), `balance_after`, `created_at`, `admin_id` (nullable). Append-only -- never update or delete rows. |
| **Signup control toggle** | Global on/off for public registration. When off, only invited users can register. This is essential for beta launches, enterprise deployments, and controlling growth. Must take effect immediately without restart. | MEDIUM | New `platform_settings` table with key-value pairs. Signup endpoint checks `allow_public_signup` setting on every request. Setting change writes to DB, no cache needed for this low-frequency check. |
| **Email invitation with unique link** | Admin enters email, system generates a time-limited, single-use token and sends an invite email. Invited user clicks link, lands on registration form with email pre-filled and locked. Standard SaaS invitation pattern. | MEDIUM | New `invitations` table: `id`, `email`, `token_hash`, `status` (pending/accepted/expired/revoked), `expires_at`, `created_at`, `invited_by` (admin_id). Reuses existing email service for sending. New registration endpoint that accepts invite token. |
| **Invite link expiry and single-use** | Invite links that never expire or can be reused are security holes. 7-day default expiry is standard. Link must be invalidated after successful registration. | LOW | Token validation checks `expires_at` and `status=pending`. On successful registration, update status to `accepted`. Cron job or on-check cleanup marks expired invites. |
| **User class/tier assignment** | Each user belongs to a tier (free/standard/premium) that determines their credit allocation. Admin can change a user's tier. This is the foundation for commercial differentiation. | LOW | New `user_class` enum column on `users` table (default: `free`). Admin endpoint to update. Tier definitions live in `user_classes.yaml` config file. |
| **Audit logging of admin actions** | Every admin action (user deactivation, credit adjustment, tier change, invite sent) must be logged with who, what, when, and target. Essential for accountability, debugging, and compliance. | MEDIUM | New `admin_audit_log` table: `id`, `admin_id`, `action` (string, e.g., `user.deactivate`), `target_type`, `target_id`, `details` (JSONB), `ip_address`, `created_at`. Log at service layer, not router layer, to ensure consistency. |
| **Platform settings page** | Centralized admin page for global configuration: signup toggle, default tier, invite expiry, credit reset policy, credit cost per message. Without this, admins must edit config files and restart servers. | MEDIUM | `platform_settings` key-value table. Admin frontend form that reads/writes settings. Backend caches settings with short TTL or reads on every request (low frequency, acceptable). |

---

## Differentiators

Features that go beyond the minimum. These make the admin experience feel polished and professional, but Spectra can launch v0.5 without them if time is constrained.

| Feature | Value Proposition | Complexity | Dependencies on Existing |
|---------|-------------------|------------|--------------------------|
| **Admin dashboard with trend charts** | At-a-glance platform health: user growth, message volume, credit consumption over time. Most internal admin tools start as CRUD-only and add dashboards later. Having it from day one signals maturity. | MEDIUM | Aggregation queries against existing `users`, `chat_sessions`, `chat_messages`, `files` tables plus new `credit_transactions`. Charts rendered with the same Plotly infrastructure from v0.4 (or simpler Chart.js in admin frontend since no agent-generated charts needed). |
| **Credit distribution overview** | Dashboard widget showing credit usage breakdown by tier: how many free/standard/premium users, average credit consumption per tier, users near depletion. Helps admin understand if tier allocations are right-sized. | MEDIUM | Aggregation query on `user_credits` joined with `users.user_class`. Low-credit threshold configurable in platform settings. |
| **Bulk credit adjustments by tier** | "Grant 50 extra credits to all Free-tier users." Useful for promotions, compensation after outages, or seasonal adjustments. Doing this one user at a time is tedious. | MEDIUM | Batch UPDATE on `user_credits` WHERE user's class matches. Must create individual `credit_transactions` rows for each affected user (not a single bulk entry) for audit trail integrity. Could be slow for thousands of users -- consider async task. |
| **Pending invitation management** | Admin sees all pending invites with status (pending/accepted/expired), can revoke or resend. Provides visibility into the invitation funnel and prevents lost invites. | LOW | Simple CRUD on `invitations` table. Revoke = update status to `revoked`. Resend = create new token, update expiry, re-send email. |
| **User detail page with activity summary** | Clicking a user shows comprehensive view: profile, tier, credit balance, credit history, file count, session count, last login. Prevents admin from needing to query multiple pages. | MEDIUM | Aggregation endpoint that joins `users`, `user_credits`, `credit_transactions`, `files`, `chat_sessions`. Single API call, one page render. |
| **Per-tier credit editing from admin UI** | Admin can adjust credit allocations per tier (e.g., change Free from 10 to 15 credits/week) without editing YAML files or redeploying. Overrides stored in `platform_settings`, falling back to YAML defaults. | LOW | Platform settings with keys like `tier.free.credits_per_week`. Service reads setting first, falls back to YAML. Simple form in admin frontend. |
| **Credit reset policy configuration** | Toggle between manual-only, weekly auto-reset, and monthly auto-reset. Reset schedule configurable per tier or globally. Auto-reset implemented via scheduled task (cron or APScheduler). | MEDIUM | Scheduled task that runs periodically, checks reset policy, resets credits for eligible users based on their tier allocation. Must log reset transactions. APScheduler or system cron. |
| **Low-credit user alerts** | Admin dashboard highlights users below 10% of their tier allocation. Proactive visibility prevents support tickets from users who suddenly cannot use the platform. | LOW | Query: SELECT users WHERE credits.balance < (tier.allocation * 0.1). Display as list or alert badge on dashboard. |
| **Invite-only registration messaging** | When public signup is disabled, the signup page shows a clear, branded message: "Registration is currently invite-only. Contact your administrator for access." Not a generic 403. | LOW | Frontend checks signup toggle via public API endpoint. Conditionally renders invite-only message instead of signup form. |

---

## Anti-Features

Features to explicitly NOT build in v0.5. These are commonly requested, seem reasonable, but would add significant scope or create problems.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Stripe/payment integration** | "Let users self-serve upgrade their tier and pay." | Payment processing is an entire milestone of work: webhook handling, subscription lifecycle, failed payment recovery, invoice generation, refund logic, tax calculation, PCI compliance considerations. Mixing it with the admin portal foundation doubles the scope and risk. The requirements correctly defer this. | Build tier assignment and credit allocation now. Add `stripe_price_id` field to tier config as a placeholder. Payment integration becomes a clean follow-on milestone that plugs into the existing tier system. |
| **Per-model credit costs** | "Different LLM models should cost different credits (Opus = 3.0, Haiku = 0.5)." | Spectra v0.5 does not yet have user-facing model selection. Building variable credit costs before the feature that uses them is premature engineering. It also complicates the credit deduction path (need to know which model at deduction time). | Implement flat `default_credit_cost` per message. When per-model selection ships in a future milestone, extend the deduction logic to read model-specific costs from config. The credit ledger already supports variable amounts per transaction. |
| **Dynamic tier creation via admin UI** | "Let admins create new tiers (e.g., 'Enterprise', 'Trial') through the portal." | Dynamic tiers require a database-backed tier definition system with validation, dependent data migration when tiers change, and complex UI for tier attribute management. It is over-engineering for a product that will have 3-5 tiers for the foreseeable future. | Static tiers in YAML config. Adding a tier is a config change + migration + deploy. This is appropriate for a decision that happens once per quarter, not daily. |
| **Self-service tier upgrade (user-facing)** | "Users should be able to upgrade their own tier." | Without payment integration, a self-service upgrade is either free (which defeats the purpose) or requires manual admin approval (which is just a support ticket with extra UI). Self-service upgrades only make sense with integrated payments. | Admin manually changes user tier. Future Stripe milestone adds self-service with payment. |
| **Real-time credit balance WebSocket** | "Show credit balance updating in real-time as user sends messages." | WebSocket infrastructure adds operational complexity. Credit balance changes are low-frequency (one deduction per message, not hundreds per second). The frontend can simply re-fetch balance after each message completes. | Poll credit balance on page load and after each message response. Include updated balance in the chat message response payload. |
| **Multi-admin role hierarchy** | "Super admin, billing admin, support admin with different permissions." | RBAC with multiple admin roles is a significant infrastructure investment (permission matrix, role management UI, per-endpoint permission checks). Spectra's admin portal will have 1-3 admins for the foreseeable future. | Single `is_admin` boolean. All admins have full access. When the team grows to 5+ admins, add granular roles as a separate feature. |
| **User self-service credit purchase** | "Let users buy additional credits when they run out." | Requires payment integration (Stripe), credit package definition, purchase flow UI, receipt generation, and refund handling. This is a monetization feature, not an admin portal feature. | Admin manually adjusts credits for users who request more. Future monetization milestone adds self-service purchase. |
| **Email notification for credit depletion** | "Email users when their credits are low or depleted." | Adds email sending volume, potential spam complaints, and configuration complexity (what threshold triggers email? how often? can user opt out?). For v0.5, the in-app "out of credits" message is sufficient. | In-app banner when credits are below 20%. Admin can see low-credit users in dashboard. Email notifications can be added in a later UX polish milestone. |
| **Invitation with pre-assigned tier** | "Let admin assign a tier when inviting a user." | Adds complexity to the invite flow and the registration handler. The default tier (free) is appropriate for most invites. Admin can change tier immediately after user registers. | All invited users start at the default tier (configurable in platform settings). Admin changes tier after registration if needed. |
| **Admin audit log export/SIEM integration** | "Export audit logs to CSV or integrate with Splunk/Datadog." | Enterprise feature that adds export infrastructure, API endpoints, and potentially streaming integration. Not needed for a platform with 1-3 admins. | Audit logs viewable in admin portal with search/filter. Export can be done via direct database query for now. Add API export when enterprise customers demand it. |

---

## Feature Dependencies

```
Platform Settings Table (foundation)
    |
    +---> Signup Toggle (reads from settings)
    |         |
    |         +---> Invite-Only Registration (depends on toggle being OFF)
    |                    |
    |                    +---> Invitation System (creates invites when toggle OFF)
    |                              |
    |                              +---> Invite Registration Endpoint
    |                                        (new /auth/signup-with-invite)
    |
    +---> Credit Config (default cost, reset policy stored in settings)
    |         |
    |         +---> Credit System (uses config for costs and reset)
    |
    +---> Default Tier Setting (default user_class for new signups)

User Model Changes (is_admin, user_class)
    |
    +---> Admin Auth (requires is_admin field)
    |         |
    |         +---> Admin JWT/Session (separate token handling)
    |                    |
    |                    +---> All Admin Endpoints (protected by admin auth)
    |
    +---> User Class/Tier (requires user_class field)
              |
              +---> Credit Allocation (tier determines credit amount)
              |         |
              |         +---> Credit Balance (per-user, seeded from tier)
              |         |         |
              |         |         +---> Credit Deduction (on message send)
              |         |         |         |
              |         |         |         +---> Out-of-Credits Blocking
              |         |         |
              |         |         +---> Credit Transaction Log (records every movement)
              |         |         |
              |         |         +---> Auto-Reset (scheduled task resets based on tier)
              |         |
              |         +---> Tier Change (admin action, recalculates credits)
              |
              +---> User Management CRUD (needs tier for display/filter)

Audit Logging (cross-cutting concern)
    |
    +---> Wraps ALL admin actions (user mgmt, credit adj, invites, settings)
```

### Critical Path (must be sequential)

1. **Database migrations** -- Add `is_admin`, `user_class` to users table. Create `platform_settings`, `user_credits`, `credit_transactions`, `invitations`, `admin_audit_log` tables.
2. **Platform settings service** -- Key-value read/write against `platform_settings` table. All other features depend on reading config from this table.
3. **Admin auth** -- Admin login, JWT with admin claim, `AdminCurrentUser` dependency. All admin endpoints depend on this.
4. **User management CRUD** -- List, view, activate/deactivate, delete. Foundation for all admin user operations.
5. **Credit system core** -- Balance tracking, deduction on message, transaction logging. This is the highest-risk feature.
6. **Invitation system** -- Create invite, send email, invite-based registration. Depends on signup toggle from platform settings.
7. **Admin dashboard** -- Read-only aggregation queries. Can be built last since it depends on data from all other features.

### Can Be Parallelized

- **Admin frontend scaffolding** (independent of backend, can start immediately)
- **Audit logging middleware** (can be added to endpoints after they exist)
- **Signup toggle + invite-only messaging** (frontend work independent of invitation backend)
- **Tier configuration UI** (reads/writes platform_settings, independent of credit system)

### Dependency Notes

- **Credit deduction requires credit balance:** Cannot deduct if no balance record exists. User credit records must be created at signup (with tier-default allocation).
- **Invitation system requires email service:** Existing SMTP/email infrastructure from password reset. Must handle failure gracefully (invite created but email failed to send).
- **Tier change requires credit recalculation:** When admin changes a user's tier, the credit balance should NOT be immediately overwritten. The new allocation applies at next reset. Current balance remains unchanged. This prevents confusion ("I had 45 credits, admin upgraded me, now I have 100 -- or do I have 145?").
- **Signup toggle requires both backend and frontend changes:** Backend rejects signup requests when disabled. Frontend hides signup form. Both must be implemented -- frontend-only is bypassable.

---

## Feature Categories and Complexity Budget

### Category 1: Admin Authentication and Foundation (LOW-MEDIUM risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| `is_admin` field on User model | LOW | LOW -- simple migration |
| CLI admin seed command | LOW | LOW -- one-time script |
| Admin login endpoint | LOW | LOW -- reuses existing auth |
| Admin JWT with role claim | LOW | MEDIUM -- must not break existing user JWT flow |
| Session timeout (admin) | LOW | LOW -- configurable token expiry |
| `AdminCurrentUser` dependency | LOW | LOW -- extends existing pattern |
| SPECTRA_MODE router mounting | MEDIUM | MEDIUM -- must not break existing routes |

### Category 2: User Management (LOW-MEDIUM risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| User list with pagination | LOW | LOW -- standard query |
| Search by email/name | LOW | LOW -- ILIKE query |
| Filter by status/tier/date | LOW | LOW -- WHERE clauses |
| User detail view (aggregated) | MEDIUM | LOW -- joins across tables |
| Activate/deactivate | LOW | LOW -- boolean flip |
| Admin-triggered password reset | LOW | LOW -- reuses existing flow |
| Change user tier | LOW | LOW -- enum update |
| Adjust credit balance | MEDIUM | MEDIUM -- must be atomic with transaction log |
| Delete user (cascade) | MEDIUM | MEDIUM -- must cascade correctly to new tables |

### Category 3: Credit System (HIGH risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| `user_credits` table and model | LOW | LOW -- schema design |
| Credit balance on user creation | LOW | LOW -- default from tier config |
| Credit deduction on message send | HIGH | HIGH -- atomicity, race conditions, must not break chat flow |
| Transaction logging (append-only ledger) | MEDIUM | LOW -- standard insert pattern |
| Out-of-credits blocking (backend) | LOW | MEDIUM -- must handle edge case of exact-zero balance |
| Out-of-credits UI (frontend) | LOW | LOW -- conditional rendering |
| Admin manual credit adjustment | MEDIUM | MEDIUM -- must log with reason, must be atomic |
| Bulk credit adjustment by tier | MEDIUM | MEDIUM -- batch operation, individual transaction rows |
| Auto-reset scheduled task | MEDIUM | MEDIUM -- scheduled job reliability, timezone handling |
| Credit overview dashboard widget | MEDIUM | LOW -- read-only aggregation |

### Category 4: Signup Control and Invitations (MEDIUM risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| `platform_settings` key-value table | LOW | LOW -- simple schema |
| Signup toggle (backend enforcement) | LOW | LOW -- check setting before signup |
| Signup toggle (frontend messaging) | LOW | LOW -- conditional render |
| Invitation creation (admin) | MEDIUM | LOW -- token generation, DB insert |
| Invite email sending | LOW | LOW -- reuses email service |
| Invite-based registration endpoint | MEDIUM | MEDIUM -- new auth flow alongside existing signup |
| Invite link validation (expiry, single-use) | LOW | LOW -- token checks |
| Pending invitation list (admin) | LOW | LOW -- CRUD query |
| Revoke/resend invitations | LOW | LOW -- status update, new token |

### Category 5: Admin Dashboard (LOW risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| Total users (active/inactive) | LOW | LOW -- COUNT query |
| New signups over time | LOW | LOW -- GROUP BY date |
| Total sessions/files/messages | LOW | LOW -- COUNT queries |
| Credit consumption summary | MEDIUM | LOW -- aggregation on credit_transactions |
| Trend charts | MEDIUM | LOW -- frontend charting, data already available |
| Low-credit user alerts | LOW | LOW -- threshold query |

### Category 6: Audit Logging (MEDIUM risk)

| Feature | Complexity | Risk |
|---------|-----------|------|
| `admin_audit_log` table | LOW | LOW -- schema design |
| Audit logging service | MEDIUM | LOW -- centralized log function |
| Logging on all admin actions | MEDIUM | MEDIUM -- must not be forgotten on any endpoint |
| Audit log viewer (admin UI) | MEDIUM | LOW -- paginated list with filters |

---

## MVP Recommendation

### Must Have (v0.5 Core)

Prioritize in this order based on dependency chain:

1. **Database migrations + platform settings** -- Foundation for everything. Add `is_admin`, `user_class` to users. Create all new tables. Seed `platform_settings` with defaults.

2. **Admin auth + SPECTRA_MODE** -- Admin login, admin JWT, mode-based router mounting. Without this, no admin functionality is accessible.

3. **User management CRUD** -- List/search/filter users, view details, activate/deactivate, reset password, change tier, delete. This is the most immediately useful admin capability.

4. **Credit system core** -- Credit balance per user, deduction on message send, out-of-credits blocking, transaction logging. This is the commercial gate.

5. **Signup toggle + invitation system** -- Platform settings toggle, invite creation/sending, invite-based registration. Enables controlled growth.

6. **Audit logging** -- Wrap all admin actions. Must be in v0.5, but can be added to endpoints after they are built.

7. **Admin dashboard** -- Metrics and trend charts. Highest visibility but lowest urgency (the platform functions without it).

### Defer to Later

- **Bulk credit adjustments** -- Convenience feature. Admin can adjust individual users for now. Add when user base exceeds 100.
- **Credit auto-reset** -- Can start with manual-only reset. Auto-reset (weekly/monthly) adds scheduled task complexity. Implement in v0.5.x once manual flow is validated.
- **Trend charts on dashboard** -- Start with numeric KPIs only. Charts are polish. Add after core dashboard metrics work.
- **Admin audit log viewer with advanced filtering** -- Start with simple chronological list. Advanced search/filter is a UX enhancement.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Admin auth + CLI seed | HIGH | LOW | P1 |
| SPECTRA_MODE router mounting | HIGH | MEDIUM | P1 |
| User list/search/filter | HIGH | LOW | P1 |
| User activate/deactivate | HIGH | LOW | P1 |
| User delete (cascade) | HIGH | MEDIUM | P1 |
| Admin password reset | MEDIUM | LOW | P1 |
| Change user tier | HIGH | LOW | P1 |
| Credit balance per user | HIGH | MEDIUM | P1 |
| Credit deduction on message | HIGH | HIGH | P1 |
| Out-of-credits blocking | HIGH | LOW | P1 |
| Credit transaction log | HIGH | MEDIUM | P1 |
| Manual credit adjustment | HIGH | MEDIUM | P1 |
| Signup toggle | HIGH | LOW | P1 |
| Invitation system | HIGH | MEDIUM | P1 |
| Invite-based registration | HIGH | MEDIUM | P1 |
| Platform settings page | HIGH | MEDIUM | P1 |
| Audit logging | HIGH | MEDIUM | P1 |
| Admin dashboard (numeric KPIs) | MEDIUM | LOW | P1 |
| Dashboard trend charts | MEDIUM | MEDIUM | P2 |
| Bulk credit adjustments | MEDIUM | MEDIUM | P2 |
| Credit auto-reset (scheduled) | MEDIUM | MEDIUM | P2 |
| Per-tier credit editing (admin UI) | MEDIUM | LOW | P2 |
| Low-credit user alerts | LOW | LOW | P2 |
| Pending invitation management | MEDIUM | LOW | P2 |
| User detail page (aggregated) | MEDIUM | MEDIUM | P2 |
| Audit log viewer (advanced filter) | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for v0.5 launch -- the admin portal is non-functional without these
- P2: Should have, add during v0.5 development when core is stable
- P3: Nice to have, can ship in v0.5.x follow-up

---

## Competitor Feature Analysis (Admin/Credit Patterns in AI SaaS)

| Feature | ChatGPT (OpenAI) | Claude (Anthropic) | Julius AI | Spectra v0.5 Target |
|---------|-------------------|---------------------|-----------|---------------------|
| Admin portal | Yes (Org admin) | Yes (Org admin) | Basic team mgmt | Yes (dedicated portal) |
| User management | List, add, remove | List, roles, remove | List, invite | Full CRUD + tier mgmt |
| Credit/usage system | Token-based billing | Token-based billing | Message credits | Message credit with tiers |
| Tier system | Plus/Pro/Team/Enterprise | Free/Pro/Team/Enterprise | Free/Pro/Enterprise | Free/Standard/Premium |
| Invite system | Email invite to org | Email invite to org | Email invite | Email invite + toggle |
| Signup control | Org-only join | Org-only join | Public | Toggle public/invite-only |
| Audit logging | Admin audit log | Admin audit log | None visible | Full audit logging |
| Credit visibility | Usage dashboard | Usage dashboard | Credit counter | Balance + transaction history |
| Network isolation | SSO/SCIM | SSO/SCIM | None | Tailscale VPN (unique) |

**Key advantages for Spectra v0.5:**
- **Split-horizon deployment** (Tailscale VPN for admin) is a genuine security differentiator over competitors who rely solely on RBAC
- **Credit transparency** (full transaction history) exceeds most competitors who show only current balance
- **Signup toggle** (public/invite-only switch) is more flexible than competitors who are either always-public or always-org-only

---

## Detailed Feature Specifications

### Credit Deduction: The Highest-Risk Feature

The credit deduction path is the most technically critical feature in v0.5 because it touches the existing chat flow (the core product) and must be bulletproof.

**Deduction flow:**
1. User sends message via existing chat endpoint
2. BEFORE agent pipeline starts: check credit balance >= message cost
3. If insufficient: return 402 with "insufficient credits" error
4. If sufficient: atomically deduct credits (SELECT FOR UPDATE on user_credits, UPDATE balance, INSERT credit_transaction)
5. Proceed with existing agent pipeline
6. If agent pipeline fails: do NOT refund credits (the LLM API was still called and billed)

**Why deduct before, not after:**
- If you deduct after, a user can send 10 concurrent requests and only pay for the last one
- "Deduct first, no refund on failure" is the standard pattern (used by OpenAI, Anthropic, all AI SaaS)
- The LLM API call costs money regardless of whether the response is useful

**Race condition mitigation:**
```sql
-- Atomic deduction with row-level lock
BEGIN;
SELECT balance FROM user_credits WHERE user_id = $1 FOR UPDATE;
-- Check balance >= cost in application code
UPDATE user_credits SET balance = balance - $cost WHERE user_id = $1;
INSERT INTO credit_transactions (user_id, amount, type, balance_after, ...) VALUES (...);
COMMIT;
```

**Complexity:** HIGH -- this modifies the critical path of the core product.

### Invitation Registration: Parallel Auth Flow

The invitation system creates a second registration path alongside the existing public signup.

**Two registration endpoints:**
1. `POST /auth/signup` -- existing public signup (blocked when signup toggle is OFF)
2. `POST /auth/signup-with-invite` -- new invite-based signup (always available when valid token provided)

**Why two endpoints, not one:**
- Keeps existing signup untouched (no regression risk)
- Invite validation logic is separate from general signup validation
- Clear API contract: invite signup requires `invite_token` field

**Invite registration flow:**
1. Admin creates invite for `user@example.com`
2. System generates cryptographic token, hashes and stores it, sends email with link
3. User clicks link: `https://app.spectra.io/register?invite=<token>`
4. Frontend pre-fills and locks email field, shows registration form
5. User submits: `POST /auth/signup-with-invite` with `{invite_token, email, password, first_name, last_name}`
6. Backend validates: token exists, not expired, not used, email matches
7. Creates user account with default tier, marks invite as accepted
8. Returns JWT tokens (auto-login, same as existing signup)

**Complexity:** MEDIUM -- the hardest part is ensuring the existing signup flow is not broken.

### Platform Settings: Keep It Simple

**Database schema:**
```sql
CREATE TABLE platform_settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON-encoded for complex values
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID REFERENCES users(id)  -- which admin changed it
);
```

**Initial settings to seed:**
| Key | Default Value | Type | Description |
|-----|--------------|------|-------------|
| `allow_public_signup` | `true` | boolean | Toggle public registration |
| `default_user_class` | `"free"` | string | Tier for new signups |
| `invite_expiry_days` | `7` | integer | Days before invite links expire |
| `credit_reset_policy` | `"manual"` | string | manual/weekly/monthly |
| `default_credit_cost` | `1.0` | float | Credits per message |

**Why key-value, not structured table:**
- Flexible: new settings can be added without migration
- Simple: one table, one service, universal read/write
- Values are JSON-encoded for type safety at application layer
- Matches the requirements spec exactly

**Complexity:** LOW -- the simplest feature in v0.5, but foundational for many others.

---

## Sources

### High Confidence (Official patterns, established SaaS practices)
- [EnterpriseReady Audit Logging Guide](https://www.enterpriseready.io/features/audit-log/) -- Definitive guide on what to log, how to store, retention policy
- [Martin Fowler: Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) -- Authoritative reference for feature flag patterns
- [Frontegg User Management Guide](https://frontegg.com/guides/user-management) -- Comprehensive SaaS user management patterns

### Medium Confidence (Multiple sources agree, verified patterns)
- [Stigg: Building AI Credits](https://www.stigg.io/blog-posts/weve-built-ai-credits-and-it-was-harder-than-we-expected) -- Real-world AI credit system challenges: idempotency, race conditions, ledger design
- [ColorWhistle SaaS Credits Guide](https://colorwhistle.com/saas-credits-system-guide/) -- Credit ledger architecture, FIFO expiry, wallet management patterns
- [FlexPrice: Credit System Implementation](https://flexprice.io/blog/how-to-implement-credit-system-in-subscription-model) -- Subscription credit allocation and reset patterns
- [Zluri: SaaS User Management](https://www.zluri.com/blog/saas-user-management) -- User lifecycle management best practices
- [DataDab: Invite-Only SaaS](https://www.datadab.com/blog/invite-only-saas-growth/) -- Why invite-only works for growth control
- [Userpilot: Invited User Onboarding](https://userpilot.com/blog/onboard-invited-users-saas/) -- Best practices for invited user registration flows
- [Chris Dermody: Audit Logging Best Practices](https://chrisdermody.com/best-practices-for-audit-logging-in-a-saas-business-app/) -- Practical audit logging for SaaS applications

### Low Confidence (Single source, verify during implementation)
- Credit deduction with `SELECT FOR UPDATE` atomicity -- Standard PostgreSQL pattern, but verify with SQLAlchemy async session behavior
- APScheduler for auto-reset scheduled tasks -- Verify compatibility with FastAPI async lifecycle

---
*Feature research for: Admin Portal, Credit System, Invitation Flow (v0.5)*
*Researched: 2026-02-16*
