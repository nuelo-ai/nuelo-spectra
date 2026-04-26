# Phase 60: Config-Driven Pricing & Startup Sync - Pattern Map

**Mapped:** 2026-04-23
**Files analyzed:** 5 new/modified files
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/config/user_classes.yaml` | config | static | (self -- extend existing) | exact |
| `backend/app/services/user_class.py` | service | transform | (self -- extend existing) | exact |
| `backend/app/services/pricing_sync.py` | service | batch | `backend/app/services/platform_settings.py` | role-match |
| `backend/app/services/platform_settings.py` | service | CRUD | (self -- modify DEFAULTS) | exact |
| `backend/app/routers/admin/billing_settings.py` | controller | request-response | (self -- add guard) | exact |

## Pattern Assignments

### `backend/app/config/user_classes.yaml` (config, static)

**Analog:** Self (extend existing file)

**Current structure** (lines 1-31):
```yaml
user_classes:
  free_trial:
    display_name: "Free Trial"
    credits: 100
    reset_policy: none
    trial_duration_days: 7
    workspace_access: true
    max_active_collections: 1
  standard:
    display_name: "Standard"
    credits: 100
    reset_policy: none
    workspace_access: true
    max_active_collections: 5
```

**Extension pattern:** Add `has_plan: false/true` and `price_cents: NNNN` as flat fields in each tier block (D-02). Add `credit_packages:` as a new top-level key alongside `user_classes:` (D-01). Field names match CreditPackage model columns (D-03).

---

### `backend/app/services/user_class.py` (service, transform)

**Analog:** Self (extend existing file)

**YAML loading + cache pattern** (lines 17-34):
```python
def get_user_classes() -> dict:
    """Load and cache the full user_classes dict from YAML."""
    global _user_classes_cache, _cache_loaded_at

    now = time.time()
    if _user_classes_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _user_classes_cache

    with open(_CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)

    _user_classes_cache = data["user_classes"]
    _cache_loaded_at = now
    return _user_classes_cache
```

**Extension pattern:** Add a new `get_credit_packages() -> list[dict]` function that reads `data["credit_packages"]` from the same YAML file. Use the same TTL cache pattern. The YAML `data` variable already contains both keys after `yaml.safe_load()` -- just need to cache and return `data["credit_packages"]` separately (or share the parsed `data` between both getters).

**Cache invalidation pattern** (lines 48-51):
```python
def invalidate_cache() -> None:
    """Clear the user classes cache. Useful for testing."""
    global _user_classes_cache, _cache_loaded_at
    _user_classes_cache = None
    _cache_loaded_at = 0.0
```

---

### `backend/app/services/pricing_sync.py` (service, batch) -- NEW FILE

**Analog:** `backend/app/services/platform_settings.py` (for DB upsert pattern) + `backend/app/routers/admin/billing_settings.py` (for Stripe Price creation pattern)

**Imports pattern** (from platform_settings.py lines 1-16 + subscription.py lines 1-17):
```python
import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.credit_package import CreditPackage
from app.models.platform_setting import PlatformSetting
from app.services.platform_settings import get as get_setting, upsert, invalidate_cache
from app.services.user_class import get_user_classes, get_credit_packages
```

**DB upsert pattern** (from platform_settings.py lines 83-109):
```python
async def upsert(db: AsyncSession, key: str, value: Any, admin_id: UUID) -> None:
    result = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )
    existing = result.scalar_one_or_none()

    json_value = json.dumps(value)

    if existing:
        existing.value = json_value
        existing.updated_by = admin_id
    else:
        setting = PlatformSetting(
            key=key,
            value=json_value,
            updated_by=admin_id,
        )
        db.add(setting)
```
Note: For startup seeding, pass `admin_id=None` (column is nullable). Use the imported `upsert()` function directly rather than reimplementing.

**Stripe client access pattern** (from subscription.py lines 49-59):
```python
@staticmethod
def _get_stripe_client() -> stripe.StripeClient:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise StripeConfigError("Stripe secret key is not configured")
    return stripe.StripeClient(settings.stripe_secret_key)
