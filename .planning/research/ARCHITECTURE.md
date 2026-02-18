# Architecture Patterns: Admin Portal Integration (v0.5)

**Domain:** Admin portal for AI-powered data analytics platform
**Researched:** 2026-02-16
**Confidence:** HIGH (based on direct codebase analysis of existing Spectra v0.4 source code)

---

## Executive Summary

The admin portal integrates into the existing Spectra platform through three layers: (1) same FastAPI codebase with mode-gated router mounting via `SPECTRA_MODE` env var, (2) five new database tables plus two column additions to the existing `users` table in the same Alembic migration chain, and (3) a separate `admin-frontend/` Next.js application independent from the existing `frontend/`.

The core architectural principle is **shared models and services, isolated entry points**. Admin routers call the same database layer and reuse existing services (auth, email) but live in their own namespace (`/api/admin/`). The most critical integration point is credit deduction at the chat message layer -- credits must be checked and deducted BEFORE the expensive LangGraph agent pipeline runs, at the router level in `routers/chat.py`, not inside `ChatService.create_message`.

Six components are modified (main.py, config.py, dependencies.py, models/user.py, routers/auth.py, routers/chat.py). Everything else is additive -- new models, new services, new router package, new frontend app. The agent system (`agents/`) is completely untouched.

---

## Current Architecture (Before -- v0.4)

```
frontend/ (Next.js 16, port 3000)
    |
    v
backend/ (FastAPI, port 8000)
    |
    +-- routers/: auth, chat, chat_sessions, files, search, health
    +-- services/: auth, chat, chat_session, file, agent_service, email, search
    +-- models/: User, File, ChatMessage, ChatSession, PasswordResetToken, SearchQuota
    +-- agents/: LangGraph pipeline (manager, coding, code_checker, execute, data_analysis, visualization)
    +-- config/: prompts.yaml, llm_providers.yaml, allowlist.yaml, search.yaml, settings.yaml
    |
    v
PostgreSQL (single database, Alembic migrations)
```

**Key source files affected by v0.5:**
- `backend/app/main.py` -- Router mounting, CORS, lifespan
- `backend/app/config.py` -- Settings class (Pydantic BaseSettings)
- `backend/app/dependencies.py` -- `CurrentUser` dependency, `DbSession`
- `backend/app/models/user.py` -- User model (id, email, hashed_password, first_name, last_name, is_active)
- `backend/app/routers/auth.py` -- Signup, login, refresh, password reset
- `backend/app/routers/chat.py` -- Chat query, stream, context management
- `backend/app/services/chat.py` -- `ChatService.create_message`, `create_session_message`
- `backend/app/schemas/user.py` -- `UserResponse` Pydantic model

---

## Recommended Architecture (After -- v0.5)

```
frontend/ (Next.js 16, port 3000)        admin-frontend/ (Next.js, port 3001)
    |                                          |
    v                                          v
backend/ (FastAPI, port 8000, SPECTRA_MODE=dev serves all)
    |
    +-- SPECTRA_MODE gating in main.py:
    |     public mode: auth, chat, files, sessions, search, health
    |     admin mode:  /api/admin/* routers + health
    |     dev mode:    all of the above
    |
    +-- routers/:
    |     auth.py (MODIFIED: signup toggle + invite token)
    |     chat.py (MODIFIED: credit check before query)
    |     chat_sessions.py, files.py, search.py, health.py (unchanged)
    |     admin/                    <-- NEW package
    |       __init__.py             (aggregates sub-routers)
    |       auth.py, dashboard.py, users.py, settings.py, invitations.py, credits.py
    |
    +-- services/:
    |     auth.py, chat.py, chat_session.py, file.py, agent_service.py, email.py (existing)
    |     credit.py                 <-- NEW: shared credit check + deduction
    |     admin/                    <-- NEW package
    |       audit.py, settings.py, user_management.py, invitation.py, credit.py
    |
    +-- models/:
    |     user.py (MODIFIED: +is_admin, +user_class)
    |     platform_settings.py      <-- NEW
    |     user_credit.py            <-- NEW
    |     credit_transaction.py     <-- NEW
    |     invitation.py             <-- NEW
    |     admin_audit_log.py        <-- NEW
    |
    +-- agents/: UNCHANGED (no admin awareness)
    +-- config/:
    |     user_classes.yaml         <-- NEW
    |     (all others unchanged)
    |
    v
PostgreSQL (same database, extended with 5 new tables + 2 column additions)
```

