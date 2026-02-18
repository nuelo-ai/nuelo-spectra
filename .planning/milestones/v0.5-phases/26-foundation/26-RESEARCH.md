# Phase 26: Foundation - Research

**Researched:** 2026-02-16
**Domain:** Database schema, split-horizon architecture, admin authentication, audit logging
**Confidence:** HIGH

## Summary

Phase 26 builds the infrastructure layer for the entire v0.5 Admin Portal milestone. It touches four domains: (1) database schema changes adding 5 new tables and 2 new columns to users, (2) split-horizon routing controlled by `SPECTRA_MODE` env var, (3) admin authentication with JWT `is_admin` claim and sliding-window session timeout, and (4) audit logging for all admin mutations.

The existing codebase is well-structured for these changes. The FastAPI app in `main.py` already uses a router-based architecture that can be conditionally mounted. The JWT system in `utils/security.py` uses PyJWT 2.11.0 with custom claims, which trivially supports adding an `is_admin` claim. SQLAlchemy 2.0.46 with Alembic 1.18.3 and asyncpg 0.31.0 provides a mature async migration pipeline. No new backend dependencies are needed -- all required libraries are already installed.

**Primary recommendation:** Implement in this order: (1) Alembic migration for schema changes, (2) SPECTRA_MODE routing in main.py, (3) admin auth middleware + CLI seed command, (4) audit logging middleware. Each layer builds on the previous.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Admin bootstrap:**
- Seed admin via CLI: `python -m app.cli seed-admin` reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`
- Auto-creates a new user account if email doesn't exist (works on empty DB), sets `is_admin=true`
- Idempotent: if admin already exists, re-running resets password from current `.env` value (doubles as password recovery for seeded admin)
- Additional admins created via admin API -- first admin promotes existing users through an admin endpoint
- Non-seeded admins recover passwords through existing email reset flow (Phase 12 SMTP)

**Audit logging:**
- Mutations only -- log creates, updates, deletes, promotions, credit adjustments. Skip read-only GET requests
- Details field captures before + after values: `{before: {credits: 100}, after: {credits: 50}, reason: "manual deduction"}`
- Capture admin's IP address alongside admin_id per audit entry
- Retention: Claude's discretion (admin actions are low-volume, likely keep forever)

**Mode behavior:**
- Default `SPECTRA_MODE` is `dev` when env var is not set (exposes both public + admin routes for local development)
- Production: two separate backend instances -- public backend on main network, admin backend on Tailscale VPN
- Routes not available in current mode return 404 (not 403) -- hides existence of admin routes from public backend
- Log a WARNING when requests hit routes outside current mode (detect misconfiguration or scanning)

**Auth responses:**
- Reuse existing JWT system with added `is_admin` claim -- one auth system, admin check is a middleware layer
- 30-minute inactivity timeout with sliding window -- each admin API call resets the timer
- In dev mode, non-admin user hitting admin endpoint gets 403 Forbidden (clear error for development)
- In public mode, admin routes simply don't exist (404, routes aren't registered)
- Lockout policy: Claude's discretion (admin backend is VPN-isolated, brute force risk is low)

### Claude's Discretion

- Audit log retention policy (keep forever vs auto-purge -- low volume makes forever reasonable)
- Lockout after failed admin login attempts (Tailscale isolation reduces brute force risk)
- Exact JWT claim structure and middleware implementation
- Database migration strategy for backfilling existing users

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.128.0 | Web framework with dependency injection | Already in use, router system supports conditional mounting |
| SQLAlchemy | 2.0.46 | Async ORM with mapped_column pattern | Already in use, all models follow Mapped[] pattern |
| Alembic | 1.18.3 | Database migrations with async support | Already in use, env.py configured for async_engine_from_config |
| PyJWT | 2.11.0 | JWT creation and verification | Already in use, supports arbitrary custom claims natively |
| asyncpg | 0.31.0 | PostgreSQL async driver | Already in use via SQLAlchemy async engine |
| pwdlib | 0.3.x | Argon2 password hashing | Already in use via `utils/security.py` |
| Pydantic | 2.12.5 | Request/response validation | Already in use for all schemas |
| Click | 8.3.1 | CLI framework | Already installed as FastAPI/uvicorn transitive dependency |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.x | Settings from env vars | Already used in `config.py` for `Settings` class |
| python-dotenv | 1.x | `.env` file loading | Already used by pydantic-settings |

### New Dependencies Required
**None.** All required functionality is covered by existing installed packages.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Click for CLI | Typer (also installed, 0.21.1) | Typer wraps Click with type hints. Either works. Click is simpler for a single `seed-admin` command with no subcommand tree. Recommend Click for minimal footprint. |
| In-process audit log | Separate audit service | Overkill for this scale. DB-backed audit in same transaction is simpler and ensures atomicity. |

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── cli.py                    # CLI module (python -m app.cli seed-admin)
├── cli/                      # Alternative: package with __main__.py
│   ├── __init__.py
│   └── __main__.py           # Entry point for python -m app.cli
├── config.py                 # Add SPECTRA_MODE, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_SESSION_TIMEOUT_MINUTES
├── dependencies.py           # Add get_current_admin_user dependency
├── main.py                   # Conditional router mounting based on SPECTRA_MODE
├── middleware/
│   └── audit.py              # Audit logging middleware (or use FastAPI dependency)
├── models/
│   ├── user.py               # Add is_admin, user_class columns
│   ├── admin_audit_log.py    # New: audit log model
│   ├── user_credit.py        # New: per-user credit balance
│   ├── credit_transaction.py # New: credit transaction history
│   ├── invitation.py         # New: invite records
│   └── platform_setting.py   # New: key-value platform settings
├── routers/
│   └── admin/                # New: admin router package
│       ├── __init__.py       # Exports admin router
│       └── auth.py           # Admin login endpoint
└── services/
    └── admin/
        └── auth.py           # Admin auth service logic
```

