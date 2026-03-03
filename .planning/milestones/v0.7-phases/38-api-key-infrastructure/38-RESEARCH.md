# Phase 38: API Key Infrastructure - Research

**Researched:** 2026-02-23
**Domain:** API key authentication, FastAPI dependency injection, SQLAlchemy async models, Alembic migrations, SPECTRA_MODE routing
**Confidence:** HIGH

## Summary

Phase 38 establishes the foundational infrastructure for API key-based authentication in Spectra. The work has three distinct concerns: (1) the data layer — an `api_keys` table with SHA-256-hashed key storage and a SQLAlchemy model; (2) the service layer — an `ApiKeyService` that handles key generation, listing, and revocation; and (3) the authentication layer — a new FastAPI dependency `get_authenticated_user()` that accepts either a JWT token (fast path) or a Bearer API key (SHA-256 lookup fallback), plus a FastAPI `APIRouter` mounted under `/api/v1/` with APIKEY CRUD endpoints.

The architectural decisions are already locked in STATE.md: SHA-256 hashing (not Argon2), `spe_<token_urlsafe(32)>` prefix format, unified `get_authenticated_user()` dependency, and `scopes`/`expires_at` columns in the schema for forward compatibility. The `SPECTRA_MODE=api` and `SPECTRA_MODE=dev` routing requirements are pure `main.py` additions following an already-established mode-gate pattern.

The codebase already has all the infrastructure needed: SQLAlchemy async models, Alembic migrations, a service class pattern (`CreditService`), SHA-256 token patterns (`routers/auth.py` invitation token hashing), and a `SPECTRA_MODE` guard pattern in `main.py`. Phase 38 is almost entirely additive — no existing code needs modification except `main.py` (new mode branch) and `alembic/env.py` (import new model).

