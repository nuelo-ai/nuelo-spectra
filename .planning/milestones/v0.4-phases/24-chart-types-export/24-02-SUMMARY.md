---
phase: 24-chart-types-export
plan: 02
subsystem: frontend-charts
tags: [chart-export, plotly, client-side]
dependency_graph:
  requires: [phase-23-frontend-chart-rendering]
  provides: [chart-png-export, chart-svg-export]
  affects: [DataCard, ChartRenderer]
tech_stack:
  added: [plotly-downloadImage]
  patterns: [ref-forwarding, useImperativeHandle]
key_files:
  created:
    - frontend/src/components/chart/ChartExportButtons.tsx
  modified:
    - frontend/src/components/chart/ChartRenderer.tsx
    - frontend/src/components/chat/DataCard.tsx
decisions:
  - Client-side Plotly.downloadImage() for instant export without server round-trip
  - Ref forwarding via forwardRef/useImperativeHandle to expose chart DOM element
  - Export buttons only visible when chart fully rendered (not streaming)
  - Filename sanitization matches existing CSV/Markdown button pattern
  - 1200x800 default export dimensions for high-quality downloads
metrics:
  duration_seconds: 152
  tasks_completed: 2
  files_created: 1
  files_modified: 2
  commits: 2
  completed_date: 2026-02-13
---

# Phase 24 Plan 02: Chart Export Functionality Summary

**One-liner:** Client-side PNG/SVG chart export via Plotly.downloadImage() with ref-forwarded ChartRenderer and integrated export buttons in DataCard.

## Objective

Add PNG/SVG chart export functionality by refactoring ChartRenderer to forward a ref exposing its DOM element, creating a ChartExportButtons component using Plotly.downloadImage(), and integrating export buttons into DataCard below the chart. This enables users to download charts for reports and presentations with instant client-side export (no server round-trip).

## Execution Summary

**Pattern:** Fully autonomous (no checkpoints)

**Tasks completed:** 2/2

### Task 1: Refactor ChartRenderer with ref forwarding and create ChartExportButtons

**Commit:** 599ac2f

**Changes:**
- Refactored ChartRenderer from plain function component to `forwardRef` component
- Added `ChartRendererHandle` interface with `getElement()` method
- Implemented `useImperativeHandle` to expose chart `<div>` element to parent components
- Created ChartExportButtons.tsx with PNG and SVG download buttons
- Both buttons call `Plotly.downloadImage()` with 1200x800 dimensions
- Loading state management during export (disable buttons, show "Exporting..." text)

**Files:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartRenderer.tsx` (modified)
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartExportButtons.tsx` (created)

**Key decisions:**
- Used `forwardRef` and `useImperativeHandle` pattern for clean ref access
- Kept all existing ChartRenderer functionality unchanged (Plotly.react, ResizeObserver, cleanup)
- Matched existing DownloadButtons component style (`variant="outline"`, `size="sm"`)

### Task 2: Integrate ChartExportButtons into DataCard below chart

**Commit:** bef2b5a

**Changes:**
- Added `chartRendererRef` using `useRef<ChartRendererHandle>(null)`
- Imported `ChartRendererHandle` type and `ChartExportButtons` component
- Passed `ref={chartRendererRef}` to dynamically imported ChartRenderer
- Rendered ChartExportButtons below chart with right alignment (`flex justify-end`)
- Export buttons only visible when `!isStreaming` to prevent incomplete chart export
- Filename derived from query brief (lowercase, hyphenated, max 30 chars)

