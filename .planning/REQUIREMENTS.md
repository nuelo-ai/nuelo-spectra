# Requirements: Spectra v0.8 Spectra Pulse (Detection)

**Defined:** 2026-03-05
**Core Value:** Accurate data analysis through correct, safe Python code generation

---

## v0.8 Requirements

Requirements for the Spectra Pulse (Detection) milestone. Each maps to roadmap phases starting at Phase 47.

### Collections

- [x] **COLL-01**: User can create a new Collection (name-only dialog via "Create Collection" button)
- [x] **COLL-02**: User can view their Collections as a grid of cards (name, status badge, created date, file count, signal count)
- [x] **COLL-03**: User can view a Collection detail page with 4-tab layout (Overview, Files, Signals, Reports)
- [x] **COLL-04**: User can update a Collection's name/description

### Files

- [x] **FILE-01**: User can upload CSV/Excel files to a Collection via drag-drop or click (FileUploadZone)
- [x] **FILE-02**: User can view column profile of a file in a slide-out DataSummaryPanel (clicking a file row)
- [x] **FILE-03**: User can select files via checkboxes to activate the sticky action bar (shows selected count + Run Detection button)
- [x] **FILE-04**: User can remove a file from a Collection

### Pulse Detection

- [x] **PULSE-01**: User can trigger Pulse detection on selected files via "Run Detection (N credits)" button showing the configured flat credit cost
- [x] **PULSE-02**: System pre-checks credit balance before execution and blocks run if insufficient (shows upgrade/add credits prompt)
- [x] **PULSE-03**: System deducts flat credit cost (workspace_credit_cost_pulse) before execution and refunds on failure
- [x] **PULSE-04**: User sees full-page detection loading state with 4 animated steps replacing entire page content (Profiling data → Detecting anomalies → Analyzing trends → Generating signals)
- [x] **PULSE-05**: After detection completes, user is navigated to Detection Results page with generated Signals

### Signals

- [ ] **SIGNAL-01**: User can view Signal list sorted by severity (critical → warning → info) on Detection Results page (/workspace/collections/[id]/signals)
- [ ] **SIGNAL-02**: Highest-severity Signal is auto-selected on Detection Results page load
- [ ] **SIGNAL-03**: User can view Signal detail panel with: title + severity/category badges, Recharts chart visualization, analysis text, 2x2 statistical evidence grid, Investigation section (Investigate + What-If buttons — buttons present but disabled with "coming soon" or disabled state)
- [ ] **SIGNAL-04**: Signal chart type is driven by signal's chartType field (bar → BarChart, line → AreaChart, scatter → ScatterChart via Recharts)

### Reports

- [x] **REPORT-01**: User can view Reports tab listing all collection reports as rows (type badge, title, source line, generated date, "View Report" button)
- [x] **REPORT-02**: User can open a full-page report viewer (/workspace/collections/[id]/reports/[reportId]) with sticky header (back button, report title, type badge), white paper area, markdown-rendered content
- [x] **REPORT-03**: User can download a report as Markdown (functional download)
- [x] **REPORT-04**: "Download as PDF" button is present but disabled (opacity-60 — planned v0.9 backend feature)

### Navigation & Overview

- [ ] **NAV-01**: User can access Pulse Analysis from sidebar ("Pulse Analysis" entry → /workspace); sidebar also shows Chat, Files, API, Settings, Admin Panel (only /workspace, /chat, /admin are live routes)
- [ ] **NAV-02**: Collection Overview tab shows stat cards (files count, signal count, reports count, credits used), Run Detection banner, 2-column grid of up to 4 Signal card previews (non-interactive), compact file table with "View all files" link, activity feed
- [ ] **NAV-03**: Collection Signals tab shows all Signal cards (non-interactive) and "Open Signals View" button navigating to Detection Results page
- [ ] **NAV-04**: Collection detail header shows running credit usage pill ("Credits used: N" with Zap icon)

### Admin