### Pattern 1: Conditional Router Mounting (SPECTRA_MODE)
**What:** Mount different router sets based on SPECTRA_MODE environment variable
**When to use:** Application startup in main.py
**Example:**
```python
# In main.py
from app.config import get_settings

settings = get_settings()
mode = settings.spectra_mode  # "public", "admin", or "dev"

# Public routes (always registered in public and dev modes)
if mode in ("public", "dev"):
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(chat.router)
    app.include_router(chat_sessions.router)
    app.include_router(search.router)

# Admin routes (only registered in admin and dev modes)
if mode in ("admin", "dev"):
    from app.routers.admin import admin_router
    app.include_router(admin_router, prefix="/api/admin")

# Health is always available
app.include_router(health.router)
```

### Pattern 2: Admin Auth Dependency (Middleware Layer)
**What:** FastAPI dependency that checks `is_admin` claim in JWT and enforces session timeout
**When to use:** Every admin endpoint
**Example:**
```python
# In dependencies.py
async def get_current_admin_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    request: Request,
) -> User:
    """Verify JWT has is_admin=True claim and session is not expired."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    # Check admin claim
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check sliding window timeout
    issued_at = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    if datetime.now(timezone.utc) - issued_at > timedelta(minutes=settings.admin_session_timeout_minutes):
        raise HTTPException(status_code=401, detail="Admin session expired")

    # ... get user from DB, verify is_admin in DB too ...
    return user

CurrentAdmin = Annotated[User, Depends(get_current_admin_user)]
```

### Pattern 3: Sliding Window Session with Short-Lived Tokens
**What:** Issue short-lived admin JWTs (e.g., 30 min). On each admin API call, return a refreshed token in the response header. Client replaces its token. If 30 min pass with no calls, token expires.
**When to use:** Admin session timeout with sliding window
**Implementation options:**

**Option A -- Re-issue token in response header (recommended):**
Each admin endpoint (or a middleware) issues a fresh JWT on successful auth. The admin frontend reads `X-Admin-Token` from response headers and updates its stored token. No API call for 30 minutes = token expires = forced re-login.

**Option B -- Server-side session store:**
Store `admin_id -> last_activity` in Redis/memory. Check on each request, update timestamp. Adds server-side state, more complex. Not recommended given existing stateless JWT pattern.

**Recommendation:** Option A. It stays stateless, requires no new infrastructure, and aligns with the existing JWT architecture. The admin frontend simply updates its stored token from each response header.

### Pattern 4: Audit Logging via Dependency Injection
**What:** Use a FastAPI dependency or utility function called explicitly in admin service functions to create audit log entries
**When to use:** Every admin mutation (create, update, delete)
**Example:**
```python
# In services/admin/audit.py
async def log_admin_action(
    db: AsyncSession,
    admin_id: UUID,
    action: str,
    target_type: str,
    target_id: str,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    # Don't commit here -- let the caller's transaction commit include the audit log
```

