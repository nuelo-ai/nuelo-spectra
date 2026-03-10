---
phase: 44-guided-investigation-explain
plan: "02"
subsystem: ui
tags: [investigation, qa-thread, checkpoint, next-js, shadcn, mockup]

requires:
  - phase: 44-guided-investigation-explain/44-01
    provides: InvestigationSession/QAExchange types and MOCK_INVESTIGATION_SESSIONS in mock-data.ts
provides:
  - InvestigationQAThread component (scrollable completed + active Q&A exchange)
  - InvestigationCheckpoint component (Sparkles card with Proceed button and generating state)
  - Full investigation page route at /workspace/collections/[id]/signals/[signalId]/investigate
affects:
  - 44-guided-investigation-explain/44-03 (report viewer — investigation page navigates there on Proceed)

tech-stack:
  added: []
  patterns:
    - "useState callback initializer for computing initial showCheckpoint state at mount"
    - "Functional state update in handleSelectChoice/handleFreeText to avoid stale closures then call side-effect checkForCheckpoint"
    - "null render from InvestigationQAThread when all exchanges complete (parent shows checkpoint instead)"

key-files:
  created:
    - pulse-mockup/src/components/workspace/investigation-qa-thread.tsx
    - pulse-mockup/src/components/workspace/investigation-checkpoint.tsx
    - pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/investigate/page.tsx
  modified: []

key-decisions:
  - "InvestigationQAThread returns null when all exchanges complete — parent page owns checkpoint visibility via showCheckpoint state"
  - "checkForCheckpoint called after functional setExchanges update to ensure it receives latest array"
  - "useState initializer function used for showCheckpoint to correctly derive initial value from mock sessions at mount"
  - "handleProceed always navigates to rpt-inv-001 (hardcoded for mockup) regardless of which signal is being investigated"

requirements-completed:
  - EXPL-02
  - EXPL-03

duration: ~2min
completed: 2026-03-04
---

# Phase 44 Plan 02: Investigation Q&A Page Summary

**Doctor-style conversational Q&A investigation page with scrollable exchange thread, radio-choice buttons, free-text fallback, and checkpoint card that triggers 2-second generation loading then report navigation.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-04T19:26:44Z
- **Completed:** 2026-03-04T19:28:30Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments

- Built `InvestigationQAThread` — renders collapsed past exchange pairs (Spectra/You labels, muted text) above the active question with left-accent border, full-width choice buttons, and optional free-text Textarea+Submit
- Built `InvestigationCheckpoint` — primary/5 bordered card with Sparkles icon, "Ready to generate report" heading, optional context textarea, and Proceed button that swaps to Loader2 spinner while generating
- Built full investigation page route — sticky header with Back link + "Guided Investigation" title + credits badge, signal context block, Q&A thread wired to exchange state, checkpoint shown when all exchanges answered, 2s timer then navigation to report viewer

## Task Commits

1. **Task 1: InvestigationQAThread and InvestigationCheckpoint components** - `4372a5c` (feat)
2. **Task 2: Investigation page route** - `a0ecc5a` (feat)

## Files Created/Modified

- `pulse-mockup/src/components/workspace/investigation-qa-thread.tsx` - Scrollable Q&A thread: completed exchanges collapsed above active question with choice buttons and free-text area
- `pulse-mockup/src/components/workspace/investigation-checkpoint.tsx` - Checkpoint summary card with Sparkles icon, Proceed button, and Loader2 generating state
- `pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/investigate/page.tsx` - Full-page investigation route; selects in-progress session or most recent complete session; checkpoint triggers on all-answered state

## Decisions Made

- `InvestigationQAThread` returns null when all exchanges are complete — parent page controls checkpoint visibility via `showCheckpoint` state rather than threading it through the component.
- Used functional state update pattern (`setExchanges(prev => ...)`) in handlers so `checkForCheckpoint` receives the latest array and avoids stale closure issues.
- Used `useState` with initializer function for `showCheckpoint` so sig-001 (which loads a fully-answered complete session) shows the checkpoint immediately on mount.
- `handleProceed` navigates to `rpt-inv-001` hardcoded — acceptable for mockup; in production this would use the session's `reportId`.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Investigation page fully functional: sig-001 shows checkpoint immediately, sig-002 shows 1 completed + 1 active exchange
- Clicking "Proceed with Report" navigates to `/workspace/collections/col-001/reports/rpt-inv-001`
- Plan 03 (report viewer) can build on the `rpt-inv-001` / `rpt-inv-002` mock report data established in Plan 01

---
*Phase: 44-guided-investigation-explain*
*Completed: 2026-03-04*

## Self-Check: PASSED

- investigation-qa-thread.tsx: FOUND
- investigation-checkpoint.tsx: FOUND
- investigate/page.tsx: FOUND
- commit 4372a5c: FOUND
- commit a0ecc5a: FOUND
