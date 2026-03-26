# Phase 58: Billing UI & Subscription Management - Research

**Researched:** 2026-03-22
**Domain:** Frontend billing UI (Next.js/React), backend subscription management endpoints, email templates
**Confidence:** HIGH

## Summary

Phase 58 builds the user-facing billing experience on top of the Phase 57 Stripe backend foundation. The work splits into three domains: (1) frontend pages and components for plan selection and subscription management, (2) new backend API endpoints for plan changes, cancellation, on-demand selection, pricing data, billing history, and credit packages listing, and (3) payment confirmation email templates.

The existing codebase provides strong foundations. Phase 57 delivered checkout session creation endpoints, webhook handlers for all Stripe events, and the SubscriptionService with full lifecycle management. The frontend has shadcn/ui components (Card, Badge, Button, Tabs, AlertDialog, Table, Skeleton, Sonner), React Query for data fetching, and an established API client pattern. The settings page exists but needs restructuring into a tabbed layout.

**Primary recommendation:** Build backend API endpoints first (plan change, cancel, select on-demand, pricing, billing history, credit packages), then frontend settings layout restructure, then plan selection page, then manage plan page with all sub-sections.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Stripe-hosted Checkout (redirect)** -- NOT embedded checkout. No `@stripe/stripe-js` or `@stripe/react-stripe-js` in frontend. Overrides BILL-04 and BILL-07.
- **Plan Selection page** (`/settings/plan`): 3 tier cards (On Demand, Basic, Premium), pricing from backend API, Basic highlighted with "Most Popular" badge, current plan marked with badge.
- **Settings navigation restructure**: Tab/sub-nav with Profile | API Keys | Plan & Billing. Each tab is its own page under `/settings/*`.
- **Manage Plan page** (`/settings/billing`): Stacked vertical sections -- plan status card, credits section with inline package cards, billing history table.
- **Subscription change flow**: "Change Plan" navigates to `/settings/plan`, confirmation dialog before processing, server-side via `stripe.subscriptions.update()` (no new Checkout session), webhook confirms change.
- **Subscription cancellation**: Cancel button opens confirmation dialog, backend calls Stripe API `cancel_at_period_end = true`, status shows "Cancelled -- active until [date]".
- **Credit top-up flow**: Packages shown as inline cards in Credits section, click Buy redirects to Stripe-hosted Checkout (payment mode), trial users: Buy Credits hidden entirely.
- **Payment confirmation emails**: Via Spectra email service (existing SMTP handler), covers new subscription, credit top-up, monthly renewal. Stripe automatic receipts NOT used.
- **On Demand selection**: Simple API call (no Stripe checkout), sets tier and redirects to `/settings/billing`.