**Primary recommendation:** Follow the existing `PasswordResetToken` / `Invitation` model pattern for storage, the `CreditService` class pattern for service layer, and the `main.py` mode-gate pattern for routing. Use `secrets.token_urlsafe(32)` for generation and `hashlib.sha256` for storage — both already imported in `routers/auth.py`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APIKEY-01 | User can view their API keys on the Settings/API Keys page | Frontend: new `ApiKeySection` component added to `settings/page.tsx`; Backend: `GET /api/v1/keys` endpoint using `get_current_user` dependency |
| APIKEY-02 | User can create an API key with a name and description | Backend: `POST /api/v1/keys` returns full key once; Frontend: modal/dialog showing key once on creation |
| APIKEY-03 | User can revoke their own API keys | Backend: `DELETE /api/v1/keys/{id}` sets `is_active=False`; Frontend: revoke button with confirmation |
| APIKEY-04 | Revoked API keys cannot be used for authentication | `get_authenticated_user()` dependency checks `is_active=True` before accepting key; SHA-256 lookup filters revoked |
| APIKEY-05 | API keys stored securely (hashed, full key shown once at creation) | `secrets.token_urlsafe(32)` generated; SHA-256 hash stored; plain key returned only from POST response |
| APISEC-01 | API requests authenticate via API key in `Authorization: Bearer` header | New `get_authenticated_user()` dependency: JWT fast path first, then SHA-256 key lookup |
| APISEC-02 | Invalid or revoked API keys return 401 Unauthorized | `get_authenticated_user()` raises `HTTPException(status_code=401)` for any failed lookup |
| APIINFRA-01 | `SPECTRA_MODE=api` enables API routes on existing backend — no separate codebase | `main.py` mode-gate: add `if mode in ("api", "dev"):` block mounting the `api_v1_router` |
| APIINFRA-02 | API routes are versioned under `/api/v1/` | `APIRouter()` with `prefix="/api/v1"` included conditionally in `main.py` |
| APIINFRA-05 | In `SPECTRA_MODE=dev`, all `/api/v1/` routes active alongside existing routes | `main.py` existing `if mode in ("public", "dev"):` — just extend the api_v1 block to include dev |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `secrets` (stdlib) | Python 3.12 | Cryptographically secure token generation | Built-in, no deps, correct for high-entropy tokens |
| `hashlib` (stdlib) | Python 3.12 | SHA-256 hashing of API keys | Already used in `routers/auth.py` for invitation/reset tokens |
| `sqlalchemy[asyncio]` | >=2.0.0 (already installed) | Async ORM for `ApiKey` model | Project standard — all models use this |
| `alembic` | >=1.13.0 (already installed) | Database migrations | Project standard |
| `fastapi` | >=0.115.0 (already installed) | Router, dependency injection | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pwdlib[argon2]` | >=0.3.0 (already installed) | Password hashing | NOT used for API keys (decision: SHA-256 for high-entropy tokens) |
| `pyjwt` | >=2.9.0 (already installed) | JWT decode in `get_authenticated_user()` fast path | Existing `verify_token()` utility handles this |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SHA-256 (decision: locked) | Argon2 | Argon2 is for low-entropy passwords; SHA-256 is industry-standard for random 32-byte tokens (GitHub, Stripe) — no performance penalty |
| `secrets.token_urlsafe(32)` | UUID4 | UUID4 is not URL-safe and has lower entropy density; `token_urlsafe(32)` is 43 chars of base64url |
| In-DB revocation check | In-memory cache | API keys are long-lived; no in-memory revocation cache needed (unlike JWT deactivation) |

**Installation:** No new packages needed. Everything is already in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── models/
│   └── api_key.py              # NEW: ApiKey SQLAlchemy model
├── services/
│   └── api_key.py              # NEW: ApiKeyService (create, list, revoke, authenticate)
├── routers/
│   └── api_v1/
│       ├── __init__.py         # NEW: api_v1_router aggregator
│       └── api_keys.py         # NEW: CRUD endpoints for API keys (user-facing)
├── schemas/
│   └── api_key.py              # NEW: ApiKeyCreate, ApiKeyResponse, ApiKeyListItem schemas
├── dependencies.py             # MODIFIED: add get_authenticated_user() dependency
├── main.py                     # MODIFIED: add api/dev mode gates for api_v1_router
alembic/
├── env.py                      # MODIFIED: import api_key model
└── versions/
    └── XXXX_add_api_keys_table.py  # NEW: migration
frontend/src/
├── components/settings/
│   └── ApiKeySection.tsx       # NEW: list + create + revoke UI component
├── hooks/
│   └── useApiKeys.ts           # NEW: TanStack Query hooks (list, create, revoke)
└── app/(dashboard)/settings/
    └── page.tsx                # MODIFIED: add <ApiKeySection /> below <AccountInfo />
```

### Pattern 1: API Key Model (follows PasswordResetToken pattern)

**What:** SQLAlchemy async model with `token_hash` (unique, indexed), `key_prefix` (first 12 chars of raw key stored for display), `is_active` boolean.
**When to use:** Any time a secret needs to be stored as one-way hash but partially displayed.

```python
# Source: existing pattern from app/models/password_reset.py + app/models/invitation.py
from sqlalchemy import String, DateTime, Boolean, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ApiKey(Base):
    """API key model. Full key shown once at creation; stored as SHA-256 hash."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_prefix: Mapped[str] = mapped_column(String(16))   # first 12 chars of raw key
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scopes: Mapped[list[str] | None] = mapped_column(
        PG_ARRAY(String), nullable=True
    )  # Forward compat; NULL = all scopes
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # NULL = no expiry
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
```

### Pattern 2: Key Generation (follows `routers/auth.py` invitation token pattern)

**What:** Generate raw key → store hash → return raw key once.
**When to use:** Any single-use or display-once secret.

```python
# Source: existing pattern from app/routers/auth.py (lines 87, 331) and app/services/email.py
import hashlib
import secrets

def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its SHA-256 hash.

    Returns:
        (raw_key, token_hash) — raw_key returned to user ONCE, token_hash stored in DB
    """
    raw = secrets.token_urlsafe(32)   # 43 base64url chars
    full_key = f"spe_{raw}"           # locked format from STATE.md
    token_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, token_hash
```

