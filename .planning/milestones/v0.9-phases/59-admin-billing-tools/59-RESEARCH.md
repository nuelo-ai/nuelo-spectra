# Phase 59: Admin Billing Tools - Research

**Researched:** 2026-03-24
**Domain:** Stripe admin operations (refunds, coupons, promotion codes, billing settings), admin frontend CRUD pages
**Confidence:** HIGH

## Summary

Phase 59 adds admin-facing billing management tools: a user billing detail tab (subscription status, payment history, Stripe event log), tier override with Stripe sync, refund processing, billing platform settings (including monetization master switch), and discount code management via Stripe Coupons/Promotion Codes API.

The backend already has a well-established admin router pattern (`backend/app/routers/admin/`) with authentication, audit logging, and service-layer separation. The admin frontend uses Next.js with shadcn/ui components, TanStack Query hooks, and a sidebar navigation structure. New features follow these existing patterns directly.

**Primary recommendation:** Build 4 plans: (1) Backend billing admin endpoints + StripeEvent model extension, (2) User billing tab frontend, (3) Billing settings backend + frontend, (4) Discount codes backend + frontend. Each plan follows existing admin router/service/hook patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Single new "Billing" tab added to UserDetailTabs (5 tabs total: Overview, Activity, Credit Transactions, API Keys, Billing)
- D-02: Billing tab contains stacked sections: subscription status card at top, payment history table, Stripe event log table
- D-03: Stripe event log shows raw webhook events (event type, timestamp, processing status) -- not human-readable timeline
- D-04: Subscription status card includes 4 action buttons: Force-set tier, Cancel subscription, View in Stripe (external link), Initiate refund
- D-05: Force-set tier syncs with Stripe -- if user has active subscription, the Stripe subscription is updated/cancelled to match the new tier. Not a local-only override.
- D-06: Force-set tier requires mandatory reason field (logged for audit trail)
- D-07: Tier change dialog shows current tier, new tier selector, reason text field, and confirmation with Stripe sync explanation
- D-08: Refund button on each payment row in the payment history table
- D-09: Refund dialog pre-fills full amount with option to enter partial amount
- D-10: Credits auto-deducted from purchased_balance proportional to refund amount (e.g., full refund of 50-credit purchase removes 50 credits)
- D-11: Refund triggers Stripe Refund API and records in PaymentHistory
- D-12: Separate Billing Settings page in admin (new route, not extending existing SettingsForm)
- D-13: Monetization master switch -- when disabled: hides all billing UI from public frontend. Existing subscribers keep their tier and can still cancel. New users get Free Trial as default.
- D-14: Billing settings include: monetization toggle, trial_duration_days, credit prices per package, subscription prices per tier, subscription credit amounts per tier
- D-15: Prices editable in admin UI -- backend syncs to Stripe Products/Prices API. Spectra DB is source of truth.
- D-16: Two discount types supported: percentage off subscription, fixed amount off subscription. No free credits or trial extension codes.
- D-17: Dedicated Discount Codes page in admin with table (code, type, amount, status, usage count, expiry) + create form dialog
- D-18: Row actions: edit, deactivate, delete
- D-19: Codes support usage limits (max redemptions) and optional expiration date -- maps to Stripe coupon max_redemptions and redeem_by
- D-20: Users apply discount codes during Stripe-hosted Checkout (promotion_code passed to Checkout Session). No custom code entry UI on Plan Selection page.
- D-21: Admin creates discount code in Spectra -> backend creates Stripe Coupon + Promotion Code via API

### Claude's Discretion
- Billing tab section ordering, spacing, and visual hierarchy
- Payment history table columns and pagination approach
- Stripe event log table columns and filtering
- Refund dialog exact layout and validation messages
- Billing Settings page form layout and field grouping
- Discount Codes table columns, sorting, and empty state
- Loading states and error handling for all new pages/sections
- Admin navigation structure for new Billing Settings and Discount Codes pages

