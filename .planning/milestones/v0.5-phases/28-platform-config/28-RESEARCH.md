# Phase 28: Platform Config - Research

**Researched:** 2026-02-16
**Domain:** Backend settings API, tier management, signup control (FastAPI + SQLAlchemy)
**Confidence:** HIGH

## Summary

Phase 28 builds runtime platform configuration on top of infrastructure already in place: the `platform_settings` table exists (key-value with `key`, `value` TEXT, `updated_at`, `updated_by`), the `PlatformSetting` model is registered, the `user_classes.yaml` config is loaded by `UserClassService` with 30s TTL cache, and the `User.user_class` field (String(20)) is already on the users table. The `Invitation` model also exists with `token_hash`, `status`, `expires_at` fields.

The work is primarily: (1) a `PlatformSettingsService` for cached read/write of settings, (2) admin API endpoints for settings CRUD and tier management, (3) modifying the signup flow to check `allow_public_signup` setting, and (4) modifying the frontend registration page to show an invite-only message when signup is disabled.

**Primary recommendation:** Build a thin `PlatformSettingsService` with module-level dict cache (same pattern as `user_class.py`), a flat admin settings API with partial-update PATCH semantics, and integrate signup gating at the existing `auth_service.create_user()` call site.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- When signup is disabled, registration page still renders but form is hidden/disabled, replaced with message: "Thank you for your interest. We are currently open for beta test invitees only. Please send us an email as per the contact if you are interested to participate."
- Signup toggle takes effect immediately -- no grace period. If someone submits the form after toggle, they get rejected
- Default tier for new signups (public or invite) is configurable in platform settings (not hardcoded to free)
- Tier credit allocations are read-only from `user_classes.yaml` -- no admin override through platform_settings in this phase
- Admin can view tier summary: tier name, credit allocation (from yaml), and user count per tier
- Admin can assign/change a user's tier
- When admin changes a user's tier, their credit balance resets to the new tier's allocation
- Tier allocation changes (yaml edits) apply to existing users on next scheduled reset only, not immediately
- Individual per-user credit adjustments remain available via Phase 27's admin credit endpoints
- Registration page should feel informative, not like an error -- user sees the page with the message, not a redirect

### Claude's Discretion
- Settings API shape and update patterns
- Validation strategy
- Response metadata structure
- Cache invalidation approach (30s TTL already decided in architecture)

### Deferred Ideas (OUT OF SCOPE)
- Admin-editable credit overrides per tier via platform_settings UI -- deferred to future milestone. For now, tier credit allocations can only be changed by editing `user_classes.yaml`
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETTINGS-01 | Centralized settings page for global platform configuration | Admin settings API (flat endpoint) + Phase 31 admin frontend (backend-only this phase) |
| SETTINGS-02 | Signup toggle setting (allow_public_signup: true/false) | `PlatformSettingsService.get("allow_public_signup")` with default `true`; checked in signup endpoint |
| SETTINGS-03 | Default user class for new signups setting | Replace hardcoded `get_default_class()` with `PlatformSettingsService.get("default_user_class")` |
| SETTINGS-04 | Invite link expiry duration setting (days) | `invite_expiry_days` key in platform_settings; used when creating invitations |
| SETTINGS-05 | Credit reset policy setting (manual / weekly auto-reset / monthly auto-reset) | `credit_reset_policy` key; scheduler reads from settings service instead of per-class yaml |
| SETTINGS-06 | Credit amount overrides per user class | DEFERRED per user decision -- tier allocations read-only from yaml this phase |
| SETTINGS-07 | Default credit cost per message setting | Replace `_DEFAULT_CREDIT_COST = Decimal("1.0")` in `chat.py` with settings service read |
| SETTINGS-08 | Settings persisted in platform_settings table with 30s TTL cache | `PlatformSettingsService` with module-level cache, same pattern as `user_class.py` |
| TIER-01 | User classes defined in user_classes.yaml | Already implemented in `app/services/user_class.py` -- no changes needed |
| TIER-02 | Admin can edit credit amounts per tier | DEFERRED per user decision -- read-only from yaml this phase |
| TIER-03 | Adding/removing tiers requires config change + redeployment | Already true by design -- yaml-based, no DB tiers |
| TIER-04 | Users table has user_class field | Already implemented: `User.user_class = String(20), default="free"` |
| TIER-05 | Admin can view all tiers with current credit allocations | New admin endpoint reading `get_user_classes()` + user count query |
| TIER-06 | Admin can assign or change a user's tier manually | New admin endpoint: update `User.user_class` + reset credits to new tier allocation |
| TIER-07 | Admin can view how many users are in each tier | SQL `GROUP BY user_class` query -- similar to existing `get_credit_distribution()` |
| SIGNUP-01 | Global toggle: allow public signup | `allow_public_signup` setting key, default `true` |
| SIGNUP-02 | When disabled, signup page shows invite-only message | Frontend: check public endpoint `/auth/signup-status`; conditionally render message |
| SIGNUP-03 | When disabled, only users with valid invite token can register | Backend: signup endpoint checks setting; if disabled, requires `invite_token` field |
| SIGNUP-04 | Toggle changes take effect immediately | 30s TTL cache ensures near-immediate effect; no restart needed |
</phase_requirements>

