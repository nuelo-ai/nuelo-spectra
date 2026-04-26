# Phase 60: Config-Driven Pricing & Startup Sync - Research

**Researched:** 2026-04-23
**Domain:** YAML config parsing, database seeding, Stripe Product/Price API
**Confidence:** HIGH

## Summary

Phase 60 transforms hardcoded pricing defaults into config-driven values read from `user_classes.yaml`, automatically seeded to the database on first startup, and auto-provisioned in Stripe. The codebase already has all the building blocks: YAML loading with TTL cache (`user_class.py`), platform_settings upsert with cache invalidation, CreditPackage model, and Stripe `client.v1.prices.create()` patterns in `billing_settings.py`.

The primary work is: (1) extend `user_classes.yaml` with `has_plan`, `price_cents`, and `credit_packages` sections, (2) write a startup seeding function called from `lifespan()` that fills empty DB values from config, (3) write a Stripe sync function that creates Products/Prices for any tier or package missing a `stripe_price_id`, and (4) add a Stripe readiness check utility that gates `monetization_enabled=true`.

**Primary recommendation:** Build a single `backend/app/services/pricing_sync.py` module containing all seeding and Stripe sync logic, keeping `lifespan()` clean with a single async call. Re-use the existing `SubscriptionService._get_stripe_client()` pattern and `platform_settings.upsert()` for all DB writes.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Credit packages defined in `user_classes.yaml` under `credit_packages:` top-level key
- **D-02:** Tier pricing uses flat fields `has_plan: true` and `price_cents: 2900` in each tier block
- **D-03:** Credit package entries use fields matching CreditPackage model: `name`, `price_cents`, `credit_amount`, `display_order`
- **D-04:** Config-to-DB seeding runs in `lifespan()` in `main.py`, after LLM/SMTP validation but before scheduler. Idempotent (fills gaps only)
- **D-05:** DB seeding failures are fail-fast. Stripe API failures are graceful (log warning, continue)
- **D-06:** `monetization_enabled` defaults to `false` (change DEFAULTS from `True` to `False`)
- **D-07:** Stripe readiness check utility validates all tiers/packages have `stripe_price_id` + `STRIPE_SECRET_KEY` configured. Blocks `monetization_enabled=true` in PUT endpoint (returns 422)
- **D-08:** One Stripe Product per tier/package with one Price attached
- **D-09:** Stripe auto-provisioning only runs in `dev` and `public` SPECTRA_MODEs. DB seeding runs in all modes
- **D-10:** v0.8.x to v0.10 upgrade path: Alembic migrations, lifespan seeds, monetization off by default
- **D-11:** Subscription pricing reset: overwrite DB with config, deactivate old Stripe Prices, create new ones. Existing subscribers grandfathered
- **D-12:** Credit package reset: overwrite DB rows to match config. Packages not in config deactivated (`is_active=false`), never deleted

### Claude's Discretion
- Stripe Product naming convention details (exact prefix, metadata fields)
- Startup sync ordering between subscription pricing and credit packages
- Logging verbosity and format for sync operations
- Internal implementation of the idempotent "fill gaps" check

### Deferred Ideas (OUT OF SCOPE)
- Retroactive price updates for existing subscribers
- Per-environment pricing overrides

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SUB-01 | User classes config includes `has_plan` flag | Extend `user_classes.yaml` tier blocks; update `get_user_classes()` return type |
| SUB-02 | User classes config includes `price_cents` for tiers with `has_plan: true` | Same YAML extension; validated during config loading |
| SUB-03 | Default subscription pricing seeded to platform_settings on first startup | Seeding function checks for empty `stripe_price_*` and `price_*_cents` keys, calls `upsert()` |
| SUB-04 | Stripe Products/Prices auto-created for subscription tiers missing Stripe Price ID | Stripe sync uses `client.v1.products.create()` + `client.v1.prices.create()` with `recurring` param |
| PKG-01 | Default credit packages defined in config file | `credit_packages:` section in `user_classes.yaml` |
| PKG-02 | Credit packages from config seeded to DB on first startup | Seeding function inserts CreditPackage rows when table is empty |
| PKG-03 | Stripe Products/Prices auto-created for credit packages missing Stripe Price ID | Stripe sync uses one-time Price (no `recurring` param) for each package |
| SAFE-01 | Existing admin-customized Stripe Price IDs preserved | Seeding is idempotent: only fills empty/missing values |
| SAFE-02 | No manual Stripe Price ID configuration needed for initial deployment | Auto-provisioning creates all Stripe objects on first startup |

