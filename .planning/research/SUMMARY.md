# Project Research Summary

**Project:** Spectra v0.5 Admin Portal
**Domain:** SaaS admin portal with user management, credit-based usage control, invitation-only signup, and split-horizon deployment
**Researched:** 2026-02-16
**Confidence:** HIGH

## Executive Summary

Spectra v0.5 adds the operational backbone for commercial SaaS operation: an admin portal with user management, credit-based usage metering, controlled signup via invitations, and split-horizon network deployment. The research reveals this is not exotic territory -- these are well-established SaaS patterns with proven solutions. The challenge is integration, not innovation.

The recommended approach builds on the existing FastAPI + PostgreSQL + Next.js stack with minimal new dependencies: APScheduler for credit reset scheduling (backend) and Recharts for admin dashboard charts (frontend). The split-horizon deployment is pure configuration (SPECTRA_MODE env var) with no new infrastructure beyond what Tailscale already provides. Most of the work is new models, new services, and new routers that follow existing patterns.

The key risk is the credit deduction system. It appears deceptively simple but introduces three critical pitfalls: (1) race conditions from concurrent message requests overdrawing credit balances, (2) float precision drift accumulating over hundreds of transactions, and (3) deducting credits before the expensive agent pipeline runs but after the user commits to the action. Each has a known solution (SELECT FOR UPDATE, NUMERIC columns, reserve-then-confirm pattern), but all must be implemented correctly from day one -- retrofitting credit atomicity after launch is nearly impossible without database downtime. The invitation system and admin portal are straightforward by comparison, reusing existing auth and email infrastructure.

## Key Findings

### Recommended Stack

Almost everything needed already exists in the stack or comes from Python stdlib. The backend adds exactly one new dependency: APScheduler for scheduled credit resets. The admin frontend is a separate Next.js 16 app reusing the same libraries as the public frontend (TanStack Query, Zustand, shadcn/ui) plus Recharts for dashboard trend charts.

**Core technologies:**
- **APScheduler (>=3.11.0)**: Periodic credit reset scheduler (weekly/monthly auto-allocation) -- lightweight, integrates with FastAPI's lifespan, no external dependencies. Chosen over Celery (too heavy), cron (not portable), and fastapi-utils (too simple).
- **Recharts (^3.7.0)**: Admin dashboard charts (signups over time, credit usage trends) -- shadcn/ui's official charting library, 45KB vs Plotly's 1MB. Matches existing design system.
- **Existing stack**: FastAPI, PostgreSQL + SQLAlchemy + Alembic, JWT auth (PyJWT), SMTP email (aiosmtplib + Jinja2), Next.js 16, React 19, TanStack Query, Zustand, Radix UI -- all unchanged.
- **No new infrastructure**: Tailscale VPN (already in use), Docker Compose, PostgreSQL (same database, 5 new tables).

**Critical decision points:**
- **NUMERIC(10,2) not FLOAT for credit values** -- float precision drift causes balance confusion after hundreds of transactions.
- **Separate admin-frontend/ app, not a route** -- deployment isolation, bundle isolation, independent iteration.
- **SPECTRA_MODE=public|admin|dev** -- same codebase, conditional router mounting, mode-aware CORS.

### Expected Features

The requirements are well-scoped and appropriately defer Stripe integration, per-model credit costs, and self-service tier upgrades. v0.5 builds the internal plumbing (credit ledger, tier assignment, admin controls) that future monetization will plug into.

**Must have (table stakes):**
- Admin auth with CLI seed for first admin (chicken-and-egg solved)
- User management: list/search/filter, activate/deactivate, delete with cascade
- Credit system: balance per user, deduction on message send, out-of-credits blocking, transaction log
- Signup control toggle with invite-only mode (immediate effect, no restart)
- Invitation system: email invite with time-limited, single-use tokens
- User class/tier assignment (free/standard/premium) determining credit allocation
- Audit logging of all admin actions (who, what, when, target)
- Platform settings key-value store (runtime config without redeployment)

**Should have (differentiators):**
- Admin dashboard with trend charts (signups, messages, credit usage over time)
- Credit distribution overview by tier
- Pending invitation management (revoke/resend)
- User detail page with activity summary
- Auto-reset credit policy configuration (manual/weekly/monthly)

