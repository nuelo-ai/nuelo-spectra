---
phase: 24-chart-types-export
plan: 03
subsystem: frontend-charts
tags: [chart-switching, plotly-restyle, client-side]
dependency_graph:
  requires: [phase-24-chart-export]
  provides: [chart-type-switching, chart-type-compatibility]
  affects: [DataCard, ChartTypeSwitcher]
tech_stack:
  added: [plotly-restyle, chart-type-compatibility]
  patterns: [client-side-chart-manipulation, data-shape-analysis]
key_files:
  created:
    - frontend/src/lib/chartTypeCompatibility.ts
    - frontend/src/components/chart/ChartTypeSwitcher.tsx
  modified:
    - frontend/src/components/chat/DataCard.tsx
    - .gitignore
decisions:
  - Client-side Plotly.restyle() for instant chart type switching (no backend round-trip)
  - Data shape analysis determines compatible chart types (numeric x-axis = all 3 types, categorical = bar+line only)
  - Toggle button UI instead of select dropdown for better visual feedback
  - Switcher returns null for non-switchable types (pie, histogram, box) - only export buttons shown
  - Fixed .gitignore pattern from 'lib/' to '/lib/' to not ignore frontend/src/lib/
  - Toolbar layout uses justify-between with switcher on left, export on right
metrics:
  duration_seconds: 130
  tasks_completed: 2
  files_created: 2
  files_modified: 2
  commits: 2
  completed_date: 2026-02-13
---

# Phase 24 Plan 03: Chart Type Switching Summary

**One-liner:** Client-side chart type switching between bar/line/scatter using Plotly.restyle() with data shape compatibility analysis and toggle button UI.

## Objective

Add chart type switching functionality by creating a data shape compatibility utility to determine valid chart types, building a ChartTypeSwitcher component that uses Plotly.restyle() for instant client-side type changes, and integrating the switcher into DataCard alongside the existing export buttons. This enables users to explore the same data in different visual formats without backend round-trips.

## Execution Summary

**Pattern:** Fully autonomous (no checkpoints)

**Tasks completed:** 2/2

### Task 1: Create chart type compatibility utility and ChartTypeSwitcher component

**Commit:** 75c1320

**Changes:**
- Created chartTypeCompatibility.ts with data shape analysis functions
- `detectCurrentChartType()` identifies bar/line/scatter from trace properties (type and mode)
- `getCompatibleChartTypes()` returns valid types based on data shape (numeric x-axis = all 3, categorical = bar+line)
- Created ChartTypeSwitcher.tsx with toggle button UI
- Uses Plotly.restyle() to change trace type/mode without full re-render
- Returns null for non-switchable types (pie, histogram, box, donut)
- Toggle buttons show active state with bg-primary highlighting
- Each button has icon (BarChart3, TrendingUp, Circle) and label

**Files:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/lib/chartTypeCompatibility.ts` (created)
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartTypeSwitcher.tsx` (created)
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.gitignore` (modified)

**Key decisions:**
- Data shape analysis checks x-axis values: numeric allows all 3 types, categorical only bar+line (scatter doesn't make sense with categorical x-axis)
- Toggle button UI provides better visual feedback than select dropdown
- Plotly.restyle() is instant (no re-render, no network call)
- Fixed .gitignore blocking issue: changed `lib/` to `/lib/` to only ignore root lib/ (Python) and not frontend/src/lib/

### Task 2: Integrate ChartTypeSwitcher into DataCard alongside export buttons

**Commit:** f95da81

**Changes:**
- Added ChartTypeSwitcher import to DataCard
- Updated chart toolbar section with justify-between layout
- Type switcher on left (only visible for bar/line/scatter charts)
- Export buttons on right (always visible for any chart type)
- Both components receive same chartRendererRef for DOM access
- Toolbar only appears when not streaming (ensures chart completeness)
- ml-auto on export buttons ensures right alignment even when switcher returns null

**Files:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chat/DataCard.tsx` (modified)

