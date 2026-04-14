# Phase 55: Tier Restructure & Data Foundation - Research

**Researched:** 2026-03-18
**Domain:** SQLAlchemy/Alembic schema changes, YAML configuration, dual-balance credit logic
**Confidence:** HIGH

## Summary

Phase 55 is a backend-only data foundation phase. No Stripe integration, no UI changes, no trial enforcement. The work consists of four distinct areas: (1) restructure `user_classes.yaml` to reflect the 4 consumer tiers plus internal, (2) add dual-balance credit tracking by adding `purchased_balance` to `UserCredit` and refactoring `CreditService`, (3) create billing database tables (Subscription, PaymentHistory, CreditPackage, StripeEvent) via Alembic migration, and (4) update registration defaults and APScheduler logic.

The codebase is well-structured with consistent patterns: SQLAlchemy `mapped_column` with type hints, `NUMERIC(10,1)` for balances, `SELECT FOR UPDATE` locking in CreditService, YAML-based tier config with 30s TTL cache, and Alembic migrations for all schema changes. All changes follow existing patterns -- no new libraries or frameworks needed.

**Primary recommendation:** Execute as a series of sequential changes -- YAML config first, then User model changes, then UserCredit dual-balance, then new billing tables, then CreditService refactor, then scheduler update. Each step builds on the previous.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- No `free` tier users exist in production -- skip data migration entirely
- Drop the `free` key from `user_classes.yaml`
- Keep `standard` as the DB key (do NOT rename to `basic` in DB) -- display name can be "Basic" in UI later
- No Alembic data migration for user rows needed
- Add `on_demand` key with `reset_policy: none`, `credits: 0`
- `UserCredit` gets new `purchased_balance` field alongside existing `balance` (which becomes subscription balance)
- Credit deduction: subscription first, purchased second
- Refunds: reverse order -- purchased first, then subscription (last-out-first-in)
- Subscription reset: subscription balance resets to tier allocation, purchased balance untouched
- Purchased credits never reset, never expire
- Update `get_default_class()` to return `"free_trial"` instead of `"free"`
- Update `User` model default for `user_class` field to `"free_trial"`
- Add `trial_expires_at` (DateTime, nullable) to User model
- `trial_duration_days` added as platform setting (default: 7 days)
- Free trial config: `credits: 100`, `trial_duration_days: 7`
- APScheduler `process_credit_resets()` must skip subscription-tier users (standard/premium)

### Claude's Discretion
- Exact column types and constraints for new billing tables (Subscription, PaymentHistory, CreditPackage, StripeEvent)
- Alembic migration ordering and dependency chain
- Whether to split the `balance` field rename or keep as-is and add `purchased_balance` alongside
- Default values for On Demand `workspace_access` and `max_active_collections` in YAML

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TIER-01 | System supports 4 consumer tiers: Free Trial, On Demand, Basic, Premium | YAML config restructure with existing `get_user_classes()` loader |
| TIER-02 | Drop `free`, keep `standard`, add `on_demand` in user_classes.yaml | Direct YAML edit + `get_default_class()` update |
| TIER-03 | Existing `free` tier users migrated | Owner confirmed no free users in prod -- mark as N/A, just drop the key |
| TIER-04 | User credit balance split into subscription + purchased credits | Add `purchased_balance` column to `UserCredit`, refactor `CreditService` |
| TIER-05 | Credit deduction: subscription first, purchased second | Refactor `CreditService.deduct_credit()` with dual-balance logic |
| TIER-06 | Purchased credits persist across billing cycles (never reset) | `execute_reset()` only resets `balance`, leaves `purchased_balance` untouched |
| TIER-07 | Subscription credits reset via Stripe webhook | Phase 57 scope -- in Phase 55, just ensure reset logic only touches `balance` field |
| TIER-08 | APScheduler skips subscription-tier users | Add tier skip logic in `process_credit_resets()` |
| DATA-01 | Subscription table | New SQLAlchemy model + Alembic migration |
| DATA-02 | PaymentHistory table | New SQLAlchemy model + Alembic migration |
| DATA-03 | CreditPackage table | New SQLAlchemy model + Alembic migration |
| DATA-04 | StripeEvent table | New SQLAlchemy model + Alembic migration |
| DATA-05 | `trial_expires_at` field on User model | Add column + Alembic migration |
| DATA-06 | `purchased_balance` field on UserCredit model | Add column + Alembic migration |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ (already installed) | ORM models with `mapped_column` | Project standard, async support |
| Alembic | 1.13+ (already installed) | Database migrations | Project standard for all schema changes |
| PyYAML | 6.0+ (already installed) | Tier config from `user_classes.yaml` | Project standard for tier definitions |
| APScheduler | 3.11.x (already installed) | Credit reset scheduling | Project standard, `<4.0` pinned |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.x (already installed) | Schema updates for dual-balance responses | Update `CreditBalanceResponse` |

