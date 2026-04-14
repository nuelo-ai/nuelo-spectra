# Phase 57: Stripe Backend & Webhook Foundation - Research

**Researched:** 2026-03-20
**Domain:** Stripe payment integration (Python SDK, webhooks, checkout sessions)
**Confidence:** HIGH

## Summary

Phase 57 integrates the Stripe Python SDK into the existing FastAPI backend to create checkout sessions (subscription and one-time payment) and process webhook events idempotently. The codebase already has all data models in place (Subscription, StripeEvent, PaymentHistory, CreditPackage), a mature CreditService with dual-balance operations, and an email service for notifications. The Next.js proxy already forwards raw body as `arrayBuffer()` which is compatible with Stripe signature verification.

The implementation is straightforward: add `stripe>=14.0.0` to dependencies, create a `SubscriptionService` class following the existing single-service-per-domain pattern (like CreditService), add two routers (webhook + subscription/checkout), and wire everything through FastAPI's dependency injection. All five webhook event types have clear handler logic defined in CONTEXT.md.

**Primary recommendation:** Use `stripe` Python SDK v14.x with synchronous API calls (they are IO-bound but fast), FastAPI `Request.body()` for raw webhook payload, and `stripe.Webhook.construct_event()` for signature verification. Store Stripe Price IDs in platform_settings (subscriptions) and CreditPackage table (top-ups).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Stripe webhook goes through the Next.js catch-all proxy -- backend is not publicly accessible
- Stripe POSTs to `https://app.yourdomain.com/api/webhooks/stripe`, proxy forwards to FastAPI at `/webhooks/stripe`
- Webhook processing is synchronous (inline during request) -- no background queue. Stripe retries on failure.
- Stripe API keys configured via environment variables: `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`
- Stripe prices managed in Stripe Dashboard -- store Stripe Price IDs in DB
- Server-side price resolution: client never controls the amount
- Stripe Customer created lazily on first checkout (not on registration)
- Full validation before creating checkout sessions: trial users cannot top-up (TRIAL-07), already-subscribed users cannot re-subscribe
- After successful checkout, redirect to Manage Plan page (`/settings/billing`)
- Phase 57 includes checkout API endpoints: `POST /subscriptions/checkout` and `POST /credits/purchase`
- Single `SubscriptionService` class handling all Stripe operations
- Single webhook router file with `POST /webhooks/stripe`
- Custom exception classes for Stripe errors
- All events deduplicated via `stripe_events` table before processing
- `checkout.session.completed` (subscription): activates subscription, creates/updates Subscription record, sets user tier
- `checkout.session.completed` (top-up): adds purchased credits to `purchased_balance` via CreditService
- `invoice.paid` (renewal): resets subscription credits to full tier allocation (unused credits lost). Purchased credits untouched.
- `invoice.payment_failed`: marks subscription status as `past_due` AND sends email notification
- `customer.subscription.updated`: handles plan changes -- updates `plan_tier` and `status`
- `customer.subscription.deleted`: credits remain usable until `current_period_end`, then zero out. User transitions to On Demand. Purchased credits preserved.
- Payment failure triggers both DB status flag AND email notification

### Claude's Discretion
- Exact SubscriptionService method signatures and internal organization
- Stripe metadata fields passed in checkout sessions
- Webhook handler error logging and retry behavior details
- Stripe Customer creation flow details (email, name, metadata)
- How cancel-at-period-end is tracked and enforced for credit zeroing
- Test structure and fixtures for webhook testing
- Email template content for payment failure notification

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STRIPE-01 | Stripe Python SDK integrated with API key config via env vars | `stripe>=14.0.0` added to pyproject.toml, Settings class extended with `stripe_secret_key` and `stripe_webhook_secret` |
| STRIPE-02 | Checkout Session creates subscription for Basic/Premium | `stripe.checkout.Session.create(mode="subscription", ...)` with Price ID from platform_settings |
| STRIPE-03 | Checkout Session creates one-time payment for credit top-ups | `stripe.checkout.Session.create(mode="payment", ...)` with Price ID from CreditPackage.stripe_price_id |
| STRIPE-04 | Webhook endpoint with signature verification and raw body parsing | `Request.body()` + `stripe.Webhook.construct_event()` + `Stripe-Signature` header |
| STRIPE-05 | Webhook idempotency via stripe_events deduplication table | Check StripeEvent by stripe_event_id before processing; insert on success |
| STRIPE-06 | `checkout.session.completed` activates subscription or adds credits | Route by `session.mode`: subscription vs payment; call CreditService or update Subscription |
| STRIPE-07 | `invoice.paid` handles renewal and credit reset | Call `CreditService.execute_reset()` with tier allocation; update `current_period_start/end` |
| STRIPE-08 | `invoice.payment_failed` marks subscription at risk and notifies user | Set status=`past_due` on Subscription; send email via existing SMTP service |
| STRIPE-09 | `customer.subscription.updated` handles plan changes | Update `plan_tier` and `status` on Subscription record; update user_class on User |
| STRIPE-10 | `customer.subscription.deleted` downgrades to On Demand at cycle end | Set `cancel_at_period_end=True`; subscription credits stay until `current_period_end` |
| SUB-06 | Subscription state stored locally with Stripe as source of truth | Subscription model already exists with all needed fields; webhooks keep it in sync |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stripe | >=14.0.0,<15.0 | Stripe API client for Python | Official Stripe SDK; handles API versioning, retries, signature verification |

