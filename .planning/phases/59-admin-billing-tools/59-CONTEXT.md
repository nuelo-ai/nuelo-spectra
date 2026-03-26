# Phase 59: Admin Billing Tools - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Admins can monitor, override, and manage user billing state including subscriptions, payments, refunds, and discount codes. Covers: user billing detail view in admin, tier override with Stripe sync, subscription cancellation on behalf of users, refund processing, billing platform settings with monetization master switch, and discount code CRUD with Stripe Coupons/Promotion Codes integration. Does NOT include user-facing billing changes (Phase 58 scope), annual billing, multi-currency, or free credits/trial extension discount types.

</domain>

<decisions>
## Implementation Decisions

### User billing detail view
- **D-01:** Single new "Billing" tab added to UserDetailTabs (5 tabs total: Overview, Activity, Credit Transactions, API Keys, Billing)
- **D-02:** Billing tab contains stacked sections: subscription status card at top, payment history table, Stripe event log table
- **D-03:** Stripe event log shows raw webhook events (event type, timestamp, processing status) — not human-readable timeline
- **D-04:** Subscription status card includes 4 action buttons: Force-set tier, Cancel subscription, View in Stripe (external link), Initiate refund

### Tier override workflow
- **D-05:** Force-set tier syncs with Stripe — if user has active subscription, the Stripe subscription is updated/cancelled to match the new tier. Not a local-only override.
- **D-06:** Force-set tier requires mandatory reason field (logged for audit trail)
- **D-07:** Tier change dialog shows current tier, new tier selector, reason text field, and confirmation with Stripe sync explanation

### Refund workflow
- **D-08:** Refund button on each payment row in the payment history table
- **D-09:** Refund dialog pre-fills full amount with option to enter partial amount
- **D-10:** Credits auto-deducted from purchased_balance proportional to refund amount (e.g., full refund of 50-credit purchase removes 50 credits)
- **D-11:** Refund triggers Stripe Refund API and records in PaymentHistory

### Billing platform settings
- **D-12:** Separate Billing Settings page in admin (new route, not extending existing SettingsForm)
- **D-13:** Monetization master switch — when disabled: hides all billing UI (plan selection, buy credits, upgrade/downgrade) from public frontend. Existing subscribers keep their tier and can still cancel. New users get Free Trial as default.
- **D-14:** Billing settings include: monetization toggle, subscription prices per tier. Trial duration, trial credits, and monthly credit allocations are managed via user_classes.yaml (not admin-editable).
- **D-15:** Prices editable in admin UI — backend syncs to Stripe Products/Prices API. Spectra DB is source of truth.

### Discount code management
- **D-16:** Two discount types supported: percentage off subscription, fixed amount off subscription. No free credits or trial extension codes.
- **D-17:** Dedicated Discount Codes page in admin with table (code, type, amount, status, usage count, expiry) + create form dialog
- **D-18:** Row actions: edit, deactivate, delete
- **D-19:** Codes support usage limits (max redemptions) and optional expiration date — maps to Stripe coupon max_redemptions and redeem_by
- **D-20:** Users apply discount codes during Stripe-hosted Checkout (promotion_code passed to Checkout Session). No custom code entry UI on Plan Selection page.
- **D-21:** Admin creates discount code in Spectra → backend creates Stripe Coupon + Promotion Code via API

### Claude's Discretion
- Billing tab section ordering, spacing, and visual hierarchy
- Payment history table columns and pagination approach
- Stripe event log table columns and filtering
- Refund dialog exact layout and validation messages
- Billing Settings page form layout and field grouping
- Discount Codes table columns, sorting, and empty state
- Loading states and error handling for all new pages/sections
- Admin navigation structure for new Billing Settings and Discount Codes pages

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Admin Requirements
- `.planning/REQUIREMENTS.md` — ADMIN-01 through ADMIN-10 (all 10 requirements for this phase)

### Monetization Spec
- `requirements/monetization-requirement.md` — Overall monetization user flows and business rules

### Prior Phase Contexts
- `.planning/phases/55-tier-restructure-data-foundation/55-CONTEXT.md` — DB key `standard` (display "Basic"), dual-balance credit model (subscription_balance + purchased_balance), tier structure
- `.planning/phases/57-stripe-backend-webhook-foundation/57-CONTEXT.md` — SubscriptionService architecture, webhook handlers, Stripe Customer model
- `.planning/phases/58-billing-ui-subscription-management/58-CONTEXT.md` — Stripe-hosted checkout (redirect), plan selection page, manage plan page, subscription change/cancel flows, credit top-up