### Pattern 3: ApiKeyService (follows CreditService class pattern)

**What:** Static-method class grouping all API key DB operations.
**When to use:** Any service with multiple related DB operations.

```python
# Source: pattern from app/services/credit.py
class ApiKeyService:
    @staticmethod
    async def create(db, user_id, name, description) -> tuple[ApiKey, str]:
        """Returns (api_key_record, full_raw_key). full_raw_key not stored."""

    @staticmethod
    async def list_for_user(db, user_id) -> list[ApiKey]:
        """Returns active + revoked keys for user (sorted by created_at desc)."""

    @staticmethod
    async def revoke(db, key_id, user_id) -> bool:
        """Sets is_active=False. Returns False if key not found or not owned by user."""

    @staticmethod
    async def authenticate(db, raw_key: str) -> User | None:
        """Hash raw_key, lookup in DB, check is_active, return User or None."""
```

### Pattern 4: Unified `get_authenticated_user()` dependency

**What:** FastAPI dependency that accepts Bearer token as either JWT or API key. JWT fast path (same as existing `get_current_user`), then SHA-256 key lookup fallback.
**When to use:** All `/api/v1/` endpoints.

```python
# Source: architecture decision from STATE.md; pattern from app/dependencies.py
from fastapi.security import OAuth2PasswordBearer

# Reuse the same oauth2_scheme — both JWT and API keys arrive as Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

async def get_authenticated_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})

    # Fast path: try JWT first
    try:
        user_id_str = verify_token(token, "access", settings)
        # ... same logic as get_current_user
        return user
    except HTTPException:
        pass  # Fall through to API key check

    # Slow path: API key lookup
    user = await ApiKeyService.authenticate(db, token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key",
                            headers={"WWW-Authenticate": "Bearer"})
    return user
```

### Pattern 5: `main.py` mode-gate for `/api/v1/` router

**What:** Following the existing `if mode in ("public", "dev"):` and `if mode in ("admin", "dev"):` pattern, add a new block for the api_v1 router.
**When to use:** Conditional route mounting based on `SPECTRA_MODE`.

```python
# Source: app/main.py lines 319-335 (existing mode-gate pattern)

# API v1 routes (api and dev modes)
if mode in ("api", "dev"):
    from app.routers.api_v1 import api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")
```

The existing `Settings.spectra_mode` validator only allows `"public"`, `"admin"`, `"dev"` — it must be updated to also accept `"api"`.

### Pattern 6: Alembic migration (follows existing migration pattern)

```python
# Source: backend/alembic/versions/e49613642cfe and dfe836ff84e9 patterns

def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_token_hash', 'api_keys', ['token_hash'], unique=True)
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False)
```

### Pattern 7: Frontend API key section (follows AccountInfo/ProfileForm pattern)

**What:** New `ApiKeySection.tsx` component added to `settings/page.tsx`. Uses TanStack Query mutations (same as `useSettings.ts`) and `apiClient` (same as all hooks).
**When to use:** Whenever settings page gets a new section.

```typescript
// Source: pattern from frontend/src/hooks/useSettings.ts + AccountInfo.tsx
// useApiKeys.ts — mirrors useSettings.ts structure
export function useApiKeys() {
  return useQuery({ queryKey: ["api-keys"], queryFn: ... });
}
export function useCreateApiKey() {
  return useMutation({ mutationFn: ..., onSuccess: () => queryClient.invalidateQueries(...) });
}
export function useRevokeApiKey() {
  return useMutation({ mutationFn: ..., onSuccess: () => queryClient.invalidateQueries(...) });
}
```

### Anti-Patterns to Avoid