---

## Component Boundaries

### NEW Components

| Component | Location | Responsibility | Communicates With |
|-----------|----------|---------------|-------------------|
| Admin router package | `routers/admin/__init__.py` | Aggregates all admin sub-routers under `/api/admin` | `main.py` mounts single combined router |
| `admin/auth.py` router | `routers/admin/auth.py` | Admin login (same JWT, validates `is_admin`) | `dependencies.py` (`CurrentAdmin`), `services/auth.py` |
| `admin/users.py` router | `routers/admin/users.py` | User list/search/filter, activate/deactivate, class change, delete | `services/admin/user_management.py` |
| `admin/settings.py` router | `routers/admin/settings.py` | Platform settings CRUD | `services/admin/settings.py` |
| `admin/invitations.py` router | `routers/admin/invitations.py` | Invite create/revoke/resend/list | `services/admin/invitation.py`, `services/email.py` |
| `admin/credits.py` router | `routers/admin/credits.py` | Credit view/adjust/bulk-adjust/history | `services/admin/credit.py` |
| `admin/dashboard.py` router | `routers/admin/dashboard.py` | Aggregate metrics (read-only) | All models via direct queries |
| `services/credit.py` | `services/credit.py` | Credit check + atomic deduction (shared by chat router and admin) | `UserCredit`, `CreditTransaction` models |
| `services/admin/audit.py` | `services/admin/audit.py` | Write audit log entries | `AdminAuditLog` model |
| `services/admin/settings.py` | `services/admin/settings.py` | Get/set platform settings with cache | `PlatformSettings` model |
| `services/admin/user_management.py` | `services/admin/user_management.py` | Admin user operations | `User`, `UserCredit` models |
| `services/admin/invitation.py` | `services/admin/invitation.py` | Invitation lifecycle | `Invitation` model, `services/email.py` |
| `services/admin/credit.py` | `services/admin/credit.py` | Admin credit adjustment, history queries | `UserCredit`, `CreditTransaction` models |
| Admin frontend | `admin-frontend/` | Separate Next.js SPA for admin UI | Backend `/api/admin/*` endpoints only |
| `user_classes.yaml` | `backend/app/config/user_classes.yaml` | Static tier definitions (free/standard/premium) | `services/admin/settings.py` reads with DB overrides |

### MODIFIED Components

| Component | Location | What Changes | Risk |
|-----------|----------|-------------|------|
| `main.py` | `backend/app/main.py` | Add `SPECTRA_MODE` gating for router mounting; mode-aware CORS origins | MEDIUM -- central file, must not break existing routes |
| `config.py` | `backend/app/config.py` | Add `spectra_mode: str = "dev"` and `admin_frontend_url: str` settings | LOW -- additive fields with defaults |
| `dependencies.py` | `backend/app/dependencies.py` | Add `CurrentAdmin` dependency (wraps `CurrentUser` + `is_admin` check) | LOW -- additive, existing deps unchanged |
| `models/user.py` | `backend/app/models/user.py` | Add `is_admin: Mapped[bool]` (default False) and `user_class: Mapped[str]` (default "free") | LOW -- additive columns with defaults |
| `schemas/user.py` | `backend/app/schemas/user.py` | Add `is_admin` and `user_class` to `UserResponse` | LOW -- additive fields |
| `routers/auth.py` | `backend/app/routers/auth.py` | Modify `signup` to check `allow_public_signup` setting and accept invite tokens | MEDIUM -- touches critical auth flow |
| `routers/chat.py` | `backend/app/routers/chat.py` | Insert credit check before `agent_service.run_chat_query()` in query and stream endpoints | HIGH -- touches most critical user-facing flow |

### UNCHANGED Components

| Component | Why Unchanged |
|-----------|--------------|
| `agents/` (entire LangGraph pipeline) | Agent system has no admin awareness; credit check happens before agents run |
| `services/file.py` | File management orthogonal to admin features |
| `services/chat.py` | Message CRUD unchanged; credit gating at router level, not service level |
| `services/agent_service.py` | Agent orchestration unchanged |
| `routers/chat_sessions.py` | Session CRUD unchanged |
| `routers/files.py` | File endpoints unchanged |
| `routers/search.py` | Search functionality unchanged |
| `routers/health.py` | Health check unchanged (mounted in all modes) |
| `frontend/` | Minimal changes only -- invite signup page, credit display (deferred to Phase 4/6) |

