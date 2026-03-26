# Technology Stack: Monetization

**Project:** Spectra -- Stripe Integration, Subscription Management, Billing UI, Admin Billing Tools
**Researched:** 2026-03-18
**Confidence:** HIGH (all libraries verified via PyPI, npm, and official Stripe documentation)

## Overview

Monetization adds Stripe payment processing to the existing Spectra stack. The change footprint is deliberately small: one new backend dependency (`stripe` Python SDK), two new frontend dependencies (`@stripe/stripe-js` and `@stripe/react-stripe-js`), zero new infrastructure. Everything else -- database schema, API routes, credit system changes, billing UI -- builds on existing patterns with existing libraries.

---

## What Changes (and What Does Not)

### Does NOT Change

- FastAPI backend framework
- PostgreSQL + SQLAlchemy ORM + Alembic migrations
- JWT authentication flow
- LangGraph agent orchestration / E2B sandbox
- APScheduler (existing, reused for trial expiration emails)
- SMTP email service (existing, reused for billing notifications)
- Admin frontend framework (Next.js 16 + React 19 + shadcn/ui)
- Docker + Dokploy deployment infrastructure
- Platform settings pattern (30s TTL cache, admin-configurable)
- SPECTRA_MODE split-horizon architecture

### Changes Required

| Layer | What Changes | Why |
|-------|-------------|-----|
| Backend: New dependency | `stripe` Python SDK | Stripe API calls (Checkout Sessions, Subscriptions, Webhooks, Refunds) |
| Backend: New models | `subscriptions`, `payment_history`, `credit_packages` tables | Track subscription state, billing records, top-up packages |
| Backend: Schema changes | `users` table + `stripe_customer_id`, `trial_expires_at` | Link users to Stripe, track trial expiration |
| Backend: Schema changes | `user_credits` table + `purchased_credits` column | Dual-source credit tracking (subscription vs purchased) |
| Backend: New routers | `routers/billing.py`, `routers/webhooks.py` | Billing API endpoints + Stripe webhook receiver |
| Backend: Service changes | `CreditService` deduction priority logic | Subscription credits consumed first, purchased credits second |
| Backend: Middleware | Trial expiration check on authenticated requests | Block expired trial users, force plan selection |
| Backend: Admin router | Extend admin with billing visibility + customer service tools | Override, cancel, refund, billing event log |
| Frontend: New dependencies | `@stripe/stripe-js`, `@stripe/react-stripe-js` | Embedded Checkout UI components |
| Frontend: New pages | `/settings/plan`, `/settings/billing` | Plan selection, billing management |
| Frontend: New components | Trial banner, upgrade prompt, credit purchase section | Monetization UX |
| Admin frontend: New views | User billing detail, payment history, refund/override controls | Customer service tooling |

---

## Recommended Stack Additions

### Backend: New Python Dependency (1 package)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `stripe` | `>=14.4.0` | Stripe API integration | Official Stripe Python SDK. v14.4.1 is current (released 2026-03-06). Supports Python 3.7-3.12. Handles Checkout Sessions, Subscriptions, Invoices, Refunds, Webhook signature verification -- all in one package. Async-compatible for FastAPI. |

**That is the only new backend dependency.** The `stripe` SDK includes everything:
- `stripe.checkout.Session.create()` -- create Checkout Sessions
- `stripe.Subscription.modify()` / `.delete()` -- subscription lifecycle
- `stripe.Refund.create()` -- refund processing
- `stripe.Webhook.construct_event()` -- webhook signature verification
- Customer creation, invoice retrieval, payment intent lookup

No separate webhook library, no payment processing library, no subscription management library. One package.

