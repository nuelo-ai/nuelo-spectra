---
phase: 55-tier-restructure-data-foundation
plan: 02
subsystem: api
tags: [credits, dual-balance, tier-gating, registration, pydantic]

# Dependency graph
requires:
  - phase: 55-01
    provides: "purchased_balance column on UserCredit, balance_pool on CreditTransaction, trial_expires_at on User, updated user_classes.yaml"
provides:
  - "Dual-balance CreditService: subscription-first deduction, LIFO refund, sub-only reset"
  - "CreditBalanceResponse with purchased_balance and total_balance"
  - "Registration sets trial_expires_at for free_trial users"
  - "Tier gating tests updated for on_demand tier (no free tier references)"
affects: [56-stripe-integration, 57-webhook-billing, credit-purchase-flow]

# Tech tracking
tech-stack:
  added: []
  patterns: ["dual-balance deduction (subscription first, purchased second)", "LIFO refund to purchased_balance", "balance_pool tracking on CreditTransaction"]

key-files:
  created:
    - backend/tests/test_credit_dual_balance.py
  modified:
    - backend/app/services/credit.py
    - backend/app/schemas/credit.py
    - backend/app/services/auth.py
    - backend/tests/test_tier_gating.py
    - backend/tests/test_user_classes_workspace.py

key-decisions:
  - "Refund LIFO: all refunds go to purchased_balance (simplest LIFO implementation)"
  - "Admin adjust targets subscription pool only (balance_pool=subscription)"
  - "is_low calculation uses total (subscription + purchased) for accuracy"

patterns-established:
  - "Dual-balance deduction: always consume subscription first, purchased second"
  - "Balance pool tracking: every CreditTransaction records balance_pool (subscription/purchased/split)"
  - "Trial expiration: read trial_duration_days from class config, not hardcoded"

requirements-completed: [TIER-04, TIER-05, TIER-06, TIER-07, TIER-08]

# Metrics
duration: 6min
completed: 2026-03-18
---

# Phase 55 Plan 02: Credit Service & Registration Summary

**Dual-balance CreditService with subscription-first deduction, LIFO refund, trial-aware registration, and updated tier gating tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-18T16:27:19Z
- **Completed:** 2026-03-18T16:33:35Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- CreditService refactored for dual-balance: deduction consumes subscription credits first, then purchased
- Refund uses LIFO pattern -- credits returned to purchased_balance
- Credit reset only resets subscription balance, purchased_balance untouched
- CreditBalanceResponse schema extended with purchased_balance and total_balance fields
- Registration now sets trial_expires_at for free_trial users from class config
- All tier gating tests updated to use on_demand instead of removed free tier

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor CreditService for dual-balance and update schema** (TDD)
   - `8a95609` (test) - Failing tests for dual-balance CreditService
   - `907b481` (feat) - Dual-balance CreditService implementation
2. **Task 2: Update registration for trial expiration and fix tier gating tests** - `b7f1b65` (feat)

## Files Created/Modified
- `backend/app/services/credit.py` - Dual-balance deduction, LIFO refund, balance_pool on all transactions
- `backend/app/schemas/credit.py` - CreditBalanceResponse with purchased_balance and total_balance
- `backend/app/services/auth.py` - trial_expires_at set during registration, purchased_balance=0 on UserCredit
- `backend/tests/test_credit_dual_balance.py` - 8 tests covering deduction, refund, reset, balance query
- `backend/tests/test_tier_gating.py` - Updated from free tier to on_demand, added on_demand workspace test
- `backend/tests/test_user_classes_workspace.py` - Updated tier list from free to on_demand with correct values

## Decisions Made
- Refund LIFO: all refunds go to purchased_balance (simplest LIFO implementation matching the plan)
- Admin adjust targets subscription pool only with balance_pool="subscription"
- is_low calculation uses total (subscription + purchased) instead of just subscription balance
- Decimal conversion in refund to prevent float/Decimal type mismatch

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed float/Decimal type mismatch in refund**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** `user_credit.purchased_balance += amount` fails when purchased_balance is float and amount is Decimal
- **Fix:** Changed to `user_credit.purchased_balance = Decimal(str(user_credit.purchased_balance)) + amount`
- **Files modified:** backend/app/services/credit.py
- **Verification:** test_refund_to_purchased_balance passes
- **Committed in:** 907b481

**2. [Rule 1 - Bug] Updated test_user_classes_workspace.py for removed free tier**
- **Found during:** Task 2 (overall test verification)
- **Issue:** Tests referenced `free` tier which was removed in Plan 01 YAML changes, causing pre-existing failures
- **Fix:** Updated tier lists from free to on_demand with correct values
- **Files modified:** backend/tests/test_user_classes_workspace.py
- **Verification:** All 4 workspace config tests pass
- **Committed in:** b7f1b65

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dual-balance credit system is fully operational
- Registration creates trial-aware users with proper credit initialization
- All modified tests pass (20 tests across 3 test files)
- Ready for Phase 56 (Stripe integration) which will use purchased_balance for credit purchases

---
*Phase: 55-tier-restructure-data-foundation*
*Completed: 2026-03-18*