- **Storing plain API keys:** Never store the full key in the DB — only `token_hash`. The `key_prefix` column stores the first 12 chars for display only.
- **Using Argon2 for API keys:** Decision locked in STATE.md. SHA-256 is correct for high-entropy tokens. Argon2 is for passwords.
- **Modifying `get_current_user`:** The existing dependency must remain unchanged. Create a new `get_authenticated_user()` alongside it.
- **Checking JWT claims first then falling through silently:** The fast-path/fallback logic must not leak JWT decode errors to API key callers; catch `HTTPException` from `verify_token` before attempting key lookup.
- **Mounting `/api/v1/` routes in all modes:** Only mount in `api` and `dev` modes. In `public` mode, a `404` catch-all (similar to the existing `/api/admin/` catch-all) is advisable but not required for Phase 38.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure random token | Custom RNG | `secrets.token_urlsafe(32)` | Cryptographically secure, stdlib, URL-safe |
| Token hashing | Custom hash | `hashlib.sha256(key.encode()).hexdigest()` | Already used in project for invitation/reset tokens |
| DB session management | Manual connection | `get_db()` async session dependency | Project standard, handles commit/rollback |
| Frontend data fetching | Manual fetch | TanStack Query via `useQuery`/`useMutation` | Project standard in all hooks |
| Unique index on token_hash | Application-level check | DB `UNIQUE` index + Alembic | Race condition safety, O(1) lookup |

**Key insight:** The entire security model rests on `token_hash` being unique and indexed. The DB constraint is the safety net; don't try to enforce uniqueness in Python.

---

## Common Pitfalls

### Pitfall 1: `SPECTRA_MODE` validator rejects `"api"`
**What goes wrong:** `config.py` line 88 — `validate_admin_credentials_for_admin_modes` only allows `"public"`, `"admin"`, `"dev"`. Adding `SPECTRA_MODE=api` to `.env` will raise `ValueError` at startup.
**Why it happens:** The validator is an explicit allowlist, not a passthrough.
**How to avoid:** Update `config.py` to accept `"api"` as a valid mode. Also update the mode validation check in `main.py` line 292.
**Warning signs:** `ValidationError` or `ValueError` on startup when `SPECTRA_MODE=api`.

### Pitfall 2: JWT fallback swallows legitimate errors
**What goes wrong:** `verify_token()` raises `HTTPException` — if you catch all exceptions from the JWT path, you lose meaningful error info and may incorrectly fall through to API key lookup for expired JWTs.
**Why it happens:** The fallback logic is "try JWT, then try key" but the boundary is fuzzy.
**How to avoid:** Only catch JWT decode failures (invalid format), not expired-token errors. If token starts with `spe_`, skip JWT and go straight to key lookup. If it doesn't start with `spe_`, try JWT only.
**Warning signs:** Expired JWT tokens returning "Invalid or revoked API key" instead of "Token has expired".

### Pitfall 3: `alembic/env.py` not updated with new model import
**What goes wrong:** Alembic autogenerate does not detect the new `ApiKey` model because `env.py` imports models explicitly.
**Why it happens:** Line 14 of `env.py` has an explicit import list: `from app.models import user, file, ..., invitation, platform_setting`. New model must be added.
**How to avoid:** Add `api_key` to the import list in `env.py` before running `alembic revision --autogenerate`.
**Warning signs:** Autogenerated migration is empty even though `ApiKey` model was created.

### Pitfall 4: `User` model missing `api_keys` relationship
**What goes wrong:** `ApiKey.user` relationship works (FK defined on ApiKey), but `User.api_keys` is not defined — causes `AttributeError` if accessed.
**Why it happens:** SQLAlchemy relationships must be defined on both sides when using back_populates.
**How to avoid:** Add `api_keys: Mapped[list["ApiKey"]]` relationship to `user.py` with `cascade="all, delete-orphan"`.
**Warning signs:** `AttributeError: 'User' object has no attribute 'api_keys'`.

### Pitfall 5: `SPECTRA_MODE=api` bypasses admin credential validator
**What goes wrong:** The `validate_admin_credentials_for_admin_modes` validator in `config.py` may not require `ADMIN_EMAIL`/`ADMIN_PASSWORD` in api mode, but admin routes should NOT be mounted in api mode either.
**Why it happens:** The validator checks `dev` and `admin` modes but not `api` mode — this is correct behavior.
**How to avoid:** Confirm that the `api` mode does NOT include admin routes. The `main.py` block for admin routes checks `if mode in ("admin", "dev"):` — `api` mode should not be in this list.
**Warning signs:** Admin panel accessible from API mode deployment.

