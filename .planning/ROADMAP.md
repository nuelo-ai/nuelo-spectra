# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** — Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** — Phases 7-13 (shipped 2026-02-10)
- ✅ **v0.3 Multi-file Conversation Support** — Phases 14-19 (shipped 2026-02-12)
- ✅ **v0.4 Data Visualization** — Phases 20-25 (shipped 2026-02-15)
- **v0.5 Admin Portal** — Phases 26-31 (in progress)

## Phases

<details>
<summary>✅ v0.1 Beta MVP (Phases 1-6) — SHIPPED 2026-02-06</summary>

- [x] Phase 1: Foundation Setup (6/6 plans) — completed 2026-02-06
- [x] Phase 2: File Upload & AI Profiling (6/6 plans) — completed 2026-02-06
- [x] Phase 3: Multi-File Management (4/4 plans) — completed 2026-02-06
- [x] Phase 4: AI Agent System & Code Generation (8/8 plans) — completed 2026-02-06
- [x] Phase 5: Secure Code Execution & E2B (6/6 plans) — completed 2026-02-06
- [x] Phase 6: Interactive Data Cards & Frontend Polish (6/6 plans) — completed 2026-02-06

</details>

<details>
<summary>✅ v0.2 Intelligence & Integration (Phases 7-13) — SHIPPED 2026-02-10</summary>