### Supporting (already in project)
| Library | Purpose | Already Installed |
|---------|---------|-------------------|
| fastapi | HTTP framework, request handling | Yes |
| sqlalchemy[asyncio] | ORM for Subscription, StripeEvent, PaymentHistory | Yes |
| aiosmtplib + jinja2 | Email notifications for payment failures | Yes |
| pydantic-settings | Settings management for Stripe env vars | Yes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stripe SDK | Raw HTTP calls | SDK handles API versioning, retries, type hints -- no reason to go raw |
| Synchronous webhook | Background queue (Celery/ARQ) | Complexity not justified; Stripe retries on failure; operations are fast DB writes |

**Installation:**
```bash
# Add to backend/pyproject.toml dependencies:
"stripe>=14.0.0,<15.0",
```

**Version verification:** stripe 14.4.1 is latest on PyPI as of 2026-03-06. Requires Python >=3.7. Project uses Python >=3.12 -- fully compatible.

## Architecture Patterns

### New Files
```
backend/
├── app/
│   ├── config.py                    # ADD: stripe_secret_key, stripe_webhook_secret
│   ├── services/
│   │   └── subscription.py          # NEW: SubscriptionService class
│   ├── routers/
│   │   ├── webhooks.py              # NEW: POST /webhooks/stripe
│   │   └── subscriptions.py         # NEW: POST /subscriptions/checkout, POST /credits/purchase
│   ├── schemas/
│   │   └── subscription.py          # NEW: Pydantic schemas for checkout requests/responses
│   ├── exceptions/
│   │   └── stripe.py                # NEW: Custom Stripe exception classes
│   └── templates/
│       └── email/
│           ├── payment_failed.html  # NEW: Payment failure email template
│           └── payment_failed.txt   # NEW: Payment failure email (text)
```

### Pattern 1: SubscriptionService (Single Service Per Domain)
**What:** All Stripe operations go through one service class, matching CreditService pattern.
**When to use:** All Stripe API calls and webhook event handling.
**Example:**
```python
# backend/app/services/subscription.py
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings

class SubscriptionService:
    """Handles all Stripe operations: customers, checkout sessions, webhook events."""

    @staticmethod
    def _get_stripe_client() -> stripe.StripeClient:
        """Get configured Stripe client."""
        settings = get_settings()
        return stripe.StripeClient(settings.stripe_secret_key)

    @staticmethod
    async def get_or_create_customer(
        db: AsyncSession, user_id: UUID, email: str, name: str | None = None
    ) -> str:
        """Get existing Stripe Customer ID or create new one (lazy creation)."""
        # Check Subscription table for existing stripe_customer_id
        # If none, create via Stripe API, store on Subscription record
        ...

    @staticmethod
    async def create_subscription_checkout(
        db: AsyncSession, user_id: UUID, plan_tier: str, success_url: str, cancel_url: str
    ) -> str:
        """Create Stripe Checkout Session for subscription. Returns session URL."""
        ...

    @staticmethod
    async def create_topup_checkout(
        db: AsyncSession, user_id: UUID, package_id: UUID, success_url: str, cancel_url: str
    ) -> str:
        """Create Stripe Checkout Session for credit top-up. Returns session URL."""
        ...

    # Webhook handlers
    @staticmethod
    async def handle_checkout_completed(db: AsyncSession, session: dict) -> None: ...

    @staticmethod
    async def handle_invoice_paid(db: AsyncSession, invoice: dict) -> None: ...

    @staticmethod
    async def handle_invoice_payment_failed(db: AsyncSession, invoice: dict) -> None: ...

    @staticmethod
    async def handle_subscription_updated(db: AsyncSession, subscription: dict) -> None: ...

    @staticmethod
    async def handle_subscription_deleted(db: AsyncSession, subscription: dict) -> None: ...
```

