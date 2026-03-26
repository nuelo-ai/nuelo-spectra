# Feature Research: Monetization (Stripe + Billing + Credits)

**Domain:** SaaS monetization for AI data analytics platform
**Researched:** 2026-03-18
**Confidence:** HIGH (well-documented domain, Stripe has extensive official docs, existing codebase patterns are clear)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any SaaS with paid plans. Missing these = product feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Plan Selection page** | Users need to see options, compare, and choose | MEDIUM | 3-tier card layout (On Demand / Basic / Premium). Depends on: tier restructure complete, Stripe Products/Prices configured. Existing pattern: Settings page already has tabs -- add "Plan & Billing" tab |
| **Stripe Checkout for subscriptions** | Industry-standard secure payment. Users trust Stripe's hosted/embedded UI | MEDIUM | Use Checkout Sessions API (not custom payment forms). Supports subscriptions + one-time payments. Backend creates session, frontend redirects. Depends on: Stripe account setup, Products/Prices in Stripe dashboard |
| **Webhook handler for payment events** | Payment confirmation must be server-authoritative, not client-side | HIGH | Must handle: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`. Requires idempotency (track processed event IDs). Must verify webhook signatures. Return 200 immediately, process async. Depends on: Subscription + PaymentHistory data models |
| **Manage Plan page (billing dashboard)** | Users need to see their plan status, next billing date, credits | MEDIUM | Shows: current plan, status, next billing date, credit allocation vs remaining, purchased credits. Actions: Change Plan, Cancel Subscription. Depends on: Subscription model, billing API endpoints |
| **Cancel subscription flow** | Users must be able to cancel without contacting support | LOW | Cancel at end of billing cycle (not immediate). Confirmation dialog with clear date. Stripe handles the scheduling. Depends on: Subscription model, webhook for `customer.subscription.deleted` |
| **Billing history** | Users expect receipts and payment records | LOW | Table of past payments: date, description, amount. Sourced from PaymentHistory table (populated by webhooks). Stripe also sends email receipts automatically |
| **Trial expiration with blocking** | Free trial must actually end -- otherwise no conversion pressure | MEDIUM | `trial_expires_at` field (registration + 14 days). Check on auth middleware OR background scheduler. Full-screen blocking overlay when expired. Depends on: User model change, frontend overlay component. Currently missing entirely from codebase |
| **Trial status banner** | Users must know trial is ticking | LOW | Persistent banner: "X days remaining, Y credits left". Amber at 3 days / 10 credits. Becomes blocking overlay at expiration. Depends on: trial_expires_at field, balance API already exists |
| **Credit top-up purchases** | Pay-as-you-go is table stakes for usage-based SaaS | MEDIUM | Predefined packages (e.g., 50/200/500 credits). Stripe Checkout Session in `payment` mode (one-time). Webhook adds credits on success. Depends on: CreditPackage model, modified CreditService. Free Trial users NOT eligible |
| **Credit deduction priority** | Users expect purchased credits to be preserved (they paid real money) | MEDIUM | Deduct subscription credits first (they expire at cycle end), purchased credits second (they persist). Requires splitting UserCredit.balance into two tracked pools OR adding a `purchased_credits` field. Depends on: UserCredit model change, CreditService modification |
| **Tier restructure** | New tier model must work before any billing features | HIGH | Drop `free` tier entirely. Keep `free_trial` as temporary state (14-day). Rename `standard` to `basic`. Add `on_demand` (0 base credits, top-up only). Existing user migration needed. Depends on: user_classes.yaml update, migration script for existing users, all tier-checking code audit |
| **Subscription data model** | Backend must track subscription state | MEDIUM | New Subscription table: user_id, stripe_subscription_id, stripe_customer_id, plan_tier, status, current_period_start/end, cancel_at_period_end. New PaymentHistory table. New CreditPackage table. Alembic migrations |
| **Admin: billing visibility** | Admins need to see user subscription status and payment history | LOW | Add subscription info to existing user detail page in admin portal. Show payment history per user. Depends on: Subscription + PaymentHistory models, admin API endpoints |

### Differentiators (Competitive Advantage)

Features that set Spectra apart. Not required for launch but add value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Upgrade/downgrade with proration** | Smooth mid-cycle plan changes without manual calculation | MEDIUM | Stripe handles proration by default. Basic to Premium: immediate allocation bump, prorated charge. Premium to Basic: takes effect at cycle end. Reduces churn from "locked in" feeling |
| **Admin: manual subscription override** | Customer service tool for billing disputes and courtesy credits | MEDIUM | Admin force-sets tier regardless of Stripe state (e.g., grant Premium for X days). Must log reason + admin who applied. Override flag on Subscription model. Depends on: Subscription model, admin API |
| **Admin: cancel on behalf of user** | Support can resolve stuck subscriptions | LOW | Same as user-cancel but triggered from admin portal. Logs admin action. Depends on: existing admin user management patterns |
| **Admin: refund capability** | Handle billing disputes without Stripe dashboard | HIGH | Full or partial refund via Stripe Refund API. Optionally deducts credits granted by refunded payment. Must log in PaymentHistory. Complex edge cases: partial refunds, refund + credit clawback timing |
| **Admin: billing event log** | Full audit trail for customer support | LOW | Stripe event history per user from PaymentHistory + webhook events. Already have CreditTransaction audit trail -- extend pattern to billing events |
| **Failed payment grace period** | Retain users through temporary payment issues | LOW | 3-day grace period on failed invoice. Stripe retries automatically (Smart Retries). After grace: downgrade to On Demand, preserve purchased credits. Notify user via email |
| **Early upgrade from trial** | Let users convert before trial ends | LOW | "Upgrade" button available during trial (not just after expiration). Trial credits forfeited on upgrade -- subscription allocation begins immediately. Better UX than waiting for block |
| **Low credit "Buy Credits" nudge** | Revenue capture at moment of need | LOW | When header credit pill shows low balance, add "Buy Credits" quick link. Contextual upsell without being pushy. Depends on: existing `is_low` flag in CreditBalanceResponse |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems for Spectra's current stage and scale.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Custom credit amounts** | "Let users buy any number of credits" | Complicates pricing, Stripe product management, and fraud surface. Users who buy 1 credit at a time create payment processing overhead | Offer 3-4 predefined packages only. Covers 90% of use cases. Simpler Stripe setup (fixed Price objects) |
| **Annual billing** | Lower churn, higher LTV | Adds complexity to proration, refund logic, and cancellation flows. Premature for a product still finding pricing | Defer to post-launch. Add as a Price variant in Stripe later (same Product, different interval). No code changes needed if architecture is clean |
| **Multi-currency support** | "International users want local currency" | Stripe Tax complexity, currency conversion edge cases, accounting nightmares | USD only for launch. Stripe handles international cards in USD. Add multi-currency only when non-US revenue exceeds 20% |
| **Stripe Customer Portal** | "Let Stripe handle billing management entirely" | Loses control over UX, cannot enforce credit-specific logic (top-ups, deduction priority), branding disconnect. Spectra needs custom Manage Plan page for credit display | Build custom billing pages. Use Stripe only for payment collection (Checkout Sessions) and event processing (webhooks) |
| **Coupon/promo codes at launch** | Growth lever, marketing tool | Adds discount logic to every billing flow. Testing matrix explodes. Premature optimization before product-market fit | Defer. Stripe Coupons API exists and is easy to add later. Admin can manually adjust credits as workaround |
| **Freemium tier (ongoing free access)** | "Keep free users in funnel" | Spectra's current `free` tier (10 credits/week forever) has zero conversion pressure. Users never upgrade. AI compute costs money -- free tiers bleed margin | Eliminate ongoing free. 14-day trial forces decision. On Demand tier (pay-per-use, no subscription) serves cost-conscious users without ongoing subsidy |
| **Real-time subscription status sync** | "Show instant status after payment" | Webhooks are async (seconds to minutes delay). Polling Stripe API on every page load is rate-limit hostile | Redirect to success page after Checkout, show "Processing..." state. Webhook updates within seconds. Polling fallback only if webhook delayed > 30s |
| **Tax handling at launch** | Legal compliance concern | Stripe Tax is a separate product with its own complexity. Most early-stage SaaS products defer tax | Defer. Stripe Tax can be enabled later with minimal code changes. State clearly in ToS that prices are pre-tax |

## Feature Dependencies

```
[Tier Restructure]
    |
    +--requires--> [user_classes.yaml update]
    +--requires--> [Existing user migration script]
    +--requires--> [Tier-checking code audit]
    |
    v