## Standard Stack

### Core (already in codebase)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | API framework | Already used throughout |
| SQLAlchemy 2.x | (existing) | Async ORM | Already used with mapped_column pattern |
| Pydantic v2 | (existing) | Request/response schemas | Already used for all schemas |
| PyYAML | (existing) | user_classes.yaml loading | Already used in user_class.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | -- | Serialize/deserialize platform_settings values | Values stored as JSON text in DB |

### No New Dependencies
This phase requires zero new libraries. Everything needed is already in the project.

## Architecture Patterns

### Recommended Project Structure (new files only)
```
backend/app/
  services/
    platform_settings.py      # NEW: PlatformSettingsService with TTL cache
    admin/
      settings.py             # NEW: Admin settings business logic
      tiers.py                # NEW: Admin tier management business logic
  routers/admin/
    settings.py               # NEW: Admin settings API endpoints
    tiers.py                  # NEW: Admin tier management endpoints
  schemas/
    platform_settings.py      # NEW: Pydantic schemas for settings API
```

### Pattern 1: Module-Level TTL Cache (proven pattern in codebase)
**What:** Cache platform settings in a module-level dict with 30s TTL, same as `user_class.py`
**When to use:** For all platform settings reads (hot path for signup check, credit cost, etc.)
**Example:**
```python
# Source: app/services/user_class.py (existing pattern)
import json
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.platform_setting import PlatformSetting

_settings_cache: dict[str, str] | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

# Default values for all known settings
_DEFAULTS: dict[str, str] = {
    "allow_public_signup": json.dumps(True),
    "default_user_class": json.dumps("free"),
    "invite_expiry_days": json.dumps(7),
    "credit_reset_policy": json.dumps("weekly"),
    "default_credit_cost": json.dumps(1.0),
}

async def get_all_settings(db: AsyncSession) -> dict[str, str]:
    """Load all settings with 30s TTL cache."""
    global _settings_cache, _cache_loaded_at
    now = time.time()
    if _settings_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _settings_cache

    result = await db.execute(select(PlatformSetting))
    rows = result.scalars().all()
    loaded = {row.key: row.value for row in rows}

    # Merge defaults for any missing keys
    merged = {**_DEFAULTS, **loaded}
    _settings_cache = merged
    _cache_loaded_at = now
    return merged

async def get_setting(db: AsyncSession, key: str) -> any:
    """Get a single parsed setting value."""
    settings = await get_all_settings(db)
    raw = settings.get(key, _DEFAULTS.get(key))
    return json.loads(raw) if raw else None

def invalidate_cache() -> None:
    """Invalidate after admin writes."""
    global _settings_cache, _cache_loaded_at
    _settings_cache = None
    _cache_loaded_at = 0.0
```

### Pattern 2: Admin Router Registration (proven pattern in codebase)
**What:** Register new admin routers in `app/routers/admin/__init__.py`
**When to use:** Adding new admin endpoint modules
**Example:**
```python
# Source: app/routers/admin/__init__.py (extend existing)
from app.routers.admin import settings as admin_settings
from app.routers.admin import tiers as admin_tiers

admin_router.include_router(admin_settings.router)
admin_router.include_router(admin_tiers.router)
```

### Pattern 3: Flat Settings API with Partial PATCH
**What:** Single endpoint for reading all settings, PATCH for partial updates
**When to use:** Admin settings API -- simplest approach for key-value table
**Rationale:** Flat is appropriate because there are only ~5 settings. Grouping by domain would over-engineer. PATCH with partial dict matches the key-value table design naturally.
```python
# GET /api/admin/settings -> returns all settings as flat dict
# PATCH /api/admin/settings -> accepts partial dict, upserts changed keys

@router.get("/settings")
async def get_settings(db: DbSession, admin: CurrentAdmin) -> dict:
    settings = await get_all_settings(db)
    return {k: json.loads(v) for k, v in settings.items()}

@router.patch("/settings")
async def update_settings(
    body: SettingsUpdateRequest,  # dict of key-value pairs
    db: DbSession,
    admin: CurrentAdmin,
    request: Request,
) -> dict:
    # Validate each key
    # Upsert each changed key
    # Invalidate cache
    # Audit log
    ...
```

