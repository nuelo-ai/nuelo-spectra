---
phase: 59-admin-billing-tools
plan: 02
subsystem: api
tags: [stripe, fastapi, admin, discount-codes, coupons, promotion-codes]

# Dependency graph
requires:
  - phase: 59-admin-billing-tools-01
    provides: DiscountCode model, migration, SubscriptionService admin methods
provides:
  - Discount code CRUD service with Stripe Coupon + Promotion Code sync
  - Admin discount code management endpoints (list, create, update, deactivate, delete)
  - Promotion code entry enabled in Stripe Checkout sessions
affects: [59-03, 59-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Stripe Coupon + Promotion Code dual-create pattern for discount codes
    - allow_promotion_codes in Stripe Checkout for user-facing code entry

key-files:
  created:
    - backend/app/services/discount_code.py
    - backend/app/schemas/discount_code.py
    - backend/app/routers/admin/discount_codes.py
  modified:
    - backend/app/routers/admin/__init__.py
    - backend/app/services/subscription.py

key-decisions:
  - "Stripe Coupon duration is 'forever' for percent_off and 'once' for amount_off"
  - "Stripe Promotion Code expires_at cannot be updated after creation -- update locally only with warning log"
  - "allow_promotion_codes: True added to both subscription and top-up checkout sessions"

patterns-established:
  - "Discount code CRUD follows same CurrentAdmin + DbSession + explicit db.commit() pattern as billing endpoints"
  - "Stripe Coupon + Promotion Code always created as a pair per D-21"

requirements-completed: [ADMIN-08, ADMIN-09, ADMIN-10]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 59 Plan 02: Discount Code Backend Summary

**Discount code CRUD service with Stripe Coupon + Promotion Code sync and Checkout promotion code entry**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T19:13:21Z
- **Completed:** 2026-03-24T19:17:01Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- DiscountCodeService with full CRUD: create (Stripe Coupon + Promo Code sync), list, update, deactivate (Stripe sync), delete (Stripe cleanup + DB removal)
- Admin discount code router with 5 endpoints: GET list, POST create, PUT update, POST deactivate, DELETE
- Schemas with input validation (code pattern, discount type enum, positive values)
- Both subscription and top-up Stripe Checkout sessions now show promotion code entry field

## Task Commits

Each task was committed atomically:

1. **Task 1: Discount code service + schemas + router** - `43fdeb9` (feat)
2. **Task 2: Enable promotion codes in Stripe Checkout sessions** - `ad9146b` (feat)

## Files Created/Modified
- `backend/app/schemas/discount_code.py` - Create/Update/Response/List schemas with Pydantic validation
- `backend/app/services/discount_code.py` - DiscountCodeService with Stripe Coupon + Promotion Code sync
- `backend/app/routers/admin/discount_codes.py` - Admin CRUD endpoints with audit logging
- `backend/app/routers/admin/__init__.py` - Registered discount_codes router
- `backend/app/services/subscription.py` - Added allow_promotion_codes to both checkout methods

## Decisions Made
- Stripe Coupon duration set to "forever" for percent_off (applies to all invoices) and "once" for amount_off (one-time discount)
- Stripe Promotion Code expires_at is immutable after creation; local update logged as warning but saved locally for admin reference
- Delete operation deactivates Stripe Promotion Code before deleting Stripe Coupon, then removes DB row

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] subscription.py not present in worktree branch**
- **Found during:** Task 2
- **Issue:** The worktree branch diverged before subscription.py was added; file not tracked
- **Fix:** Checked out subscription.py from feature/v0.1-milestone branch, then applied the allow_promotion_codes changes
- **Files modified:** backend/app/services/subscription.py
- **Verification:** grep confirms 2 occurrences of allow_promotion_codes
- **Committed in:** ad9146b

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to bring file into worktree. No scope creep.

## Issues Encountered
- Plan 01 commits not in this worktree (parallel execution). Cherry-pick attempted but had conflicts due to branch divergence. Resolved by working with worktree's current __init__.py state and checking out subscription.py from feature branch. The orchestrator will merge all worktree branches.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Discount code backend API complete; ready for Plan 03 (admin billing frontend)
- Plan 04 (billing settings UI) has full backend support
- Stripe Checkout sessions now accept promotion codes for user-facing discount application

## Self-Check: PASSED

All 5 files verified present. Both task commits (43fdeb9, ad9146b) verified in git log.

---
*Phase: 59-admin-billing-tools*
*Completed: 2026-03-24*