**Key decisions:**
- justify-between with flex-shrink-0 and ml-auto ensures proper layout
- Export buttons always right-aligned regardless of switcher visibility
- Both components share chartRendererRef callback pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed .gitignore pattern blocking frontend/src/lib/**
- **Found during:** Task 1 file creation
- **Issue:** chartTypeCompatibility.ts was created but not showing in git status. Investigation revealed .gitignore line 13 `lib/` was catching frontend/src/lib/ directory (intended for Python lib/ only)
- **Fix:** Changed `lib/` to `/lib/` to only match root-level lib directory
- **Files modified:** .gitignore
- **Commit:** 75c1320 (included with Task 1)

## Verification Results

**TypeScript compilation:** Passed (`npx tsc --noEmit`)

**Next.js build:** Passed (`npm run build`)

**Must-haves verification:**

✅ **Truth 1:** User can switch between bar, line, and scatter chart types after initial generation
- ChartTypeSwitcher renders toggle buttons for compatible types
- Clicking button calls Plotly.restyle() to change trace type/mode
- Works for bar/line/scatter charts

✅ **Truth 2:** Chart type switcher only shows applicable types for the current data shape
- getCompatibleChartTypes() analyzes x-axis data type
- Numeric x-axis returns ['bar', 'line', 'scatter']
- Categorical x-axis returns ['bar', 'line']
- Only compatible types are rendered as buttons

✅ **Truth 3:** Switching chart type re-renders the chart instantly without backend round-trip
- Plotly.restyle() modifies existing chart in-place
- No network requests, no state updates, no component re-renders
- Instant visual feedback

✅ **Truth 4:** Chart type switcher is hidden for pie, donut, histogram, and box plots (single-type only)
- detectCurrentChartType() returns null for non-switchable types
- ChartTypeSwitcher returns null (no render) when initial type is null
- Only export buttons visible for these chart types

✅ **Artifact 1:** chartTypeCompatibility.ts provides data shape analysis
- File created at `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/lib/chartTypeCompatibility.ts`
- Exports getCompatibleChartTypes and detectCurrentChartType functions

✅ **Artifact 2:** ChartTypeSwitcher.tsx uses Plotly.restyle() for switching
- File created at `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartTypeSwitcher.tsx`
- Contains Plotly.restyle() calls with correct parameters

✅ **Artifact 3:** DataCard.tsx integrates ChartTypeSwitcher next to ChartExportButtons
- File imports and renders ChartTypeSwitcher
- Positioned in toolbar with switcher on left, export on right

✅ **Key link 1:** ChartTypeSwitcher imports from chartTypeCompatibility
- Import statement verified: `import { getCompatibleChartTypes, detectCurrentChartType } from '@/lib/chartTypeCompatibility'`

✅ **Key link 2:** ChartTypeSwitcher calls Plotly.restyle()
- Verified 3 Plotly.restyle() calls for bar/line/scatter switching

✅ **Key link 3:** DataCard imports and renders ChartTypeSwitcher
- Import verified at line 19
- Render verified at line 188

## Success Criteria

✅ For bar/line/scatter charts, a row of toggle buttons appears below the chart allowing the user to switch between compatible types

✅ Clicking a different type instantly re-renders the chart via Plotly.restyle() without any backend call

✅ For pie, donut, histogram, and box charts, the switcher is hidden (only export buttons visible)

✅ The chart toolbar is neatly laid out with switcher on the left and export buttons on the right

## Technical Decisions

1. **Data shape analysis:** Numeric x-axis allows all 3 types (bar/line/scatter), categorical x-axis only allows bar/line (scatter doesn't make sense with categorical data)

2. **Plotly.restyle() API:** Used correct parameters for each type:
   - Line: `{type: 'scatter', mode: 'lines'}`
   - Scatter: `{type: 'scatter', mode: 'markers'}`
   - Bar: `{type: 'bar', mode: undefined}` (clear mode to prevent scatter-like rendering)

3. **Toggle button UI:** Chose toggle buttons over select dropdown for better visual feedback and consistency with modern UI patterns

4. **Early returns:** ChartTypeSwitcher returns null if chart is not switchable (<=1 compatible types), keeping UI clean

5. **Toolbar layout:** justify-between with flex-shrink-0 and ml-auto ensures proper spacing and alignment regardless of switcher visibility

6. **.gitignore fix:** Changed `lib/` to `/lib/` to prevent ignoring frontend source directories while maintaining Python lib/ exclusion

## Performance Notes

- Plotly.restyle() is extremely fast (single DOM update, no re-render)
- No network requests for chart type switching
- No React state updates or component re-renders
- Data shape analysis runs once on component mount (cached in local state)
- Zero LLM tokens consumed for type switching (fully client-side)

## Next Steps

This completes Phase 24 (Chart Types & Export). All 3 plans in this phase are now complete:
- Plan 01: Enhanced chart type selection and labeling (completed)
- Plan 02: Chart export functionality (completed)
- Plan 03: Chart type switching (completed)

Next phase: Phase 25 or milestone completion tasks.

## Self-Check: PASSED

**Files created:**
```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/lib/chartTypeCompatibility.ts" ] && echo "FOUND: chartTypeCompatibility.ts" || echo "MISSING: chartTypeCompatibility.ts"
```
FOUND: chartTypeCompatibility.ts

```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartTypeSwitcher.tsx" ] && echo "FOUND: ChartTypeSwitcher.tsx" || echo "MISSING: ChartTypeSwitcher.tsx"
```
FOUND: ChartTypeSwitcher.tsx

**Files modified:**
```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chat/DataCard.tsx" ] && echo "FOUND: DataCard.tsx" || echo "MISSING: DataCard.tsx"
```
FOUND: DataCard.tsx

```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.gitignore" ] && echo "FOUND: .gitignore" || echo "MISSING: .gitignore"
```
FOUND: .gitignore

**Commits:**
```bash
git log --oneline --all | grep -q "75c1320" && echo "FOUND: 75c1320" || echo "MISSING: 75c1320"
```
FOUND: 75c1320

```bash
git log --oneline --all | grep -q "f95da81" && echo "FOUND: f95da81" || echo "MISSING: f95da81"
```
FOUND: f95da81

All files and commits verified successfully.