**Files:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chat/DataCard.tsx` (modified)

**Key decisions:**
- Export buttons hidden during streaming to ensure chart completeness
- Filename sanitization matches existing CSV/Markdown button pattern
- Right-aligned to match existing download button placement
- Ref chain: DataCard → ChartRenderer → ChartExportButtons.getChartElement

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

**TypeScript compilation:** Passed (`npx tsc --noEmit`)

**Next.js build:** Passed (`npm run build`)

**Must-haves verification:**

✅ **Truth 1:** User can download any rendered chart as PNG via download button below chart
- ChartExportButtons renders PNG button
- Button calls `Plotly.downloadImage(element, { format: 'png', width: 1200, height: 800 })`
- Button appears below chart in DataCard when not streaming

✅ **Truth 2:** User can download any rendered chart as SVG via download button below chart
- ChartExportButtons renders SVG button
- Button calls `Plotly.downloadImage(element, { format: 'svg', width: 1200, height: 800 })`
- Button appears below chart in DataCard when not streaming

✅ **Truth 3:** Download buttons appear below chart in DataCard, only when chart is rendered and not streaming
- ChartExportButtons wrapped in `{!isStreaming && (...)}` conditional
- Positioned below ChartRenderer with right alignment
- Only visible when `chartSpecs` exists

✅ **Artifact 1:** ChartExportButtons.tsx provides PNG/SVG download buttons using Plotly.downloadImage()
- File created at `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartExportButtons.tsx`
- Contains `Plotly.downloadImage()` calls

✅ **Artifact 2:** ChartRenderer.tsx uses forwardRef with ChartRendererHandle
- File exports `ChartRendererHandle` interface
- Component wrapped with `forwardRef<ChartRendererHandle, ChartRendererProps>`
- Uses `useImperativeHandle` to expose `getElement()` method

✅ **Artifact 3:** DataCard.tsx integrates ChartExportButtons below chart
- File imports and renders `ChartExportButtons`
- Positioned below `ChartRenderer` component

✅ **Key link 1:** ChartExportButtons calls Plotly.downloadImage(chartRef.current.getElement())
- ChartExportButtons receives `getChartElement` function
- Function returns `chartRendererRef.current?.getElement() ?? null`
- Plotly.downloadImage called with returned element

✅ **Key link 2:** DataCard imports and renders ChartExportButtons below ChartRenderer
- DataCard imports `ChartExportButtons`
- Renders below `<ChartRenderer>` in chart section

## Success Criteria

✅ When a chart is rendered in DataCard, two export buttons (PNG, SVG) appear below it

✅ Clicking PNG triggers a browser download of the chart as a 1200x800 PNG image

✅ Clicking SVG triggers a browser download as SVG

✅ Buttons are hidden during streaming

✅ The filename is derived from the query brief

## Technical Decisions

1. **Ref forwarding pattern:** Used `forwardRef` + `useImperativeHandle` instead of direct ref access to maintain encapsulation and provide clean API
2. **Export dimensions:** 1200x800 provides high-quality exports suitable for presentations and reports
3. **Loading state:** Disabled both buttons during export to prevent concurrent download attempts
4. **Filename sanitization:** Matched existing pattern (lowercase, replace non-alphanumeric with hyphens, trim, max 30 chars) for consistency
5. **Conditional rendering:** Export buttons only shown when `!isStreaming` to ensure chart completeness

## Performance Notes

- Client-side export via Plotly.downloadImage() is instant (no server round-trip)
- No additional network requests required for export functionality
- Ref forwarding adds negligible overhead (single useImperativeHandle hook)

## Next Steps

This plan completes chart export functionality. Next plans in Phase 24:
- Plan 03: Additional chart types or advanced export options (if planned)

## Self-Check: PASSED

**Files created:**
```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartExportButtons.tsx" ] && echo "FOUND: ChartExportButtons.tsx" || echo "MISSING: ChartExportButtons.tsx"
```
FOUND: ChartExportButtons.tsx

**Files modified:**
```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chart/ChartRenderer.tsx" ] && echo "FOUND: ChartRenderer.tsx" || echo "MISSING: ChartRenderer.tsx"
```
FOUND: ChartRenderer.tsx

```bash
[ -f "/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/chat/DataCard.tsx" ] && echo "FOUND: DataCard.tsx" || echo "MISSING: DataCard.tsx"
```
FOUND: DataCard.tsx

**Commits:**
```bash
git log --oneline --all | grep -q "599ac2f" && echo "FOUND: 599ac2f" || echo "MISSING: 599ac2f"
```
FOUND: 599ac2f

```bash
git log --oneline --all | grep -q "bef2b5a" && echo "FOUND: bef2b5a" || echo "MISSING: bef2b5a"
```
FOUND: bef2b5a

All files and commits verified successfully.
