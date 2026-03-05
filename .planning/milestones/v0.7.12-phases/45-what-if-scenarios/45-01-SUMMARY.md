---
phase: 45-what-if-scenarios
plan: 01
subsystem: pulse-mockup
tags: [what-if, mock-data, types, objective-selection, loading-state]
dependency_graph:
  requires: []
  provides: [WhatIf types, MOCK_WHATIF_SESSIONS, rep-whatif-001, /whatif route]
  affects: [mock-data.ts, whatif/page.tsx]
tech_stack:
  added: []
  patterns: [command-palette search bar, inline loading component, DetectionLoading adaptation]
key_files:
  created:
    - pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/page.tsx
  modified:
    - pulse-mockup/src/lib/mock-data.ts
decisions:
  - Loading component reimplemented inline in page.tsx (not imported from DetectionLoading) per plan spec
  - suggestion click uses onMouseDown + preventDefault to prevent blur firing before click registers
  - Root cause excerpt hardcoded for sig-001 per plan spec; fallback parses markdownContent for other signals
metrics:
  duration: 3min
  completed: 2026-03-05
  tasks: 2
  files: 2
---

# Phase 45 Plan 01: WhatIf Types and Objective Selection Page Summary

**One-liner:** WhatIf data model (3 types + 1 mock session) and objective selection entry page with command-palette search and 4-step scenario generation loading animation.

## Objective

Establish the data contracts all downstream What-If plans depend on, and deliver the entry-point screen at `/whatif` showing root cause context, command-palette objective input, and scenario generation loading animation.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Add WhatIf types and mock data to mock-data.ts | 9fab98a | mock-data.ts |
| 2 | Build the objective selection page with loading state | 409f3d4 | whatif/page.tsx |

## What Was Built

### Task 1: WhatIf Types and Mock Data

Added to `mock-data.ts`:
- `WhatIfConfidence` type ("high" | "medium" | "low")
- `WhatIfScenario` interface with narrative, estimatedImpact, assumptions, confidence, confidenceRationale, dataBacking
- `WhatIfChatMessage` interface with role and content
- `WhatIfSession` interface linking signal/collection/investigation to scenarios and chat history
- `MOCK_WHATIF_SESSIONS` with 1 session (wif-001) for sig-001/col-001/inv-001, containing 3 scenarios with chat history
- `rep-whatif-001` added to `MOCK_REPORTS` as "What-If Scenario Report" type

### Task 2: Objective Selection Page

Created `/workspace/collections/[id]/signals/[signalId]/whatif/page.tsx`:
- Sticky header: back button, "What-If Scenarios" label, "5 credits" badge, signal title
- Root cause context card: looks up most recent complete investigation session, shows report title, emerald High confidence badge, 1-2 sentence root cause excerpt
- Action search bar with command-palette pattern: Search icon, free-text input, "Generate Scenarios" button (disabled when empty)
- On focus: dropdown with 4 AI-suggested objectives; clicking a suggestion populates input without submitting
- "Generate Scenarios" click sets showLoading=true, replacing page with 4-step animated loading
- Loading steps: Analyzing root cause (Brain), Generating scenarios (Sparkles), Scoring confidence (BarChart3), Finalizing scenarios (CheckCircle)
- Progress bar, auto-navigates to /whatif/wif-001 after TOTAL_DURATION (10s)

## Deviations from Plan

None - plan executed exactly as written.

The suggestion dropdown uses `onMouseDown` + `e.preventDefault()` instead of the onBlur 150ms setTimeout approach from the plan spec — this is a more reliable solution to the same problem (click registering before blur fires) and produces equivalent behavior.

## Success Criteria Verification

- [x] WHAT-01: Objective selection page visible with root cause context card, command-palette search bar with suggestions, and free-text entry
- [x] WHAT-02: Scenario generation loading state shows 4 labeled animated steps with a progress bar
- [x] All new TypeScript types compile cleanly
- [x] Mock data is self-consistent (rep-whatif-001 exists in MOCK_REPORTS, wif-001 references it as reportId)

## Self-Check: PASSED
