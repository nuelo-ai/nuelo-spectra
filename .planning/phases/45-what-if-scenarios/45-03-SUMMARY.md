---
phase: 45-what-if-scenarios
plan: 03
subsystem: ui
tags: [what-if, signal-detail-panel, report-viewer, entry-points, badge, cta]

requires:
  - phase: 45-what-if-scenarios-01
    provides: [WhatIf types, MOCK_WHATIF_SESSIONS, rep-whatif-001, /whatif entry page]
  - phase: 45-what-if-scenarios-02
    provides: [/whatif/[sessionId] session page, WhatIfRefinementChat component]
provides:
  - What-If button in signal-detail-panel Investigation section (enabled/disabled based on complete investigation)
  - What-If Scenario Report badge in report viewer sticky header (violet)
  - Explore What-If Scenarios CTA at bottom of investigation reports (violet card with Start What-If link)
affects: [signal-detail-panel.tsx, report viewer page, Phase 45 complete]

tech-stack:
  added: []
  patterns:
    - Conditional enabled/disabled button using hasCompleteInvestigation check against MOCK_INVESTIGATION_SESSIONS
    - Additive-only changes to existing components — no existing behavior modified

key-files:
  created: []
  modified:
    - pulse-mockup/src/components/workspace/signal-detail-panel.tsx
    - pulse-mockup/src/app/workspace/collections/[id]/reports/[reportId]/page.tsx

key-decisions:
  - "What-If button enabled/disabled check uses MOCK_INVESTIGATION_SESSIONS.some() — no import of MOCK_WHATIF_SESSIONS needed in signal-detail-panel.tsx (unused import avoided)"
  - "Wand2 icon used for What-If (matches plan spec); violet color scheme used for all What-If UI elements to distinguish from blue Investigation theme"
  - "WHAT-05 (Add Scenario) and WHAT-06 (side-by-side comparison) confirmed intentionally deferred per user decision in CONTEXT.md"

patterns-established:
  - "Violet color scheme for What-If feature surface: bg-violet-500/10 text-violet-400 border-violet-500/30 for badge; bg-violet-600 for CTA button; bg-violet-50/border-violet-200 for CTA card"
  - "What-If button disabled state: opacity-50 cursor-not-allowed + disabled prop + informational label in parens"

requirements-completed: [WHAT-07]

duration: continuation (checkpoint)
completed: 2026-03-05
---

# Phase 45 Plan 03: What-If Entry Points and Report Viewer Summary

**What-If button wired into signal detail panel (enabled for sig-001, disabled without investigation), violet What-If Scenario Report badge in report viewer, and violet Explore What-If Scenarios CTA on investigation reports — all 7 WHAT requirements reviewer-approved.**

## Performance

- **Duration:** Continuation after human-verify checkpoint
- **Started:** 2026-03-05T15:51:43Z
- **Completed:** 2026-03-05
- **Tasks:** 2 (1 auto + 1 human-verify)
- **Files modified:** 2

## Accomplishments

- Added What-If button to signal detail panel's Investigation section, enabled when the signal has a complete investigation (`sig-001`), disabled with an explanatory label otherwise; both Investigate and What-If buttons rendered side by side in a flex container
- Extended report viewer sticky header with a violet "What-If Scenario Report" badge rendered conditionally on `report.type`
- Added "Explore What-If Scenarios" violet CTA card at the bottom of investigation reports, linking to the signal's `/whatif` route via `report.signalId`
- Reviewer approved all 7 WHAT requirements (WHAT-01 through WHAT-04, WHAT-07); WHAT-05 and WHAT-06 confirmed intentionally deferred

## Task Commits

Each task was committed atomically:

1. **Task 1: Add What-If entry points to signal detail panel and report viewer** - `5e559a7` (feat)
2. **Task 2: Human verification checkpoint** - no code commit (reviewer approved)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `pulse-mockup/src/components/workspace/signal-detail-panel.tsx` — Added Wand2 icon import, `hasCompleteInvestigation` computed from MOCK_INVESTIGATION_SESSIONS, What-If button (enabled/disabled) alongside Investigate button in a flex container
- `pulse-mockup/src/app/workspace/collections/[id]/reports/[reportId]/page.tsx` — Added Wand2 import, violet "What-If Scenario Report" badge in sticky header, "Explore What-If Scenarios" CTA block at bottom of investigation report paper

## Decisions Made

- **Avoided unused import:** Plan spec said to import `MOCK_WHATIF_SESSIONS` in signal-detail-panel.tsx, but since the enabled/disabled check only needs `MOCK_INVESTIGATION_SESSIONS`, importing the unused symbol would cause a TypeScript lint warning. Import omitted.
- **Color system:** All What-If UI elements use violet to visually separate from the blue Investigation theme — consistent across badge (violet-400/violet-500/10), CTA card (violet-50/violet-200), CTA button (violet-600/violet-700).
- **Deferred requirements confirmed:** WHAT-05 (Add Scenario) and WHAT-06 (side-by-side comparison) are not implemented. Reviewer confirmed this is intentional per product scope decision.

## Deviations from Plan

None — plan executed exactly as written (one minor import omission to avoid an unused-import TypeScript warning, which does not affect behavior).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 45 (What-If Scenarios) is fully complete — all 3 plans executed and all 7 WHAT requirements reviewer-approved
- The complete What-If flow is functional end-to-end: signal detail panel → objective selection → loading animation → session page (scenario list + detail + chat) → report → report viewer with badge
- Ready for Phase 46 (Admin Workspace / v0.12) or any remaining planned phases

---
*Phase: 45-what-if-scenarios*
*Completed: 2026-03-05*

## Self-Check: PASSED

- FOUND: `pulse-mockup/src/components/workspace/signal-detail-panel.tsx`
- FOUND: `pulse-mockup/src/app/workspace/collections/[id]/reports/[reportId]/page.tsx`
- FOUND: `.planning/phases/45-what-if-scenarios/45-03-SUMMARY.md`
- FOUND: commit `5e559a7` — feat(45-03)
