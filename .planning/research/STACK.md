# Technology Stack: v0.5 Admin Portal

**Project:** Spectra - AI-powered data analytics platform
**Researched:** 2026-02-16
**Confidence:** HIGH (no exotic dependencies, builds on existing patterns, all libraries well-established)

## Overview

v0.5 adds an admin portal with user management, credit system, invitation flow, and split-horizon deployment. The good news: almost everything needed is already in the stack or available via Python stdlib. The admin frontend is a separate Next.js app reusing the same library choices as the public frontend. No new backend framework dependencies are required -- the additions are limited to one scheduling library and standard library usage.

**Key principle: minimize new dependencies.** The existing stack (FastAPI + SQLAlchemy + Alembic + PyJWT + Jinja2 + SMTP) already provides everything needed for admin auth, audit logging, invitation emails, and database schema changes. The credit reset scheduler is the only genuinely new backend capability requiring a library.

---

## What Changes (and What Does Not)

### Does NOT Change

- FastAPI backend framework
- PostgreSQL database + SQLAlchemy ORM + Alembic migrations
- JWT authentication (PyJWT) + refresh tokens
- SMTP email service (aiosmtplib + Jinja2 templates)
- LangGraph agent orchestration
- E2B sandbox execution
- Pydantic settings + python-dotenv
- Public frontend: Next.js 16 / React 19 / TanStack Query / Zustand / shadcn/ui

### Changes Required

| Layer | What Changes | Why |
|-------|-------------|-----|
| Backend: User Model | Add `is_admin`, `user_class`, `credit_balance`, `last_credit_reset` fields | Admin role, tier assignment, credit tracking |
| Backend: New Models | 5 new tables (platform_settings, user_credits, credit_transactions, invitations, admin_audit_log) | Admin features require persistent state |
| Backend: Router Mounting | `SPECTRA_MODE` env var controls which routers mount | Split-horizon architecture |
| Backend: New Routers | `admin/` directory with 5 admin routers | Admin API endpoints |
| Backend: Scheduler | APScheduler for periodic credit resets | Weekly/monthly credit allocation |
| Backend: YAML Config | `user_classes.yaml` for tier definitions | Static tier config |
| Backend: CLI Command | Admin seed script | First admin account creation |
| Backend: Email Templates | New invitation email template | Invite flow |
| New: Admin Frontend | Separate Next.js app at `admin-frontend/` | Network-isolated admin portal |
| Config: Settings | New env vars (`SPECTRA_MODE`, `ADMIN_FRONTEND_URL`) | Split-horizon + CORS |

---

## Recommended Stack Additions

### Backend: Python -- 1 New Dependency

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `apscheduler` | `>=3.11.0` | Periodic credit reset scheduler | Well-established Python scheduler. AsyncIOScheduler integrates with FastAPI's event loop via lifespan. Handles weekly/monthly credit resets without external cron or Celery overhead. Only needed on the `admin` or `dev` mode deployment. |

**Why APScheduler over alternatives:**
- **vs Celery**: Overkill. Celery requires Redis/RabbitMQ broker. We need one periodic job (credit reset), not a distributed task queue.
- **vs `fastapi-utils` repeat_every**: Too simple. No cron expression support, no persistence across restarts, no timezone handling.
- **vs OS-level cron**: Not portable. Docker deployments need the scheduler inside the application.
- **vs manual endpoint**: Admin could trigger resets manually, but auto-reset is a stated requirement. APScheduler handles both -- scheduled auto-reset plus manual trigger via admin API.

### Backend: Python Standard Library (No New Dependencies)

These capabilities come from Python stdlib -- no pip installs needed:

| Capability | Module | Purpose |
|------------|--------|---------|
| Invite token generation | `secrets.token_urlsafe(32)` | Cryptographically secure, URL-safe invite tokens. 32 bytes = 256-bit entropy. |
| Token expiry | `datetime` | Invite link expiration (7-day default) |
| YAML config parsing | `pyyaml` (already installed) | `user_classes.yaml` tier definitions |
| Enum for user classes | `enum.Enum` + SQLAlchemy `Enum` type | `free`, `standard`, `premium` tier enum |
| Audit log serialization | `json` (stdlib) | Serializing action details in audit log |
| CLI admin seed | `argparse` or simple script | `python -m app.cli.seed_admin` |

