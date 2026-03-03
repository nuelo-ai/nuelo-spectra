---
phase: quick-3
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements/Pulse-req-milestone-plan.md
autonomous: true
requirements: [QUICK-3]
must_haves:
  truths:
    - "Document covers all milestones v0.8 through v0.11 plus v1.0 as defined in Decisions Log"
    - "Each milestone has clear scope, deliverables, and frontend/backend breakdown"
    - "Admin portal planning is included with tier gating, credit costs, and monitoring"
    - "Document references the confirmed sequence: v0.8 Pulse, v0.9 Collections, v0.10 Explain, v1.0 What-If, v0.11 Admin Workspace"
  artifacts:
    - path: "requirements/Pulse-req-milestone-plan.md"
      provides: "Phased milestone implementation plan for Spectra Pulse module"
      min_lines: 200
  key_links: []
---

<objective>
Create a phased milestone implementation plan document for the Spectra Pulse module (Analysis Workspace).

Purpose: Provide a structured roadmap breaking down the full Spectra Pulse implementation into versioned milestones (v0.8 through v0.11 + v1.0), with clear scope, deliverables, and frontend/backend/admin breakdown per milestone.

Output: `requirements/Pulse-req-milestone-plan.md`
</objective>

<execution_context>
@/Users/marwazisiagian/.claude/get-shit-done/workflows/execute-plan.md
@/Users/marwazisiagian/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@requirements/Spectra-Pulse-Requirement.md
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Pulse-req-milestone-plan.md with full phased implementation plan</name>
  <files>requirements/Pulse-req-milestone-plan.md</files>
  <action>
Create `requirements/Pulse-req-milestone-plan.md` — a comprehensive milestone implementation plan document for the Spectra Pulse / Analysis Workspace module. This is a planning document (not code), written in Markdown.

**Document structure:**