### Pattern 2: Webhook Router with Signature Verification
**What:** Single endpoint that verifies Stripe signature, deduplicates events, dispatches to handlers.
**When to use:** All incoming Stripe webhook events.
**Example:**
```python
# backend/app/routers/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import stripe
from sqlalchemy import select
from app.config import get_settings
from app.database import get_db
from app.models.stripe_event import StripeEvent
from app.services.subscription import SubscriptionService

router = APIRouter(tags=["webhooks"])

EVENT_HANDLERS = {
    "checkout.session.completed": SubscriptionService.handle_checkout_completed,
    "invoice.paid": SubscriptionService.handle_invoice_paid,
    "invoice.payment_failed": SubscriptionService.handle_invoice_payment_failed,
    "customer.subscription.updated": SubscriptionService.handle_subscription_updated,
    "customer.subscription.deleted": SubscriptionService.handle_subscription_deleted,
}

@router.post("/webhooks/stripe", status_code=200)
async def stripe_webhook(request: Request):
    """Process Stripe webhook events with signature verification and deduplication."""
    settings = get_settings()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Deduplication check
    async for db in get_db():
        existing = await db.execute(
            select(StripeEvent).where(StripeEvent.stripe_event_id == event["id"])
        )
        if existing.scalar_one_or_none():
            return {"status": "already_processed"}

        # Dispatch to handler
        handler = EVENT_HANDLERS.get(event["type"])
        if handler:
            await handler(db, event["data"]["object"])

        # Record processed event
        db.add(StripeEvent(
            stripe_event_id=event["id"],
            event_type=event["type"],
        ))
        await db.commit()

    return {"status": "success"}
```

### Pattern 3: Checkout Endpoint with Server-Side Price Resolution
**What:** Client sends plan tier or package ID, server resolves Stripe Price ID from DB.
**When to use:** All checkout session creation.
**Example:**
```python
# backend/app/routers/subscriptions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.dependencies import CurrentUser, DbSession
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

class CheckoutRequest(BaseModel):
    plan_tier: str  # "standard" or "premium"

class CheckoutResponse(BaseModel):
    checkout_url: str

@router.post("/checkout", response_model=CheckoutResponse)
async def create_subscription_checkout(
    body: CheckoutRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create Stripe Checkout Session for subscription."""
    # Validation: trial users blocked, already-subscribed blocked
    if current_user.user_class == "free_trial":
        # Trial users CAN subscribe (this converts them)
        pass
    # Check for existing active subscription...

    url = await SubscriptionService.create_subscription_checkout(
        db, current_user.id, body.plan_tier,
        success_url=f"{settings.frontend_url}/settings/billing?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/settings/plan",
    )
    return CheckoutResponse(checkout_url=url)
```

### Pattern 4: Stripe Configuration via Settings + Platform Settings
**What:** API keys in Settings (env vars), Price IDs in platform_settings table or CreditPackage table.
**When to use:** Any Stripe configuration lookup.
**Example:**
```python
# In config.py Settings class:
stripe_secret_key: str = ""       # STRIPE_SECRET_KEY env var
stripe_webhook_secret: str = ""   # STRIPE_WEBHOOK_SECRET env var

# Price IDs stored in platform_settings:
# "stripe_price_basic_monthly" -> "price_xxx"
# "stripe_price_premium_monthly" -> "price_yyy"

# Credit package Price IDs stored in CreditPackage.stripe_price_id
```

