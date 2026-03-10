---
phase: 43-collections-reports
plan: 01
subsystem: ui
tags: [react, nextjs, shadcn, tabs, mock-data, collections]

# Dependency graph
requires:
  - phase: 42-analysis-workspace
    provides: SignalCard component, collection page base, DetectionLoading, FileTable, StickyActionBar, FileUploadZone, DataSummaryPanel
provides:
  - Four-tab collection detail page (Overview | Files | Signals | Reports)
  - Report and ActivityItem TypeScript types in mock-data.ts
  - MOCK_REPORTS (3 entries with full markdown content)
  - MOCK_ACTIVITY (5 entries)
  - OverviewStatCards component (4-card stat row)
  - ActivityFeed component (vertical timeline)
  - RunDetectionBanner component (CTA banner)
  - "Credits used" header pill on collection detail
affects: 43-02-report-reader, 43-03-signals-tab, future plans importing MOCK_REPORTS or MOCK_ACTIVITY

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Controlled Tabs with value+onValueChange for cross-tab navigation from Overview
    - Pass isSelected=false/onSelect=noop to SignalCard when used in non-interactive link context
    - Filter MOCK_* arrays by collectionId at the page level for scoped data

key-files:
  created:
    - pulse-mockup/src/components/workspace/overview-stat-cards.tsx
    - pulse-mockup/src/components/workspace/activity-feed.tsx
    - pulse-mockup/src/components/workspace/run-detection-banner.tsx
  modified:
    - pulse-mockup/src/lib/mock-data.ts
    - pulse-mockup/src/app/workspace/collections/[id]/page.tsx

key-decisions:
  - "Pass isSelected=false and onSelect no-op to SignalCard in Overview/Signals tabs since those contexts use Link navigation not in-page selection"
  - "Use controlled Tabs (value+onValueChange) rather than uncontrolled defaultValue to allow Overview 'View all files' button to programmatically switch to Files tab"
  - "COLL-01 (archive/unarchive) and COLL-02 (collection limit display) deferred per prior user decision in 43-CONTEXT.md"

patterns-established:
  - "Overview tab signals section: wrap each SignalCard in a Link to the signals page, pass isSelected=false/onSelect=noop"
  - "Report card row layout: FileText icon | type Badge | title | generatedAt | View Report ghost button"
  - "ActivityFeed icon mapping: pulse=Zap, file=FileUp, report=FileText, chat=MessageSquare"

requirements-completed: [COLL-07, COLL-03]

# Metrics
duration: 15min
completed: 2026-03-04
---

# Phase 43 Plan 01: Collections Reports Summary

**Four-tab collection detail hub with Report/ActivityItem mock data types, stat cards, activity feed, and run-detection banner — delivering COLL-07 (credits display) and COLL-03 (reports list)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-04T18:00:00Z
- **Completed:** 2026-03-04T18:06:56Z
- **Tasks:** 2
- **Files modified:** 5 (1 modified, 4 created)

## Accomplishments

- Extended mock-data.ts with Report, ActivityItem types and MOCK_REPORTS (3 entries), MOCK_ACTIVITY (5 entries) — all with full content
- Replaced flat collection detail page with four-tab hub: Overview, Files, Signals, Reports
- Overview tab: 4 stat cards, RunDetectionBanner, signals hero (first 4 with Link), compact files table with "View all" tab-switch, activity feed timeline
- Reports tab: 3 report cards with type badges, titles, generated dates, and "View Report" links pointing to future report reader route
- Header shows "Credits used: N" pill with Zap icon (COLL-07)
- Files tab preserves all original behavior (upload zone, file table, data summary panel, sticky action bar)
- TypeScript compiles cleanly with no errors

## Task Commits

1. **Task 1: Extend mock-data.ts with Report, ActivityItem types and mock data** - `748ed1a` (feat)
2. **Task 2: Redesign collection detail page as four-tab hub** - `017a393` (feat)

## Files Created/Modified

- `pulse-mockup/src/lib/mock-data.ts` - Added ReportType, Report, ActivityItem types; MOCK_REPORTS (3 items), MOCK_ACTIVITY (5 items)
- `pulse-mockup/src/app/workspace/collections/[id]/page.tsx` - Replaced with four-tab hub layout using controlled Tabs
- `pulse-mockup/src/components/workspace/overview-stat-cards.tsx` - New: 4-card stat row (files, signals, reports, credits used)
- `pulse-mockup/src/components/workspace/activity-feed.tsx` - New: vertical timeline feed with icon mapping
- `pulse-mockup/src/components/workspace/run-detection-banner.tsx` - New: contextual CTA banner for running detection

## Decisions Made

- Used controlled Tabs (value+onValueChange) so the Overview "View all files in Files tab" button can programmatically switch tabs
- Passed `isSelected=false` and `onSelect={() => {}}` to SignalCard when rendered in Overview and Signals tabs, since those contexts use Link navigation — not in-page selection. This satisfied the existing SignalCard interface without modifying it.
- COLL-01 and COLL-02 deferred as planned per user decision in 43-CONTEXT.md

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added required isSelected and onSelect props to SignalCard usage**
- **Found during:** Task 2 (collection detail page redesign)
- **Issue:** SignalCard interface requires `isSelected: boolean` and `onSelect: (id: string) => void` — plan's code snippet omitted these
- **Fix:** Added `isSelected={false}` and `onSelect={() => {}}` to all SignalCard usages in non-selection contexts
- **Files modified:** pulse-mockup/src/app/workspace/collections/[id]/page.tsx
- **Verification:** TypeScript compiles without errors
- **Committed in:** 017a393 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Necessary to satisfy existing SignalCard interface. No scope creep.

## Issues Encountered

None beyond the SignalCard props fix above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 43-01 foundation is complete: tabbed layout, Report/ActivityItem types, and MOCK_REPORTS are all in place
- Plan 43-02 (report reader) can import MOCK_REPORTS and build the `/workspace/collections/[id]/reports/[reportId]` page
- "View Report" links already point to the correct route that 43-02 will create
- Files tab preserves all detection flow intact

---
*Phase: 43-collections-reports*
*Completed: 2026-03-04*
