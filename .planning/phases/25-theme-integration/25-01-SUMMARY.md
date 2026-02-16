---
phase: 25-theme-integration
plan: 01
subsystem: frontend-visualization
tags: [theme, ui, plotly, nord-palette, dark-mode]

dependency_graph:
  requires:
    - "24-03: Chart type switching infrastructure"
    - "next-themes package for theme detection"
  provides:
    - "Theme-aware chart rendering with Nord palette"
    - "Chart theme configuration module (chartTheme.ts)"
  affects:
    - "All Plotly chart visualizations in the platform"
    - "Chart exports (PNG/SVG capture themed appearance)"

tech_stack:
  added:
    - "Nord color palette (16 colors + 5 darkened Aurora variants)"
    - "next-themes useTheme() hook integration"
  patterns:
    - "Theme captured on mount only (intentional stale closure)"
    - "Deep merge of theme config over backend layout"
    - "Separate light/dark colorways for data trace legibility"

key_files:
  created:
    - path: "frontend/src/lib/chartTheme.ts"
      purpose: "Nord palette constants and Plotly layout theme configs"
      exports: ["NORD_PALETTE", "LIGHT_AURORA", "getChartThemeConfig", "getPieChartOverrides"]
  modified:
    - path: "frontend/src/components/chart/ChartRenderer.tsx"
      changes: "Integrated useTheme(), applied theme config to Plotly layout/traces"
    - path: "backend/app/config/prompts.yaml"
      changes: "Removed template='plotly_white' (frontend now controls theming)"

decisions:
  - what: "Use Nord palette for all chart colors"
    why: "Matches platform's existing Nord-based design system"
    alternatives: "Custom palette, Plotly defaults"

  - what: "Darken Aurora colors for light mode (LIGHT_AURORA)"
    why: "Pure Aurora yellow/orange wash out on white backgrounds"
    impact: "Better contrast and readability in light mode"

  - what: "Theme captured on mount only (isDark NOT in useEffect deps)"
    why: "Already-rendered charts keep original theme on toggle (per user decision)"
    impact: "Only newly generated charts pick up current theme"

  - what: "Frontend merges theme config OVER backend layout"
    why: "Backend sets transparent backgrounds; frontend replaces with themed colors"
    implementation: "Deep merge preserves backend axis labels/titles while applying theme fonts"

  - what: "White text on pie chart slices in both themes"
    why: "Colored slices provide sufficient contrast; consistent across themes"

metrics:
  duration: 189s
  tasks_completed: 3
  files_created: 1
  files_modified: 2
  commits: 2
  completed_at: "2026-02-14T01:10:24Z"
---

# Phase 25 Plan 01: Theme Integration Summary

**One-liner:** Nord-themed Plotly charts with dark/light mode support via chartTheme module and useTheme() integration.

## What Was Built

Integrated dark/light theme support into Plotly chart rendering using the Nord color palette. Charts now automatically match the platform's current theme with proper color contrast, readable text hierarchy, and correct export behavior.

**Key capabilities:**
- Dark mode: Nord Aurora colors (vivid red/orange/yellow/green/purple) on dark Nord backgrounds
- Light mode: Darkened Aurora variants (better contrast) on light gray backgrounds
- Theme-aware text: Snow colors for dark mode, Tailwind grays for light mode
- Visual hierarchy: Title > axis labels > tick marks > gridlines (descending brightness)
- Horizontal legends positioned below charts
- White text on pie chart colored slices
- Exported PNG/SVG captures themed appearance with filled backgrounds
- Already-rendered charts keep original theme; only new charts use current theme

## Task Breakdown

### Task 1: Create chart theme configuration module and update visualization prompt
**Files:** `frontend/src/lib/chartTheme.ts`, `backend/app/config/prompts.yaml`
**Commit:** e7ab52f

