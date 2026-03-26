# Architecture Research: Spectra Monetization Integration

**Domain:** Payment gateway + subscription management for existing SaaS analytics platform
**Researched:** 2026-03-18
**Confidence:** HIGH

## System Overview

Integration adds Stripe payment processing, subscription lifecycle management, and billing UI to the existing Spectra credit-based analytics platform. The key insight: Spectra already has a credit system with atomic deduction, tier-based allocations, and transaction logging. Monetization wraps Stripe around the existing credit engine rather than replacing it.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Plan Select  │  │ Manage Plan  │  │  Trial Banner / Upgrade  │  │
│  │ /settings/   │  │ /settings/   │  │  Prompt (global overlay) │  │
│  │ plan         │  │ billing      │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
│         │                 │                      │                  │
├─────────┴─────────────────┴──────────────────────┴──────────────────┤
│                    Route Handler Proxy (/api/*)                      │
├─────────────────────────────────────────────────────────────────────┤
│                         Backend Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ BillingRouter│  │StripeWebhook │  │ CreditService│              │
│  │ /billing/*   │  │ /webhooks/   │  │ (EXISTING)   │              │
│  │              │  │ stripe       │  │              │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                      │
│  ┌──────┴─────────────────┴──────────────────┴───────┐              │
│  │              SubscriptionService (NEW)              │              │
│  │  - Stripe Checkout session creation                │              │
│  │  - Subscription lifecycle management               │              │
│  │  - Tier transition logic                           │              │
│  │  - Credit source tracking                          │              │
│  └──────────────────────┬────────────────────────────┘              │
│                         │                                           │
├─────────────────────────┴───────────────────────────────────────────┤
│                         Data Layer                                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ users    │  │ subscriptions│  │payment_history│  │credit_    │  │
│  │(MODIFIED)│  │    (NEW)     │  │   (NEW)      │  │packages   │  │
│  │          │  │              │  │              │  │  (NEW)    │  │
│  └──────────┘  └──────────────┘  └──────────────┘  └───────────┘  │
│  ┌──────────┐  ┌──────────────┐                                    │
│  │user_     │  │credit_       │  Existing tables                   │
│  │credits   │  │transactions  │  (MODIFIED: new credit_source col) │
│  │(MODIFIED)│  │ (MODIFIED)   │                                    │
│  └──────────┘  └──────────────┘                                    │
├─────────────────────────────────────────────────────────────────────┤
│                     External Services                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Stripe API                                │   │
│  │  Products/Prices │ Checkout Sessions │ Webhooks │ Customers  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | New vs Modified |
|-----------|----------------|-----------------|
| **SubscriptionService** | Stripe Checkout session creation, subscription CRUD, tier transition logic, credit source tracking | NEW |
| **BillingRouter** | `/billing/*` endpoints for plan selection, subscription management, top-up purchases, billing history | NEW |
| **StripeWebhookRouter** | `/webhooks/stripe` endpoint with raw body signature verification, event dispatch | NEW |
| **TrialService** | Trial expiration checks, blocked state enforcement, trial banner data | NEW |
| **CreditService** | Atomic deduction with credit source priority (subscription first, purchased second) | MODIFIED |
| **UserCredit model** | Add `purchased_balance` column to track non-expiring purchased credits separately | MODIFIED |
| **User model** | Add `stripe_customer_id` and `trial_expires_at` columns | MODIFIED |
| **CreditTransaction model** | Add `credit_source` column (subscription/purchased/trial) | MODIFIED |
| **user_classes.yaml** | Restructure tiers: drop `free`, rename `standard` -> `basic`, add `on_demand` | MODIFIED |
| **PlatformSettings** | Add billing-related settings (trial_duration_days, credit_price_per_unit, subscription prices/credits) | MODIFIED |
| **Auth middleware** | Add trial expiration check on authenticated requests | MODIFIED |
| **Admin BillingRouter** | Admin billing visibility, override, cancel, refund capabilities | NEW |
| **Plan Selection page** | `/settings/plan` with tier cards and Stripe Checkout redirect | NEW |
| **Manage Plan page** | `/settings/billing` with subscription details, buy credits, billing history | NEW |
| **Trial Banner** | Global overlay component for trial status and forced upgrade prompt | NEW |

## Recommended Project Structure

### Backend (new/modified files)

```
backend/app/
├── models/
│   ├── user.py                    # MODIFY: add stripe_customer_id, trial_expires_at
│   ├── user_credit.py             # MODIFY: add purchased_balance column
│   ├── credit_transaction.py      # MODIFY: add credit_source column
│   ├── subscription.py            # NEW: Subscription model
│   ├── payment_history.py         # NEW: PaymentHistory model
│   └── credit_package.py          # NEW: CreditPackage model
├── schemas/
│   ├── billing.py                 # NEW: Pydantic schemas for billing endpoints
│   └── credit.py                  # MODIFY: add credit_source to response schemas
├── services/
│   ├── credit.py                  # MODIFY: credit source priority deduction
│   ├── subscription.py            # NEW: Stripe integration + subscription lifecycle
│   ├── trial.py                   # NEW: trial expiration logic
│   └── stripe_webhook.py          # NEW: webhook event dispatch + handlers
├── routers/
│   ├── billing.py                 # NEW: /billing/* endpoints (public)
│   ├── webhooks.py                # NEW: /webhooks/stripe (unauthenticated, signature-verified)
│   └── admin/
│       └── billing.py             # NEW: admin billing management endpoints
├── config/
│   └── user_classes.yaml          # MODIFY: restructure tiers
└── main.py                        # MODIFY: register new routers, add trial middleware
```

### Frontend (new/modified files)

```
frontend/src/
├── app/
│   └── (dashboard)/
│       └── settings/
│           ├── plan/
│           │   └── page.tsx       # NEW: Plan Selection page
│           └── billing/
│               └── page.tsx       # NEW: Manage Plan + Buy Credits page
├── components/
│   ├── billing/
│   │   ├── plan-card.tsx          # NEW: tier selection card component
│   │   ├── credit-package-card.tsx # NEW: credit top-up package card
│   │   ├── billing-history.tsx    # NEW: billing history table
│   │   └── subscription-status.tsx # NEW: current plan status display
│   ├── trial-banner.tsx           # NEW: trial countdown banner
│   └── upgrade-prompt.tsx         # NEW: blocking upgrade overlay
├── hooks/
│   ├── use-billing.ts             # NEW: TanStack Query hooks for billing API
│   └── use-trial.ts              # NEW: trial status hook
└── stores/
    └── billing-store.ts           # NEW: Zustand store for billing state
```

### Admin Frontend (new files)

```
admin-frontend/src/
├── app/
│   └── (admin)/
│       └── billing/
│           └── page.tsx           # NEW: Admin billing overview
├── components/
│   └── billing/
│       ├── user-subscription.tsx  # NEW: per-user subscription view
│       ├── billing-event-log.tsx  # NEW: Stripe event history
│       └── refund-dialog.tsx      # NEW: admin refund modal
```

### Structure Rationale

- **`services/subscription.py` as the core orchestrator:** All Stripe API calls go through this service. Routers and webhook handlers call SubscriptionService methods. This keeps Stripe coupling in one place.
- **`services/stripe_webhook.py` separate from `services/subscription.py`:** Webhook event parsing and dispatch is a different concern from subscription business logic. The webhook handler maps events to SubscriptionService method calls.
- **`routers/webhooks.py` as a separate router (not under `/billing/`):** The webhook endpoint is unauthenticated (no JWT) but signature-verified. It must not go through the auth middleware. Keeping it in a separate router makes this explicit.
- **Billing components in `components/billing/`:** Groups all billing UI together. The plan card, credit package card, and subscription status components are reused across Plan Selection and Manage Plan pages.
- **Trial banner and upgrade prompt as global components:** These live outside the billing folder because they appear on every page, not just billing pages.

## Architectural Patterns

### Pattern 1: Stripe as Source of Truth for Subscription State

**What:** Stripe owns the canonical subscription state. The local `subscriptions` table is a cache synced via webhooks. Never trust local state for billing decisions -- always verify with Stripe for critical operations (e.g., before granting access after a plan change).

**When to use:** All subscription lifecycle operations.

**Trade-offs:** Adds Stripe API latency to some operations, but eliminates state drift bugs. The local cache handles 99% of reads (displaying subscription info to user), and webhooks keep it updated.

**Example:**

```python
# services/subscription.py

class SubscriptionService:
    @staticmethod
    async def create_checkout_session(
        db: AsyncSession,
        user_id: UUID,
        price_id: str,
        mode: str,  # "subscription" or "payment" (for top-ups)
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create Stripe Checkout Session. Returns checkout URL."""
        user = await db.get(User, user_id)

        # Get or create Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"spectra_user_id": str(user_id)},
            )
            user.stripe_customer_id = customer.id
            await db.flush()

        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"spectra_user_id": str(user_id)},
        )
        return session.url
```

### Pattern 2: Webhook Event Dispatch with Idempotency

**What:** The webhook endpoint verifies the Stripe signature, then dispatches to typed handler functions. Each handler is idempotent -- processing the same event twice produces the same result. Use `stripe_event_id` deduplication to short-circuit already-processed events.

**When to use:** All Stripe webhook processing.

**Trade-offs:** Requires a processed events tracking mechanism (column on PaymentHistory or separate table). Small storage cost, large correctness gain.

**Example:**

```python
# routers/webhooks.py

from fastapi import APIRouter, Request, HTTPException

router = APIRouter(tags=["webhooks"])

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook receiver. No auth middleware -- uses signature verification."""
    payload = await request.body()  # Raw bytes, NOT .json()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Dispatch to handler
    handler = WEBHOOK_HANDLERS.get(event["type"])
    if handler:
        await handler(db, event)

    return {"status": "ok"}

# Event handler map
WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_payment_failed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
}
```

### Pattern 3: Credit Source Priority Deduction

**What:** Track credits by source (subscription vs purchased). When deducting, consume subscription credits first (they expire at cycle end) and purchased credits second (they persist). This requires splitting the single `balance` field into `balance` (subscription) + `purchased_balance`.

**When to use:** Every credit deduction operation.

**Trade-offs:** Adds complexity to CreditService.deduct_credit(). The alternative (single pool) is simpler but users lose purchased credits unfairly at subscription reset. Source tracking is the correct approach for a paid product.

**Example:**

```python
# Modified CreditService.deduct_credit() logic:
# 1. Try subscription balance first
# 2. Remaining cost from purchased balance
# 3. Record which source(s) were used in CreditTransaction.credit_source

async def deduct_credit(db, user_id, cost, api_key_id=None):
    credit = await get_credit_row_locked(db, user_id)

    sub_balance = Decimal(str(credit.balance))
    purchased = Decimal(str(credit.purchased_balance))
    total = sub_balance + purchased

    if total < cost:
        return CreditDeductionResult(success=False, ...)

    # Deduct from subscription first
    from_sub = min(sub_balance, cost)
    from_purchased = cost - from_sub

    credit.balance = sub_balance - from_sub
    credit.purchased_balance = purchased - from_purchased

    # Log with source tracking
    ...
```

### Pattern 4: Trial Expiration via Auth Middleware Check

**What:** Add a lightweight trial expiration check to the existing auth dependency. If `user.trial_expires_at` is set and has passed AND `user.user_class == "free_trial"`, return a 403 with a specific error code that the frontend uses to show the upgrade prompt.

**When to use:** Every authenticated request for trial users.

**Trade-offs:** Adds a datetime comparison to every request for trial users (negligible cost). The alternative (background scheduler) has a lag window where expired trial users can still use the system. Middleware check is instant.

**Example:**

```python
# In auth dependency (or as middleware):
if user.user_class == "free_trial" and user.trial_expires_at:
    if datetime.now(timezone.utc) >= user.trial_expires_at:
        raise HTTPException(
            status_code=403,
            detail={"code": "TRIAL_EXPIRED", "message": "Free trial has expired"}
        )
```

## Data Flow

### Subscription Purchase Flow

```
User clicks "Subscribe" on Plan Selection page
    |
    v
Frontend POST /api/billing/subscribe { price_id, plan_tier }
    |
    v
BillingRouter -> SubscriptionService.create_checkout_session()
    |
    v
Stripe Checkout Session created (returns URL)
    |
    v
Frontend redirects to Stripe Checkout hosted page
    |
    v
User completes payment on Stripe
    |
    v
Stripe sends checkout.session.completed webhook
    |
    v
POST /webhooks/stripe (raw body + signature verification)
    |
    v
stripe_webhook.py -> handle_checkout_completed()
    |
    v
SubscriptionService:
    1. Create/update Subscription row
    2. Update user.user_class to new tier
    3. Allocate subscription credits (CreditService.execute_reset)
    4. Create PaymentHistory record
    |
    v
User returns to success_url (/settings/billing)
Frontend fetches GET /api/billing/manage -> sees active subscription
```

### Credit Top-Up Flow

```
User selects credit package on Manage Plan page
    |
    v
Frontend POST /api/billing/top-up { package_id }
    |
    v
BillingRouter -> SubscriptionService.create_checkout_session(mode="payment")
    |
    v
Stripe Checkout Session (one-time payment)
    |
    v
User pays -> checkout.session.completed webhook
    |
    v
handle_checkout_completed():
    1. credit.purchased_balance += package.credit_amount
    2. Create CreditTransaction(type="top_up", credit_source="purchased")
    3. Create PaymentHistory record
```

### Monthly Renewal Flow

```
Stripe charges customer at cycle end
    |
    v
invoice.paid webhook received
    |
    v
handle_invoice_paid():
    1. Update subscription.current_period_start/end
    2. Reset subscription credits: credit.balance = tier_allocation
    3. Purchased credits UNTOUCHED
    4. Create PaymentHistory record
    5. Create CreditTransaction(type="subscription_renewal")
```

### State Management (Frontend)

```
Zustand billing-store:
    subscription: { plan, status, current_period_end, credits_remaining }
    trial: { expires_at, days_remaining, is_expired }
    |
    v
TanStack Query:
    useSubscription() -> GET /api/billing/manage
    usePlans() -> GET /api/billing/plans
    useBillingHistory() -> GET /api/billing/manage (includes history)
    useTrialStatus() -> derived from user auth response
    |
    v
Components subscribe to store + queries
```

## Integration Points with Existing Architecture

### Critical Integration: Stripe Webhook Bypasses Auth and Proxy

The Stripe webhook endpoint at `/webhooks/stripe` has two unique requirements that break the normal request flow:

1. **No JWT auth:** The endpoint must be unauthenticated. Stripe sends POST requests with signature headers, not JWT tokens.
2. **Raw body access:** Signature verification requires the exact bytes Stripe sent. The existing route handler proxy in `frontend/src/app/api/[...slug]/route.ts` reads `request.arrayBuffer()` and forwards it, which preserves bytes. This should work, but introduces an unnecessary hop.

**Recommendation:** Expose the webhook endpoint directly on the FastAPI backend, bypassing the Next.js proxy. In production (Dokploy), configure Stripe to hit the backend service directly. The webhook URL in Stripe Dashboard should point to the backend origin (not the frontend proxy).

If the proxy must be used (e.g., single-domain deployment), it will work because the catch-all proxy already forwards raw `arrayBuffer()` bodies. But direct is simpler and eliminates a failure point.

### Integration: SPECTRA_MODE Router Registration

The existing `main.py` conditionally registers routers based on `SPECTRA_MODE`. Billing routers need:

| Router | Modes |
|--------|-------|
| `billing.py` (user-facing) | `public`, `dev` |
| `webhooks.py` (Stripe webhook) | `public`, `dev` |
| `admin/billing.py` (admin tools) | `admin`, `dev` |

This follows the existing split-horizon pattern. No architectural change needed -- just add the new routers to the mode conditionals in `main.py`.

### Integration: APScheduler Credit Reset Must Respect Credit Sources

The existing scheduler runs `CreditService.execute_reset()` which sets `balance = tier_allocation`. After monetization, this must be changed to:

1. Reset only `balance` (subscription credits) to tier allocation
2. Leave `purchased_balance` untouched
3. The scheduler logic in `app/scheduler.py` likely iterates users and checks `is_reset_due()` -- this continues to work but `execute_reset()` internals change.

**Important:** For subscription tiers (basic/premium), the monthly reset should be driven by Stripe's `invoice.paid` webhook, NOT the APScheduler. The scheduler remains for non-subscription tiers only. This prevents double-resets and keeps Stripe as the billing cycle authority.

### Integration: user_classes.yaml Restructure

Current tiers: `free_trial`, `free`, `standard`, `premium`, `internal`
Target tiers: `free_trial`, `on_demand`, `basic`, `premium`, `internal`

Changes:
- **Drop `free`:** No more ongoing free tier. Existing `free` users need a migration path (force to trial state or grandfather them).
- **Rename `standard` -> `basic`:** Name change + credit allocation changes.
- **Add `on_demand`:** New tier with `credits: 0`, `reset_policy: none`, `top_up_eligible: true`.
- **Modify `free_trial`:** Add `top_up_eligible: false` flag.

This requires an Alembic migration to update `user.user_class` for existing users.

### Integration: Platform Settings Expansion

Add new settings to `DEFAULTS` dict in `platform_settings.py`:

```python
DEFAULTS: dict[str, str] = {
    # ... existing settings ...
    "trial_duration_days": json.dumps(14),
    "credit_price_per_unit": json.dumps("0.10"),  # $0.10 per credit
    "subscription_price_basic": json.dumps("29.00"),
    "subscription_price_premium": json.dumps("79.00"),
    "subscription_credits_basic": json.dumps(200),
    "subscription_credits_premium": json.dumps(500),
}
```

Add corresponding validation in `validate_setting()`. Existing 30s TTL cache pattern applies.

### Integration: Frontend Catch-All Proxy

The existing `/api/[...slug]/route.ts` will proxy billing API calls automatically (`/api/billing/*` -> backend `/billing/*`). No change needed to the proxy. New pages at `/settings/plan` and `/settings/billing` are purely frontend routes -- they call the proxied API.

### Integration: Admin Frontend

The admin frontend has its own catch-all proxy (same pattern). New admin billing endpoints (`/admin/billing/*`) will be proxied automatically. New admin billing page goes under `(admin)/billing/`.

## External Services

| Service | Integration Pattern | Gotchas |
|---------|---------------------|---------|
| **Stripe API** | `stripe` Python SDK. Configure `stripe.api_key` from env var at startup. SDK v5+ supports async natively. | Test mode vs live mode keys. Webhook signing secrets differ per environment. Must use raw request body for webhook verification. |
| **Stripe Checkout** | Server-side session creation, client-side redirect to Stripe-hosted page. No need to handle card details. PCI compliance delegated to Stripe. | Success URL redirect can be faked -- never trust it for fulfillment. Always use webhooks. |
| **Stripe Customer Portal** | Optional. Could replace self-built Manage Plan page. | Less customizable. Spectra's credit system is custom, so a fully Stripe-hosted portal will not show credit balances. Build own Manage Plan page. |

## Anti-Patterns

### Anti-Pattern 1: Fulfilling Orders on Checkout Success URL

**What people do:** Grant access/credits when the user returns to the success URL after Stripe Checkout.
**Why it's wrong:** The success URL redirect can fail (user closes browser, network error) or be manually navigated to. The user would get nothing despite paying.
**Do this instead:** Only fulfill (grant subscription, add credits) in the webhook handler for `checkout.session.completed`. The success URL page should poll or show a "processing" state, then refresh when the webhook has been processed.

### Anti-Pattern 2: Storing Stripe Secret Keys in Platform Settings

**What people do:** Put Stripe API keys in the platform_settings database table for runtime configurability.
**Why it's wrong:** Stripe secret keys are highly sensitive. The platform_settings table is readable by all admin users and may appear in logs. Database backups expose the keys.
**Do this instead:** Store `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` as environment variables only. Only non-secret Stripe config (publishable key, price IDs) goes in platform_settings or env vars.

### Anti-Pattern 3: Mixing Credit Sources in a Single Balance Column

**What people do:** Add purchased credits directly to the existing `balance` column.
**Why it's wrong:** When the monthly subscription reset runs, it sets `balance = tier_allocation`, wiping out any purchased credits the user had. Credits the user paid money for disappear.
**Do this instead:** Track `balance` (subscription credits, reset monthly) and `purchased_balance` (never reset, never expire) as separate columns on `user_credits`. Deduction draws from subscription first, purchased second.

### Anti-Pattern 4: Trusting Local Subscription State for Access Control

**What people do:** Check the local `subscriptions` table to determine if a user has an active subscription without considering webhook delays.
**Why it's wrong:** Webhooks can be delayed, missed, or the local state can drift from Stripe reality. A user whose payment failed might still show "active" locally.
**Do this instead:** For non-critical reads (display purposes), use local state. For critical access decisions (granting access after upgrade, blocking after cancellation), verify with a Stripe API call or ensure webhook processing is idempotent and deduped.

### Anti-Pattern 5: Running Subscription Credit Resets from Both Scheduler and Webhooks

**What people do:** Keep the existing APScheduler monthly reset running AND handle `invoice.paid` webhook credit resets.
**Why it's wrong:** Double-resets. If both fire for a subscription user, credits get reset twice. If the scheduler fires before the webhook, it resets credits before payment is confirmed.
**Do this instead:** For subscription tiers (basic/premium), credit resets are driven exclusively by `invoice.paid` webhooks. The APScheduler continues only for non-subscription tiers (on_demand with manual admin resets, if any). Add a check in the scheduler: skip users whose `user_class` is a subscription tier.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Current architecture is fine. Single backend instance handles webhooks. SQLite-level webhook volume. |
| 1k-10k users | Webhook processing should be fast (< 1s). If slow, consider async task queue for webhook handlers. Stripe retries on timeout. |
| 10k+ users | Move webhook processing to a background task queue (Celery/ARQ). Return 200 immediately, process asynchronously. Add webhook event dedup table. |

### Scaling Priorities

1. **First bottleneck: Webhook processing time.** If handlers take > 5s, Stripe retries and you get duplicate processing. Keep handlers fast. Use idempotency keys.
2. **Second bottleneck: Credit deduction contention.** The existing `SELECT FOR UPDATE` pattern on `user_credits` is correct but creates a bottleneck under high concurrency for the same user. Unlikely to be an issue before 10k+ users.

## Alembic Migration Plan

The monetization feature requires multiple Alembic migrations. Recommended ordering:

1. **Migration 1: Add columns to existing tables**
   - `users.stripe_customer_id` (String, nullable)
   - `users.trial_expires_at` (DateTime(timezone=True), nullable)
   - `user_credits.purchased_balance` (NUMERIC(10,1), default 0)
   - `credit_transactions.credit_source` (String(20), nullable)

2. **Migration 2: Create new tables**
   - `subscriptions` (id, user_id, stripe_subscription_id, stripe_customer_id, plan_tier, status, current_period_start, current_period_end, cancel_at_period_end, created_at, updated_at)
   - `payment_history` (id, user_id, stripe_payment_intent_id, stripe_event_id, amount_cents, currency, type, credit_amount, status, created_at)
   - `credit_packages` (id, name, credit_amount, price_cents, stripe_price_id, is_active, created_at)

3. **Migration 3: Tier restructure (data migration)**
   - Update `users.user_class`: rename `standard` -> `basic`, migrate `free` users (decision needed: -> `free_trial` with 14-day clock or -> `on_demand`)
   - Seed `credit_packages` with initial top-up options
   - Update `user_classes.yaml` simultaneously (file change, not DB migration, but must be deployed atomically with the migration)
   - Backfill `trial_expires_at` for existing `free_trial` users: `created_at + 14 days`

## Build Order (Suggested Phase Structure)

Based on dependency analysis, the recommended build order is:

1. **Tier Restructure + Trial Expiration** (no Stripe dependency)
   - Restructure user_classes.yaml
   - Add `trial_expires_at` to User model
   - Trial expiration middleware check
   - Upgrade prompt UI (static -- no payment yet)
   - Alembic migrations 1 + 3

2. **Stripe Core + Webhook Foundation** (backend only)
   - `stripe` SDK integration, env var setup
   - SubscriptionService + Subscription model
   - Webhook endpoint with signature verification
   - Event handlers for checkout.session.completed, invoice.paid, subscription lifecycle
   - PaymentHistory model + CreditPackage model
   - Alembic migration 2

3. **Credit Source Tracking** (modifies existing CreditService)
   - Add `purchased_balance` to UserCredit
   - Modify CreditService.deduct_credit() for source priority
   - Modify scheduler's execute_reset() to preserve purchased credits
   - Alembic migration 1 (purchased_balance part)

4. **Billing UI** (frontend, depends on backend endpoints)
   - Plan Selection page
   - Manage Plan page (subscription details + buy credits + billing history)
   - Trial banner component
   - Settings navigation update

5. **Admin Billing Tools** (admin frontend, depends on backend)
   - Admin billing overview page
   - Per-user subscription view
   - Override, cancel, refund capabilities
   - Billing event log

## Sources

- [FastAPI Stripe Payment Gateway Integration (2025)](https://www.fast-saas.com/blog/fastapi-stripe-integration/)
- [Building a Stripe Subscription Backend with FastAPI](https://dev.to/fastapier/building-a-stripe-subscription-backend-with-fastapi-3n3)
- [Building a Payment Backend with FastAPI, Stripe Checkout, and Webhooks](https://medium.com/@abdulikram/building-a-payment-backend-with-fastapi-stripe-checkout-and-webhooks-08dc15a32010)
- [Stripe Webhook Signature Verification](https://docs.stripe.com/webhooks/signature)
- [Stripe Build Subscriptions with Checkout](https://docs.stripe.com/payments/checkout/build-subscriptions)
- [Stripe Receive Webhook Events](https://docs.stripe.com/webhooks)
- [Stripe Checkout Sessions API Updates (2025-03-31)](https://docs.stripe.com/changelog/basil/2025-03-31/checkout-legacy-subscription-upgrade)
- Spectra codebase: `backend/app/services/credit.py`, `backend/app/models/user.py`, `backend/app/models/user_credit.py`, `backend/app/models/credit_transaction.py`, `backend/app/services/platform_settings.py`, `backend/app/config/user_classes.yaml`, `frontend/src/app/api/[...slug]/route.ts`
- Spectra requirements: `requirements/monetization-requirement.md`, `requirements/monetization-milestone-plan.md`

---
*Architecture research for: Spectra Monetization (Stripe payment gateway, subscription management, billing UI, admin billing tools)*
*Researched: 2026-03-18*
