# Pitfalls Research

**Domain:** SaaS monetization -- Stripe payment gateway, subscription management, billing UI, admin billing tools added to existing credit-based analytics platform
**Researched:** 2026-03-18
**Confidence:** HIGH (Stripe docs + community patterns + codebase analysis)

## Critical Pitfalls

### Pitfall 1: Webhook Handler is Not Idempotent -- Double-Charging and Duplicate Credit Grants

**What goes wrong:**
Stripe retries webhook delivery on timeout, 5xx, or network failure. Without idempotency, the same `checkout.session.completed` event processes twice: user gets double credits on a top-up, or a subscription activates twice creating duplicate `Subscription` rows. Duplicate charges account for up to 8% of user complaints in SaaS platforms.

**Why it happens:**
Developers test with single webhook deliveries and never simulate retries. The happy path works, so idempotency feels like over-engineering. Then in production, a slow DB write causes Stripe to retry, and the handler runs again.

**How to avoid:**
- Create a `stripe_events` table with `event_id` (unique constraint) and `processed_at`.
- At the start of every webhook handler: `INSERT INTO stripe_events (event_id) ... ON CONFLICT DO NOTHING`. If the insert returns 0 rows affected, the event was already processed -- return 200 immediately.
- Wrap the entire handler logic in a DB transaction. If the transaction fails, the event ID row also rolls back, allowing Stripe to retry cleanly.
- Keep webhook handlers fast (under 5 seconds). Acknowledge with 200, then do heavy work (email, credit allocation) in a background task or queue.

**Warning signs:**
- No `stripe_events` or `processed_webhooks` table in the schema.
- Webhook handler does credit allocation directly without checking for prior processing.
- Users report "I got charged twice" or "I got extra credits."

**Phase to address:**
Phase 1 (Stripe Integration) -- idempotency must be baked into the webhook handler from day one, not bolted on later.

---

### Pitfall 2: Stripe State and Local DB Drift -- Subscription Says Active but Stripe Says Cancelled

**What goes wrong:**
The local `Subscription` table shows `status: active` but Stripe's subscription is `canceled` or `past_due`. This happens when webhooks are missed (endpoint down during deploy), processed out of order, or when admin overrides local state without touching Stripe. Users get access they should not have, or lose access they should have.

**Why it happens:**
Treating the local DB as the source of truth for subscription state. In reality, Stripe is the source of truth for billing state. The local DB is a cache of Stripe's state. When the cache diverges, everything breaks.

**How to avoid:**
- **Stripe is the source of truth for billing.** Local DB is a read-optimized cache.
- On every subscription-sensitive operation (credit reset, access check at plan boundaries), verify against Stripe if the local data is stale (e.g., `current_period_end` has passed).
- Build a reconciliation endpoint: admin can trigger a "sync from Stripe" for a user, which fetches `stripe.Subscription.retrieve()` and updates local state.
- Handle out-of-order events: use `event.data.object.created` timestamp comparison, not arrival order. If a `customer.subscription.deleted` arrives before `customer.subscription.updated`, process based on the event's timestamp, not the order received.
- Log every webhook event (even ones you skip due to idempotency) for debugging.

**Warning signs:**
- No reconciliation mechanism exists.
- Admin tier override updates local DB but does not log that it intentionally diverges from Stripe.
- Users report "my plan shows Basic but I was charged for Premium."

**Phase to address:**
Phase 1 (Stripe Integration) -- reconciliation strategy must be designed alongside webhook handling.

---

### Pitfall 3: Single-Balance Credit System Cannot Track Credit Source -- Refunds Become Impossible

**What goes wrong:**
The current `UserCredit` model has a single `balance` field (NUMERIC(10,1)). The monetization plan requires: "subscription credits consumed first, purchased credits last." With a single balance field, there is no way to know which credits are subscription-granted vs. purchased. When admin issues a refund for a credit top-up, the system cannot deduct the correct credits back -- it just has a number with no provenance.

This is the **most Spectra-specific pitfall** because it requires restructuring the existing credit model that every feature (chat, Pulse, API) depends on.

**Why it happens:**
The current credit system was designed for a simple metered model: tier gives you X credits, deduction is atomic, reset is periodic. There was no concept of "credit source." Adding purchased credits without tracking source creates an accounting black hole.