### Deferred Ideas (OUT OF SCOPE)
- Free credits bonus discount codes -- codes that add bonus credits (not Stripe coupon, Spectra-only)
- Trial extension discount codes -- codes that extend trial_expires_at
- Annual billing -- yearly subscription option
- Multi-currency support -- pricing in different currencies
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADMIN-01 | Admin can view user subscription status in user detail page | Subscription model has all needed fields; new Billing tab component reads from existing Subscription table |
| ADMIN-02 | Admin can view payment history per user | PaymentHistory model already has user_id FK; new admin endpoint queries by user_id |
| ADMIN-03 | Admin can force-set user tier regardless of Stripe state (manual override with reason logging) | Existing useChangeTier hook + change_user_tier service; extend with Stripe sync (cancel/create sub) and reason field |
| ADMIN-04 | Admin can cancel user subscription on behalf of user | Existing SubscriptionService.cancel_subscription pattern; new admin endpoint wraps with audit log |
| ADMIN-05 | Admin can view full Stripe billing event log per user | StripeEvent model needs user_id column (migration); webhook handler needs to extract and store user_id |
| ADMIN-06 | Admin can issue full or partial refund for a specific payment | Stripe SDK v14: client.v1.refunds.create(); credit deduction from purchased_balance |
| ADMIN-07 | Admin billing platform settings: trial_duration_days, credit prices, subscription prices, subscription credit amounts | Extend platform_settings DEFAULTS + VALID_KEYS; new Billing Settings admin page |
| ADMIN-08 | Admin can create and manage discount codes | New DiscountCode model + Stripe Coupons/Promotion Codes API integration |
| ADMIN-09 | Admin can deactivate discount codes | Stripe Promotion Code update (active=false) + local DB update |
| ADMIN-10 | Discount codes integrate with Stripe Coupons/Promotion Codes API | SDK v14: client.v1.coupons.create(), client.v1.promotion_codes.create() |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stripe (Python) | >=14.0.0,<15.0 | Stripe API operations (refunds, coupons, promotion codes) | Already pinned in project; SDK v14 uses client.v1 namespace |
| FastAPI | existing | Admin API endpoints | Project standard |
| SQLAlchemy (async) | existing | Database models and queries | Project standard |
| Alembic | existing | Database migrations | Project standard |
| Next.js | existing | Admin frontend | Project standard |
| shadcn/ui | existing | UI components (Table, Dialog, Card, Switch, Select) | Project standard |
| TanStack Query | existing | Data fetching and mutations | Project standard |
| Sonner | existing | Toast notifications | Project standard |

### No New Dependencies Required
This phase uses only existing libraries. No new pip or npm packages needed.

## Architecture Patterns

### Recommended Project Structure

**Backend additions:**
```
backend/app/
├── routers/admin/
│   ├── billing.py          # NEW: user billing detail, force-set tier, cancel, refund
│   ├── billing_settings.py # NEW: billing platform settings CRUD
│   └── discount_codes.py   # NEW: discount code CRUD
├── services/
│   ├── subscription.py     # EXTEND: add admin refund, admin force-set-tier methods
│   └── discount_code.py    # NEW: discount code service (Stripe sync)
├── models/
│   ├── stripe_event.py     # EXTEND: add user_id column
│   └── discount_code.py    # NEW: DiscountCode model
└── schemas/
    ├── admin_billing.py    # NEW: request/response schemas
    └── discount_code.py    # NEW: discount code schemas
```

**Admin frontend additions:**
```
admin-frontend/src/
├── app/(admin)/
│   ├── billing-settings/
│   │   └── page.tsx        # NEW: Billing Settings page
│   └── discount-codes/
│       └── page.tsx        # NEW: Discount Codes page
├── components/
│   ├── users/
│   │   └── UserBillingTab.tsx  # NEW: Billing tab for UserDetailTabs
│   ├── billing/
│   │   ├── BillingSettingsForm.tsx  # NEW
│   │   ├── RefundDialog.tsx         # NEW
│   │   └── ForceSetTierDialog.tsx   # NEW
│   └── discount-codes/
│       ├── DiscountCodesTable.tsx    # NEW
│       └── DiscountCodeForm.tsx     # NEW
└── hooks/
    ├── useBilling.ts       # NEW: billing admin hooks
    └── useDiscountCodes.ts # NEW: discount code hooks
```

### Pattern 1: Admin Router + Service + Audit
**What:** Every admin action follows router -> service -> audit log pattern
**When to use:** All new admin endpoints
**Example:**
```python
# Source: backend/app/routers/admin/users.py (established pattern)
@router.post("/{user_id}/refund")
async def refund_payment(
    user_id: UUID,
    body: RefundRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    result = await SubscriptionService.admin_refund(db, user_id, body.payment_id, body.amount_cents)
    await log_admin_action(db, admin_id=current_admin.id, action="refund_payment", ...)
    await db.commit()
    return result
```

### Pattern 2: Admin Frontend Hook + Mutation
**What:** TanStack Query useMutation with adminApiClient, invalidating query cache on success
**When to use:** All admin write operations
**Example:**
```typescript
// Source: admin-frontend/src/hooks/useUsers.ts (established pattern)
export function useRefundPayment() {
  return useUserMutation<{ userId: string; paymentId: string; amountCents: number }>((p) =>
    adminApiClient.post(`/api/admin/billing/users/${p.userId}/refund`, {
      payment_id: p.paymentId,
      amount_cents: p.amountCents,
    })
  );
}
```