---

## New Database Models

### Entity Relationship Additions

```
users (MODIFIED)
  + is_admin: Boolean (default false)
  + user_class: String/Enum (default 'free')
  |
  +-- 1:1 --> user_credits
  |             id, user_id (FK unique), balance (Float), last_reset_at, created_at
  |
  +-- 1:N --> credit_transactions
  |             id, user_id (FK), amount (Float), transaction_type, reason,
  |             balance_after, admin_id (FK nullable), model_used (nullable), created_at
  |
  +-- 1:N --> invitations (as admin_id -- who created the invite)
  |             id, email, token_hash, admin_id (FK), user_class,
  |             status ('pending'|'accepted'|'expired'|'revoked'),
  |             expires_at, accepted_at, created_at
  |
  +-- 1:N --> admin_audit_log (as admin_id -- who performed the action)
                id, admin_id (FK), action, target_type, target_id,
                details (JSON), ip_address, created_at

platform_settings (NEW, standalone)
  id, key (String unique), value (JSON), updated_by (FK users nullable), updated_at
```

### Model Definitions

**User model additions (`backend/app/models/user.py`):**
```python
# Add to existing User class:
is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
user_class: Mapped[str] = mapped_column(String(20), default="free")  # free, standard, premium
```

**`backend/app/models/platform_settings.py` (NEW):**
```python
class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

**`backend/app/models/user_credit.py` (NEW):**
```python
class UserCredit(Base):
    __tablename__ = "user_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    balance: Mapped[float] = mapped_column(default=0.0)
    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

**`backend/app/models/credit_transaction.py` (NEW):**
```python
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[float] = mapped_column(nullable=False)  # negative=deduction, positive=grant
    transaction_type: Mapped[str] = mapped_column(String(30))  # usage, admin_adjust, reset, signup_grant
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    balance_after: Mapped[float] = mapped_column(nullable=False)
    admin_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)  # future: per-model costs
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

**`backend/app/models/invitation.py` (NEW):**
```python
class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user_class: Mapped[str] = mapped_column(String(20), default="free")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, expired, revoked
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

**`backend/app/models/admin_audit_log.py` (NEW):**
```python
class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)  # 'user.deactivate', 'credits.adjust'
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'user', 'invitation', 'settings'
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
```

---

## Critical Data Flow Changes

### 1. Credit Deduction at Chat Message Layer (HIGHEST RISK)

Credits must be checked and deducted BEFORE the LangGraph agent pipeline starts. Agents are expensive (multiple LLM calls, E2B sandbox). You cannot afford to run the pipeline and then discover the user has no credits.

**Current flow:**
```
Router (chat.py query_with_ai) --> agent_service.run_chat_query() --> Agent pipeline --> Save message
```

**New flow:**
```
Router (chat.py query_with_ai)
  --> credit_service.check_and_deduct(user_id, cost)  <-- NEW: deduct BEFORE agent runs
  --> agent_service.run_chat_query()                    (unchanged)
  --> Agent pipeline                                    (unchanged)
  --> Save message                                      (unchanged)
  |
  +-- On InsufficientCreditsError: HTTP 402, no agent invocation
```

**Why deduct-before-execute (not reserve-then-confirm):** The reservation pattern adds complexity for marginal benefit. In practice, API credit systems charge for the attempt, not the result. If the agent fails, the user still consumed compute resources. This matches how OpenAI, Anthropic, and every LLM API works.

**Implementation in `services/credit.py` (NEW shared service):**
```python
class CreditService:
    @staticmethod
    async def check_and_deduct(
        db: AsyncSession, user_id: UUID, cost: float
    ) -> CreditTransaction:
        """Atomically check balance and deduct credits.

        Uses SELECT FOR UPDATE to prevent race conditions from concurrent
        chat messages overdrawing the balance.
        """
        result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = result.scalar_one_or_none()

        if credit is None or credit.balance < cost:
            raise InsufficientCreditsError(
                balance=credit.balance if credit else 0.0,
                required=cost
            )

        credit.balance -= cost
        transaction = CreditTransaction(
            user_id=user_id,
            amount=-cost,
            transaction_type="usage",
            balance_after=credit.balance,
        )
        db.add(transaction)
        await db.flush()  # flush within caller's transaction
        return transaction
```