```
Call as: `from app.services.subscription import SubscriptionService; client = SubscriptionService._get_stripe_client()`

**Stripe Price creation pattern** (from billing_settings.py lines 108-145):
```python
from app.services.subscription import SubscriptionService

client = SubscriptionService._get_stripe_client()

# Recurring price (subscriptions)
new_price = client.v1.prices.create(
    params={
        "unit_amount": new_price_cents,
        "currency": "usd",
        "recurring": {"interval": "month"},
        "product_data": {
            "name": f"Spectra {tier.title()} Plan",
        },
        "lookup_key": f"{tier}_monthly",
        "transfer_lookup_key": True,
    }
)

# Deactivate old price
if old_stripe_price_id:
    try:
        client.v1.prices.update(
            old_stripe_price_id, params={"active": False}
        )
    except Exception:
        logger.warning("Failed to deactivate old Stripe price: %s", old_stripe_price_id)
```
Note: D-08 mandates separate Product creation (`client.v1.products.create()`) instead of inline `product_data`. Adapt this pattern accordingly.

**Graceful error handling pattern** (from billing_settings.py lines 146-153):
```python
except Exception as e:
    logger.error("Failed to create Stripe price for %s: %s", tier, str(e))
    raise HTTPException(status_code=500, detail=f"Failed to create Stripe price for {tier} plan: {str(e)}")
```
Note: For startup Stripe sync, use `logger.warning()` and continue instead of raising (D-05 graceful failure). For DB seeding errors, let exceptions propagate (D-05 fail-fast).

**SPECTRA_MODE guard pattern** (from config.py lines 84, 108):
```python
from app.config import get_settings
settings = get_settings()
if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
    # Run Stripe sync
else:
    logger.info("Stripe sync skipped (mode=%s)", settings.spectra_mode)