**Defer (v2+):**
- Stripe/payment integration (doubles scope, clean follow-on milestone)
- Per-model credit costs (no user-facing model selection yet)
- Dynamic tier creation via admin UI (static YAML is appropriate for 3-5 tiers)
- Self-service tier upgrade (requires payment integration)
- Real-time credit balance WebSocket (polling is sufficient)

### Architecture Approach

Shared models and services, isolated entry points. Admin routers call the same database layer and reuse existing services (auth, email) but live in their own namespace (`/api/admin/`). The most critical integration point is credit deduction at the chat message layer -- credits must be checked and deducted BEFORE the expensive LangGraph agent pipeline runs, at the router level in `routers/chat.py`.

**Major components:**
1. **Mode-gated router mounting** -- `SPECTRA_MODE` env var controls which routers mount. Public mode: auth, chat, files, sessions, search. Admin mode: `/api/admin/*` routers. Dev mode: all. Lazy imports prevent admin routes leaking into public deployment.
2. **Credit system** -- `UserCredit` table (1:1 with users), `CreditTransaction` append-only ledger. Deduction uses SELECT FOR UPDATE to prevent race conditions. Deduct BEFORE agent runs, not after (no refunds on failure matches LLM API billing patterns).
3. **Platform settings service** -- Key-value DB table with 30-second in-memory cache. Settings change at runtime without restart. Precedence: DB overrides > YAML defaults > hardcoded fallbacks.
4. **Admin router package** -- `routers/admin/__init__.py` aggregates 6 sub-routers (auth, dashboard, users, settings, invitations, credits) into single mount point.
5. **Audit logging** -- `AdminAuditLog` table, logged in same transaction as business action (atomic). No middleware -- explicit service calls in admin routers for semantic action names.
6. **Invitation system** -- Reuses existing password reset token pattern: `secrets.token_urlsafe(32)`, SHA-256 hash stored, email pre-filled and locked, single-use validation.
7. **Admin frontend** -- Separate Next.js app at `admin-frontend/`, same stack as public frontend (TanStack Query, Zustand, shadcn/ui), API client points to `/api/admin/`.

**Database changes:**
- Add `is_admin` (Boolean, default False), `user_class` (Enum, default 'free') to `users` table
- Create 5 new tables: `platform_settings`, `user_credits`, `credit_transactions`, `invitations`, `admin_audit_log`
- Single Alembic migration with three-step pattern for NOT NULL columns (add nullable, backfill, alter to NOT NULL)

### Critical Pitfalls

Research identified 15 pitfalls across critical, moderate, and minor severity. The top 5 require explicit prevention during implementation:

1. **Credit deduction race condition** -- Two concurrent messages from the same user both read balance before either deducts, allowing overdraw. **Prevention:** Use `SELECT FOR UPDATE` (or `FOR NO KEY UPDATE`) to lock the row during balance check + deduction. Alternative: single atomic `UPDATE ... WHERE balance >= cost RETURNING balance`.

2. **Float precision drift** -- Using PostgreSQL FLOAT for credit values causes precision loss after hundreds of operations (0.1 + 0.2 = 0.30000000000000004). **Prevention:** Use NUMERIC(10,2) in PostgreSQL, Decimal in Python. Define credit costs in YAML as strings and parse with Decimal().

3. **Admin router leak to public deployment** -- Admin endpoints accidentally exposed in public mode if router imports have side effects or mode gating is wrong. **Prevention:** Lazy imports inside mode conditional, startup assertion test verifying no `/api/admin/*` routes in public mode.

4. **Alembic migration on production users table** -- Adding NOT NULL columns to existing users table fails without defaults. **Prevention:** Three-step migration: add nullable with server_default, backfill, alter to NOT NULL, optionally remove server_default.

5. **Invitation token predictability** -- Weak randomness (UUID4, sequential IDs) or missing single-use enforcement allows unauthorized registrations. **Prevention:** Reuse existing password reset pattern: `secrets.token_urlsafe(32)`, SHA-256 hash storage, status='accepted' after use, expires_at check.

