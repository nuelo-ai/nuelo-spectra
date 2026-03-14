---
phase: 52-admin-and-qa
plan: 02
subsystem: ui
tags: [react, nextjs, tanstack-query, typescript, admin-portal, credits]

requires:
  - phase: 52-01
    provides: GET /api/credit-costs endpoint returning { chat, pulse_run } from platform_settings
provides:
  - Admin Portal Credits card with Pulse Detection Cost per Run field (configurable via Save)
  - useCreditCosts() TanStack Query hook in workspace frontend
  - Collection detail page using live credit cost from /api/credit-costs (no hardcoded constant)
affects:
  - collection-detail-page
  - admin-settings
  - credit-display

tech-stack:
  added: []
  patterns:
    - "useCreditCosts follows useCredits pattern: useQuery with staleTime, no refetchInterval"
    - "Loading state via isLoadingCreditCosts: spinner in header badge, fallback ?? 0 for number props"

key-files:
  created:
    - frontend/src/hooks/useCreditCosts.ts
  modified:
    - admin-frontend/src/types/settings.ts
    - admin-frontend/src/components/settings/SettingsForm.tsx
    - frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx

key-decisions:
  - "useCreditCosts path is /credit-costs (not /api/credit-costs) because apiClient auto-prepends BASE_URL=/api"
  - "Loading fallback: header badge shows Loader2 spinner; OverviewStatCards.creditsUsed and RerunDetectionDialog.creditCost use ?? 0 to satisfy number prop type"

patterns-established:
  - "Credit cost display: always guard undefined with loading state in UI text, ?? 0 for number-typed props"

requirements-completed:
  - ADMIN-01
  - ADMIN-02

duration: ~35min (across two sessions including human verify)
completed: 2026-03-09
---

# Phase 52 Plan 02: Admin and QA — Frontend Credit Cost Wiring Summary

**Admin Portal Credits card extended with Pulse Detection Cost per Run field; useCreditCosts() hook replaces hardcoded CREDIT_COST=5 constant in collection detail page with live /api/credit-costs data**

## Performance

- **Duration:** ~35 min (two sessions — tasks 1-2 in first, human verify in second)
- **Started:** 2026-03-09T17:18:32Z
- **Completed:** 2026-03-09T17:34:02Z
- **Tasks:** 3 of 3 complete
- **Files modified:** 4

## Accomplishments
- Extended `PlatformSettings` interface with `workspace_credit_cost_pulse: number`
- Added Pulse Detection Cost per Run input to Admin Portal Settings Credits card with state, validation, and save payload
- Created `useCreditCosts()` hook following the `useCredits` pattern (staleTime 5min)
- Removed `const CREDIT_COST = 5` from collection detail page; all 4 usages replaced with `creditCosts?.pulse_run`
- Header badge shows spinner while loading — no NaN or undefined shown to user

## Task Commits

Each task was committed atomically:

1. **Task 1: Admin frontend — add workspace_credit_cost_pulse to settings type and form** - `c3733e9` (feat)
2. **Task 2: Workspace frontend — useCreditCosts hook and replace CREDIT_COST constant** - `d854c41` (feat)
3. **Task 3: Human verify — admin settings form and live credit cost display** - checkpoint approved (no code commit; items 1, 2, 3, 5, 6 confirmed; item 4 loading state near-realtime so not isolatable in testing)

**Plan metadata:** `fdd2d49` (docs: complete admin credit cost wiring plan at checkpoint)

## Files Created/Modified
- `admin-frontend/src/types/settings.ts` - Added `workspace_credit_cost_pulse: number` to PlatformSettings
- `admin-frontend/src/components/settings/SettingsForm.tsx` - pulseCreditCost state, useEffect sync, validation, payload, Credits card UI field
- `frontend/src/hooks/useCreditCosts.ts` - New hook exporting `useCreditCosts()` and `CreditCosts` interface
- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` - Removed CREDIT_COST constant, added useCreditCosts hook, loading state in header badge

## Decisions Made
- `useCreditCosts` uses path `/credit-costs` (not `/api/credit-costs`) because `apiClient` auto-prepends `BASE_URL = "/api"` in `fetchWithAuth`. The existing `useCredits.ts` pattern was examined and its `/api/credits/balance` path is an existing inconsistency in that file, not the norm.
- `OverviewStatCards.creditsUsed` and `RerunDetectionDialog.creditCost` are typed as `number` (not `number | undefined`), so `?? 0` fallback used while loading. Header badge has full loading UI (Loader2 spinner).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript type error for number | undefined props**
- **Found during:** Task 2 (frontend TypeScript compilation)
- **Issue:** `creditsUsed` and `creditCost` props are typed as `number`, but `creditCosts?.pulse_run` resolves to `number | undefined`. TypeScript rejected the assignment.
- **Fix:** Added `?? 0` fallback for both prop sites. Header badge already uses full loading state so it doesn't need a fallback.
- **Files modified:** `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`
- **Verification:** `npx tsc --noEmit` passes with zero errors
- **Committed in:** d854c41 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — type bug)
**Impact on plan:** Necessary for TypeScript correctness. No scope creep. Loading state still behaves as planned.

## Issues Encountered
- Pre-existing test failures in `test_pulse_agent.py`, `test_pulse_service.py`, `test_routing.py`, `test_user_classes_workspace.py` (25 failures, 233 passing). These are unrelated to credit costs and were present before this plan. Credit cost tests all pass (3/3).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ADMIN-01 and ADMIN-02 fully complete: admin can configure Pulse Detection Cost per Run via Admin Portal; workspace frontend reads live value from /api/credit-costs
- `useCreditCosts()` hook is available for any future component that needs credit cost display
- Phase 52 Admin and QA is now complete — ready for v0.8 release or next phase work

---
*Phase: 52-admin-and-qa*
*Completed: 2026-03-09*
