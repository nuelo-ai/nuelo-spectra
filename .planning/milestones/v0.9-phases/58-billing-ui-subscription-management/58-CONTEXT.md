# Phase 58: Billing UI & Subscription Management - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can view plans, subscribe, manage their subscription, and purchase credit top-ups through Stripe. Covers: Plan Selection page with pricing, settings navigation restructure, Manage Plan page with subscription details/credits/billing history, subscribe/upgrade/downgrade/cancel flows, credit top-up purchase, and payment confirmation emails. Does NOT include admin billing tools (Phase 59), annual billing, multi-currency, or discount codes (deferred).

</domain>

<decisions>
## Implementation Decisions

### Stripe checkout approach
- **Stripe-hosted Checkout (redirect)** — NOT embedded checkout
- User clicks Subscribe/Buy → backend creates Checkout Session → returns URL → frontend redirects to `checkout.stripe.com` → after payment, Stripe redirects back to `/settings/billing`
- Overrides BILL-04 (embedded checkout) and BILL-07 (`@stripe/react-stripe-js`) — neither package needed
- No `@stripe/stripe-js` or `@stripe/react-stripe-js` in frontend

### Plan Selection page (`/settings/plan`)
- Card-based layout: 3 tier cards side by side (On Demand, Basic, Premium)
- Each card shows: tier name, monthly price (or "Pay as you go"), monthly credit allocation, feature list, action button
- **Basic plan highlighted** with colored border or "Most Popular" badge — nudges mid-tier
- Pricing fetched from backend API (platform settings / CreditPackage table) — single source of truth, admin can change without redeploying
- Current plan marked with badge if user is already subscribed
- On Demand card has "Select On Demand" button → API call sets tier (no Stripe checkout) → redirect to `/settings/billing`
- Basic/Premium cards have "Subscribe" button → Stripe-hosted Checkout redirect
- Replaces the existing placeholder plan page from Phase 56

### Settings navigation restructure
- Add tab/sub-nav to settings: **Profile | API Keys | Plan & Billing**
- Each tab is its own page under `/settings/*`
- Restructure existing `/settings` page into `/settings/profile` (or keep as default)
- `/settings/plan` = Plan Selection page
- `/settings/billing` = Manage Plan page
- Satisfies BILL-06

### Manage Plan page (`/settings/billing`)
- Stacked vertical sections (consistent with existing settings page pattern):
  1. **Plan status card** — Current plan name, price, status (Active/Cancelled), next billing date, [Change Plan] and [Cancel] buttons
  2. **Credits section** — Subscription balance (X / allocation), purchased balance, total. [Buy Credits] with inline package cards
  3. **Billing history table** — Date, type (subscription/top-up/renewal), amount, status. Data from PaymentHistory table
- For On Demand users: plan card shows "On Demand", "No active subscription", [Choose Plan] button. Credits section shows purchased balance only. No cancel button.
- For trial users: plan card shows "Free Trial", credits section shows trial balance, no Buy Credits option (hidden, not disabled)

### Subscription change flow (upgrade/downgrade)
- "Change Plan" button navigates to `/settings/plan`
- Current plan is marked, user picks a new plan
- **Confirmation dialog** before processing — explains what happens:
  - Upgrade (e.g., Basic → Premium): "You'll be charged the difference immediately. New credits added now."
  - Downgrade (e.g., Premium → Basic): "Change takes effect at end of billing cycle on [date]."
- **Server-side via Stripe API** (`stripe.subscriptions.update()`) — no new Checkout session needed. Card already on file from initial subscription. Stripe handles proration.
- Webhook confirms the change → update local DB

### Subscription cancellation
- Cancel button on Manage Plan page opens confirmation dialog
- Dialog explains: access continues until end of billing cycle, subscription credits reset to 0 after that date, purchased credits preserved, user moves to On Demand
- Two buttons: [Keep Plan] and [Cancel Plan]
- Backend calls Stripe API to set `cancel_at_period_end = true`
- After cancellation confirmed: plan status card shows "Cancelled — active until [date]"

### Credit top-up flow
- Credit packages shown as small inline cards in the Credits section of `/settings/billing`
- Packages fetched from backend API (CreditPackage table) — e.g., 50/200/500 credits
- Each card shows: credit amount, price, [Buy] button
- Click Buy → backend creates Stripe Checkout Session (payment mode) → redirect to `checkout.stripe.com`
- After payment → redirect back to `/settings/billing` with success toast: "X credits added!"
- Trial users: Buy Credits section hidden entirely (backend enforces TRIAL-07 too)