**How to avoid:**
- Add a `credit_source` concept. Two approaches:
  - **Dual balance fields:** Add `subscription_balance` and `purchased_balance` to `UserCredit`. Deduction reads subscription first, then purchased. Simple but inflexible.
  - **Credit ledger model (recommended):** Each credit grant is a ledger entry with `source` (subscription_reset, top_up_purchase, admin_adjustment), `amount`, `remaining`, and `expires_at`. Deduction walks the ledger in priority order. This supports refund traceability -- you can tie a refund to a specific purchase ledger entry.
- The current `CreditTransaction` table already logs transactions but does not track remaining balance per source. Extending it to a proper ledger is the cleanest path.
- **Migration:** Existing users' balances become a single ledger entry with `source: legacy_balance`. No credits are lost.

**Warning signs:**
- `UserCredit.balance` remains a single field after monetization work.
- Refund endpoint just does `balance -= refund_amount` without checking what was purchased.
- Credit deduction has no priority logic (subscription first, purchased second).

**Phase to address:**
Phase 1 or early Phase 2 -- credit model restructure must happen BEFORE Stripe integration writes credits, otherwise you are building on a foundation that cannot support the requirements.

---

### Pitfall 4: Tier Migration Breaks Existing Users -- `free` Tier Users Lose Access Overnight

**What goes wrong:**
Current `user_classes.yaml` has `free` tier (10 credits/week, ongoing). The monetization plan eliminates `free` entirely -- only `free_trial` (temporary, 14 days) exists. If the code deploys with `free` removed from `user_classes.yaml`, every existing `free` tier user's `get_class_config("free")` returns `None`. The `CreditService.deduct_credit()` calls `get_class_config(user_class)` -- if it returns `None`, the unlimited check fails, balance lookups break, and users effectively get locked out. The `scheduler.py` reset logic also breaks because it reads config per user class.

**Why it happens:**
Tier restructure is treated as a "config change" when it is really a "data migration." The `user_class` column on `User` contains string values (`"free"`, `"standard"`) that must match keys in `user_classes.yaml`. Renaming or removing keys without migrating the data column is a schema-data mismatch.

**How to avoid:**
- Write an Alembic migration that:
  1. Updates all `User.user_class = 'free'` to `'free_trial'` (with `trial_expires_at` set to migration date + grace period, e.g., 30 days).
  2. Updates all `User.user_class = 'standard'` to `'basic'`.
  3. Adds `on_demand` to `user_classes.yaml`.
- Keep the old tier keys in `user_classes.yaml` as aliases during a transition period (1 release cycle), mapping to the new tiers. Remove aliases in the next release.
- Send email notification to affected `free` tier users before deploying: "Your account will transition to a free trial. You have 30 days to choose a plan."
- Test the migration on a copy of production data, not just an empty dev DB.

**Warning signs:**
- `user_classes.yaml` is modified without a corresponding Alembic migration.
- `User.user_class` column still contains `"free"` or `"standard"` values after deploy.
- No communication plan for existing users.

**Phase to address:**
Phase 1 (Tier Restructure) -- must be the first thing done, before any Stripe code touches tiers.

---

### Pitfall 5: Trial Expiration Checked Only on Page Load -- Background Abuse Window

**What goes wrong:**
Trial expiration is checked only when the frontend loads (e.g., a React `useEffect` or route guard). A user who keeps a browser tab open past the 14-day trial continues to use the app until they refresh. API users with `spe_` keys bypass the frontend entirely and never see the trial check.

**Why it happens:**
Frontend-only enforcement feels sufficient during development because you always refresh. The API path (`/api/v1/query`) is overlooked because it was built before monetization existed.

**How to avoid:**
- **Backend middleware enforcement:** Add a check in the auth dependency (FastAPI `Depends`) that runs on every authenticated request. If `user_class == 'free_trial'` and `trial_expires_at < now()`, return 403 with a body that the frontend interprets as "trial expired."
- This covers ALL paths: frontend, API v1, MCP server.
- Do NOT rely on a background scheduler to flip the user's tier. The scheduler is a nice-to-have for pre-emptive state cleanup, but the real-time check must be in the request path.
- The existing `CreditService.deduct_credit()` already checks balance -- add trial expiration as a pre-check before balance check.