### Anti-Patterns to Avoid
- **Client-controlled pricing:** Never accept price/amount from frontend. Always resolve from DB.
- **Webhook without deduplication:** Stripe retries, so same event may arrive multiple times. Always check `stripe_events` table first.
- **Webhook without signature verification:** Always verify `Stripe-Signature` header. Never skip in production.
- **Modifying raw body before verification:** The proxy passes `arrayBuffer()` which preserves bytes. Do NOT parse JSON before verification.
- **Setting `stripe.api_key` globally:** Use `StripeClient` instance or pass `api_key` per-call to avoid global state issues in async apps.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Webhook signature verification | Custom HMAC verification | `stripe.Webhook.construct_event()` | Handles timestamp tolerance, multiple signatures, constant-time comparison |
| Checkout flow | Custom payment form | Stripe Checkout Sessions | PCI compliance, 3D Secure, localization handled by Stripe |
| Customer management | Custom Stripe API calls | stripe SDK `Customer.create()` | SDK handles retries, API versioning, error types |
| Idempotency | Custom dedup logic | StripeEvent table + simple existence check | Model already exists, pattern is straightforward |

**Key insight:** The Stripe Python SDK handles all the hard parts (signature verification, API versioning, retries). The custom code should focus on business logic: mapping events to database operations.

## Common Pitfalls

### Pitfall 1: Raw Body Corruption in Webhook
**What goes wrong:** Stripe signature verification fails because the body was parsed/modified before verification.
**Why it happens:** Frameworks often parse JSON body automatically. FastAPI's `Request.body()` returns raw bytes, but using a Pydantic model dependency would parse it first.
**How to avoid:** Use `request.body()` directly in the webhook endpoint. Do NOT use Pydantic body parsing for the webhook route.
**Warning signs:** `SignatureVerificationError` on every webhook despite correct secret.

### Pitfall 2: Missing Stripe-Signature Header Through Proxy
**What goes wrong:** The Next.js proxy might not forward the `Stripe-Signature` header.
**Why it happens:** The proxy currently only forwards `Authorization` and `Content-Type` headers explicitly.
**How to avoid:** Update the proxy to forward the `Stripe-Signature` header (or forward all headers). This is a CRITICAL requirement.
**Warning signs:** Webhook endpoint always returns 400 "Missing Stripe-Signature header".

### Pitfall 3: Race Condition on Subscription Record Creation
**What goes wrong:** Two webhook events arrive nearly simultaneously for the same user, both try to create a Subscription record.
**Why it happens:** `checkout.session.completed` and `customer.subscription.updated` can fire close together.
**How to avoid:** Use `INSERT ... ON CONFLICT (user_id) DO UPDATE` or check-then-create with proper locking. The deduplication table prevents duplicate processing of the same event, but different events can still race.
**Warning signs:** IntegrityError on unique constraint for `user_id` in subscriptions table.

### Pitfall 4: Confusing Subscription Cancellation Flow
**What goes wrong:** User's credits are zeroed immediately on cancel instead of at period end.
**Why it happens:** `customer.subscription.deleted` fires when Stripe deletes the subscription, which happens at period end (if `cancel_at_period_end=true`). But `customer.subscription.updated` fires immediately with `cancel_at_period_end=true`.
**How to avoid:** On `subscription.updated` with `cancel_at_period_end=true`: set flag in DB, do NOT change credits. On `subscription.deleted`: transition user to on_demand, zero subscription credits.
**Warning signs:** Credits disappear before the billing period ends.

### Pitfall 5: Checkout Session Metadata Loss
**What goes wrong:** Webhook handler cannot determine which user or package a checkout belongs to.
**Why it happens:** Not passing enough metadata when creating the checkout session.
**How to avoid:** Always include `metadata` and `client_reference_id` on the checkout session: `client_reference_id=str(user_id)`, `metadata={"user_id": str(user_id), "plan_tier": "premium"}` for subscriptions, `metadata={"user_id": str(user_id), "package_id": str(package_id)}` for top-ups.
**Warning signs:** Webhook handler cannot link checkout to a user.

### Pitfall 6: User Tier Not Updated After Subscription Change
**What goes wrong:** Subscription record updates but `User.user_class` stays stale.
**Why it happens:** Forgetting to update the User model's `user_class` field alongside the Subscription record.
**How to avoid:** Every webhook handler that changes subscription state must also update `User.user_class` to match.
**Warning signs:** User sees old tier in UI, credit deduction uses wrong tier config.

## Code Examples

