---
phase: 28-platform-config
plan: 02
subsystem: api
tags: [fastapi, signup-gating, invite-only, tier-change, platform-settings, frontend]

requires:
  - phase: 28-platform-config/01
    provides: PlatformSettingsService, admin settings/tiers endpoints, TierSummaryResponse schema
  - phase: 27-credit-system
    provides: CreditService.execute_reset, UserCredit model, credit transaction logging
  - phase: 26-admin-auth
    provides: CurrentAdmin dependency, admin_router, audit logging
provides:
  - Admin tier change endpoint (PUT /api/admin/tiers/users/{user_id}) with atomic credit reset
  - Public signup-status endpoint (GET /auth/signup-status)
  - Signup gating with invite_token validation when public signup disabled
  - Runtime-configurable default_credit_cost in chat flow
  - Runtime-configurable default_user_class in signup flow
  - Frontend invite-only registration page with branded message
affects: [29-admin-dashboard, 30-admin-frontend]

tech-stack:
  added: []
  patterns: [invite-token-sha256-validation, platform-settings-lazy-import, fail-open-frontend-display]

key-files:
  created:
    - backend/app/services/admin/tiers.py
  modified:
    - backend/app/routers/admin/tiers.py
    - backend/app/routers/auth.py
    - backend/app/services/auth.py
    - backend/app/schemas/auth.py
    - backend/app/schemas/platform_settings.py
    - backend/app/routers/chat.py
    - frontend/src/app/(auth)/register/page.tsx

key-decisions:
  - "Invite token validated via SHA-256 hash lookup against Invitation model (same pattern as password reset tokens)"
  - "Frontend fails open on signup-status fetch error (shows form rather than blocking)"
  - "Unlimited tier uses Decimal('-1') sentinel balance instead of numeric allocation"

patterns-established:
  - "Lazy import of platform_settings in endpoints to avoid circular imports"
  - "Invite validation: hash token, query Invitation with status=pending and not expired, mark accepted"

requirements-completed: [TIER-04, TIER-06, SIGNUP-01, SIGNUP-02, SIGNUP-03, SIGNUP-04]

duration: 2min
completed: 2026-02-16
---

# Phase 28 Plan 02: Tier Change, Signup Gating & Configurable Settings Summary

**Admin tier change with atomic credit reset, invite-only signup gating (backend + frontend), and runtime-configurable credit cost and default tier**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-16T20:54:12Z
- **Completed:** 2026-02-16T20:56:30Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Admin tier change endpoint atomically updates user_class and resets credit balance to new tier allocation
- Public signup-status endpoint and backend signup gating with invite_token validation
- Frontend registration page conditionally shows branded invite-only message
- Chat credit cost and default user class now read from platform_settings at runtime

## Task Commits

Each task was committed atomically:

1. **Task 1: Admin tier change endpoint and signup gating in backend** - `b446ef6` (feat)
2. **Task 2: Frontend registration page invite-only mode** - `e32e8e5` (feat)

## Files Created/Modified
- `backend/app/services/admin/tiers.py` - change_user_tier service with atomic credit reset
- `backend/app/routers/admin/tiers.py` - Added PUT /tiers/users/{user_id} endpoint with audit logging
- `backend/app/routers/auth.py` - Added GET /signup-status public endpoint and signup gating logic
- `backend/app/services/auth.py` - create_user now accepts optional default_class parameter
- `backend/app/schemas/auth.py` - Added invite_token field to SignupRequest
- `backend/app/schemas/platform_settings.py` - Added TierChangeRequest schema
- `backend/app/routers/chat.py` - Credit cost reads from platform_settings instead of hardcoded value
- `frontend/src/app/(auth)/register/page.tsx` - Signup status check on mount, invite-only message display

## Decisions Made
- Invite token validated via SHA-256 hash (consistent with password reset token pattern)
- Frontend fails open on signup-status fetch error to avoid blocking legitimate users
- Unlimited tiers get Decimal("-1") sentinel balance (consistent with existing CreditService pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All platform config APIs complete, ready for admin dashboard frontend (phase 29/30)
- Tier management, signup gating, and settings endpoints are fully operational
- Frontend registration page responds to runtime setting changes

---
*Phase: 28-platform-config*
*Completed: 2026-02-16*