### Pitfall 6: Frontend one-time key display
**What goes wrong:** User refreshes after creating a key and the full key is gone — UI doesn't make it obvious the key is gone forever.
**Why it happens:** The backend only returns the full key from the `POST` response; subsequent `GET` calls only return the prefix.
**How to avoid:** Show the full key in a modal/dialog that forces the user to explicitly copy it, with a warning "This key will not be shown again." Use a "Copy to clipboard" button and a "I have copied my key" confirmation before closing.
**Warning signs:** User support tickets saying "I can't find my API key".

---

## Code Examples

### Full key generation and storage

```python
# Source: derived from existing patterns in app/routers/auth.py (hashlib.sha256)
#         and app/services/email.py (secrets.token_urlsafe)
import hashlib
import secrets

def generate_api_key() -> tuple[str, str, str]:
    """
    Returns: (full_raw_key, key_prefix, token_hash)
    - full_raw_key: returned to user once, never stored
    - key_prefix: first 12 chars of full_raw_key, stored for display
    - token_hash: SHA-256 of full_raw_key, stored for lookup
    """
    raw = secrets.token_urlsafe(32)       # 43 base64url chars
    full_key = f"spe_{raw}"               # e.g. "spe_abc123..."
    key_prefix = full_key[:12]            # e.g. "spe_abc123.."
    token_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, token_hash
```

### SHA-256 lookup for authentication

```python
# Source: derived from app/routers/auth.py line 331 (reset-password SHA-256 pattern)
import hashlib
from sqlalchemy import select

async def authenticate_by_key(db: AsyncSession, raw_key: str) -> User | None:
    """Look up user by raw API key. Returns None if invalid or revoked."""
    token_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.token_hash == token_hash)
        .where(ApiKey.is_active == True)  # noqa: E712
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return None
    # Optionally update last_used_at (non-critical, use flush not commit)
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_user_by_id(db, api_key.user_id)
```

### Routing mode gate in main.py

```python
# Source: existing pattern from app/main.py lines 319-335
# Add "api" to accepted modes list (line 292):
if mode not in ("public", "admin", "dev", "api"):
    raise ValueError(f"Invalid SPECTRA_MODE: '{mode}'. Must be 'public', 'admin', 'dev', or 'api'")

# Add api_v1 router mounting block:
if mode in ("api", "dev"):
    from app.routers.api_v1 import api_v1_router
    app.include_router(api_v1_router)  # router has prefix="/api/v1" set internally
```

### Pydantic schemas for API key endpoints

```python
# Source: schema pattern from app/schemas/auth.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)

class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    full_key: str        # ONLY returned from POST — never from GET
    created_at: datetime

class ApiKeyListItem(BaseModel):
    id: UUID
    name: str
    description: str | None
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}
```

### APIKEY CRUD router