### Pattern 4: Public Signup Status Endpoint (unauthenticated)
**What:** Public endpoint the registration page calls to check if signup is allowed
**When to use:** Frontend needs to know signup status BEFORE user is authenticated
```python
# GET /auth/signup-status -> {"signup_allowed": true/false, "message": "..."}
# No auth required -- this is a public endpoint
```

### Pattern 5: Strict Validation with Pydantic
**What:** Validate each setting key and value type strictly before writing
**When to use:** Admin settings update -- prevent invalid values from corrupting platform behavior
**Rationale:** Platform settings affect core behavior (signup, credits). Invalid values could break the platform. Better to reject at API level than discover at runtime.
```python
# Define allowed keys and their Pydantic validators
SETTING_VALIDATORS = {
    "allow_public_signup": bool,
    "default_user_class": str,  # must be in user_classes.yaml keys
    "invite_expiry_days": int,  # must be 1-365
    "credit_reset_policy": str,  # must be in {"manual", "weekly", "monthly"}
    "default_credit_cost": float,  # must be > 0
}
```

### Anti-Patterns to Avoid
- **Storing settings in .env or config.py:** These require restart. Platform settings must be in DB for runtime changes.
- **Per-request DB query without cache:** Settings are read on every signup attempt and every chat message. Must use TTL cache.
- **Separate cache per setting key:** Load all settings at once (there are only ~5). Single cache dict, single DB query.
- **Returning stale data after write:** Always `invalidate_cache()` after any admin write to settings.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTL caching | Custom async cache decorator | Module-level dict + timestamp (existing pattern) | Already proven in `user_class.py`, zero dependencies |
| JSON serialization for DB text column | Custom serializer | `json.dumps()` / `json.loads()` | Stdlib, simple, values are always JSON |
| Setting validation | Manual if/else chains | Pydantic model with field validators | Already using Pydantic everywhere; catches type errors at API boundary |
| Tier user counts | Manual loops | SQLAlchemy `GROUP BY` | Single efficient query; pattern exists in `get_credit_distribution()` |

**Key insight:** The existing codebase patterns are exactly what this phase needs. No new abstractions required -- just new instances of proven patterns.

## Common Pitfalls

### Pitfall 1: Cache Stale After Admin Write
**What goes wrong:** Admin updates a setting, but the cache still serves the old value for up to 30 seconds.
**Why it happens:** TTL cache doesn't invalidate on write.
**How to avoid:** Call `invalidate_cache()` in the same request handler that writes the setting. The admin's next GET will see fresh data. Other instances (in multi-process deployment) will pick up within 30s.
**Warning signs:** Admin toggles signup off but can still register for 30 seconds.

### Pitfall 2: Signup Race Condition
**What goes wrong:** User loads registration page (signup allowed), admin toggles signup off, user submits form -- should be rejected.
**Why it happens:** Frontend checked status at page load but backend must re-check at form submission.
**How to avoid:** Backend signup endpoint ALWAYS checks `allow_public_signup` setting at request time, regardless of what frontend showed. Frontend check is cosmetic only.
**Warning signs:** Registration succeeds despite setting being disabled.

### Pitfall 3: Tier Change Without Credit Reset
**What goes wrong:** Admin changes user from free (10 credits) to premium (500 credits) but balance stays at 3.
**Why it happens:** Forgot to reset credits when changing tier.
**How to avoid:** Tier change endpoint MUST atomically: (1) update `User.user_class`, (2) reset `UserCredit.balance` to new tier allocation, (3) log a credit transaction.
**Warning signs:** User tier shows "Premium" but balance is stuck at old value.

### Pitfall 4: Invalid default_user_class Breaks Signup
**What goes wrong:** Admin sets `default_user_class` to "gold" which doesn't exist in `user_classes.yaml`.
**Why it happens:** No validation against yaml keys.
**How to avoid:** Validate `default_user_class` value against `get_user_classes().keys()` before saving.
**Warning signs:** New user registration crashes with KeyError or gets user_class that has no credit config.

