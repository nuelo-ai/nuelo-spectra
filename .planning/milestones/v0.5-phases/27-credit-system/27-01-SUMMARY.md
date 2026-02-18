---
phase: 27-credit-system
plan: 01
subsystem: api
tags: [credits, decimal, yaml, caching, select-for-update, pydantic]

# Dependency graph
requires:
  - phase: 26-foundation
    provides: "User model with user_class column, UserCredit and CreditTransaction models, database async session"
provides:
  - "user_classes.yaml with 5 tier definitions (free_trial, free, standard, premium, internal)"
  - "UserClassService with cached YAML loading (30s TTL)"
  - "CreditService with atomic deduction, balance queries, reset execution, admin adjustments"
  - "Pydantic schemas for all credit operations"
affects: [27-02, 27-03, 27-04]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Module-level cache with TTL for YAML config", "SELECT FOR UPDATE for atomic credit operations", "Decimal arithmetic for credit amounts"]

key-files:
  created:
    - backend/app/config/user_classes.yaml
    - backend/app/services/user_class.py
    - backend/app/services/credit.py
    - backend/app/schemas/credit.py
  modified: []

key-decisions:
  - "Sentinel value Decimal(-1) for unlimited user balance_after in transactions"
  - "Low-credit threshold: balance < 20% of tier allocation OR balance < 3, whichever triggers first"
  - "get_low_credit_users loads class configs in Python rather than SQL to keep tier allocation logic in one place"

patterns-established:
  - "YAML config with module-level TTL cache: load once, reuse for 30s"
  - "CreditService static methods following ChatService pattern"
  - "All credit arithmetic uses Python Decimal, never float"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-02-16
---

# Phase 27 Plan 01: Core Credit Service Summary

**Atomic credit deduction with SELECT FOR UPDATE, 5-tier YAML config with 30s cache, and Pydantic schemas for all credit operations**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-16T19:21:50Z
- **Completed:** 2026-02-16T19:24:05Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created user_classes.yaml with 5 tiers matching CONTEXT.md spec exactly
- Built UserClassService with 30s TTL cache for YAML loading (get_user_classes, get_class_config, get_default_class, invalidate_cache)
- Implemented CreditService with 9 public methods: deduct_credit, get_balance, admin_adjust, execute_reset, manual_reset, get_transaction_history, get_credit_distribution, get_low_credit_users, is_reset_due
- Created 5 Pydantic schemas: CreditBalanceResponse, CreditDeductionResult, CreditTransactionResponse, CreditAdjustmentRequest, CreditManualResetRequest

## Task Commits

Each task was committed atomically:

1. **Task 1: Create user_classes.yaml and UserClassService** - `35dfbd7` (feat)
2. **Task 2: Create CreditService and credit schemas** - `6e51e62` (feat)

## Files Created/Modified
- `backend/app/config/user_classes.yaml` - Tier definitions with credits, reset_policy, display_name for 5 user classes
- `backend/app/services/user_class.py` - YAML config loader with 30s TTL module-level cache
- `backend/app/services/credit.py` - CreditService with atomic deduction (SELECT FOR UPDATE), balance queries, reset execution, admin adjustments, distribution/low-credit analytics
- `backend/app/schemas/credit.py` - Pydantic models for credit balance, deduction results, transactions, adjustment/reset requests

## Decisions Made
- Used Decimal("-1") as sentinel value for unlimited users' balance_after in transactions (distinguishes from actual zero balance)
- Low-credit threshold uses dual condition: balance < 20% of tier allocation OR balance < 3 credits (whichever triggers first), matching research recommendation
- get_low_credit_users loads tier configs in Python loop rather than embedding allocation values in SQL, keeping tier allocation logic centralized in user_classes.yaml
- manual_reset sets admin_id on the transaction record after execute_reset creates it (execute_reset is shared between auto and manual resets)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CreditService is the foundation for all remaining Phase 27 plans
- Plan 02 (admin endpoints) will call admin_adjust, manual_reset, get_transaction_history, get_credit_distribution, get_low_credit_users
- Plan 03 (chat integration) will call deduct_credit and get_balance
- Plan 04 (scheduler) will call is_reset_due and execute_reset

---
*Phase: 27-credit-system*
*Completed: 2026-02-16*
