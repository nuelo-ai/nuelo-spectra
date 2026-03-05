---
phase: 42-analysis-workspace-pulse-detection
plan: 03
subsystem: ui
tags: [react, next.js, shadcn-ui, tailwindcss, file-management, detection-flow, credit-estimate]

# Dependency graph
requires:
  - phase: 42-01
    provides: "App scaffold, shell layout, mock data module, shadcn/ui components"
provides:
  - "Collection detail page with file management at /workspace/collections/[id]"
  - "File table with checkboxes, type icons, profiling status badges"
  - "Data summary side panel (Sheet) for file inspection"
  - "Sticky bottom action bar with credit estimate and Run Detection button"
  - "Full-page animated detection loading with 4-step progression"
  - "Auto-navigation to signals page after detection completes"
affects: [42-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [sticky-action-bar, full-page-loading-replacement, file-selection-state]

key-files:
  created:
    - pulse-mockup/src/app/workspace/collections/[id]/page.tsx
    - pulse-mockup/src/app/workspace/collections/[id]/layout.tsx
    - pulse-mockup/src/components/workspace/file-table.tsx
    - pulse-mockup/src/components/workspace/file-upload-zone.tsx
    - pulse-mockup/src/components/workspace/data-summary-panel.tsx
    - pulse-mockup/src/components/workspace/sticky-action-bar.tsx
    - pulse-mockup/src/components/workspace/detection-loading.tsx
  modified: []

key-decisions:
  - "Sticky action bar uses fixed positioning with backdrop blur for always-visible detection controls"
  - "Detection loading replaces page content (full-page transition) rather than overlay per CONTEXT.md"
  - "Credit estimate calculated dynamically: selectedCount * COST_PER_FILE from mock-data constants"

patterns-established:
  - "File selection state pattern: parent page manages selectedFileIds, passes down to FileTable and StickyActionBar"
  - "Detection loading as full-page replacement: isDetecting state triggers component swap in page"
  - "Profiling status badges: emerald=Ready, amber+pulse=Profiling, red=Error"

requirements-completed: [PULSE-04, PULSE-05, PULSE-08]

# Metrics
duration: 3min
completed: 2026-03-04
---

# Phase 42 Plan 03: Collection Detail & Detection Flow Summary

**Collection detail page with file table (checkboxes, profiling badges), sticky action bar with dynamic credit estimate, and animated 4-step detection loading that auto-navigates to signals**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-04T16:14:05Z
- **Completed:** 2026-03-04T16:18:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Collection detail page at /workspace/collections/[id] with header (name, status badge, date), file upload dropzone, and file table
- File table with select-all/individual checkboxes, type-specific icons (CSV=green FileText, Excel=blue FileSpreadsheet), profiling status badges (Ready/Profiling/Error), and clickable file names that open a data summary side panel
- Data summary Sheet panel showing file metadata, row/column counts, detected data types, and sample column names
- Sticky bottom action bar with file count, dynamic credit estimate (~N credits for N files), and Run Detection button disabled with hint text when no files selected
- Full-page detection loading with 4 animated steps (Analyzing files, Detecting patterns, Scoring signals, Finalizing results) with progress bar and auto-navigation to signals page

## Task Commits

Each task was committed atomically:

1. **Task 1: Collection detail page with file table and data summary panel** - `1d78a66` (feat)
2. **Task 2: Sticky action bar with credit estimate and detection loading state** - `833b4a2` (feat)

## Files Created/Modified
- `pulse-mockup/src/app/workspace/collections/[id]/layout.tsx` - Pass-through layout for collection routes
- `pulse-mockup/src/app/workspace/collections/[id]/page.tsx` - Collection detail page managing file selection, detection, and panel state
- `pulse-mockup/src/components/workspace/file-table.tsx` - File list table with checkboxes, type icons, profiling status badges
- `pulse-mockup/src/components/workspace/file-upload-zone.tsx` - Drag-and-drop upload zone with visual feedback
- `pulse-mockup/src/components/workspace/data-summary-panel.tsx` - Right-side Sheet panel with file metadata and mock data summary
- `pulse-mockup/src/components/workspace/sticky-action-bar.tsx` - Fixed bottom bar with credit estimate and Run Detection button
- `pulse-mockup/src/components/workspace/detection-loading.tsx` - Animated 4-step loading with progress bar and auto-navigation
- `pulse-mockup/src/components/ui/checkbox.tsx` - shadcn checkbox component (dependency)

## Decisions Made
- Sticky action bar uses fixed center-bottom positioning with backdrop blur and card background for visibility over page content
- Detection loading uses interval-based step progression (~3.5s per step, ~13.5s total) matching the 15-30s estimated range
- File type icons use color-coded lucide icons: emerald for CSV, blue for Excel
- Data summary panel hardcodes realistic mock data (12,847 rows, 24 columns, 6 sample columns with types)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Collection detail page complete with full detection flow
- Auto-navigation to /workspace/collections/[id]/signals ready for Plan 04 (Signal Results)
- File selection and detection state patterns established for reuse

## Self-Check: PASSED

All 7 created files verified on disk. Both task commits (1d78a66, 833b4a2) verified in git log. Build passes cleanly.

---
*Phase: 42-analysis-workspace-pulse-detection*
*Completed: 2026-03-04*