### Backend: Existing Dependencies (Already Installed, Zero Changes)

| Existing Dependency | v0.5 Usage | Notes |
|---------------------|-----------|-------|
| `fastapi[standard]` | Admin routers, dependency injection, CORS | Router prefix `/api/admin/` |
| `sqlalchemy[asyncio]` + `asyncpg` | 5 new tables, user model extensions | Same ORM patterns, new models |
| `alembic` | Migration for new tables + user model changes | Same migration chain |
| `pyjwt` | Admin JWT tokens (same mechanism) | Add `is_admin` claim to token payload |
| `pydantic-settings` | New settings: `SPECTRA_MODE`, `ADMIN_FRONTEND_URL` | Extend existing `Settings` class |
| `aiosmtplib` + `jinja2` | Invitation emails | New template, same email service |
| `pyyaml` | `user_classes.yaml` parsing | Already used for agent configs |
| `pwdlib[argon2]` | Admin password hashing | Same auth service |
| `httpx` | Health checks (if needed) | Already installed |

---

### Admin Frontend: New Next.js Application

The admin frontend is a **separate Next.js app** (not a route in the existing frontend). It uses the same library stack as the public frontend for consistency and developer familiarity.

#### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `next` | `16.1.6` | Admin frontend framework | Match public frontend version exactly. Separate app, same framework. |
| `react` | `19.2.3` | UI library | Match public frontend. |
| `react-dom` | `19.2.3` | React DOM renderer | Match public frontend. |
| `typescript` | `^5` | Type safety | Match public frontend. |

#### State & Data Fetching

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@tanstack/react-query` | `^5.90.20` | Server state management, API calls | Same pattern as public frontend. Admin CRUD operations use mutations + query invalidation. |
| `zustand` | `^5.0.11` | Client state (auth, UI state) | Lightweight, same as public frontend. Admin auth state, sidebar state. |

#### UI Components & Styling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `radix-ui` | `^1.4.3` | Headless UI primitives | Same as public frontend. Dialog, dropdown, tabs for admin panels. |
| `tailwindcss` | `^4` | Utility CSS | Same as public frontend. |
| `class-variance-authority` | `^0.7.1` | Component variants | Same as public frontend. |
| `clsx` + `tailwind-merge` | Latest | Class name utilities | Same as public frontend. |
| `lucide-react` | `^0.563.0` | Icons | Same as public frontend. |
| `sonner` | `^2.0.7` | Toast notifications | Admin action feedback (user created, credits adjusted, etc). |
| `next-themes` | `^0.4.6` | Dark mode | Consistency with public frontend. |

#### Data Display

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@tanstack/react-table` | `^8.21.3` | User list, invitation list, audit log tables | Already used in public frontend for data tables. Server-side pagination, sorting, filtering. |

#### Charts (Admin Dashboard)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `recharts` | `^3.7.0` | Admin dashboard trend charts (signups, messages, credits over time) | **shadcn/ui's official chart components are built on Recharts.** Using Recharts directly means we get shadcn chart patterns (ChartContainer, ChartTooltip) that match the existing design system. The admin dashboard needs simple line/bar/area charts -- not the heavy scientific plotting that Plotly handles in the public app. Recharts is ~45KB gzipped vs Plotly's ~1MB. |

**Why Recharts (not Plotly) for admin dashboard:**
- The public frontend uses Plotly for user-facing data visualization (complex, interactive, AI-generated charts). That is a different use case.
- Admin dashboard charts are simple metrics: signups over time, credit usage trends, message counts. These are static line/bar charts with fixed data shapes.
- shadcn/ui provides copy-paste chart components built on Recharts. Using Recharts means the admin dashboard charts match the shadcn design system natively.
- Recharts is ~45KB gzipped. Plotly is ~1MB. The admin portal should load fast.
- Recharts v3.7.0 supports React 19 (may need `--legacy-peer-deps` for `react-is` peer dependency).

