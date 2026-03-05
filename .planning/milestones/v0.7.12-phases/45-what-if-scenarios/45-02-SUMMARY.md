---
phase: 45-what-if-scenarios
plan: 02
subsystem: ui
tags: [what-if, scenarios, refinement-chat, 4-panel-layout, next-js, shadcn]

requires:
  - phase: 45-what-if-scenarios-01
    provides: [WhatIf types, MOCK_WHATIF_SESSIONS, /whatif entry page]
provides:
  - 4-panel What-If session page at /whatif/[sessionId]
  - WhatIfRefinementChat component (per-scenario free-form refinement)
  - Scenario list panel with confidence badges and Generate Report button
  - Scenario detail panel with all 6 fields (narrative, impact, assumptions, confidence, rationale, data backing)
affects: [phase 45-03 if any, report pages consuming rep-whatif-001]

tech-stack:
  added: []
  patterns:
    - key prop remount pattern for resetting child component state on scenario switch
    - 3-column fixed/flex/fixed panel layout within workspace content area
    - Per-bubble chat thread (user=right/primary, assistant=left/muted)

key-files:
  created:
    - pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]/page.tsx
    - pulse-mockup/src/components/workspace/whatif-refinement-chat.tsx
  modified: []

key-decisions:
  - "key={selectedScenarioId} on WhatIfRefinementChat causes React to remount on scenario switch, resetting chat state from new initialMessages — no useEffect needed"
  - "Tasks 1 and 2 committed together (single commit) since the page imports the component and both must exist for TypeScript to compile"

patterns-established:
  - "key prop remount: parent passes key={selectedId} on child component to reset all internal state when selection changes"
  - "Confidence badge colors: high=emerald-400/emerald-500/30, medium=amber-400/amber-500/30, low=muted-foreground/border"

requirements-completed: [WHAT-03, WHAT-04, WHAT-05, WHAT-06]

duration: 1min
completed: 2026-03-05
---

# Phase 45 Plan 02: WhatIf Session Page Summary

**4-panel What-If session page with confidence-badged scenario list, 6-field detail view, and per-scenario refinement chat — all linked by live scenario switching via React key remount.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-05T15:47:56Z
- **Completed:** 2026-03-05T15:49:00Z
- **Tasks:** 2
- **Files modified:** 2 (both new)

## Accomplishments

- Built `/whatif/[sessionId]` route with 3-column layout: 280px scenario list, flex-1 detail panel, 300px refinement chat
- Scenario list auto-selects first scenario on mount; confidence badges use emerald/amber/muted color logic; Generate What-If Report button navigates to report page
- Scenario detail panel renders all 6 fields with Card sections: narrative, estimated impact (highlighted block), assumptions (CheckCircle list), confidence + rationale, data backing
- WhatIfRefinementChat component: scrollable bubble thread, empty-state placeholder, Textarea + Send button, Enter key shortcut, auto-scroll to bottom on new messages
- Scenario switching updates detail panel and chat panel simultaneously via `key={selectedScenarioId}` React remount pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Build WhatIf session page with 4-panel layout, scenario list, and scenario detail** - `0d2bc6a` (feat)
2. **Task 2: Build WhatIfRefinementChat component** - `0d2bc6a` (feat, combined with Task 1)

Note: Tasks 1 and 2 were committed together since the session page imports the chat component — both needed to compile cleanly.

**Plan metadata:** (committed below)

## Files Created/Modified

- `pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]/page.tsx` — 4-panel What-If session page; auto-selects first scenario; passes key+scenario+initialMessages to chat component
- `pulse-mockup/src/components/workspace/whatif-refinement-chat.tsx` — Per-scenario refinement chat panel; hardcoded AI response on send; auto-scrolls on new messages

## Decisions Made

- **key prop remount pattern:** Parent passes `key={selectedScenarioId}` to `WhatIfRefinementChat` so React automatically remounts the component when a different scenario is selected, resetting all internal state (messages, input) from the new `initialMessages` prop — no useEffect or manual reset needed.
- **Combined commit:** Tasks 1 and 2 committed in one commit because Task 1's page has a TypeScript import of Task 2's component; staging only Task 1 would produce a compile error.
- **WHAT-05 and WHAT-06 not implemented:** These requirements (Add Scenario action, side-by-side comparison) are explicitly dropped/deferred per the user decision documented in CONTEXT.md. Requirement IDs appear in frontmatter for traceability only.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- What-If session page is fully functional: scenario selection, detail view, refinement chat, and report navigation all work
- Phase 45 is complete — both plans (01 objective selection + 02 session page) are done
- If Phase 45-03 exists it would build on MOCK_WHATIF_SESSIONS and the established panel pattern

---
*Phase: 45-what-if-scenarios*
*Completed: 2026-03-05*

## Self-Check: PASSED

- FOUND: `pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]/page.tsx`
- FOUND: `pulse-mockup/src/components/workspace/whatif-refinement-chat.tsx`
- FOUND: `.planning/phases/45-what-if-scenarios/45-02-SUMMARY.md`
- FOUND: commit `0d2bc6a` — feat(45-02)
