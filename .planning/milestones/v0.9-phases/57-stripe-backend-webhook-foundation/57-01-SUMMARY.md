---
phase: 57-stripe-backend-webhook-foundation
plan: 01
subsystem: payments
tags: [stripe, pydantic, email, proxy, exceptions]

# Dependency graph
requires:
  - phase: 55-tier-restructure-dual-balance
    provides: subscription model, user class tiers, dual-balance credit system
provides:
  - Stripe SDK v14.x installed and importable
  - Settings with stripe_secret_key and stripe_webhook_secret
  - Custom Stripe exception classes (StripeConfigError, StripeWebhookError, PaymentError, CheckoutValidationError)
  - Pydantic schemas for checkout requests/responses
  - Platform settings with Stripe price ID keys
  - Next.js proxy Stripe-Signature header forwarding
  - Payment failure email templates (HTML + text)
  - send_payment_failed_email function
  - Test scaffolds for webhook and subscription service tests
affects: [57-02-PLAN, 57-03-PLAN]

# Tech tracking
tech-stack:
  added: [stripe>=14.0.0]
  patterns: [custom exception hierarchy for Stripe ops, payment email template pattern]

key-files:
  created:
    - backend/app/exceptions/__init__.py
    - backend/app/exceptions/stripe.py
    - backend/app/schemas/subscription.py
    - backend/app/templates/email/payment_failed.html
    - backend/app/templates/email/payment_failed.txt
    - backend/tests/test_webhook.py
    - backend/tests/test_subscription_service.py
  modified:
    - backend/pyproject.toml
    - backend/app/config.py
    - backend/app/services/platform_settings.py
    - backend/app/services/email.py
    - frontend/src/app/api/[...slug]/route.ts

key-decisions:
  - "Stripe SDK pinned to v14.x (>=14.0.0,<15.0) for API stability"
  - "Payment failed email follows exact same pattern as password_reset email (HTML + txt, dev mode console fallback)"

patterns-established:
  - "Stripe exception hierarchy: StripeConfigError, StripeWebhookError, PaymentError, CheckoutValidationError"
  - "Platform settings for Stripe price IDs: stripe_price_standard_monthly, stripe_price_premium_monthly"

requirements-completed: [STRIPE-01, SUB-06]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 57 Plan 01: Stripe Foundation Summary

**Stripe SDK v14.x with config, exception classes, Pydantic schemas, proxy header fix, payment email templates, and 22 test scaffolds**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T20:05:10Z
- **Completed:** 2026-03-20T20:08:36Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Stripe Python SDK v14.4.1 installed and importable with version pin
- Settings class extended with stripe_secret_key and stripe_webhook_secret fields
- Custom exception hierarchy for all Stripe payment operations
- Pydantic schemas for subscription checkout, top-up checkout, and status responses
- Platform settings extended with Stripe price ID keys for standard/premium tiers
- Next.js API proxy now forwards Stripe-Signature header to backend
- Payment failure email templates (HTML + plaintext) matching existing email design
- send_payment_failed_email function with dev-mode console fallback
- 22 test stubs scaffolded across webhook and subscription service test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Stripe SDK, config, exceptions, schemas, and platform settings** - `c4c1531` (feat)
2. **Task 2: Proxy header fix, email templates, and test scaffolds** - `5381074` (feat)

## Files Created/Modified
- `backend/pyproject.toml` - Added stripe>=14.0.0 dependency
- `backend/app/config.py` - Added stripe_secret_key and stripe_webhook_secret Settings fields
- `backend/app/exceptions/__init__.py` - New exceptions package
- `backend/app/exceptions/stripe.py` - StripeConfigError, StripeWebhookError, PaymentError, CheckoutValidationError
- `backend/app/schemas/subscription.py` - SubscriptionCheckoutRequest, TopupCheckoutRequest, CheckoutResponse, SubscriptionStatusResponse
- `backend/app/services/platform_settings.py` - Added stripe_price_standard_monthly and stripe_price_premium_monthly defaults
- `frontend/src/app/api/[...slug]/route.ts` - Added Stripe-Signature header forwarding
- `backend/app/services/email.py` - Added send_payment_failed_email function
- `backend/app/templates/email/payment_failed.html` - HTML payment failed email template
- `backend/app/templates/email/payment_failed.txt` - Plaintext payment failed email template
- `backend/tests/test_webhook.py` - 14 test stubs for webhook handlers (STRIPE-04 through STRIPE-10)
- `backend/tests/test_subscription_service.py` - 8 test stubs for subscription service (STRIPE-01 through STRIPE-03)

## Decisions Made
- Stripe SDK pinned to v14.x (>=14.0.0,<15.0) for API stability
- Payment failed email follows exact same pattern as password_reset email (HTML + txt, dev mode console fallback)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Stripe API keys will be needed when Plans 02-03 are executed.

## Next Phase Readiness
- All Stripe foundations in place for Plan 02 (SubscriptionService + webhook router)
- Exception classes, schemas, config fields, and test scaffolds ready to use
- Pre-existing test failures (test_code_checker, test_graph_visualization, etc.) are unrelated to this plan

---
*Phase: 57-stripe-backend-webhook-foundation*
*Completed: 2026-03-20*