**Why NOT Tremor:**
- Tremor is excellent for dashboards but is a heavier abstraction layer on top of Recharts + Radix + Tailwind. Since we already have shadcn/ui (which uses Radix + Tailwind), adding Tremor creates overlapping component systems. Use shadcn/ui's own chart components (Recharts-based) instead.

---

## Admin Frontend: What to Copy from Public Frontend

The admin frontend should copy these configuration files from the public frontend (not share them via monorepo -- keeps deployment simple):

| File | Copy From | Modify |
|------|-----------|--------|
| `tailwind.config.ts` | `frontend/` | Same config |
| `tsconfig.json` | `frontend/` | Same config |
| `postcss.config.mjs` | `frontend/` | Same config |
| `.eslintrc.json` | `frontend/` | Same config |
| `components/ui/` | `frontend/` | Copy shadcn components needed (button, card, dialog, table, input, select, badge, etc.) |
| `lib/utils.ts` | `frontend/` | Same cn() utility |
| `lib/api-client.ts` | `frontend/` | Modify base URL to admin API |

**Why NOT a monorepo (Turborepo/Nx):**
- The project is 23K LOC across 4 milestones. Adding monorepo tooling (Turborepo, workspace configs, shared packages) introduces significant complexity for minimal benefit.
- The admin frontend shares UI library choices but has completely different pages, layouts, and API endpoints.
- Copying shared code (shadcn components, utilities) is ~20 files. Maintaining a monorepo to avoid copying 20 files is not worth the overhead.
- Split-horizon deployment means these are deployed to different networks. Independent build/deploy pipelines are simpler.

---

## Split-Horizon Architecture: No New Dependencies

The split-horizon deployment is a **configuration pattern**, not a technology addition:

| Aspect | Implementation | New Dependency? |
|--------|---------------|-----------------|
| `SPECTRA_MODE` env var | `pydantic-settings` (existing) | No |
| Conditional router mounting | Python `if/elif` in `main.py` | No |
| Admin routers directory | `backend/app/routers/admin/` | No |
| Tailscale VPN | Infrastructure concern, not code | No |
| Docker Compose for admin | Docker config file | No |
| CORS for admin frontend | Extend `Settings.cors_origins` | No |

### Backend `main.py` Pattern

```python
# Extend config.py
spectra_mode: str = "dev"  # "public" | "admin" | "dev"
admin_frontend_url: str = "http://localhost:3001"

# In main.py
settings = get_settings()

if settings.spectra_mode in ("public", "dev"):
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(chat.router)
    app.include_router(chat_sessions.router)
    app.include_router(search.router)

if settings.spectra_mode in ("admin", "dev"):
    from app.routers.admin import (
        admin_auth, admin_users, admin_settings,
        admin_invitations, admin_credits
    )
    app.include_router(admin_auth.router)
    app.include_router(admin_users.router)
    app.include_router(admin_settings.router)
    app.include_router(admin_invitations.router)
    app.include_router(admin_credits.router)

# Always include health
app.include_router(health.router)
```

---

## Database Changes: No New Dependencies

All database changes use the existing SQLAlchemy + Alembic stack:

### New Tables (5)

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `platform_settings` | `key` (PK), `value` (JSON), `updated_at`, `updated_by` | Key-value store for runtime config |
| `user_credits` | `user_id` (FK), `balance` (Float), `last_reset` | Per-user credit state |
| `credit_transactions` | `id`, `user_id`, `amount`, `type` (enum: deduction/adjustment/reset), `reason`, `admin_id`, `created_at` | Immutable transaction log |
| `invitations` | `id`, `email`, `token` (unique), `status` (enum: pending/accepted/expired/revoked), `expires_at`, `invited_by`, `created_at` | Invite records |
| `admin_audit_log` | `id`, `admin_id`, `action`, `target_type`, `target_id`, `details` (JSON), `created_at` | Immutable audit trail |

### User Table Extensions