</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| YAML config definition | Config / Static | -- | Static file read at startup, cached |
| DB seeding (platform_settings + credit_packages) | API / Backend | Database | Backend writes config defaults to DB on startup |
| Stripe Product/Price provisioning | API / Backend | -- | Server-side Stripe API calls require secret key |
| Monetization toggle guard | API / Backend | -- | Validation logic in PUT endpoint |
| Reset-to-defaults | API / Backend | Database | Backend overwrites DB values, manages Stripe lifecycle |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stripe | >=14.0.0,<15.0 | Stripe API client | Already pinned in project pyproject.toml [VERIFIED: pyproject.toml] |
| PyYAML | (existing) | YAML config parsing | Already used by `user_class.py` for `user_classes.yaml` [VERIFIED: codebase] |
| SQLAlchemy | (existing) | Async ORM for DB operations | Project standard, `async_session_maker` pattern [VERIFIED: database.py] |
| FastAPI | (existing) | API framework / lifespan hook | `lifespan()` in `main.py` is the integration point [VERIFIED: main.py] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | (existing) | Config validation | Already used for Settings class, can validate YAML schema |

No new dependencies required. All libraries are already in the project.

## Architecture Patterns

### System Architecture Diagram

```
user_classes.yaml
    |
    v
[YAML Loader] -- get_user_classes() + get_credit_packages()
    |                                      |
    v                                      v
[Subscription Pricing Seeder]    [Credit Package Seeder]
    |                                      |
    |  (check: platform_settings empty?)   |  (check: credit_packages empty?)
    |                                      |
    v                                      v
[platform_settings table]         [credit_packages table]
    |                                      |
    |  (check: stripe_price_id empty?)     |  (check: stripe_price_id NULL?)
    |                                      |
    v                                      v
[Stripe Sync: Products + Prices]  [Stripe Sync: Products + Prices]
    |  (recurring monthly)                 |  (one-time)
    |                                      |
    v                                      v
[Store stripe_price_id back to DB] [Store stripe_price_id back to DB]
    |                                      |
    +------- Startup Complete -------------+
                    |
                    v
          [Stripe Readiness Check] <-- billing_settings PUT guard
```

### Recommended Project Structure
```
backend/app/
├── config/
│   └── user_classes.yaml          # Extended with has_plan, price_cents, credit_packages
├── services/
│   ├── user_class.py              # Extended with get_credit_packages()
│   ├── pricing_sync.py            # NEW: seeding + Stripe sync + readiness check + reset
│   ├── platform_settings.py       # DEFAULTS dict updated (monetization_enabled -> false)
│   └── subscription.py            # No changes needed
├── routers/admin/
│   └── billing_settings.py        # PUT endpoint gets monetization toggle guard
└── main.py                        # lifespan() calls pricing_sync.seed_and_sync()
```

### Pattern 1: Idempotent DB Seeding
**What:** Check if value exists before inserting; never overwrite existing values
**When to use:** Every startup, to fill gaps from config without destroying admin edits
**Example:**
```python
# Source: existing platform_settings.py upsert pattern
from app.services.platform_settings import get as get_setting, upsert

async def seed_subscription_pricing(db: AsyncSession, config: dict) -> None:
    """Seed subscription pricing from config. Fills gaps only."""
    for tier_name, tier_config in config.items():
        if not tier_config.get("has_plan"):
            continue
        
        price_key = f"price_{tier_name}_monthly_cents"
        stripe_key = f"stripe_price_{tier_name}_monthly"
        
        # Only seed if no DB value exists
        existing_price = await get_setting(db, price_key)
        if existing_price is None or existing_price == 0:
            await upsert(db, price_key, tier_config["price_cents"], admin_id=None)
        
        # Ensure stripe key exists (empty string = gap to fill)
        existing_stripe = await get_setting(db, stripe_key)
        if existing_stripe is None:
            await upsert(db, stripe_key, "", admin_id=None)
```

