---
phase: 56-trial-expiration-conversion-pressure
plan: 02
subsystem: ui
tags: [trial, banner, overlay, conversion, react, next.js, tailwind]

# Dependency graph
requires:
  - phase: 56-trial-expiration-conversion-pressure
    plan: 01
    provides: "useTrialState hook, UserResponse types, 402 interception, trial enforcement"
provides:
  - "TrialBanner component with days remaining, credit balance, amber urgency, and dismiss"
  - "TrialExpiredOverlay component blocking dashboard/workspace for expired trial users"
  - "Placeholder /settings/plan page with 3 tier cards (On Demand, Basic, Premium)"
  - "Layout integration in both (dashboard) and (workspace) route groups"
affects: [57-stripe, 58-credits]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "usePathname-based self-hiding for overlay on /settings/* paths"
    - "sessionStorage dismiss pattern for per-session banner dismissal"
    - "flex-col wrapper in layout for banner above main content"

key-files:
  created:
    - frontend/src/components/trial/TrialBanner.tsx
    - frontend/src/components/trial/TrialExpiredOverlay.tsx
    - frontend/src/app/(dashboard)/settings/plan/page.tsx
  modified:
    - frontend/src/app/(dashboard)/layout.tsx
    - frontend/src/app/(workspace)/layout.tsx
    - backend/app/dependencies.py
    - backend/app/routers/credits.py
    - frontend/src/hooks/useCredits.ts

key-decisions:
  - "TrialExpiredOverlay uses usePathname to self-hide on /settings/* paths rather than separate layout"
  - "Banner shows immediately without waiting for credit balance (null-safe rendering)"
  - "Credits router prefix corrected from /api/credits to /credits (proxy strips /api)"

patterns-established:
  - "Trial components in frontend/src/components/trial/ directory"
  - "Layout flex-col wrapper pattern for banner + main content in route group layouts"
  - "Overlay self-hiding via pathname check for selective blocking"

requirements-completed: [TRIAL-04, TRIAL-05, TRIAL-06]

# Metrics
duration: ~15min
completed: 2026-03-20
---

# Phase 56 Plan 02: Trial UI Components & Layout Integration Summary

**Trial banner with days/credits and amber urgency on all authenticated pages, blocking overlay for expired users (except settings), and placeholder plan page with 3 tier cards**

## Performance

- **Duration:** ~15 min (across checkpoint boundary)
- **Started:** 2026-03-19T19:15:00Z
- **Completed:** 2026-03-20T11:14:25Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- TrialBanner component shows days remaining and credit balance for active trial users on all authenticated pages
- TrialExpiredOverlay blocks dashboard and workspace for expired trial users, while allowing settings access
- Placeholder /settings/plan page with On Demand, Basic, Premium tier cards and Coming Soon buttons
- Fixed API URL double-prefix bugs found during visual verification

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TrialBanner and TrialExpiredOverlay components** - `7111436` (feat)
2. **Task 2: Layout integration and placeholder /settings/plan page** - `3f6b506` (feat)
3. **Task 3: Visual verification fixes** - `e9fe07c` (fix)

## Files Created/Modified
- `frontend/src/components/trial/TrialBanner.tsx` - Sticky trial banner with days remaining, credit balance, amber urgency at <=3 days or <=10 credits, session-dismissible
- `frontend/src/components/trial/TrialExpiredOverlay.tsx` - Full blocking overlay with View Plans and Log Out, self-hides on /settings/* via usePathname
- `frontend/src/app/(dashboard)/settings/plan/page.tsx` - Placeholder plan page with 3 tier cards (On Demand, Basic, Premium) and Coming Soon buttons
- `frontend/src/app/(dashboard)/layout.tsx` - Added TrialBanner and TrialExpiredOverlay to dashboard layout (covers settings pages too)
- `frontend/src/app/(workspace)/layout.tsx` - Added TrialBanner and TrialExpiredOverlay to workspace layout
- `backend/app/dependencies.py` - Fixed TRIAL_EXEMPT_PREFIXES paths, removed duplicate /api/version entry
- `backend/app/routers/credits.py` - Fixed router prefix from /api/credits to /credits
- `frontend/src/hooks/useCredits.ts` - Fixed credit fetch URL from /api/credits/balance to /credits/balance

## Decisions Made
- TrialExpiredOverlay uses `usePathname()` to self-hide on `/settings/*` paths, keeping both dashboard and settings under the same layout without needing separate overlay logic
- Banner renders immediately without waiting for credit balance to load (null-safe rendering with conditional credit display), improving perceived load time
- Credits router prefix corrected from `/api/credits` to `/credits` since the Next.js proxy already adds the `/api` prefix when forwarding to the backend

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] API URL double-prefix on credits endpoints**
- **Found during:** Task 3 (visual verification)
- **Issue:** apiClient.get("/api/credits/balance") resulted in double /api prefix since apiClient already prepends /api
- **Fix:** Changed URL to "/credits/balance" in TrialBanner, useCredits hook, and backend credits router prefix
- **Files modified:** frontend/src/components/trial/TrialBanner.tsx, frontend/src/hooks/useCredits.ts, backend/app/routers/credits.py
- **Verification:** Credit balance loads correctly in trial banner
- **Committed in:** e9fe07c

**2. [Rule 1 - Bug] TRIAL_EXEMPT_PREFIXES had wrong path for credits**
- **Found during:** Task 3 (visual verification)
- **Issue:** Exempt prefix "/api/credits/balance" didn't match actual backend path "/credits/balance", causing 402 on credits endpoint for expired trial users
- **Fix:** Updated to "/credits/balance", removed duplicate "/api/version" entry
- **Files modified:** backend/app/dependencies.py
- **Verification:** Expired trial users can still fetch credit balance
- **Committed in:** e9fe07c

**3. [Rule 1 - Bug] Banner blocked on null creditBalance guard**
- **Found during:** Task 3 (visual verification)
- **Issue:** Banner returned null when creditBalance===null (during async fetch), so banner never appeared until credits loaded
- **Fix:** Removed creditBalance===null guard, made credit display conditional with null check
- **Files modified:** frontend/src/components/trial/TrialBanner.tsx
- **Verification:** Banner shows immediately with days remaining, credits appear when loaded
- **Committed in:** e9fe07c

---

**Total deviations:** 3 auto-fixed (3 bugs)
**Impact on plan:** All fixes necessary for correct operation. No scope creep.

## Issues Encountered
- DB migration for purchased_balance column and 4 billing tables needed to be applied manually during testing (migration file already existed from Phase 55, just not applied to local dev DB)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Complete trial lifecycle UI is functional: banner, overlay, plan page
- Ready for Phase 57 (Stripe integration) to replace Coming Soon buttons with actual payment flows
- Credits endpoint paths now consistent across frontend and backend

## Self-Check: PASSED

All 5 key files verified present. All 3 task commits verified in git log.

---
*Phase: 56-trial-expiration-conversion-pressure*
*Completed: 2026-03-20*