| New Column | Type | Default | Notes |
|------------|------|---------|-------|
| `is_admin` | Boolean | `False` | Admin role flag |
| `user_class` | Enum(free/standard/premium) | `free` | Tier assignment |
| `credit_balance` | Float | `0.0` | Current credit balance (denormalized for fast reads) |
| `last_credit_reset` | DateTime | `None` | Last auto-reset timestamp |
| `last_login_at` | DateTime | `None` | For admin dashboard metrics |
| `invited_by` | UUID (FK, nullable) | `None` | Track invitation source |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Credit reset scheduler | APScheduler (AsyncIOScheduler) | Celery + Redis | Overkill for 1 periodic job. Adds Redis dependency, worker process, broker config. |
| Credit reset scheduler | APScheduler | OS cron | Not portable. Docker/Tailscale deployment needs in-app scheduler. |
| Credit reset scheduler | APScheduler | `fastapi-utils` repeat_every | No cron expressions, no timezone support, no graceful restart handling. |
| Admin dashboard charts | Recharts (via shadcn chart patterns) | Plotly | Plotly is 20x larger (~1MB vs ~45KB). Admin needs simple line/bar charts, not scientific plotting. |
| Admin dashboard charts | Recharts | Tremor | Overlapping abstraction layer with shadcn/ui. Both use Radix + Tailwind. Pick one. |
| Admin dashboard charts | Recharts | Chart.js | No shadcn/ui integration. Recharts has official shadcn chart components. |
| Invite tokens | `secrets.token_urlsafe(32)` | UUID v4 | UUID v4 has only 122 bits of entropy. `token_urlsafe(32)` has 256 bits. Also URL-safe by design. |
| Invite tokens | `secrets.token_urlsafe(32)` | itsdangerous (signed tokens) | Unnecessary. Invite tokens are stored in DB and validated by lookup, not by signature verification. |
| Project structure | Separate apps (copy shared code) | Monorepo (Turborepo) | 23K LOC project. Monorepo tooling overhead not justified. Admin shares ~20 files with public frontend. |
| Admin auth | Same JWT mechanism + `is_admin` claim | Separate auth system | Same database, same user table. Adding `is_admin` to JWT payload is simpler than a second auth system. |
| Audit logging | Database table (admin_audit_log) | External service (Datadog, ELK) | Over-engineered for admin action logging. DB table is queryable, portable, and requires no external services. |
| Platform settings | Key-value DB table | Redis | Settings change rarely. DB reads are fast enough. Redis adds infrastructure dependency for no benefit. |
| User class config | YAML file | Database table with admin CRUD | Requirement specifies static tiers. YAML is version-controlled, reviewed in PRs, deployed predictably. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `celery` + `redis` | Overkill for 1 periodic job. Adds 2 infrastructure dependencies. | APScheduler (in-process) |
| `tremor` | Overlaps with shadcn/ui. Both wrap Radix + Tailwind. | Recharts via shadcn chart components |
| `plotly.js` (in admin frontend) | Too heavy for simple metrics charts. Already in public frontend for different purpose. | Recharts (~45KB) |
| `itsdangerous` | Signed tokens unnecessary. Invite tokens validated by DB lookup. | `secrets.token_urlsafe(32)` |
| `turborepo` / `nx` | Monorepo tooling overhead not justified for 2 small frontends. | Copy shared files |
| `fastapi-admin` / `sqladmin` | Auto-generated admin UIs don't match Spectra's custom admin requirements. | Custom admin routers + React frontend |
| `redis` | No caching or session storage needs. Platform settings are low-read. | PostgreSQL (existing) |
| `flower` / `celery-beat` | Only needed with Celery. Not using Celery. | APScheduler |
| `alembic-autogenerate` blindly | 5 new tables + column additions need careful migration ordering. | Write migrations manually or review autogenerated. |
| `RBAC library` (casbin, etc.) | Binary admin/non-admin check. No complex role hierarchy. | Simple `is_admin` boolean check in dependency. |
| `rate limiting library` | Admin API is VPN-only. Rate limiting is a public API concern (future). | Network isolation is the security layer. |

---

## Installation

### Backend (1 new package)

```bash
cd backend

# Add to pyproject.toml dependencies:
# "apscheduler>=3.11.0",

pip install apscheduler
```

