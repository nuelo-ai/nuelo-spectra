---
phase: 51-frontend-migration
plan: 03
subsystem: ui
tags: [react, nextjs, tanstack-query, workspace, collections, signals]

requires:
  - phase: 51-01
    provides: "Hex.tech palette, UI components, workspace types/hooks/store"
  - phase: 51-02
    provides: "UnifiedSidebar, (workspace) route group layout"
provides:
  - "Collection list page with API data, create dialog, loading/error/empty states"
  - "Collection detail page with 4 tabs (Overview, Files, Signals, Reports)"
  - "15 workspace components (cards, tables, upload, detection loading, etc.)"
  - "GET /collections/{id}/signals backend endpoint"
affects: [51-04]

tech-stack:
  added: []
  patterns:
    - "File upload via FormData with useUploadFile mutation and ref-based callback"
    - "Signal severity sorting with const severityOrder map"
    - "Sheet component for slide-out data summary panel"

key-files:
  created:
    - frontend/src/app/(workspace)/workspace/page.tsx
    - frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx
    - frontend/src/components/workspace/collection-card.tsx
    - frontend/src/components/workspace/collection-list.tsx
    - frontend/src/components/workspace/create-collection-dialog.tsx
    - frontend/src/components/workspace/empty-state.tsx
    - frontend/src/components/workspace/overview-stat-cards.tsx
    - frontend/src/components/workspace/run-detection-banner.tsx
    - frontend/src/components/workspace/signal-card.tsx
    - frontend/src/components/workspace/activity-feed.tsx
    - frontend/src/components/workspace/detection-loading.tsx
    - frontend/src/components/workspace/file-table.tsx
    - frontend/src/components/workspace/file-upload-zone.tsx
    - frontend/src/components/workspace/data-summary-panel.tsx
    - frontend/src/components/workspace/sticky-action-bar.tsx
  modified:
    - frontend/src/hooks/useWorkspace.ts
    - backend/app/routers/collections.py
    - backend/app/services/collection.py

key-decisions:
  - "Credit cost hardcoded to 5 per run (flat pricing per decisions)"
  - "DataSummaryPanel uses Sheet (slide-out) instead of Dialog for better UX"
  - "Signal previews show up to 4 cards in 2-col grid on Overview tab"
  - "Added GET /collections/{id}/signals backend endpoint (was missing)"

patterns-established:
  - "Workspace component pattern: copy mockup layout, replace mock data with typed props from workspace.ts"
  - "File selection via Zustand store (selectedFileIds) shared between FileTable and StickyActionBar"

requirements-completed: [NAV-02, NAV-03, NAV-04, SIGNAL-01, SIGNAL-02]

duration: 10min
completed: 2026-03-07
---

# Phase 51 Plan 03: Workspace Pages Summary

**Collection list and detail pages with 4 tabs (Overview/Files/Signals/Reports), file upload, detection trigger, and signal severity sorting -- all wired to live API**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-07T19:26:51Z
- **Completed:** 2026-03-07T19:37:00Z
- **Tasks:** 4 (3 auto + 1 checkpoint with fixes)
- **Files modified:** 20

## Accomplishments
- Collection list page with create dialog, skeleton loading, error retry, and empty state
- Collection detail page with 4 tabs rendering live API data via TanStack Query hooks
- File upload with drag-drop zone and real useUploadFile mutation
- Detection trigger via sticky action bar with credit cost display
- Signals sorted by severity (critical > warning > info) with auto-selection of highest
- 15 workspace components migrated from mockup with mock data replaced by typed props

## Task Commits

Each task was committed atomically:

1. **Task 1: Collection list page + workspace components** - `1a09089` (feat)
2. **Task 2: Overview tab components** - `5b05b44` (feat)
3. **Task 3: Files/Signals/Reports tabs + collection detail page** - `eff9e9a` (feat)
4. **Fix: Collection list fetch, file upload, signals endpoint** - `3f22fd9` (fix)

## Files Created/Modified
- `frontend/src/app/(workspace)/workspace/page.tsx` - Collection list page with API data
- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` - Collection detail with 4 tabs
- `frontend/src/components/workspace/collection-card.tsx` - Collection card with name, counts, date
- `frontend/src/components/workspace/collection-list.tsx` - Grid of collection cards or empty state
- `frontend/src/components/workspace/create-collection-dialog.tsx` - Create collection via mutation
- `frontend/src/components/workspace/empty-state.tsx` - Empty state with CTA
- `frontend/src/components/workspace/overview-stat-cards.tsx` - File/signal/report/credit stat cards
- `frontend/src/components/workspace/run-detection-banner.tsx` - Detection CTA banner
- `frontend/src/components/workspace/signal-card.tsx` - Signal card with severity badge (preview + interactive)
- `frontend/src/components/workspace/activity-feed.tsx` - Timeline of signals and reports
- `frontend/src/components/workspace/detection-loading.tsx` - 4-step animated detection overlay
- `frontend/src/components/workspace/file-table.tsx` - File rows with checkbox selection
- `frontend/src/components/workspace/file-upload-zone.tsx` - Drag-drop file upload with mutation
- `frontend/src/components/workspace/data-summary-panel.tsx` - Slide-out sheet with markdown renderer
- `frontend/src/components/workspace/sticky-action-bar.tsx` - Fixed action bar with Run Detection button
- `frontend/src/hooks/useWorkspace.ts` - Fixed trailing slash, added refetchOnMount
- `backend/app/routers/collections.py` - Added GET /collections/{id}/signals endpoint
- `backend/app/services/collection.py` - Added list_collection_signals method

## Decisions Made
- Credit cost hardcoded to 5 per run matching flat pricing decision
- DataSummaryPanel uses Sheet component (slide-out from right) instead of Dialog for non-blocking UX
- Signal previews limited to 4 on Overview tab in 2-column grid
- Added backend signals endpoint that was missing from Phase 48 (required for frontend to fetch signals)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed trailing slash on API endpoints**
- **Found during:** Checkpoint verification (Issue 1)
- **Issue:** useCollections and useCreateCollection called /collections/ with trailing slash; backend route is /collections without trailing slash, causing redirect issues
- **Fix:** Removed trailing slashes, added refetchOnMount: "always" to useCollections
- **Files modified:** frontend/src/hooks/useWorkspace.ts
- **Committed in:** 3f22fd9

**2. [Rule 1 - Bug] Fixed file upload stale closure**
- **Found during:** Checkpoint verification (Issue 2)
- **Issue:** handleFiles useCallback depended on uploadMutation which changes identity every render, causing stale closures
- **Fix:** Used useRef to hold latest mutate function, removing dependency from useCallback
- **Files modified:** frontend/src/components/workspace/file-upload-zone.tsx
- **Committed in:** 3f22fd9

**3. [Rule 2 - Missing Critical] Added GET /collections/{id}/signals endpoint**
- **Found during:** Checkpoint verification (Issue 3)
- **Issue:** Frontend useCollectionSignals hook called /collections/{id}/signals but no such backend endpoint existed
- **Fix:** Added endpoint to collections router and list_collection_signals to CollectionService
- **Files modified:** backend/app/routers/collections.py, backend/app/services/collection.py
- **Committed in:** 3f22fd9

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** All fixes necessary for correct functionality. No scope creep.

## Issues Encountered
None beyond the checkpoint feedback items (documented as deviations above).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All workspace pages ready for signal detail view (plan 04)
- 15 workspace components available for reuse
- Backend signals endpoint available for signal list/detail pages

---
*Phase: 51-frontend-migration*
*Completed: 2026-03-07*
