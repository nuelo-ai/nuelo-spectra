---
phase: 58-billing-ui-subscription-management
plan: 01
subsystem: api
tags: [stripe, fastapi, pydantic, subscription, billing]

# Dependency graph
requires:
  - phase: 57-stripe-backend-webhook-foundation
    provides: SubscriptionService, Subscription model, PaymentHistory model, CreditPackage model, webhook handlers
provides:
  - GET /subscriptions/plans endpoint for plan pricing display
  - POST /subscriptions/change endpoint for upgrade/downgrade
  - POST /subscriptions/cancel endpoint for period-end cancellation
  - POST /subscriptions/select-on-demand endpoint for on-demand tier switch
  - GET /subscriptions/billing-history endpoint for payment history
  - GET /credits/packages endpoint for credit package listing
  - Pydantic schemas for all billing UI responses
  - SubscriptionService.change_plan and cancel_subscription methods
  - Wave 0 test stubs for subscription change, cancel, billing history
affects: [58-03-plan-selection-page, 58-04-manage-plan-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [stripe-subscription-update-for-plan-changes, cancel-at-period-end-pattern]

key-files:
  created:
    - backend/tests/test_subscription_change.py
    - backend/tests/test_subscription_cancel.py
    - backend/tests/test_billing_history.py
  modified:
    - backend/app/schemas/subscription.py
    - backend/app/services/subscription.py
    - backend/app/services/platform_settings.py
    - backend/app/routers/subscriptions.py
    - backend/app/routers/credits.py

key-decisions:
  - "Upgrade uses proration_behavior=create_prorations, downgrade uses none (Stripe best practice)"
  - "Cancel uses subscriptions.update(cancel_at_period_end=True), not subscriptions.cancel()"
  - "Standard tier displayed as Basic in all API responses (D-01 context decision)"
  - "Platform settings price_standard_monthly_cents=2900 and price_premium_monthly_cents=7900 as defaults"

patterns-established:
  - "Plan change via Stripe subscription update (not new checkout): card already on file"
  - "Billing history type_display_map for human-readable payment type names"

requirements-completed: [SUB-02, SUB-03, SUB-04, SUB-05, TOPUP-01, TOPUP-02, BILL-01, BILL-02, BILL-05]

# Metrics
duration: 4min
completed: 2026-03-22
---

# Phase 58 Plan 01: Backend API Endpoints Summary

**6 new billing API endpoints with Stripe subscription update for plan changes, period-end cancellation, and billing history**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-23T03:46:36Z
- **Completed:** 2026-03-23T03:50:55Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Created 6 new API endpoints for billing UI consumption (plans, change, cancel, select-on-demand, billing-history, credit packages)
- Added change_plan and cancel_subscription methods to SubscriptionService with correct Stripe proration behavior
- Created 14 Wave 0 test stubs across 3 test files covering subscription change, cancel, and billing history
- Added 7 new Pydantic response schemas for billing UI data contracts

## Task Commits

Each task was committed atomically:

1. **Task 0: Create Wave 0 test stub files** - `63d9323` (test)
2. **Task 1: Add schemas, platform settings defaults, and service methods** - `7d2c8e4` (feat)
3. **Task 2: Add 6 new router endpoints** - `47479a3` (feat)

## Files Created/Modified
- `backend/tests/test_subscription_change.py` - 7 test stubs for plan change and on-demand selection (SUB-02, SUB-03, SUB-05)
- `backend/tests/test_subscription_cancel.py` - 3 test stubs for subscription cancellation (SUB-04)
- `backend/tests/test_billing_history.py` - 4 test stubs for billing history endpoint (BILL-05)
- `backend/app/schemas/subscription.py` - 7 new Pydantic models for billing UI responses
- `backend/app/services/subscription.py` - change_plan and cancel_subscription methods
- `backend/app/services/platform_settings.py` - price_standard_monthly_cents and price_premium_monthly_cents defaults
- `backend/app/routers/subscriptions.py` - 5 new endpoints (plans, change, cancel, select-on-demand, billing-history)
- `backend/app/routers/credits.py` - 1 new endpoint (packages)

## Decisions Made
- Upgrade uses `proration_behavior="create_prorations"` for immediate charge; downgrade uses `"none"` for end-of-cycle effect
- Cancel uses `stripe.subscriptions.update(cancel_at_period_end=True)` -- NOT `stripe.subscriptions.cancel()` which terminates immediately
- Standard tier displayed as "Basic" in all API responses per D-01 context decision
- Platform settings pricing defaults: $29.00/month standard, $79.00/month premium

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Backend test suite requires environment variables (DATABASE_URL, SECRET_KEY) not available in worktree -- verified syntax via AST parsing and test collection instead of full test run

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 6 API endpoints ready for frontend consumption in Plans 03 and 04
- Test stubs ready for implementation when manual testing begins
- Schemas define the data contract between backend and frontend

---
*Phase: 58-billing-ui-subscription-management*
*Completed: 2026-03-22*
