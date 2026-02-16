---
phase: 29-user-management
plan: 02
subsystem: api
tags: [fastapi, token-invalidation, account-actions, admin, audit]

# Dependency graph
requires:
  - phase: 29-01
    provides: "Admin user listing, detail, and activity endpoints"
  - phase: 27-03
    provides: "CreditService with admin_adjust method"
  - phase: 28-01
    provides: "Admin tier change service (change_user_tier)"
provides:
  - "Admin account action endpoints: activate, deactivate, password reset, tier change, credit adjustment"
  - "In-memory token invalidation mechanism for immediate logout on deactivation"
  - "ActivateDeactivateResponse, PasswordResetTriggerResponse, CreditAdjustRequest schemas"
affects: [29-03, admin-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns: [in-memory-revocation-set, thread-safe-ttl-dict]

key-files:
  created: []
  modified:
    - backend/app/dependencies.py
    - backend/app/services/admin/users.py
    - backend/app/schemas/admin_users.py
    - backend/app/routers/admin/users.py

key-decisions:
  - "In-memory revocation set with TTL (30 min) for immediate token invalidation on deactivation"
  - "Revocation check placed before DB lookup in get_current_user to avoid unnecessary queries"
  - "trigger_password_reset reuses existing forgot-password flow (same token, email, expiry)"
  - "Tier change and credit adjustment reuse existing services directly in router (no duplication)"

patterns-established:
  - "Thread-safe in-memory revocation: _deactivation_lock + dict[UUID, float] with TTL cleanup"
  - "Account action endpoints follow: service call -> audit log -> commit -> return response"

requirements-completed: [USER-09, USER-10, USER-11, USER-12]

# Metrics
duration: 2min
completed: 2026-02-16
---

# Phase 29 Plan 02: Account Actions Summary

**Admin account action endpoints with in-memory token revocation for immediate logout, password reset trigger via existing SMTP flow, and tier/credit management reusing existing services**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-16T22:19:17Z
- **Completed:** 2026-02-16T22:21:43Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- In-memory deactivation set with thread-safe TTL cleanup for immediate token invalidation
- Revocation check in get_current_user() intercepts deactivated users before DB lookup
- Five account action endpoints: deactivate, activate, password-reset, tier change, credit adjustment
- All actions audit-logged with admin ID, target user, and client IP

## Task Commits

Each task was committed atomically:

1. **Task 1: Token invalidation mechanism and account action service functions** - `5d3eff3` (feat)
2. **Task 2: Add account action endpoints to the admin users router** - `fa8d7fa` (feat)

## Files Created/Modified

- `backend/app/dependencies.py` - Added mark_user_deactivated, clear_user_deactivation, is_user_deactivated functions and revocation check in get_current_user
- `backend/app/services/admin/users.py` - Added deactivate_user, activate_user, trigger_password_reset service functions
- `backend/app/schemas/admin_users.py` - Added ActivateDeactivateResponse, PasswordResetTriggerResponse, CreditAdjustRequest schemas
- `backend/app/routers/admin/users.py` - Added 5 account action endpoints with audit logging

## Decisions Made

- Used in-memory dict with threading lock (not Redis) for token revocation -- consistent with existing patterns (_reset_cooldowns, _login_attempts) and single-instance deployment
- Revocation check placed before DB lookup to save a query for deactivated users
- trigger_password_reset invalidates existing active tokens before creating new one (same as forgot-password flow)
- Reused TierChangeRequest from platform_settings schemas rather than creating duplicate
- Reused CreditBalanceResponse from credit schemas for credit adjustment response

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added existing token invalidation in trigger_password_reset**
- **Found during:** Task 1 (trigger_password_reset implementation)
- **Issue:** Plan didn't mention invalidating existing active reset tokens before creating a new one
- **Fix:** Added UPDATE to set is_active=False on existing tokens for the user's email (same pattern as forgot-password endpoint)
- **Files modified:** backend/app/services/admin/users.py
- **Verification:** Follows same pattern as auth.py forgot_password endpoint
- **Committed in:** 5d3eff3 (Task 1 commit)

**2. [Rule 3 - Blocking] Passed Settings to trigger_password_reset**
- **Found during:** Task 1 (trigger_password_reset implementation)
- **Issue:** Plan signature had `frontend_base_url` string param, but send_password_reset_email requires full Settings object for SMTP config
- **Fix:** Changed signature to accept Settings object, used settings.frontend_url for the link
- **Files modified:** backend/app/services/admin/users.py, backend/app/routers/admin/users.py
- **Verification:** Import and route registration verified successfully
- **Committed in:** 5d3eff3 and fa8d7fa

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness and compatibility with existing email flow. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All account action endpoints operational, ready for admin frontend integration (plan 03)
- 8 total admin user endpoints now available (list, detail, activity + 5 actions)
- Token invalidation mechanism ready for production use

---
*Phase: 29-user-management*
*Completed: 2026-02-16*