### Admin Frontend (new application)

```bash
# Create admin frontend
mkdir admin-frontend
cd admin-frontend

npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Core dependencies (match public frontend versions)
npm install @tanstack/react-query@^5.90.20 @tanstack/react-table@^8.21.3 zustand@^5.0.11
npm install radix-ui@^1.4.3 class-variance-authority@^0.7.1 clsx@^2.1.1 tailwind-merge@^3.4.0
npm install lucide-react@^0.563.0 sonner@^2.0.7 next-themes@^0.4.6

# Admin-specific: charts for dashboard
npm install recharts@^3.7.0

# Dev dependencies
npm install -D @tailwindcss/postcss@^4 tailwindcss@^4 tw-animate-css@^1.4.0
npm install -D @types/node@^20 @types/react@^19 @types/react-dom@^19
```

**Note on Recharts + React 19:** Recharts v3.7.0 may flag a peer dependency warning for `react-is`. If npm install fails, use `npm install recharts@^3.7.0 --legacy-peer-deps`. This is a known issue with Recharts' `react-is` dependency not yet declaring React 19 in its peer range.

### Public Frontend (0 new packages)

```bash
# No changes to public frontend dependencies for v0.5
```

---

## Environment Variables: New Additions

```bash
# .env additions for v0.5

# Split-horizon mode: "public" | "admin" | "dev" (default: "dev")
SPECTRA_MODE=dev

# Admin frontend URL (for CORS and email links)
ADMIN_FRONTEND_URL=http://localhost:3001

# Invite link settings (optional, has defaults)
INVITE_EXPIRY_DAYS=7

# Credit reset settings (optional, has defaults)
CREDIT_RESET_ENABLED=true
CREDIT_RESET_SCHEDULE=weekly  # "weekly" | "monthly" | "manual"
```

---

## Integration Points with Existing Stack

### 1. JWT Token Payload (Extended)

```python
# Current payload: {"sub": user_id, "exp": expiry}
# v0.5 payload: {"sub": user_id, "exp": expiry, "is_admin": True/False}

# Admin dependency (new):
async def get_current_admin(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

### 2. Email Service (Extended)

```python
# Existing: password_reset.html template
# New: invitation.html template (same Jinja2 + aiosmtplib pattern)
# New: invitation_accepted.html template (optional notification to admin)
```

### 3. Credit Deduction (Chat Service Integration)

```python
# In existing chat router (chat.py), before processing message:
# 1. Check user.credit_balance >= credit_cost
# 2. If insufficient: return 402 Payment Required
# 3. If sufficient: deduct and create credit_transaction record
# This modifies the existing chat flow but uses existing models/services pattern
```

### 4. Signup Flow (Modified)

```python
# In existing auth router (auth.py), signup endpoint:
# 1. Check platform_settings["allow_public_signup"]
# 2. If disabled: check for valid invite token in request
# 3. If invite: validate token, mark as accepted, proceed with signup
# 4. Assign default user_class from platform_settings
# 5. Set initial credit_balance from user_class config
```

### 5. APScheduler Lifespan Integration

```python
# In main.py lifespan (existing pattern):
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...

    # Credit reset scheduler (admin/dev mode only)
    if settings.spectra_mode in ("admin", "dev"):
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            reset_credits_job,
            trigger="cron",
            day_of_week="mon",  # Weekly on Monday (configurable)
            hour=0, minute=0,
            timezone="UTC"
        )
        scheduler.start()
        app.state.scheduler = scheduler

    yield

    # Shutdown scheduler
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
    await engine.dispose()
