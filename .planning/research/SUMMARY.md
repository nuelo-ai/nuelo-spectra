# Project Research Summary

**Project:** Spectra — Monetization Milestone (Stripe Integration, Subscription Management, Billing UI, Admin Billing Tools)
**Domain:** SaaS monetization for credit-based AI analytics platform
**Researched:** 2026-03-18
**Confidence:** HIGH

## Executive Summary

Spectra monetization is a Stripe-around-existing-credit-engine integration, not a greenfield payment system build. The core insight from all four research tracks is that Spectra already has the hardest part built: atomic credit deduction, tier-based allocations, transaction logging, admin portal, and a split-horizon multi-mode architecture. What monetization adds is a payment collection layer (Stripe Checkout Sessions), a subscription lifecycle manager (webhooks + local DB mirror), and a billing UI (two new settings pages). The total new dependency footprint is exactly 3 packages: `stripe` Python SDK on the backend, plus `@stripe/stripe-js` and `@stripe/react-stripe-js` on the frontend. Zero new infrastructure.

The recommended approach is to build in dependency order, not feature order. Tier restructure must come first — it is a data migration that affects every other component. Then the credit model must be split into dual balance columns (subscription credits vs. purchased credits) before any Stripe code writes credit values. Only after those foundations are stable should Stripe Checkout Sessions, the webhook handler, and the billing UI be built. This ordering avoids the highest-cost recovery scenario: deploying a single-balance credit model that requires a complex data migration once payments are live.

The key risk is the webhook handler. Stripe retries on timeout and network failure, making idempotency non-optional. A `stripe_events` deduplication table must be part of the Stripe integration phase from the start, not an afterthought. The second risk is Stripe-local state drift: the local `subscriptions` table is a read cache; Stripe is the source of truth. The monthly credit reset must be driven by the `invoice.paid` webhook, not the existing APScheduler, to prevent double-resets. Both risks have clear mitigations and are avoidable with the phase ordering below.

---

## Key Findings

### Recommended Stack