### Payment confirmation emails
- **Spectra email service** (existing SMTP handler) — consistent sender domain with other Spectra emails
- Covers ALL payment events: new subscription, credit top-up purchase, monthly renewal
- Payment failure email already exists from Phase 57
- Stripe automatic receipts NOT used (different sender domain)

### Claude's Discretion
- Settings tab/nav component design (tabs vs sidebar vs other)
- Exact card styling, spacing, typography for plan cards and package cards
- Loading skeletons for billing page sections
- Billing history table pagination/scrolling approach
- Error state handling (failed to load billing data, Stripe unavailable)
- Email template content and formatting for payment confirmations
- Success toast component implementation
- How "cancelled" state is visually displayed on plan status card

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Billing & Subscription Requirements
- `.planning/REQUIREMENTS.md` — SUB-01 through SUB-05, TOPUP-01 through TOPUP-05, BILL-01 through BILL-06 (BILL-04 and BILL-07 overridden — no embedded checkout)

### Monetization Spec
- `requirements/monetization-requirement.md` — User experience flows for upgrade, cancel, credit top-up

### Phase 55 Context (prior decisions)
- `.planning/phases/55-tier-restructure-data-foundation/55-CONTEXT.md` — DB key `standard` (display "Basic"), dual-balance credit system, 100 trial credits / 7 days, On Demand tier design

### Phase 56 Context (prior decisions)
- `.planning/phases/56-trial-expiration-conversion-pressure/56-CONTEXT.md` — 402 trial enforcement, trial credit restrictions (TRIAL-07), placeholder plan page exists at `/settings/plan`, settings pages accessible during expired trial

### Phase 57 Context (prior decisions)
- `.planning/phases/57-stripe-backend-webhook-foundation/57-CONTEXT.md` — Backend checkout endpoints (`POST /subscriptions/checkout`, `POST /credits/purchase`), SubscriptionService, webhook handlers, Stripe Customer created lazily, redirect to `/settings/billing` after checkout

### Backend Endpoints
- `backend/app/routers/subscriptions.py` — Subscription checkout endpoint
- `backend/app/routers/credits.py` — Credit purchase endpoint
- `backend/app/services/subscription.py` — SubscriptionService (checkout sessions, subscription updates)
- `backend/app/schemas/subscription.py` — Subscription schemas

### Frontend
- `frontend/src/app/(dashboard)/settings/plan/page.tsx` — Existing placeholder plan page (to be replaced)
- `frontend/src/app/(dashboard)/settings/page.tsx` — Current settings page (to be restructured with tab nav)
- `frontend/src/hooks/useTrialState.ts` — Trial state hook (for hiding Buy Credits)
- `frontend/src/hooks/useAuth.tsx` — Auth hook with user tier info
- `frontend/src/hooks/useCredits.ts` — Credits hook (for balance display)

### Email Service
- `backend/app/services/email.py` — Existing SMTP email handler for payment confirmation emails

### Roadmap
- `.planning/ROADMAP.md` — Phase 58 success criteria, dependency chain to Phase 59

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Card`, `CardHeader`, `CardContent` (shadcn/ui): Used in existing plan placeholder — reuse for billing page sections
- `Badge` (shadcn/ui): Used for "Current Plan" marker on tier cards
- `Button` (shadcn/ui): Standard button component throughout app
- `useAuth` hook: Exposes `user.user_class` for tier detection
- `useTrialState` hook: Trial state for hiding Buy Credits from trial users
- `useCredits` hook: Credit balance data
- `SubscriptionService`: Backend service for checkout sessions and subscription management
- Email service: SMTP handler for sending payment confirmations

### Established Patterns
- Settings page: stacked vertical sections (`space-y-6`) with card components
- Auth state via `useAuth` hook + React Query
- API calls via fetch through Next.js catch-all proxy (`/api/[...slug]`)
- shadcn/ui + Tailwind CSS for all components
- Toast notifications likely available via shadcn/ui

### Integration Points
- `/settings` layout needs tab navigation (new)
- `/settings/plan` page replacement (exists as placeholder)
- `/settings/billing` page (new)
- Backend: existing checkout endpoints, subscription update endpoint (may need new endpoint for plan change and cancellation)
- Email service: new templates for subscription confirmation, top-up confirmation, renewal confirmation

</code_context>

<specifics>
## Specific Ideas

- Stripe-hosted redirect chosen over embedded checkout — simplifies frontend, no Stripe JS packages needed
- Upgrade/downgrade via Stripe subscription update API (no re-checkout) — card already on file
- All payment confirmation emails via Spectra's own SMTP handler for consistent sender domain
- On Demand selection is a simple API call (no Stripe involved) since there's no payment
- Trial users: Buy Credits hidden entirely (not disabled/grayed out)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 58-billing-ui-subscription-management*
*Context gathered: 2026-03-21*