### Webhook Raw Body + Signature Verification (FastAPI)
```python
# Source: stripe-python official examples + FastAPI adaptation
@router.post("/webhooks/stripe", status_code=200)
async def stripe_webhook(request: Request):
    payload = await request.body()  # Raw bytes -- do NOT parse
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
```

### Create Subscription Checkout Session
```python
# Source: Stripe Checkout Session API docs
client = stripe.StripeClient(settings.stripe_secret_key)

session = client.checkout.sessions.create(params={
    "mode": "subscription",
    "customer": stripe_customer_id,
    "line_items": [{"price": stripe_price_id, "quantity": 1}],
    "success_url": success_url,
    "cancel_url": cancel_url,
    "client_reference_id": str(user_id),
    "metadata": {"user_id": str(user_id), "plan_tier": plan_tier},
    "subscription_data": {
        "metadata": {"user_id": str(user_id), "plan_tier": plan_tier},
    },
})
```

### Create Top-Up Payment Checkout Session
```python
session = client.checkout.sessions.create(params={
    "mode": "payment",
    "customer": stripe_customer_id,
    "line_items": [{"price": package.stripe_price_id, "quantity": 1}],
    "success_url": success_url,
    "cancel_url": cancel_url,
    "client_reference_id": str(user_id),
    "metadata": {
        "user_id": str(user_id),
        "package_id": str(package_id),
        "credit_amount": str(package.credit_amount),
        "payment_type": "topup",
    },
})
```

### Lazy Customer Creation
```python
async def get_or_create_customer(
    db: AsyncSession, user_id: UUID, email: str, name: str | None = None
) -> str:
    result = await db.execute(
        select(Subscription.stripe_customer_id)
        .where(Subscription.user_id == user_id)
    )
    existing_id = result.scalar_one_or_none()
    if existing_id:
        return existing_id

    client = SubscriptionService._get_stripe_client()
    customer = client.customers.create(params={
        "email": email,
        "name": name or email,
        "metadata": {"user_id": str(user_id)},
    })
    return customer.id
```

### Payment Failure Email (following existing email service pattern)
```python
# backend/app/services/email.py -- new function following existing pattern
async def send_payment_failed_email(
    to_email: str,
    first_name: str | None,
    settings: Settings,
) -> bool:
    display_name = first_name or "there"

    if not is_smtp_configured(settings):
        logger.info("Payment failed email (dev mode)", extra={"email": to_email})
        return True

    html_template = _jinja_env.get_template("payment_failed.html")
    text_template = _jinja_env.get_template("payment_failed.txt")

    template_vars = {"first_name": display_name, "billing_url": f"{settings.frontend_url}/settings/billing"}
    # ... same SMTP send pattern as send_password_reset_email
```

