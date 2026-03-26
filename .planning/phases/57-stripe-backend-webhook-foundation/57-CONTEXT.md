# Phase 57: Stripe Backend & Webhook Foundation - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend payment infrastructure that integrates Stripe SDK, creates checkout sessions for subscriptions and one-time credit top-ups, and processes webhook events idempotently. Covers: SubscriptionService, webhook endpoint with signature verification and deduplication, all event handlers (checkout.session.completed, invoice.paid, invoice.payment_failed, customer.subscription.updated, customer.subscription.deleted), checkout session API endpoints, and payment failure email notifications. Does NOT include frontend UI (Phase 58), admin billing tools (Phase 59), or annual billing/multi-currency (deferred).

</domain>

<decisions>
## Implementation Decisions

### Webhook routing & security
- Stripe webhook goes through the Next.js catch-all proxy (`/api/[...slug]/route.ts`) — backend is not publicly accessible per deployment architecture
- Stripe POSTs to `https://app.yourdomain.com/api/webhooks/stripe`, proxy forwards to FastAPI at `/webhooks/stripe`
- No dedicated Next.js route handler needed — existing proxy already forwards raw body as `arrayBuffer()`, which is compatible with Stripe signature verification
- Webhook processing is synchronous (inline during request) — no background queue. Stripe retries on failure.
- Stripe API keys configured via environment variables: `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`, with test keys in dev and live keys in production

### Checkout session design
- Stripe prices managed in Stripe Dashboard — create Products and Prices there, store Stripe Price IDs in DB (`CreditPackage.stripe_price_id` for top-ups, platform settings for subscription prices)
- Server-side price resolution: client never controls the amount, backend looks up Price ID from DB
- Stripe Customer created lazily on first checkout (not on registration) — stored on Subscription record
- Full validation before creating checkout sessions: trial users can't top-up (TRIAL-07), already-subscribed users can't re-subscribe to same plan, clear error messages
- After successful checkout, redirect to Manage Plan page (`/settings/billing`)
- Phase 57 includes the checkout API endpoints: `POST /subscriptions/checkout` (subscription) and `POST /credits/purchase` (top-up) — Phase 58 frontend just calls them

### Event handler behavior
- `checkout.session.completed` (subscription): activates subscription, creates/updates Subscription record, sets user tier
- `checkout.session.completed` (top-up): adds purchased credits to `purchased_balance` immediately via CreditService
- `invoice.paid` (renewal): resets subscription credits to full tier allocation (unused credits from previous cycle are lost). Purchased credits untouched.
- `invoice.payment_failed`: marks subscription status as `past_due` in Subscription table AND sends email notification to user (leverage existing SMTP email handler)
- `customer.subscription.updated`: handles plan changes (upgrade/downgrade) — updates `plan_tier` and `status` in Subscription table
- `customer.subscription.deleted`: subscription credits remain usable until `current_period_end` date. On that date, subscription credits zero out. User transitions to On Demand tier. Purchased credits preserved indefinitely.
- All events deduplicated via `stripe_events` table before processing

### SubscriptionService shape
- Single `SubscriptionService` class handling all Stripe operations: customer creation, checkout sessions, and webhook event processing
- Single webhook router file with `POST /webhooks/stripe` — dispatches to handler methods on SubscriptionService based on event type
- Custom exception classes for Stripe errors (`StripeError`, `PaymentDeclinedError`, etc.) — router catches and returns appropriate HTTP status codes
- Consistent with existing codebase patterns (CreditService handles all credit ops, single-service-per-domain)

### Claude's Discretion
- Exact SubscriptionService method signatures and internal organization
- Stripe metadata fields passed in checkout sessions
- Webhook handler error logging and retry behavior details
- Stripe Customer creation flow details (email, name, metadata)
- How cancel-at-period-end is tracked and enforced for credit zeroing
- Test structure and fixtures for webhook testing
- Email template content for payment failure notification

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stripe & Subscription Requirements
- `.planning/REQUIREMENTS.md` — STRIPE-01 through STRIPE-10, SUB-06 (all Phase 57 requirements)

### Monetization Spec
- `requirements/monetization-requirement.md` — Tier classes, user experience flows for upgrade/cancel/top-up