**Additional high-risk areas:**
- CORS configuration must be mode-aware (public origins in public mode, admin origins in admin mode, both in dev)
- Credit deduction must happen BEFORE agent pipeline runs (agents are expensive, no refunds on failure)
- Audit log and business action must be in same transaction (flush, not commit, until both complete)
- Platform settings cache must not use `@lru_cache` (settings change at runtime)

## Implications for Roadmap

Based on dependency analysis and risk prioritization, suggest six sequential phases:

### Phase 1: Foundation (Database + Config + Mode Gating)
**Rationale:** Everything else depends on schema, config, mode gating, and admin auth. Pure backend, fully testable via pytest and API calls before any frontend work.

**Delivers:**
- Alembic migration: add `is_admin`, `user_class` to users table, create 5 new tables
- `SPECTRA_MODE` env var in settings, conditional router mounting in `main.py`
- `CurrentAdmin` dependency (extends `CurrentUser` + `is_admin` check)
- `routers/admin/__init__.py` package structure (empty sub-routers)
- `services/admin/audit.py` and `services/admin/settings.py`
- `user_classes.yaml` config file with tier definitions
- CLI admin seed command (`python -m app.cli seed-admin`)

**Addresses:** Pitfall 4 (migration), Pitfall 3 (mode gating), Pitfall 11 (admin bootstrap)

**Research flag:** Standard patterns, no research-phase needed.

### Phase 2: Credit System (Highest Risk First)
**Rationale:** Credit deduction touches the most critical user-facing flow (chat). Building early surfaces integration issues before other features add complexity. Admin credit endpoints enable testing (manually grant credits, verify deduction).

**Delivers:**
- `services/credit.py` (shared: atomic `check_and_deduct`, `InsufficientCreditsError`)
- `services/admin/credit.py` (admin: adjust, bulk-adjust, balance view, history)
- Hook credit check into `routers/chat.py` -- all four query/stream endpoints
- Create `UserCredit` record on user signup (modify auth service)
- `routers/admin/credits.py` (admin endpoints)
- Seed `default_credit_cost` platform setting

**Addresses:** Pitfall 1 (race condition with SELECT FOR UPDATE), Pitfall 2 (NUMERIC columns), Pitfall 8 (deduct before agent)

**Research flag:** Standard patterns, but CRITICAL to implement correctly. Phase-specific research: "How to implement reserve-then-confirm pattern for SSE streaming?"

### Phase 3: User Management + Platform Settings
**Rationale:** Depends on Phase 1 (schema, admin auth) but not Phase 2. Built after Phase 2 so user class changes can immediately affect credit allocations.

**Delivers:**
- `services/admin/user_management.py` (list, search, filter, activate, deactivate, change class, delete)
- `routers/admin/users.py`
- `routers/admin/settings.py` (CRUD on platform_settings table)
- Implement `allow_public_signup` check in existing `routers/auth.py` signup
- `routers/admin/dashboard.py` (aggregate queries)

**Addresses:** Pitfall 10 (config precedence), Pitfall 15 (settings cache)

**Research flag:** Standard CRUD patterns, no research-phase needed.

### Phase 4: Invitation System
**Rationale:** Depends on signup control toggle (Phase 3), email service (existing), and user model changes (Phase 1). First phase that requires a public frontend change.

**Delivers:**
- `services/admin/invitation.py` (create, validate, accept, revoke, resend, list expired)
- Invitation email template (reuse existing `services/email.py` patterns)
- `routers/admin/invitations.py`
- Modify `routers/auth.py` signup to accept and validate invite tokens
- Add invite signup page to public frontend (`/signup?invite=TOKEN`)

**Addresses:** Pitfall 5 (token security)

**Research flag:** Standard patterns (existing password reset provides template), no research-phase needed.

### Phase 5: Audit Log Completion + Dashboard Polish
**Rationale:** Audit log viewer is useful only after all admin actions are logging. Dashboard polish requires all data tables to exist.

**Delivers:**
- Wire `log_admin_action()` calls into ALL admin endpoints from Phases 2-4
- Audit log viewer endpoint (list, filter by action/admin/date range)
- Dashboard aggregate queries: credit distribution, low-credit users, trend calculations
- Recharts chart data endpoints