Monetization adds exactly 3 new dependencies to the existing stack. The `stripe` Python SDK (`>=14.4.0`) handles all server-side Stripe operations — Checkout Sessions, subscription lifecycle, refunds, and webhook signature verification — in a single package. On the frontend, `@stripe/stripe-js` (`>=8.10.0`) is the Stripe.js loader and `@stripe/react-stripe-js` (`>=5.6.0`) provides the `EmbeddedCheckout` component. React 19 compatibility is confirmed (resolved in v3.1.0, Dec 2024, issue #540). The admin frontend requires no new dependencies; all admin billing actions are server-side FastAPI calls rendered with existing shadcn/ui components.

The recommended Checkout UX is Stripe Embedded Checkout (not redirect), because `redirectToCheckout` was deprecated in Stripe's 2025-09-30 Clover API changelog. Embedded Checkout keeps users on the Spectra domain, maintains PCI compliance (card data never touches Spectra servers), and falls back to a server-side redirect with a one-line backend change if iframe issues arise. The Stripe Customer Portal is explicitly rejected: Spectra needs custom billing pages to display credit balances, top-up packages, and tier-specific logic that the hosted portal cannot render.

**Core technologies:**
- `stripe>=14.4.0`: All server-side Stripe API calls — the only new backend dependency
- `@stripe/stripe-js>=8.10.0`: Stripe.js CDN loader — required by the React component
- `@stripe/react-stripe-js>=5.6.0`: Embedded Checkout React components — React 19 confirmed compatible
- All other stack components (FastAPI, SQLAlchemy, Alembic, APScheduler, SMTP, shadcn/ui, TanStack Query): existing, reused with targeted modifications

See `.planning/research/STACK-monetization.md` for full dependency rationale, version pinning notes, and what NOT to add.

### Expected Features

Monetization features follow a strict dependency chain: tier restructure unlocks subscription models, subscription models unlock Stripe integration, Stripe integration unlocks billing UI, billing UI unlocks admin tools. Building out of this order creates rework.

**Must have (table stakes — P1 for launch):**
- Tier restructure — eliminates ongoing `free` tier, adds `on_demand`, renames `standard` -> `basic`; foundation for all billing logic
- Trial expiration mechanism — `trial_expires_at` field + backend auth middleware check; without this, free trial never ends
- Subscription data model — `subscriptions`, `payment_history`, `credit_packages` tables via Alembic migrations
- Stripe webhook handler with idempotency — server-authoritative payment fulfillment; the central nervous system for all billing state
- Plan Selection page (`/settings/plan`) — three-tier card layout, triggers Stripe Checkout
- Stripe Checkout Sessions — subscription mode for plans, payment mode for top-ups
- Manage Plan page (`/settings/billing`) — current plan status, billing history, cancel action
- Cancel subscription flow — cancel at period end (not immediate) with confirmation dialog
- Credit top-up purchases — predefined packages (e.g., 50/200/500 credits), one-time Checkout Sessions
- Credit deduction priority — subscription credits consumed first (expire at cycle end), purchased credits second (never expire)
- Trial status banner — countdown display, escalating urgency (blue → amber → red)
- Admin billing visibility — subscription status and payment history in existing admin user detail page

**Should have (P2 — add when triggered by first real case):**
- Admin manual subscription override (with mandatory `expires_at` and reason)
- Admin cancel on behalf of user
- Admin refund capability (full/partial via Stripe Refund API + credit clawback)
- Admin billing event log
- Failed payment grace period (3 days, then downgrade to On Demand)
- Upgrade/downgrade proration (Stripe handles the math; expose mid-cycle change UI)

**Defer to v2+:**
- Annual billing (add as a Price variant in Stripe; no structural code change needed when the time comes)
- Coupon/promo codes (Stripe Coupons API exists; defer until marketing needs them)
- Multi-currency support (defer until non-US revenue warrants it)
- Stripe Tax (add in-place when legal/accounting requires it)

See `.planning/research/FEATURES-monetization.md` for the full feature dependency graph and prioritization matrix.

### Architecture Approach

The architecture wraps Stripe around the existing credit engine rather than replacing it. A new `SubscriptionService` becomes the central Stripe API orchestrator — all Checkout Session creation, subscription lifecycle management, and tier transition logic passes through it. A separate `StripeWebhookRouter` (at `/webhooks/stripe`) is explicitly excluded from JWT auth middleware and signature-verified instead. The existing `CreditService.deduct_credit()` is modified to implement dual-source deduction priority. The existing APScheduler credit reset is scoped to non-subscription tiers only; subscription credit resets are driven exclusively by `invoice.paid` webhooks to prevent double-resets.

Three Alembic migrations are required in sequence: (1) additive column changes to existing tables (`stripe_customer_id`, `trial_expires_at`, `purchased_balance`, `credit_source`), (2) three new tables (`subscriptions`, `payment_history`, `credit_packages`), and (3) a data migration for tier restructure plus backfilling `trial_expires_at` for existing trial users.

**Major components:**
1. `SubscriptionService` (NEW) — Stripe API calls, checkout session creation, subscription CRUD, tier transitions, credit source tracking
2. `StripeWebhookRouter` (NEW) — raw body signature verification, event dispatch to typed handlers, `stripe_events` idempotency table
3. `BillingRouter` (NEW) — `/billing/*` user-facing endpoints for plan selection, subscription management, top-ups, billing history
4. `CreditService` (MODIFIED) — dual-source deduction priority: subscription balance first, purchased balance second
5. `UserCredit` model (MODIFIED) — add `purchased_balance` column separate from subscription `balance`
6. Auth middleware (MODIFIED) — trial expiration check (`trial_expires_at < now()`) on every authenticated request
7. Plan Selection page `/settings/plan` (NEW) — tier cards with Stripe Embedded Checkout
8. Manage Plan page `/settings/billing` (NEW) — subscription details, top-up packages, billing history
9. Admin BillingRouter (NEW) — admin visibility, override, cancel, refund endpoints
10. Trial Banner / Upgrade Prompt (NEW) — global overlay components, appear on every page

See `.planning/research/ARCHITECTURE-MONETIZATION.md` for full data flows, file-level project structure, anti-patterns, and Alembic migration plan.

### Critical Pitfalls

1. **Non-idempotent webhook handler** — Stripe retries on failure; without deduplication, a slow DB write triggers duplicate credit grants. Prevention: create a `stripe_events` table with a unique constraint on `event_id`; check and insert at the start of every handler inside the same DB transaction. Must be built in from day one.

2. **Single-balance credit model** — Adding purchased credits to the existing `balance` column means the monthly subscription reset (`balance = tier_allocation`) silently wipes credits users paid for. Prevention: split `UserCredit` into `balance` (subscription, resets monthly) and `purchased_balance` (never resets) before any Stripe code writes credits. Recovery cost after the fact is high.

3. **Tier migration breaks existing users** — Removing `free` from `user_classes.yaml` without an Alembic data migration leaves every `free` tier user's `get_class_config("free")` returning `None`, breaking credit deduction and scheduler resets. Prevention: write the Alembic data migration first; keep old tier keys as aliases for one release cycle; test on a production data copy.

4. **Trial expiration only enforced in the frontend** — Users with open tabs and API key users bypass frontend route guards entirely. Prevention: enforce trial check in the FastAPI auth dependency (`Depends`), covering all paths (frontend, API v1, MCP server). Backend middleware, not scheduler, is the real-time enforcement mechanism.

5. **Client-controlled Stripe pricing** — Accepting `price_id` or `amount` from the frontend request body allows a malicious user to pay $0.01 for Premium. Prevention: the API accepts only a plan name (`"basic"` or `"premium"`); the backend resolves it to a Stripe Price ID from server-side config. The client never controls what gets charged.

See `.planning/research/PITFALLS-monetization.md` for the full pitfall list, security mistakes, UX pitfalls, recovery strategies, and the "Looks Done But Isn't" verification checklist.

---

## Implications for Roadmap

All four research files independently converge on the same build ordering. The dependency graph is unambiguous: tier restructure and credit model changes must precede Stripe integration, which must precede billing UI, which must precede admin tools.

### Phase 1: Tier Restructure and Trial Expiration

**Rationale:** No Stripe code should be written against the old tier structure. Tier restructure is a data migration, not a config change — deploying it first prevents the "free tier users locked out overnight" failure mode. Trial expiration belongs here because it has zero Stripe dependency and is a prerequisite for conversion pressure. This phase also includes the credit model dual-balance split because it must happen before any Stripe code writes credit values.
**Delivers:** Clean tier model (`free_trial`, `on_demand`, `basic`, `premium`, `internal`) in `user_classes.yaml`, Alembic migrations for column additions and data migration of existing `free`/`standard` users, `purchased_balance` column on `UserCredit`, `trial_expires_at` on `User`, trial expiration middleware check in FastAPI auth dependency, upgrade prompt UI as a static component (no payment flow yet).
**Addresses:** Tier restructure, existing user migration, credit model dual-balance, trial expiration mechanism, trial banner (static version).
**Avoids:** Pitfall 3 (tier migration breaks existing users), Pitfall 4 (trial only checked on frontend), and the high-cost recovery for single-balance credit model (Pitfall 2).

### Phase 2: Stripe Core and Webhook Foundation

**Rationale:** Backend-only phase. Establishes the payment infrastructure before any UI is built on top of it. Webhook idempotency and the `stripe_events` table must be locked in here — once `invoice.paid` events start firing in production, retroactively adding idempotency is risky.
**Delivers:** `stripe` SDK installed, `SubscriptionService`, `Subscription`/`PaymentHistory`/`CreditPackage` models (Alembic migration 2), webhook endpoint with signature verification and `stripe_events` deduplication, event handlers for `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated/deleted`, modified `CreditService.deduct_credit()` for source priority, APScheduler scoped to non-subscription tiers.
**Uses:** `stripe>=14.4.0`, FastAPI, SQLAlchemy, Alembic, existing `CreditService`.
**Avoids:** Pitfall 1 (non-idempotent webhooks), Pitfall 2 (Stripe-local state drift and double-reset), Pitfall 5 (client-controlled pricing), Pitfall 7 (Stripe secret keys in platform_settings).

### Phase 3: Billing UI

**Rationale:** Frontend billing pages depend on backend endpoints being functional and tested. Building UI second reduces the iteration loop — API contracts are stable before React components consume them. This is also where the Stripe Embedded Checkout components are introduced.
**Delivers:** `@stripe/stripe-js` and `@stripe/react-stripe-js` installed, Plan Selection page (`/settings/plan`) with tier cards and Stripe Embedded Checkout, Manage Plan page (`/settings/billing`) with subscription status + buy credits + billing history, cancel subscription flow with confirmation dialog, settings navigation update (new "Plan & Billing" tab), TanStack Query billing hooks.
**Implements:** Plan Selection page, Manage Plan page, Trial Banner (wired to live data), Upgrade Prompt overlay (wired to backend `TRIAL_EXPIRED` 403 response).
**Avoids:** UX pitfalls — trial banner non-dismissible in last 3 days, cancel confirmation shows access-until-date, credit balance display shows subscription and purchased credits separately.

### Phase 4: Admin Billing Tools

**Rationale:** Admin tools read and act on data created by all preceding phases. Building last means the data they operate on is already populated and tested. P2 features (override, refund) can be deferred to post-launch if timeline is tight; admin billing visibility (P1) is the minimum viable deliverable for this phase.
**Delivers:** Admin billing visibility (subscription status + payment history on user detail page), admin billing event log, manual subscription override (with `expires_at`, reason, and background revert task for expired overrides), cancel on behalf of user, refund capability (Stripe Refund API + credit clawback prompt).
**Avoids:** Pitfall 6 (admin override ghost state — override must have `expires_at`, a `subscription_overrides` table, and a resolver that checks overrides before Stripe subscription state).

### Phase Ordering Rationale

- Tier restructure must be first because it is a prerequisite that cannot be safely retrofitted after Stripe code runs against old tier names
- Credit model dual-balance must happen before the first Stripe event writes credits, otherwise purchased credits get wiped on the first subscription reset
- Stripe backend before billing UI so frontend components have stable API contracts to consume
- Admin tools last because they depend on data that all other phases produce; the override data model should be designed in Phase 2 even if the UI comes in Phase 4

### Research Flags

Phases that need extra attention during implementation planning:

- **Phase 1 (Tier Restructure):** The migration path for existing `free` tier users requires a product decision before the Alembic data migration can be written: migrate to `free_trial` with a 30-day grace period, or migrate directly to `on_demand`. This decision also determines whether a user communication email needs to go out before deploy. Must be resolved before Phase 1 task breakdown.
- **Phase 2 (Stripe Core + Webhooks):** High implementation complexity across several intersecting concerns — idempotency, out-of-order event handling, APScheduler/webhook dual-reset prevention, Stripe Dashboard pre-configuration (Products, Prices, webhook endpoint registration), and webhook URL routing (direct to FastAPI backend vs. through Next.js proxy). Recommend a detailed task-level breakdown before implementation begins.

Phases with standard patterns (can proceed without additional research):

- **Phase 3 (Billing UI):** Well-documented Stripe Embedded Checkout + Next.js patterns. `@stripe/react-stripe-js` component usage is straightforward once the backend Checkout Session endpoint is working. The existing settings page tab pattern is the model to follow.
- **Phase 4 (Admin Billing Tools):** Follows existing Spectra admin portal patterns exactly. No novel integration points; the override data model is the only architectural decision, and research provides the recommended schema.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All 3 new packages verified on PyPI and npm as of 2026-03-18. React 19 compatibility confirmed via GitHub issue #540 resolution. `redirectToCheckout` deprecation confirmed via Stripe changelog. Zero new infrastructure required. |
| Features | HIGH | Stripe documentation is comprehensive. Spectra codebase patterns are clear (credit system, admin portal, platform settings all directly inspected). Feature dependencies are deterministic from the codebase. |
| Architecture | HIGH | Integration patterns verified against official Stripe FastAPI examples and direct Spectra codebase analysis. Split-horizon router registration, proxy bypass for webhooks, and APScheduler scoping all confirmed against actual code paths. |
| Pitfalls | HIGH | All 7 critical pitfalls grounded in either Stripe's own documentation, community post-mortems (Stigg, Hookdeck, Stripe.dev reconciliation series), or direct analysis of the Spectra codebase (e.g., single-balance field confirmed in `user_credits`, `user_classes.yaml` tier names confirmed). No speculative pitfalls. |

**Overall confidence:** HIGH

### Gaps to Address

- **Existing `free` tier user migration path:** Research identifies the migration is required but the product decision (grace period vs. immediate On Demand) needs owner input before the Alembic migration script can be written. This is a pre-Phase-1 decision.
- **Stripe Dashboard pre-configuration:** Products, Prices, and webhook endpoint registration in the Stripe Dashboard must happen before Phase 2 can be tested. This is a manual prerequisite that should appear as a setup task before Phase 2 begins.
- **`stripe_events` dedup table schema:** Research recommends the table but does not specify whether to include `processed_at`, `event_type`, `user_id`, and retention policy. Should be specified during Phase 2 task breakdown.
- **Webhook URL routing (direct vs. proxied):** Research recommends pointing Stripe directly at the FastAPI backend origin rather than routing through the Next.js proxy. Whether this is possible depends on the Dokploy routing config. Verify during Phase 2 environment setup before registering the webhook endpoint in Stripe Dashboard.

---

## Sources

### Primary (HIGH confidence — official docs and codebase)
- [Stripe Build Subscriptions with Checkout](https://docs.stripe.com/payments/checkout/build-subscriptions)
- [Stripe Webhook Signature Verification](https://docs.stripe.com/webhooks/signature)
- [Stripe Receive Webhook Events](https://docs.stripe.com/webhooks)
- [Stripe Checkout Sessions API](https://docs.stripe.com/payments/quickstart-checkout-sessions)
- [Stripe Idempotent Requests](https://docs.stripe.com/api/idempotent_requests)
- [Stripe Database Reconciliation Series (Parts 1-3)](https://stripe.dev/blog/database-reconciliation-growing-businesses-part-1)
- [redirectToCheckout deprecated — Stripe Clover changelog 2025-09-30](https://docs.stripe.com/changelog/clover/2025-09-30/remove-redirect-to-checkout)
- [stripe PyPI v14.4.1](https://pypi.org/project/stripe/) — verified 2026-03-18
- [@stripe/stripe-js npm v8.10.0](https://www.npmjs.com/package/@stripe/stripe-js) — verified 2026-03-18
- [@stripe/react-stripe-js npm v5.6.1](https://www.npmjs.com/package/@stripe/react-stripe-js) — verified 2026-03-18
- [React 19 support — issue #540 resolved (Dec 2024)](https://github.com/stripe/react-stripe-js/issues/540)
- Spectra codebase: `backend/app/services/credit.py`, `backend/app/models/user_credit.py`, `backend/app/models/user.py`, `backend/app/config/user_classes.yaml`, `backend/app/services/platform_settings.py`, `frontend/src/app/api/[...slug]/route.ts`
- Spectra requirements: `requirements/monetization-requirement.md`, `requirements/monetization-milestone-plan.md`

### Secondary (MEDIUM confidence — community patterns)
- [FastAPI + Stripe Integration (fast-saas.com)](https://www.fast-saas.com/blog/fastapi-stripe-integration/)
- [Stripe Webhook Best Practices (Stigg)](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks)
- [Stripe Webhooks Guide (Hookdeck)](https://hookdeck.com/webhooks/platforms/guide-to-stripe-webhooks-features-and-best-practices)
- [Stripe + Next.js 2026 Guide (dev.to)](https://dev.to/sameer_saleem/the-ultimate-guide-to-stripe-nextjs-2026-edition-2f33)
- [Stripe Subscription Lifecycle in Next.js 2026 (dev.to)](https://dev.to/thekarlesi/stripe-subscription-lifecycle-in-nextjs-the-complete-developer-guide-2026-4l9d)
- [Building a Payment Backend with FastAPI, Stripe, and Webhooks (Medium)](https://medium.com/@abdulikram/building-a-payment-backend-with-fastapi-stripe-checkout-and-webhooks-08dc15a32010)
- [Webhook Idempotency Patterns (Medium)](https://medium.com/@sohail_saifii/handling-payment-webhooks-reliably-idempotency-retries-validation-69b762720bf5)
- [SaaS Free Trial Conversion Best Practices (UserPilot)](https://userpilot.com/blog/saas-free-trial-best-practices/)
- [How to Implement Credit System in Subscription Model (FlexPrice)](https://flexprice.io/blog/how-to-implement-credit-system-in-subscription-model)
- [Managing Subscription Changes in Stripe (Moldstud)](https://moldstud.com/articles/p-how-to-effectively-manage-subscription-changes-in-stripe-and-avoid-common-pitfalls)

---
*Research completed: 2026-03-18*
*Milestone: Monetization*
*Ready for roadmap: yes*