### Pattern 2: Stripe Product + Price Creation (Recurring)
**What:** Create a Stripe Product, then attach a recurring monthly Price
**When to use:** For subscription tiers missing a `stripe_price_id`
**Example:**
```python
# Source: Context7 /stripe/stripe-python + existing billing_settings.py pattern
from app.services.subscription import SubscriptionService

async def create_stripe_subscription_price(
    tier_name: str, price_cents: int
) -> str:
    """Create Stripe Product + recurring Price for a subscription tier."""
    client = SubscriptionService._get_stripe_client()
    
    product = client.v1.products.create(
        params={
            "name": f"Spectra {tier_name.title()} Plan",
            "metadata": {"tier": tier_name, "type": "subscription"},
        }
    )
    
    price = client.v1.prices.create(
        params={
            "product": product.id,
            "unit_amount": price_cents,
            "currency": "usd",
            "recurring": {"interval": "month"},
            "lookup_key": f"{tier_name}_monthly",
            "transfer_lookup_key": True,
        }
    )
    return price.id
```

### Pattern 3: Stripe Product + Price Creation (One-Time)
**What:** Create a Stripe Product, then attach a one-time Price for credit packages
**When to use:** For credit packages missing a `stripe_price_id`
**Example:**
```python
# Source: Context7 /stripe/stripe-python
async def create_stripe_package_price(
    package_name: str, price_cents: int, credit_amount: int
) -> str:
    """Create Stripe Product + one-time Price for a credit package."""
    client = SubscriptionService._get_stripe_client()
    
    product = client.v1.products.create(
        params={
            "name": f"Spectra {package_name}",
            "metadata": {
                "type": "credit_package",
                "credit_amount": str(credit_amount),
            },
        }
    )
    
    price = client.v1.prices.create(
        params={
            "product": product.id,
            "unit_amount": price_cents,
            "currency": "usd",
            # No "recurring" = one-time price
        }
    )
    return price.id
```

### Pattern 4: Graceful Stripe Failure
**What:** Stripe errors log warnings but don't block startup
**When to use:** Stripe sync step (D-05)
**Example:**
```python
# Source: D-05 decision
try:
    stripe_price_id = await create_stripe_subscription_price(tier_name, price_cents)
    await upsert(db, stripe_key, stripe_price_id, admin_id=None)
    logger.info("Created Stripe price for %s: %s", tier_name, stripe_price_id)
except Exception as e:
    logger.warning(
        "Stripe sync failed for %s (will retry on next startup): %s",
        tier_name, str(e)
    )
    # Continue -- app works without Stripe Price IDs
```

### Pattern 5: SPECTRA_MODE Guard
**What:** Only run Stripe provisioning in dev/public modes
**When to use:** Wrapping the Stripe sync call
**Example:**
```python
# Source: D-09 decision, existing config.py pattern
from app.config import get_settings

settings = get_settings()
if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
    await sync_stripe_prices(db, tiers_config, packages_config)
else:
    logger.info("Stripe sync skipped (mode=%s)", settings.spectra_mode)
```

### Anti-Patterns to Avoid
- **Overwriting existing DB values:** The seeder MUST check for existing values first. `upsert()` always writes -- the guard must be BEFORE the call, not inside it.
- **Creating duplicate Stripe Products:** Each startup should check `stripe_price_id` is empty before creating. Without this, every restart creates new Products in Stripe.
- **Blocking startup on Stripe errors:** DB seeding is fail-fast (D-05), but Stripe errors must be caught and logged. Mixing these up blocks deployment when Stripe is unavailable.
- **Using module-level cache during seeding:** The TTL cache in `platform_settings.py` may serve stale data during seeding. Call `invalidate_cache()` after seeding completes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Platform settings upsert | Custom INSERT/UPDATE SQL | `platform_settings.upsert()` | Already handles insert-or-update, used everywhere [VERIFIED: platform_settings.py] |
| Stripe client instantiation | Direct `stripe.StripeClient()` | `SubscriptionService._get_stripe_client()` | Handles missing key errors, consistent config [VERIFIED: subscription.py] |
| YAML loading + caching | Custom file reading | Extend `get_user_classes()` pattern | 30s TTL cache already works [VERIFIED: user_class.py] |
| DB session in lifespan | Manual engine.connect() | `async_session_maker()` from `database.py` | Same factory used by all services [VERIFIED: database.py] |