**No new dependencies required.** All work uses existing libraries.

## Architecture Patterns

### Recommended Change Structure
```
backend/
├── app/
│   ├── config/
│   │   └── user_classes.yaml          # MODIFY: drop free, add on_demand
│   ├── models/
│   │   ├── __init__.py                # MODIFY: register new models
│   │   ├── user.py                    # MODIFY: default + trial_expires_at
│   │   ├── user_credit.py             # MODIFY: add purchased_balance
│   │   ├── subscription.py            # NEW: Subscription model
│   │   ├── payment_history.py         # NEW: PaymentHistory model
│   │   ├── credit_package.py          # NEW: CreditPackage model
│   │   └── stripe_event.py            # NEW: StripeEvent model
│   ├── services/
│   │   ├── credit.py                  # MODIFY: dual-balance logic
│   │   ├── user_class.py              # MODIFY: get_default_class()
│   │   └── platform_settings.py       # MODIFY: add trial_duration_days default
│   ├── schemas/
│   │   └── credit.py                  # MODIFY: add purchased_balance to responses
│   └── scheduler.py                   # MODIFY: skip subscription tiers
├── alembic/
│   ├── env.py                         # MODIFY: import new models
│   └── versions/
│       └── {new}_tier_restructure_billing_tables.py  # NEW
```

### Pattern 1: SQLAlchemy Model Definition (existing project pattern)
**What:** All models use `mapped_column` with type hints, UUID primary keys, timezone-aware DateTimes
**When to use:** All new billing tables
**Example:**
```python
# Source: backend/app/models/user_credit.py (existing pattern)
from sqlalchemy import DateTime, ForeignKey, NUMERIC, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.models.base import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    plan_tier: Mapped[str] = mapped_column(String(20))  # standard, premium
    status: Mapped[str] = mapped_column(String(30))  # active, past_due, canceled, trialing
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

### Pattern 2: Alembic Migration (existing project pattern)
**What:** All schema changes via revision files, explicit `sa.Column` definitions, proper ForeignKeyConstraint
**When to use:** All table creation and column additions in this phase
**Example:**
```python
# Source: backend/alembic/versions/f47a0001b000 (existing pattern)
def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        # ... columns
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

def downgrade() -> None:
    op.drop_table("subscriptions")
```

### Pattern 3: Dual-Balance Credit Deduction
**What:** Consume subscription credits first, then purchased credits. Atomic with SELECT FOR UPDATE.
**When to use:** `CreditService.deduct_credit()` refactor
**Example:**
```python
# Dual-balance deduction logic
current_sub = Decimal(str(credit.balance))
current_purchased = Decimal(str(credit.purchased_balance))
total_available = current_sub + current_purchased

if total_available < cost:
    # insufficient funds
    return CreditDeductionResult(success=False, ...)

# Consume subscription first
if current_sub >= cost:
    credit.balance = current_sub - cost
else:
    # Subscription exhausted, remainder from purchased
    remainder = cost - current_sub
    credit.balance = Decimal("0")
    credit.purchased_balance = current_purchased - remainder
