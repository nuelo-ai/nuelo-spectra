---
status: complete
phase: 59-admin-billing-tools
source: [59-01-SUMMARY.md, 59-02-SUMMARY.md, 59-03-SUMMARY.md, 59-04-SUMMARY.md]
started: 2026-03-25T20:00:00Z
updated: 2026-03-26T03:52:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Billing Tab — Subscribed User
expected: Admin → Users → subscribed user → Billing tab. Subscription card shows standard/active. Payment history shows subscription payment. Action buttons visible.
result: pass

### 2. Billing Tab — Free Trial User
expected: Admin → Users → free trial user → Billing tab. Empty state for subscription, payments, and Stripe events.
result: pass

### 3. Force Set Tier (admin override)
expected: Force Set Tier to Standard with reason. Tier changes. No Stripe subscription created for admin override.
result: pass

### 4. Admin Cancel Subscription
expected: Cancel Subscription from Billing tab. Stripe shows scheduled cancellation.
result: pass

### 5. Refund Payment
expected: Refund button enabled on payment row with stripe_payment_intent_id. Dialog shows pre-filled amount and credit deduction preview. Refund succeeds in Stripe.
result: pass

### 6. Billing Settings — Load and Save
expected: Page shows monetization toggle and subscription pricing only. Save works with success toast and persists on refresh.
result: pass

### 7. Create Discount Code
expected: Create code TEST50, Percentage Off, 50. Row appears in table. Stripe Coupon + Promotion Code created.
result: pass

### 8. Edit Discount Code
expected: Edit dialog — code/type/value disabled, max_redemptions/expires_at editable. Save updates table.
result: pass

### 9. Deactivate Discount Code
expected: Status changes to inactive. Stripe Promotion Code deactivated.
result: pass

### 10. Delete Discount Code
expected: Row disappears. Stripe Coupon deleted.
result: pass

### 11. Promotion Code at Checkout
expected: Stripe Checkout page shows "Add promotion code" input. Code applies discount.
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none — all gaps resolved]

## Fixes Applied During UAT

1. Dropped trial_duration_days, trial_credits, credits_standard_monthly, credits_premium_monthly from platform_settings (YAML is source of truth)
2. Stripe SDK v14: promotion code coupon param nested in promotion object
3. Billing settings toggle snap-back (stale query cache → use mutation response)
4. Delete discount code 204 No Content response handling
5. Trial banner persistence (sessionStorage → component state only)
6. Monetization toggle wired to public frontend (via /credits/balance response + useMonetization hook)
7. Subscribers keep Billing tab when monetization off (per D-13), but Change Plan and Buy Credits hidden
8. Payment_intent extraction via invoice.payments API (Stripe API 2026-02-25 moved from top-level)