### Pattern 3: Platform Settings Extension
**What:** Add new keys to DEFAULTS dict, extend VALID_KEYS, add validation
**When to use:** ADMIN-07 billing settings
**Example:**
```python
# Source: backend/app/services/platform_settings.py
DEFAULTS: dict[str, str] = {
    # ... existing keys ...
    "monetization_enabled": json.dumps(True),
    "credits_standard_monthly": json.dumps(100),
    "credits_premium_monthly": json.dumps(500),
}
```

### Anti-Patterns to Avoid
- **Direct Stripe Dashboard management:** Admin should manage everything from Spectra admin UI. Stripe Dashboard is read-only reference.
- **Updating Stripe Price unit_amount:** Stripe Prices are IMMUTABLE for amount. Must create new Price and update subscription to use it. See "Common Pitfalls" below.
- **Querying Stripe Events API per-user:** Stripe Events API does NOT support customer_id filtering. Must use local StripeEvent table with user_id.
- **Local-only tier override:** D-05 explicitly requires Stripe sync. Never change tier without updating Stripe subscription state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Refund processing | Custom refund tracking | Stripe Refund API (`client.v1.refunds.create()`) | Handles card network refund flow, dispute protection |
| Discount codes | Custom coupon engine | Stripe Coupons + Promotion Codes API | Automatic application during checkout, usage tracking, expiry |
| Price management | Custom price store | Stripe Products/Prices API (create new Price) | Stripe validates pricing, handles billing cycles |
| Audit trail | Custom log table | Existing `log_admin_action()` service | Already built with IP tracking, target_type, details JSON |

**Key insight:** All monetary operations (refunds, coupons, price changes) MUST go through Stripe API to maintain Stripe as the payment source of truth. The Spectra DB mirrors state but does not replace Stripe.

## Common Pitfalls

### Pitfall 1: Stripe Price Immutability
**What goes wrong:** Attempting to update `unit_amount` on an existing Stripe Price fails silently or errors.
**Why it happens:** Stripe Prices are immutable by design for `unit_amount`, `currency`, `recurring`. Only `active`, `metadata`, `nickname`, `lookup_key` can be updated.
**How to avoid:** When admin changes a subscription price in billing settings: (1) Create a NEW Stripe Price with the new amount, (2) Store the new Price ID in platform_settings, (3) Existing subscriptions continue at old price until renewal or plan change. New subscriptions use new Price.
**Warning signs:** Stripe API error "You cannot update the unit_amount of a price" or silent no-op.

### Pitfall 2: Stripe Events API Has No Customer Filter
**What goes wrong:** Attempting to fetch Stripe events filtered by customer_id returns all events or errors.
**Why it happens:** Stripe Events API only supports filtering by `created` date range, `type`, and `delivery_success`. No customer/user filter.
**How to avoid:** Extend the local `StripeEvent` model with a `user_id` column. Extract user_id from event data in the webhook handler and store it. Query locally for per-user event log.
**Warning signs:** Admin event log showing events for all users, not just the selected one.

### Pitfall 3: Refund Credit Deduction Math
**What goes wrong:** Partial refund credit deduction is miscalculated, leaving purchased_balance negative or deducting wrong amount.
**Why it happens:** Credit deduction must be proportional: `credits_to_deduct = (refund_amount / original_payment_amount) * original_credit_amount`.
**How to avoid:** Always calculate ratio from the original PaymentHistory row. Use Decimal arithmetic (already project pattern). Clamp to 0 minimum.
**Warning signs:** purchased_balance going negative after partial refund.

### Pitfall 4: Force-Set Tier Stripe Sync Edge Cases
**What goes wrong:** Admin force-sets tier to "on_demand" but Stripe subscription remains active, causing webhook to re-upgrade user.
**Why it happens:** Setting user_class locally without cancelling Stripe subscription means next webhook event re-syncs to subscription tier.
**How to avoid:** Force-set tier must: (1) If setting to on_demand: cancel Stripe subscription immediately (not at period end), (2) If setting to standard/premium: create or update Stripe subscription, (3) If no existing subscription: just update user_class locally.
**Warning signs:** User tier "bouncing back" after admin override.