**Key insight:** This phase is primarily wiring -- connecting existing config loading, DB upsert, and Stripe API patterns into a new startup sequence. Almost no new abstractions are needed.

## Common Pitfalls

### Pitfall 1: Cache Staleness During Seeding
**What goes wrong:** `get_all()` in `platform_settings.py` uses a 30s TTL cache. If you call `get_all()` to check for existing values, then `upsert()` to write, then `get_all()` again -- you get stale cached data.
**Why it happens:** Module-level cache doesn't know about writes in the same process.
**How to avoid:** Call `invalidate_cache()` after all seeding is complete. Or use direct DB queries (bypass cache) during the seeding function.
**Warning signs:** Tests pass individually but fail when run together; values appear missing after seeding.

### Pitfall 2: VALID_KEYS Gate in platform_settings
**What goes wrong:** `platform_settings.py` has a `VALID_KEYS = set(DEFAULTS.keys())` set. If new tiers are added to config (e.g., `price_business_monthly_cents`), `validate_setting()` rejects them as unknown keys.
**Why it happens:** VALID_KEYS is derived from hardcoded DEFAULTS, not from config.
**How to avoid:** Either (a) add all possible tier pricing keys to DEFAULTS, or (b) make VALID_KEYS dynamic based on loaded config, or (c) bypass `validate_setting()` during seeding (seeding writes known-good config values).
**Warning signs:** 422 errors when trying to save seeded pricing for tiers beyond standard/premium.

### Pitfall 3: Stripe Product Duplication on Restart
**What goes wrong:** If Stripe sync creates a Product + Price but fails to save the `stripe_price_id` back to DB (e.g., DB write error after Stripe call), next startup creates another Product.
**Why it happens:** Stripe creation and DB write are not atomic.
**How to avoid:** Use `lookup_key` on Prices with `transfer_lookup_key: True` (already in the codebase pattern). This way Stripe itself manages uniqueness by lookup key. Alternatively, list existing Products by metadata before creating.
**Warning signs:** Multiple Products with the same name in Stripe Dashboard.

### Pitfall 4: Platform Settings upsert() Requires admin_id
**What goes wrong:** `upsert()` takes `admin_id: UUID` as a required parameter. During startup seeding, there's no admin user context.
**Why it happens:** The function was designed for admin-triggered changes.
**How to avoid:** Pass `admin_id=None` -- the `updated_by` column is already nullable (`Mapped[UUID | None]`). This correctly indicates "system-seeded" values.
**Warning signs:** TypeError on startup if admin_id parameter handling is wrong.

### Pitfall 5: Credit Package Seeding Condition
**What goes wrong:** Seeding credit packages "when no packages exist" (D-04 idempotent) could mean checking `COUNT(*) == 0`. But if an admin deletes all packages, next restart re-seeds them.
**Why it happens:** Ambiguity between "first startup" and "empty table".
**How to avoid:** This is actually desired behavior per D-04 (fills gaps). For credit packages specifically, check if any row with the config package name exists, not just if the table is empty. This preserves admin customizations while filling missing packages.
**Warning signs:** Admin deactivates a package, restart re-creates it.

## Code Examples