**Hook point in `routers/chat.py` -- four endpoints need credit checks:**
1. `POST /{file_id}/query` (query_with_ai)
2. `POST /{file_id}/stream` (stream_query)
3. `POST /sessions/{session_id}/query` (session_query_with_ai)
4. `POST /sessions/{session_id}/stream` (session_stream_query)

```python
# Added before agent_service call in each endpoint:
from app.services.credit import CreditService, InsufficientCreditsError
from app.services.admin.settings import get_platform_setting

credit_cost = await get_platform_setting(db, "default_credit_cost", default=1.0)
try:
    await CreditService.check_and_deduct(db, current_user.id, credit_cost)
except InsufficientCreditsError as e:
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=f"Insufficient credits. Balance: {e.balance}, Required: {e.required}"
    )
```

**Why NOT deduct inside `ChatService.create_message`:** The existing `create_message` and `create_session_message` are called for BOTH user messages AND assistant responses. Hooking credit logic there would either double-charge (deduct on both) or require role-checking in a data layer method, violating separation of concerns. The router is the correct boundary because it represents a user-initiated action.

### 2. Mode-Gated Router Mounting (main.py)

```python
# In main.py -- replace static router inclusion
settings = get_settings()

# Always mount health (needed for load balancer checks in all modes)
app.include_router(health.router)

if settings.spectra_mode in ("public", "dev"):
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(chat.router)
    app.include_router(chat_sessions.router)
    app.include_router(search.router)

if settings.spectra_mode in ("admin", "dev"):
    from app.routers.admin import admin_router
    app.include_router(admin_router, prefix="/api/admin")
```

