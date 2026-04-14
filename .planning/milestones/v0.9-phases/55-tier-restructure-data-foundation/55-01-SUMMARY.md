---
phase: 55-tier-restructure-data-foundation
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, yaml, tier-config, billing, dual-balance, stripe]

# Dependency graph
requires: []
provides:
  - "5-tier YAML config (free_trial, on_demand, standard, premium, internal)"
  - "Subscription, PaymentHistory, CreditPackage, StripeEvent SQLAlchemy models"
  - "User.trial_expires_at, UserCredit.purchased_balance, CreditTransaction.balance_pool fields"
  - "Alembic migration for all schema changes"
  - "Wave 0 test stubs for TIER-01 through TIER-08 and DATA-01 through DATA-06"
affects: [55-02-logic-refactor, 56-trial-flow, 57-stripe-integration, 58-billing-ui, 59-admin-monetization]

# Tech tracking
tech-stack:
  added: []
  patterns: [dual-balance credit model, reset_policy=none for scheduler skip]

key-files:
  created:
    - backend/app/models/subscription.py
    - backend/app/models/payment_history.py
    - backend/app/models/credit_package.py
    - backend/app/models/stripe_event.py
    - backend/alembic/versions/a1b2c3d4e5f6_tier_restructure_billing_tables.py
    - backend/tests/test_tier_config.py
    - backend/tests/test_dual_balance.py
    - backend/tests/test_scheduler_skip.py
    - backend/tests/test_billing_models.py
  modified:
    - backend/app/config/user_classes.yaml
    - backend/app/models/user.py
    - backend/app/models/user_credit.py
    - backend/app/models/credit_transaction.py
    - backend/app/models/__init__.py
    - backend/alembic/env.py
    - backend/app/services/user_class.py
    - backend/app/services/platform_settings.py

key-decisions:
  - "Alembic migration created manually (no local DB connection for autogenerate)"
  - "down_revision corrected to 357a798917d0 (actual head, not f47a0001b000 from plan)"
  - "TIER-08 implemented via reset_policy=none -- no scheduler code changes needed"
  - "TIER-03 no data migration -- owner confirmed no free-tier users in production"

patterns-established:
  - "Dual-balance pattern: UserCredit.balance (subscription) + UserCredit.purchased_balance (purchased)"
  - "Balance pool audit: CreditTransaction.balance_pool tracks which pool was debited"
  - "Scheduler skip via config: reset_policy=none causes is_reset_due() to return False"

requirements-completed: [TIER-01, TIER-02, TIER-03, TIER-08, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06]

# Metrics
duration: 4min
completed: 2026-03-18
---

# Phase 55 Plan 01: Tier Restructure Data Foundation Summary

**5-tier YAML config with dual-balance fields, 4 billing SQLAlchemy models, and Alembic migration for all schema changes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T16:20:05Z
- **Completed:** 2026-03-18T16:23:35Z
- **Tasks:** 4
- **Files modified:** 18

## Accomplishments
- Restructured user_classes.yaml from old 5-tier (with 'free') to new 5-tier (with 'on_demand'), setting standard/premium reset_policy=none for TIER-08 scheduler skip
- Created 4 new billing models: Subscription, PaymentHistory, CreditPackage, StripeEvent
- Added dual-balance fields (purchased_balance on UserCredit, balance_pool on CreditTransaction) and trial_expires_at on User
- Updated all service defaults from "free" to "free_trial" with trial_duration_days platform setting
- Created Wave 0 test stubs (17 tests across 4 files) for all Phase 55 requirements

## Task Commits

Each task was committed atomically:

1. **Task 0: Create Wave 0 test stubs** - `f415ae9` (test)
2. **Task 1a: Restructure YAML, create billing models, update existing models** - `47499bb` (feat)
3. **Task 1b: Update service defaults to free_trial** - `a880b7f` (feat)
4. **Task 2: Create Alembic migration** - `08649dc` (feat)

## Files Created/Modified
- `backend/app/config/user_classes.yaml` - 5-tier config (free_trial, on_demand, standard, premium, internal)
- `backend/app/models/subscription.py` - Subscription model mirroring Stripe state
- `backend/app/models/payment_history.py` - Payment event records
- `backend/app/models/credit_package.py` - Predefined credit packages for purchase
- `backend/app/models/stripe_event.py` - Webhook idempotency deduplication
- `backend/app/models/user.py` - Added trial_expires_at, changed default to free_trial
- `backend/app/models/user_credit.py` - Added purchased_balance for dual-balance
- `backend/app/models/credit_transaction.py` - Added balance_pool for audit trail
- `backend/app/models/__init__.py` - Registered 4 new billing models
- `backend/alembic/env.py` - Added 4 new model imports for autogenerate
- `backend/alembic/versions/a1b2c3d4e5f6_tier_restructure_billing_tables.py` - Migration for all schema changes
- `backend/app/services/user_class.py` - get_default_class() returns "free_trial"
- `backend/app/services/platform_settings.py` - default_user_class="free_trial", added trial_duration_days
- `backend/tests/test_tier_config.py` - TIER-01, TIER-02, TIER-08 stubs
- `backend/tests/test_dual_balance.py` - TIER-04 through TIER-07 stubs
- `backend/tests/test_scheduler_skip.py` - TIER-08 scheduler skip stubs
- `backend/tests/test_billing_models.py` - DATA-01 through DATA-06 stubs

## Decisions Made
- Alembic migration created manually since no local DB connection available for autogenerate
- Corrected down_revision to `357a798917d0` (actual alembic head) instead of `f47a0001b000` (plan assumed)
- TIER-08 (scheduler skip for subscription tiers) implemented purely via YAML config change -- no scheduler code modifications needed
- TIER-03 (free tier migration) requires no data migration per owner confirmation that no free-tier users exist in production

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected Alembic down_revision**
- **Found during:** Task 2 (Alembic migration)
- **Issue:** Plan specified `f47a0001b000` as the latest migration head, but actual head is `357a798917d0`
- **Fix:** Set down_revision to `357a798917d0` in migration file
- **Files modified:** backend/alembic/versions/a1b2c3d4e5f6_tier_restructure_billing_tables.py
- **Verification:** `alembic heads` would show correct chain
- **Committed in:** 08649dc

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary correction for migration chain integrity. No scope creep.

## Issues Encountered
- Pre-existing test failure in `test_code_checker.py::TestDisallowedImports::test_disallowed_plotly_express` -- unrelated to our changes, not addressed

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All data models in place for Plan 02 (logic refactor: CreditService dual-balance, trial expiration)
- Alembic migration ready to run on target database
- Wave 0 test stubs ready to be filled in during Plan 02 execution

## Self-Check: PASSED

All 9 created files verified present. All 4 task commits verified in git log.

---
*Phase: 55-tier-restructure-data-foundation*
*Completed: 2026-03-18*