### Pattern 5: CLI Module with `python -m` Entry Point
**What:** Create `app/cli/__init__.py` + `app/cli/__main__.py` so `python -m app.cli` works
**When to use:** Admin seeding command
**Example:**
```python
# app/cli/__main__.py
import asyncio
import click
from app.cli import seed_admin

@click.group()
def cli():
    """Spectra admin CLI tools."""
    pass

@cli.command()
def seed_admin_cmd():
    """Seed the first admin user from .env credentials."""
    asyncio.run(seed_admin())

if __name__ == "__main__":
    # Support: python -m app.cli seed-admin
    cli()
```

### Anti-Patterns to Avoid
- **Registering admin routes then checking mode in middleware:** This exposes route existence (different error codes). Instead, simply don't register admin routes in public mode. Routes that don't exist return 404 naturally.
- **Separate auth system for admin:** Don't create a parallel JWT/session system. Reuse existing `create_tokens` / `verify_token` with an added `is_admin` claim.
- **Audit logging in middleware for all requests:** Don't blindly log every request. Only log mutations explicitly in service functions where you have business context (before/after values).
- **Storing admin session state in a database table:** Don't create an `admin_sessions` table. Stateless JWT with sliding window via token reissue is simpler and consistent with existing architecture.
- **Hand-rolling `python -m` without Click/Typer:** Always use a CLI framework. Even for one command, it provides `--help`, error handling, and future extensibility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt/scrypt | pwdlib (already used) | Timing attacks, salt management, algorithm upgrades |
| JWT creation/verification | Manual base64/HMAC | PyJWT (already used) | Algorithm negotiation attacks, claim validation |
| CLI argument parsing | sys.argv parsing | Click (already installed) | Help text, validation, error messages |
| Enum column types | String columns with validation | SQLAlchemy Enum or String with CHECK | DB-level enforcement, migration-friendly |
| IP address extraction | Manual header parsing | `request.client.host` + `X-Forwarded-For` header | Proxy-awareness, IPv6 handling |

**Key insight:** Every piece of this phase uses existing libraries. The risk is in the integration patterns (conditional routing, claim-based auth, audit in transactions), not in building new primitives.

## Common Pitfalls

### Pitfall 1: Alembic Migration Breaks Existing Data
**What goes wrong:** Adding `is_admin` (non-nullable Boolean) or `user_class` (non-nullable String) to existing users table without defaults causes migration failure on tables with existing rows.
**Why it happens:** PostgreSQL requires a value for non-nullable columns when rows already exist.
**How to avoid:** Use `server_default` in the migration. For `is_admin`: `server_default=sa.text("false")`. For `user_class`: `server_default="free"`. After migration, optionally remove server_default if you want the application to always set it explicitly.
**Warning signs:** `alembic upgrade head` fails with "column cannot be null" error.

### Pitfall 2: Circular Import with Conditional Router Imports
**What goes wrong:** Importing admin routers at module level in main.py when those routers import models/services that aren't needed in public mode.
**Why it happens:** Python executes all imports at module load time.
**How to avoid:** Use lazy imports inside the `if mode in ("admin", "dev"):` block. This is already shown in Pattern 1 above.
**Warning signs:** ImportError when running in public mode, or unnecessary memory usage.

### Pitfall 3: Audit Log in Separate Transaction
**What goes wrong:** Audit log entry is committed independently from the action it logs. If the main action fails/rolls back, a phantom audit entry exists.
**Why it happens:** Using a separate `db.commit()` for the audit log, or using a separate session.
**How to avoid:** Add audit log entry to the same session/transaction as the main action. Single `db.commit()` at the end covers both the action and the audit entry.
**Warning signs:** Audit entries for actions that didn't actually complete.

### Pitfall 4: `user_class` as Python Enum vs String Column
**What goes wrong:** Using Python `enum.Enum` mapped to PostgreSQL ENUM type. Adding a new tier later requires an Alembic migration to ALTER TYPE, which is painful in PostgreSQL (requires creating new type, migrating, dropping old).
**Why it happens:** PostgreSQL ENUM types are rigid -- you can't easily add values in a transaction.
**How to avoid:** Use `String(20)` column with a CHECK constraint, or just use a plain `String(20)` column with application-level validation via `user_classes.yaml`. The config file already defines valid tiers. PostgreSQL ENUM is not worth the migration headache.
**Warning signs:** Alembic autogenerate produces ugly ENUM migration code.

