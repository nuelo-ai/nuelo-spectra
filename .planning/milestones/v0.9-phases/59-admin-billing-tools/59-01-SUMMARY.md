---
phase: 59-admin-billing-tools
plan: 01
subsystem: api
tags: [stripe, fastapi, admin, billing, refund, discount-codes, sqlalchemy, alembic]

# Dependency graph
requires:
  - phase: 57-stripe-backend-webhook-foundation
    provides: SubscriptionService, webhook router, StripeEvent model
  - phase: 58-billing-ui-subscription-management
    provides: Subscription/PaymentHistory models, cancel/change_plan methods
provides:
  - Admin billing API endpoints (user detail, force-set-tier, cancel, refund)
  - Admin billing settings API endpoints (monetization toggle, pricing, credits)
  - DiscountCode model and migration
  - StripeEvent user_id column for per-user event filtering
  - SubscriptionService admin methods (admin_force_set_tier, admin_cancel_subscription, admin_refund)
affects: [59-02, 59-03, 59-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Admin billing router pattern with CurrentAdmin + DbSession + explicit db.commit()
    - Proportional credit deduction on refund using Decimal arithmetic
    - Force-set-tier with immediate Stripe sub cancellation (not cancel_at_period_end)
    - Billing settings with Stripe Price auto-creation on price change

key-files:
  created:
    - backend/app/routers/admin/billing.py
    - backend/app/routers/admin/billing_settings.py
    - backend/app/schemas/admin_billing.py
    - backend/app/models/discount_code.py
    - backend/alembic/versions/059_01_stripe_event_user_id_and_discount_codes.py
  modified:
    - backend/app/models/stripe_event.py
    - backend/app/models/__init__.py
    - backend/app/routers/webhooks.py
    - backend/app/routers/admin/__init__.py
    - backend/app/services/subscription.py
    - backend/app/services/platform_settings.py

key-decisions:
  - "Force-set-tier uses immediate Stripe subscription cancel (not cancel_at_period_end) for admin overrides"
  - "Admin force-set to paid tier without existing sub sets user_class locally only (no Stripe billing created)"
  - "Refund credit deduction is proportional: (refund_amount / original_amount) * original_credit_amount"
  - "Billing settings PUT auto-creates Stripe Price objects when price_cents values change"

patterns-established:
  - "Admin billing endpoints follow CurrentAdmin + DbSession + explicit db.commit() pattern"
  - "DiscountCode model includes Stripe coupon/promotion code sync fields for future Plan 02"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 59 Plan 01: Admin Billing Backend Summary

**Admin billing API with force-set-tier (Stripe sync), refund with proportional credit deduction, billing settings CRUD, and DiscountCode model**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T19:04:28Z
- **Completed:** 2026-03-24T19:09:24Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- StripeEvent model extended with user_id FK column; webhook router extracts user_id from event data
- DiscountCode model created with full Stripe coupon/promotion code sync fields
- Admin billing router with 4 endpoints: user billing detail, force-set-tier, admin cancel, refund
- Admin billing settings router with GET/PUT for monetization config, trial credits, pricing
- Three admin service methods on SubscriptionService with full Stripe integration and audit logging
- Platform settings extended with monetization_enabled, trial_credits, credits_standard/premium_monthly

## Task Commits

Each task was committed atomically:

1. **Task 1: Database migrations + models + StripeEvent user_id extraction** - `ce9b399` (feat)
2. **Task 2: Admin billing router + billing settings router + service methods + schemas** - `b827c13` (feat)

## Files Created/Modified
- `backend/app/models/stripe_event.py` - Added user_id FK column for per-user event filtering
- `backend/app/models/discount_code.py` - New DiscountCode model with Stripe sync fields
- `backend/app/models/__init__.py` - Registered DiscountCode in model exports
- `backend/alembic/versions/059_01_stripe_event_user_id_and_discount_codes.py` - Migration for user_id column and discount_codes table
- `backend/app/routers/webhooks.py` - Extract user_id from webhook event data into StripeEvent rows
- `backend/app/schemas/admin_billing.py` - All request/response schemas for admin billing
- `backend/app/routers/admin/billing.py` - Admin billing endpoints (detail, force-set-tier, cancel, refund)
- `backend/app/routers/admin/billing_settings.py` - Billing settings GET/PUT with Stripe Price auto-creation
- `backend/app/routers/admin/__init__.py` - Registered billing and billing_settings routers
- `backend/app/services/subscription.py` - Added admin_force_set_tier, admin_cancel_subscription, admin_refund
- `backend/app/services/platform_settings.py` - Added billing keys and validation rules

## Decisions Made
- Force-set-tier uses immediate Stripe subscription cancel (not cancel_at_period_end) for admin overrides -- admin actions should take effect immediately
- Admin force-set to paid tier without existing subscription sets user_class locally only (no Stripe billing created) -- admin override does not create billing obligations
- Refund credit deduction uses proportional Decimal arithmetic: (refund_amount / original_amount) * original_credit_amount
- Billing settings PUT auto-creates Stripe Price objects when price_cents values change, deactivates old prices

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Import verification requires DATABASE_URL and SECRET_KEY env vars (not available in worktree). Used AST syntax validation and schema-only imports as alternative verification. All syntax valid and patterns confirmed present.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Admin billing backend API complete; ready for Plan 02 (discount code CRUD endpoints)
- Plan 03 (admin billing frontend) can consume these endpoints
- Plan 04 (billing settings UI) can consume billing-settings endpoints

## Self-Check: PASSED

All 12 files verified present. Both task commits (ce9b399, b827c13) verified in git log.

---
*Phase: 59-admin-billing-tools*
*Completed: 2026-03-24*