### Claude's Discretion
- Settings tab/nav component design (tabs vs sidebar vs other)
- Exact card styling, spacing, typography for plan cards and package cards
- Loading skeletons for billing page sections
- Billing history table pagination/scrolling approach
- Error state handling (failed to load billing data, Stripe unavailable)
- Email template content and formatting for payment confirmations
- Success toast component implementation
- How "cancelled" state is visually displayed on plan status card

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SUB-01 | User can subscribe to Basic or Premium plan via Plan Selection page | Plan Selection page with Subscribe buttons -> POST /subscriptions/checkout -> Stripe redirect. Existing checkout endpoint ready. |
| SUB-02 | User can upgrade from Basic to Premium (immediate) | New POST /subscriptions/change endpoint calling stripe.subscriptions.update(). Webhook handler (STRIPE-09) already processes plan changes. |
| SUB-03 | User can downgrade from Premium to Basic (end of cycle) | Same /subscriptions/change endpoint with proration_behavior="none" and billing_cycle_anchor preservation. |
| SUB-04 | User can cancel subscription (end of cycle, purchased credits preserved) | New POST /subscriptions/cancel endpoint calling stripe.subscriptions.update(cancel_at_period_end=True). Webhook handler (STRIPE-10) already handles deletion. |
| SUB-05 | User can select On Demand plan (no subscription) | New POST /subscriptions/select-on-demand endpoint -- updates user_class to on_demand, no Stripe interaction. |
| TOPUP-01 | Predefined credit packages available for purchase | New GET /credits/packages endpoint returning active CreditPackage rows ordered by display_order. |
| TOPUP-02 | Credit packages configurable via CreditPackage table | Already exists (Phase 55 DATA-03). Packages fetched from DB, not hardcoded. |
| TOPUP-03 | User can purchase credits via Stripe Checkout from Manage Plan page | Existing POST /credits/purchase endpoint returns checkout_url. Frontend redirects to Stripe. |
| TOPUP-04 | Purchased credits added on successful payment (via webhook) | Already implemented in Phase 57 (STRIPE-06). No work needed. |
| TOPUP-05 | Free Trial users not eligible for credit top-up | Backend enforcement exists (Phase 57). Frontend hides Buy Credits section for trial users via useTrialState. |
| BILL-01 | Plan Selection page showing On Demand, Basic, Premium with pricing | New /settings/plan page replacing existing placeholder. Pricing from GET /subscriptions/plans endpoint. |
| BILL-02 | Plan Selection shows current plan/trial status | useAuth provides user.user_class. Existing placeholder already does this. Enhance with subscription status from GET /subscriptions/status. |
| BILL-03 | Manage Plan page with subscription details, credits, billing history | New /settings/billing page composing PlanStatusCard + CreditBalanceCard + BillingHistoryTable. Data from multiple API endpoints. |
| BILL-04 | Stripe Embedded Checkout (OVERRIDDEN -- using redirect instead) | Owner decision: Stripe-hosted redirect. No embedded checkout. Requirement satisfied by redirect flow. |
| BILL-05 | Billing history display on Manage Plan page | New GET /subscriptions/billing-history endpoint returning PaymentHistory rows for current user. |
| BILL-06 | Settings navigation updated with "Plan & Billing" section | New SettingsLayout component with Tabs navigation wrapping all /settings/* pages. |
| BILL-07 | @stripe/stripe-js and @stripe/react-stripe-js (OVERRIDDEN -- not needed) | Owner decision: No Stripe JS packages. Redirect approach eliminates this dependency. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | App router, pages, layouts | Already in project |
| React | 19.2.3 | UI components | Already in project |
| shadcn/ui (new-york) | N/A (components) | Card, Badge, Button, Tabs, AlertDialog, Table, Skeleton, Separator, Sonner | Already installed and used throughout |
| @tanstack/react-query | 5.90.20 | Data fetching, cache invalidation | Already in project for all API calls |
| sonner | 2.0.7 | Toast notifications | Already installed, Toaster in providers.tsx |
| Tailwind CSS | v4 | Styling | Already in project |
| Lucide React | 0.563.0 | Icons | Already in project |

### Backend
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | API endpoints | Project framework |
| stripe (Python) | >=14.0.0,<15.0 | Stripe API calls for subscription update/cancel | Already pinned in Phase 57 |
| Jinja2 | (existing) | Email templates | Already used for password reset, invite, payment failed emails |
| aiosmtplib | (existing) | SMTP email sending | Already in email service |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stripe-hosted Checkout | Embedded Checkout | LOCKED: Owner chose redirect for simplicity -- no Stripe JS packages needed |
| Custom pagination | Infinite scroll | Billing history is finite; simple "load more" or full list is sufficient |

**Installation:** No new packages needed. All dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
  app/(dashboard)/settings/
    layout.tsx               # NEW: Settings layout with tab navigation
    page.tsx                 # Existing: Profile settings (restructured)
    keys/
      page.tsx               # NEW: API Keys page (extracted from settings)
    plan/
      page.tsx               # EXISTS: Replace placeholder with full plan selection
    billing/
      page.tsx               # NEW: Manage Plan page
  components/
    settings/
      SettingsLayout.tsx     # NEW: Tab navigation wrapper
      SettingsNav.tsx        # NEW: Tab bar component
      ProfileForm.tsx        # EXISTS
      PasswordForm.tsx       # EXISTS
      AccountInfo.tsx        # EXISTS
      ApiKeySection.tsx      # EXISTS
    billing/
      PlanCard.tsx           # NEW: Single tier card
      PlanStatusCard.tsx     # NEW: Current plan info
      CreditBalanceCard.tsx  # NEW: Credit balance display
      CreditPackageCard.tsx  # NEW: Purchasable credit package
      BillingHistoryTable.tsx # NEW: Payment history table
  hooks/
    useSubscription.ts       # NEW: Subscription status hook
    useBillingHistory.ts     # NEW: Billing history hook
    usePlanPricing.ts        # NEW: Plan pricing hook
    useCreditPackages.ts     # NEW: Credit packages hook

backend/app/
  routers/
    subscriptions.py         # EXTEND: Add change, cancel, select-on-demand, plans, billing-history endpoints
  schemas/
    subscription.py          # EXTEND: Add plan change, pricing, billing history schemas
  services/
    subscription.py          # EXTEND: Add change_plan, cancel_subscription methods
    email.py                 # EXTEND: Add payment confirmation email functions
  templates/email/
    subscription_confirmation.html  # NEW
    subscription_confirmation.txt   # NEW
    topup_confirmation.html         # NEW
    topup_confirmation.txt          # NEW
    renewal_confirmation.html       # NEW
    renewal_confirmation.txt        # NEW
```

### Pattern 1: Settings Layout with Tab Navigation
**What:** A shared layout component that wraps all `/settings/*` pages with consistent header and tab navigation.
**When to use:** For the settings page restructure (BILL-06).
**Example:**
```typescript
// frontend/src/app/(dashboard)/settings/layout.tsx
// Uses Next.js App Router nested layout
// SettingsNav uses shadcn Tabs with usePathname() for active state
// "Plan & Billing" tab highlights for both /settings/plan and /settings/billing
```

### Pattern 2: API Call -> Stripe Redirect
**What:** Frontend calls backend API to create Stripe session, receives URL, redirects via `window.location.href`.
**When to use:** Subscribe flow and credit top-up flow.
**Example:**
```typescript
// 1. Call backend
const res = await apiClient.post("/subscriptions/checkout", { plan_tier: "standard" });
const { checkout_url } = await res.json();
// 2. Redirect to Stripe
window.location.href = checkout_url;
// 3. Stripe redirects back to /settings/billing?session_id={id}
// 4. Page detects query param, shows success toast, invalidates queries
```

### Pattern 3: Direct API Call for Plan Changes (No Checkout)
**What:** Upgrade/downgrade and cancellation use direct Stripe API calls server-side -- no new checkout session.
**When to use:** When user already has a subscription with card on file.
**Example:**
```python
# backend: stripe.subscriptions.update() for plan change
# backend: stripe.subscriptions.update(cancel_at_period_end=True) for cancel
# Frontend shows confirmation dialog, calls POST /subscriptions/change or /subscriptions/cancel
```

### Pattern 4: Query Param Toast Pattern
**What:** After Stripe redirect, detect query params (`session_id`, `topup=success`) to show success toasts.
**When to use:** Post-payment redirect handling on billing page.
**Example:**
```typescript
// In /settings/billing page
const searchParams = useSearchParams();
useEffect(() => {
  if (searchParams.get("session_id")) {
    toast.success("Subscription activated!");
    // Clean URL by replacing without query params
    router.replace("/settings/billing");
    // Invalidate relevant queries
    queryClient.invalidateQueries({ queryKey: ["subscription"] });
    queryClient.invalidateQueries({ queryKey: ["credits"] });
  }
}, [searchParams]);
```

### Pattern 5: Established API Client Pattern
**What:** All frontend API calls go through `apiClient` from `@/lib/api-client.ts` which auto-injects auth tokens and handles refresh.
**When to use:** Every API call in this phase.

### Anti-Patterns to Avoid
- **Hardcoding pricing in frontend:** Pricing must come from backend API (platform_settings / CreditPackage table). Single source of truth.
- **Using Stripe JS packages:** Owner explicitly ruled these out. All Stripe interaction is backend-only.
- **Creating new checkout sessions for plan changes:** Upgrade/downgrade uses `stripe.subscriptions.update()` since card is already on file.
- **Showing Buy Credits to trial users:** Must be hidden (not disabled). Backend also enforces this but UI should not show the option.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Toast notifications | Custom toast component | sonner (already installed) + shadcn Sonner wrapper | Already configured in providers.tsx, used throughout app |
| Confirmation dialogs | Custom modal | shadcn AlertDialog | Handles focus trap, keyboard nav, accessibility |
| Tab navigation | Custom tab implementation | shadcn Tabs component | Already installed, handles keyboard navigation |
| Data table | Custom table markup | shadcn Table component | Consistent styling, proper semantic HTML |
| Loading states | Custom spinners | shadcn Skeleton component | Already used in project |
| Date formatting | Manual string formatting | `Intl.DateTimeFormat` or `toLocaleDateString` | Browser-native, handles locale |
| Currency formatting | Manual cent conversion | `(amount_cents / 100).toFixed(2)` with Intl.NumberFormat | Consistent display, handles locale |

**Key insight:** Every UI component needed for this phase already exists in the project's shadcn installation. No new component library installations required.

## New Backend Endpoints Required

The following endpoints do NOT exist yet and must be created:

| Endpoint | Method | Purpose | Implementation |
|----------|--------|---------|----------------|
| `/subscriptions/change` | POST | Upgrade/downgrade subscription | Calls `stripe.subscriptions.update()` with new price_id |
| `/subscriptions/cancel` | POST | Cancel subscription at period end | Calls `stripe.subscriptions.update(cancel_at_period_end=True)` |
| `/subscriptions/select-on-demand` | POST | Switch to On Demand (no Stripe) | Updates user.user_class to "on_demand", cancels any active subscription |
| `/subscriptions/plans` | GET | Return plan pricing for Plan Selection page | Reads from platform_settings + user_classes.yaml |
| `/subscriptions/billing-history` | GET | Return user's payment history | Queries PaymentHistory table for current user |
| `/credits/packages` | GET | Return available credit packages | Queries CreditPackage table (active, ordered) |

### Existing Endpoints (ready to use)
| Endpoint | Status |
|----------|--------|
| `POST /subscriptions/checkout` | Ready (Phase 57) |
| `GET /subscriptions/status` | Ready (Phase 57) |
| `POST /credits/purchase` | Ready (Phase 57) |
| `GET /credits/balance` | Ready (Phase 55) |

## Common Pitfalls

### Pitfall 1: Stripe Proration on Plan Changes
**What goes wrong:** Upgrade/downgrade proration behavior is not specified, leading to unexpected charges.
**Why it happens:** Stripe has multiple proration behaviors: `create_prorations`, `always_invoice`, `none`.
**How to avoid:** For upgrades, use `proration_behavior="create_prorations"` (Stripe default) so the user is charged the difference immediately. For downgrades, use `proration_behavior="none"` because the change takes effect at cycle end.
**Warning signs:** User is charged full price on upgrade instead of prorated difference.

### Pitfall 2: Race Condition Between Redirect and Webhook
**What goes wrong:** User lands on billing page after Stripe redirect, but webhook hasn't processed yet -- subscription data shows old state.
**Why it happens:** Stripe webhook delivery can have a slight delay after checkout completion.
**How to avoid:** After detecting `session_id` query param, show the success toast immediately (optimistic), then invalidate queries. The page will eventually show correct state when webhook processes. Consider a brief polling interval or just rely on the next React Query refetch.
**Warning signs:** User sees "No active subscription" briefly after subscribing.

### Pitfall 3: Settings Page Restructure Breaking Existing Routes
**What goes wrong:** Moving API Keys out of `/settings` page into `/settings/keys` breaks bookmarks or navigation.
**Why it happens:** The current settings page has ProfileForm, PasswordForm, AccountInfo, AND ApiKeySection all on one page.
**How to avoid:** Keep `/settings` as the default route showing Profile content. Move ApiKeySection to `/settings/keys` as a new route. Use Next.js layout.tsx to wrap all settings pages with tab navigation. The existing `/settings` URL still works -- it just shows Profile tab.
**Warning signs:** 404 errors on settings sub-pages.

### Pitfall 4: Display Name Mismatch Between "standard" and "Basic"
**What goes wrong:** Backend uses `standard` as the DB key but UI must display "Basic" to users.
**Why it happens:** Phase 55 decision: DB key is `standard`, display name is "Basic" (user_classes.yaml: `display_name: "Standard"` -- note this still says "Standard" in config but CONTEXT.md says display as "Basic").
**How to avoid:** The pricing API should return display names. Frontend should NEVER use raw tier keys for display. Use a mapping or backend-provided display names.
**Warning signs:** UI shows "Standard" instead of "Basic" to users.

### Pitfall 5: Not Invalidating Auth/User Query After Plan Change
**What goes wrong:** After subscribing or changing plan, the user object still shows the old user_class.
**Why it happens:** useAuth caches the user object. Plan changes update user_class on the backend but the frontend cache is stale.
**How to avoid:** After any plan-related action, invalidate both subscription queries AND the auth/user query so useAuth re-fetches and components like useTrialState update.
**Warning signs:** Trial banner still shows after user subscribes; Buy Credits section still hidden.

### Pitfall 6: Cancel vs Delete Confusion
**What goes wrong:** Calling `stripe.subscriptions.cancel()` immediately terminates the subscription instead of scheduling cancellation at period end.
**Why it happens:** In Stripe Python SDK v14+, `cancel()` is immediate cancellation. To schedule cancellation at period end, you must use `update()` with `cancel_at_period_end=True`.
**How to avoid:** Use `stripe.subscriptions.update(sub_id, cancel_at_period_end=True)` for the cancel flow. The actual deletion happens via Stripe at period end, which triggers the `customer.subscription.deleted` webhook (already handled in Phase 57).
**Warning signs:** User's subscription immediately terminates instead of continuing until end of cycle.

### Pitfall 7: Email Templates Missing for Webhook-Triggered Events
**What goes wrong:** Renewal confirmation emails never send because the webhook handler doesn't call the email function.
**Why it happens:** Phase 57 webhook handlers update DB state but don't send confirmation emails (only payment_failed sends email).
**How to avoid:** Add email sending to webhook handlers: `handle_checkout_completed` (new subscription + top-up), `handle_invoice_paid` (renewal). Create email template functions and call them from the appropriate handlers.
**Warning signs:** Users never receive confirmation emails for subscriptions, top-ups, or renewals.

## Code Examples

### Subscription Change Endpoint (Backend)
```python
# New endpoint in subscriptions.py
@router.post("/change")
async def change_subscription_plan(
    body: PlanChangeRequest,  # { plan_tier: "standard" | "premium" }
    db: DbSession,
    current_user: CurrentUser,
):
    # 1. Look up existing subscription
    # 2. Determine if upgrade or downgrade
    # 3. Resolve new price_id from platform_settings
    # 4. Call stripe.subscriptions.update() with:
    #    - items: [{ id: existing_item_id, price: new_price_id }]
    #    - proration_behavior: "create_prorations" (upgrade) or "none" (downgrade)
    #    - metadata: { plan_tier: new_tier }
    # 5. Update subscription metadata
    # 6. Return result with change type (upgrade/downgrade)
```

### Cancel Subscription Endpoint (Backend)
```python
@router.post("/cancel")
async def cancel_subscription(db: DbSession, current_user: CurrentUser):
    # 1. Look up active subscription
    # 2. Call stripe.subscriptions.update(sub_id, cancel_at_period_end=True)
    # 3. Update local Subscription.cancel_at_period_end = True
    # 4. Return { cancel_at: period_end_date }
```

### Plan Pricing Endpoint (Backend)
```python
@router.get("/plans")
async def get_plans(db: DbSession, current_user: CurrentUser):
    # 1. Read platform_settings for stripe_price_standard_monthly, stripe_price_premium_monthly
    # 2. Read platform_settings for subscription prices (price_standard_monthly_cents, price_premium_monthly_cents)
    # 3. Read user_classes.yaml for credit allocations
    # 4. Return structured plan data with pricing, features, credit allocations
```

### Settings Layout with Tabs (Frontend)
```typescript
// frontend/src/app/(dashboard)/settings/layout.tsx
import { SettingsNav } from "@/components/settings/SettingsNav";

export default function SettingsLayout({ children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="mx-auto max-w-4xl p-6 space-y-8">
        {/* Header + Back button */}
        <SettingsNav />
        {children}
      </div>
    </div>
  );
}
```

### Toast After Stripe Redirect (Frontend)
```typescript
"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