### Extended user_classes.yaml
```yaml
# Source: D-01, D-02, D-03 decisions
user_classes:
  free_trial:
    display_name: "Free Trial"
    credits: 100
    reset_policy: none
    trial_duration_days: 7
    workspace_access: true
    max_active_collections: 1
    has_plan: false
  on_demand:
    display_name: "On Demand"
    credits: 0
    reset_policy: none
    workspace_access: true
    max_active_collections: 3
    has_plan: false
  standard:
    display_name: "Standard"
    credits: 100
    reset_policy: none
    workspace_access: true
    max_active_collections: 5
    has_plan: true
    price_cents: 2900
  premium:
    display_name: "Premium"
    credits: 500
    reset_policy: none
    workspace_access: true
    max_active_collections: -1
    has_plan: true
    price_cents: 7900
  internal:
    display_name: "Internal"
    credits: 0
    reset_policy: unlimited
    workspace_access: true
    max_active_collections: -1
    has_plan: false

credit_packages:
  - name: "Starter Pack"
    price_cents: 500
    credit_amount: 50
    display_order: 1
  - name: "Value Pack"
    price_cents: 1500
    credit_amount: 200
    display_order: 2
  - name: "Pro Pack"
    price_cents: 3500
    credit_amount: 500
    display_order: 3
```

### Stripe Readiness Check Utility (D-07)
```python
# Source: D-07 decision
from app.config import get_settings
from app.services.platform_settings import get_all as get_platform_settings
from app.models.credit_package import CreditPackage
from sqlalchemy import select

async def check_stripe_readiness(db: AsyncSession) -> dict:
    """Check if Stripe is fully configured for monetization.
    
    Returns:
        {"ready": bool, "missing": list[str]}
    """
    missing = []
    settings = get_settings()
    
    if not settings.stripe_secret_key:
        missing.append("STRIPE_SECRET_KEY not configured")
    
    # Check subscription tiers
    platform = await get_platform_settings(db)
    user_classes = get_user_classes()
    for tier_name, tier_config in user_classes.items():
        if not tier_config.get("has_plan"):
            continue
        stripe_key = f"stripe_price_{tier_name}_monthly"
        stripe_id = json.loads(platform.get(stripe_key, '""'))
        if not stripe_id:
            missing.append(f"Missing Stripe Price for {tier_name} subscription")
    
    # Check credit packages
    result = await db.execute(
        select(CreditPackage).where(CreditPackage.is_active == True)
    )
    packages = result.scalars().all()
    for pkg in packages:
        if not pkg.stripe_price_id:
            missing.append(f"Missing Stripe Price for credit package '{pkg.name}'")
    
    return {"ready": len(missing) == 0, "missing": missing}
```