### Proxy Header Forwarding Fix
```typescript
// frontend/src/app/api/[...slug]/route.ts
// ADD Stripe-Signature to forwarded headers:
const stripeSignature = request.headers.get("stripe-signature");
if (stripeSignature) headers["Stripe-Signature"] = stripeSignature;
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `stripe.api_key = "sk_..."` global | `stripe.StripeClient(api_key)` instance | stripe-python v7+ | Thread-safe, no global state |
| `stripe.Event.construct_from()` | `stripe.Webhook.construct_event()` | stripe-python v2+ | Built-in signature verification |
| Charges API | Payment Intents / Checkout Sessions | 2019+ | SCA compliance, better UX |
| Custom payment forms | Stripe Checkout (hosted/embedded) | 2019+ | PCI scope reduction |

**Deprecated/outdated:**
- `stripe.Charge.create()`: Use Checkout Sessions or Payment Intents instead
- Setting `stripe.api_key` globally: Use `StripeClient` instance for async safety
- `stripe.error.*` exception module path: In v14.x, use `stripe.SignatureVerificationError` directly

## Open Questions

1. **Stripe-Signature header forwarding through proxy**
   - What we know: Proxy currently only forwards `Authorization` and `Content-Type` explicitly
   - What's unclear: Whether this is sufficient or if we need to add `Stripe-Signature`
   - Recommendation: **Must update proxy to forward `Stripe-Signature` header.** This is critical. Add it to the explicit header forwarding list.

2. **StripeClient vs module-level stripe calls**
   - What we know: stripe-python v14.x supports both `stripe.checkout.Session.create()` (module-level) and `StripeClient().checkout.sessions.create()` (instance)
   - What's unclear: Whether the StripeClient approach works cleanly with `construct_event`
   - Recommendation: Use module-level `stripe.api_key` setting at startup for simplicity (set once in lifespan), use `stripe.Webhook.construct_event()` for webhook verification. This is the most common pattern in FastAPI integrations.

3. **Platform settings keys for subscription Price IDs**
   - What we know: Platform settings service exists with validation
   - What's unclear: Exact key names for subscription tier prices
   - Recommendation: Add `stripe_price_basic_monthly` and `stripe_price_premium_monthly` to DEFAULTS in platform_settings.py, with empty string defaults. These get populated when Stripe Dashboard is configured.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.23.x |
| Config file | backend/pyproject.toml (dev dependencies) |
| Quick run command | `cd backend && python -m pytest tests/test_subscription_service.py -x` |
| Full suite command | `cd backend && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STRIPE-01 | Stripe SDK initialized, settings loaded | unit | `pytest tests/test_stripe_config.py -x` | No -- Wave 0 |
| STRIPE-04 | Webhook signature verification | unit | `pytest tests/test_webhook.py::test_signature_verification -x` | No -- Wave 0 |
| STRIPE-05 | Event deduplication | unit | `pytest tests/test_webhook.py::test_deduplication -x` | No -- Wave 0 |
| STRIPE-06 | checkout.session.completed handler | unit | `pytest tests/test_webhook.py::test_checkout_completed -x` | No -- Wave 0 |
| STRIPE-07 | invoice.paid handler credit reset | unit | `pytest tests/test_webhook.py::test_invoice_paid -x` | No -- Wave 0 |
| STRIPE-08 | invoice.payment_failed handler | unit | `pytest tests/test_webhook.py::test_invoice_payment_failed -x` | No -- Wave 0 |
| STRIPE-09 | subscription.updated handler | unit | `pytest tests/test_webhook.py::test_subscription_updated -x` | No -- Wave 0 |
| STRIPE-10 | subscription.deleted handler | unit | `pytest tests/test_webhook.py::test_subscription_deleted -x` | No -- Wave 0 |
| STRIPE-02 | Subscription checkout session creation | unit | `pytest tests/test_subscription_service.py::test_create_subscription_checkout -x` | No -- Wave 0 |
| STRIPE-03 | Top-up checkout session creation | unit | `pytest tests/test_subscription_service.py::test_create_topup_checkout -x` | No -- Wave 0 |
| SUB-06 | Subscription state stored locally | unit | `pytest tests/test_billing_models.py -x` | Yes (exists) |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_webhook.py tests/test_subscription_service.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_webhook.py` -- covers STRIPE-04 through STRIPE-10 (webhook signature, dedup, all handlers)
- [ ] `tests/test_subscription_service.py` -- covers STRIPE-01, STRIPE-02, STRIPE-03 (SDK config, checkout creation)
- [ ] Mock fixtures for Stripe API responses (stripe Event objects, Session objects, Customer objects)
- [ ] stripe package install: add `"stripe>=14.0.0,<15.0"` to pyproject.toml dependencies

## Sources

### Primary (HIGH confidence)
- [stripe PyPI](https://pypi.org/project/stripe/) -- v14.4.1 latest, Python >=3.7
- [Stripe webhook signature docs](https://docs.stripe.com/webhooks/signature) -- `construct_event()` API
- [stripe-python webhook example](https://github.com/stripe/stripe-python/blob/master/examples/webhooks.py) -- raw body handling
- [Stripe Checkout Session API](https://docs.stripe.com/api/checkout/sessions/create?lang=python) -- create session params
- Existing codebase: models, services, routers, proxy, config -- all read directly

### Secondary (MEDIUM confidence)
- [FastAPI Stripe integration tutorial](https://www.fast-saas.com/blog/fastapi-stripe-integration/) -- FastAPI-specific patterns
- [Stripe webhook setup docs](https://docs.stripe.com/webhooks/quickstart) -- endpoint setup guide

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- stripe SDK is the only option, version verified on PyPI
- Architecture: HIGH -- follows existing codebase patterns exactly (CreditService, router pattern, email service)
- Pitfalls: HIGH -- well-documented issues (raw body, header forwarding, deduplication) from official docs and community
- Webhook handlers: HIGH -- CONTEXT.md has extremely detailed handler behavior specs

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable domain, SDK versioning is predictable)
