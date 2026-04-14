---
status: resolved
phase: 58-billing-ui-subscription-management
source: [58-VERIFICATION.md]
started: 2026-03-23T00:00:00Z
updated: 2026-03-24T00:00:00Z
---

## Current Test

[all tests complete]

## Tests

### 1. Plan Selection page renders with live pricing
expected: Open /settings/plan as a free trial user. Three plan cards visible, On Demand / Basic / Premium labels shown with prices from backend, Basic card has Most Popular badge and left border, your plan has Current Plan badge with disabled button. No hardcoded prices.
result: passed

### 2. Subscribe redirects to Stripe hosted checkout
expected: Click Subscribe on Basic as a new user with no subscription. Browser navigates to checkout.stripe.com hosted checkout page (not an embedded form on page).
result: passed

### 3. Upgrade confirmation dialog with proration messaging
expected: As a subscribed user (standard), click Upgrade to Premium. AlertDialog appears with exact prorated amount from Stripe before request is sent.
result: passed

### 4. Cancel Plan confirmation and pending cancellation state
expected: Click Cancel Plan on /settings/billing. Confirmation AlertDialog appears. After confirming, plan status card reflects cancel_at_period_end state.
result: passed

### 5. Post-Stripe redirect toast and URL cleanup
expected: After returning from Stripe checkout (session_id query param), "Subscription activated!" toast shown once, then URL changes to /settings/billing with no query params.
result: passed

### 6. Trial users cannot see Buy Credits section
expected: Log in as a free_trial user. Navigate to /settings/billing and verify Credit packages section is completely hidden.
result: passed

### 7. Confirmation emails in dev mode
expected: Complete a subscription checkout with SMTP not configured. Server logs show "SUBSCRIPTION CONFIRMED (Dev Mode)" with plan name and amount.
result: skipped — SMTP configured in environment, dev mode not testable without disabling SMTP

## Summary

total: 7
passed: 6
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

Fixes applied during UAT:
- Stripe SDK v14 compatibility (v1 namespace, period dates from items)
- Missing db.commit() in router endpoints (credit reset was rolling back)
- Repair migration for partially-applied billing tables
- Proration preview endpoint using Stripe create_preview API
- always_invoice proration behavior for immediate charging
- Separate Plan/Billing nav tabs
- Post-upgrade page refresh fix (window.location.href)
- Processing state in upgrade dialog
- On-demand switch confirmation dialog with detailed explanation