```

### Pattern 4: Dual-Balance Refund (LIFO)
**What:** Refund to purchased first, then subscription (reverse of deduction order)
**When to use:** `CreditService.refund()` refactor
**Example:**
```python
# LIFO refund: purchased first, then subscription
# Track which pool was debited via balance_pool field on CreditTransaction
# OR use simple LIFO: refund to purchased_balance first up to its pre-deduction level
credit.purchased_balance += amount  # simplified -- refund goes to purchased first
```

### Anti-Patterns to Avoid
- **Renaming `balance` column:** Do NOT rename `balance` to `subscription_balance`. Keep the existing column name to avoid breaking every query that references it. The column semantically becomes subscription balance, but the field name stays `balance`.
- **Multi-migration dependencies:** Do NOT create multiple separate Alembic migration files with cross-dependencies for a single phase. One migration file handles all changes atomically.
- **Hardcoding tier names in conditionals:** Use YAML config properties (like `reset_policy`) to drive behavior, not tier name string comparisons. Exception: the scheduler skip logic for subscription tiers is a specific business rule.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Migration scripts | Manual SQL ALTER TABLE | Alembic `op.add_column()`, `op.create_table()` | Alembic handles rollback, dependency chains, cross-DB compatibility |
| Tier config parsing | Hardcoded tier dicts | Existing `get_user_classes()` YAML loader with cache | Already works, 30s TTL cache, single source of truth |
| Atomic balance updates | Manual SQL UPDATE with app-level checks | SQLAlchemy `SELECT FOR UPDATE` pattern (already in CreditService) | Prevents race conditions, proven pattern in codebase |
| Platform settings | Config files or env vars | Existing `PlatformSettingsService` with TTL cache | Already has upsert, caching, validation infrastructure |

## Common Pitfalls

### Pitfall 1: Breaking existing `balance` references
**What goes wrong:** Renaming `balance` to `subscription_balance` breaks every file that reads `credit.balance`
**Why it happens:** Desire for semantic clarity overrides practical concerns
**How to avoid:** Keep `balance` as the field name. Add `purchased_balance` alongside it. The existing `balance` field IS the subscription balance -- just document it.
**Warning signs:** Find all references to `.balance` before making changes (CreditService, scheduler, schemas, admin endpoints, routers)

### Pitfall 2: Forgetting to update `models/__init__.py` and `alembic/env.py`
**What goes wrong:** Alembic autogenerate won't see new models; imports fail at runtime
**Why it happens:** New model files created but not registered in the two required import locations
**How to avoid:** Always add new models to both `backend/app/models/__init__.py` and `backend/alembic/env.py`
**Warning signs:** `alembic revision --autogenerate` produces empty migration

### Pitfall 3: APScheduler skip logic using wrong criteria
**What goes wrong:** Subscription-tier users still get their credits reset by APScheduler
**Why it happens:** Using `reset_policy` alone -- standard has `reset_policy: weekly` which would still trigger resets
**How to avoid:** The decision says APScheduler must skip subscription tiers (standard/premium) because Stripe handles their resets. Change standard/premium `reset_policy` in YAML to `none` or add explicit tier-name checks in scheduler. The cleanest approach: change standard/premium `reset_policy` to `none` in YAML since Stripe webhook will handle their resets in Phase 57.
**Warning signs:** `is_reset_due()` returns True for standard/premium users

### Pitfall 4: Dual-balance transaction logging ambiguity
**What goes wrong:** Transaction history doesn't indicate which balance pool was affected
**Why it happens:** `CreditTransaction` only records total `amount` and `balance_after`, not which pool
**How to avoid:** Add a `balance_pool` field to `CreditTransaction` (e.g., `"subscription"`, `"purchased"`, `"split"`) so audit trail is clear. Also consider adding `purchased_balance_after` field.
**Warning signs:** Admin cannot reconcile transaction history with balance changes

### Pitfall 5: Platform settings default not updated
**What goes wrong:** `default_user_class` platform setting still defaults to `"free"` in `DEFAULTS` dict
**Why it happens:** `platform_settings.py` has hardcoded `DEFAULTS` dict separate from `get_default_class()`
**How to avoid:** Update `DEFAULTS["default_user_class"]` from `json.dumps("free")` to `json.dumps("free_trial")`
**Warning signs:** Admin platform settings page shows "free" as default class

### Pitfall 6: Existing test_tier_gating.py references `free` tier
**What goes wrong:** Tests fail because `free` tier no longer exists in YAML
**Why it happens:** Tests were written for 5-tier model including `free`
**How to avoid:** Update test fixtures to use the new tier set (free_trial, on_demand, standard, premium, internal). Tests that mock `get_class_config` with `free` config need updating.
**Warning signs:** `pytest backend/tests/test_tier_gating.py` fails after YAML changes

## Code Examples

### user_classes.yaml (target state)
```yaml
# Source: Owner decisions from CONTEXT.md
user_classes:
  free_trial:
    display_name: "Free Trial"
    credits: 100
    reset_policy: none
    trial_duration_days: 7
    workspace_access: true
    max_active_collections: 1
  on_demand:
    display_name: "On Demand"
    credits: 0
    reset_policy: none
    workspace_access: true
    max_active_collections: 3
  standard:
    display_name: "Standard"
    credits: 100
    reset_policy: none       # Changed from weekly -- Stripe handles resets
    workspace_access: true
    max_active_collections: 5
  premium:
    display_name: "Premium"
    credits: 500
    reset_policy: none       # Changed from monthly -- Stripe handles resets
    workspace_access: true
    max_active_collections: -1
  internal:
    display_name: "Internal"
    credits: 0
    reset_policy: unlimited
    workspace_access: true
    max_active_collections: -1
