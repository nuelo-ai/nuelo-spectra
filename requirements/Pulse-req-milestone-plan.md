# Spectra Pulse — Milestone Implementation Plan

> Source requirements: [Spectra-Pulse-Requirement.md](./Spectra-Pulse-Requirement.md)

---

## Overview

This document breaks down the full Spectra Pulse (Pulse Analysis) implementation into versioned milestones with clear scope, deliverables, and frontend/backend/admin breakdown per milestone.

> **Frontend Implementation Basis:** The `pulse-mockup/` Next.js app (v0.7.11–v0.7.12) is the authoritative frontend reference for all v0.8–v0.12 milestones. When building the actual functionality, **adopt and migrate the mockup code directly** — component structure, routing, layout, and styling are already production-ready. Do not rebuild the UI from scratch. Replace mock data and hardcoded state with real API calls and backend integration. The mockup routes, component names, and interaction patterns documented in each milestone's Frontend Scope section below correspond directly to files in `pulse-mockup/app/` and `pulse-mockup/components/`.

**Confirmed milestone sequence** (Decisions Log #4):

```
v0.8 (Pulse) -> v0.9 (Collections) -> v0.10 (Explain) -> v0.11 (What-If Scenarios) -> v0.12 (Admin Workspace Management)
```

**Deferred items:**
- Monitoring module (recurring automated analysis) — deferred to post-v0.12 backlog (Decision #6)
- Persistent AI Memory — future exploration post-v0.12 (Decision #8)
- Full predictive ML model — moved to Appendix in requirements, not in milestone scope

---

## Milestone Summary

| Version | Name | Scope | Key Deliverable | Complexity |
|---------|------|-------|-----------------|:---:|
| **v0.8** | Spectra Pulse (Detection) | Create Collections, attach files, run Pulse, view Signals | Signal cards with statistical findings | XL |
| **v0.9** | Collections (Workspace Persistence) | Reports, archiving, Chat-to-Collection bridge | Persistent workspace with downloadable reports | L |
| **v0.10** | Explain (Guided Investigation) | Q&A investigation flow, root cause identification | Doctor-style interview leading to root cause hypothesis | L |
| **v0.11** | What-If Scenarios (Prescriptive) | AI-generated scenarios, refinement, comparison | Data-backed scenario cards with side-by-side comparison | XL |
| **v0.12** | Admin Workspace Management | Activity dashboard, per-user tracking, alerts | Full admin visibility over workspace usage | M |

---

## v0.8 — Spectra Pulse (Detection)

**Goal:** Users can create a Collection, attach data files, run Pulse detection, and view Signals as cards with statistical findings and visualizations.

This is the foundation milestone. It introduces the Pulse Analysis as a new module separate from Chat, establishes the core data model (Collection, File, Signal), and delivers the first stage of the Detect -> Explain -> What-If pipeline.

### Backend Scope

**Data model — new tables:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Collection` | id, name, description, status (active/archived), user_id, created_at, updated_at | The workspace container. See Section 5 ER diagram. |
| `File` | id, collection_id, original_filename, file_type, column_profile (JSON), row_count | Data sources attached to a Collection. |
| `Signal` | id, collection_id, title, description, severity, category, visualization (JSON), statistical_evidence (JSON) | Individual findings from Pulse analysis. |

**API endpoints:**
- `POST /collections` — Create a new Collection
- `GET /collections` — List user's Collections (with pagination, status filter)
- `GET /collections/{id}` — Get Collection detail with Signals
- `PATCH /collections/{id}` — Update Collection name/description
- `DELETE /collections/{id}` — Delete Collection (soft delete or archive)
- `POST /collections/{id}/files` — Attach file(s) to Collection
- `DELETE /collections/{id}/files/{file_id}` — Remove file from Collection
- `POST /collections/{id}/pulse` — Trigger Pulse detection run
- `GET /collections/{id}/signals` — List Signals for a Collection

**Pulse Agent (new agent):**
- Follows existing agent system patterns (extends base agent class)
- Profiles attached data files (column types, distributions, missing values)
- Runs statistical analyses in E2B sandbox:
  - Anomaly detection (statistical outliers, unusual patterns)
  - Trend analysis (time-series trends, period-over-period changes)
  - Concentration analysis (Pareto distributions, segment dominance)
  - Data quality checks (missing data patterns, inconsistencies)
- Generates Signal objects from analysis results
- Each Signal includes: title (key finding headline), description, severity badge (opportunity/warning/critical/info), category, visualization config, statistical evidence

**Credit integration:**
- New platform setting: `workspace_credit_cost_pulse` (default: 5.0)
- Pre-check before Pulse run: verify user has >= 5.0 credits
- Show cost estimate to user before running
- Deduct before execution, refund on failure (follows existing credit pattern)

### Frontend Scope

**Navigation:**
- New "Pulse Analysis" sidebar entry (label: "Pulse Analysis", links to /workspace). Routes: /workspace (Collections list) and /workspace/collections/[id] (Collection detail).
- Sidebar also includes Chat, Files, API, Settings, Admin Panel entries. Only /workspace, /chat, and /admin are live routes — others remain # placeholders.
- Sidebar collapse toggle for desktop. Credit balance shown in the header as a Zap-icon pill.

**Collections list page (/workspace):**
- Grid of Collection cards showing: name, status badge (Active = emerald green, Archived = muted gray), created date, file count, signal count.
- "Create Collection" button opens a dialog with a name field only.
- Empty state shown when no collections exist.

**Collection detail page (/workspace/collections/[id]) — 4-tab layout:**
- Page header: collection name, status badge, credit usage pill ("Credits used: N" with Zap icon).
- Tab 1 — Overview: stat cards (files count, signal count, reports count, credits used), Run Detection banner, 2-column grid of up to 4 Signal cards (non-interactive, link to Detection Results page), compact file table with "View all files in Files tab" link, activity feed.
- Tab 2 — Files: FileUploadZone (drag/drop or click to upload). FileTable with row checkboxes. Clicking a file row opens DataSummaryPanel (slide-out sheet showing column profile). A sticky action bar appears at the bottom when files are selected: shows selected count and "Run Detection (5 credits)" button with credit estimate.
- Tab 3 — Signals: all Signal cards (non-interactive) plus "Open Signals View" button that navigates to the Detection Results page.
- Tab 4 — Reports: list of reports as rows (type badge, title, source line, generated date, "View Report" button).

**Detection loading state:**
- Triggered by "Run Detection" in the Files tab sticky action bar. Replaces the entire page content (full-page transition — not an inline spinner or panel). Animated steps: Profiling data, Detecting anomalies, Analyzing trends, Generating signals. After completion, navigates to the Detection Results page.

**Detection Results page (/workspace/collections/[id]/signals):**
- Breadcrumb header: Collections / [Collection Name] / Detection Results.
- Two-column layout: left = SignalListPanel, right = SignalDetailPanel.
- SignalListPanel: scrollable list sorted by severity (critical first, then warning, then info). Each entry: severity color indicator, signal title, category tag. Auto-selects the highest severity signal on load.
- SignalDetailPanel sections (in order): title + severity/category badges, Visualization card (Recharts chart driven by signal.chartType), Analysis text, Statistical Evidence (2x2 metric grid), Investigation section (Investigate button + What-If button + past investigation report list).
- Severity color scheme: critical = red, warning = amber, info = blue. Note: there is no "opportunity" severity badge in the mockup — severity values are critical, warning, and info only.

### Admin Scope (Minimal for v0.8)

**user_classes.yaml extension:**
- Add `workspace_access` (boolean) per tier
- Add `max_active_collections` (integer, -1 for unlimited) per tier
- Tier defaults: free_trial=1, free=0 (no access), standard=5, premium=unlimited, internal=unlimited

**Access gating:**
- Enforce tier-based workspace access check on Collection creation
- When `workspace_access: false`, show upgrade prompt
- When collection limit reached, show limit message with archive or upgrade options

**Platform settings:**
- Add `workspace_credit_cost_pulse` to platform_settings table (runtime configurable via Admin Portal)

### Key Dependencies

- Existing E2B sandbox infrastructure (code execution)
- Existing agent system (base agent class, orchestration)
- Existing credit infrastructure (credit_transactions, balance checks)
- Existing file upload system (user uploaded files)

### NOT in v0.8

- Investigation / Explain (v0.10)
- What-If Scenarios (v0.11)
- Reports and report compilation (v0.9)
- Chat-to-Collection bridge (v0.9)
- PDF export (v0.9)
- Admin workspace dashboard (v0.12)
- Monitoring module (deferred post-v0.12)

---

## v0.9 — Collections (Workspace Persistence)

**Goal:** Collections become full persistent workspaces with report generation, management features, and a bridge from Chat sessions.

This milestone adds the output layer to the workspace: structured reports compiled from Pulse signals, downloadable in markdown and PDF formats. It also introduces collection lifecycle management (archiving) and the ability to bring data cards from Chat into Collections.

### Backend Scope

**Data model — new tables:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Report` | id, collection_id, type, title, markdown_content, source_refs (JSON), generated_at | Compiled output from workspace activities. Types: pulse_summary, investigation, scenario, chat_compilation. |
| `ChatItem` | id, collection_id, chat_session_id, data_card_id, title, content (JSON), added_at | Bridge from Chat sessions to Collections. |

**API endpoints:**
- `POST /collections/{id}/reports` — Compile report from Pulse signals
- `GET /collections/{id}/reports` — List reports for a Collection
- `GET /collections/{id}/reports/{report_id}` — Get report content
- `GET /collections/{id}/reports/{report_id}/download` — Download as markdown or PDF
- `PATCH /collections/{id}/archive` — Archive a Collection
- `PATCH /collections/{id}/unarchive` — Unarchive a Collection
- `POST /collections/{id}/chat-items` — Add data card from Chat to Collection
- `GET /collections/{id}/chat-items` — List Chat items in a Collection

**Report compilation:**
- Generate structured markdown from Pulse signals (title, findings, visualizations, evidence)
- Report types: `pulse_summary` (auto-generated from all signals)
- Template-based compilation with minimal LLM usage

**Collection archiving:**
- Active/archived status management
- Archived Collections: read-only (view reports, download) but cannot run new operations
- Limit enforcement: count only active Collections against tier limit

### Frontend Scope

**Collection management:**
- Archive/unarchive action buttons on Collection detail and list pages. Status badge is already shown in the v0.8 mockup (Active = emerald, Archived = muted gray), but action buttons are not yet implemented — this is COLL-01 (known mockup gap, planned for v0.9).
- Collection limit usage display: "X of Y active collections" counter in the collection list or detail header. Not present in the v0.8 mockup — this is COLL-02 (known mockup gap, planned for v0.9).
- Upgrade prompt when collection limit is hit: "You've reached the limit for your plan. Archive a Collection or upgrade to [next tier]."

**Report viewer (/workspace/collections/[id]/reports/[reportId]):**
- Full-page layout (not embedded in the collection detail tabs). Sticky header: Back button (to collection detail), report title, type badge (Investigation Report = blue badge, What-If Scenario Report = violet badge), "Download as Markdown" button (functional), "Download as PDF" button (present but disabled, opacity-60 — planned backend feature).
- White paper area centered on a muted background (max-w-3xl, white bg, px-16 py-12, gray-900 text). Paper header shows: type badge, h1 title, generated date.
- Markdown rendered inline as HTML (custom converter — handles h1/h2/h3, bold, italic, hr, tables, ul, blockquotes, paragraphs).
- Investigation Reports only: "Related Signals — Same Root Cause" section (one gray card per related signal with "View Signal" link), then "Explore What-If Scenarios" CTA (violet card, "Start What-If →" button linking to /whatif for that signal).
- What-If Scenario Reports: no extra sections beyond the markdown content.

**Chat-to-Collection bridge:**
- "Add to Collection" button on each ResultCard in Chat (table, chart placeholder, or text result card).
- AddToCollectionModal: searches active collections only (archived collections are excluded from the picker). Shows collection name, signal count, file count. "Add" button per collection row. After adding: success state showing collection name for 1.5 seconds, then modal closes. Footer: "+ Create new collection" link.

**Credit display:**
- Running credit total shown in the collection detail header: "Credits used: N" with Zap icon pill.

### Admin Scope

**Admin collection visibility:**
- Admin can view all Collections across all users
- Filter by user, status, date range

**Platform settings — new credit costs:**
- `workspace_credit_cost_report_compile` (default: 1.0)
- `workspace_credit_cost_report_export` (default: 0.5)

### Key Dependencies

- v0.8 complete (Collection, File, Signal models and Pulse agent must exist)

### NOT in v0.9

- Investigation / Explain (v0.10)
- What-If Scenarios (v0.11)
- User document upload during investigation
- Admin workspace activity dashboard (v0.12)

---

## v0.10 — Explain (Guided Investigation)

**Goal:** Users can investigate a Signal through a guided Q&A flow (doctor-style interview) to identify root causes. Each investigation produces a root cause hypothesis that may explain multiple Signals.

This milestone adds the second stage of the Detect -> Explain -> What-If pipeline. The Investigation agent asks structured questions with discrete choices, progressively narrowing to a root cause over 3-5 exchanges.

### Backend Scope

**Data model — new tables:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Investigation` | id, signal_id, collection_id, status (in_progress/complete), qa_trail (JSON), started_at, completed_at | The Q&A exchange trail for a Signal investigation. |
| `RootCause` | id, investigation_id, hypothesis, confidence (high/medium/low), evidence (JSON), related_signal_ids (JSON) | Root cause identified from investigation. Can link to multiple Signals. |

**API endpoints:**
- `POST /signals/{id}/investigations` — Start investigation for a Signal
- `GET /signals/{id}/investigations` — List past investigations for a Signal
- `GET /investigations/{id}` — Get investigation detail with Q&A trail
- `POST /investigations/{id}/exchange` — Submit answer, get next question
- `GET /investigations/{id}/root-causes` — List root causes from investigation

**Investigation Agent (new agent):**
- Follows existing agent system patterns
- Takes Signal context (title, description, statistical evidence, visualization data)
- Generates hypotheses based on signal data and category
- Asks structured questions with discrete options plus free-text option
- Each exchange:
  1. Agent presents hypothesis + question with structured choices
  2. User selects an option or provides free-text answer
  3. Agent narrows focus, runs additional statistical analysis in E2B if needed
  4. Next question based on accumulated context
- 3-5 exchanges to reach root cause (agent determines when sufficient information gathered)
- Produces RootCause with hypothesis statement, confidence level, evidence, and related_signal_ids
- Each exchange saved to `investigation.qa_trail` JSON array

**Root cause linking:**
- A single RootCause can reference multiple Signals via `related_signal_ids`
- Example: "APAC pricing change" root cause explains both "revenue drop" and "customer churn spike" signals
- UI can show which Signals a root cause explains

**Credit integration:**
- `workspace_credit_cost_investigate_start` (default: 3.0) — first exchange
- `workspace_credit_cost_investigate_exchange` (default: 1.0) — each subsequent exchange
- Pre-check before start and before each exchange
- Show cost estimates: "Starting investigation (3 credits)" and "Next question (1 credit)"

### Frontend Scope

**Investigation page (/workspace/collections/[id]/signals/[signalId]/investigate):**
- Full-page dedicated route. Sticky header: "Back to Signals" button, "Guided Investigation" label, "3 credits" badge, signal title on the right.
- Signal context block: muted card showing signal title and truncated description.
- Q&A thread (InvestigationQAThread): renders each exchange as a question block. Spectra's question is shown with multiple-choice buttons (discrete options) plus a free-text textarea option per exchange. Answered choices are visually locked (cannot be re-selected after submission).
- Closing question appears after ≥3 exchanges are answered with no unanswered exchange remaining: "Is there anything else you'd like to discuss about this signal before I generate the report?" Two choice buttons: "No, that covers it — proceed with report" and "Yes, I'd like to discuss something".
- "Discuss something" path: free-text textarea input with send button (Cmd+Enter or click). Submitting appends the user's input as a discussion exchange and adds a new AI follow-up question to the thread. The closing question resets to hidden, allowing another round of discussion. Multiple discussion rounds are possible before proceeding.
- "Proceed with report" path: InvestigationCheckpoint component is shown with "Generate Report" button. Clicking triggers a 2-second loading state, then navigates to the report viewer.
- Note: there is no separate root cause card UI step. The investigation ends directly in report generation (no root cause card → What-If prompt sequence).

**Signal detail panel (updated for v0.10):**
- Investigation section (in SignalDetailPanel on Detection Results page):
  - "Investigate (3 credits)" button — always enabled, navigates to the investigation page (relaunches or starts a new investigation).
  - "What-If (5 credits)" button shown alongside: enabled only if at least one complete investigation session exists for this signal; otherwise disabled with "(requires investigation)" text.
  - List of past investigation reports below buttons: date, report title (truncated), Complete badge, links to report viewer.

**Investigation history:**
- Past investigation reports listed in the SignalDetailPanel Investigation section.
- Each entry shows: generated date, report title, Complete badge, "View Report" link.

### Admin Scope

**Platform settings — new credit costs:**
- `workspace_credit_cost_investigate_start` (default: 3.0)
- `workspace_credit_cost_investigate_exchange` (default: 1.0)

**Activity tracking:**
- Investigation activities logged to workspace_activity_log:
  - `investigation_start` — when user begins an investigation
  - `investigation_exchange` — each Q&A exchange

### Key Dependencies

- v0.9 complete (Collections with reports — investigation produces a report)
- v0.8 complete (Signals must exist to investigate)

### NOT in v0.10

- What-If Scenarios (v0.11)
- User document upload during investigation (noted as "later version" in requirements Section 6 Step 2)
- Admin workspace dashboard (v0.12)

---

## v0.11 — What-If Scenarios (Prescriptive Analytics)

**Goal:** Users can explore data-backed what-if scenarios from root causes, compare options with estimated impacts, refine via scoped chat, and decide on an approach. This completes the full Pulse -> Explain -> What-If pipeline and the Pulse Analysis reaches its complete vision.

### Backend Scope

**Data model — new table:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Scenario` | id, root_cause_id, objective, name, narrative, assumptions (JSON), projected_outcomes (JSON), confidence, confidence_rationale, data_backing (JSON), refinement_trail (JSON), is_selected (boolean) | AI-generated scenario with data-backed estimates. |

**API endpoints:**
- `POST /root-causes/{id}/scenarios` — Generate scenarios for a root cause (requires objective)
- `GET /root-causes/{id}/scenarios` — List scenarios for a root cause
- `GET /scenarios/{id}` — Get scenario detail
- `POST /scenarios/{id}/refine` — Refine scenario via scoped chat exchange
- `POST /root-causes/{id}/scenarios/add` — Generate additional scenario
- `PATCH /scenarios/{id}/select` — Mark scenario as selected
- `GET /root-causes/{id}/scenarios/compare` — Get comparison view of all scenarios

**Strategy Agent (new agent):**
- Takes objective + root cause context + original data
- Phase 1 — Objective handling:
  - Receives user's stated objective (selected from choices or free-text)
  - Anchors all subsequent analysis to this objective
- Phase 2 — Scenario generation:
  - Runs targeted analysis in E2B: groupbys, historical trends, segment performance, period comparisons
  - Identifies what the data can actually support as scenarios
  - Generates 2-3 named scenarios simultaneously
  - Each scenario contains: name, narrative, estimated impact with ranges, key assumptions, confidence level + rationale, data backing (references to actual analysis results)
- Phase 3 — Refinement:
  - Scoped chat (stays on-topic with the scenarios, not freeform)
  - Each refinement exchange: user question -> agent runs additional E2B analysis -> updated response
  - Refinement exchanges saved to scenario's `refinement_trail`
- Phase 4 — Additional scenarios:
  - User can request new scenarios alongside existing set
  - Each new scenario is a full E2B analysis cycle

**Credit integration:**
- `workspace_credit_cost_whatif_generate` (default: 5.0) — initial 2-3 scenario generation
- `workspace_credit_cost_whatif_refine` (default: 1.0) — each refinement exchange
- `workspace_credit_cost_whatif_add_scenario` (default: 2.0) — each additional scenario
- Pre-check before each action, show cost estimates

### Frontend Scope

**What-If Objective page (/workspace/collections/[id]/signals/[signalId]/whatif):**
- Accessible from two entry points: (a) SignalDetailPanel "What-If (5 credits)" button (enabled only after at least one complete investigation exists for the signal), and (b) "Start What-If →" CTA button in an Investigation Report viewer.
- Sticky header: "Back to Signals" link, "What-If Scenarios" label, "5 credits" badge, signal title.
- Root cause context card (muted background): investigation report title, confidence badge (e.g., "High confidence"), brief root cause description text.
- Objective section: "Define your objective" heading plus subtext. Action search bar with Search icon, text input, and "Generate Scenarios →" button (disabled until text is non-empty, costs 5 credits). On input focus: suggestions dropdown shows 4 pre-computed objective options. Suggestion selection uses onMouseDown + preventDefault to avoid blur/click race condition.
- After "Generate Scenarios" is clicked: inline loading state replaces the main content (the sticky header remains visible). 4 animated steps with step icons and spinner/checkmark states: Analyzing root cause, Generating scenarios, Scoring confidence, Finalizing scenarios. Progress bar below steps. Estimated time shown. Navigates to the What-If Session page after ~10 seconds.

**What-If Session page (/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]):**
- Three-panel layout. Objective shown in page header (signal title + objective text on right side).
- Scenario list panel (280px, left): vertical list of scenario buttons. Each entry shows scenario name, confidence badge (High = emerald, Medium = amber, Low = muted), estimated impact. The selected scenario has a ring highlight. Below the last scenario: a separator and "Generate What-If Report" primary button.
- Scenario detail panel (fills remaining width, center): header with selected scenario name, confidence badge, and "Refine" toggle button. Scrollable content with 5 cards: Narrative & Recommendations, Estimated Impact (highlighted primary-color box with projected outcome), Assumptions (checklist items), Confidence (badge + rationale text), Data Backing.
- Refine panel (320px, right overlay): slides in from the right edge via CSS translate when the "Refine" toggle button is clicked, overlaying the detail panel. Header: "Refine Scenario" label + X close button. Contains WhatIfRefinementChat scoped to the currently selected scenario. Chat history resets when switching scenarios (component remount via key={selectedScenarioId}).
- "Generate What-If Report" button in the scenario list panel routes to the report viewer showing the What-If Scenario Report.
- Deferred: WHAT-05 — "Add Scenario" button (user requests additional scenario generation beyond the initial set) is not in the mockup. Planned for v0.11 implementation.
- Deferred: WHAT-06 — Side-by-side scenario comparison view is not in the mockup. The "Compare & Decide" phase from the original requirements is replaced by the scenario list + "Generate What-If Report" action. Planned for v0.11 implementation.

### Admin Scope

**Platform settings — new credit costs:**
- `workspace_credit_cost_whatif_generate` (default: 5.0)
- `workspace_credit_cost_whatif_refine` (default: 1.0)
- `workspace_credit_cost_whatif_add_scenario` (default: 2.0)

**Activity tracking:**
- What-If activities logged to workspace_activity_log:
  - `whatif_generate` — initial scenario generation
  - `whatif_refine` — each refinement exchange
  - `whatif_add_scenario` — additional scenario generation

### Key Dependencies

- v0.10 complete (Investigation + RootCause models must exist)
- v0.9 complete (Reports — scenario comparison generates a report)
- v0.8 complete (Signals, Collections, Pulse)

### NOT in v0.11

- Admin workspace dashboard (v0.12)
- Monitoring module (deferred post-v0.12)
- Persistent AI Memory (future exploration post-v0.12)

---

## v0.12 — Admin Workspace Management

**Goal:** Full admin visibility and control over Pulse Analysis usage, including activity dashboards, per-user tracking, credit cost management, and operational alerts.

This milestone builds the admin-facing monitoring and management layer for the workspace. It requires all workspace features (Pulse, Collections, Explain, What-If) to exist for meaningful analytics.

### Backend Scope

**Data model — new table:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `workspace_activity_log` | id, user_id, collection_id, activity_type (enum), credit_cost, duration_ms, metadata (JSON), created_at | Comprehensive activity tracking for all workspace operations. |

Activity type enum values: `pulse_run`, `investigation_start`, `investigation_exchange`, `whatif_generate`, `whatif_refine`, `whatif_add_scenario`, `report_compile`, `report_export`

**API endpoints:**
- `GET /api/admin/workspace/dashboard` — Workspace activity dashboard metrics (aggregated)
- `GET /api/admin/workspace/users/{user_id}/activity` — Per-user workspace activity
- `GET /api/admin/workspace/activity-log` — Activity log with filtering (user, collection, type, date range)
- `GET /api/admin/workspace/funnel` — Funnel analytics: Pulse -> Explain -> What-If adoption
- `GET /api/admin/workspace/alerts` — Active alerts (high-cost collections, failed runs)
- `PATCH /api/admin/workspace/alerts/thresholds` — Configure alert thresholds

**Dashboard metrics computation:**
- Total Collections over time (daily/weekly/monthly aggregation)
- Active vs. Archived snapshot counts
- Activity counts per day by type (Pulse runs, Investigations, What-If generations, Reports)
- Funnel: stage adoption drop-off (% of Collections that proceed Pulse -> Explain -> What-If)
- Workspace credits consumed over time, broken down by activity type
- Average credits per Collection lifecycle

**Alerts:**
- High-cost Collection: flag Collections exceeding configurable credit threshold
- Failed Pulse runs: track runs that failed or returned zero signals
- Workspace adoption rate: % of eligible users (by tier) who have created at least one Collection

### Frontend Scope (Admin Portal)

**Workspace Activity Dashboard (new Admin page) — Section 7.3a:**

| Widget | Visualization | Data |
|--------|---------------|------|
| Total Collections created | Line chart with trend | Daily/weekly/monthly aggregation |
| Active vs. Archived Collections | Donut chart | Current snapshot |
| Pulse runs per day | Bar chart | Daily count |
| Investigations started per day | Bar chart | Daily count |
| What-If scenarios generated per day | Bar chart | Daily count |
| Reports generated per day | Bar chart | Daily count |
| Funnel: Pulse -> Explain -> What-If | Funnel chart | Stage adoption drop-off |
| Workspace credits consumed | Line chart by activity type | Credits over time |
| Avg. credits per Collection | KPI card | Calculated metric |

**Per-User Workspace Tab (extends existing user detail page) — Section 7.3b:**
- List of user's Collections: name, status, created date, signal count, report count, total credits used
- Credit consumption breakdown: Pulse vs. Explain vs. What-If vs. Reports (bar or pie chart)
- Activity timeline: when they last used the Workspace, frequency of use
- Collection limit usage display: "3 of 5 active collections"

**Workspace Credit Costs settings section:**
- Editable form for all workspace credit cost settings:
  - Pulse: Run Detection
  - Explain: Start Investigation
  - Explain: Per Q&A Exchange
  - What-If: Generate Scenarios
  - What-If: Refine Scenario
  - What-If: Add Scenario
  - Report: Compile & Generate
  - Report: PDF Export
- Save button with confirmation

**Alerts section:**
- Configurable thresholds (high-cost Collection credit limit, etc.)
- Alert list: active alerts with collection/user context
- Dismiss/acknowledge actions

### Key Dependencies

- v0.11 complete (all workspace features must exist for meaningful monitoring)
- Existing Admin Portal infrastructure (user detail page, settings page)

---

## Cross-Cutting Concerns

These patterns apply across all milestones and should be implemented consistently from v0.8 onward.

### Frontend Migration from Mockup

The `pulse-mockup/` app contains complete, working UI for the entire v0.8–v0.12 scope. The implementation strategy for each milestone is **migrate, not rebuild**:

1. **Copy components** — move relevant components from `pulse-mockup/components/` into the main `frontend/` app. Components are already built with the correct tech stack (Next.js, shadcn/ui, Recharts, Tailwind).
2. **Replace mock data** — each component uses local mock data arrays and constants. Replace these with API calls to the new backend endpoints defined in each milestone's Backend Scope.
3. **Wire up routing** — the mockup uses Next.js App Router. Adapt routes to match the main frontend's routing conventions.
4. **Remove loading stubs** — the mockup simulates delays with `setTimeout`. Replace with real async states driven by API response status.
5. **Connect credit checks** — the mockup shows credit costs as static labels. Wire to live credit balance from the user session and enforce pre-checks per the Credit Pre-Check Pattern below.

The mockup is the UI contract. Any deviation from its component structure or interaction patterns requires explicit product sign-off.

**Design refresh:** Where the existing Spectra frontend (Chat, Files, Settings, Admin) diverges from the `pulse-mockup/` design — colors, component styles, typography, layout patterns, spacing — treat the mockup as the new design standard and align the existing screens accordingly. This is an intentional opportunity to refresh the overall Spectra UI to match the more polished workspace aesthetic. Specific pages and components that need alignment will be identified and clarified during each milestone's development. When in doubt, the `pulse-mockup/` visual decisions take precedence over the existing frontend.

### Credit Pre-Check Pattern

Every workspace activity that costs credits follows this flow:

1. **Check:** Verify user has sufficient credits for the activity
2. **Estimate:** Show cost estimate to user before running ("This will use ~5 credits. You have 23 remaining.")
3. **Deduct:** Deduct credits before execution begins
4. **Execute:** Run the activity (Pulse, Investigation exchange, etc.)
5. **Refund on failure:** If execution fails, refund the deducted credits
6. **Log:** Record activity to workspace_activity_log with credit_cost and duration

This follows the existing credit transaction pattern used in Chat sessions.

### E2B Sandbox Reuse

All statistical analysis runs through the existing E2B sandbox infrastructure:
- Pulse Agent runs data profiling and statistical methods in E2B
- Investigation Agent runs follow-up analyses in E2B during Q&A exchanges
- Strategy Agent runs targeted analysis in E2B for scenario generation and refinement
- No new sandbox infrastructure needed — same execution environment, same security model

### Agent System Extension

New agents follow existing agent system patterns:

| Agent | Milestone | Role |
|-------|-----------|------|
| **Pulse Agent** | v0.8 | Data profiling, statistical analysis, Signal generation |
| **Investigation Agent** | v0.10 | Hypothesis generation, structured Q&A, root cause identification |
| **Strategy Agent** | v0.11 | Objective-based scenario generation, data-backed estimates, refinement |

All agents:
- Extend the base agent class
- Use the existing orchestration system
- Execute code in E2B sandbox
- Return structured outputs (Signals, Q&A exchanges, Scenarios)

### Auto-Save

Collection state is saved continuously throughout the user's workflow:
- No explicit "save" button needed
- All progress (Signals, investigations, scenarios) persists automatically
- User can leave and return to a Collection at any point
- Archived Collections are read-only but fully browsable

### Error Handling

Graceful degradation if any workspace operation fails mid-execution:
- Pulse fails: show error message, refund credits, allow retry
- Investigation exchange fails: preserve Q&A trail up to failure point, allow retry from last exchange
- What-If generation fails: preserve any partially generated scenarios, allow regeneration
- Report compilation fails: show error, allow retry
- Network errors: auto-save ensures no work is lost

---

## Deferred / Out of Scope

These items are explicitly excluded from milestones v0.8 through v0.12:

| Item | Status | Reference |
|------|--------|-----------|
| **Monitoring module** (recurring automated analysis) | Post-v0.12 backlog | Decision #6 |
| **Persistent AI Memory** (cross-session context) | Future exploration post-v0.12 | Decision #8 |
| **PDF generation** (elaborate templating) | Skip unless explicitly requested | Decision #5. Note: v0.9 includes basic PDF download option but no elaborate generation/templating. |
| **User document upload during investigation** | Later version | Section 6 Step 2: "this is for later version" |
| **Full predictive ML model** | Appendix concept | Moved to Appendix in requirements, not in milestone scope |

---

## Credit Cost Summary

All workspace credit costs, aggregated for reference. All values are defaults stored as `platform_settings` entries, runtime-configurable via Admin Portal.

| Setting Key | Activity | Default Cost | Milestone |
|-------------|----------|:---:|:---:|
| `workspace_credit_cost_pulse` | Pulse: Run Detection | 5.0 | v0.8 |
| `workspace_credit_cost_report_compile` | Report: Compile & Generate | 1.0 | v0.9 |
| `workspace_credit_cost_report_export` | Report: PDF Export | 0.5 | v0.9 |
| `workspace_credit_cost_investigate_start` | Explain: Start Investigation | 3.0 | v0.10 |
| `workspace_credit_cost_investigate_exchange` | Explain: Per Q&A Exchange | 1.0 | v0.10 |
| `workspace_credit_cost_whatif_generate` | What-If: Generate Scenarios | 5.0 | v0.11 |
| `workspace_credit_cost_whatif_refine` | What-If: Refine Scenario | 1.0 | v0.11 |
| `workspace_credit_cost_whatif_add_scenario` | What-If: Add Scenario | 2.0 | v0.11 |

---

## Tier Access Summary

Collection limits and workspace access by tier. Configured in `user_classes.yaml`.

| Tier | Workspace Access | Max Active Collections | Rationale |
|------|:---:|:---:|---|
| `free_trial` | Yes | 1 | Let users experience the "wow" moment that converts |
| `free` | No | 0 | Chat-only. Workspace is the upgrade incentive |
| `standard` | Yes | 5 | Enough for regular use |
| `premium` | Yes | Unlimited | Power users, no friction |
| `internal` | Yes | Unlimited | Internal/admin testing |
