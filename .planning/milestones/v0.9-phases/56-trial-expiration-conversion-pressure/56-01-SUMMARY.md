---
phase: 56-trial-expiration-conversion-pressure
plan: 01
subsystem: auth
tags: [trial, enforcement, 402, fastapi, react-hooks]

# Dependency graph
requires:
  - phase: 55-tier-restructure
    provides: "user_class field on User model, user_classes.yaml config"
provides:
  - "Trial expiration enforcement via 402 on non-exempt API paths"
  - "_check_trial_expiration helper in dependencies.py"
  - "TRIAL_EXEMPT_PREFIXES constant for path-based exemption"
  - "check_topup_eligible guard in credits router"
  - "UserResponse with user_class and trial_expires_at fields"
  - "402 interception in api-client.ts (trial-expired event)"
  - "useTrialState hook for computed trial state"
affects: [56-02-PLAN, 57-stripe, 58-credits]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Path-based exempt prefix matching for trial enforcement"
    - "402 status code for payment-required (trial expired)"
    - "CustomEvent dispatch for cross-component communication (trial-expired)"

key-files:
  created:
    - backend/tests/test_trial.py
    - frontend/src/hooks/useTrialState.ts
  modified:
    - backend/app/dependencies.py
    - backend/app/schemas/user.py
    - backend/app/routers/credits.py
    - frontend/src/types/auth.ts
    - frontend/src/lib/api-client.ts

key-decisions:
  - "Trial check extracted to _check_trial_expiration helper used by both get_current_user and get_authenticated_user"
  - "402 interception placed before 401 handler to prevent token refresh loops on expired trials"

patterns-established:
  - "TRIAL_EXEMPT_PREFIXES: tuple of path prefixes exempt from trial enforcement"
  - "402 -> CustomEvent('trial-expired') pattern for frontend trial expiration handling"

requirements-completed: [TRIAL-01, TRIAL-02, TRIAL-03, TRIAL-07]

# Metrics
duration: 5min
completed: 2026-03-19
---

# Phase 56 Plan 01: Backend Trial Enforcement & Frontend Data Layer Summary

**Backend 402 enforcement for expired free_trial users with path-based exemptions, plus frontend UserResponse types, 402 interception, and useTrialState hook**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-19T19:06:20Z
- **Completed:** 2026-03-19T19:11:20Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Backend returns HTTP 402 for expired trial users on non-exempt API paths (single enforcement point for web, API, MCP)
- Exempt paths (/auth/*, /api/credits/balance, /admin/*, /health, /version) bypass trial check
- Frontend api-client intercepts 402 before 401 handler, dispatching trial-expired CustomEvent
- useTrialState hook computes isTrial, isExpired, daysRemaining from user data for Plan 02 UI components

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend trial enforcement (TDD RED)** - `c2f1da7` (test)
2. **Task 1: Backend trial enforcement (TDD GREEN)** - `9fea86d` (feat)
3. **Task 2: Frontend data layer** - `8578dc4` (feat)

_Note: Task 1 used TDD with separate RED and GREEN commits_

## Files Created/Modified
- `backend/tests/test_trial.py` - 11 tests covering trial enforcement, exempt paths, non-trial bypass, top-up guard
- `backend/app/dependencies.py` - _check_trial_expiration helper, TRIAL_EXEMPT_PREFIXES, Request param on get_current_user
- `backend/app/schemas/user.py` - user_class and trial_expires_at fields on UserResponse
- `backend/app/routers/credits.py` - check_topup_eligible guard function
- `frontend/src/types/auth.ts` - user_class and trial_expires_at on UserResponse interface
- `frontend/src/lib/api-client.ts` - 402 interception in fetchWithAuth and upload methods
- `frontend/src/hooks/useTrialState.ts` - Computed trial state hook (isTrial, isExpired, daysRemaining)

## Decisions Made
- Extracted trial check to `_check_trial_expiration` helper shared by both `get_current_user` and `get_authenticated_user` (DRY, single enforcement logic)
- Placed 402 interception before 401 handler in api-client to prevent token refresh loops when trial is expired

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Two pre-existing test failures (test_code_checker, test_graph_visualization) unrelated to trial changes -- no regressions from adding Request parameter to get_current_user

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend trial enforcement active -- Plan 02 can build UI components (banner, modal, sidebar badge)
- useTrialState hook ready for consumption by TrialExpirationBanner and ConversionModal components
- trial-expired CustomEvent ready for modal trigger in Plan 02

---
*Phase: 56-trial-expiration-conversion-pressure*
*Completed: 2026-03-19*