### Pitfall 5: Sliding Window Token Reissue Creates Token Flood
**What goes wrong:** Every admin API response reissues a new token, causing the frontend to constantly update stored tokens and potentially causing race conditions with parallel requests.
**Why it happens:** Multiple simultaneous admin API calls each return a new token; the frontend overwrites with the last one received, potentially invalidating in-flight requests.
**How to avoid:** Tokens are self-contained JWTs -- they don't invalidate previous tokens. Each token is independently valid for its own 30-minute window. The frontend should update its stored token from any response but doesn't need to worry about races because old tokens remain valid until their own expiry. The key constraint is: `iat` (issued-at) plus timeout window defines validity, not token replacement.
**Warning signs:** 401 errors during rapid sequential admin operations.

### Pitfall 6: Missing `__init__.py` Import for New Models
**What goes wrong:** Alembic autogenerate doesn't detect new tables because the models aren't imported in `env.py`.
**Why it happens:** Alembic only sees models that are imported and registered with `Base.metadata`.
**How to avoid:** Add all new model imports to `app/models/__init__.py` AND to `alembic/env.py`'s import section. Current env.py imports specific modules: `from app.models import user, file, chat_message, chat_session, search_quota, password_reset`. Must add all 5 new models.
**Warning signs:** `alembic revision --autogenerate` produces empty migration.

### Pitfall 7: Not Verifying `is_admin` in Database (JWT-Only Check)
**What goes wrong:** Admin user is demoted (is_admin set to false in DB) but existing JWT still has `is_admin=True` claim and remains valid for 30 minutes.
**Why it happens:** JWTs are stateless -- changing DB doesn't invalidate existing tokens.
**How to avoid:** The admin dependency MUST verify `is_admin` in the database on every request, not just trust the JWT claim. The JWT claim is a fast pre-filter; the DB check is the source of truth.
**Warning signs:** Demoted admin retains access until token expires.

## Code Examples

### Database Models for Phase 26

#### Modified User Model
```python
# app/models/user.py - additions
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...

    # New admin fields
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    user_class: Mapped[str] = mapped_column(String(20), default="free")
```

#### Admin Audit Log Model
```python
# app/models/admin_audit_log.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    admin_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(50))  # "user", "credit", "setting", etc.
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max length
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
```

#### Platform Settings Model
```python
# app/models/platform_setting.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)  # admin who last changed it
```

#### User Credits Model
```python
# app/models/user_credit.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, DateTime, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class UserCredit(Base):
    __tablename__ = "user_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    balance: Mapped[float] = mapped_column(NUMERIC(10, 1), default=0)
    last_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
```

#### Credit Transactions Model
```python
# app/models/credit_transaction.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, ForeignKey, DateTime, NUMERIC, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[float] = mapped_column(NUMERIC(10, 1))  # positive = credit, negative = debit
    balance_after: Mapped[float] = mapped_column(NUMERIC(10, 1))
    transaction_type: Mapped[str] = mapped_column(String(30))  # "usage", "admin_adjustment", "reset", "initial"
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
```

#### Invitations Model
```python
# app/models/invitation.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    invited_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, expired, revoked
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
```

### Admin JWT Token with is_admin Claim
```python
# In utils/security.py - new function
def create_admin_tokens(user_id: str, settings: Settings) -> dict[str, str]:
    """Create JWT tokens with is_admin claim for admin users."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.admin_session_timeout_minutes
    )
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "access",
        "is_admin": True,
    }
    access_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    # Admin refresh token (longer lived, for token reissue)
    refresh_payload = {
        "sub": user_id,
        "exp": now + timedelta(hours=8),  # workday session
        "type": "refresh",
        "is_admin": True,
    }
    refresh_token = jwt.encode(refresh_payload, settings.secret_key, algorithm=settings.algorithm)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
```

