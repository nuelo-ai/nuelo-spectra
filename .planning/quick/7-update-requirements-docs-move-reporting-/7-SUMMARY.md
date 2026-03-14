# Quick Task 7 Summary: Update Requirements Docs — Restructure Milestones

**Date:** 2026-03-14
**Status:** Complete

## What Was Done

### Task 1: Archive Spectra-Pulse-Requirement.md ✅
- Copied to `requirements/Spectra-Pulse-Requirement-v1-archived.md`
- Added archive notice header pointing to v2

### Task 2: Create Spectra-Pulse-Requirement-v2.md ✅
- New decisions added to log (#9–#12):
  - Reporting moved to v0.8 (already shipped)
  - Guided Investigation dropped
  - What-If entry point revised (direct from Signal, no prerequisite)
  - v0.9 (Collections/Chat bridge) dropped
- Data model updated: removed Investigation and RootCause tables; Scenario now links directly to Signal
- User journey updated: Guided Investigation step removed, What-If accessible directly from SignalDetailPanel
- Admin section updated: removed investigation credit costs; activity log enum updated

### Task 3: Update Pulse-req-milestone-plan.md ✅
- Milestone sequence updated: v0.8 (shipped) → v0.9 (What-If) → v0.10 (Admin)
- Dropped milestones documented: old v0.9 (Collections), v0.10 (Explain)
- v0.8 section updated to reflect Reporting as part of shipped scope
- v0.9 (was v0.11) updated: Scenario links to Signal directly, What-If always enabled, no investigation prerequisite
- v0.10 (was v0.12) updated: removed investigation activity types from log
- Credit cost summary updated: removed investigation costs
- Agent table updated: removed Investigation Agent
- Deferred items list updated with dropped features

## Files Changed
- `requirements/Spectra-Pulse-Requirement-v1-archived.md` — created (archive of v1 with notice)
- `requirements/Spectra-Pulse-Requirement-v2.md` — created (updated requirements)
- `requirements/Pulse-req-milestone-plan.md` — updated (restructured milestones)