### Frontend (Public): New npm Dependencies (2 packages)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@stripe/stripe-js` | `>=8.10.0` | Stripe.js loader | Securely loads Stripe.js from Stripe's CDN. Required by `@stripe/react-stripe-js`. Thin wrapper, no framework dependency. v8.10.0 is current. |
| `@stripe/react-stripe-js` | `>=5.6.0` | React components for Embedded Checkout | Provides `EmbeddedCheckoutProvider` and `EmbeddedCheckout` components. React 19 supported since v3.1.0 (Dec 2024, issue #540 resolved). v5.6.1 is current. |

### Admin Frontend: New Dependencies

**NONE.** All admin billing features (subscription override, cancel on behalf, refund, billing event log) are standard data display and API mutations. Uses existing shadcn/ui components (Table, Card, Dialog, Badge, Button) and TanStack Query hooks calling FastAPI endpoints. No Stripe client-side SDK needed in admin -- all Stripe operations are server-side through FastAPI.

### Infrastructure: No Changes

**NONE.** Stripe is a hosted service -- no new containers, no Redis, no message queues. The webhook endpoint is a standard FastAPI route. Existing APScheduler handles any periodic jobs (trial warning emails). Existing SMTP infrastructure handles billing email notifications.

---

## Architecture Decision: Embedded Checkout

**Decision:** Use Stripe Embedded Checkout, not Stripe-hosted redirect.

**Why:**
1. **`redirectToCheckout` is deprecated.** Stripe removed support in the 2025-09-30 Clover API changelog. Server-side redirect via `session.url` still works, but Embedded is the recommended path.
2. **Better UX.** Users stay on the Spectra domain. No jarring redirect to stripe.com and back. Consistent with Spectra's single-page app behavior.
3. **Same PCI compliance.** The Embedded Checkout iframe is fully Stripe-hosted. No card data touches Spectra servers.
4. **Compatible with Spectra's architecture.** FastAPI creates Checkout Session with `ui_mode='embedded'`, returns `client_secret`. Frontend renders `EmbeddedCheckout` component with that secret.

**Data flow:**

```
Frontend                         FastAPI Backend              Stripe
   |                                   |                        |
   |-- POST /api/billing/subscribe --->|                        |
   |                                   |-- checkout.Session ---->|
   |                                   |    .create(             |
   |                                   |      ui_mode='embedded' |
   |                                   |      mode='subscription'|
   |                                   |    )                    |
   |                                   |<-- { client_secret } ---|
   |<--- { client_secret } ------------|                        |
   |                                   |                        |
   | [Renders EmbeddedCheckout         |                        |
   |  with client_secret in iframe]    |                        |
   |                                   |                        |
   | User completes payment            |                        |
   |                                   |<-- webhook: ------------|
   |                                   |    checkout.session     |
   |                                   |    .completed           |
   |                                   |                        |
   | [Frontend polls /api/billing/     |                        |
   |  manage or uses return_url]       |                        |
   |                                   |                        |
   |<-- redirect to /settings/billing  |                        |
```

**Fallback:** If Embedded Checkout causes layout/iframe issues, switching to server-side redirect (`session.url` instead of `client_secret`) is a one-line backend change. The frontend would use `window.location.href = session.url` instead of rendering `EmbeddedCheckout`. No dependency changes needed.

---

## What NOT to Add

| Temptation | Why Not | Use Instead |
|------------|---------|-------------|
| `stripe-agent-toolkit` | AI toolkit for Stripe operations. Spectra needs standard payment APIs, not AI-driven billing. | `stripe` SDK directly |
| `stripe` (Node.js / `npm install stripe`) | All Stripe server operations go through FastAPI. Frontend only needs client-side `@stripe/stripe-js`. | `stripe` Python SDK on backend |
| Redis / Celery / background task queue | Webhook processing is lightweight (update DB, allocate credits, send email). Process synchronously in the request handler. | Direct processing in webhook handler |
| Separate billing microservice | Spectra is a monolith. Adding billing routes to existing FastAPI app is simpler and maintains transactional consistency with the credit system. | New router in existing app |
| `python-money` / currency libraries | Stripe handles all amounts in cents (integers). No currency conversion needed -- USD only per requirements. | Store amounts as `int` (cents) |
| Stripe Customer Portal (`billing_portal`) | Spectra needs custom billing UI that shows credit balances, tier info, top-up packages. Stripe's portal cannot display Spectra-specific data. | Custom `/settings/billing` page |
| Separate email service for billing | Spectra already has aiosmtplib + Jinja2 templates. Stripe sends receipt emails automatically. | Existing SMTP + Stripe built-in receipts |
| `@stripe/react-stripe-js` in admin-frontend | Admin billing tools are API calls to FastAPI, not direct Stripe interactions. | shadcn/ui + TanStack Query |

---

## Integration Points with Existing Stack

### 1. Database (PostgreSQL + SQLAlchemy + Alembic)

**3 new tables** via Alembic migration:

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `subscriptions` | user_id, stripe_subscription_id, stripe_customer_id, plan_tier, status, current_period_start, current_period_end, cancel_at_period_end | Mirror of Stripe subscription state |
| `payment_history` | user_id, stripe_payment_intent_id, amount_cents, currency, type (subscription/top_up), credit_amount, status | Billing history for UI display |
| `credit_packages` | name, credit_amount, price_cents, stripe_price_id, is_active | Predefined top-up packages (admin-configurable) |

**Schema changes to existing tables:**

| Table | Change | Why |
|-------|--------|-----|
| `users` | Add `stripe_customer_id` (nullable varchar) | Link user to Stripe Customer object |
| `users` | Add `trial_expires_at` (nullable timestamp) | Track when free trial ends (set to registration + 14 days) |
| `user_credits` | Add `purchased_credits` (integer, default 0) | Separate purchased credits from subscription credits for deduction priority |

### 2. Credit System (Existing CreditService)

Current state: single `credits_remaining` field with atomic deduction (`SELECT FOR UPDATE`).

Required change: dual-source deduction.
- `credits_remaining` = subscription credits (reset monthly, expire at cycle end)
- `purchased_credits` = top-up credits (never expire, never reset)
- **Deduction order:** subscription credits first (they expire anyway), purchased credits second (preserve user value)
- The atomic deduction pattern (`SELECT FOR UPDATE`) stays the same -- just applied across two columns

This is a service-layer change, not a new dependency.

### 3. APScheduler (Existing)

No new scheduled jobs required. Trial expiration is handled by auth middleware (check `trial_expires_at` on every authenticated request). Middleware is more reliable than a scheduler -- no race conditions with timing.

**Optional:** Add a scheduled job for sending "trial expiring soon" warning emails (e.g., at 3 days remaining). This uses existing APScheduler + SMTP infrastructure.

### 4. Platform Settings (Existing)

Add new runtime-configurable settings using the existing platform_settings pattern (30s TTL cache):

| Setting | Type | Purpose |
|---------|------|---------|
| `trial_duration_days` | int | Free trial length (default: 14) |
| `credit_price_per_unit` | float | Price per credit for top-ups |
| `subscription_price_basic` | int (cents) | Monthly price for Basic tier |
| `subscription_price_premium` | int (cents) | Monthly price for Premium tier |
| `subscription_credits_basic` | int | Monthly credit allocation for Basic |
| `subscription_credits_premium` | int | Monthly credit allocation for Premium |

Note: `stripe_webhook_secret` should be in .env (not platform_settings) because it is needed at app startup for webhook verification and should not be runtime-mutable.

### 5. Tier Configuration (user_classes.yaml)

Existing tiers need restructuring:
- Drop `free` tier (10 credits/week ongoing -- eliminated per requirements)
- Keep `free_trial` as temporary state (100 credits, 14 days)
- Rename `standard` to `basic`
- Add `on_demand` tier (0 base credits, top-up only)
- Keep `premium` and `internal` unchanged

This is a YAML configuration change + Alembic data migration for existing users.

### 6. Frontend API Layer (TanStack Query)

New TanStack Query hooks for billing endpoints:

| Hook | Endpoint | Type |
|------|----------|------|
| `useBillingPlans()` | `GET /api/billing/plans` | Query |
| `useSubscriptionStatus()` | `GET /api/billing/manage` | Query |
| `useBillingHistory()` | `GET /api/billing/manage` | Query (same endpoint, different data) |
| `useCreditPackages()` | `GET /api/billing/packages` | Query |
| `useCreateCheckoutSession()` | `POST /api/billing/subscribe` | Mutation |
| `useCreateTopUpSession()` | `POST /api/billing/top-up` | Mutation |
| `useCancelSubscription()` | `POST /api/billing/cancel` | Mutation |
| `useChangePlan()` | `POST /api/billing/change-plan` | Mutation |

No new Zustand stores needed. Billing data is server-authoritative -- TanStack Query's cache is sufficient.

### 7. UI Components (shadcn/ui)

All billing UI uses existing shadcn/ui components:
- **Card** -- plan selection cards, billing summary
- **Badge** -- plan status, trial/active/cancelled indicators
- **Button** -- subscribe, cancel, purchase actions
- **Table** -- billing history
- **Dialog** -- cancel confirmation, refund confirmation
- **Alert** -- trial expiration warnings
- **Tabs** -- settings navigation (add "Plan & Billing" tab)

No new UI component libraries needed.

---

## Environment Variables -- New

| Variable | Location | Purpose |
|----------|----------|---------|
| `STRIPE_SECRET_KEY` | Backend .env | Stripe API authentication. Server-side only, never exposed to frontend. Starts with `sk_test_` (test) or `sk_live_` (production). |
| `STRIPE_PUBLISHABLE_KEY` | Frontend .env.local | Stripe.js initialization. Safe to expose -- it is a publishable key. Starts with `pk_test_` or `pk_live_`. Set as `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` for Next.js client-side access. |
| `STRIPE_WEBHOOK_SECRET` | Backend .env | Webhook signature verification. Starts with `whsec_`. Required for `stripe.Webhook.construct_event()`. |

---

## Stripe Dashboard Pre-Configuration

Before coding begins, the Stripe dashboard requires setup:

1. **Products:** Create "Basic Plan" and "Premium Plan" products
2. **Prices:** Create monthly recurring prices for each product (these return `price_id` values needed in code)
3. **Credit packages:** Create one-time prices for each top-up package (50, 200, 500 credits)
4. **Webhook endpoint:** Register `https://<domain>/api/webhooks/stripe`
5. **Webhook events:** Select: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`
6. **Test mode:** All development uses Stripe test mode (test API keys, test card numbers)

---

## Installation

```bash
# Backend -- add to pyproject.toml dependencies:
#   "stripe>=14.4.0",
cd backend && uv add stripe

# Frontend -- install Stripe client packages:
cd frontend && npm install @stripe/stripe-js @stripe/react-stripe-js

# Admin frontend -- no changes
```

---

## Version Pinning Rationale

| Package | Pin | Why |
|---------|-----|-----|
| `stripe` (Python) | `>=14.4.0` (floor only) | Stripe SDK follows semver. Minor/patch updates add API features. The Stripe API version is pinned per-request (not per-SDK-version), so SDK updates are safe. |
| `@stripe/stripe-js` | `>=8.10.0` (floor only) | Thin loader. Updates add Stripe.js features. No breaking changes within major. |
| `@stripe/react-stripe-js` | `>=5.6.0` (floor only) | v5.x supports React 19. Updates add component features. |

---

## Recommended Stack Summary

| Technology | Version | New? | Where | Purpose |
|------------|---------|------|-------|---------|
| `stripe` | `>=14.4.0` | **YES** | Backend | Stripe API (payments, subscriptions, webhooks, refunds) |
| `@stripe/stripe-js` | `>=8.10.0` | **YES** | Frontend | Stripe.js loader for Embedded Checkout |
| `@stripe/react-stripe-js` | `>=5.6.0` | **YES** | Frontend | React Embedded Checkout components |
| `fastapi[standard]` | `>=0.115` | No (existing) | Backend | New billing + webhook routes |
| `sqlalchemy[asyncio]` | `>=2.0` | No (existing) | Backend | New tables + schema changes |
| `alembic` | `>=1.13` | No (existing) | Backend | DB migrations |
| `apscheduler` | `>=3.11,<4.0` | No (existing) | Backend | Trial warning email jobs |
| `aiosmtplib` + `jinja2` | existing | No (existing) | Backend | Billing notification emails |
| `pydantic-settings` | `>=2.0` | No (existing) | Backend | New env vars |

**Total new dependencies: 3** (1 backend, 2 frontend). Zero new infrastructure.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Payment gateway | Stripe | Paddle, LemonSqueezy | Stripe is the industry standard for SaaS. Best API, best docs, best Python SDK. Paddle/LemonSqueezy are merchant-of-record (handle tax) but less flexible for custom credit systems. |
| Checkout UX | Embedded Checkout | Stripe-hosted redirect | `redirectToCheckout` deprecated. Embedded keeps users on-site. Same PCI compliance. |
| Checkout UX | Embedded Checkout | Custom payment form (Stripe Elements) | Elements requires handling card input, validation, error states, 3D Secure. Embedded Checkout handles all of this automatically. Only use Elements if you need a fully custom payment UI. |
| Subscription management | Custom Manage Plan page | Stripe Customer Portal | Portal cannot show Spectra credit balances, tier info, or top-up packages. Custom page integrates with Spectra's credit system. |
| Webhook processing | Synchronous in handler | Background queue (Celery/Redis) | Webhook handlers do lightweight DB updates. No long-running tasks. Synchronous processing with quick 200 response is sufficient. |
| Credit tracking | Dual-column (subscription + purchased) | Separate credit_transactions ledger table | Ledger table is more audit-friendly but adds query complexity. Dual-column is simpler and sufficient for deduction priority. Can add ledger later if needed. |
| Trial expiration | Auth middleware check | APScheduler periodic job | Middleware catches every request in real-time. Scheduler has timing gaps (user could use the app between scheduler runs). Use middleware as primary, scheduler for warning emails only. |

---

## Sources

- [stripe PyPI -- v14.4.1](https://pypi.org/project/stripe/) -- verified 2026-03-18
- [@stripe/stripe-js npm -- v8.10.0](https://www.npmjs.com/package/@stripe/stripe-js) -- verified 2026-03-18
- [@stripe/react-stripe-js npm -- v5.6.1](https://www.npmjs.com/package/@stripe/react-stripe-js) -- verified 2026-03-18
- [React 19 support -- issue #540 resolved](https://github.com/stripe/react-stripe-js/issues/540) -- React 19 peer dep added v3.1.0 (Dec 2024)
- [redirectToCheckout deprecated](https://docs.stripe.com/changelog/clover/2025-09-30/remove-redirect-to-checkout) -- Stripe Clover changelog
- [Build subscriptions with Checkout](https://docs.stripe.com/payments/checkout/build-subscriptions) -- official Stripe docs
- [Stripe webhook signature verification](https://docs.stripe.com/webhooks/signature) -- official docs
- [FastAPI + Stripe integration](https://www.fast-saas.com/blog/fastapi-stripe-integration/) -- community patterns
- [Stripe + Next.js 2026 guide](https://dev.to/sameer_saleem/the-ultimate-guide-to-stripe-nextjs-2026-edition-2f33) -- Embedded Checkout patterns
- [Stripe subscription lifecycle in Next.js 2026](https://dev.to/thekarlesi/stripe-subscription-lifecycle-in-nextjs-the-complete-developer-guide-2026-4l9d) -- webhook event handling

---

*Stack research for: Spectra Monetization*
*Researched: 2026-03-18*
*Confidence: HIGH -- 3 new dependencies total (stripe Python SDK, @stripe/stripe-js, @stripe/react-stripe-js). All versions verified. Zero new infrastructure. Embedded Checkout is Stripe's current recommended approach. All other changes use existing libraries and patterns.*
