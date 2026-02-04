---
phase: 06-frontend-ui-interactive-data-cards
plan: 18
subsystem: ui
tags: [react, tanstack-query, error-handling, refetchInterval, try-catch-finally]

# Dependency graph
requires:
  - phase: 06-frontend-ui-interactive-data-cards (plans 06-11, 06-14, 06-15)
    provides: FileUploadZone Continue to Chat button, FileSidebar, useFiles hook
provides:
  - Fault-tolerant Continue to Chat button handler with try/catch/finally
  - Independent sidebar refresh via refetchInterval (10s fallback)
  - Sidebar error state display instead of misleading empty state
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "try/catch/finally for UI handlers that must always complete cleanup"
    - "refetchInterval as independent fallback for manual query refetch"
    - "Error state branch in conditional rendering (isLoading -> isError -> data -> empty)"

key-files:
  created: []
  modified:
    - frontend/src/components/file/FileUploadZone.tsx
    - frontend/src/components/file/FileSidebar.tsx
    - frontend/src/hooks/useFileManager.ts

key-decisions:
  - "finally block guarantees dialog close + state reset regardless of errors"
  - "exact: true on invalidateQueries/refetchQueries prevents over-refetching summary query"
  - "refetchInterval 10s balances responsiveness and network traffic"

patterns-established:
  - "try/catch/finally: UI handlers that must always cleanup use finally for guaranteed state reset"
  - "Layered error recovery: primary path (explicit refetch) + fallback (refetchInterval) + error UI (isError)"

# Metrics
duration: 2min
completed: 2026-02-04
---

# Phase 6 Plan 18: Button Handler Resilience & Sidebar Fallback Refresh Summary

**try/catch/finally on Continue to Chat handler with 10s refetchInterval fallback and sidebar error state**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-04T20:02:31Z
- **Completed:** 2026-02-04T20:03:58Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Continue to Chat button handler rewritten with try/catch/finally -- dialog always closes regardless of errors
- Removed early `return` in context POST catch block that was blocking dialog close and tab open
- Added `exact: true` to invalidateQueries/refetchQueries to prevent over-refetching the summary query
- Added refetchInterval: 10000 to useFiles for independent 10s sidebar refresh fallback
- Added isError state to FileSidebar with "Failed to load files" / "Retrying automatically..." UI

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite button handler with try/catch/finally and non-blocking context save** - `77099f9` (fix)
2. **Task 2: Add refetchInterval to useFiles and error state to FileSidebar** - `c4b751b` (feat)

## Files Created/Modified
- `frontend/src/components/file/FileUploadZone.tsx` - Rewrote Continue to Chat onClick with try/catch/finally, removed early return, added exact: true
- `frontend/src/hooks/useFileManager.ts` - Added refetchInterval: 10000 to useFiles query
- `frontend/src/components/file/FileSidebar.tsx` - Added isError destructuring and error state UI branch

## Decisions Made
- **finally block for guaranteed cleanup:** Dialog close and state reset moved to finally block so user can never get stuck in a dialog that won't close. This is the non-negotiable invariant.
- **exact: true on query operations:** Prevents refetching the summary query when only the file list needs updating. Reduces unnecessary network traffic.
- **10-second refetchInterval:** Balances responsiveness (users see files within 10s if primary refetch fails) against network traffic. Primary path (button handler explicit refetch) provides instant updates; this is purely a safety net.
- **Error state replaces misleading empty state:** When GET /files/ fails, showing "No files yet" misleads users. Error state with "Retrying automatically..." is honest and actionable (users know the system is recovering).

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Upload flow is now fully resilient to errors at every layer
- Sidebar has independent refresh capability as safety net
- Error states provide honest feedback to users
- Ready for remaining gap closure plans (06-17, 06-19) if needed

---
*Phase: 06-frontend-ui-interactive-data-cards*
*Completed: 2026-02-04*