### Phase 55 Context (prior decisions)
- `.planning/phases/55-tier-restructure-data-foundation/55-CONTEXT.md` — Dual-balance credit system, tier definitions, APScheduler skip logic, CreditService refactor decisions

### Phase 56 Context (prior decisions)
- `.planning/phases/56-trial-expiration-conversion-pressure/56-CONTEXT.md` — 402 trial enforcement, trial credit restrictions (TRIAL-07), exempt endpoints pattern

### Deployment Architecture
- `DEPLOYMENT.md` — Split-horizon architecture: backend not publicly accessible, all traffic through Next.js proxy, Dokploy service configuration

### Existing Billing Models
- `backend/app/models/subscription.py` — Subscription table (stripe_subscription_id, stripe_customer_id, plan_tier, status, billing period, cancel_at_period_end)
- `backend/app/models/stripe_event.py` — StripeEvent table for webhook idempotency
- `backend/app/models/payment_history.py` — PaymentHistory table (stripe_payment_intent_id, amount, type, credit_amount, status)
- `backend/app/models/credit_package.py` — CreditPackage table (credit_amount, price_cents, stripe_price_id, is_active)

### Credit Service
- `backend/app/services/credit.py` — CreditService with dual-balance deduction, refund, reset logic (SELECT FOR UPDATE locking)

### Email Service
- `backend/app/services/email.py` — Existing SMTP email handler for payment failure notifications

### Proxy Layer
- `frontend/src/app/api/[...slug]/route.ts` — Catch-all API proxy that forwards raw body as arrayBuffer (webhook path)

### Roadmap
- `.planning/ROADMAP.md` — Phase 57 success criteria, dependency chain to Phase 58-59

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CreditService` (`backend/app/services/credit.py`): Dual-balance deduction, refund, reset methods — webhook handlers call these for credit operations
- `Subscription` model (`backend/app/models/subscription.py`): Full schema ready with Stripe fields, status, billing period, cancel_at_period_end
- `StripeEvent` model (`backend/app/models/stripe_event.py`): Idempotency table ready — webhook checks this before processing
- `PaymentHistory` model (`backend/app/models/payment_history.py`): Transaction logging ready for checkout completions and renewals
- `CreditPackage` model (`backend/app/models/credit_package.py`): Has `stripe_price_id` field ready for Stripe Dashboard price linking
- Email service (`backend/app/services/email.py`): SMTP handler for payment failure notifications
- Catch-all proxy (`frontend/src/app/api/[...slug]/route.ts`): Already forwards raw body for webhook signature verification

### Established Patterns
- SQLAlchemy `SELECT FOR UPDATE` locking for atomic credit operations
- Platform settings service for configurable values (subscription price IDs can go here)
- FastAPI dependency injection for auth and DB sessions
- `NUMERIC(10, 1)` for balance fields
- Alembic migrations for all schema changes
- Router pattern: one file per domain in `backend/app/routers/`

### Integration Points
- `backend/app/routers/` — New webhook router and subscription router
- `backend/app/services/` — New SubscriptionService
- `backend/app/services/credit.py` — CreditService called by webhook handlers for credit reset and top-up
- `backend/app/services/user_class.py` — Tier config lookup for credit allocation amounts
- `backend/app/dependencies.py` — Auth dependencies for checkout endpoints
- Platform settings — Store Stripe Price IDs for subscription tiers

</code_context>

<specifics>
## Specific Ideas

- Owner emphasized: backend is not publicly accessible — Stripe webhook MUST go through Next.js proxy (per DEPLOYMENT.md architecture)
- Payment failure triggers both DB status flag AND email notification (not just status flag) — leverage existing SMTP handler
- Subscription cancellation is end-of-cycle: credits stay usable until `current_period_end`, then zero out. Example: "If renewal is Feb 22 and user unsubscribes Feb 15, credits work until Feb 22 cutoff"
- Stripe Dashboard is the source of truth for prices — no dynamic price creation via API
- Stripe Customer created lazily (on first checkout), not eagerly (on registration)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 57-stripe-backend-webhook-foundation*
*Context gathered: 2026-03-20*