- [x] **ADMIN-01**: Tier-based workspace access enforced on Collection creation — workspace_access (boolean) and max_active_collections (integer, -1 = unlimited) per tier in user_classes.yaml; tier defaults: free_trial=1, free=0 (no access), standard=5, premium=unlimited, internal=unlimited
- [x] **ADMIN-02**: workspace_credit_cost_pulse configurable via Admin Portal platform settings (runtime configurable, no redeploy required); default: 5.0 credits

---

## v0.9 Requirements (Future)

Deferred to v0.9 Collections (Workspace Persistence) milestone.

### Collection Management

- **COLL-05**: User can archive a Collection (action button on list and detail pages) — COLL-01 known mockup gap
- **COLL-06**: User can unarchive a Collection — COLL-01 known mockup gap
- **COLL-07**: User can see collection limit usage display ("X of Y active collections") — COLL-02 known mockup gap
- **COLL-08**: User sees upgrade prompt when collection limit is reached

### Chat Bridge

- **BRIDGE-01**: User can add a Chat result card to a Collection via "Add to Collection" modal
- **BRIDGE-02**: AddToCollectionModal shows only active collections with name, signal count, file count

### Reports (Extended)

- **REPORT-05**: User can compile a Pulse Summary report from Signals (POST /collections/{id}/reports)
- **REPORT-06**: PDF export backend implementation ("Download as PDF" becomes functional)

---

## Out of Scope

Explicitly excluded from v0.8. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Guided Investigation (Explain) | v0.10 — requires Investigation Agent and Q&A flow |
| What-If Scenarios | v0.11 — requires Strategy Agent and scenario generation |
| Admin Workspace Activity Dashboard | v0.12 — requires all workspace features to exist for meaningful analytics |
| Monitoring / scheduled re-runs | Post-v0.12 backlog — requires scheduling infrastructure |
| Sensitivity threshold sliders for signals | Anti-feature — users lack statistical expertise to tune safely; severity tiers are the correct UX |
| "Opportunity" as a 4th severity level | Severity maps to urgency not valence; valence belongs in signal title text |
| Celery / async task queue for Pulse | E2B execution is the bottleneck; async queue adds infrastructure without UX improvement |
| Real-time SSE progress during Pulse run | Polling/timer fallback is pragmatic for v0.8; SSE from Pulse endpoint is a future optimization |
| PDF export (functional) | v0.9 — button present but disabled in mockup |
| Chat-to-Collection bridge | v0.9 |

---

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| COLL-01 | Phase 48 | Complete |
| COLL-02 | Phase 48 | Complete |
| COLL-03 | Phase 48 | Complete |
| COLL-04 | Phase 48 | Complete |
| FILE-01 | Phase 48 | Complete |
| FILE-02 | Phase 48 | Complete |
| FILE-03 | Phase 48 | Complete |
| FILE-04 | Phase 48 | Complete |
| PULSE-01 | Phase 50 | Complete |
| PULSE-02 | Phase 49 | Complete |
| PULSE-03 | Phase 49 | Complete |
| PULSE-04 | Phase 50 | Complete |
| PULSE-05 | Phase 50 | Complete |
| SIGNAL-01 | Phase 51 | Pending |
| SIGNAL-02 | Phase 51 | Pending |
| SIGNAL-03 | Phase 51 | Pending |
| SIGNAL-04 | Phase 51 | Pending |
| REPORT-01 | Phase 48 | Complete |
| REPORT-02 | Phase 48 | Complete |
| REPORT-03 | Phase 48 | Complete |
| REPORT-04 | Phase 48 | Complete |
| NAV-01 | Phase 51 | Pending |
| NAV-02 | Phase 51 | Pending |
| NAV-03 | Phase 51 | Pending |
| NAV-04 | Phase 51 | Pending |
| ADMIN-01 | Phase 47 | Complete |
| ADMIN-02 | Phase 47 | Complete |

**Coverage:**
- v0.8 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---

*Requirements defined: 2026-03-05*
*Last updated: 2026-03-05 — traceability filled after roadmap creation (Phases 47-52)*