```

**CreditPackage model pattern** (from credit_package.py lines 11-28):
```python
class CreditPackage(Base):
    __tablename__ = "credit_packages"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    credit_amount: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```
Use this for credit package seeding: insert rows with `name`, `credit_amount`, `price_cents`, `display_order` from config. Leave `stripe_price_id=None` for Stripe sync to fill.

---

### `backend/app/services/platform_settings.py` (service, CRUD) -- MODIFY

**Analog:** Self

**DEFAULTS dict** (lines 25-37):
```python
DEFAULTS: dict[str, str] = {
    "allow_public_signup": json.dumps(True),
    "default_user_class": json.dumps("free_trial"),
    "invite_expiry_days": json.dumps(7),
    "default_credit_cost": json.dumps("1.0"),
    "max_pending_invites": json.dumps(50),
    "workspace_credit_cost_pulse": json.dumps("5.0"),
    "stripe_price_standard_monthly": json.dumps(""),
    "stripe_price_premium_monthly": json.dumps(""),
    "price_standard_monthly_cents": json.dumps(2900),
    "price_premium_monthly_cents": json.dumps(7900),
    "monetization_enabled": json.dumps(True),
}
```
**Change:** Line 37 -- `json.dumps(True)` becomes `json.dumps(False)` per D-06.

---

### `backend/app/routers/admin/billing_settings.py` (controller, request-response) -- MODIFY

**Analog:** Self

**PUT endpoint validation pattern** (lines 73-85):
```python
@router.put("", response_model=BillingSettingsResponse)
async def update_billing_settings(
    body: BillingSettingsUpdateRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    updates = body.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Validate each setting
    for field_name, value in updates.items():
        key = _FIELD_TO_KEY.get(field_name)
        if not key:
            continue
        error = validate_setting(key, value)
        if error:
            raise HTTPException(status_code=422, detail=error)
```
**Extension pattern:** Add monetization toggle guard (D-07) after validation, before upsert. When `monetization_enabled` is being set to `True`, call `check_stripe_readiness(db)` and return 422 if not ready:
```python
# Guard: block monetization_enabled=true if Stripe not ready
if updates.get("monetization_enabled") is True:
    from app.services.pricing_sync import check_stripe_readiness
    readiness = await check_stripe_readiness(db)
    if not readiness["ready"]:
        raise HTTPException(
            status_code=422,
            detail={"message": "Cannot enable monetization", "missing": readiness["missing"]}
        )
```

---

### `backend/app/main.py` (config, startup) -- MODIFY

**Analog:** Self

**Lifespan insertion point** (lines 226-229, after SMTP validation, before checkpointer):
```python
    # Validate SMTP email configuration
    from app.services.email import validate_smtp_connection, is_smtp_configured
    smtp_configured = await validate_smtp_connection(settings)
    if smtp_configured:
        logging.getLogger("spectra.smtp").info("SMTP connection validated - email delivery active")
```
**Insert after SMTP block (line 228), before checkpointer block (line 230):**
```python
    # Seed pricing config to database and sync Stripe (Phase 60)
    from app.database import async_session_maker
    from app.services.pricing_sync import seed_pricing_from_config
    async with async_session_maker() as db:
        await seed_pricing_from_config(db)
        await db.commit()
```
Uses `async_session_maker` from `database.py` (line 16 of database.py) -- same factory all services use.

## Shared Patterns

### Stripe Client Access
**Source:** `backend/app/services/subscription.py` lines 49-59
**Apply to:** `pricing_sync.py` (all Stripe operations)
```python
from app.services.subscription import SubscriptionService
client = SubscriptionService._get_stripe_client()
```

### Platform Settings Upsert
**Source:** `backend/app/services/platform_settings.py` lines 83-109
**Apply to:** `pricing_sync.py` (subscription pricing seeding)
```python
from app.services.platform_settings import upsert, invalidate_cache
await upsert(db, key, value, admin_id=None)
# After all seeding:
invalidate_cache()
```

### TTL Cache + Invalidation
**Source:** `backend/app/services/user_class.py` lines 9-13, 48-51
**Apply to:** `user_class.py` extension (credit packages cache), `pricing_sync.py` (invalidate after seeding)
```python
_user_classes_cache: dict | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

def invalidate_cache() -> None:
    global _user_classes_cache, _cache_loaded_at
    _user_classes_cache = None
    _cache_loaded_at = 0.0
```

### Logging Convention
**Source:** `backend/app/main.py` lines 217, 223, 227, 247
**Apply to:** `pricing_sync.py` (all seeding/sync log messages)
```python
logger = logging.getLogger("spectra.pricing")
logger.info("Subscription pricing seeded from config")
logger.warning("Stripe sync failed for %s: %s", tier_name, str(e))
```
Uses `spectra.*` namespace consistent with other lifespan loggers.

### DB Query Pattern (CreditPackage)
**Source:** `backend/app/routers/credits.py` lines 1-18
**Apply to:** `pricing_sync.py` (credit package seeding + readiness check)
```python
from sqlalchemy import select
from app.models.credit_package import CreditPackage

result = await db.execute(
    select(CreditPackage).where(CreditPackage.is_active == True)
)
packages = result.scalars().all()
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/tests/test_pricing_sync.py` | test | batch | No existing test file for pricing sync; use pytest-asyncio patterns from RESEARCH.md |

The test file has no direct analog in the codebase. Planner should reference RESEARCH.md Validation Architecture section for test structure (pytest + pytest-asyncio, mock Stripe client, async DB session fixture).

## Metadata

**Analog search scope:** `backend/app/services/`, `backend/app/routers/admin/`, `backend/app/config/`, `backend/app/models/`, `backend/app/main.py`
**Files scanned:** 8
**Pattern extraction date:** 2026-04-23
