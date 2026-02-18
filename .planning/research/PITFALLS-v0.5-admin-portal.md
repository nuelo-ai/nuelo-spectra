# Domain Pitfalls: v0.5 Admin Portal, Credit System, Invitation Flow

**Domain:** Admin portal with credit system, invitation flow, user class management, audit logging, and split-horizon deployment added to existing AI data analytics SaaS platform
**Researched:** 2026-02-16
**Confidence:** HIGH (derived from direct codebase analysis of 23K LOC + verified technical sources)

**Context:** Spectra v0.5 adds an admin portal to an existing FastAPI + Next.js platform with 4 shipped milestones, PostgreSQL with Alembic migrations, JWT auth with refresh tokens, 6 AI agents via LangGraph, async SQLAlchemy sessions, and SSE streaming. The admin portal introduces credit-based usage metering at the message layer, invitation-only signup flow, user class tiering, audit logging, and a split-horizon deployment model (SPECTRA_MODE env var) -- all while preserving the existing public-facing application. Single developer project.

---

## Critical Pitfalls

Mistakes at this level cause data corruption, security breaches, or require significant rewrites.

### Pitfall 1: Credit Deduction Race Condition -- Concurrent Messages Drain Balance Below Zero

**What goes wrong:**
Two concurrent chat messages from the same user both read `credit_balance = 1.0` before either deducts. Both pass the "has enough credits" check, both deduct 1.0, and the user ends up with `balance = -1.0`. In Spectra's architecture, this is especially likely because the `/chat/{file_id}/stream` endpoint is async and a user can fire multiple queries from different browser tabs (file tabs or sessions) simultaneously.

**Why it happens:**
The existing chat endpoints (`chat.py` lines 109-149, 152-236) use `DbSession` (injected via `get_db()` dependency) which creates a new `AsyncSession` per request. Without explicit row-level locking, SQLAlchemy's default `READ COMMITTED` isolation means two transactions can both SELECT the same credit balance, both see it as sufficient, and both UPDATE it independently.

**Consequences:**
- Users get free messages by exploiting concurrent requests
- Credit balance goes negative, breaking downstream logic that assumes `balance >= 0`
- If credits are eventually tied to revenue (Stripe integration mentioned in requirements), this becomes a financial loss