```python
# Source: pattern from app/routers/credits.py and app/dependencies.py
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/keys", tags=["API Keys"])

@router.get("", response_model=list[ApiKeyListItem])
async def list_api_keys(current_user: CurrentUser, db: DbSession):
    return await ApiKeyService.list_for_user(db, current_user.id)

@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(body: ApiKeyCreateRequest, current_user: CurrentUser, db: DbSession):
    api_key, full_key = await ApiKeyService.create(db, current_user.id, body.name, body.description)
    return ApiKeyCreateResponse(
        id=api_key.id, name=api_key.name,
        key_prefix=api_key.key_prefix, full_key=full_key,
        created_at=api_key.created_at,
    )

@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(key_id: UUID, current_user: CurrentUser, db: DbSession):
    revoked = await ApiKeyService.revoke(db, key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bearer tokens = JWT only | Bearer tokens = JWT OR API key (unified dependency) | Phase 38 (new) | External callers use API keys; internal app continues using JWT; same header format |
| No `/api/v1/` prefix | `/api/v1/` versioned prefix gated by mode | Phase 38 (new) | Future API versions can be `/api/v2/` without touching v1 |
| `SPECTRA_MODE` = `public\|admin\|dev` | Extended to also support `api` | Phase 38 (new) | 5th Dokploy service gets its own dedicated mode (Phase 39) |

**Deprecated/outdated:**
- Nothing deprecated in this phase — purely additive.

---

## Open Questions

1. **Should `get_authenticated_user()` also update `last_used_at` on every request?**
   - What we know: The schema has `last_used_at TIMESTAMPTZ NULL` per STATE.md
   - What's unclear: Whether updating on every request (db write per API call) is acceptable latency cost
   - Recommendation: Yes, update it via `db.flush()` (not commit — the endpoint's own commit will persist it). This is a no-op overhead for now and useful for Phase 40 usage logging.

2. **Should `SPECTRA_MODE=api` mode require `ADMIN_EMAIL`/`ADMIN_PASSWORD`?**
   - What we know: The validator currently requires these for `dev` and `admin` modes; `api` mode will not mount admin routes
   - What's unclear: Whether api mode should also seed an admin user at startup
   - Recommendation: `api` mode does NOT require admin credentials — it is a pure API service without admin portal. The Settings validator should NOT add `api` to its check.

3. **How should the frontend display 0 API keys (empty state)?**
   - What we know: The GET endpoint returns an empty list
   - What's unclear: UX design — inline empty state or just the create button
   - Recommendation: Simple empty state with "No API keys yet" text and a prominent "Create API Key" button. Modal for creation.

4. **Should the `api_v1_router` use `CurrentUser` (JWT dependency) or `ApiAuthUser` (unified dependency) for the APIKEY CRUD endpoints?**
   - What we know: Phase 38 adds both the APIKEY management endpoints AND the unified auth dependency
   - What's unclear: The APIKEY CRUD endpoints themselves (create/list/revoke) — should they accept JWT (users managing their own keys from the frontend) or only API keys?
   - Recommendation: APIKEY CRUD endpoints should use the existing `CurrentUser` (JWT dependency), NOT the new `get_authenticated_user()`. Users create/manage keys via the frontend (authenticated via JWT). The `get_authenticated_user()` unified dependency is for future Phase 40 endpoints that external API callers call.

---

## Sources

### Primary (HIGH confidence)
- `backend/app/main.py` — SPECTRA_MODE gate pattern, router mounting, existing mode validation
- `backend/app/dependencies.py` — `get_current_user()` pattern to extend
- `backend/app/routers/auth.py` — SHA-256 token hashing pattern (invitation tokens, reset tokens)
- `backend/app/services/credit.py` — `CreditService` class pattern for `ApiKeyService`
- `backend/app/models/invitation.py`, `password_reset.py` — token_hash storage model pattern
- `backend/app/config.py` — `SPECTRA_MODE` validator and `Settings` class
- `backend/alembic/env.py` — model import requirement for Alembic autogenerate
- `backend/alembic/versions/e49613642cfe_add_search_quotas_table.py` — migration pattern
- `.planning/STATE.md` — locked decisions: SHA-256, `spe_` prefix, `get_authenticated_user()` architecture, `scopes`/`expires_at` schema, 120s timeout
- `frontend/src/hooks/useSettings.ts` — TanStack Query hook pattern
- `frontend/src/app/(dashboard)/settings/page.tsx` — settings page component pattern

### Secondary (MEDIUM confidence)
- `compose.yaml` — `SPECTRA_MODE: dev` confirms docker-compose always uses dev mode; APIINFRA-05 is satisfied by the `if mode in ("api", "dev"):` block
- `backend/pyproject.toml` — confirmed no new packages needed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project; no new dependencies
- Architecture: HIGH — all patterns derived directly from existing codebase code, plus explicit locked decisions in STATE.md
- Pitfalls: HIGH — derived from direct code inspection of config.py validator, alembic/env.py import list, main.py mode checks

**Research date:** 2026-02-23
**Valid until:** 2026-03-25 (30 days; stable patterns)