**Addresses:** Pitfall 7 (audit log growth -- index on created_at DESC, LIMIT on queries)

**Research flag:** Standard patterns, no research-phase needed.

### Phase 6: Admin Frontend
**Rationale:** Frontend is a pure consumer of the API built in Phases 1-5. All endpoints are stable and tested before UI work begins. Can run in parallel with Phases 2-5 if second developer builds UI against API stubs/mocks.

**Delivers:**
- Initialize `admin-frontend/` Next.js project (shadcn/ui, TanStack Query, Zustand, Recharts)
- Admin login page
- Dashboard page (Recharts charts, metrics)
- User management pages (list with search/filter, detail view)
- Platform settings page (form with save)
- Invitations page (list + create dialog)
- Credit management views (user credit detail, bulk adjust)
- Audit log viewer (table with date/action/admin filters)

**Addresses:** Pitfall 9 (CORS for dual frontends), Pitfall 14 (admin frontend talking to wrong backend mode)

**Research flag:** Standard Next.js + shadcn patterns, no research-phase needed. May need phase-specific research: "Recharts best practices for admin dashboards with shadcn/ui".

### Phase Ordering Rationale

- **Phase 1 first:** Foundation for everything. No admin functionality works without schema, mode gating, and admin auth.
- **Phase 2 second (credit system):** Highest technical risk. Integration with existing chat flow is the most complex change. Build when codebase is simple, before other features add noise.
- **Phase 3 before Phase 4:** User management provides immediate value and enables testing (create test users, assign classes). Invitation system depends on signup toggle from platform settings.
- **Phase 5 after data-generating phases:** Audit log viewer and dashboard need data from Phases 2-4. Building them earlier produces empty UIs.
- **Phase 6 last (or parallel):** Frontend depends on stable API contracts. Building after backend phases complete reduces rework from API changes.

**Dependency chains:**
- Database migration -> Admin auth -> All admin features
- Platform settings table -> Signup toggle -> Invitation system
- User model changes -> User class assignment -> Credit allocation
- Credit system core -> Admin credit endpoints -> Dashboard credit charts

**Avoids pitfall cascades:**
- Phase 1 catches router leak (Pitfall 3) before any admin functionality is written
- Phase 2 forces atomic credit design (Pitfall 1, 2) before integration spreads across codebase
- Phase 4 invitation system reuses Phase 1 password reset pattern (Pitfall 5)

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Credit system):** Reserve-then-confirm pattern for SSE streaming. Specific question: "How to handle credit deduction when stream disconnects mid-agent-execution?"
- **Phase 6 (Admin frontend):** Recharts integration with shadcn/ui chart components. Specific question: "What are the shadcn/ui Recharts chart components and how to use them for time-series data?"

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Standard Alembic migration, FastAPI mode gating, dependency injection patterns (all existing in codebase)
- **Phase 3:** Standard CRUD routers, SQLAlchemy queries, Pydantic schemas
- **Phase 4:** Reuses existing password reset token pattern from `routers/auth.py`
- **Phase 5:** Read-only aggregation queries, standard audit log table patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | One new backend dependency (APScheduler, well-established). One new frontend library (Recharts, shadcn-recommended). Everything else uses existing stack or Python stdlib. No exotic technologies. |
| Features | HIGH | Well-understood SaaS patterns with established best practices. Requirements appropriately scoped (defer Stripe, per-model costs, self-service). Credit system most complex but has proven solutions. |
| Architecture | HIGH | Direct codebase analysis of existing Spectra v0.4 source code (23K LOC). Integration points clearly identified. Mode-gated routing is pure configuration. |
| Pitfalls | HIGH | Credit race condition (Pitfall 1) and float precision (Pitfall 2) are well-documented with standard solutions (SELECT FOR UPDATE, NUMERIC). Migration patterns (Pitfall 4) from official Alembic cookbook. |

**Overall confidence:** HIGH

### Gaps to Address

