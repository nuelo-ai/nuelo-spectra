# Quick Task 7: Update Requirements Docs — Restructure Milestones

**Date:** 2026-03-14
**Description:** Update requirements docs: move Reporting to v0.8 (already built), drop v0.9, drop Guided Investigation (v0.10), keep What-If as new v0.9 (direct from Signal), Admin becomes v0.10. Archive old Spectra-Pulse-Requirement.md and create v2.

## Tasks

### Task 1: Archive Spectra-Pulse-Requirement.md
- **Files:** `requirements/Spectra-Pulse-Requirement.md` → `requirements/Spectra-Pulse-Requirement-v1-archived.md`
- **Action:** Add archive notice header to the file, rename it
- **Done:** File renamed with archive notice

### Task 2: Create Spectra-Pulse-Requirement-v2.md
- **Files:** `requirements/Spectra-Pulse-Requirement-v2.md` (new)
- **Action:** Updated requirements with:
  - New decisions in log (drop Investigation, What-If direct from Signal)
  - Data model: remove Investigation and RootCause tables
  - User Journey: remove Explain/Q&A step, update What-If entry (direct from Signal, no prerequisite)
  - Admin section: remove investigation credit costs
- **Done:** File created

### Task 3: Update Pulse-req-milestone-plan.md
- **Files:** `requirements/Pulse-req-milestone-plan.md`
- **Action:** Restructure milestones:
  - v0.8 ✅ (already shipped — includes Reporting, no changes to shipped scope)
  - v0.9 dropped (Collections/Chat bridge deferred)
  - v0.10 dropped (Guided Investigation dropped)
  - What-If → new v0.9 (direct Signal entry, no investigation prerequisite)
  - Admin → new v0.10
  - Update milestone summary, credit costs, agent table
- **Done:** File updated