**CORS must also be mode-aware:**
```python
origins = []
if settings.spectra_mode in ("public", "dev"):
    origins.extend(settings.get_cors_origins())      # existing frontend origins
if settings.spectra_mode in ("admin", "dev"):
    origins.append(settings.admin_frontend_url)       # http://localhost:3001

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Admin Auth Dependency

Reuse the existing JWT pipeline. Do NOT create a separate auth system.

```python
# In dependencies.py -- add after existing CurrentUser
async def get_current_admin(
    current_user: CurrentUser,
) -> User:
    """Verify current user has admin privileges.

    Depends on CurrentUser (which handles JWT validation + user lookup).
    Only adds the is_admin check.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

CurrentAdmin = Annotated[User, Depends(get_current_admin)]
```

Every admin router endpoint uses `CurrentAdmin` instead of `CurrentUser`. This provides defense-in-depth: even if admin routers are accidentally mounted in public mode, non-admin users get 403.

### 4. Signup Flow Modification

The existing `POST /auth/signup` must check the `allow_public_signup` platform setting and accept invite tokens.

```python
# In routers/auth.py signup endpoint -- add before user creation:
from app.services.admin.settings import get_platform_setting

allow_signup = await get_platform_setting(db, "allow_public_signup", default=True)
invite_token = signup_data.invite_token  # NEW optional field on SignupRequest schema

if not allow_signup and not invite_token:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Registration is currently invite-only"
    )

if invite_token:
    invitation = await InvitationService.validate_and_accept(db, invite_token, signup_data.email)
    # invitation.user_class overrides default
```

The `SignupRequest` schema gets one new optional field: `invite_token: str | None = None`. This is backward-compatible -- existing signup requests without the field continue to work.

### 5. Audit Logging Pattern

Implement as an explicit service function called in admin routers, NOT as middleware. Middleware-based audit logging is fragile: hard to capture semantic action names, target details, and admin identity reliably from raw request/response data.

```python
# In services/admin/audit.py
async def log_admin_action(
    db: AsyncSession,
    admin_id: UUID,
    action: str,                    # e.g., "user.deactivate", "credits.adjust", "settings.update"
    target_type: str | None = None, # e.g., "user", "invitation", "settings"
    target_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()  # flush, NOT commit -- let caller's transaction handle atomicity
    return entry
```

**Critical: audit log and business action in the same transaction:**
```python
# Good: atomic
user.is_active = False
await log_admin_action(db, admin.id, "user.deactivate", target_type="user", target_id=user_id)
await db.commit()  # both succeed or both roll back

# Bad: split transactions
user.is_active = False
await db.commit()
await log_admin_action(db, admin.id, "user.deactivate", ...)
await db.commit()  # if this fails, action is unlogged
```

### 6. Platform Settings Service

Key-value store with in-memory cache. Settings change rarely (admin updates them occasionally), so a 30-second TTL avoids DB queries on every chat message (for credit cost lookups).

```python
# In services/admin/settings.py
_settings_cache: dict[str, tuple[Any, datetime]] = {}
CACHE_TTL = timedelta(seconds=30)

async def get_platform_setting(db: AsyncSession, key: str, default: Any = None) -> Any:
    """Get platform setting with 30-second in-memory cache."""
    now = datetime.utcnow()
    if key in _settings_cache:
        value, cached_at = _settings_cache[key]
        if now - cached_at < CACHE_TTL:
            return value

    result = await db.execute(
        select(PlatformSettings.value).where(PlatformSettings.key == key)
    )
    row = result.scalar_one_or_none()
    value = row if row is not None else default
    _settings_cache[key] = (value, now)
    return value
```

**Config resolution order** (for user class credits, credit costs, etc.):
1. Check `platform_settings` table for the key
2. Fall back to `user_classes.yaml` config default
3. Fall back to hardcoded default

This means the system works immediately after deployment with just the YAML -- no need to seed the `platform_settings` table.

---

## Admin Router Package Structure

```python
# backend/app/routers/admin/__init__.py
from fastapi import APIRouter
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .users import router as users_router
from .settings import router as settings_router
from .invitations import router as invitations_router
from .credits import router as credits_router

admin_router = APIRouter(tags=["Admin"])
admin_router.include_router(auth_router, prefix="/auth", tags=["Admin Auth"])
admin_router.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])
admin_router.include_router(users_router, prefix="/users", tags=["Admin Users"])
admin_router.include_router(settings_router, prefix="/settings", tags=["Admin Settings"])
admin_router.include_router(invitations_router, prefix="/invitations", tags=["Admin Invitations"])
admin_router.include_router(credits_router, prefix="/credits", tags=["Admin Credits"])
```

Result: `main.py` mounts one router: `app.include_router(admin_router, prefix="/api/admin")`. All admin endpoints are at `/api/admin/auth/...`, `/api/admin/users/...`, etc.

---

## Admin Frontend Architecture

```
admin-frontend/
  src/
    app/                    # Next.js App Router pages
      layout.tsx            # Admin shell (sidebar nav, auth check)
      login/page.tsx
      dashboard/page.tsx
      users/
        page.tsx            # User list with search/filter
        [id]/page.tsx       # User detail (profile, credits, history)
      settings/page.tsx     # Platform settings form
      invitations/page.tsx  # Invitation list + create form
      credits/page.tsx      # Credit overview, bulk actions
      audit/page.tsx        # Audit log viewer with filters
    lib/
      api-client.ts         # Admin API client (same pattern as frontend/src/lib/api-client.ts)
      query-client.ts       # TanStack Query client
    components/
      admin/                # Admin-specific UI components
    hooks/                  # Custom hooks
    types/                  # TypeScript types for admin API
```

**Key decisions:**
- Same stack as existing frontend: Next.js, TanStack Query, shadcn/ui -- consistency and developer familiarity
- SPA mode is fine (no SSR needed for admin) -- use `"use client"` throughout
- Share NO runtime code with `frontend/` -- independent apps with independent deployments and bundles
- Copy the `api-client.ts` pattern but configure base URL to `/api/admin/`

**Why a separate app, not a route in existing frontend:**
1. **Deployment isolation** -- admin frontend deploys on Tailscale only; a route in the public frontend would expose admin code in the public bundle
2. **Bundle isolation** -- admin components never ship to public users
3. **Independent iteration** -- admin UI evolves without touching public app builds or test suites

---

## Patterns to Follow

### Pattern 1: Admin Router Package with Sub-Router Aggregation

**What:** Bundle all admin routers into a single package with a combined router exported from `__init__.py`.
**When:** Always.
**Why:** Keeps `main.py` clean (one line to mount all admin routes). Matches how the existing codebase organizes routers by functional area.

### Pattern 2: Atomic Admin Operations (Audit + Action in Same Transaction)

**What:** Always call `log_admin_action()` with `flush()` inside the same transaction as the business operation, then `commit()` once.
**When:** Every admin write operation.
**Why:** Ensures no admin action goes unlogged. If the audit write fails, the business action rolls back too.

### Pattern 3: SELECT FOR UPDATE on Credit Operations

**What:** Use `select(...).with_for_update()` for all credit balance mutations.
**When:** Every credit deduction or adjustment.
**Why:** Prevents race conditions where two concurrent chat messages could overdraw credits. PostgreSQL row-level locking ensures serialized access to the balance row.

### Pattern 4: Config File + DB Override for Settings

**What:** Static defaults in `user_classes.yaml`, runtime overrides in `platform_settings` table.
**When:** For user class credits, credit costs, and any admin-configurable setting.
**Why:** System works with just YAML on first deploy. Admins can override without code changes or redeployment. DB overrides take precedence.

### Pattern 5: Credit Record on User Creation

**What:** When a user signs up, create a `UserCredit` row with initial balance based on their `user_class` allocation.
**When:** In the signup flow (both public and invite-based).
**Why:** Every user must have a credit record before they can send messages. Creating it at signup avoids null-check complexity throughout the credit service.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Middleware-Based Admin Auth

**What:** Using FastAPI middleware to check `is_admin` on all `/api/admin/` paths.
**Why bad:** Middleware runs before dependency injection, so you do not have the `User` object. You would need to duplicate JWT parsing and DB lookup logic in middleware, creating two parallel auth paths.
**Instead:** `CurrentAdmin` dependency on every admin endpoint. Reuses the existing auth pipeline.

### Anti-Pattern 2: Credit Deduction in ChatService.create_message

**What:** Hooking credit checks into the message persistence layer.
**Why bad:** `create_message` is called for both user messages AND assistant responses. Credit logic in the data layer violates separation of concerns and risks double-charging.
**Instead:** Deduct credits at the router level, before calling `agent_service.run_chat_query()`.

### Anti-Pattern 3: Separate Auth System for Admin

**What:** Creating a parallel JWT/session system for admin users.
**Why bad:** Doubles the auth surface area, requires separate token refresh logic, and creates confusion about which token to use when.
**Instead:** Same JWT pipeline, same `users` table, `is_admin` flag checked by `CurrentAdmin` dependency.

### Anti-Pattern 4: Sharing Components Between Frontend and Admin Frontend

**What:** Creating a shared component library (`packages/shared-ui/`) used by both apps.
**Why bad:** Creates coupling between independently deployed apps. Shared library changes require coordinated deployments. Premature abstraction for a small admin UI.
**Instead:** Copy the api-client pattern and use shadcn/ui in both. These apps have different audiences, different deployment lifecycles, and the admin app is small enough that duplication is preferable.

### Anti-Pattern 5: Storing User Class Definitions in Database

**What:** A `user_classes` table that admins can add/remove tiers from at runtime.
**Why bad:** Tier changes affect code paths (enum validation, Stripe integration in future, feature gating). Adding a tier at runtime without corresponding code changes leads to undefined behavior.
**Instead:** Tiers defined in `user_classes.yaml` (require deploy to add new tier). Credit amounts per tier are overridable via `platform_settings`.

### Anti-Pattern 6: Admin-Only Database

**What:** Separate PostgreSQL database for admin data.
**Why bad:** Admin actions need to read and write user data that lives in the main database. A separate database would require cross-database queries or data sync.
**Instead:** Same database, new tables in the same schema, same Alembic migration chain.

---

## Suggested Build Order

Build order follows dependency chains. Each phase produces something independently testable.

### Phase 1: Foundation (Database + Config + Mode Gating)

**Build:**
1. Add `spectra_mode: str = "dev"` and `admin_frontend_url: str = "http://localhost:3001"` to `config.py`
2. Add `is_admin` (Boolean, default False) and `user_class` (String, default "free") to User model
3. Create all 5 new model files (platform_settings, user_credit, credit_transaction, invitation, admin_audit_log)
4. Register new models in `models/__init__.py` for Alembic discovery
5. Generate single Alembic migration
6. Create `user_classes.yaml` config file
7. Create `routers/admin/__init__.py` package structure (empty sub-routers)
8. Implement `SPECTRA_MODE` gating in `main.py`
9. Add `CurrentAdmin` dependency to `dependencies.py`
10. Create `services/admin/` package with `audit.py` and `settings.py`
11. Create admin seed CLI command (`python -m app.cli seed-admin --email admin@example.com`)
12. Update `schemas/user.py` to include `is_admin` and `user_class`

**Why first:** Everything else depends on schema, config, mode gating, and admin auth. Pure backend, fully testable via pytest and API calls.

**Testable:** `SPECTRA_MODE=admin` starts with only health router + admin routes. `SPECTRA_MODE=dev` shows all. `/api/admin/` returns 403 for non-admin JWT. Admin seed CLI creates admin user.

### Phase 2: Credit System

**Build:**
1. Create `services/credit.py` (shared: `check_and_deduct`, `InsufficientCreditsError`)
2. Create `services/admin/credit.py` (admin: adjust, bulk-adjust, balance view, history)
3. Hook credit check into `routers/chat.py` -- all four query/stream endpoints
4. Create `UserCredit` record on user signup (modify auth service)
5. Create `routers/admin/credits.py` (admin endpoints)
6. Seed `default_credit_cost` platform setting

**Why second:** Credit deduction touches the most critical user-facing flow (chat). Building early surfaces integration issues before other features add complexity. Admin credit endpoints enable testing (manually grant credits, verify deduction).

**Testable:** Chat message deducts credits. 402 returned when balance insufficient. Admin adjusts credits via API. Credit transaction history records all operations.

### Phase 3: User Management + Platform Settings

**Build:**
1. Create `services/admin/user_management.py` (list, search, filter, activate, deactivate, change class, delete)
2. Create `routers/admin/users.py`
3. Create `routers/admin/settings.py` (CRUD)
4. Implement `allow_public_signup` check in existing `routers/auth.py` signup
5. Create `routers/admin/dashboard.py` (aggregate queries)

**Why third:** Depends on Phase 1 (schema, admin auth) but not Phase 2. Built after Phase 2 so user class changes can immediately affect credit allocations.

**Testable:** Admin lists/searches/filters users. Changing user class updates credit allocation. Toggling `allow_public_signup` blocks/allows public registration. Dashboard shows aggregate metrics.

### Phase 4: Invitation System

**Build:**
1. Create `services/admin/invitation.py` (create, validate, accept, revoke, resend, list expired)
2. Create invitation email template (reuse existing `services/email.py` patterns)
3. Create `routers/admin/invitations.py`
4. Modify `routers/auth.py` signup to accept and validate invite tokens
5. Add invite signup page to public frontend (`/signup?invite=TOKEN`)

**Why fourth:** Depends on signup control toggle (Phase 3), email service (existing), and User model changes (Phase 1). First phase that requires a public frontend change.

**Testable:** Admin creates invite via API. Email sent. User clicks link, registers with pre-filled email. Invite marked accepted. Resend and revoke work.

### Phase 5: Audit Log Completion + Dashboard Polish

**Build:**
1. Wire `log_admin_action()` calls into ALL admin endpoints from Phases 2-4
2. Create audit log viewer endpoint (list, filter by action/admin/date range)
3. Polish dashboard aggregate queries (add credit distribution, low-credit users)

**Why fifth:** Audit log viewer is useful only after all admin actions are logging. Dashboard polish requires all data tables to exist.

**Testable:** Every admin action appears in audit log. Audit viewer filters work. Dashboard shows complete metrics.

### Phase 6: Admin Frontend

**Build:**
1. Initialize `admin-frontend/` Next.js project (shadcn/ui, TanStack Query, Zustand)
2. Admin login page
3. Dashboard page (charts, metrics)
4. User management pages (list with search/filter, detail view)
5. Platform settings page (form with save)
6. Invitations page (list + create dialog)
7. Credit management views (user credit detail, bulk adjust)
8. Audit log viewer (table with date/action/admin filters)

**Why last:** Frontend is a pure consumer of the API built in Phases 1-5. All endpoints are stable and tested before UI work begins.

**Alternative:** Phase 6 can run in parallel with Phases 2-5 if a second developer builds UI against API stubs/mocks.

**Testable:** Full admin portal accessible at `localhost:3001`.

---

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Credit deduction concurrency | SELECT FOR UPDATE, fine | Still fine (row-level lock, microseconds) | Consider Redis-based credit balance caching |
| Platform settings reads | DB hit per request (fast) | 30-second cache handles load | Move to Redis with pub/sub invalidation |
| Audit log table growth | Negligible | ~100K rows/month, index on created_at | Partition by month, archive old data |
| Dashboard aggregation queries | Direct COUNT/SUM queries | Add materialized views or cached metrics | Pre-computed metrics table, updated by cron |
| User list with search | LIKE queries, fine | Add pg_trgm GIN index for fuzzy search | Elasticsearch for full-text |
| Invitation token lookup | Hash index, instant | Same | Same (invites are low-volume) |

---

## Migration Strategy

**Single Alembic migration** for all v0.5 schema changes because:
1. All five tables are new (no data migration risk)
2. The two User column additions are backward-compatible (both have defaults)
3. Atomic: one migration to apply, one to roll back

```bash
alembic revision --autogenerate -m "add_admin_portal_tables_and_user_extensions"

# The migration creates:
# 1. users.is_admin (Boolean, default=False, server_default=false)
# 2. users.user_class (String(20), default='free', server_default='free')
# 3. platform_settings table
# 4. user_credits table
# 5. credit_transactions table
# 6. invitations table
# 7. admin_audit_log table
```

After migration, existing users get `is_admin=false` and `user_class='free'` via server defaults. Existing UserCredit rows need to be backfilled for existing users -- include a data migration step:

```python
# In the migration's upgrade():
# After creating user_credits table, backfill for existing users
op.execute("""
    INSERT INTO user_credits (id, user_id, balance, created_at)
    SELECT gen_random_uuid(), id, 10.0, NOW()
    FROM users
    WHERE id NOT IN (SELECT user_id FROM user_credits)