**Warning signs:**
- Trial check only exists in frontend code (React component or route guard).
- API v1 endpoints have no trial awareness.
- Scheduler is the only mechanism that transitions trial users.

**Phase to address:**
Phase 1 (Trial Expiration) -- must be backend middleware, not frontend logic.

---

### Pitfall 6: Admin Override Creates Ghost State -- Stripe and Local DB Permanently Disagree

**What goes wrong:**
Admin grants a user Premium "as a courtesy" via the admin portal. The local `Subscription` table now says Premium, but Stripe has no subscription for this user. When the credit reset scheduler runs, it grants Premium credits. When the "courtesy period" ends, there is no Stripe event to trigger a downgrade -- the admin must remember to manually revert. If they forget, the user stays on free Premium forever.

**Why it happens:**
Admin override is built as "just update the local DB" without considering the lifecycle. There is no expiration mechanism or Stripe-side representation of the override.

**How to avoid:**
- Admin overrides must have a mandatory `expires_at` timestamp and `override_reason`.
- Create a separate `subscription_overrides` table: `user_id, tier, granted_by, reason, expires_at, created_at`.
- The subscription state resolver checks overrides first (if active and not expired), then falls back to Stripe subscription state.
- Background task checks for expired overrides daily and reverts users to their Stripe-derived state.
- Admin dashboard shows active overrides with countdown.

**Warning signs:**
- Admin override directly writes to `User.user_class` with no expiration.
- No audit trail for why a user's tier was changed.
- Users discovered on Premium tier with no Stripe subscription and no override record.

**Phase to address:**
Phase 3 (Admin Billing Tools) -- but the override data model should be designed in Phase 1 alongside the subscription model.

---

### Pitfall 7: Checkout Session Price Comes from Frontend -- Users Can Pay $0 for Premium

**What goes wrong:**
The frontend sends the plan ID and price to the backend's `/api/billing/subscribe` endpoint. The backend passes these values to `stripe.checkout.Session.create()` without validation. A malicious user intercepts the request and changes the price to $0.01 or swaps a Basic plan ID for Premium.

**Why it happens:**
Developers build the plan selection UI first, wire it to the API, and trust the request body because "our UI sends the right values." The Stripe Checkout Session creation accepts whatever `line_items` you give it.

**How to avoid:**
- **Never accept price or plan details from the client.** The frontend sends only a plan identifier (e.g., `"basic"` or `"premium"`).
- The backend resolves this to a server-side Stripe Price ID stored in platform settings or environment variables.
- Create Stripe Products and Prices in the Stripe Dashboard (or via API during setup), store their IDs in the backend config.
- The `POST /api/billing/subscribe` endpoint: receives `{ "plan": "basic" }`, looks up `STRIPE_PRICE_ID_BASIC` from config, creates Checkout Session with that price. The client never sees or controls the price.

**Warning signs:**
- API endpoint accepts `price_id` or `amount` from request body.
- Stripe Price IDs are stored in frontend code or environment.
- No server-side plan-to-price mapping exists.

