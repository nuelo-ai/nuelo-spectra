# Spectra Pulse — Milestone Implementation Plan

> Source requirements: [Spectra-Pulse-Requirement.md](./Spectra-Pulse-Requirement.md)

---

## Overview

This document breaks down the full Spectra Pulse (Analysis Workspace) implementation into versioned milestones with clear scope, deliverables, and frontend/backend/admin breakdown per milestone.

**Confirmed milestone sequence** (Decisions Log #4):

```
v0.8 (Pulse) -> v0.9 (Collections) -> v0.10 (Explain) -> v1.0 (What-If Scenarios) -> v0.11 (Admin Workspace Management)
```

**Deferred items:**
- Monitoring module (recurring automated analysis) — deferred to post-v1.0 backlog (Decision #6)
- Persistent AI Memory — future exploration post-v0.11 (Decision #8)
- Full predictive ML model — moved to Appendix in requirements, not in milestone scope

---

## Milestone Summary

| Version | Name | Scope | Key Deliverable | Complexity |
|---------|------|-------|-----------------|:---:|
| **v0.8** | Spectra Pulse (Detection) | Create Collections, attach files, run Pulse, view Signals | Signal cards with statistical findings | XL |
| **v0.9** | Collections (Workspace Persistence) | Reports, archiving, Chat-to-Collection bridge | Persistent workspace with downloadable reports | L |
| **v0.10** | Explain (Guided Investigation) | Q&A investigation flow, root cause identification | Doctor-style interview leading to root cause hypothesis | L |
| **v1.0** | What-If Scenarios (Prescriptive) | AI-generated scenarios, refinement, comparison | Data-backed scenario cards with side-by-side comparison | XL |
| **v0.11** | Admin Workspace Management | Activity dashboard, per-user tracking, alerts | Full admin visibility over workspace usage | M |

---

## v0.8 — Spectra Pulse (Detection)

**Goal:** Users can create a Collection, attach data files, run Pulse detection, and view Signals as cards with statistical findings and visualizations.

This is the foundation milestone. It introduces the Analysis Workspace as a new module separate from Chat, establishes the core data model (Collection, File, Signal), and delivers the first stage of the Detect -> Explain -> What-If pipeline.

### Backend Scope

**Data model — new tables:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Collection` | id, name, description, status (active/archived), user_id, created_at, updated_at | The workspace container. See Section 5 ER diagram. |
| `File` | id, collection_id, original_filename, file_type, column_profile (JSON), row_count | Data sources attached to a Collection. |
| `Signal` | id, collection_id, title, description, severity, category, visualization (JSON), statistical_evidence (JSON) | Individual findings from Pulse analysis. |

**API endpoints:**
- `POST /api/v1/collections` — Create a new Collection
- `GET /api/v1/collections` — List user's Collections (with pagination, status filter)
- `GET /api/v1/collections/{id}` — Get Collection detail with Signals
- `PATCH /api/v1/collections/{id}` — Update Collection name/description
- `DELETE /api/v1/collections/{id}` — Delete Collection (soft delete or archive)
- `POST /api/v1/collections/{id}/files` — Attach file(s) to Collection
- `DELETE /api/v1/collections/{id}/files/{file_id}` — Remove file from Collection
- `POST /api/v1/collections/{id}/pulse` — Trigger Pulse detection run
- `GET /api/v1/collections/{id}/signals` — List Signals for a Collection

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
- New "Analysis Workspace" entry point in main navigation (separate from Chat)
- Route: `/workspace` (list) and `/workspace/{collection_id}` (detail)

**Collection list page:**
- View existing Collections with name, status, created date, signal count
- "Create New Collection" action
- Status indicators (active/archived)

**Collection detail page:**
- File selection area: pick from uploaded files or upload new
- "Run Detection" button with credit cost display ("This will use ~5 credits")
- Loading state during Pulse execution (15-30 seconds expected)
- Credit balance indicator

**Signal cards UI (after Pulse completes):**
- Left panel: scrollable signal list with title, severity badge, category tag
- Main panel: selected signal detail view
  - Title (key finding headline)
  - Description (detailed explanation)
  - Severity badge (color-coded: opportunity=green, warning=amber, critical=red, info=blue)
  - Category tag (anomaly, trend, concentration, quality)
  - Visualization (chart rendered from Signal's visualization config)
  - Statistical evidence summary

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
- What-If Scenarios (v1.0)
- Reports and report compilation (v0.9)
- Chat-to-Collection bridge (v0.9)
- PDF export (v0.9)
- Admin workspace dashboard (v0.11)
- Monitoring module (deferred post-v1.0)

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
- `POST /api/v1/collections/{id}/reports` — Compile report from Pulse signals
- `GET /api/v1/collections/{id}/reports` — List reports for a Collection
- `GET /api/v1/collections/{id}/reports/{report_id}` — Get report content
- `GET /api/v1/collections/{id}/reports/{report_id}/download` — Download as markdown or PDF
- `PATCH /api/v1/collections/{id}/archive` — Archive a Collection
- `PATCH /api/v1/collections/{id}/unarchive` — Unarchive a Collection
- `POST /api/v1/collections/{id}/chat-items` — Add data card from Chat to Collection
- `GET /api/v1/collections/{id}/chat-items` — List Chat items in a Collection

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
- Archive/unarchive actions on Collection list and detail pages
- Status indicators (active badge vs. archived badge)
- Collection limit usage display: "3 of 5 active collections"
- Upgrade prompt when limit hit: "You've reached the limit for your plan. Archive a Collection or upgrade to [next tier]."

**Report viewer:**
- Rendered markdown display within Collection detail page
- Report list with type, title, generated date
- In-page reading view with proper typography

**Download options:**
- "Download as Markdown" button
- "Download as PDF" button (basic PDF rendering from markdown — no elaborate templating per Decision #5)

**Chat-to-Collection bridge:**
- "Add to Collection" action on data cards in Chat sessions
- Collection picker modal: select which Collection to add the card to
- Chat items appear in Collection alongside Signals

**Credit display:**
- Running credit total in Collection header: "Credits used: 14"
- Credit cost indicators on report compilation and export actions

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
- What-If Scenarios (v1.0)
- User document upload during investigation
- Admin workspace activity dashboard (v0.11)

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
- `POST /api/v1/signals/{id}/investigations` — Start investigation for a Signal
- `GET /api/v1/signals/{id}/investigations` — List past investigations for a Signal
- `GET /api/v1/investigations/{id}` — Get investigation detail with Q&A trail
- `POST /api/v1/investigations/{id}/exchange` — Submit answer, get next question
- `GET /api/v1/investigations/{id}/root-causes` — List root causes from investigation

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

**Signal card enhancement:**
- "Investigate" button on each Signal card (available after Pulse completion)
- Investigation status indicator on Signal card if investigation exists

**Investigation UI:**
- Doctor-style interview flow (not a chat — structured Q&A):
  - Spectra presents: hypothesis text + structured choices (radio/checkboxes) + free-text option
  - User selects/types answer and submits
  - Visual narrowing: each exchange visually narrows the scope (progress indicator, 3-5 steps)
  - Root cause summary card when investigation completes
- Root cause display: hypothesis statement, confidence badge, supporting evidence
- "Done" state: investigation complete with root cause identified

**Investigation history:**
- View past investigations for a Signal
- Each investigation shows: date, status, root cause (if complete), exchange count
- Can review full Q&A trail of past investigations

**Root cause visualization:**
- Root cause card shows which Signals it explains (linked signal titles)
- From a Signal card, show if a root cause has been identified linking it to other Signals

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

- What-If Scenarios (v1.0)
- User document upload during investigation (noted as "later version" in requirements Section 6 Step 2)
- Admin workspace dashboard (v0.11)

---

## v1.0 — What-If Scenarios (Prescriptive Analytics)

**Goal:** Users can explore data-backed what-if scenarios from root causes, compare options with estimated impacts, refine via scoped chat, and decide on an approach. This completes the full Pulse -> Explain -> What-If pipeline.

This is the "1.0" milestone — the Analysis Workspace reaches its complete vision. Users go from raw data to actionable recommendations in a single guided workflow.

### Backend Scope

**Data model — new table:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `Scenario` | id, root_cause_id, objective, name, narrative, assumptions (JSON), projected_outcomes (JSON), confidence, confidence_rationale, data_backing (JSON), refinement_trail (JSON), is_selected (boolean) | AI-generated scenario with data-backed estimates. |

**API endpoints:**
- `POST /api/v1/root-causes/{id}/scenarios` — Generate scenarios for a root cause (requires objective)
- `GET /api/v1/root-causes/{id}/scenarios` — List scenarios for a root cause
- `GET /api/v1/scenarios/{id}` — Get scenario detail
- `POST /api/v1/scenarios/{id}/refine` — Refine scenario via scoped chat exchange
- `POST /api/v1/root-causes/{id}/scenarios/add` — Generate additional scenario
- `PATCH /api/v1/scenarios/{id}/select` — Mark scenario as selected
- `GET /api/v1/root-causes/{id}/scenarios/compare` — Get comparison view of all scenarios

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

**Phase 1 UI — Set Objective:**
- Triggered from root cause card: "Explore What-If" button
- Spectra presents root cause context and asks for objective
- Presented as selection with options + free-text:
  - Context: "Revenue declined 18% due to APAC Enterprise pricing pressure."
  - Prompt: "What would you like to explore?"
  - Options: 3-4 AI-suggested objectives based on root cause
  - Free-text: "Type your own objective"
- Credit cost display: "Generating scenarios will use ~5 credits"

**Phase 2 UI — Scenario generation:**
- Loading state while AI generates scenarios (15-30 seconds)
- Progress indicator showing generation in progress
- Scenario cards appear when ready:
  - Scenario name (e.g., "Shift Focus to Domestic SMB")
  - Narrative explanation (2-3 paragraphs)
  - Estimated impact with range (e.g., "$420K-$580K over Q1")
  - Key assumptions listed
  - Confidence badge (high/medium/low) with rationale
  - Data backing summary

**Phase 3 UI — Explore and Refine:**
- Per-scenario refinement chat panel
- Scoped chat input: user asks follow-up questions about a specific scenario
- AI responses include updated analysis and numbers (no hallucinated figures)
- "Add Scenario" button to request additional scenarios (2 credits)
- Refinement history visible in scenario detail

**Phase 4 UI — Compare and Decide:**
- Side-by-side comparison cards for all scenarios:
  - Scenario name + one-line summary
  - Estimated impact range
  - Confidence level
  - Time to impact
- "Select" action on preferred scenario
- Selected scenario comparison becomes a report section
- Report auto-generated: objective stated, scenarios evaluated, selected approach with rationale

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

### NOT in v1.0

- Admin workspace dashboard (v0.11)
- Monitoring module (deferred post-v1.0)
- Persistent AI Memory (future exploration post-v0.11)

---

## v0.11 — Admin Workspace Management

**Goal:** Full admin visibility and control over Analysis Workspace usage, including activity dashboards, per-user tracking, credit cost management, and operational alerts.

This milestone builds the admin-facing monitoring and management layer for the workspace. It requires all workspace features (Pulse, Collections, Explain, What-If) to exist for meaningful analytics.

### Backend Scope

**Data model — new table:**

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `workspace_activity_log` | id, user_id, collection_id, activity_type (enum), credit_cost, duration_ms, metadata (JSON), created_at | Comprehensive activity tracking for all workspace operations. |

Activity type enum values: `pulse_run`, `investigation_start`, `investigation_exchange`, `whatif_generate`, `whatif_refine`, `whatif_add_scenario`, `report_compile`, `report_export`

**API endpoints:**
- `GET /api/v1/admin/workspace/dashboard` — Workspace activity dashboard metrics (aggregated)
- `GET /api/v1/admin/workspace/users/{user_id}/activity` — Per-user workspace activity
- `GET /api/v1/admin/workspace/activity-log` — Activity log with filtering (user, collection, type, date range)
- `GET /api/v1/admin/workspace/funnel` — Funnel analytics: Pulse -> Explain -> What-If adoption
- `GET /api/v1/admin/workspace/alerts` — Active alerts (high-cost collections, failed runs)
- `PATCH /api/v1/admin/workspace/alerts/thresholds` — Configure alert thresholds

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

- v1.0 complete (all workspace features must exist for meaningful monitoring)
- Existing Admin Portal infrastructure (user detail page, settings page)

---

## Cross-Cutting Concerns

These patterns apply across all milestones and should be implemented consistently from v0.8 onward.

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
| **Strategy Agent** | v1.0 | Objective-based scenario generation, data-backed estimates, refinement |

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

These items are explicitly excluded from milestones v0.8 through v0.11:

| Item | Status | Reference |
|------|--------|-----------|
| **Monitoring module** (recurring automated analysis) | Post-v1.0 backlog | Decision #6 |
| **Persistent AI Memory** (cross-session context) | Future exploration post-v0.11 | Decision #8 |
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
| `workspace_credit_cost_whatif_generate` | What-If: Generate Scenarios | 5.0 | v1.0 |
| `workspace_credit_cost_whatif_refine` | What-If: Refine Scenario | 1.0 | v1.0 |
| `workspace_credit_cost_whatif_add_scenario` | What-If: Add Scenario | 2.0 | v1.0 |

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