### SPECTRA_MODE Configuration
```python
# In config.py - additions to Settings class
class Settings(BaseSettings):
    # ... existing fields ...

    # Admin / Split-Horizon
    spectra_mode: str = "dev"  # "public", "admin", or "dev"
    admin_email: str = ""      # For seed-admin CLI
    admin_password: str = ""   # For seed-admin CLI
    admin_session_timeout_minutes: int = 30
```

### Seed Admin CLI
```python
# app/cli/__main__.py
import asyncio
import click
from dotenv import load_dotenv

load_dotenv()

@click.group()
def cli():
    """Spectra CLI tools."""
    pass

@cli.command("seed-admin")
def seed_admin():
    """Seed or reset admin user from ADMIN_EMAIL and ADMIN_PASSWORD in .env"""
    asyncio.run(_seed_admin())

async def _seed_admin():
    from app.config import get_settings
    from app.database import async_session_maker
    from app.models.user import User
    from app.utils.security import hash_password
    from sqlalchemy import select

    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        click.echo("Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env")
        raise SystemExit(1)

    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == settings.admin_email))
        user = result.scalar_one_or_none()

        if user:
            user.hashed_password = hash_password(settings.admin_password)
            user.is_admin = True
            click.echo(f"Admin user '{settings.admin_email}' updated (password reset, is_admin=True)")
        else:
            user = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                is_admin=True,
                user_class="free",
            )
            db.add(user)
            click.echo(f"Admin user '{settings.admin_email}' created")

        await db.commit()

if __name__ == "__main__":
    cli()
```

### Alembic Migration with Backfill
```python
# Example migration pattern for adding columns + creating tables + backfilling
def upgrade() -> None:
    # 1. Add new columns to users table with server defaults
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("user_class", sa.String(20), server_default="free", nullable=False))

    # 2. Create new tables
    op.create_table("platform_settings", ...)
    op.create_table("user_credits", ...)
    op.create_table("credit_transactions", ...)
    op.create_table("invitations", ...)
    op.create_table("admin_audit_log", ...)

    # 3. Backfill: create user_credits records for all existing users
    # Use raw SQL for data migration in Alembic (not ORM)
    op.execute("""
        INSERT INTO user_credits (id, user_id, balance, created_at)
        SELECT gen_random_uuid(), id, 0, NOW()
        FROM users
        WHERE id NOT IN (SELECT user_id FROM user_credits)
    """)
```

### Admin Route with 404 Hiding
```python
# In main.py - route not available in current mode returns 404 naturally
# because the routes are never registered. No special middleware needed.

# Optional: add a catch-all for /api/admin/* in public mode to log warnings
if mode == "public":
    @app.api_route("/api/admin/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def admin_route_not_found(path: str):
        import logging
        logging.getLogger("spectra.security").warning(
            f"Request to admin route /api/admin/{path} in public mode"
        )
        raise HTTPException(status_code=404, detail="Not Found")
```

## Discretion Recommendations

### Audit Log Retention: Keep Forever
**Recommendation:** No auto-purge. Admin actions are low-volume (tens per day at most). Even after years, the table will be small. Adding purge logic introduces complexity and data loss risk. If needed later, a simple `DELETE WHERE created_at < '...'` query handles it.

### Lockout Policy: 5 Failed Attempts, 15-Minute Cooldown
**Recommendation:** Implement a lightweight lockout even though the admin backend is VPN-isolated. Use an in-memory dictionary (like the existing `_reset_cooldowns` pattern in `routers/auth.py`). After 5 failed login attempts from the same IP within 15 minutes, return 429 Too Many Requests. This protects against compromised Tailscale nodes or insider threats. No DB table needed -- memory is sufficient since admin backend restarts are rare.

### JWT Claim Structure
**Recommendation:**
```json
{
  "sub": "uuid-string",
  "exp": 1708123456,
  "iat": 1708121656,
  "type": "access",
  "is_admin": true
}
```
The `iat` (issued-at) claim is critical for the sliding window: `now - iat > timeout` means expired. New tokens reissued on each admin API call update `iat` and `exp`. Regular user tokens do NOT get `is_admin` claim (absence = false).

### Migration Strategy for Backfilling
**Recommendation:** Single migration file with three phases:
1. `ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL`
2. `ALTER TABLE users ADD COLUMN user_class VARCHAR(20) DEFAULT 'free' NOT NULL`
3. `INSERT INTO user_credits ... SELECT FROM users` (create credit records for all existing users with balance=0)