```

### UserCredit model (target state)
```python
# Source: existing model + DATA-06
class UserCredit(Base):
    __tablename__ = "user_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    balance: Mapped[float] = mapped_column(NUMERIC(10, 1), default=0)  # subscription credits
    purchased_balance: Mapped[float] = mapped_column(NUMERIC(10, 1), default=0)  # purchased credits
    last_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

### CreditBalanceResponse (target state)
```python
# Source: existing schema + dual-balance additions
class CreditBalanceResponse(BaseModel):
    balance: Decimal             # subscription credits
    purchased_balance: Decimal   # purchased credits
    total_balance: Decimal       # subscription + purchased (convenience)
    tier_allocation: int
    reset_policy: str
    next_reset_at: datetime | None
    is_low: bool
    is_unlimited: bool
    display_class: str

    model_config = {"from_attributes": True}
```

### Billing Table Schemas (Claude's Discretion)

```python
# Subscription -- one per user, stores local copy of Stripe state
class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[UUID] (PK)
    user_id: Mapped[UUID] (FK users.id, unique, CASCADE)
    stripe_subscription_id: Mapped[str | None] (String(255), unique, nullable)
    stripe_customer_id: Mapped[str | None] (String(255), nullable, indexed)
    plan_tier: Mapped[str] (String(20))  # "standard" or "premium"
    status: Mapped[str] (String(30))     # active, past_due, canceled, trialing, incomplete
    current_period_start: Mapped[datetime | None]
    current_period_end: Mapped[datetime | None]
    cancel_at_period_end: Mapped[bool] (default False)
    created_at, updated_at: Mapped[datetime]

# PaymentHistory -- one row per payment event
class PaymentHistory(Base):
    __tablename__ = "payment_history"
    id: Mapped[UUID] (PK)
    user_id: Mapped[UUID] (FK users.id, CASCADE, indexed)
    stripe_payment_intent_id: Mapped[str | None] (String(255), unique, nullable)
    amount_cents: Mapped[int]  # store in cents to avoid float issues
    currency: Mapped[str] (String(3), default "usd")
    payment_type: Mapped[str] (String(30))  # subscription, topup, refund
    credit_amount: Mapped[float | None] (NUMERIC(10,1), nullable)  # credits added/removed
    status: Mapped[str] (String(30))  # succeeded, failed, refunded, partial_refund
    created_at: Mapped[datetime]

# CreditPackage -- configurable top-up packages
class CreditPackage(Base):
    __tablename__ = "credit_packages"
    id: Mapped[UUID] (PK)
    name: Mapped[str] (String(100))
    credit_amount: Mapped[int]
    price_cents: Mapped[int]
    stripe_price_id: Mapped[str | None] (String(255), nullable)
    is_active: Mapped[bool] (default True)
    display_order: Mapped[int] (default 0)
    created_at: Mapped[datetime]

# StripeEvent -- idempotency deduplication
class StripeEvent(Base):
    __tablename__ = "stripe_events"
    id: Mapped[UUID] (PK)
    stripe_event_id: Mapped[str] (String(255), unique, indexed)
    event_type: Mapped[str] (String(100))
    processed_at: Mapped[datetime]
    created_at: Mapped[datetime]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `balance` field | Dual balance (subscription + purchased) | Phase 55 | All credit operations need dual-balance awareness |
| `free` as default tier | `free_trial` as default tier | Phase 55 | Registration, platform settings defaults change |
| APScheduler resets all recurring | APScheduler skips subscription tiers | Phase 55 | Stripe webhook handles subscription resets (Phase 57) |
| 5 tiers (free_trial, free, standard, premium, internal) | 5 tiers (free_trial, on_demand, standard, premium, internal) | Phase 55 | `free` removed, `on_demand` added |

## Open Questions

1. **On Demand workspace_access and max_active_collections defaults**
   - What we know: Owner wants these configurable in YAML
   - What's unclear: Exact default values
   - Recommendation: Use `workspace_access: true`, `max_active_collections: 3` (reasonable middle ground between free_trial=1 and standard=5)

2. **CreditTransaction balance_pool tracking**
   - What we know: Dual-balance needs audit trail clarity
   - What's unclear: Whether to add `balance_pool` field now or defer
   - Recommendation: Add `balance_pool` (String(20), nullable) to CreditTransaction in this phase's migration. Existing rows get NULL. New transactions record "subscription", "purchased", or "split".

3. **Standard/Premium reset_policy in YAML**
   - What we know: APScheduler must skip these users. Stripe handles resets in Phase 57.
   - What's unclear: Whether to change reset_policy to "none" now or add explicit scheduler skip logic
   - Recommendation: Change to `reset_policy: none` in YAML now. This is cleaner than adding tier-name conditionals. The `is_reset_due()` function already returns False for `none` policy, so no scheduler code change needed beyond removing the now-unnecessary skip.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ / pytest-asyncio 0.23+ |
| Config file | `backend/pyproject.toml` (dev dependency) |
| Quick run command | `cd backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TIER-01 | 4 consumer tiers exist in YAML config | unit | `pytest tests/test_tier_config.py::test_four_consumer_tiers -x` | No -- Wave 0 |
| TIER-02 | `free` dropped, `on_demand` added, `standard` kept | unit | `pytest tests/test_tier_config.py::test_tier_keys -x` | No -- Wave 0 |
| TIER-03 | No free tier users (no migration needed) | manual-only | N/A -- owner confirmed no prod users | N/A |
| TIER-04 | Dual balance: subscription + purchased | unit | `pytest tests/test_dual_balance.py::test_balance_split -x` | No -- Wave 0 |
| TIER-05 | Deduction: subscription first, purchased second | unit | `pytest tests/test_dual_balance.py::test_deduction_order -x` | No -- Wave 0 |
| TIER-06 | Purchased credits never reset | unit | `pytest tests/test_dual_balance.py::test_purchased_persists_on_reset -x` | No -- Wave 0 |
| TIER-07 | Subscription reset only touches balance (not purchased) | unit | `pytest tests/test_dual_balance.py::test_subscription_reset -x` | No -- Wave 0 |
| TIER-08 | APScheduler skips subscription tiers | unit | `pytest tests/test_scheduler_skip.py::test_skip_subscription_tiers -x` | No -- Wave 0 |
| DATA-01 | Subscription table exists with correct schema | unit | `pytest tests/test_billing_models.py::test_subscription_model -x` | No -- Wave 0 |
| DATA-02 | PaymentHistory table schema | unit | `pytest tests/test_billing_models.py::test_payment_history_model -x` | No -- Wave 0 |
| DATA-03 | CreditPackage table schema | unit | `pytest tests/test_billing_models.py::test_credit_package_model -x` | No -- Wave 0 |
| DATA-04 | StripeEvent table schema | unit | `pytest tests/test_billing_models.py::test_stripe_event_model -x` | No -- Wave 0 |
| DATA-05 | `trial_expires_at` on User model | unit | `pytest tests/test_billing_models.py::test_user_trial_field -x` | No -- Wave 0 |
| DATA-06 | `purchased_balance` on UserCredit | unit | `pytest tests/test_billing_models.py::test_user_credit_purchased_balance -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_tier_config.py` -- covers TIER-01, TIER-02 (YAML config validation)
- [ ] `tests/test_dual_balance.py` -- covers TIER-04, TIER-05, TIER-06, TIER-07 (dual-balance CreditService logic)
- [ ] `tests/test_scheduler_skip.py` -- covers TIER-08 (APScheduler subscription skip)
- [ ] `tests/test_billing_models.py` -- covers DATA-01 through DATA-06 (model importability, field existence)
- [ ] Update `tests/test_tier_gating.py` -- fix references to dropped `free` tier