### Pitfall 5: Promotion Code vs Coupon Confusion
**What goes wrong:** Creating only a Stripe Coupon but not a Promotion Code, so the code cannot be entered during Checkout.
**Why it happens:** In Stripe, a Coupon is the discount rule; a Promotion Code is the user-facing code that references the coupon. Checkout Sessions use `allow_promotion_codes: true` or explicitly pass `discounts` with promotion code.
**How to avoid:** Always create BOTH: Coupon first (defines the discount), then Promotion Code (defines the user-facing code, max_redemptions, expiry). Store both IDs in the local DiscountCode model.
**Warning signs:** Discount code created in admin but users cannot apply it during checkout.

### Pitfall 6: db.commit() in Admin Endpoints
**What goes wrong:** Data not persisted after admin action.
**Why it happens:** The `get_db()` dependency only closes the session; it does NOT auto-commit. This is a documented project pattern from Phase 58.
**How to avoid:** Every admin endpoint must explicitly call `await db.commit()` after all operations (existing pattern in admin/users.py, admin/settings.py).
**Warning signs:** Admin sees success toast but data reverts on page refresh.

## Code Examples

### Stripe Refund via SDK v14
```python
# Source: Stripe API docs (verified 2026-03-24)
client = SubscriptionService._get_stripe_client()

# Full refund
refund = client.v1.refunds.create(params={
    "payment_intent": payment_history.stripe_payment_intent_id,
    "reason": "requested_by_customer",
})

# Partial refund (amount in cents)
refund = client.v1.refunds.create(params={
    "payment_intent": payment_history.stripe_payment_intent_id,
    "amount": 1500,  # $15.00
    "reason": "requested_by_customer",
})
```

### Stripe Coupon + Promotion Code Creation
```python
# Source: Stripe API docs (verified 2026-03-24)
client = SubscriptionService._get_stripe_client()

# Percentage coupon
coupon = client.v1.coupons.create(params={
    "percent_off": 25.0,
    "duration": "forever",  # or "once", "repeating"
    "max_redemptions": 100,
    "redeem_by": 1735689600,  # Unix timestamp
    "metadata": {"source": "spectra_admin"},
})

# Fixed amount coupon
coupon = client.v1.coupons.create(params={
    "amount_off": 500,  # $5.00 in cents
    "currency": "usd",
    "duration": "once",
    "metadata": {"source": "spectra_admin"},
})

# Promotion code (user-facing code)
promo = client.v1.promotion_codes.create(params={
    "coupon": coupon.id,
    "code": "SUMMER2026",
    "max_redemptions": 100,
    "expires_at": 1735689600,
    "active": True,
})
```

### New Price Creation (for price changes)
```python
# Source: Stripe API docs (verified 2026-03-24)
# Stripe Prices are IMMUTABLE for unit_amount -- must create new Price
client = SubscriptionService._get_stripe_client()

new_price = client.v1.prices.create(params={
    "unit_amount": 3900,  # $39.00 in cents
    "currency": "usd",
    "recurring": {"interval": "month"},
    "product": existing_product_id,
    "lookup_key": "standard_monthly",
    "transfer_lookup_key": True,  # Moves lookup_key from old price to new
})

# Deactivate old price
client.v1.prices.update(old_price_id, params={"active": False})

# Store new price ID in platform settings
await platform_settings.upsert(db, "stripe_price_standard_monthly", new_price.id, admin_id)
```

