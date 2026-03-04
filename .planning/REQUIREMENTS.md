# Requirements: Spectra

**Defined:** 2026-03-03
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.7.11 Requirements (Spectra Pulse Mockup)

Mockup screens for the full Analysis Workspace feature set (v0.8–v0.12 scope). These are static/interactive frontend mockup pages built as standalone design references — no live backend integration.

### Analysis Workspace (Pulse Detection)

- [x] **PULSE-01**: Designer can view a mockup of the Analysis Workspace entry page with navigation and branding (separate from Chat)
- [x] **PULSE-02**: Designer can view a Collection list page showing name, status (active/archived), created date, and signal count
- [x] **PULSE-03**: Designer can view a "Create New Collection" flow with name input
- [x] **PULSE-04**: Designer can view a Collection detail page with file selection area (pick from uploaded files or upload new)
- [x] **PULSE-05**: Designer can view the "Run Detection" button with credit cost display and loading/progress state (15–30s indicator)
- [x] **PULSE-06**: Designer can view the Signal cards layout — left scrollable panel (title, severity badge, category tag) + main detail panel
- [x] **PULSE-07**: Designer can view a Signal detail view: title, description, severity badge (color-coded), category tag, visualization chart area, statistical evidence summary
- [x] **PULSE-08**: Designer can view credit balance indicator and pre-action cost estimate ("This will use ~5 credits")

### Collections & Reports

- [ ] **COLL-01**: Designer can view archive/unarchive actions and status indicators (active vs. archived badge)
- [ ] **COLL-02**: Designer can view Collection limit usage display ("3 of 5 active collections") and upgrade prompt
- [x] **COLL-03**: Designer can view a Report list with type, title, and generated date
- [x] **COLL-04**: Designer can view an in-page Report reader with rendered markdown and proper typography
- [x] **COLL-05**: Designer can view Download options: "Download as Markdown" and "Download as PDF" buttons
- [x] **COLL-06**: Designer can view the Chat-to-Collection bridge — "Add to Collection" action on a data card with Collection picker modal
- [x] **COLL-07**: Designer can view running credit total in Collection header ("Credits used: 14")

### Explain (Guided Investigation)

- [x] **EXPL-01**: Designer can view an "Investigate" button on a Signal card and investigation status indicator
- [x] **EXPL-02**: Designer can view the doctor-style Q&A interview flow: hypothesis text + structured choices (radio) + free-text option
- [x] **EXPL-03**: Designer can view a progress indicator showing narrowing scope over 3–5 exchange steps
- [ ] **EXPL-04**: Designer can view a Root Cause summary card: hypothesis statement, confidence badge (high/medium/low), supporting evidence
- [x] **EXPL-05**: Designer can view investigation history list (date, status, root cause summary, exchange count)
- [ ] **EXPL-06**: Designer can view which Signals a root cause links to (cross-signal connection display)

### What-If Scenarios

- [ ] **WHAT-01**: Designer can view the Objective selection screen: root cause context + selection choices + free-text option
- [ ] **WHAT-02**: Designer can view the scenario generation loading state with progress indicator
- [ ] **WHAT-03**: Designer can view Scenario cards: name, narrative, estimated impact range, assumptions, confidence badge + rationale, data backing summary
- [ ] **WHAT-04**: Designer can view a per-scenario refinement chat panel (scoped, not freeform)
- [ ] **WHAT-05**: Designer can view the "Add Scenario" action (2 credits) alongside existing scenarios
- [ ] **WHAT-06**: Designer can view the side-by-side comparison view: scenario name, impact range, confidence, time to impact, and Select action
- [ ] **WHAT-07**: Designer can view a generated What-If Report section showing objective + evaluated scenarios + selected approach

### Admin Workspace Management

- [ ] **ADMIN-01**: Designer can view a Workspace Activity Dashboard with line chart (Collections over time), donut chart (active vs. archived), bar charts (Pulse/Investigation/What-If/Report activity)
- [ ] **ADMIN-02**: Designer can view a funnel chart showing Pulse → Explain → What-If adoption drop-off
- [ ] **ADMIN-03**: Designer can view workspace credit consumption charts (by activity type over time) and avg credits per Collection KPI card
- [ ] **ADMIN-04**: Designer can view a per-user Workspace tab extension: Collections list, credit breakdown chart, activity timeline, limit usage
- [ ] **ADMIN-05**: Designer can view a Workspace Credit Costs settings section with editable fields for all 8 activity costs
- [ ] **ADMIN-06**: Designer can view an Alerts section with configurable thresholds and active alert list with dismiss actions

## Future Requirements

### Implementation Milestones (v0.8–v0.12)

These are tracked in `requirements/Pulse-req-milestone-plan.md`. Mockup milestone is a design prerequisite only.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live backend integration | Mockup only — no API calls, no real data |
| Monitoring module (recurring analysis) | Deferred post-v0.12 per Decision #6 |
| Persistent AI Memory | Future exploration post-v0.12 per Decision #8 |
| Full predictive ML model | Appendix concept, not in milestone scope |
| User document upload during investigation | Later version per requirements Section 6 Step 2 |
| PDF generation (elaborate templating) | Basic download option only per Decision #5 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PULSE-01 | Phase 42 | Complete |
| PULSE-02 | Phase 42 | Complete |
| PULSE-03 | Phase 42 | Complete |
| PULSE-04 | Phase 42 | Complete |
| PULSE-05 | Phase 42 | Complete |
| PULSE-06 | Phase 42 | Complete |
| PULSE-07 | Phase 42 | Complete |
| PULSE-08 | Phase 42 | Complete |
| COLL-01 | Phase 43 | Pending |
| COLL-02 | Phase 43 | Pending |
| COLL-03 | Phase 43 | Complete |
| COLL-04 | Phase 43 | Complete |
| COLL-05 | Phase 43 | Complete |
| COLL-06 | Phase 43 | Complete |
| COLL-07 | Phase 43 | Complete |
| EXPL-01 | Phase 44 | Complete |
| EXPL-02 | Phase 44 | Complete |
| EXPL-03 | Phase 44 | Complete |
| EXPL-04 | Phase 44 | Pending |
| EXPL-05 | Phase 44 | Complete |
| EXPL-06 | Phase 44 | Pending |
| WHAT-01 | Phase 45 | Pending |
| WHAT-02 | Phase 45 | Pending |
| WHAT-03 | Phase 45 | Pending |
| WHAT-04 | Phase 45 | Pending |
| WHAT-05 | Phase 45 | Pending |
| WHAT-06 | Phase 45 | Pending |
| WHAT-07 | Phase 45 | Pending |
| ADMIN-01 | Phase 46 | Pending |
| ADMIN-02 | Phase 46 | Pending |
| ADMIN-03 | Phase 46 | Pending |
| ADMIN-04 | Phase 46 | Pending |
| ADMIN-05 | Phase 46 | Pending |
| ADMIN-06 | Phase 46 | Pending |

**Coverage:**
- v0.7.11 requirements: 34 total
- Mapped to phases: 34/34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-03 — traceability confirmed after roadmap creation (Phases 42-46)*