**Prevention:**
1. Use `SELECT ... FOR UPDATE` (via SQLAlchemy's `with_for_update()`) when reading credit balance before deduction. This locks the row so concurrent transactions block until the first completes.
2. Use `FOR NO KEY UPDATE` instead of `FOR UPDATE` since you are only changing the balance column, not the primary key -- this allows concurrent reads while blocking concurrent writes to the same row.
3. Alternatively, use a single atomic UPDATE with a WHERE clause: `UPDATE user_credits SET balance = balance - :cost WHERE user_id = :uid AND balance >= :cost RETURNING balance`. If no row is returned, the balance was insufficient. This eliminates the SELECT+UPDATE race entirely.
4. Add a CHECK constraint on the credit balance column: `CHECK (balance >= 0)` as a database-level safety net. Even if application logic fails, PostgreSQL will reject the UPDATE.

**Detection:**
- Credit balance values below zero in the database
- Credit transaction log showing more deductions than the balance should allow
- Users reporting they can send messages after credits are exhausted

**Confidence:** HIGH -- this is the most well-documented race condition pattern in billing systems. PostgreSQL's `SELECT FOR UPDATE` is the standard solution. Sources: [Preventing Postgres Race Conditions with SELECT FOR UPDATE](https://on-systems.tech/blog/128-preventing-read-committed-sql-concurrency-errors/), [Transaction Locking to Prevent Race Conditions](https://sqlfordevs.com/transaction-locking-prevent-race-condition)

---

### Pitfall 2: Float Arithmetic for Credit Values -- Precision Loss Accumulates

**What goes wrong:**
The requirements specify credits as float values (0.5, 1.0, 2.0, 3.0). Using PostgreSQL `FLOAT` or `DOUBLE PRECISION` (IEEE 754) causes precision drift over many operations. After hundreds of deductions of 0.5 credits, the balance might be `0.0000000000000001` instead of `0.0`, causing "has credits" checks to pass when they should not, or showing confusing balances in the admin UI.

**Why it happens:**
IEEE 754 floating-point cannot exactly represent all decimal fractions. `0.1 + 0.2 = 0.30000000000000004` in IEEE 754. Each credit deduction introduces a tiny error. Over a user's lifetime of hundreds or thousands of messages, these errors compound.

**Consequences:**
- Users see balance of `0.0000001` instead of `0.0` -- confusing UI
- Comparison `balance >= cost` passes when balance should be exactly zero
- Admin credit adjustments produce unexpected results
- Future Stripe integration may produce mismatches between what Spectra tracks and what Stripe reports

**Prevention:**
1. Use PostgreSQL `NUMERIC(10, 2)` (or `NUMERIC(12, 4)` if sub-cent precision needed) for all credit columns. This stores exact decimal values, not IEEE 754 approximations. In SQLAlchemy: `mapped_column(Numeric(10, 2))`.
2. Use Python `Decimal` type in application code for all credit arithmetic, not `float`. Pydantic v2 supports `Decimal` fields natively.
3. Define credit costs in YAML as strings (`"0.5"` not `0.5`) and parse with `Decimal("0.5")` to avoid float contamination at the config loading layer.
4. Alternative approach: store credits as integers in the smallest unit (e.g., 1 credit = 100 "centis"), so 0.5 credits = 50 centis. All arithmetic is integer. Display divides by 100 at the UI layer. This is the same pattern Stripe uses (cents not dollars).

**Detection:**
- Credit balances with many decimal places in the database
- Users reporting non-zero balances when they should be at zero
- Credit transaction logs where sum of deductions does not match starting balance minus current balance

**Confidence:** HIGH -- PostgreSQL official documentation explicitly states "Floating point numbers should not be used to handle money due to the potential for rounding errors." Sources: [Working with Money in Postgres](https://www.crunchydata.com/blog/working-with-money-in-postgres), [PostgreSQL Numeric Types](https://www.postgresql.org/docs/current/datatype-numeric.html), [PostgreSQL Currency Data Types](https://openillumi.com/en/en-postgresql-currency-numeric-best-practice/)

---

### Pitfall 3: SPECTRA_MODE Router Leak -- Admin Endpoints Exposed in Public Deployment

**What goes wrong:**
The split-horizon model requires `main.py` to conditionally mount routers based on `SPECTRA_MODE`. A common mistake is getting the conditional logic wrong, forgetting a router, or having shared imports that pull in admin routes as side effects. The result: admin endpoints are accessible on the public internet, bypassing the Tailscale network isolation that is the first line of defense.

**Why it happens:**
Python imports have side effects. If `app/routers/__init__.py` imports all router modules (including admin routers) for convenience, those modules are loaded even in `public` mode. If admin routers register themselves via module-level code or if a developer adds `from app.routers.admin import users` in a shared module, the admin routes may end up mounted regardless of the mode check.

The current `main.py` (lines 23, 270-275) imports all routers at module level:
```python
from app.routers import auth, chat, chat_sessions, files, health, search
```
When admin routers are added, the temptation is to add them to the same import block, then conditionally mount. But if any admin router has module-level side effects (e.g., registering background tasks, creating global state), those execute regardless.

**Consequences:**
- Admin API endpoints are publicly accessible (even if they require admin auth, the attack surface exists)
- Attackers can probe admin endpoints for vulnerabilities
- Undermines the entire defense-in-depth security model

**Prevention:**
1. Use lazy imports inside the mode conditional block:
```python
mode = os.getenv("SPECTRA_MODE", "dev")
if mode in ("admin", "dev"):
    from app.routers.admin import admin_auth, admin_users, admin_settings, admin_invitations, admin_credits
    app.include_router(admin_auth.router)
    # ...
```
2. Add a startup assertion that verifies the mounted routes match the expected set for the mode. Log all registered routes at startup and fail hard if an admin route appears in `public` mode.
3. Write a test that boots the app in `public` mode and asserts that no `/api/admin/*` routes exist in `app.routes`.
4. Never import admin router modules from non-admin code. Keep the `app/routers/admin/` package completely isolated from `app/routers/`.

**Detection:**
- Run `curl http://public-api/api/admin/users` and get anything other than 404
- Startup log showing admin routes registered in `public` mode
- OpenAPI docs at `/docs` showing admin endpoints in `public` deployment

**Confidence:** HIGH -- this is a common pattern in monorepo deployments. The prevention is straightforward but requires discipline.

---

### Pitfall 4: Alembic Migration Adding NOT NULL Columns to Users Table with Production Data

**What goes wrong:**
v0.5 adds at least three new columns to the existing `users` table: `is_admin` (Boolean), `user_class` (Enum), and possibly `credit_balance`. A naive migration like `op.add_column('users', sa.Column('user_class', sa.Enum('free', 'standard', 'premium'), nullable=False))` will fail on a table with existing rows because PostgreSQL cannot add a NOT NULL column without a default value to a table that already has data.

**Why it happens:**
In development, the database is often empty or freshly recreated, so the migration passes. In production (or staging with real data), the existing user rows have no value for the new column, violating the NOT NULL constraint.

**Consequences:**
- Migration fails in production, blocking deployment
- If the developer "fixes" it by making the column nullable, they lose the data integrity guarantee
- If they add a `server_default` in the migration but forget to remove it after, every new row gets the default even when the application should have provided a value

**Prevention:**
Use a three-step migration pattern for each NOT NULL column:
```python
# Step 1: Add column as nullable with server_default
op.add_column('users', sa.Column('user_class', sa.Enum('free', 'standard', 'premium', name='userclass'),
              nullable=True, server_default='free'))

# Step 2: Backfill existing rows (in same migration)
op.execute("UPDATE users SET user_class = 'free' WHERE user_class IS NULL")

# Step 3: Make column NOT NULL (now safe because all rows have values)
op.alter_column('users', 'user_class', nullable=False)

# Step 4 (optional): Remove server_default if application always provides value
op.alter_column('users', 'user_class', server_default=None)
```

For the `is_admin` column, default to `False`. For `user_class`, default to `'free'`.

**Detection:**
- Migration fails with: `column "user_class" of relation "users" contains null values`
- Or migration succeeds but leaves nullable columns where NOT NULL was intended

**Confidence:** HIGH -- standard Alembic pattern, documented in official Alembic cookbook. Sources: [Best Practices for Alembic Schema Migration](https://www.pingcap.com/article/best-practices-alembic-schema-migration/), [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)

---

### Pitfall 5: Invitation Token Predictability and Replay Attacks

**What goes wrong:**
If invitation tokens are generated with weak randomness (e.g., `uuid4()` alone, sequential IDs, or timestamps), attackers can guess valid tokens and register as invited users. If tokens are not properly invalidated after use, a single invitation link can be shared and used by multiple people.

**Why it happens:**
The existing password reset token system (in `auth.py` lines 234-258) already does this correctly -- it uses `create_reset_token()` which generates a random token, stores its SHA-256 hash, and marks it as `is_used` after consumption. However, developers building the invitation system may not follow the same pattern, especially if they reach for simpler approaches like JWT-based invitation tokens or bare UUIDs.

**Consequences:**
- Unauthorized users register on the platform
- Invite-only mode is bypassed
- Single invitation shared publicly allows unlimited signups

**Prevention:**
1. Follow the exact same pattern as the existing password reset tokens: generate with `secrets.token_urlsafe(32)`, store SHA-256 hash in DB, mark `is_used = True` after registration, enforce `expires_at` check.
2. Add `email` to the invitation record and validate that the registering user's email matches the invited email (the requirements already specify pre-filled, locked email).
3. Invalidate token in the same database transaction as user creation -- not before (if creation fails, token is still usable) and not after (race condition window).
4. Rate-limit the invitation acceptance endpoint to prevent brute-force token guessing.

**Detection:**
- Multiple registrations from the same invitation token
- Registrations with emails that do not match any invitation record
- Invitation tokens that were never created by an admin appearing in the system

**Confidence:** HIGH -- the existing codebase already demonstrates the correct pattern for password reset tokens. The risk is failing to reuse that pattern.

---

## Moderate Pitfalls

### Pitfall 6: Admin Session Management Conflicting with User Sessions

**What goes wrong:**
Spectra's current JWT system (in `security.py`) uses a single `secret_key` and puts `user_id` in the `sub` claim with a `type` field ("access" or "refresh"). If admin authentication reuses the same JWT infrastructure without differentiation, an admin's token could be used to access user endpoints and vice versa. Worse, if an admin is also a regular user (same `users` table), their admin session and user session could interfere.

**Why it happens:**
The existing `get_current_user` dependency (in `dependencies.py`) extracts `user_id` from any valid access token and loads the user. If admin endpoints also use JWT tokens with the same structure, a regular user's token would pass validation on admin endpoints -- the only check would be `is_admin` on the loaded user. This works but creates a subtle issue: if the admin frontend stores tokens differently than the public frontend, or if session timeouts differ (30 min for admin vs 30 days for user refresh), the shared token infrastructure becomes confusing.

**Prevention:**
1. Add an `is_admin` check as a FastAPI dependency, not just in endpoint logic:
```python
async def get_current_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
```
2. Consider adding `"role": "admin"` to the JWT payload for admin tokens, and validate it in the admin dependency. This way, a regular user's token is structurally rejected by admin endpoints even before the DB lookup.
3. Use shorter access token expiry for admin tokens (e.g., 15 minutes vs 30 minutes for regular users) to reduce session hijack window.
4. The admin frontend should handle its own token storage independently from the public frontend (different localStorage keys, different cookie names if using cookies).

**Detection:**
- Regular user accessing admin endpoints successfully
- Admin tokens working on public endpoints when they should be scoped

---

### Pitfall 7: Audit Log Table Grows Unbounded -- Query Performance Degrades

**What goes wrong:**
The `admin_audit_log` table records every admin action (user management, credit adjustments, settings changes, invitation operations). With active admin usage, this table grows continuously. Without partitioning or archival, queries like "show recent admin actions" or "filter audit log by admin" become increasingly slow as the table reaches millions of rows.

**Why it happens:**
Audit logs are append-only and rarely deleted. Developers focus on writing to the audit log but not on reading from it efficiently at scale. The admin dashboard likely queries the audit log for "recent activity" on every page load.

**Prevention:**
1. Partition the `admin_audit_log` table by month from day one using PostgreSQL range partitioning:
```sql
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY,
    admin_id UUID NOT NULL,
    action VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ...
) PARTITION BY RANGE (created_at);
```
2. Use `pg_partman` or manual partition creation for hands-off management.
3. Add a composite index on `(created_at, admin_id)` for the most common query patterns.
4. For the admin dashboard "recent activity" widget, query only the current month's partition and limit results.
5. Plan for partition pruning in queries -- always include `created_at` in WHERE clauses.

**For Spectra's scale (single developer, likely <100 admin actions/day):** Partitioning is premature optimization. A simple table with an index on `created_at DESC` will perform well for years. Add a `LIMIT` to all audit log queries. Revisit if the table exceeds 1M rows.

**Detection:**
- Audit log page load time increasing over time
- `EXPLAIN ANALYZE` showing sequential scans on audit log queries

**Confidence:** HIGH for the pattern, but LOW urgency for Spectra's expected scale. Sources: [Production-Ready Audit Logs in PostgreSQL](https://medium.com/@sehban.alam/lets-build-production-ready-audit-logs-in-postgresql-7125481713d8), [Audit Logging with Postgres Partitioning](https://elephas.io/audit-logging-with-postgres-partitioning/)

---

### Pitfall 8: Credit Deduction at Wrong Layer -- Deducting Before Agent Completes

**What goes wrong:**
Credits are deducted when a message is sent, but the AI agent pipeline is multi-step (Coding Agent -> Code Checker -> Execution -> Data Analysis Agent, as documented in `chat.py` lines 117-128). If credits are deducted at message creation but the agent pipeline fails mid-way (e.g., code checker rejects, execution timeout, LLM API error), the user loses credits for a failed response.

**Why it happens:**
The natural place to add credit deduction is at the beginning of the `/chat/{file_id}/query` or `/chat/sessions/{session_id}/stream` endpoint, alongside the file ownership check. But the agent pipeline has a `max_retries` setting (3 retries) and can fail at multiple points. The SSE stream endpoint (`/chat/{file_id}/stream`) explicitly states "Failed streams save nothing to the database" (line 174) -- credits should follow the same principle.

**Consequences:**
- Users lose credits for failed agent invocations
- Users learn to avoid complex queries that might fail, reducing platform value
- Credit refund logic adds complexity and is error-prone

**Prevention:**
1. Deduct credits AFTER the agent pipeline completes successfully. In the non-streaming endpoint, deduct after `agent_service.run_chat_query()` returns. In the streaming endpoint, deduct in the final "completed" event handler.
2. Reserve credits at the start (decrement balance, record as "pending" in transaction log), then confirm or release after completion. This prevents the race condition where a user fires two messages that both pass the balance check while only one should succeed.
3. The reserve-then-confirm pattern also handles the case where the SSE stream is disconnected mid-way (`request.is_disconnected()` check at line 207) -- the reservation is released.

**Detection:**
- Credit transactions with no corresponding successful agent response
- Users complaining about credit loss on error messages
- Credit transaction log showing deductions with no matching chat message in `chat_messages` table

---

### Pitfall 9: CORS Configuration for Admin Frontend Breaks Public Frontend

**What goes wrong:**
The current CORS configuration (`main.py` lines 260-267) uses `settings.get_cors_origins()` to allow specific origins with `allow_credentials=True`. When adding the admin frontend (localhost:3001 in dev, admin.spectra.ts.net in production), the developer may add both origins to `cors_origins`. In `public` mode, the admin frontend origin should NOT be in the allowed origins list (since admin endpoints do not exist). If it is, browsers receive confusing CORS headers, and in `admin` mode, the public frontend origin may need to be excluded.

**Why it happens:**
Starlette's CORSMiddleware applies the same CORS policy to all routes. There is no per-router CORS configuration without significant middleware customization. When the same codebase serves different modes, the CORS origins must also be mode-dependent.

**Prevention:**
1. Make CORS origins mode-dependent in `main.py`:
```python
mode = os.getenv("SPECTRA_MODE", "dev")
if mode == "public":
    origins = settings.get_cors_origins()  # public frontend only
elif mode == "admin":
    origins = settings.get_admin_cors_origins()  # admin frontend only
else:  # dev
    origins = settings.get_cors_origins() + settings.get_admin_cors_origins()
```
2. Add `admin_cors_origins` to the Settings class, separate from `cors_origins`.
3. In dev mode, include both `http://localhost:3000` and `http://localhost:3001`.
4. Test CORS preflight responses in each mode to verify correct origin handling.

**Detection:**
- Browser console showing CORS errors when accessing admin frontend
- Public frontend unexpectedly allowing requests from admin origin
- Preflight OPTIONS requests returning wrong `Access-Control-Allow-Origin` header

**Confidence:** HIGH -- this is a direct consequence of the split-horizon model interacting with the existing CORS setup. Sources: [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/), [FastAPI CORS Starlette Trusted Hosts Origins 2025](https://johal.in/fastapi-cors-starlette-trusted-hosts-origins-2025-2/)

---

### Pitfall 10: User Class Config YAML + DB Override Precedence Confusion

**What goes wrong:**
User class definitions live in `user_classes.yaml` (static config) but credit amounts per tier can be overridden in the `platform_settings` DB table. When the admin edits credit amounts in the portal, those overrides are stored in DB. But when the developer edits `user_classes.yaml` to change defaults, the DB overrides mask the changes. The result: the admin edits credits in the UI, the developer changes the YAML, and neither change takes effect as expected because the precedence rules are unclear.

**Why it happens:**
Two sources of truth for the same data. The requirements specify "Admin portal can edit credit amounts and display names per tier" (stored in DB) and "Predefined tiers defined in a config file" (YAML). Without clear precedence documentation and code comments, future changes (or even current development) will produce unexpected behavior.

**Prevention:**
1. Establish and document explicit precedence: DB overrides ALWAYS win over YAML defaults. YAML provides the fallback values only.
2. Implement a single `get_tier_config(tier_name)` function that reads YAML, then overlays DB overrides. All code goes through this function -- never read YAML directly for tier data.
3. In the admin UI, show both the YAML default and the current override, so the admin knows what they are overriding.
4. When a YAML value changes (after redeployment), the admin UI should surface the new default alongside any existing override so the admin can decide whether to keep their override or reset to the new default.

**Detection:**
- Admin changes credit amounts in the portal but users still see old values (DB override not being read)
- Developer changes YAML defaults but production shows old values (DB override masking YAML)
- Different behavior between fresh deployments (no DB overrides) and existing deployments (with DB overrides)

---

## Minor Pitfalls

### Pitfall 11: First Admin Account Bootstrap Chicken-and-Egg

**What goes wrong:**
The requirements state "First admin account is seeded via CLI command or environment variable." If the seed mechanism requires the backend to be running (e.g., hitting an API endpoint), but the backend in admin mode requires admin auth for all endpoints, there is no way to create the first admin.

**Prevention:**
1. Create a CLI command (e.g., `python -m app.cli seed-admin --email admin@example.com --password ...`) that directly writes to the database, bypassing the API entirely.
2. Alternatively, support `ADMIN_SEED_EMAIL` and `ADMIN_SEED_PASSWORD` environment variables that the `lifespan` function checks on startup -- if no admin exists and the env vars are set, create one.
3. Never expose an unauthenticated admin creation endpoint, even temporarily.

---

### Pitfall 12: Credit Reset Cron Job -- Timezone and Partial Reset Issues

**What goes wrong:**
Weekly/monthly credit resets need a background job. If the reset runs at midnight UTC but some users signed up at 11 PM UTC, they get less than a full week of credits on their first cycle. If the reset job fails or is delayed, users miss their reset. If it runs twice (e.g., container restart), users get double credits.

**Prevention:**
1. Make the reset idempotent: store `last_reset_at` on the user credit record and only reset if `last_reset_at` is older than one cycle.
2. Track reset via `credit_transactions` table with type `"reset"` -- if a reset transaction exists for this cycle, skip.
3. For v0.5, start with admin-triggered manual reset. Add automated reset as a later enhancement.

---

### Pitfall 13: Enum Column Migration -- PostgreSQL Enum Type Creation

**What goes wrong:**
Adding a `user_class` column with a PostgreSQL ENUM type requires creating the ENUM type first. Alembic's autogenerate may not handle this correctly, especially for downgrade (dropping an ENUM type that may still be referenced). If the migration is run, rolled back, and run again, the ENUM type already exists and the migration fails.

**Prevention:**
1. Create the ENUM type explicitly in the migration:
```python
userclass = sa.Enum('free', 'standard', 'premium', name='userclass')
userclass.create(op.get_bind(), checkfirst=True)
```
2. In the downgrade, drop the ENUM type after removing the column:
```python
op.drop_column('users', 'user_class')
sa.Enum(name='userclass').drop(op.get_bind(), checkfirst=True)
```
3. Use `checkfirst=True` to make both operations idempotent.

---

### Pitfall 14: Admin Frontend Talking to Wrong Backend Mode

**What goes wrong:**
In development, both frontends talk to `localhost:8000` (dev mode, all routes). In production, the admin frontend must talk to `admin-api.spectra.ts.net` (admin mode). If the admin frontend's `NEXT_PUBLIC_API_URL` is misconfigured to point to the public API, all admin requests fail with 404 (admin routes do not exist in public mode). The errors are not obvious -- just "endpoint not found."

**Prevention:**
1. Add a `/health` endpoint that returns the current `SPECTRA_MODE` in both public and admin modes.
2. The admin frontend should check the health endpoint on startup and warn/fail if the backend is not in admin or dev mode.
3. Use environment-specific `.env` files for the admin frontend with clear variable names: `NEXT_PUBLIC_ADMIN_API_URL`.

---

### Pitfall 15: `get_settings()` Cache Invalidation for Runtime Platform Settings

**What goes wrong:**
The current `get_settings()` uses `@lru_cache` (config.py line 88), meaning settings are loaded once and cached forever. Platform settings (signup toggle, credit costs, reset policies) are stored in the `platform_settings` DB table and must change at runtime without server restart. If any code reads platform settings through the cached `Settings` object, changes will not be reflected.

**Prevention:**
1. Keep `get_settings()` with `@lru_cache` for environment-based configuration (DB URL, JWT secret, API keys) -- these do not change at runtime.
2. Create a separate `PlatformSettingsService` that reads from the `platform_settings` DB table on each request (or with a short TTL cache of 30-60 seconds).
3. Never mix env-based settings and DB-based platform settings in the same class or function.
4. The admin UI "changes take effect immediately" requirement (section 4 of the requirements) explicitly requires DB-backed settings, not env vars.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation | Priority |
|-------------|---------------|------------|----------|
| Database migrations (adding to users table) | NOT NULL column on existing data fails | Three-step migration: add nullable, backfill, alter to NOT NULL | Must do first |
| Credit system implementation | Race condition on concurrent deductions | Atomic UPDATE with WHERE or SELECT FOR NO KEY UPDATE | Implement before any message-layer integration |
| Credit system implementation | Float precision drift | Use NUMERIC(10,2) in PostgreSQL, Decimal in Python | Decide at column creation time, cannot change later without migration |
| Credit deduction integration | Deducting before agent completes | Reserve-then-confirm pattern, deduct only on success | Design at integration time |
| Split-horizon router mounting | Admin routes leaked to public mode | Lazy imports inside mode conditional, startup route assertion test | Test in CI before any deployment |
| CORS for dual frontends | Admin origins in public mode | Mode-dependent CORS origins configuration | Configure when adding admin frontend |
| Invitation flow | Token predictability, replay | Reuse existing password reset token pattern (secrets + SHA-256 + DB) | Implement when building invitation system |
| User class config | YAML + DB override confusion | Single function with documented precedence (DB wins) | Establish pattern before building admin UI for tier editing |
| Admin auth | Session/token conflicts with user auth | Separate dependency (`CurrentAdmin`), role in JWT | Implement in first admin auth phase |
| Audit logging | Unbounded table growth | Index on created_at DESC, LIMIT on all queries. Partitioning later if needed | Implement logging first, optimize only if scale demands |
| Admin seeding | Cannot create first admin | CLI command or env var seed at startup | Must work before any admin testing |
| Platform settings | lru_cache prevents runtime changes | Separate PlatformSettingsService reading from DB | Design before implementing signup toggle or credit cost changes |
| Enum migration | PostgreSQL ENUM type not idempotent | Use checkfirst=True on create/drop | Handle in migration writing |

---

## Integration Pitfalls (Existing System Interactions)

### Credit Deduction + SSE Streaming
The streaming endpoint (`/chat/{file_id}/stream`) uses an async generator that yields events over a long-lived connection. If credits are deducted at the start but the stream fails mid-way, the credit is lost. If credits are deducted at the end but the client disconnects before the "completed" event, the deduction may not happen. The reserve-then-confirm pattern (Pitfall 8) is essential here.

### Admin User Deactivation + Active User Sessions
When an admin deactivates a user account (sets `is_active = False`), the user's existing JWT tokens remain valid until expiry (up to 30 minutes for access, 30 days for refresh). The existing `get_current_user` dependency (`dependencies.py` line 61-66) already checks `is_active`, so the user will be blocked on next token verification. However, an active SSE stream will continue until the next message attempt. This is acceptable behavior but should be documented.

### Credit System + Search Quotas Coexistence
The existing `SearchQuota` model (`search_quota.py`) already implements daily per-user usage tracking for web searches. The credit system introduces a second usage-tracking mechanism. These must not conflict -- web searches should either deduct credits OR use the existing quota system, not both. Decide which system governs and deprecate or integrate the other.

### `lru_cache` Settings + SPECTRA_MODE
The `get_settings()` function is cached at module import time. `SPECTRA_MODE` is read from env vars. If the mode is added to the `Settings` class, it is available through the cached settings. But if any code reads `os.getenv("SPECTRA_MODE")` directly (bypassing Settings), there is a risk of inconsistency if the env var is modified after startup. Always read mode through `settings.spectra_mode`.

---

## Sources

- [Preventing Postgres Race Conditions with SELECT FOR UPDATE](https://on-systems.tech/blog/128-preventing-read-committed-sql-concurrency-errors/) -- Credit race condition patterns
- [Transaction Locking to Prevent Race Conditions](https://sqlfordevs.com/transaction-locking-prevent-race-condition) -- PostgreSQL locking strategies
- [The SELECT FOR UPDATE Trap Everyone Falls Into](https://medium.com/fresha-data-engineering/the-select-for-update-trap-everyone-falls-into-8643089f94c7) -- FOR NO KEY UPDATE alternative
- [Working with Money in Postgres](https://www.crunchydata.com/blog/working-with-money-in-postgres) -- NUMERIC vs FLOAT for monetary values
- [PostgreSQL Numeric Types Documentation](https://www.postgresql.org/docs/current/datatype-numeric.html) -- Official float warning
- [PostgreSQL Currency Data Types: Why NUMERIC is the Only Safe Choice](https://openillumi.com/en/en-postgresql-currency-numeric-best-practice/) -- NUMERIC best practices
- [Best Practices for Alembic Schema Migration](https://www.pingcap.com/article/best-practices-alembic-schema-migration/) -- Migration patterns
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) -- Official migration patterns
- [Production-Ready Audit Logs in PostgreSQL](https://medium.com/@sehban.alam/lets-build-production-ready-audit-logs-in-postgresql-7125481713d8) -- Audit log optimization
- [Audit Logging with Postgres Partitioning](https://elephas.io/audit-logging-with-postgres-partitioning/) -- Partitioning strategy
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/) -- Official CORS reference
- [FastAPI CORS Starlette Trusted Hosts Origins 2025](https://johal.in/fastapi-cors-starlette-trusted-hosts-origins-2025-2/) -- CORS pitfalls
- [FastAPI Best Practices: Production-Ready Patterns for 2025](https://orchestrator.dev/blog/2025-1-30-fastapi-production-patterns/) -- General FastAPI patterns