""")
```

---

## Complete File Structure

```
backend/app/
  config.py                              # MODIFIED: +spectra_mode, +admin_frontend_url
  main.py                                # MODIFIED: mode-gated routing, mode-aware CORS
  dependencies.py                        # MODIFIED: +CurrentAdmin dependency
  models/
    user.py                              # MODIFIED: +is_admin, +user_class columns
    platform_settings.py                 # NEW
    user_credit.py                       # NEW
    credit_transaction.py                # NEW
    invitation.py                        # NEW
    admin_audit_log.py                   # NEW
  schemas/
    user.py                              # MODIFIED: +is_admin, +user_class in UserResponse
    admin/                               # NEW package
      __init__.py
      users.py                           # UserListResponse, UserDetailResponse, etc.
      settings.py                        # PlatformSettingResponse, UpdateSettingRequest
      invitations.py                     # InvitationCreate, InvitationResponse, etc.
      credits.py                         # CreditAdjustRequest, CreditHistoryResponse, etc.
      dashboard.py                       # DashboardMetrics, etc.
  routers/
    auth.py                              # MODIFIED: signup toggle + invite token
    chat.py                              # MODIFIED: credit check before query (4 endpoints)
    admin/                               # NEW package
      __init__.py                        # Aggregates sub-routers into admin_router
      auth.py                            # POST /api/admin/auth/login
      dashboard.py                       # GET /api/admin/dashboard/metrics
      users.py                           # GET/PATCH/DELETE /api/admin/users/...
      settings.py                        # GET/PUT /api/admin/settings/...
      invitations.py                     # GET/POST/PATCH /api/admin/invitations/...
      credits.py                         # GET/POST /api/admin/credits/...
  services/
    credit.py                            # NEW: shared check_and_deduct
    admin/                               # NEW package
      __init__.py
      audit.py                           # log_admin_action()
      settings.py                        # get/set_platform_setting() with cache
      user_management.py                 # list, search, activate, deactivate, etc.
      invitation.py                      # create, validate, accept, revoke, resend
      credit.py                          # admin adjust, bulk adjust, history queries
  config/
    user_classes.yaml                    # NEW: tier definitions

admin-frontend/                          # NEW: entire directory (Phase 6)
  package.json
  next.config.js
  src/
    app/
      layout.tsx
      login/page.tsx
      dashboard/page.tsx
      users/page.tsx, [id]/page.tsx
      settings/page.tsx
      invitations/page.tsx
      credits/page.tsx
      audit/page.tsx
    lib/
      api-client.ts
      query-client.ts
    components/admin/
    hooks/
    types/
```

---

## Sources

- Direct analysis of existing Spectra v0.4 source code: `main.py`, `config.py`, `dependencies.py`, `models/user.py`, `routers/auth.py`, `routers/chat.py`, `services/chat.py`, `database.py`, `models/base.py`, all schemas -- HIGH confidence
- `requirements/milestone-05-req.md` requirements document -- HIGH confidence
- Existing Alembic migration chain (9 migrations) -- HIGH confidence
- FastAPI dependency injection patterns (project convention) -- HIGH confidence
- SQLAlchemy `SELECT FOR UPDATE` for concurrent credit operations -- standard PostgreSQL pattern, HIGH confidence
- FastAPI CORS middleware with explicit origins (existing project pattern) -- HIGH confidence