### Pitfall 5: Signup Status Endpoint Requires Auth
**What goes wrong:** Registration page can't check if signup is allowed because the endpoint requires a JWT.
**Why it happens:** All endpoints default to requiring auth.
**How to avoid:** `GET /auth/signup-status` must be a public (unauthenticated) endpoint, like login/register.
**Warning signs:** Registration page shows spinner forever or fails silently.

### Pitfall 6: SETTINGS-05 vs user_classes.yaml reset_policy Conflict
**What goes wrong:** Platform setting `credit_reset_policy` says "monthly" but yaml says "weekly" per tier.
**Why it happens:** Unclear which takes precedence.
**How to avoid:** Per context decisions, SETTINGS-05 is a global override. But per the deferred decisions, tier-level overrides are out of scope. Resolution: SETTINGS-05 is the GLOBAL default policy. Individual tiers still use their yaml `reset_policy`. If the user wants SETTINGS-05 to override per-tier, that's a future phase decision. For now, store it but don't override yaml.
**Warning signs:** Confusion about which reset policy applies.

## Code Examples

### Creating PlatformSettingsService
```python
# app/services/platform_settings.py
"""Platform settings service with 30s TTL cache."""

import json
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_setting import PlatformSetting

_settings_cache: dict[str, str] | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

DEFAULTS: dict[str, str] = {
    "allow_public_signup": json.dumps(True),
    "default_user_class": json.dumps("free"),
    "invite_expiry_days": json.dumps(7),
    "credit_reset_policy": json.dumps("weekly"),
    "default_credit_cost": json.dumps(1.0),
}

VALID_KEYS = set(DEFAULTS.keys())


async def get_all(db: AsyncSession) -> dict[str, str]:
    """Load all platform settings with 30s TTL cache."""
    global _settings_cache, _cache_loaded_at
    now = time.time()
    if _settings_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _settings_cache

    result = await db.execute(select(PlatformSetting))
    rows = result.scalars().all()
    loaded = {row.key: row.value for row in rows}
    merged = {**DEFAULTS, **loaded}
    _settings_cache = merged
    _cache_loaded_at = now
    return merged


async def get(db: AsyncSession, key: str):
    """Get a single parsed setting value."""
    all_settings = await get_all(db)
    raw = all_settings.get(key, DEFAULTS.get(key))
    return json.loads(raw) if raw else None


async def upsert(db: AsyncSession, key: str, value, admin_id: UUID) -> None:
    """Upsert a single setting."""
    result = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )
    existing = result.scalar_one_or_none()
    json_value = json.dumps(value)

    if existing:
        existing.value = json_value
        existing.updated_at = datetime.now(timezone.utc)
        existing.updated_by = admin_id
    else:
        db.add(PlatformSetting(
            key=key,
            value=json_value,
            updated_at=datetime.now(timezone.utc),
            updated_by=admin_id,
        ))


def invalidate_cache() -> None:
    """Clear cache after writes."""
    global _settings_cache, _cache_loaded_at
    _settings_cache = None
    _cache_loaded_at = 0.0
```

### Admin Tier Summary Endpoint
```python
# Query pattern for tier summary with user counts
from sqlalchemy import func, select
from app.models.user import User
from app.services.user_class import get_user_classes

async def get_tier_summary(db: AsyncSession) -> list[dict]:
    """Get all tiers with credit allocations and user counts."""
    # Get user counts per class from DB
    result = await db.execute(
        select(
            User.user_class,
            func.count(User.id).label("user_count"),
        )
        .where(User.is_active == True)
        .group_by(User.user_class)
    )
    counts = {row.user_class: row.user_count for row in result.all()}

    # Merge with yaml config
    classes = get_user_classes()
    summary = []
    for class_name, config in classes.items():
        summary.append({
            "name": class_name,
            "display_name": config.get("display_name", class_name),
            "credits": config.get("credits", 0),
            "reset_policy": config.get("reset_policy", "none"),
            "user_count": counts.get(class_name, 0),
        })
    return summary
```

### Tier Change with Credit Reset
```python
# Pattern for changing user tier with atomic credit reset
async def change_user_tier(
    db: AsyncSession, user_id: UUID, new_class: str, admin_id: UUID
) -> None:
    """Change user tier and reset credits to new tier's allocation."""
    from app.services.user_class import get_class_config
    from app.models.user_credit import UserCredit

    class_config = get_class_config(new_class)
    if class_config is None:
        raise ValueError(f"Unknown user class: {new_class}")

    # Update user class
    user = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user_row = user.scalar_one_or_none()
    if not user_row:
        raise ValueError("User not found")

    old_class = user_row.user_class
    user_row.user_class = new_class

    # Reset credits to new tier allocation
    new_allocation = class_config.get("credits", 0)
    credit_result = await db.execute(
        select(UserCredit).where(UserCredit.user_id == user_id).with_for_update()
    )
    credit = credit_result.scalar_one_or_none()
    if credit:
        await CreditService.execute_reset(
            db, credit, new_allocation, transaction_type="tier_change"
        )
```

