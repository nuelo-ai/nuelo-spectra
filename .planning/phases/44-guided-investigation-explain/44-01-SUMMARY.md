---
phase: 44-guided-investigation-explain
plan: "01"
subsystem: pulse-mockup
tags: [investigation, mock-data, signal-card, signal-detail-panel, types]
dependency_graph:
  requires: []
  provides:
    - InvestigationStatus type
    - InvestigationSession type
    - QAExchange type
    - RelatedSignal type
    - MOCK_INVESTIGATION_SESSIONS export
    - Investigation badge on SignalCard
    - Investigation section on SignalDetailPanel
  affects:
    - pulse-mockup/src/lib/mock-data.ts
    - pulse-mockup/src/components/workspace/signal-card.tsx
    - pulse-mockup/src/components/workspace/signal-detail-panel.tsx
tech_stack:
  added: []
  patterns:
    - Investigation status badge using existing Badge component pattern (variant=outline with custom color classes)
    - Link-wrapped Button for navigation to investigate route
    - Filter + reverse pattern for most-recent-first report list
key_files:
  created: []
  modified:
    - pulse-mockup/src/lib/mock-data.ts
    - pulse-mockup/src/components/workspace/signal-card.tsx
    - pulse-mockup/src/components/workspace/signal-detail-panel.tsx
    - pulse-mockup/src/app/workspace/collections/[id]/signals/page.tsx
decisions:
  - RelatedSignal type placed before Report interface so it can be referenced in Report.relatedSignals
  - Investigation section replaces the disabled Tooltip/Investigate button block entirely (no "Coming soon" fallback retained)
  - collectionId added as required prop on SignalDetailPanel (not optional) to enforce correct usage
  - Report list uses slice().reverse() to avoid mutating the source MOCK_INVESTIGATION_SESSIONS array
metrics:
  duration: "~8 minutes"
  completed_date: "2026-03-04"
  tasks_completed: 2
  files_modified: 4
---

# Phase 44 Plan 01: Investigation Data Model and Signal Entry Points Summary

**One-liner:** Investigation data model (InvestigationStatus, InvestigationSession, QAExchange, RelatedSignal) wired into signal cards and detail panel with live Investigate button and past-report list.

## What Was Built

This plan established the investigation data foundation for Phase 44. All downstream plans (Plan 02: Q&A page, Plan 03: report viewer) import types and data from `mock-data.ts` which is now extended with the investigation domain.

### Task 1: Investigation types and mock data (mock-data.ts)

New types added:
- `InvestigationStatus` — `"none" | "in-progress" | "complete"`
- `QAExchange` — single Q&A round with choices array and selectedChoice
- `InvestigationSession` — full session record linking signal, collection, status, and exchanges
- `RelatedSignal` — cross-signal link for report footers

Extended types:
- `Report` interface extended with optional `signalId?: string` and `relatedSignals?: RelatedSignal[]`

New mock data:
- `MOCK_INVESTIGATION_SESSIONS` with 3 sessions: `inv-001` (sig-001, complete, 3 exchanges), `inv-002` (sig-001, complete, 2 exchanges), `inv-003` (sig-002, in-progress, 1 answered + 1 unanswered)
- Two investigation Report entries added to `MOCK_REPORTS`: `rpt-inv-001` (Enterprise Pricing Impact) and `rpt-inv-002` (Seasonal Demand Hypothesis) — both with full markdown content and proper `signalId`/`relatedSignals` fields

### Task 2: Signal card badge and detail panel Investigation section

`signal-card.tsx`:
- Imports `MOCK_INVESTIGATION_SESSIONS` and `InvestigationStatus`
- Computes latest status from the last session for the signal
- Renders amber "Investigating" badge for in-progress, emerald "Investigated" badge for complete; nothing for "none"

`signal-detail-panel.tsx`:
- Props extended with `collectionId: string`
- Imports removed: `Tooltip`, `TooltipTrigger`, `TooltipContent`, `Search`
- Imports added: `Link`, `Microscope`, `MOCK_INVESTIGATION_SESSIONS`, `MOCK_REPORTS`
- Actions section replaced entirely with Investigation section containing:
  - Active Link-wrapped Button to `/workspace/collections/{collectionId}/signals/{signalId}/investigate`
  - Compact past-reports list (most recent first) showing date, title, and Complete badge
  - "No investigations yet" fallback for signals with no sessions

`signals/page.tsx`:
- Passes `collectionId` prop to `SignalDetailPanel`

## Verification

TypeScript compiles without errors after both tasks (`npx tsc --noEmit`).

Expected behavior in browser:
- `sig-001` (Revenue Anomaly) shows "Investigated" (emerald) badge in card list
- `sig-002` (Customer Churn) shows "Investigating" (amber) badge in card list
- Other signals show no investigation badge
- Selecting `sig-001` in detail panel: Investigation section with Investigate button and 2 past report rows
- Selecting `sig-002` in detail panel: Investigation section with Investigate button, no past reports

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 5290da3 | feat(44-01): add investigation types and mock data to mock-data.ts |
| 2 | dc551cf | feat(44-01): add investigation status badge to signal-card and Investigation section to signal-detail-panel |

## Self-Check: PASSED

All key files found. Both task commits verified in git log.