**Phase to address:**
Phase 1 (Stripe Integration) -- Checkout Session creation must use server-side price resolution from day one.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single `balance` field instead of dual/ledger | No migration needed, existing deduction code unchanged | Cannot track credit source, refunds are guesswork, deduction priority impossible | Never -- this is the core requirement. Must restructure before writing any Stripe credit code |
| Polling Stripe API on every request instead of webhook-driven cache | No webhook infrastructure needed | API rate limits (25 req/s test, 100 req/s live), 200-500ms latency per request, Stripe costs at scale | Only for reconciliation checks, not as primary state source |
| Storing Stripe secrets in `platform_settings` DB table | Runtime configurable via admin UI | Secrets in DB are queryable by anyone with DB access; if admin portal has SQL injection, secrets leak | Never -- use environment variables. `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` belong in `.env`, not the DB |
| Skipping Stripe test mode and testing against live | Faster "real" testing | Accidental charges, no test clocks for trial simulation, cannot test edge cases | Never -- always use test mode. Use Stripe Test Clocks for trial expiration testing |
| Hardcoding credit packages in frontend | Fast to build | Price changes require frontend redeploy, risk of client-server mismatch | MVP only -- move to `/api/billing/packages` endpoint reading from DB within same milestone |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Stripe Webhooks | Responding 200 only after all processing completes (DB writes, emails, credit allocation). Stripe times out at 20 seconds, retries, causing duplicate processing | Respond 200 immediately after signature verification and event ID dedup check. Process in background task. If you must process synchronously, keep it under 5 seconds |
| Stripe Checkout Sessions | Using `payment` mode for subscriptions (creates one-time charge, no recurring billing) | Use `mode='subscription'` for Basic/Premium plans. Use `mode='payment'` only for one-time credit top-ups |
| Stripe Webhooks (signature) | Parsing the request body as JSON before verifying the signature. `stripe.Webhook.construct_event()` requires the raw request body bytes, not parsed JSON | In FastAPI: use `await request.body()` to get raw bytes. Do NOT use `await request.json()` before verification |
| Stripe Customer objects | Creating a new Stripe Customer for every checkout session. User ends up with 5 Customer objects in Stripe, each with separate payment methods | Create ONE Stripe Customer on first purchase, store `stripe_customer_id` on the User or Subscription model. Reuse for all subsequent sessions |
| Stripe Proration | Ignoring proration on plan changes (Basic to Premium). User pays full Premium price immediately, not the prorated difference | Use `proration_behavior='create_prorations'` (Stripe default) when updating subscriptions. Test proration amounts in test mode |
| APScheduler credit reset | Current `scheduler.py` resets credits based on `user_classes.yaml` allocation. After monetization, subscription users should reset based on their Stripe subscription cycle, not the scheduler | Subscription credit resets should be triggered by `invoice.paid` webhook (Stripe bills, credits reset). Only On Demand and legacy users use the scheduler. Dual reset paths must not conflict |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous Stripe API calls in webhook handler | Webhook processing takes 3-10 seconds. Stripe retries. Multiple handlers run concurrently for the same user, causing race conditions on credit balance | Use `SELECT FOR UPDATE` on credit rows (already done in CreditService). Keep Stripe API calls out of the hot path. Cache Stripe Customer data locally | At 50+ concurrent webhook events (e.g., batch subscription renewal at month boundary) |
| Loading full billing history on every Manage Plan page load | Page load time increases linearly with transaction count. At 100+ transactions, the page takes 2+ seconds | Paginate `PaymentHistory` queries. Cache current subscription status separately from history. Load history on scroll/click | At 6+ months of active subscription (100+ transactions per user) |
| Credit balance check on every API request (trial + subscription + purchased) | If checking Stripe API on each request, 200-500ms added per request. At 10 concurrent users, Stripe rate limit risk | Cache subscription state locally. Only verify against Stripe when local data suggests period boundary (current_period_end passed) | At 100+ API requests/minute or 50+ concurrent users |
| Webhook event log table grows unbounded | `stripe_events` table with every event ID. Query performance degrades for reconciliation queries | Add `created_at` index, implement retention policy (archive events older than 90 days), partition by month if needed | At 100K+ events (roughly 1 year of moderate usage) |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Stripe Secret Key in frontend environment variables (e.g., `NEXT_PUBLIC_STRIPE_SECRET_KEY`) | Full API access from any browser. Attacker can create charges, read customer data, issue refunds | Only `STRIPE_PUBLISHABLE_KEY` goes to frontend. Secret key stays server-side only. Verify no `NEXT_PUBLIC_` prefix on secret keys |
| Webhook endpoint has no signature verification | Attacker sends fake webhook events: "checkout.session.completed" for any user, granting free credits/subscriptions | Always use `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`. Reject events that fail verification with 400 |
| Credit top-up amount accepted from client request body | User sends `{ "credits": 99999, "amount_cents": 1 }` to buy 99999 credits for $0.01 | Server resolves credit amount from the Stripe Price ID. Credit packages are defined server-side (DB or config). The Checkout Session success webhook reads the package details from metadata, not from the client |
| No rate limiting on billing endpoints | Attacker spams `/api/billing/subscribe` creating thousands of Checkout Sessions, exhausting Stripe API limits and potentially triggering fraud flags | Rate limit billing endpoints: max 5 requests/minute per user for subscription/top-up creation. Use the existing FastAPI middleware pattern |
| Refund endpoint accessible without admin verification | Any authenticated user could potentially trigger refunds | Refund endpoints must require admin role check. Refund actions must log admin_id, reason, and original transaction reference |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Trial banner dismissible with no persistence | User dismisses banner, forgets trial is expiring, gets blocked with no warning | Banner is non-dismissible in the last 3 days. Before that, dismissal is per-session only (reappears on next login). Banner urgency escalates: blue (14-7 days) -> amber (7-3 days) -> red (3-0 days) |
| "Your trial expired" shown as a redirect to /login | User thinks their account was deleted or hacked | Show a full-screen overlay ON the dashboard (user stays logged in) with clear messaging: "Your 14-day trial has ended. Choose a plan to continue." Show plan cards directly in the overlay |
| Subscription cancellation is instant with no confirmation of what happens | User clicks Cancel, panics because they think access is immediately revoked | Two-step: confirmation dialog explains "Your plan stays active until [DATE]. After that, you'll move to On Demand." Show exactly what changes and when |
| Credit balance shows one number with no breakdown | User bought 50 credits, subscription gives 200. Balance shows "250" but user does not know which expire at cycle end | Show breakdown: "Subscription: 147/200 (resets Apr 17) | Purchased: 50 (no expiry)". This requires the dual-balance model from Pitfall 3 |
| Manage Plan page requires multiple clicks to find from the main app | User runs out of credits mid-analysis, cannot quickly find where to buy more | Add "Buy Credits" link directly in the credit pill component (header). When credit deduction fails, the error toast includes a "Buy Credits" button |
| Plan change takes effect immediately with no preview | User upgrades from Basic to Premium, charge happens instantly. User did not expect to be charged today | Show a preview before confirming: "You'll be charged $X.XX today (prorated for remaining days). Your new plan starts immediately." |