**Credit deduction timing with SSE streaming:** The research identifies that credits should be deducted BEFORE the agent runs (to avoid wasting LLM costs), but the `/chat/{file_id}/stream` endpoint is a long-lived SSE connection that can disconnect mid-stream. The reserve-then-confirm pattern is mentioned but not fully detailed. During Phase 2 planning, research: "How do production AI chat APIs handle credit deduction for streaming responses?" (OpenAI, Anthropic billing patterns).

**Auto-reset scheduler reliability:** The requirements specify weekly/monthly auto-reset, but the research flags this as moderate complexity (Pitfall 12: timezone handling, idempotency, failure recovery). For v0.5, start with admin-triggered manual reset. Add automated reset as a v0.5.x enhancement after core credit system is validated. No gap blocking v0.5.0.

**Audit log growth at scale:** Pitfall 7 identifies unbounded audit log growth, but also notes that for Spectra's scale (single developer, likely <100 admin actions/day), a simple indexed table is sufficient for years. Partitioning is premature optimization. The gap: no monitoring/alerting when audit log exceeds 1M rows. Defer to v0.6+ operations milestone.

**CORS configuration complexity:** Pitfall 9 identifies that mode-aware CORS is required, but the exact implementation pattern is not detailed. During Phase 6 planning (or Phase 1 if admin frontend starts in parallel), verify: "FastAPI CORSMiddleware with dynamic origins based on settings".

**Coexistence with existing SearchQuota:** Integration pitfall flagged: existing `SearchQuota` model already implements daily per-user usage tracking for web searches. Credit system introduces second usage-tracking mechanism. During Phase 2 planning, decide: web searches deduct credits OR use existing quota system, not both. Likely answer: deprecate SearchQuota, migrate to credit system for all usage tracking.

## Sources

### Primary (HIGH confidence)
- Direct analysis of existing Spectra v0.4 source code: `main.py`, `config.py`, `dependencies.py`, `models/user.py`, `routers/auth.py`, `routers/chat.py`, `services/chat.py` -- architecture patterns verified against actual codebase
- `requirements/milestone-05-req.md` -- feature scope and acceptance criteria
- Existing Alembic migration chain (9 migrations) -- migration patterns
- FastAPI dependency injection patterns (project convention)

### Secondary (MEDIUM confidence)
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) -- v3.11.2 current, actively maintained
- [FastAPI + APScheduler patterns](https://sentry.io/answers/schedule-tasks-with-fastapi/) -- Lifespan integration pattern
- [Recharts npm](https://www.npmjs.com/package/recharts) -- v3.7.0 current
- [shadcn/ui Chart Component](https://ui.shadcn.com/docs/components/radix/chart) -- Built on Recharts
- [Preventing Postgres Race Conditions with SELECT FOR UPDATE](https://on-systems.tech/blog/128-preventing-read-committed-sql-concurrency-errors/) -- Credit race condition patterns
- [Transaction Locking to Prevent Race Conditions](https://sqlfordevs.com/transaction-locking-prevent-race-condition) -- PostgreSQL locking strategies
- [Working with Money in Postgres](https://www.crunchydata.com/blog/working-with-money-in-postgres) -- NUMERIC vs FLOAT for monetary values
- [PostgreSQL Numeric Types Documentation](https://www.postgresql.org/docs/current/datatype-numeric.html) -- Official float warning
- [Best Practices for Alembic Schema Migration](https://www.pingcap.com/article/best-practices-alembic-schema-migration/) -- Migration patterns
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) -- Official migration patterns
- [EnterpriseReady Audit Logging Guide](https://www.enterpriseready.io/features/audit-log/) -- Audit log patterns
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/) -- Official CORS reference
- [Stigg: Building AI Credits](https://www.stigg.io/blog-posts/weve-built-ai-credits-and-it-was-harder-than-we-expected) -- Real-world AI credit system challenges

### Tertiary (LOW confidence)
- Credit auto-reset scheduler timezone handling -- APScheduler supports cron expressions with timezone, but need to verify behavior during DST transitions
- Recharts React 19 compatibility -- v3.7.0 supports React 19 but may need `--legacy-peer-deps` for `react-is` peer dependency

---
*Research completed: 2026-02-16*
*Ready for roadmap: yes*