// Inside billing page component:
const searchParams = useSearchParams();
const router = useRouter();
const queryClient = useQueryClient();

useEffect(() => {
  if (searchParams.get("session_id")) {
    toast.success("Subscription activated!");
    router.replace("/settings/billing");
    queryClient.invalidateQueries({ queryKey: ["subscription"] });
    queryClient.invalidateQueries({ queryKey: ["credits", "balance"] });
    queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
  }
  if (searchParams.get("topup") === "success") {
    toast.success("Credits added to your balance!");
    router.replace("/settings/billing");
    queryClient.invalidateQueries({ queryKey: ["credits", "balance"] });
  }
}, []);
```

### Email Template Function (Backend)
```python
# Follow existing pattern from send_payment_failed_email
async def send_subscription_confirmation_email(
    to_email: str, first_name: str | None, plan_name: str, settings: Settings
) -> bool:
    # Same pattern: dev mode logging fallback, Jinja2 template, aiosmtplib.send
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stripe.js embedded checkout | Stripe-hosted redirect | Owner decision | No frontend Stripe packages needed |
| stripe.Subscription.cancel() | stripe.subscriptions.update(cancel_at_period_end=True) | Stripe SDK v14 | Must use update(), not cancel() for end-of-period cancellation |
| Single credit balance | Dual balance (subscription + purchased) | Phase 55 | Frontend must display both balances separately |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend) |
| Config file | backend/pyproject.toml |
| Quick run command | `cd backend && python -m pytest tests/test_subscription_service.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SUB-01 | Subscribe via plan selection | integration | `pytest tests/test_subscription_service.py -x -q` | Partial (checkout exists) |
| SUB-02 | Upgrade subscription | unit | `pytest tests/test_subscription_change.py -x -q` | Wave 0 |
| SUB-03 | Downgrade subscription | unit | `pytest tests/test_subscription_change.py -x -q` | Wave 0 |
| SUB-04 | Cancel subscription | unit | `pytest tests/test_subscription_cancel.py -x -q` | Wave 0 |
| SUB-05 | Select On Demand | unit | `pytest tests/test_subscription_change.py -x -q` | Wave 0 |
| TOPUP-01 | Credit packages available | unit | `pytest tests/test_billing_models.py -x -q` | Partial |
| TOPUP-03 | Purchase credits via Checkout | integration | `pytest tests/test_subscription_service.py -x -q` | Partial |
| TOPUP-05 | Trial users blocked | unit | `pytest tests/test_subscription_service.py -x -q` | Partial |
| BILL-05 | Billing history endpoint | unit | `pytest tests/test_billing_history.py -x -q` | Wave 0 |
| BILL-06 | Settings navigation | manual-only | Manual browser test | N/A |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_subscription_service.py tests/test_billing_models.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_subscription_change.py` -- covers SUB-02, SUB-03, SUB-05 (plan change + on-demand endpoints)
- [ ] `tests/test_subscription_cancel.py` -- covers SUB-04 (cancel endpoint)
- [ ] `tests/test_billing_history.py` -- covers BILL-05 (billing history endpoint)