```

---

## Version Compatibility Matrix

| Package | Version | Python/Node | Compatibility Notes |
|---------|---------|-------------|---------------------|
| `apscheduler` | >=3.11.0 | Python 3.12 | AsyncIOScheduler works with uvicorn's event loop |
| `recharts` | ^3.7.0 | React 19 | May need `--legacy-peer-deps` for `react-is` peer dep |
| `next` | 16.1.6 | Node 20+ | Same version as public frontend |
| `@tanstack/react-query` | ^5.90.20 | React 19 | Verified compatible (already in use) |
| `@tanstack/react-table` | ^8.21.3 | React 19 | Verified compatible (already in use) |
| `zustand` | ^5.0.11 | React 19 | Verified compatible (already in use) |
| `radix-ui` | ^1.4.3 | React 19 | Verified compatible (already in use) |

---

## Project Structure After v0.5

```
spectra-dev/
  backend/
    app/
      config.py                    # + SPECTRA_MODE, ADMIN_FRONTEND_URL
      main.py                      # + conditional router mounting, scheduler
      models/
        user.py                    # + is_admin, user_class, credit_balance
        platform_settings.py       # NEW
        invitation.py              # NEW
        credit_transaction.py      # NEW
        admin_audit_log.py         # NEW
      routers/
        admin/                     # NEW directory
          __init__.py
          auth.py                  # Admin login
          users.py                 # User CRUD
          settings.py              # Platform settings
          invitations.py           # Invite management
          credits.py               # Credit management
          dashboard.py             # Dashboard metrics
      services/
        admin/                     # NEW directory
          user_management.py
          invitation.py
          credit.py
          audit.py
          dashboard.py
      templates/
        email/
          password_reset.html      # existing
          invitation.html          # NEW
      cli/
        seed_admin.py              # NEW: CLI admin seed
    config/
      user_classes.yaml            # NEW: tier definitions
    alembic/
      versions/
        xxx_add_admin_portal.py    # NEW migration(s)
  frontend/                        # UNCHANGED
  admin-frontend/                  # NEW
    src/
      app/
        layout.tsx
        page.tsx                   # Dashboard
        login/page.tsx
        users/page.tsx
        users/[id]/page.tsx
        invitations/page.tsx
        settings/page.tsx
        credits/page.tsx
      components/
        ui/                        # Copied from frontend
        admin/
          dashboard-charts.tsx
          user-table.tsx
          invite-form.tsx
          credit-adjust-dialog.tsx
          audit-log.tsx
      lib/
        api-client.ts              # Admin API client
        auth.ts                    # Admin auth hooks
        utils.ts                   # Copied from frontend
```

---

## Sources

**APScheduler:**
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) -- v3.11.2 current, actively maintained
- [FastAPI + APScheduler patterns](https://sentry.io/answers/schedule-tasks-with-fastapi/) -- Lifespan integration pattern
- [APScheduler GitHub Discussions](https://github.com/agronholm/apscheduler/discussions/830) -- FastAPI integration

**Recharts:**
- [Recharts npm](https://www.npmjs.com/package/recharts) -- v3.7.0 current
- [shadcn/ui Chart Component](https://ui.shadcn.com/docs/components/radix/chart) -- Built on Recharts
- [Recharts React 19 Support](https://github.com/recharts/recharts/issues/4558) -- Supported via alpha, now stable in v3

**shadcn/ui Charts:**
- [shadcn/ui Charts](https://ui.shadcn.com/charts/area) -- Official chart components using Recharts
- [shadcn Charts Discussion](https://github.com/shadcn-ui/ui/discussions/4133) -- Community recommendations

**Invite Token Security:**
- [Python secrets module](https://docs.python.org/3/library/secrets.html) -- `token_urlsafe()` documentation
- [Secure token generation](https://blog.miguelgrinberg.com/post/the-new-way-to-generate-secure-tokens-in-python) -- Best practices

**Split-Horizon / Multi-App:**
- [Next.js Multi-Zones](https://nextjs.org/docs/pages/guides/multi-zones) -- Official multi-app documentation
- [Monorepo considerations](https://medium.com/@techbysundaram/managing-two-frontend-apps-with-one-monorepo-a-practical-next-js-setup-b518cf390d24) -- Why monorepo may not be needed

---

*Stack research for: Spectra v0.5 Admin Portal*
*Researched: 2026-02-16*
*Confidence: HIGH -- One new backend dependency (APScheduler, well-established). One new frontend library (Recharts, shadcn-recommended). Everything else uses existing stack or Python stdlib. Split-horizon is pure configuration. No exotic technologies.*