Use `server_default` so Alembic handles backfill automatically for existing rows. The `user_credits` INSERT is explicit data migration within the same migration file. This is standard Alembic practice -- no separate script needed.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy `Column()` | `mapped_column()` with `Mapped[]` typing | SQLAlchemy 2.0 (2023) | This project already uses the modern pattern |
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.100+ (2023) | This project already uses lifespan pattern |
| PostgreSQL ENUM types | String columns with app-level validation | Community best practice | Avoids painful ALTER TYPE migrations |
| Separate admin database | Shared database with role flags | Standard for monolithic apps | Simpler, single source of truth |

**Deprecated/outdated:**
- `@app.on_event("startup")` -- project already uses `lifespan`, no concern

## Open Questions

1. **Admin login endpoint path**
   - What we know: Admin routes go under `/api/admin/`. Auth endpoint could be `/api/admin/auth/login`.
   - What's unclear: Should admin login share the same `/auth/login` endpoint (with mode detection) or have its own dedicated endpoint?
   - Recommendation: Dedicated `/api/admin/auth/login` endpoint. Keeps separation clean. In public mode, this route doesn't exist. In dev mode, both endpoints work. The admin login endpoint specifically checks `is_admin` and returns admin JWT with `is_admin` claim.

2. **Credit record creation for new users (post-migration)**
   - What we know: Migration backfills existing users. New users need credit records too.
   - What's unclear: Should credit record creation happen in the signup service or via a database trigger?
   - Recommendation: Add credit record creation to the `auth_service.create_user()` function. Simple, explicit, testable. Triggers are hidden logic.

3. **Token reissue mechanism for sliding window**
   - What we know: Each admin API call should reset the 30-minute window.
   - What's unclear: Should the new token be returned in a response header or in the response body?
   - Recommendation: Response header `X-Admin-Token`. The admin frontend interceptor reads it and updates stored token. This avoids modifying every response schema. Implement via FastAPI middleware that runs after the route handler.

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** -- Direct reading of all relevant source files in the project:
  - `backend/app/main.py` -- Current router mounting, lifespan pattern
  - `backend/app/models/user.py` -- Current User model structure (Mapped[] pattern)
  - `backend/app/utils/security.py` -- Current JWT implementation (PyJWT with custom claims)
  - `backend/app/config.py` -- Current Settings class (pydantic-settings)
  - `backend/app/dependencies.py` -- Current auth dependency chain
  - `backend/app/services/auth.py` -- Current auth service pattern
  - `backend/app/routers/auth.py` -- Current router pattern, cooldown dictionary pattern
  - `backend/alembic/env.py` -- Current Alembic async configuration
  - `backend/alembic/versions/` -- Existing migration patterns (9 migrations)
  - `backend/pyproject.toml` -- Dependency list (no new deps needed)
- **Installed package versions** (verified via pip):
  - PyJWT 2.11.0, SQLAlchemy 2.0.46, Alembic 1.18.3, FastAPI 0.128.0, Pydantic 2.12.5, asyncpg 0.31.0, Click 8.3.1, Typer 0.21.1

### Secondary (MEDIUM confidence)
- **PyJWT custom claims** -- PyJWT `jwt.encode()` accepts arbitrary dictionary keys as claims. Verified by reading existing `utils/security.py` which already uses `"sub"`, `"exp"`, `"type"` custom claims. Adding `"is_admin"` is identical.
- **Alembic `server_default` for backfill** -- Standard Alembic pattern for adding non-nullable columns to tables with existing data. Confirmed by examining existing migration patterns in the project.
- **PostgreSQL `gen_random_uuid()`** -- Available in PostgreSQL 13+ (standard function, no extension needed). Used for UUID generation in data migration SQL.
- **JSONB column type** -- SQLAlchemy `dialects.postgresql.JSONB` for the audit log `details` field. Native PostgreSQL type with indexing support.

### Tertiary (LOW confidence)
- None. All findings verified against codebase or well-established library documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and in use. Zero new dependencies.
- Architecture: HIGH -- Patterns directly extend existing codebase patterns (router mounting, dependency injection, JWT claims).
- Pitfalls: HIGH -- Identified from direct codebase inspection (migration patterns, model registration, transaction boundaries).
- Discretion items: MEDIUM -- Recommendations are sound but involve implementation choices that should be validated during development.

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable stack, no fast-moving dependencies)