### DiscountCode Model
```python
# NEW model for local discount code tracking
class DiscountCode(Base):
    __tablename__ = "discount_codes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(20))  # "percent_off" or "amount_off"
    discount_value: Mapped[int] = mapped_column(Integer)  # percent (e.g., 25) or cents (e.g., 500)
    currency: Mapped[str] = mapped_column(String(3), default="usd")  # only for amount_off
    stripe_coupon_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_promotion_code_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    times_redeemed: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

### Enabling Promotion Codes in Checkout
```python
# MODIFY existing create_subscription_checkout in SubscriptionService
session = client.v1.checkout.sessions.create(params={
    "mode": "subscription",
    "customer": customer_id,
    "line_items": [{"price": price_id, "quantity": 1}],
    "success_url": success_url,
    "cancel_url": cancel_url,
    "allow_promotion_codes": True,  # ADD THIS LINE
    # ... rest of params
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `stripe.Refund.create()` | `client.v1.refunds.create()` | Stripe SDK v14 | Must use client.v1 namespace (project already on v14) |
| `stripe.Coupon.create()` | `client.v1.coupons.create()` | Stripe SDK v14 | Same namespace change |
| Update Price amount | Create new Price + deactivate old | Stripe design (always) | Prices are immutable; `transfer_lookup_key` helps migration |
| `promotion.coupon` param | `coupon` at top level for promo code create | Stripe API current | Verify exact param structure during implementation |

## Open Questions

1. **Checkout allow_promotion_codes**
   - What we know: D-20 says users apply discount codes during Stripe-hosted Checkout
   - What's unclear: Need to add `allow_promotion_codes: True` to existing checkout session creation. This is a minor change to SubscriptionService but must be coordinated.
   - Recommendation: Include in the discount codes plan as a small backend task

2. **Promotion Code API parameter structure**
   - What we know: Stripe docs show `coupon` parameter, but WebFetch returned conflicting info about whether it's top-level or nested under `promotion`
   - What's unclear: Exact SDK v14 parameter structure for `client.v1.promotion_codes.create()`
   - Recommendation: LOW confidence on exact params -- verify during implementation by testing against Stripe test mode

3. **Price sync strategy for existing subscribers**
   - What we know: When admin changes price, new Stripe Price must be created. New subscriptions use new price.
   - What's unclear: Should existing subscribers be migrated to new price on next renewal? Or stay on old price until they change plans?
   - Recommendation: Keep existing subscribers on their current price. Only new checkouts and plan changes use the new Price ID. This is simplest and most predictable.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest with pytest-asyncio |
| Config file | backend/pytest.ini or pyproject.toml |
| Quick run command | `cd backend && python -m pytest tests/ -x --timeout=30` |
| Full suite command | `cd backend && python -m pytest tests/ --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIN-01 | View user subscription status | integration | Manual verification (admin UI) | Wave 0 |
| ADMIN-02 | View payment history per user | integration | Manual verification (admin UI) | Wave 0 |
| ADMIN-03 | Force-set user tier with Stripe sync | unit | `pytest tests/test_admin_billing.py::test_force_set_tier -x` | Wave 0 |
| ADMIN-04 | Cancel user subscription on behalf | unit | `pytest tests/test_admin_billing.py::test_admin_cancel_sub -x` | Wave 0 |
| ADMIN-05 | View Stripe billing event log | integration | Manual verification (admin UI) | Wave 0 |
| ADMIN-06 | Issue full or partial refund | unit | `pytest tests/test_admin_billing.py::test_refund -x` | Wave 0 |
| ADMIN-07 | Billing platform settings | unit | `pytest tests/test_billing_settings.py -x` | Wave 0 |
| ADMIN-08 | Create and manage discount codes | unit | `pytest tests/test_discount_codes.py -x` | Wave 0 |
| ADMIN-09 | Deactivate discount codes | unit | `pytest tests/test_discount_codes.py::test_deactivate -x` | Wave 0 |
| ADMIN-10 | Discount codes integrate with Stripe | integration | Manual verification (Stripe test mode) | Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run on changed module
- **Per wave merge:** Full backend test suite
- **Phase gate:** Full suite green + manual admin UI verification

### Wave 0 Gaps
- [ ] `tests/test_admin_billing.py` -- covers ADMIN-03, ADMIN-04, ADMIN-06
- [ ] `tests/test_billing_settings.py` -- covers ADMIN-07
- [ ] `tests/test_discount_codes.py` -- covers ADMIN-08, ADMIN-09

## Sources

### Primary (HIGH confidence)
- Stripe Refunds API docs: https://docs.stripe.com/api/refunds/create -- verified SDK v14 `client.v1.refunds.create()` pattern
- Stripe Coupons API docs: https://docs.stripe.com/api/coupons/create -- verified `client.v1.coupons.create()` pattern
- Stripe Promotion Codes API docs: https://docs.stripe.com/api/promotion_codes/create -- verified create flow
- Stripe Prices API docs: https://docs.stripe.com/api/prices/update -- confirmed Price immutability for unit_amount
- Stripe Events API docs: https://docs.stripe.com/api/events/list -- confirmed no customer_id filter available
- Existing codebase: SubscriptionService, admin routers, platform_settings service -- direct code review

### Secondary (MEDIUM confidence)
- Stripe Coupons/Promotion Codes guide: https://docs.stripe.com/billing/subscriptions/coupons -- flow documentation

### Tertiary (LOW confidence)
- Promotion Code create parameter structure (`coupon` top-level vs nested under `promotion`) -- conflicting WebFetch results, verify during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all existing libraries, no new dependencies
- Architecture: HIGH - follows established admin router/service/hook patterns in the codebase
- Pitfalls: HIGH - Stripe Price immutability and Events API limitations verified against official docs
- Stripe API patterns: MEDIUM - SDK v14 namespace verified for refunds/coupons, promotion code params need runtime verification

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain, Stripe SDK pinned)