Created `chartTheme.ts` module with:
- `NORD_PALETTE`: All 16 Nord colors (Polar Night, Snow Storm, Frost, Aurora)
- `LIGHT_AURORA`: Darkened Aurora variants for light mode legibility (#a54e56, #b86f5d, #c9a956, #8a9d78, #9a7a96)
- `getChartThemeConfig(theme)`: Returns Plotly layout object with theme-specific colors, fonts, gridlines, legend positioning
- `getPieChartOverrides(theme)`: Returns pie chart text styling (white on slices, theme-appropriate outside text)

Dark mode layout highlights:
- `paper_bgcolor`: Nord 1 (#3b4252) — subtle card tint
- `plot_bgcolor`: Nord 0 (#2e3440) — darker plot area for depth
- `colorway`: Nord Aurora [#bf616a, #d08770, #ebcb8b, #a3be8c, #b48ead]
- Gridlines: Nord 2 at 30% opacity (rgba(67, 76, 94, 0.3))
- Text: Nord 4/5 for labels/titles, Nord 3 for tick marks (dimmer)

Light mode layout highlights:
- `paper_bgcolor`: #f9fafb (Tailwind gray-50)
- `plot_bgcolor`: #ffffff
- `colorway`: LIGHT_AURORA darkened variants
- Gridlines: #e5e7eb (Tailwind gray-200)
- Text: #374151 for labels, #1f2937 for titles, #9ca3af for tick marks

Updated `backend/app/config/prompts.yaml`:
- Removed `template="plotly_white"` instruction (frontend now controls all theming)
- Kept `paper_bgcolor="rgba(0,0,0,0)"` and `plot_bgcolor="rgba(0,0,0,0)"` (transparent)
- Kept "DO NOT set explicit trace colors" rule (critical for colorway to work)

**Rationale:** Backend sets transparent backgrounds; frontend merges theme config over them. This separation allows full theme control on the client side while keeping backend visualization code theme-agnostic.

### Task 2: Integrate theme detection into ChartRenderer
**Files:** `frontend/src/components/chart/ChartRenderer.tsx`
**Commit:** 0c071a9

Modified `ChartRenderer.tsx` to apply theme configuration:

1. **Added imports:**
   - `useTheme` from next-themes
   - `getChartThemeConfig`, `getPieChartOverrides` from @/lib/chartTheme

2. **Theme detection:**
   - Called `useTheme()` to get `resolvedTheme` (already resolves 'system' to 'light'/'dark')
   - Derived `isDark = resolvedTheme === 'dark'`

3. **Theme application in useEffect:**
   - Called `getChartThemeConfig(isDark ? 'dark' : 'light')` to get theme layout
   - Mapped traces to apply `getPieChartOverrides()` to pie chart types
   - Deep merged theme config with backend layout:
     - Theme config provides: colors, fonts, gridlines, legend positioning
     - Backend layout provides: axis labels, titles, data-specific text
     - Merge preserves backend text while applying theme styling
   - Increased bottom margin from 50px to 80px to accommodate horizontal legend

4. **Intentional stale closure (critical decision):**
   - `isDark` is NOT in useEffect dependency array
   - Added ESLint disable comment and explanation
   - **Behavior:** Theme is captured on component mount only
   - **Result:** When user toggles theme, existing charts keep original theme; only NEW charts use updated theme
   - **Rationale:** Per user decision — already-rendered charts in conversation preserve their original styling

### Task 3: Verify and fix chart toolbar component theming
**Files:** `frontend/src/components/chart/ChartExportButtons.tsx`, `frontend/src/components/chart/ChartTypeSwitcher.tsx`
**Commit:** None (no changes needed)

Verified both chart toolbar components for dark mode compatibility:

**ChartExportButtons.tsx analysis:**
- Uses shadcn/ui `Button` component with `variant="outline"` and `size="sm"`
- `text-muted-foreground` class for "Export:" label
- All classes use CSS variables defined in `globals.css` with `.dark` overrides
- **Verdict:** No changes needed ✓

**ChartTypeSwitcher.tsx analysis:**
- Active button: `bg-primary text-primary-foreground border-primary`
- Inactive button: `bg-background hover:bg-accent border-border`
- Label: `text-muted-foreground`
- All classes use CSS variables with dark mode support
- **Verdict:** No changes needed ✓

**Verification command output:** `grep -E "(bg-white|bg-black|text-white|text-black|border-gray|bg-gray|text-gray)"` returned empty (no hardcoded light-only colors found).

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed without architectural changes, unexpected bugs, or blocking issues.

**Task 3 finding:** Chart toolbar components already properly themed via CSS variables (no code changes required). This is a positive finding, not a deviation.

## Verification Results

**TypeScript compilation:** ✓ Passed (`npx tsc --noEmit`)
**Frontend build:** ✓ Passed (`npm run build`)
**Import verification:** ✓ All imports present (useTheme, getChartThemeConfig, getPieChartOverrides)
**ESLint suppression:** ✓ Correct (isDark not in useEffect deps, with explanation comment)
**Backend prompt update:** ✓ Confirmed (0 matches for "plotly_white", 1 match for "DO NOT set explicit trace colors")

**Expected visual behavior (requires manual testing):**
1. Dark mode chart: Nord Aurora colors, dark card background, bright Snow text, subtle gridlines
2. Light mode chart: Darkened Aurora colors, light gray background, dark text, light gridlines
3. Theme toggle: Existing chart keeps original theme, next new chart uses updated theme
4. Export: PNG/SVG captures themed appearance with filled background (not transparent)
5. Pie charts: White text on colored slices in both themes

## Self-Check

Verifying all claimed artifacts exist:

**Files created:**
- ✓ frontend/src/lib/chartTheme.ts exists
- ✓ Exports NORD_PALETTE, LIGHT_AURORA, getChartThemeConfig, getPieChartOverrides

**Files modified:**
- ✓ frontend/src/components/chart/ChartRenderer.tsx modified (useTheme integration)
- ✓ backend/app/config/prompts.yaml modified (removed template='plotly_white')

**Commits:**
- ✓ e7ab52f: "feat(25-01): create chart theme module with Nord palette"
- ✓ 0c071a9: "feat(25-01): integrate theme detection into ChartRenderer"

**TypeScript types:**
- ✓ All exports properly typed (Layout, PlotData from plotly.js-dist-min)
- ✓ No TypeScript compilation errors

## Self-Check: PASSED

All claimed files, exports, and commits verified. No missing artifacts.

## Impact & Next Steps

**Immediate impact:**
- Charts now visually native to platform's Nord-based theme system
- No more jarring white backgrounds in dark mode
- Improved data trace legibility in both themes (appropriate color contrast)
- Professional, cohesive visual experience across the platform

**Technical debt eliminated:**
- Fixed hardcoded Plotly default colors (white backgrounds, blue traces)
- Removed frontend dependency on backend theme template (`plotly_white`)
- Centralized theme configuration in dedicated module (single source of truth)

**Next steps:**
- Phase 25 Plan 02 (if exists): Additional theme integration areas
- Manual UI testing: Verify visual appearance matches specifications
- User feedback: Collect observations on color contrast and readability