[Subscription Data Model]
    |
    +--requires--> [Alembic migrations: Subscription, PaymentHistory, CreditPackage tables]
    +--requires--> [trial_expires_at field on User]
    |
    v
[Stripe Webhook Handler] --requires--> [Subscription Data Model]
    |                                    [Idempotency tracking (processed_event_ids)]
    |
    +------+--------+--------+
    |      |        |        |
    v      v        v        v
[Plan     [Manage  [Credit  [Trial
Selection  Plan     Top-Up   Expiration
Page]      Page]    Flow]    Mechanism]
    |        |        |         |
    +--------+--------+---------+
    |
    v
[Credit Deduction Priority] --requires--> [UserCredit model change (split pools)]
    |                                      [CreditService modification]
    |
    v
[Admin Billing Tools]
    +-- [Billing visibility] --requires--> [Subscription + PaymentHistory queries]
    +-- [Manual override] --requires--> [Override flag on Subscription]
    +-- [Cancel on behalf] --requires--> [Stripe cancel API integration]
    +-- [Refund capability] --requires--> [Stripe Refund API + credit clawback logic]
    +-- [Billing event log] --requires--> [PaymentHistory populated by webhooks]
```

### Dependency Notes

- **Tier Restructure is the foundation:** Everything else depends on the new tier model being in place. Cannot build subscription flows against the old free/standard/premium structure.
- **Subscription Data Model before any Stripe integration:** Webhook handler needs tables to write to. Billing pages need tables to read from.
- **Webhook Handler is the central nervous system:** Plan selection, manage plan, top-ups, and trial expiration all depend on webhooks processing Stripe events correctly.
- **Credit Deduction Priority depends on model change:** Current UserCredit has a single `balance` field. Need to track subscription vs purchased credits separately.
- **Admin tools come last:** They read/act on data created by all other features. Building them first would have nothing to display.

## MVP Definition

### Launch With (v1 Monetization)

Minimum viable monetization -- what is needed to start charging users.

- [ ] **Tier restructure** -- foundation for all billing logic; blocks everything else
- [ ] **Trial expiration mechanism** -- without this, free trial never ends and no conversion pressure exists
- [ ] **Subscription data model** (Subscription, PaymentHistory, CreditPackage tables) -- backend needs tables before any Stripe work
- [ ] **Stripe webhook handler** with idempotency -- server-authoritative payment processing; the single most critical backend component
- [ ] **Plan Selection page** -- users need to choose and pay for a plan
- [ ] **Stripe Checkout Sessions** (subscriptions + one-time purchases) -- the actual payment flow
- [ ] **Manage Plan page** with billing history -- users need to see status and manage subscription
- [ ] **Cancel subscription flow** -- legal and UX requirement; cannot trap users
- [ ] **Credit top-up purchases** (predefined packages) -- On Demand tier is useless without this
- [ ] **Credit deduction priority** (subscription first, purchased second) -- fairness to paying users
- [ ] **Admin billing visibility** -- admins need to see subscription status and payments

### Add After Validation (v1.x)

Features to add once core monetization is working and users are paying.

- [ ] **Admin manual subscription override** -- add when first customer service case arises
- [ ] **Admin cancel on behalf of user** -- add when support volume justifies it
- [ ] **Admin refund capability** -- add when first refund request comes in (use Stripe dashboard as interim)
- [ ] **Admin billing event log** -- add when debugging billing issues becomes painful
- [ ] **Upgrade/downgrade proration** -- add when users request mid-cycle plan changes (Stripe handles most of this)
- [ ] **Failed payment grace period** -- add when first payment failure causes user churn

### Future Consideration (v2+)

Features to defer until monetization is validated and revenue is flowing.

- [ ] **Annual billing** -- defer until monthly retention metrics prove the model works
- [ ] **Coupon/promo codes** -- defer until marketing campaigns need them
- [ ] **Multi-currency** -- defer until international user base warrants it
- [ ] **Stripe Tax** -- defer until legal/accounting requires it
- [ ] **Customer service role** (scoped admin access) -- defer until team grows beyond single admin

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Depends On Existing |
|---------|------------|---------------------|----------|---------------------|
| Tier restructure | HIGH | MEDIUM | P1 | user_classes.yaml, User model, all tier-checking code |
| Trial expiration | HIGH | MEDIUM | P1 | User model (trial_expires_at), auth middleware |
| Subscription data model | HIGH | MEDIUM | P1 | Alembic, existing Base model pattern |
| Stripe webhook handler | HIGH | HIGH | P1 | Subscription model, idempotency table |
| Plan Selection page | HIGH | MEDIUM | P1 | Settings page tabs (existing pattern) |
| Stripe Checkout Sessions | HIGH | MEDIUM | P1 | Backend billing API endpoints |
| Manage Plan page | HIGH | MEDIUM | P1 | Subscription model, billing API |
| Cancel subscription | HIGH | LOW | P1 | Stripe API, webhook handler |
| Credit top-up purchases | HIGH | MEDIUM | P1 | CreditPackage model, Checkout Sessions |
| Credit deduction priority | MEDIUM | MEDIUM | P1 | UserCredit model change, CreditService |
| Trial banner | MEDIUM | LOW | P1 | trial_expires_at, existing credit pill pattern |
| Admin billing visibility | MEDIUM | LOW | P1 | Admin portal patterns (existing), Subscription model |
| Upgrade/downgrade proration | MEDIUM | MEDIUM | P2 | Stripe proration (mostly automatic) |
| Admin subscription override | MEDIUM | MEDIUM | P2 | Subscription model, admin API patterns |
| Admin cancel on behalf | LOW | LOW | P2 | Stripe cancel API, admin patterns |
| Admin refund capability | MEDIUM | HIGH | P2 | Stripe Refund API, credit clawback logic |
| Admin billing event log | LOW | LOW | P2 | PaymentHistory table (already needed) |
| Failed payment grace period | MEDIUM | LOW | P2 | Webhook handler, user notification |
| Annual billing | LOW | LOW | P3 | Stripe Price objects (different interval) |
| Coupon/promo codes | LOW | MEDIUM | P3 | Stripe Coupons API |

**Priority key:**
- P1: Must have for monetization launch
- P2: Should have, add when specific trigger occurs
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Typical SaaS Analytics Tools | AI/LLM Wrappers (ChatGPT, Claude) | Spectra Approach |
|---------|------------------------------|-----------------------------------|------------------|
| Free tier | Generous free tier to build habit | Limited free tier, then paywall | 14-day trial only. No ongoing free. Forces decision |
| Pricing model | Per-seat or tiered features | Credit/token-based consumption | Hybrid: subscription allocation + pay-per-use top-ups |
| Payment flow | Embedded checkout or Stripe-hosted | Stripe Checkout typical | Stripe Checkout Sessions (hosted page for trust, embedded later) |
| Subscription management | Self-service cancel + upgrade | Self-service with billing portal | Custom Manage Plan page (not Stripe Portal -- need credit-specific UI) |
| Credit system | Rare (usually feature gating) | Token counting, usage meters | Already built: atomic deduction, tier allocation, admin adjust. Add: purchased credits pool |
| Admin billing tools | Full admin console (Chargebee-level) | Minimal (rely on Stripe dashboard) | Moderate: visibility + override + cancel. Refund deferred to P2 |
| Trial-to-paid | Soft paywall (feature limits) | Hard paywall (usage cap) | Hard paywall: blocking overlay after 14 days or credit exhaustion |

## Integration Points with Existing Codebase

These features build on top of existing Spectra infrastructure:

| Existing Component | How Monetization Uses It |
|-------------------|--------------------------|
| `user_classes.yaml` | Restructured: drop `free`, rename `standard` to `basic`, add `on_demand` |
| `CreditService` (atomic deduction) | Extended: deduction priority logic (subscription vs purchased) |
| `UserCredit` model | Extended: add `purchased_credits` field or separate tracking |
| `CreditTransaction` model | Extended: new transaction types (`top_up_purchase`, `subscription_allocation`) |
| `APScheduler` auto-resets | Extended: add trial expiration check job |
| Platform settings | Extended: new settings for pricing, trial duration, Stripe config |
| Admin portal (user management) | Extended: billing tab on user detail, new admin billing actions |
| Settings page (frontend) | Extended: new "Plan & Billing" tab |
| Auth middleware | Extended: trial expiration check, blocked state enforcement |
| Split-horizon architecture | Webhook endpoint runs in `public` mode (Stripe must reach it) |

## Sources

- [Stripe Checkout Sessions documentation](https://docs.stripe.com/payments/checkout)
- [Stripe Build Subscriptions integration](https://docs.stripe.com/billing/subscriptions/build-subscriptions)
- [Stripe Checkout Sessions vs Payment Intents comparison](https://docs.stripe.com/payments/checkout-sessions-and-payment-intents-comparison)
- [Stripe Embedded vs Hosted Checkout](https://support.stripe.com/questions/embedded-checkout-vs-stripe-hosted-checkout)
- [Stripe webhook best practices (Stigg)](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks)
- [Webhook idempotency patterns (Medium)](https://medium.com/@sohail_saifii/handling-payment-webhooks-reliably-idempotency-retries-validation-69b762720bf5)
- [Stripe webhooks guide (Hookdeck)](https://hookdeck.com/webhooks/platforms/guide-to-stripe-webhooks-features-and-best-practices)
- [SaaS billing platform features 2025 (Zenskar)](https://www.zenskar.com/blog/saas-billing-platform-features)
- [SaaS free trial conversion best practices (UserPilot)](https://userpilot.com/blog/saas-free-trial-best-practices/)
- [Free trial to paid conversion strategies (Appcues)](https://www.appcues.com/blog/free-to-paid-conversion-strategies)
- Spectra codebase: `backend/app/services/credit.py`, `backend/app/models/user_credit.py`, `backend/app/config/user_classes.yaml`
- Spectra requirements: `requirements/monetization-requirement.md`, `requirements/monetization-milestone-plan.md`

---
*Feature research for: SaaS monetization (Stripe subscriptions, billing UI, credit top-ups, admin billing tools)*
*Researched: 2026-03-18*