## Open Questions

1. **Display name for "standard" tier**
   - What we know: DB key is `standard`, user_classes.yaml says `display_name: "Standard"`, CONTEXT.md says display as "Basic"
   - What's unclear: Should user_classes.yaml be updated to say "Basic", or should the pricing API apply its own mapping?
   - Recommendation: Update the backend pricing endpoint to return "Basic" as display_name for the `standard` tier, keeping user_classes.yaml unchanged (it serves multiple purposes). The plan pricing API is the display-name source of truth for billing pages.

2. **Subscription price storage**
   - What we know: Stripe Price IDs are in platform_settings (`stripe_price_standard_monthly`, `stripe_price_premium_monthly`). But the dollar amounts for display need to come from somewhere.
   - What's unclear: Are display prices stored in platform_settings, or should they be fetched from Stripe API?
   - Recommendation: Store display prices in platform_settings (e.g., `price_standard_monthly_cents: 2900`) alongside the Stripe Price IDs. Avoids runtime Stripe API calls for page loads. Admin can update both together.

3. **Webhook email integration timing**
   - What we know: Email sending for confirmations should happen in webhook handlers. But webhook handlers currently only update DB state (except payment_failed).
   - What's unclear: Should email sending be added directly to existing webhook handler methods, or via a separate post-processing step?
   - Recommendation: Add email sending directly in the webhook handlers (same pattern as `handle_invoice_payment_failed`). Keep it simple -- no event bus or separate workers for v1.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All source files listed in canonical_refs section of CONTEXT.md
- `backend/app/services/subscription.py` -- Full SubscriptionService with all webhook handlers
- `backend/app/routers/subscriptions.py` -- Existing checkout and status endpoints
- `backend/app/routers/credits.py` -- Existing purchase endpoint
- `backend/app/services/email.py` -- Email service pattern with Jinja2 templates
- `frontend/src/app/(dashboard)/settings/` -- Existing settings pages and plan placeholder
- `frontend/src/components/ui/` -- Full shadcn component inventory
- `frontend/src/lib/api-client.ts` -- API client pattern
- `58-UI-SPEC.md` -- Approved UI design contract

### Secondary (MEDIUM confidence)
- Stripe Python SDK v14 documentation for subscriptions.update() proration behavior

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed and in use, no new dependencies
- Architecture: HIGH - Patterns directly derived from existing codebase analysis
- Pitfalls: HIGH - Derived from actual code review (e.g., cancel vs delete, proration behavior, webhook timing)

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable -- no fast-moving dependencies)