## "Looks Done But Isn't" Checklist

- [ ] **Webhook handler:** Often missing idempotency -- verify a `stripe_events` table exists with unique constraint on `event_id`, and the handler checks before processing
- [ ] **Subscription cancel:** Often missing "end of billing cycle" behavior -- verify cancellation sets `cancel_at_period_end=True` in Stripe, not immediate deletion. User retains access until period ends
- [ ] **Credit top-up:** Often missing the credit-grant record -- verify purchased credits are recorded with source metadata, not just added to a single balance field
- [ ] **Trial expiration:** Often missing API path coverage -- verify trial check runs in the FastAPI auth dependency, not just frontend route guards. Test with `curl` against `/api/v1/query`
- [ ] **Plan selection page:** Often missing "current plan" indicator -- verify the page highlights the user's active plan and disables the button for it
- [ ] **Stripe test mode:** Often missing test clock usage for trial testing -- verify trial expiration was tested using Stripe Test Clocks, not by manually changing DB timestamps
- [ ] **Admin refund:** Often missing credit clawback -- verify that when admin refunds a top-up payment, the corresponding credits are also deducted (or at minimum, the admin is prompted to deduct)
- [ ] **Webhook endpoint security:** Often missing IP allowlisting or at minimum signature verification -- verify `stripe.Webhook.construct_event()` is called before any processing
- [ ] **Existing user migration:** Often missing data migration script -- verify an Alembic migration exists that remaps `free` -> `free_trial` and `standard` -> `basic` in the `users` table
- [ ] **Credit deduction priority:** Often missing dual-source logic -- verify deduction drains subscription credits before purchased credits, and that the balance response shows both separately
- [ ] **Downgrade handling:** Often missing "preserve purchased credits" logic -- verify that when a subscription ends, only subscription-granted credits are removed; purchased credits remain untouched

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Duplicate credit grants from non-idempotent webhooks | MEDIUM | Query `CreditTransaction` for duplicate entries by `stripe_event_id`. Identify affected users. Issue manual balance corrections via `admin_adjust`. Add `stripe_events` dedup table to prevent recurrence |
| Stripe-local state drift | LOW-MEDIUM | Build reconciliation script: for each user with a `stripe_customer_id`, fetch Stripe subscription state, compare with local `Subscription` table, generate diff report. Apply corrections after admin review |
| Single-balance model deployed to production | HIGH | Requires data model migration: add `subscription_balance` and `purchased_balance` columns (or ledger table). Existing `balance` values become `subscription_balance` for subscription users, `purchased_balance` for top-up users. Existing `CreditTransaction` history needs backfill of `source` field. All deduction callers need updating. This is why getting the model right in Phase 1 is critical |
| Free tier users broken by config removal | MEDIUM | Emergency: re-add `free` key to `user_classes.yaml` as an alias pointing to `free_trial` config. Then run the Alembic migration to remap user_class values. Remove alias in next release |
| Admin override without expiration | LOW | Query `User` table for users whose `user_class` does not match any `Subscription` record. These are likely manual overrides. Add override records retroactively with a reasonable expiration |
| Checkout session with client-controlled pricing | CRITICAL | Audit all completed checkout sessions in Stripe Dashboard. Compare intended prices (from config) against actual charged amounts. Refund any undercharges. This is a revenue-loss incident |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Non-idempotent webhooks | Phase 1: Stripe Integration | `stripe_events` table exists; handler tests include duplicate event delivery; no double credit grants in test |
| Stripe-local state drift | Phase 1: Stripe Integration | Reconciliation endpoint exists; admin can trigger sync; out-of-order event test passes |
| Single-balance credit model | Phase 1: Credit Model Restructure (before Stripe writes credits) | `UserCredit` has dual balances or ledger entries; deduction respects priority; refund traces to source |
| Tier migration breaks existing users | Phase 1: Tier Restructure (first thing) | Alembic migration exists; `free`/`standard` no longer appear in `User.user_class`; old config keys handled gracefully |
| Trial only checked on frontend | Phase 1: Trial Expiration | FastAPI auth dependency checks `trial_expires_at`; API v1 and MCP requests blocked for expired trials |
| Admin override ghost state | Phase 3: Admin Billing Tools (model designed in Phase 1) | Override records have `expires_at`; background task reverts expired overrides; admin dashboard shows active overrides |
| Client-controlled pricing | Phase 1: Stripe Integration | API endpoint accepts plan name only; server resolves to Stripe Price ID; no `price` or `amount` in request schema |