### Lifespan Integration Point
```python
# Source: D-04 decision, existing main.py lifespan pattern
# Insert AFTER SMTP validation, BEFORE checkpointer/scheduler

from app.services.pricing_sync import seed_pricing_from_config

# Seed pricing config to database (fail-fast on DB errors)
async with async_session_maker() as db:
    await seed_pricing_from_config(db)
    await db.commit()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded DEFAULTS in platform_settings.py | Config-driven from user_classes.yaml | Phase 60 (this phase) | Pricing defined once in YAML, seeded to DB |
| Manual Stripe Dashboard setup | Auto-provisioned on startup | Phase 60 (this phase) | Zero manual Stripe configuration |
| `monetization_enabled` default `True` | Default `False` | Phase 60 (this phase) | Safe upgrade path for existing users |
| `product_data` inline on Price creation | Separate Product + Price creation | Phase 60 (D-08) | Clean Stripe Dashboard organization |

**Deprecated/outdated:**
- Inline `product_data` on `prices.create()`: Still works in Stripe API, but D-08 decision mandates separate Product per tier for Dashboard organization. The existing `billing_settings.py` uses inline `product_data` -- Phase 60 should create Products separately.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Credit package values (Starter 50/$5, Value 200/$15, Pro 500/$35) match v0.9 seed data | Code Examples | Wrong default pricing; easily corrected in YAML |
| A2 | `lookup_key` + `transfer_lookup_key` prevents duplicate Stripe Prices across restarts | Pitfalls | Could create duplicate Products/Prices; mitigated by checking DB before creating |

## Open Questions

1. **Credit package default values**
   - What we know: v0.9 created 3 credit packages (Starter, Value, Pro) but exact prices/credits were defined in code
   - What's unclear: Exact price_cents and credit_amount values for each package
   - Recommendation: Check the v0.9 migration or seed data to confirm exact values; use those as config defaults

2. **Dynamic VALID_KEYS in platform_settings**
   - What we know: Currently hardcoded from DEFAULTS dict, only supports standard/premium tiers
   - What's unclear: Whether future tiers beyond standard/premium will need pricing keys
   - Recommendation: For Phase 60, keep VALID_KEYS as-is since only standard and premium have `has_plan: true`. Add a comment noting this constraint for future extensibility

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0.0 + pytest-asyncio >= 0.23.0 |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend && python -m pytest tests/test_pricing_sync.py -x` |
| Full suite command | `cd backend && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SUB-01 | YAML loader returns `has_plan` field | unit | `pytest tests/test_pricing_sync.py::test_yaml_has_plan -x` | Wave 0 |
| SUB-02 | YAML loader returns `price_cents` for plan tiers | unit | `pytest tests/test_pricing_sync.py::test_yaml_price_cents -x` | Wave 0 |
| SUB-03 | Seeder writes pricing to empty platform_settings | unit | `pytest tests/test_pricing_sync.py::test_seed_subscription_pricing -x` | Wave 0 |
| SUB-04 | Stripe sync creates Price for tier missing stripe_price_id | unit (mocked Stripe) | `pytest tests/test_pricing_sync.py::test_stripe_sync_subscription -x` | Wave 0 |
| PKG-01 | YAML loader returns credit_packages list | unit | `pytest tests/test_pricing_sync.py::test_yaml_credit_packages -x` | Wave 0 |
| PKG-02 | Seeder inserts credit_packages to empty DB | unit | `pytest tests/test_pricing_sync.py::test_seed_credit_packages -x` | Wave 0 |
| PKG-03 | Stripe sync creates Price for package missing stripe_price_id | unit (mocked Stripe) | `pytest tests/test_pricing_sync.py::test_stripe_sync_packages -x` | Wave 0 |
| SAFE-01 | Existing stripe_price_id not overwritten by seeder | unit | `pytest tests/test_pricing_sync.py::test_no_overwrite_existing -x` | Wave 0 |
| SAFE-02 | Full startup flow creates all Stripe objects | integration (mocked Stripe) | `pytest tests/test_pricing_sync.py::test_full_startup_sync -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_pricing_sync.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_pricing_sync.py` -- covers SUB-01 through SAFE-02
- [ ] Stripe client mock fixture (patch `SubscriptionService._get_stripe_client`)
- [ ] In-memory SQLite or mock DB session fixture for seeding tests

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | -- |
| V3 Session Management | no | -- |
| V4 Access Control | yes | Admin-only PUT endpoint already gated by `CurrentAdmin` dependency |
| V5 Input Validation | yes | YAML config validated at load time; billing settings validated by `validate_setting()` |
| V6 Cryptography | no | -- |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML injection via config file | Tampering | Config file is server-side only, not user-uploadable; `yaml.safe_load()` already used |
| Monetization enabled without Stripe setup | Elevation of Privilege | Readiness check (D-07) blocks toggle; 422 response with specifics |
| Stripe secret key exposure | Information Disclosure | Key in env var only, never in config YAML or DB |

## Sources

### Primary (HIGH confidence)
- Context7 `/stripe/stripe-python` -- Products, Prices, StripeClient API verified
- Codebase files: `platform_settings.py`, `user_class.py`, `billing_settings.py`, `subscription.py`, `credit_package.py`, `main.py`, `database.py`, `config.py` -- all patterns verified by direct reading
- `backend/pyproject.toml` -- stripe >=14.0.0,<15.0 pinned

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- A1, A2 in Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new deps
- Architecture: HIGH -- extending existing patterns (YAML loader, upsert, Stripe client)
- Pitfalls: HIGH -- identified from direct codebase analysis (cache, VALID_KEYS, admin_id)

**Research date:** 2026-04-23
**Valid until:** 2026-05-23 (stable domain, no fast-moving dependencies)