### Signup Gating in Backend
```python
# In auth_service.create_user() or the signup router
async def signup(signup_data: SignupRequest, db: AsyncSession, ...):
    # Check if public signup is allowed
    allow_signup = await platform_settings.get(db, "allow_public_signup")
    if not allow_signup:
        # Check for invite token
        if not signup_data.invite_token:
            raise HTTPException(
                status_code=403,
                detail="Public registration is currently disabled. An invitation is required."
            )
        # Validate invite token...
```

### Frontend Signup Status Check
```typescript
// In register/page.tsx
const [signupAllowed, setSignupAllowed] = useState<boolean | null>(null);

useEffect(() => {
  fetch("http://localhost:8000/auth/signup-status")
    .then(r => r.json())
    .then(data => setSignupAllowed(data.signup_allowed))
    .catch(() => setSignupAllowed(true)); // Fail open for frontend display
}, []);

// Render: if signupAllowed === false, show the branded message
// else show the normal form
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded `get_default_class()` returns "free" | Read from `platform_settings` | This phase | Default tier becomes runtime-configurable |
| Hardcoded `_DEFAULT_CREDIT_COST = Decimal("1.0")` | Read from `platform_settings` | This phase | Cost per message becomes runtime-configurable |
| No signup gating | Check `allow_public_signup` before registration | This phase | Invite-only mode possible |

**Already in place (no migration needed):**
- `platform_settings` table exists (created in Phase 26 migration)
- `PlatformSetting` model registered
- `Invitation` model and table exist
- `User.user_class` field exists as String(20)
- `UserCredit` model with `balance` and `last_reset_at` exists

## Open Questions

1. **SETTINGS-05 (credit_reset_policy) scope**
   - What we know: The yaml defines reset_policy per tier. The requirement says "Credit reset policy setting (manual / weekly auto-reset / monthly auto-reset)".
   - What's unclear: Is this a global override for ALL tiers, or just a default? The context decisions say tier allocations are read-only from yaml, which includes reset_policy.
   - Recommendation: Store it in platform_settings but treat it as informational / future use. The scheduler continues reading per-tier reset_policy from yaml. Document this in the API response so it's clear to the admin frontend in Phase 31.

2. **SETTINGS-06 (credit overrides) -- DEFERRED**
   - What we know: Explicitly deferred per user decision.
   - Recommendation: Don't implement the `tier_credit_overrides` key. TIER-02 and SETTINGS-06 are out of scope for this phase.

3. **Invite token validation flow**
   - What we know: `Invitation` model exists with `token_hash`, `status`, `expires_at`. The signup form needs an optional `invite_token` field.
   - What's unclear: Full invite token validation (hash lookup, expiry check, status update) -- this may be partial implementation since invite creation endpoints are not in scope.
   - Recommendation: Implement the validation side (check token on signup). Invite creation can be a separate admin endpoint added in the same or next phase.

## Sources

### Primary (HIGH confidence)
- Codebase: `app/models/platform_setting.py` -- existing model, table structure
- Codebase: `app/services/user_class.py` -- proven TTL cache pattern
- Codebase: `app/services/credit.py` -- CreditService patterns for balance reset
- Codebase: `app/routers/admin/credits.py` -- admin endpoint patterns (CurrentAdmin, audit logging)
- Codebase: `app/services/auth.py` -- signup flow with `get_default_class()` TODO
- Codebase: `app/routers/chat.py` -- `_DEFAULT_CREDIT_COST` TODO
- Codebase: `app/models/invitation.py` -- invitation model structure
- Codebase: `alembic/versions/dfe836ff84e9_*.py` -- platform_settings table already migrated
- Codebase: `frontend/src/app/(auth)/register/page.tsx` -- current registration page

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions -- user-locked decisions on signup behavior and tier management

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies; all patterns already in codebase
- Architecture: HIGH -- extending existing patterns (TTL cache, admin routers, audit logging)
- Pitfalls: HIGH -- based on actual code analysis of race conditions and integration points
- Requirements mapping: HIGH -- each requirement has clear implementation path in existing code

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable -- no external dependencies, all internal patterns)