### Backend Services
- `backend/app/services/subscription.py` — SubscriptionService (checkout sessions, plan changes, cancellation, webhook handlers)
- `backend/app/services/credit.py` — CreditService (balance operations, deductions)
- `backend/app/routers/subscriptions.py` — Subscription router endpoints
- `backend/app/models/payment_history.py` — PaymentHistory model
- `backend/app/scheduler.py` — APScheduler credit reset (skips subscription users)

### Admin Frontend
- `admin-frontend/src/components/users/UserDetailTabs.tsx` — Existing 4-tab user detail (add Billing tab here)
- `admin-frontend/src/components/settings/SettingsForm.tsx` — Existing platform settings form (reference pattern, but new Billing Settings is separate page)
- `admin-frontend/src/components/credits/CreditOverview.tsx` — Credit display patterns
- `admin-frontend/src/hooks/useUsers.ts` — User management hooks (useChangeTier, useAdjustCredits, etc.)

### Stripe API
- Stripe Refunds API — for ADMIN-06 refund processing
- Stripe Coupons API + Promotion Codes API — for ADMIN-08/09/10 discount code management
- Stripe Products/Prices API — for D-15 admin-managed pricing sync

### Roadmap
- `.planning/ROADMAP.md` — Phase 59 success criteria, plan count (4 plans)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `UserDetailTabs.tsx`: Tabbed layout with Overview, Activity, Credit Transactions, API Keys — add Billing tab following same pattern
- `ConfirmModal` (shared component): Reusable for tier override and refund confirmation dialogs
- `StatusBadge` (shared component): For subscription status display
- `Table` components (shadcn/ui): Already used in UserDetailTabs for credit transactions — reuse for payment history and Stripe events
- `useChangeTier` hook: Existing tier change mutation — extend or create new variant for Stripe-synced override
- `useAdjustCredits` hook: Credit adjustment — reference pattern for refund credit deduction
- `SettingsForm.tsx`: Reference pattern for form layout, though Billing Settings is a separate page
- `Dialog` components (shadcn/ui): Used throughout admin for confirmations and forms

### Established Patterns
- Admin pages follow Card-based layout with CardHeader/CardContent
- Data tables use shadcn/ui Table components with inline actions
- Mutations via TanStack Query useMutation hooks in dedicated hook files
- API calls through Next.js catch-all proxy (`/api/[...slug]`)
- Toast notifications via Sonner
- Form state managed with useState (not React Hook Form)

### Integration Points
- `UserDetailTabs.tsx` — Add new Billing tab component
- Admin sidebar navigation — Add Billing Settings and Discount Codes links
- Backend — New admin endpoints needed: user billing detail, force-set tier (Stripe-synced), refund, billing settings CRUD, discount code CRUD
- Stripe API — New integrations: Refunds API, Coupons/Promotion Codes API, Products/Prices update API

</code_context>

<specifics>
## Specific Ideas

- Monetization master switch: when OFF, freeze existing subscriber state (can still cancel), hide all billing UI for new actions, new users still get Free Trial
- Force-set tier must sync with Stripe (not local-only override) — if setting to On Demand, cancel Stripe sub; if setting to Basic/Premium, create/update Stripe sub
- Refund auto-deducts credits proportionally — no manual two-step process
- Discount codes created in Spectra admin → synced to Stripe Coupons + Promotion Codes → users redeem during Stripe-hosted Checkout
- Prices managed in admin UI as source of truth, synced to Stripe — admin doesn't need Stripe Dashboard for price changes
- Raw Stripe events preferred over human-readable timeline for the event log (admin wants technical visibility)

</specifics>

<deferred>
## Deferred Ideas

- **Free credits bonus discount codes** — codes that add bonus credits (not Stripe coupon, Spectra-only). Could be a future enhancement.
- **Trial extension discount codes** — codes that extend trial_expires_at. Deferred to keep discount system focused on Stripe coupons.
- **Annual billing** — yearly subscription option. Not in current milestone scope.
- **Multi-currency support** — pricing in different currencies. Future milestone.

</deferred>

---

*Phase: 59-admin-billing-tools*
*Context gathered: 2026-03-24*