- [x] Phase 7: Multi-LLM Provider Infrastructure (5/5 plans) — completed 2026-02-09
- [x] Phase 8: Session Memory with PostgreSQL Checkpointing (2/2 plans) — completed 2026-02-08
- [x] Phase 9: Manager Agent with Intelligent Query Routing (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Smart Query Suggestions (2/2 plans) — completed 2026-02-08
- [x] Phase 11: Web Search Tool Integration (3/3 plans) — completed 2026-02-09
- [x] Phase 12: Production Email Infrastructure (2/2 plans) — completed 2026-02-09
- [x] Phase 13: Migrate Web Search (Tavily) (2/2 plans) — completed 2026-02-09

</details>

<details>
<summary>✅ v0.3 Multi-file Conversation Support (Phases 14-19) — SHIPPED 2026-02-12</summary>

- [x] Phase 14: Database Foundation & Migration (4/4 plans) — completed 2026-02-11
- [x] Phase 15: Agent System Enhancement (3/3 plans) — completed 2026-02-11
- [x] Phase 16: Frontend Restructure (3/3 plans) — completed 2026-02-11
- [x] Phase 17: File Management & Linking (3/3 plans) — completed 2026-02-11
- [x] Phase 18: Integration & Polish (3/3 plans) — completed 2026-02-11
- [x] Phase 19: v0.3 Gap Closure (7/7 plans) — completed 2026-02-12

</details>

<details>
<summary>✅ v0.4 Data Visualization (Phases 20-25) — SHIPPED 2026-02-15</summary>

- [x] Phase 20: Infrastructure & Pipeline (2/2 plans) — completed 2026-02-13
- [x] Phase 21: Visualization Agent (1/1 plan) — completed 2026-02-13
- [x] Phase 22: Graph Integration & Chart Intelligence (2/2 plans) — completed 2026-02-13
- [x] Phase 23: Frontend Chart Rendering (2/2 plans) — completed 2026-02-13
- [x] Phase 24: Chart Types & Export (3/3 plans) — completed 2026-02-13
- [x] Phase 25: Theme Integration (1/1 plan) — completed 2026-02-14

</details>

### v0.5 Admin Portal (In Progress)

**Milestone Goal:** Build an internal admin portal for platform management -- user management, credit system, invitation flow, signup control, and platform settings -- deployed as a network-isolated service via Tailscale VPN.

- [x] **Phase 26: Foundation** - Database schema, split-horizon architecture, admin authentication, and audit logging (completed 2026-02-16)
- [x] **Phase 27: Credit System** - Atomic credit deduction, balance tracking, transaction history, and scheduled resets (completed 2026-02-16)
- [ ] **Phase 28: Platform Config** - Platform settings, tier management, and signup control toggle
- [ ] **Phase 29: User Management** - Admin user list, search, filter, and all user account operations
- [ ] **Phase 30: Invitation System** - Email invites with time-limited single-use tokens and invite-only registration
- [ ] **Phase 31: Dashboard & Admin Frontend** - Admin Next.js app with dashboard metrics, trend charts, and all admin UI pages

## Phase Details

### Phase 26: Foundation
**Goal**: Admin infrastructure exists -- database tables, mode-gated routing, admin authentication, and audit logging are operational
**Depends on**: Nothing (first phase of v0.5)
**Requirements**: DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, DB-07, DB-08, DB-09, ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-08, ARCH-10, AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07
**Success Criteria** (what must be TRUE):
  1. Running `alembic upgrade head` creates all 5 new tables and adds `is_admin` + `user_class` fields to users table, with existing users backfilled (is_admin=false, user_class=free, credit records created)
  2. Starting the backend with `SPECTRA_MODE=public` exposes zero `/api/admin/` routes; starting with `SPECTRA_MODE=admin` exposes only admin routes; `SPECTRA_MODE=dev` exposes both
  3. An admin user seeded via `python -m app.cli seed-admin` can log in through the admin auth endpoint and receive a JWT; a regular user hitting admin endpoints gets 403
  4. Admin session expires after configured inactivity timeout (default 30 minutes), requiring re-login
  5. Every admin API call creates a row in `admin_audit_log` with admin_id, action name, target, timestamp, and details
**Plans**: 3 plans

Plans:
- [x] 26-01-PLAN.md -- Database models and Alembic migration (5 new tables, user fields, backfill)
- [x] 26-02-PLAN.md -- SPECTRA_MODE config and conditional router mounting with mode-aware CORS
- [x] 26-03-PLAN.md -- Admin auth (JWT, dependency, login, CLI seed-admin, lockout, audit logging, token reissue)

### Phase 27: Credit System
**Goal**: Users have credit balances that are atomically deducted per message, with admin controls for individual adjustment, manual reset, and scheduled auto-resets
**Depends on**: Phase 26
**Requirements**: CREDIT-01, CREDIT-02, CREDIT-03, CREDIT-04, CREDIT-05, CREDIT-06, CREDIT-07, CREDIT-08, CREDIT-09, CREDIT-10, CREDIT-12, CREDIT-13
**Success Criteria** (what must be TRUE):
  1. Sending a chat message deducts the configured credit cost (NUMERIC precision) from the user's balance atomically -- two concurrent requests from the same user cannot overdraw the balance below zero
  2. A user with zero credits (or less than the cost of one message) sees an "out of credits" message and cannot send messages
  3. Admin can view any user's credit balance and full transaction history (date, cost, remaining balance, admin note) via admin API endpoints
  4. Admin can manually add/deduct credits for individual users and can trigger manual credit reset for a user (idempotent, tracks last_reset_at)
  5. Scheduled auto-reset (weekly or monthly, configurable per class) resets user credits to their tier allocation without double-resetting
**Plans**: 4 plans

Plans:
- [x] 27-01-PLAN.md -- Core credit service: user_classes.yaml, UserClassService, CreditService, credit schemas
- [x] 27-02-PLAN.md -- Admin credit endpoints and public balance endpoint
- [x] 27-03-PLAN.md -- Chat flow credit integration and registration credit initialization
- [x] 27-04-PLAN.md -- APScheduler setup and rolling credit reset job

### Phase 28: Platform Config
**Goal**: Admins can configure platform behavior at runtime -- tier credit allocations, signup mode, invite expiry, credit policies -- without redeployment
**Depends on**: Phase 26
**Requirements**: SETTINGS-01, SETTINGS-02, SETTINGS-03, SETTINGS-04, SETTINGS-05, SETTINGS-06, SETTINGS-07, SETTINGS-08, TIER-01, TIER-02, TIER-03, TIER-04, TIER-05, TIER-06, TIER-07, SIGNUP-01, SIGNUP-02, SIGNUP-03, SIGNUP-04
**Success Criteria** (what must be TRUE):
  1. Admin can view and edit all platform settings (signup toggle, default tier, invite expiry, credit policy, cost per message, tier credit overrides) from a centralized settings API, persisted in `platform_settings` table with 30-second TTL cache
  2. Toggling `allow_public_signup` to disabled takes effect immediately -- the public signup endpoint rejects new registrations with an "invite-only" message, without requiring server restart
  3. When signup is invite-only, only users with a valid invite token can complete registration through the public signup flow
  4. User tiers are defined in `user_classes.yaml` (free/standard/premium) with admin-editable credit overrides per tier stored in platform_settings; admin can view tier summary with user counts and assign/change a user's tier
**Plans**: TBD

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD

### Phase 29: User Management
**Goal**: Admins can find, inspect, and manage any user account on the platform through admin API endpoints
**Depends on**: Phase 26, Phase 27 (credit views), Phase 28 (tier assignment)
**Requirements**: USER-01, USER-02, USER-03, USER-04, USER-05, USER-06, USER-07, USER-08, USER-09, USER-10, USER-11, USER-12, USER-13
**Success Criteria** (what must be TRUE):
  1. Admin can list all users with pagination, search by email or name, and filter by active/inactive status, user class, and signup date
  2. Admin can view a user's full profile: name, email, signup date, last login, active/inactive status, tier, credit balance, usage history, file count, and chat session count
  3. Admin can activate/deactivate a user account, trigger a password reset email, change their tier, adjust their credit balance (with reason), and delete the account (with proper cascade)
**Plans**: TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD

### Phase 30: Invitation System
**Goal**: Admins can invite users via email with time-limited single-use links, and invited users can register even when public signup is disabled
**Depends on**: Phase 26, Phase 28 (signup control toggle)
**Requirements**: INVITE-01, INVITE-02, INVITE-03, INVITE-04, INVITE-05, INVITE-06, INVITE-07, INVITE-08
**Success Criteria** (what must be TRUE):
  1. Admin enters an email address and the system generates a unique time-limited invite link (default 7 days, configurable), sends a branded email via existing SMTP service, and stores a SHA-256 hashed token in the invitations table
  2. Invited user clicks the link, sees a registration form with pre-filled locked email, sets their password and name, and completes registration -- the invite token is invalidated (single-use)
  3. Admin can view all invitations (pending/accepted/expired) and can revoke or resend pending invitations
**Plans**: TBD

Plans:
- [ ] 30-01: TBD
- [ ] 30-02: TBD

### Phase 31: Dashboard & Admin Frontend
**Goal**: A separate admin Next.js application provides a visual interface for all admin operations, including a dashboard with platform metrics and trend charts
**Depends on**: Phase 26, Phase 27, Phase 28, Phase 29, Phase 30 (all backend APIs)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07, ARCH-06, ARCH-07, ARCH-09
**Success Criteria** (what must be TRUE):
  1. Admin dashboard displays real-time platform metrics: total users (active vs inactive), new signups (today/week/month), total chat sessions, total files uploaded, total messages sent, and credit consumption summary (total used / total remaining)
  2. Dashboard renders Recharts trend charts for signups over time and messages over time, plus credit distribution by tier and low-credit user list
  3. The `admin-frontend/` Next.js application provides pages for login, dashboard, user management (list + detail), platform settings, invitations, credit management, and audit log viewing -- using same stack as public frontend (TanStack Query, Zustand, shadcn/ui, Recharts)
  4. Local development runs 3 processes (backend:8000 dev mode, frontend:3000, admin:3001) with mode-aware CORS allowing both frontends to communicate with the backend
**Plans**: TBD

Plans:
- [ ] 31-01: TBD
- [ ] 31-02: TBD
- [ ] 31-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 26 -> 27 -> 28 -> 29 -> 30 -> 31
Note: Phase 28 can start after Phase 26 (does not depend on Phase 27). Phase 30 depends on Phase 28 (signup toggle).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation Setup | v0.1 | 6/6 | Complete | 2026-02-06 |
| 2. File Upload & AI Profiling | v0.1 | 6/6 | Complete | 2026-02-06 |
| 3. Multi-File Management | v0.1 | 4/4 | Complete | 2026-02-06 |
| 4. AI Agent System & Code Generation | v0.1 | 8/8 | Complete | 2026-02-06 |
| 5. Secure Code Execution & E2B | v0.1 | 6/6 | Complete | 2026-02-06 |
| 6. Interactive Data Cards | v0.1 | 6/6 | Complete | 2026-02-06 |
| 7. Multi-LLM Infrastructure | v0.2 | 5/5 | Complete | 2026-02-09 |
| 8. Session Memory | v0.2 | 2/2 | Complete | 2026-02-08 |
| 9. Manager Agent Routing | v0.2 | 3/3 | Complete | 2026-02-08 |
| 10. Smart Query Suggestions | v0.2 | 2/2 | Complete | 2026-02-08 |
| 11. Web Search Integration | v0.2 | 3/3 | Complete | 2026-02-09 |
| 12. Production Email | v0.2 | 2/2 | Complete | 2026-02-09 |
| 13. Migrate Web Search (Tavily) | v0.2 | 2/2 | Complete | 2026-02-09 |
| 14. Database Foundation & Migration | v0.3 | 4/4 | Complete | 2026-02-11 |
| 15. Agent System Enhancement | v0.3 | 3/3 | Complete | 2026-02-11 |
| 16. Frontend Restructure | v0.3 | 3/3 | Complete | 2026-02-11 |
| 17. File Management & Linking | v0.3 | 3/3 | Complete | 2026-02-11 |
| 18. Integration & Polish | v0.3 | 3/3 | Complete | 2026-02-11 |
| 19. v0.3 Gap Closure | v0.3 | 7/7 | Complete | 2026-02-12 |
| 20. Infrastructure & Pipeline | v0.4 | 2/2 | Complete | 2026-02-13 |
| 21. Visualization Agent | v0.4 | 1/1 | Complete | 2026-02-13 |
| 22. Graph Integration & Chart Intelligence | v0.4 | 2/2 | Complete | 2026-02-13 |
| 23. Frontend Chart Rendering | v0.4 | 2/2 | Complete | 2026-02-13 |
| 24. Chart Types & Export | v0.4 | 3/3 | Complete | 2026-02-13 |
| 25. Theme Integration | v0.4 | 1/1 | Complete | 2026-02-14 |
| 26. Foundation | v0.5 | 3/3 | Complete | 2026-02-16 |
| 27. Credit System | v0.5 | 4/4 | Complete | 2026-02-16 |
| 28. Platform Config | v0.5 | 0/TBD | Not started | - |
| 29. User Management | v0.5 | 0/TBD | Not started | - |
| 30. Invitation System | v0.5 | 0/TBD | Not started | - |
| 31. Dashboard & Admin Frontend | v0.5 | 0/TBD | Not started | - |
