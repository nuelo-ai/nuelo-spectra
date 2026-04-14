# Phase 59: Admin Billing Tools - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 59-admin-billing-tools
**Areas discussed:** User billing detail view, Tier override & refund workflows, Billing platform settings, Discount code management, Monetization master switch

---

## User Billing Detail View

### Tab structure

| Option | Description | Selected |
|--------|-------------|----------|
| Single Billing tab | One new tab with stacked sections: subscription status, payment history, Stripe events. 5 tabs total. | ✓ |
| Split into two tabs | Separate Subscription and Payments tabs. 6 tabs total. | |
| Extend Overview tab | Add billing summary to Overview, separate Billing tab for details. | |

**User's choice:** Single Billing tab
**Notes:** Keeps tab count manageable at 5.

### Stripe event log format

| Option | Description | Selected |
|--------|-------------|----------|
| Human-readable timeline | Clean activity feed with expandable Stripe event IDs | |
| Raw Stripe events | Table of webhook events: event type, timestamp, processing status | ✓ |
| Both views with toggle | Default human-readable with toggle to raw events | |

**User's choice:** Raw Stripe events
**Notes:** Admin wants technical visibility into webhook processing.

### Subscription card actions

| Option | Description | Selected |
|--------|-------------|----------|
| Force-set tier button | Opens dialog with tier selector + reason field | ✓ |
| Cancel subscription button | Admin cancels user's subscription directly | ✓ |
| View in Stripe button | Link to Stripe Dashboard customer page | ✓ |
| Initiate refund | User added — refund action from subscription card | ✓ |

**User's choice:** All four actions
**Notes:** User specifically added "Initiate refund" as a 4th action beyond the presented options.

---

## Tier Override & Refund Workflows

### Tier override Stripe sync

| Option | Description | Selected |
|--------|-------------|----------|
| Local override only | DB-only change, admin handles Stripe separately | |
| Sync with Stripe | Force-set also triggers Stripe actions (cancel/create/update sub) | ✓ |
| Local override + warning | DB change with warning about Stripe state mismatch | |

**User's choice:** Sync with Stripe
**Notes:** Full automation — tier change in admin should cascade to Stripe subscription state.

### Refund selection UI

| Option | Description | Selected |
|--------|-------------|----------|
| Refund button per payment row | Each row has Refund action, opens dialog with amount | ✓ |
| Separate refund form | Standalone section/dialog for refund processing | |
| Inline refund in payment row | Expand row for inline refund form | |

**User's choice:** Refund button per payment row
**Notes:** Pre-fills full amount, option for partial.

### Refund credit handling

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-deduct credits | Credits removed proportionally on refund | ✓ |
| Manual credit adjustment | Two-step: refund money, then separately adjust credits | |
| Auto-deduct with override | Auto-calculated but admin can edit before confirming | |

**User's choice:** Auto-deduct credits
**Notes:** Keeps credit/payment relationship in sync automatically.

---

## Billing Platform Settings

### Monetization master switch behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Freeze state, hide billing UI | Existing subs stay, billing UI hidden for new actions | ✓ (modified) |
| Downgrade all to Free Trial | Cancel all subs, move everyone to Free Trial | |
| Admin assigns tiers manually | Manual tier assignment when monetization off | |

**User's choice:** Freeze state with modification — existing subscribers can still cancel their plan (cancel flow remains active)
**Notes:** User specified that plan cancellation should remain available even when monetization is disabled.

### New user tier when monetization disabled

| Option | Description | Selected |
|--------|-------------|----------|
| Free Trial (same as now) | New users get Free Trial with configured duration/credits | ✓ |
| Admin-configured default tier | Separate setting for default tier when monetization off | |
| On Demand (no trial) | Skip trial, go straight to On Demand | |

**User's choice:** Free Trial (same as now)
**Notes:** No behavior change for new user registration regardless of monetization switch state.

### Settings UI location

| Option | Description | Selected |
|--------|-------------|----------|
| Extend existing settings page | Add Billing section to SettingsForm.tsx | |
| Separate Billing Settings page | New admin route for billing config | ✓ |
| Tabbed settings page | Convert settings to tabs: General, Billing | |

**User's choice:** Separate Billing Settings page
**Notes:** Keeps billing config isolated from general platform settings.

### Price source of truth

| Option | Description | Selected |
|--------|-------------|----------|
| Admin UI editable | Prices in Spectra DB, synced to Stripe | ✓ |
| Stripe Dashboard is source | Read-only display of Stripe prices | |
| Hybrid | Credits in admin, dollar prices in Stripe | |

**User's choice:** Admin UI editable
**Notes:** Single source of truth in Spectra. Backend syncs to Stripe Products/Prices API.

---

## Discount Code Management

### Discount types

| Option | Description | Selected |
|--------|-------------|----------|
| Percentage off subscription | e.g., 20% off monthly price | ✓ |
| Fixed amount off subscription | e.g., $5 off monthly price | ✓ |
| Free credits bonus | Bonus credits on redemption (Spectra-only) | |
| Free trial extension | Extends trial_expires_at | |

**User's choice:** Percentage off and fixed amount off subscriptions only
**Notes:** Stripe-native coupon types only. Free credits and trial extension deferred.

### Discount UI structure

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated Discount Codes page | New admin route with table + create dialog | ✓ |
| Section in Billing Settings | Inline within Billing Settings page | |
| Discount Codes tab in settings | Tab alongside existing settings | |

**User's choice:** Dedicated Discount Codes page
**Notes:** Separate page with full table, create/edit/deactivate/delete actions.

### Usage limits and expiry

| Option | Description | Selected |
|--------|-------------|----------|
| Both limits + expiry | Max redemptions + optional expiration date | ✓ |
| Limits only, no expiry | Max redemptions, active until deactivated | |
| No limits | Active until manually deactivated | |

**User's choice:** Both limits + expiry
**Notes:** Maps to Stripe coupon max_redemptions and redeem_by fields.

### Redemption point

| Option | Description | Selected |
|--------|-------------|----------|
| During Stripe Checkout | Code field on Stripe-hosted checkout page | ✓ |
| On Plan Selection page | Custom code entry before checkout redirect | |
| Both checkout and plan page | Code entry at both points | |

**User's choice:** During Stripe Checkout
**Notes:** Minimal frontend work — Stripe handles validation. Pass allow_promotion_codes to Checkout Session.

---

## Claude's Discretion

- Billing tab section ordering, spacing, and visual hierarchy
- Payment history and Stripe event table columns, pagination, filtering
- Refund dialog layout and validation
- Billing Settings page form layout and field grouping
- Discount Codes table columns, sorting, empty state
- Loading states and error handling for all new pages
- Admin navigation placement for new pages

## Deferred Ideas

- Free credits bonus discount codes (Spectra-only, not Stripe coupon)
- Trial extension discount codes
- Annual billing
- Multi-currency support
