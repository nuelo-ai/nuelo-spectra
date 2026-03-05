---
quick_task: 4
subsystem: requirements
tags: [documentation, ux, requirements, mockup, v0.7.12]
key-files:
  modified:
    - requirements/Spectra-Pulse-Requirement.md
    - requirements/Pulse-req-milestone-plan.md
decisions:
  - "Mockup v0.7.12 is the source of truth for v0.8+ implementation — requirements docs updated to match"
  - "Severity values in mockup UI are critical/warning/info only — no opportunity severity badge"
  - "COLL-01 (no archive/unarchive action) and COLL-02 (no limit display) documented as known gaps for v0.9"
  - "WHAT-05 (Add Scenario) and WHAT-06 (comparison view) deferred from mockup, noted in v0.11 scope"
metrics:
  duration: 5min
  completed: "2026-03-05"
  tasks: 3
  files: 2
---

# Quick Task 4: Update Requirements Docs to Reflect v0.7.12 Summary

**One-liner:** Updated both Pulse requirements documents to replace original brainstorm UX flow with exact v0.7.12 mockup implementation — 4-tab collection detail, full-page DetectionLoading, dedicated Detection Results page, investigation closing-question-to-report flow, and 3-panel What-If session page.

---

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Audit mockup vs. requirements and capture all UX deviations | (mental audit — no files changed) | — |
| 2 | Update Spectra-Pulse-Requirement.md — UX/screen flow sections only | b8c89c3 | requirements/Spectra-Pulse-Requirement.md |
| 3 | Update Pulse-req-milestone-plan.md — frontend scope sections only | 7a2930c | requirements/Pulse-req-milestone-plan.md |

---

## Changes Made

### Spectra-Pulse-Requirement.md — Section 6 (User Journey)

- Replaced the mermaid user journey diagram with an updated version reflecting the actual implemented flow: Collections landing page, 4-tab collection detail, full-page DetectionLoading, Detection Results as separate page, investigation closing-question flow to report, What-If objective page → loading → 3-panel session page.
- Rewrote Step 1 to describe: sidebar "Analysis Workspace" entry with "Collections" landing title, 4-tab collection detail (Overview/Files/Signals/Reports), DataSummaryPanel on file click, sticky action bar with "Run Detection (5 credits)", full-page DetectionLoading.
- Rewrote Step 2 to describe: two-column Detection Results page, auto-selection of highest severity signal, SignalDetailPanel sections, Investigation section with enable/disable conditions for buttons, Guided Investigation page with Q&A thread, closing-question flow with discuss-something rounds, InvestigationCheckpoint → report generation (no root cause card), Investigation Report with Related Signals and What-If CTA.
- Rewrote Step 3 to describe: two entry points for What-If (SignalDetailPanel + Investigation Report CTA), Objective page with search-bar UX + suggestion dropdown, inline loading with 4 steps, 3-panel Session page (scenario list + scenario detail + sliding Refine overlay), "Generate What-If Report" action.
- Rewrote Step 4 to describe: auto-save, Reports tab, report viewer as full-page with sticky header, markdown rendering, Download as Markdown (functional) / PDF (disabled).
- Added new "Known Gaps (Mockup vs. Full Spec)" subsection documenting COLL-01 and COLL-02.

### Pulse-req-milestone-plan.md — Frontend Scope sections

- **v0.8 Frontend Scope:** Replaced with 4-tab collection detail layout, DataSummaryPanel, sticky action bar, full-page DetectionLoading, Detection Results two-column page, severity scheme (critical/warning/info — no opportunity badge in mockup UI).
- **v0.9 Frontend Scope:** Replaced with full-page report viewer (sticky header, paper layout, type-conditional sections), AddToCollectionModal (active collections only, success state, create link), COLL-01 and COLL-02 gap callouts.
- **v0.10 Frontend Scope:** Replaced with Guided Investigation page spec (sticky header, signal context block, Q&A thread, closing-question flow with discuss rounds, InvestigationCheckpoint, no root cause card), updated SignalDetailPanel investigation section (past reports list, What-If enable condition).
- **v0.11 Frontend Scope:** Replaced with Objective page (search-bar UX, suggestion dropdown with onMouseDown fix), inline loading state (4 animated steps), 3-panel Session page (scenario list with Generate Report button, scenario detail with 5 cards, sliding Refine overlay with per-scenario chat remount), WHAT-05 and WHAT-06 deferred callouts.

---

## Deviations from Plan

None — plan executed exactly as written. Task 1 was a mental audit (no file changes), Tasks 2 and 3 made the described UX/screen flow updates to the specified sections only.

---

## Verification Results

1. "opportunity" in screen flow descriptions: Not present in Section 6. Remaining occurrences are in Section 3 (product naming rationale) and Section 5 (ER diagram severity field) — both acceptable per plan.
2. COLL-01 appears in both files. COLL-02 appears in both files.
3. WHAT-05 and WHAT-06 deferred status documented in v0.11 Frontend Scope.
4. No pulse-mockup/ or codebase files were modified — only requirements/ files changed.

## Self-Check: PASSED

- requirements/Spectra-Pulse-Requirement.md modified: confirmed (commit b8c89c3)
- requirements/Pulse-req-milestone-plan.md modified: confirmed (commit 7a2930c)
- No files outside requirements/ modified: confirmed (git status shows only expected untracked files)