## Sources

- [Stripe Webhook Best Practices (Stigg)](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks)
- [Stripe Idempotent Requests API Reference](https://docs.stripe.com/api/idempotent_requests)
- [Stripe Database Reconciliation Series (Part 1)](https://stripe.dev/blog/database-reconciliation-growing-businesses-part-1)
- [Stripe Database Reconciliation Series (Part 2)](https://stripe.dev/blog/database-reconciliation-growing-businesses-part-2)
- [Stripe Database Reconciliation Series (Part 3)](https://stripe.dev/blog/database-reconciliation-growing-businesses-part-3)
- [Stripe Build Subscriptions Documentation](https://docs.stripe.com/billing/subscriptions/build-subscriptions)
- [Stripe How Subscriptions Work](https://docs.stripe.com/billing/subscriptions/overview)
- [Stripe Billing Credits Documentation](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits)
- [Stripe Checkout Sessions API](https://docs.stripe.com/payments/quickstart-checkout-sessions)
- [How to Implement Credit System in Subscription Model (FlexPrice)](https://flexprice.io/blog/how-to-implement-credit-system-in-subscription-model)
- [SaaS Data Migration to New Payment System (PayPro Global)](https://payproglobal.com/how-to/handle-saas-data-migration-to-payment-solution/)
- [Managing Subscription Changes in Stripe (Moldstud)](https://moldstud.com/articles/p-how-to-effectively-manage-subscription-changes-in-stripe-and-avoid-common-pitfalls)
- Spectra codebase analysis: `backend/app/services/credit.py`, `backend/app/models/user_credit.py`, `backend/app/models/user.py`, `backend/app/config/user_classes.yaml`

---
*Pitfalls research for: Spectra monetization -- Stripe payment, subscription management, billing UI, admin tools*
*Researched: 2026-03-18*
