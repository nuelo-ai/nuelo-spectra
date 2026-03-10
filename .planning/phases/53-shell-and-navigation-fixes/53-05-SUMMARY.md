---
phase: 53-shell-and-navigation-fixes
plan: 05
subsystem: ui
tags: [react, nextjs, shadcn, sidebar, navigation]

# Dependency graph
requires:
  - phase: 53-01
    provides: SidebarTrigger pattern established in WorkspacePage and MyFilesPage

provides:
  - SidebarTrigger visible in CollectionDetailPage header
  - SidebarTrigger visible in DetectionResultsPage header (all 4 render states)
  - SidebarTrigger visible in ReportDetailPage sticky header (all 3 render states)
  - Sidebar nav icon alignment corrected — pl-1 removed, shadcn p-2 default restored

affects:
  - Phase 53-06 visual verification
  - LBAR-01 gap closed
  - LBAR-02 gap closed

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SidebarTrigger added as first child in all workspace sub-view headers (matching pattern from WorkspacePage)
    - pl-1 child padding anti-pattern removed from asChild nav items

key-files:
  created: []
  modified:
    - frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx
    - frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
    - frontend/src/app/(workspace)/workspace/collections/[id]/reports/[reportId]/page.tsx
    - frontend/src/components/sidebar/UnifiedSidebar.tsx

key-decisions:
  - "LBAR-01: SidebarTrigger added to all render states (loading, error, empty, normal) so toggle is always visible regardless of page state"
  - "LBAR-02: Removed pl-1 entirely from Link and anchor asChild children — shadcn cva p-2 default is the correct sole padding source for icon alignment"
  - "Report view: used -ml-1 mr-3 on loading/error state SidebarTrigger to maintain spacing consistency with flex-row header layout"

patterns-established:
  - "SidebarTrigger as first element in header strip, matching WorkspacePage: <SidebarTrigger className=\"-ml-1\" />"
  - "All render states of a page must include SidebarTrigger to ensure toggle visibility during error/loading/empty conditions"

requirements-completed: [LBAR-01, LBAR-02]

# Metrics
duration: 3min
completed: 2026-03-10
---

# Phase 53 Plan 05: Shell and Navigation Fixes — LBAR Gap Closure Summary

**SidebarTrigger added to all three workspace sub-view pages across all render states, and pl-1 nav child padding removed to restore clean icon alignment in expanded and collapsed sidebar modes**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-10T14:33:54Z
- **Completed:** 2026-03-10T14:36:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- CollectionDetailPage restructured with flex-col layout: SidebarTrigger strip above scrollable content (matching WorkspacePage pattern)
- DetectionResultsPage updated across all 4 render states (loading, error, empty, normal) — toggle visible regardless of page state
- ReportDetailPage updated across all 3 render states (loading, error, normal) — toggle visible in all sticky header configurations
- UnifiedSidebar nav icon alignment fixed by removing pl-1 competing padding from Link and anchor asChild children

## Task Commits

1. **Task 1: Add SidebarTrigger to collection, signal, and report views (LBAR-01)** - `6e9249b` (feat)
2. **Task 2: Remove pl-1 from sidebar nav item children (LBAR-02)** - `4dd429f` (fix)

## Files Created/Modified

- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` — Added SidebarTrigger import, restructured return to flex-col with header strip above scrollable content
- `frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx` — Added SidebarTrigger import and rendered in all 4 header states
- `frontend/src/app/(workspace)/workspace/collections/[id]/reports/[reportId]/page.tsx` — Added SidebarTrigger import and rendered in all 3 sticky header states
- `frontend/src/components/sidebar/UnifiedSidebar.tsx` — Removed className="pl-1" from anchor and Link asChild children (lines 120, 142)

## Decisions Made

- Added SidebarTrigger to all render states (not just the happy path) so the toggle persists during loading, error, and empty states
- Used flex items-center gap-3 layout on signals error/empty headers to accommodate SidebarTrigger alongside existing Link element
- Used -ml-1 mr-3 on report loading/error states to preserve header spacing in non-justify-between layout
- Removed pl-1 entirely rather than replacing with an alternative — lets shadcn's p-2 default be the single source of truth for padding

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- LBAR-01 and LBAR-02 gaps from 53-04 verification are now closed
- Ready for Phase 53-06 human visual verification of toggle and icon alignment in all three sub-views
- Build exits 0 with no TypeScript errors

---
*Phase: 53-shell-and-navigation-fixes*
*Completed: 2026-03-10*

## Self-Check: PASSED

- All 4 modified source files exist on disk
- SUMMARY.md exists at expected path
- Task commits 6e9249b and 4dd429f confirmed in git log
