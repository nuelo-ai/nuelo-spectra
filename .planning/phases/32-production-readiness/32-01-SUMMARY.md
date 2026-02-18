---
phase: 32-production-readiness
plan: 01
subsystem: api, ui
tags: [fetch, api-client, settings, pydantic, next-js-rewrite]

# Dependency graph
requires:
  - phase: 31-dashboard-admin-frontend
    provides: "Admin frontend settings UI, invite flow, tier management"
provides:
  - "Production-safe relative /api URLs in frontend api-client and invite page"
  - "Clean settings API contract without credit_reset_policy"
  - "Minimal tiers router with only GET endpoint"
affects: [deployment, staging]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BASE_URL constant for all API calls in frontend api-client"

key-files:
  created: []
  modified:
    - frontend/src/lib/api-client.ts
    - frontend/src/app/(auth)/invite/[token]/page.tsx
    - backend/app/schemas/platform_settings.py
    - backend/app/services/platform_settings.py
    - admin-frontend/src/types/settings.ts
    - backend/app/routers/admin/tiers.py

key-decisions:
  - "Use BASE_URL constant rather than env var for API base path"
  - "Leave orphaned credit_reset_policy DB rows in place -- harmless, no migration needed"
  - "Keep TierChangeRequest schema class in platform_settings.py even though tiers.py no longer imports it"

patterns-established:
  - "BASE_URL = /api: all frontend fetch calls use relative paths via Next.js rewrite proxy"

requirements-completed: [INVITE-04, INVITE-05, SETTINGS-05]

# Metrics
duration: 3min
completed: 2026-02-17
---

# Phase 32 Plan 01: Production Readiness Gap Closure Summary

**Replaced hardcoded localhost URLs with relative /api paths, removed misleading credit_reset_policy from settings API, and deleted dead PUT tier route**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-18T03:22:35Z
- **Completed:** 2026-02-18T03:25:25Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- All frontend API calls now use relative `/api` paths via Next.js rewrite proxy -- works in all environments
- Settings API contract cleaned: `credit_reset_policy` removed from response, request, validation, and defaults
- Dead `PUT /api/admin/tiers/users/{user_id}` route removed with full import cleanup
- Three requirements closed: INVITE-04, INVITE-05, SETTINGS-05

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix hardcoded localhost in api-client.ts and invite page** - `f753ade` (fix)
2. **Task 2: Remove credit_reset_policy from settings schema, service, and frontend type** - `ce5b6c7` (fix)
3. **Task 3: Remove dead PUT /api/admin/tiers/users/{user_id} route** - `b0da049` (fix)

## Files Created/Modified
- `frontend/src/lib/api-client.ts` - Added BASE_URL="/api" constant, replaced all localhost:8000 refs
- `frontend/src/app/(auth)/invite/[token]/page.tsx` - Fixed two fetch calls to use relative /api URLs
- `backend/app/schemas/platform_settings.py` - Removed credit_reset_policy from SettingsResponse and SettingsUpdateRequest
- `backend/app/services/platform_settings.py` - Removed credit_reset_policy from DEFAULTS and validate_setting()
- `admin-frontend/src/types/settings.ts` - Removed credit_reset_policy from PlatformSettings interface
- `backend/app/routers/admin/tiers.py` - Removed dead PUT endpoint and cleaned up unused imports

## Decisions Made
- Used `BASE_URL = "/api"` constant rather than environment variable -- simpler, Next.js rewrite handles env-specific routing
- Left orphaned `credit_reset_policy` rows in DB -- Pydantic v2 SettingsResponse silently ignores extra keys, no migration needed
- Kept `TierChangeRequest` schema class in `platform_settings.py` even though `tiers.py` no longer imports it -- harmless and avoids unnecessary churn

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed upload retry URL inconsistency**
- **Found during:** Task 1
- **Issue:** Upload retry on line 211 used `/api${path}` while initial request used `http://localhost:8000${path}` -- inconsistent URL patterns
- **Fix:** Normalized to `${BASE_URL}${path}` for consistency with all other fetch calls
- **Files modified:** frontend/src/lib/api-client.ts
- **Committed in:** f753ade (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Auto-fix was explicitly noted in the plan as a consistency improvement. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three production-blocking gaps are closed
- App is deployable to staging/production without localhost hacks
- Settings API contract is clean and well-defined

---
*Phase: 32-production-readiness*
*Completed: 2026-02-17*