## Sources

### Primary (HIGH confidence)
- `backend/app/config/user_classes.yaml` -- current tier definitions (5 tiers)
- `backend/app/models/user.py` -- User model, `user_class` default is `"free"`
- `backend/app/models/user_credit.py` -- single `balance` field, `NUMERIC(10,1)`
- `backend/app/services/credit.py` -- CreditService with single-balance logic, SELECT FOR UPDATE
- `backend/app/services/user_class.py` -- `get_default_class()` returns `"free"`, 30s cache
- `backend/app/scheduler.py` -- APScheduler reset logic, processes all recurring users
- `backend/app/services/auth.py` -- registration creates User + UserCredit rows
- `backend/app/services/platform_settings.py` -- DEFAULTS dict includes `default_user_class: "free"`
- `backend/app/models/__init__.py` -- model registration pattern
- `backend/alembic/env.py` -- model imports for autogenerate
- `backend/alembic/versions/f47a0001b000` -- latest migration pattern reference
- `backend/app/schemas/credit.py` -- CreditBalanceResponse schema

### Secondary (MEDIUM confidence)
- `.planning/phases/55-tier-restructure-data-foundation/55-CONTEXT.md` -- owner decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new deps
- Architecture: HIGH -- follows established codebase patterns exactly
- Pitfalls: HIGH -- derived from reading actual code and identifying breaking changes

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain, internal refactor)