1. **Header and Overview**
   - Title: "Spectra Pulse — Milestone Implementation Plan"
   - Brief intro: link back to Spectra-Pulse-Requirement.md as the source requirements
   - Confirmed milestone sequence from Decisions Log: v0.8 (Pulse) -> v0.9 (Collections) -> v0.10 (Explain) -> v1.0 (What-If Scenarios) -> v0.11 (Admin Workspace Management)
   - Note that Monitoring module is deferred to post-v1.0 backlog (Decision #6)
   - Note that Persistent AI Memory is future exploration post-v0.11 (Decision #8)

2. **Milestone Summary Table**
   - One table with all milestones: version, name, one-line scope, key deliverable, estimated complexity (S/M/L/XL)

3. **v0.8 — Spectra Pulse (Detection)**
   - **Goal:** Users can create a Collection, attach data files, run Pulse detection, and view Signals
   - **Backend scope:**
     - Data model: Collection, File, Signal tables (from Section 5 ER diagram)
     - API endpoints: CRUD for Collections, file attachment, trigger Pulse run
     - Pulse Agent: new agent that profiles data, runs statistical analyses in E2B, generates Signals
     - Statistical methods: anomaly detection, trend analysis, concentration analysis, data quality checks
     - Credit integration: deduct workspace_credit_cost_pulse (5.0 default) per Pulse run with pre-check
   - **Frontend scope:**
     - New "Analysis Workspace" entry point in navigation (separate from Chat)
     - Collection list page: view existing Collections, create new
     - Collection detail page: file selection, "Run Detection" button
     - Signal cards UI: left panel signal list, main panel signal detail with title, description, severity badge, visualization
     - Loading state during Pulse execution (15-30 seconds)
     - Credit cost display before running ("This will use ~5 credits")
   - **Admin scope (minimal for v0.8):**
     - Add `workspace_access` and `max_active_collections` to `user_classes.yaml`
     - Enforce tier-based access gating (free tier blocked, free_trial = 1 collection, etc.)
     - Add `workspace_credit_cost_pulse` to platform_settings
   - **Data model changes:** Collection, File, Signal tables per Section 5
   - **Key dependencies:** Existing E2B sandbox, existing agent system, existing credit infrastructure
   - **NOT in v0.8:** Investigation (Explain), What-If, Reports, Chat-to-Collection bridge, PDF export

4. **v0.9 — Collections (Workspace Persistence)**
   - **Goal:** Collections become full persistent workspaces with report generation and management
   - **Backend scope:**
     - Report model and table (from Section 5)
     - Report compilation endpoint: generate markdown from Pulse signals
     - Collection archiving: active/archived status, limit enforcement
     - ChatItem model: bridge from Chat sessions to Collections (data card import)
   - **Frontend scope:**
     - Collection management: archive/unarchive, status indicators
     - Report viewer: rendered markdown display within Collection
     - Markdown/PDF download options
     - Chat-to-Collection: "Add to Collection" action on data cards in Chat
     - Collection limit UI: show usage ("3 of 5 active"), upgrade prompt when limit hit
     - Running credit total in Collection header ("Credits used: 14")
   - **Admin scope:**
     - Admin can view all Collections across users
     - `workspace_credit_cost_report_compile` and `workspace_credit_cost_report_export` in platform_settings
   - **Key dependencies:** v0.8 (Collection + Signal models must exist)
   - **NOT in v0.9:** Investigation, What-If, user-uploaded documents for investigation

5. **v0.10 — Explain (Guided Investigation)**
   - **Goal:** Users can investigate a Signal through guided Q&A to identify root causes
   - **Backend scope:**
     - Investigation and RootCause models/tables (from Section 5)
     - Investigation Agent: generates hypotheses, asks structured questions, narrows to root cause
     - Q&A trail storage: each exchange saved to investigation.qa_trail JSON
     - Root cause can link to multiple Signals (many-to-many via related_signal_ids)
     - Credit integration: investigate_start (3.0) + per exchange (1.0)
   - **Frontend scope:**
     - "Investigate" button on Signal cards
     - Investigation UI: doctor-style interview flow
       - Spectra presents hypothesis + structured choices (discrete options + free-text)
       - 3-5 exchange progression with visual narrowing
       - Root cause summary card when investigation completes
     - Investigation history: view past investigations for a Signal
     - Root cause visualization: which Signals a root cause explains
   - **Admin scope:**
     - `workspace_credit_cost_investigate_start` and `workspace_credit_cost_investigate_exchange` in platform_settings
     - Investigation activity tracking in workspace_activity_log
   - **Key dependencies:** v0.9 (Collections with reports), v0.8 (Signals)
   - **NOT in v0.10:** What-If scenarios, user document upload for investigation context

6. **v1.0 — What-If Scenarios (Prescriptive Analytics)**
   - **Goal:** Users can explore data-backed what-if scenarios from root causes, compare options, and decide
   - **Backend scope:**
     - Scenario model/table (from Section 5)
     - Strategy Agent: takes objective + root cause + data, runs targeted analysis in E2B, generates 2-3 narrative scenarios
     - Scenario generation: name, narrative, estimated impact with ranges, assumptions, confidence level + rationale, data backing
     - Scoped refinement chat: on-topic follow-ups that run additional E2B analysis
     - Additional scenario generation on request
     - Refinement trail storage per scenario
     - Credit integration: whatif_generate (5.0), whatif_refine (1.0), whatif_add_scenario (2.0)
   - **Frontend scope:**
     - Phase 1 UI: Objective selection (choices + free-text) triggered from root cause
     - Phase 2 UI: Scenario generation with loading state, scenario cards display
     - Phase 3 UI: Scoped refinement chat per scenario, "Add Scenario" button
     - Phase 4 UI: Side-by-side comparison cards (name, impact range, confidence, time to impact), scenario selection
     - Selected scenario becomes report section
   - **Admin scope:**
     - All What-If credit cost settings in platform_settings
     - What-If activity tracking in workspace_activity_log
   - **Key dependencies:** v0.10 (Investigation + Root Cause), v0.9 (Reports)
   - **This is the "1.0" milestone** — completes the full Pulse -> Explain -> What-If pipeline

7. **v0.11 — Admin Workspace Management**
   - **Goal:** Full admin visibility and control over Analysis Workspace usage
   - **Backend scope:**
     - workspace_activity_log table (Section 7.3c): user_id, collection_id, activity_type enum, credit_cost, duration_ms, metadata JSON
     - Admin API endpoints: workspace dashboard metrics, per-user workspace activity, activity log with filtering
     - Funnel analytics: Pulse -> Explain -> What-If stage adoption calculation
     - Alerts: high-cost Collection threshold, failed Pulse runs tracking
   - **Frontend scope (Admin Portal):**
     - Workspace Activity Dashboard page (Section 7.3a):
       - Total Collections over time (line chart)
       - Active vs. Archived (donut chart)
       - Pulse runs / Investigations / What-If / Reports per day (bar charts)
       - Funnel: stage adoption drop-off (funnel chart)
       - Workspace credits consumed over time by activity type (line chart)
       - Avg credits per Collection (KPI card)
     - Per-User Workspace tab (Section 7.3b):
       - User's Collections list with stats
       - Credit consumption breakdown by activity type
       - Activity timeline and frequency
       - Collection limit usage display
     - Workspace Credit Costs settings section: editable costs for all activity types
     - Alerts section: configurable thresholds, alert list
   - **Key dependencies:** v1.0 (all workspace features must exist for meaningful monitoring)

8. **Cross-Cutting Concerns (apply across all milestones)**
   - Credit pre-check pattern: verify sufficient credits before each activity, show cost estimate, deduct before execution, refund on failure
   - E2B sandbox reuse: all statistical analysis runs through existing E2B infrastructure
   - Agent system extension: new agents (Pulse, Investigation, Strategy) follow existing agent patterns
   - Auto-save: Collection state saved continuously (no explicit "save" action needed)
   - Error handling: graceful degradation if Pulse/Investigation/What-If fails mid-execution

9. **Deferred / Out of Scope**
   - Monitoring module (recurring automated analysis) — post v1.0 backlog (Decision #6)
   - Persistent AI Memory — future exploration post v0.11 (Decision #8)
   - PDF generation — skip unless explicitly requested (Decision #5)
     - Note: v0.9 includes basic PDF export as download option per Section 6 Step 4, but no elaborate PDF generation/templating
   - User document upload during investigation (noted as "later version" in Section 6 Step 2)
   - Full predictive ML model (moved to Appendix in requirements, not in scope)

**Formatting guidelines:**
- Use clear Markdown headers (## for milestones, ### for subsections)
- Use tables where they aid readability (summary table, credit costs)
- Keep each milestone section self-contained: someone should be able to read just one milestone section and understand its full scope
- Reference the source requirements document sections where appropriate
- No mermaid diagrams needed — this is a text planning document
- Keep the tone professional and direct — this is a technical planning document for implementation guidance
  </action>
  <verify>
    <automated>test -f requirements/Pulse-req-milestone-plan.md && wc -l requirements/Pulse-req-milestone-plan.md | awk '{print ($1 >= 200) ? "PASS: " $1 " lines" : "FAIL: only " $1 " lines"}'</automated>
  </verify>
  <done>
- requirements/Pulse-req-milestone-plan.md exists with 200+ lines
- Document covers all 5 milestones: v0.8 (Pulse), v0.9 (Collections), v0.10 (Explain), v1.0 (What-If), v0.11 (Admin Workspace)
- Each milestone has backend, frontend, and admin scope sections
- Cross-cutting concerns and deferred items documented
- Milestone sequence matches confirmed decisions from requirements
  </done>
</task>

</tasks>

<verification>
- File exists at requirements/Pulse-req-milestone-plan.md
- Document covers all milestones from v0.8 through v0.11 + v1.0
- Each milestone has backend, frontend, and admin subsections
- Deferred items clearly called out
- Cross-cutting concerns documented
</verification>

<success_criteria>
- requirements/Pulse-req-milestone-plan.md is a complete, well-structured milestone plan
- All 5 milestones have clear scope and deliverables
- Admin portal planning is included in each relevant milestone
- Document references source requirements and confirmed decisions
</success_criteria>

<output>
After completion, create `.planning/quick/3-create-pulse-milestone-implementation-pl/3-SUMMARY.md`
</output>
