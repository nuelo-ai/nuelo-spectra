---
quick_task: 4
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements/Spectra-Pulse-Requirement.md
  - requirements/Pulse-req-milestone-plan.md
autonomous: true
requirements: []
---

<objective>
Update the two Spectra Pulse requirements documents so their UX/screen flow descriptions match exactly what was built in the v0.7.12 mockup (pulse-mockup/). Only UX/screen flow content changes. Product rationale, data model (ER diagram), admin portal specs, credit cost tables, milestone backend scope, and API endpoint lists are untouched.

Purpose: These documents drive v0.8 and beyond. They must describe the flow engineers will implement — not the original brainstorm flow — so implementation teams start from an accurate baseline.
Output: Two updated .md files with accurate screen/navigation descriptions and a documented gap list (COLL-01, COLL-02).
</objective>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Audit mockup vs. requirements and capture all UX deviations</name>
  <files>
    requirements/Spectra-Pulse-Requirement.md
    requirements/Pulse-req-milestone-plan.md
  </files>
  <action>
Read the two requirements docs and compare them against what is actually built in the mockup. The mockup is the source of truth. Document every deviation before writing any changes. Use this as your checklist:

**Navigation and entry point (mockup reality):**
- Sidebar nav label is "Analysis Workspace" linking to /workspace. The landing page title is "Collections" (not "Analysis Workspace"). This matters for both docs.
- Sidebar also shows: Chat, Files, API, Settings, Admin Panel. Only /workspace, /chat, and /admin are live routes — others are # placeholders.
- Sidebar collapses/expands with a toggle button (desktop). Credit balance shown in header as a Zap-icon pill.

**Collection detail page (mockup reality — 4-tab layout):**
- The collection detail page has 4 tabs: Overview, Files, Signals, Reports.
- Overview tab shows: stat cards (files count, signal count, reports count, credits used), Run Detection banner, a 2-col grid of up to 4 Signal cards (non-interactive, link to /signals page), a compact file table with "View all files in Files tab" link, and an Activity feed.
- Files tab: FileUploadZone + FileTable with row checkboxes. Clicking a file opens a DataSummaryPanel (a slide-out sheet showing column profile). A sticky action bar at the bottom activates when files are selected, showing "Run Detection (5 credits)" button.
- Signals tab: shows all Signal cards (non-interactive) plus a button "Open Signals View" that navigates to the dedicated /signals sub-route.
- Reports tab: lists reports as rows with type badge, title, source line ("Signal — [title]", "Chat Session", or "Detection Run"), generated date, and "View Report" button.

**Detection loading (mockup reality):**
- When "Run Detection" is triggered, the entire page content is replaced by DetectionLoading (full-page transition). It is NOT an inline loading state or a spinner in a panel.

**Signals view — /workspace/collections/[id]/signals (mockup reality):**
- Separate page (not a tab). Has a breadcrumb header: Collections / [Collection Name] / Detection Results.
- Two-column layout: SignalListPanel (left, fixed width, scrollable signal list with severity sort — critical first, then warning, then info) + SignalDetailPanel (right, fills remaining width).
- Signal auto-selects the highest severity signal on load.
- SignalListPanel entries: severity badge (color-coded: critical=red, warning=amber, info=blue), signal title, category tag. There is NO "opportunity" severity in the mockup — severity values are critical, warning, info only.
- SignalDetailPanel sections (in order): title + severity/category badges, Visualization card (Recharts chart driven by signal.chartType), Analysis (description text), Statistical Evidence (2x2 metric grid), Investigation section.
- Investigation section in SignalDetailPanel contains: "Investigate" button (always enabled, 3 credits), "What-If" button (enabled only if a complete investigation exists, otherwise disabled with "(requires investigation)" label). Below the buttons: list of past investigation reports (date, title, Complete badge) or "No investigations yet".

**Guided Investigation page (mockup reality — /signals/[id]/investigate):**
- Full-page dedicated route. Sticky header: Back to Signals button, "Guided Investigation" label, "3 credits" badge, signal title on right.
- Signal context block at top (muted card showing signal title + truncated description).
- Q&A thread: each exchange shows Spectra's question, multiple-choice buttons (discrete options). User selects a choice OR provides free-text via a textarea. Answered choices are visually locked.
- After ≥3 exchanges are answered and no active (unanswered) exchange remains, a closing question appears: "Is there anything else you'd like to discuss about this signal before I generate the report?" with two choice buttons: "No, that covers it — proceed with report" and "Yes, I'd like to discuss something".
- If user picks "discuss something": a free-text textarea appears. User types and submits. This appends a new discussion exchange to the thread AND a follow-up question. closingPhase resets to "hidden", allowing another round of discussion.
- If user picks "proceed with report" (or after enough discussion): InvestigationCheckpoint appears. User clicks "Generate Report". A 2-second loading state then redirects to the report viewer.
- The requirements describe "3-5 exchanges then root cause". The mockup shows: initial 3 exchanges (or from mock session), then a closing question flow, then report generation. There is NO separate root cause card displayed before the report — investigation goes directly to report.

**What-If Objective page (mockup reality — /signals/[id]/whatif):**
- Dedicated page, accessible from SignalDetailPanel "What-If" button (only if complete investigation exists). Also accessible from the Investigation Report viewer via "Explore What-If Scenarios" CTA.
- Sticky header: Back to Signals button, "What-If Scenarios" label, "5 credits" badge, signal title on right.
- Root cause context card (muted card showing investigation report title + confidence badge + brief description).
- Objective input: "Define your objective" heading + subtext. An action search bar with a Search icon, text input, suggestion dropdown (appears on focus, 4 AI-suggested objectives), and "Generate Scenarios →" button (disabled until text entered). Suggestion selected via onMouseDown.
- When user clicks "Generate Scenarios": the page transitions to WhatIfLoading (inline, replaces main content but keeps sticky header). Loading shows 4 steps with icons (Analyzing root cause, Generating scenarios, Scoring confidence, Finalizing scenarios) with spinner/checkmark states and a progress bar. After ~10 seconds, redirects to /whatif/[sessionId].

**What-If Session page (mockup reality — /signals/[id]/whatif/[sessionId]):**
- Three-panel layout: scenario list (left, 280px fixed), scenario detail (center, fills remaining), sliding Refine panel (right overlay, 320px).
- Scenario list: vertical list of scenario buttons. Each shows scenario name, confidence badge (High/Medium/Low), estimated impact. Selected scenario has ring highlight. Below the last scenario: a separator + "Generate What-If Report" button (primary, goes to report viewer).
- Scenario detail header: scenario name, confidence badge, "Refine" button (toggles sliding chat panel).
- Scenario detail content (scrollable cards): Narrative & Recommendations, Estimated Impact (highlighted box with projected outcome), Assumptions (list), Confidence (badge + rationale text), Data Backing.
- Refine panel: slides in from the right (CSS translate), overlays the detail panel. Header: "Refine Scenario" label + X close button. Contains WhatIfRefinementChat scoped to the selected scenario. Chat history resets when switching scenarios (key prop causes remount).
- There is NO side-by-side comparison view in the mockup (WHAT-05 and WHAT-06 are deferred). The "Compare & Decide" phase from the requirements is replaced by the scenario list + "Generate Report" action.

**Report viewer (mockup reality — /collections/[id]/reports/[reportId]):**
- Full-page layout (no sidebar scroll context). Sticky header: Back button (to collection detail), report title, type badge (Investigation Report = blue, What-If Scenario Report = violet), Download as Markdown button, Download as PDF button (disabled, opacity-60).
- White paper area centered on muted background (max-w-3xl, white bg, px-16 py-12, gray-900 text). Report type badge, h1 title, generated date in paper header.
- Markdown rendered as HTML (custom converter — handles h1/h2/h3, bold, italic, hr, tables, ul, blockquotes, paragraphs).
- Investigation Reports only: "Related Signals — Same Root Cause" section (gray card per related signal, "View Signal" link). Then "Explore What-If Scenarios" CTA (violet card, "Start What-If →" button linking to /whatif for that signal).
- What-If Reports: no special extra sections.

**Chat page (mockup reality):**
- Centered column (max-w-2xl). Fixed input bar at bottom (disabled — mockup only). Messages alternate user (right-aligned bubble) and assistant (left-aligned with Activity icon avatar).
- Assistant responses contain ResultCards (table, chart placeholder, or text). Each card has "Add to Collection" button in its header.
- AddToCollectionModal: searches active collections only (archived excluded), shows collection name + signal/file counts, Add button per collection. After adding: success state with collection name for 1.5s, then modal closes. Footer: "+ Create new collection" link.

**Known gaps to document (COLL-01, COLL-02):**
- COLL-01: Collection archiving UI — collection detail page shows Active/Archived status badge, but there is NO archive/unarchive action button in the mockup. The v0.9 requirements describe archive/unarchive actions on the list and detail pages. This is unimplemented in the mockup.
- COLL-02: Collection limit usage display — the v0.9 requirements describe "3 of 5 active collections" usage text and upgrade prompts. This is NOT present in the mockup's CollectionList or collection detail header.

With this audit complete, proceed to Task 2.
  </action>
  <verify>Mental audit complete — deviations listed above. No files changed yet.</verify>
  <done>Full deviation map produced before any edits begin.</done>
</task>

<task type="auto">
  <name>Task 2: Update Spectra-Pulse-Requirement.md — UX/screen flow sections only</name>
  <files>requirements/Spectra-Pulse-Requirement.md</files>
  <action>
Update only Section 6 ("The User Journey") and any UX-describing text in Section 7 ("Admin Portal") that needs alignment. Do NOT touch: Section 1 (Decisions Log), Section 2 (The Problem), Section 3 (Naming), Section 4 (Product Architecture), Section 5 (Data Model / ER diagram), any mermaid graphs that describe module architecture (not screen flows), or any part of Section 7 that describes backend/data/API scope.

**Changes to make in Section 6:**

Replace the mermaid user journey diagram with an updated version that reflects the actual implemented flow. The key corrections:
- Detection → Collection Detail (4-tab page), not a modal/simple card list
- Signals are viewed on a dedicated "Detection Results" page (not inline on collection page)
- Investigation ends with "Generate Report" (not a root cause card → What-If prompt sequence)
- What-If starts from either the SignalDetailPanel or the Investigation Report page
- What-If goes: Objective page → Loading → Session page (scenario list + detail)
- Session page has "Generate What-If Report" action (not a compare-and-decide card view)

Replace Step 1 ("Start an Analysis — Deliverable: SIGNALS") description with:
- User enters Analysis Workspace, sees Collections list page (title: "Collections")
- User creates new Collection via "Create Collection" dialog (name field)
- Collection detail page has 4 tabs: Overview, Files, Signals, Reports
- Files tab: upload files or select from uploaded files. File click opens data summary panel (column profile). Select files with checkboxes, sticky action bar shows "Run Detection (5 credits)"
- Clicking "Run Detection" replaces entire page with a full-page detection loading state (animated, shows analysis steps)
- After detection: Overview tab shows stat cards + signal preview grid (up to 4) + activity feed. Signals tab shows all signal cards. "Open Signals View" button on Signals tab navigates to dedicated Detection Results page.

Replace Step 2 ("Guided Investigation") description with:
- From Detection Results page: user selects a Signal from the left panel. Highest severity is auto-selected.
- SignalDetailPanel shows: title, severity/category badges, visualization, analysis text, statistical evidence (2x2 grid), Investigation section
- Investigation section: "Investigate (3 credits)" button always visible. "What-If (5 credits)" button visible but disabled until a complete investigation exists.
- Clicking "Investigate" navigates to dedicated Guided Investigation page
- Investigation page: scrollable Q&A thread. Spectra asks structured questions with discrete choice buttons + free-text option per exchange.
- After ≥3 exchanges answered: closing question appears — "Is there anything else you'd like to discuss before I generate the report?" Two options: "proceed with report" or "discuss something" (opens free-text input for additional rounds)
- When user proceeds: InvestigationCheckpoint shown, clicking "Generate Report" triggers 2-second loading then opens Investigation Report in the report viewer.
- Output: Investigation Report (not a root cause card). The report viewer shows a "Related Signals — Same Root Cause" section and an "Explore What-If Scenarios" CTA.
- Note gap COLL-01: archive/unarchive actions are not yet in the mockup. Planned for v0.9.
- Severity values in the mockup: critical, warning, info (no "opportunity" severity badge).

Replace Step 3 ("What-If Scenarios") description with:
- Triggered from: (a) SignalDetailPanel "What-If" button (enabled only after complete investigation), or (b) "Start What-If →" button in Investigation Report viewer
- Phase 1 — Objective page: root cause context card shown (from investigation report), objective input with search-bar UX (type or select from 4 AI suggestions via dropdown), "Generate Scenarios →" button (disabled until text entered, costs 5 credits)
- Phase 2 — Loading: inline loading state with 4 animated steps (Analyzing root cause, Generating scenarios, Scoring confidence, Finalizing scenarios) + progress bar (~10 seconds), then redirects to session page
- Phase 3 — Session page (three-panel layout):
  - Left: scenario list (name, confidence badge, estimated impact per entry, plus "Generate What-If Report" action below last scenario)
  - Center: scenario detail (Narrative & Recommendations card, Estimated Impact card, Assumptions card, Confidence card, Data Backing card)
  - Right: sliding Refine panel (toggles via "Refine" button in detail header, overlays right side, contains scoped chat per scenario, resets on scenario switch)
- Phase 4 — Report: "Generate What-If Report" button routes to report viewer showing the What-If Scenario Report
- Deferred (WHAT-05, WHAT-06): "Add Scenario" and side-by-side comparison view are intentionally not in the mockup. Planned for v0.11.

Replace Step 4 ("Save to Collections") with a note that all progress is auto-saved to the collection. Reports appear in the collection's Reports tab. Downloading from the report viewer: "Download as Markdown" is functional; "Download as PDF" is present but disabled (planned for v0.9).

Add a new subsection at the end of Section 6: **Known Gaps (Mockup vs. Full Spec)**
- COLL-01: Collection archiving UI — Active/Archived status badge is shown on collection detail, but archive/unarchive action buttons are not implemented in the mockup. Planned for v0.9.
- COLL-02: Collection limit usage display — "X of Y active collections" counter and tier upgrade prompts are not shown in the mockup's collection list or detail pages. Planned for v0.9.
  </action>
  <verify>Open requirements/Spectra-Pulse-Requirement.md and confirm: Section 6 mermaid diagram updated, Steps 1-4 descriptions match the audit, gap COLL-01 and COLL-02 documented, no other sections changed.</verify>
  <done>Section 6 accurately describes the v0.7.12 mockup UX. Data model, product rationale, decisions log, and admin portal spec are untouched. COLL-01 and COLL-02 gaps are documented.</done>
</task>

<task type="auto">
  <name>Task 3: Update Pulse-req-milestone-plan.md — frontend scope sections only</name>
  <files>requirements/Pulse-req-milestone-plan.md</files>
  <action>
Update only the "Frontend Scope" subsections in each milestone. Do NOT touch: overview/milestone summary tables, any backend scope subsections, admin scope subsections, Key Dependencies sections, "NOT in vX.Y" lists, cross-cutting concerns, deferred/out-of-scope table, or credit cost/tier summary tables.

**v0.8 Frontend Scope — replace with:**

Navigation:
- New "Analysis Workspace" sidebar entry (links to /workspace). Route: /workspace (Collections list) and /workspace/collections/[id] (Collection detail).
- Sidebar also includes Chat, Files, API, Settings, Admin Panel. Sidebar collapse toggle for desktop. Credit balance shown in header as Zap-icon pill.

Collections list page (/workspace):
- Grid of Collection cards with name, status badge (Active = emerald, Archived = muted gray), created date, file count, signal count
- "Create Collection" button triggers dialog (name input only)
- Empty state if no collections

Collection detail page (/workspace/collections/[id]) — 4-tab layout:
- Header: collection name, status badge, credit usage pill ("Credits used: N" with Zap icon)
- Tab 1 — Overview: stat cards (files, signals, reports, credits used), Run Detection banner, 2-col grid of up to 4 Signal cards (non-interactive, link to Detection Results page), compact file table with "View all files" link, activity feed
- Tab 2 — Files: FileUploadZone (drag/drop or click), FileTable with row checkboxes. Clicking a file row opens DataSummaryPanel (slide-out sheet, column profile). Sticky action bar appears when files are selected: shows selected count + "Run Detection (5 credits)" button with credit estimate
- Tab 3 — Signals: all Signal cards (non-interactive) + "Open Signals View" button to navigate to Detection Results page
- Tab 4 — Reports: list of reports as rows (type badge, title, source line, generated date, "View Report" button)

Detection loading state:
- Triggered by "Run Detection". Replaces entire page content (full-page transition). Animated steps: Profiling data, Detecting anomalies, Analyzing trends, Generating signals. After completion, navigates to Detection Results page.

Detection Results page (/workspace/collections/[id]/signals):
- Breadcrumb header: Collections / [Name] / Detection Results
- Two-column layout: left = SignalListPanel, right = SignalDetailPanel
- SignalListPanel: scrollable, sorted by severity (critical first, warning, info). Each entry: severity color indicator, title, category tag. Auto-selects highest severity on load.
- SignalDetailPanel sections: title + severity/category badges, Visualization (Recharts chart), Analysis text, Statistical Evidence (2x2 metric grid), Investigation section (Investigate button + What-If button + past investigation report list)
- Severity color scheme: critical = red, warning = amber, info = blue (no "opportunity" severity)

**v0.9 Frontend Scope — replace with:**

Collection management:
- Archive/unarchive action on collection detail and list pages (COLL-01 — not in mockup, planned for v0.9)
- Status badge already present in mockup (Active = emerald, Archived = muted)
- Collection limit usage display: "X of Y active collections" in collection list or detail header (COLL-02 — not in mockup, planned for v0.9)
- Upgrade prompt when collection limit hit

Report viewer (/workspace/collections/[id]/reports/[reportId]):
- Full-page layout. Sticky header: Back button, report title, type badge (Investigation Report = blue badge, What-If Scenario Report = violet badge), Download as Markdown (functional), Download as PDF (present but disabled — planned backend feature)
- White paper area (max-w-3xl, white bg, gray-900 text, centered on muted background). Paper header: type badge, h1 title, generated date
- Markdown rendered inline (handles h1-h3, bold, italic, hr, tables, ul, blockquotes, paragraphs)
- Investigation Reports only: "Related Signals — Same Root Cause" section (one card per related signal with "View Signal" link), then "Explore What-If Scenarios" CTA (violet card, "Start What-If →" button linking to /whatif for that signal)

Chat-to-Collection bridge:
- "Add to Collection" button on each ResultCard in Chat
- AddToCollectionModal: searches active collections only (archived collections excluded from picker). Shows collection name, signal count, file count. "Add" button per row. Success state after add (1.5s, then closes). Footer: "+ Create new collection" link.

**v0.10 Frontend Scope — replace with:**

Investigation page (/workspace/collections/[id]/signals/[signalId]/investigate):
- Full-page dedicated route. Sticky header: "Back to Signals" button, "Guided Investigation" label, "3 credits" badge, signal title on right.
- Signal context block: muted card showing signal title and truncated description.
- Q&A thread (InvestigationQAThread): renders each exchange as a question block with discrete choice buttons and a free-text textarea option. Answered choices are visually locked.
- Closing question appears after ≥3 exchanges answered with no unanswered exchange remaining: "Is there anything else you'd like to discuss about this signal before I generate the report?" Two choice buttons: "No, that covers it — proceed with report" and "Yes, I'd like to discuss something".
- "Discuss" path: free-text textarea input, send button (Cmd+Enter or click). Submitting appends user input as a discussion exchange and a new AI follow-up question to the thread. Allows multiple discussion rounds.
- "Proceed" path: InvestigationCheckpoint component shown with "Generate Report" button. 2-second loading state, then navigates to report viewer.
- Note: there is no separate root cause card UI. The investigation ends directly in report generation.

Signal detail panel (updated for v0.10):
- Investigation section shows "Investigate (3 credits)" button (always enabled, relaunches or starts new investigation).
- "What-If (5 credits)" button shown alongside: enabled only if at least one complete investigation session exists for this signal; otherwise disabled with "(requires investigation)" text.
- List of past investigation reports below buttons (date, report title truncated, Complete badge, links to report viewer).

**v0.11 Frontend Scope — replace with:**

What-If Objective page (/workspace/collections/[id]/signals/[signalId]/whatif):
- Accessible from SignalDetailPanel (enabled only after complete investigation) and from Investigation Report "Start What-If →" CTA.
- Sticky header: "Back to Signals" link, "What-If Scenarios" label, "5 credits" badge, signal title.
- Root cause context card (muted bg): investigation report title, "High confidence" badge, brief root cause description text.
- Objective section: "Define your objective" heading, subtext. Action search bar: Search icon, text input, "Generate Scenarios →" button (disabled until text non-empty). On focus: suggestions dropdown (4 pre-computed objective options, selected via onMouseDown to avoid blur/click race).
- After "Generate Scenarios": inline loading state (replaces main content, keeps header visible). 4 animated steps with step icons and spinner/checkmark states: Analyzing root cause, Generating scenarios, Scoring confidence, Finalizing scenarios. Progress bar below steps. Estimated time shown. Navigates to session page after ~10 seconds.

What-If Session page (/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]):
- Three-panel layout. Objective shown in page header (signal title + objective text on right side).
- Scenario list panel (280px, left): vertical list of scenario buttons (name, confidence badge — High=emerald, Medium=amber, Low=muted, estimated impact). Selected scenario has ring highlight. Below last scenario: separator + "Generate What-If Report" primary button.
- Scenario detail panel (fills remaining, center): header with selected scenario name, confidence badge, "Refine" toggle button. Scrollable content with 5 cards: Narrative & Recommendations, Estimated Impact (highlighted primary-color box), Assumptions (checklist), Confidence (badge + rationale), Data Backing.
- Refine panel (320px, right overlay): slides in from right edge via CSS translate. "Refine Scenario" header + X close button. WhatIfRefinementChat scoped to selected scenario. Chat messages reset when switching scenarios (component remount).
- Deferred: "Add Scenario" button (WHAT-05) and side-by-side scenario comparison view (WHAT-06) are not in the mockup. Planned for v0.11 implementation.
  </action>
  <verify>Open requirements/Pulse-req-milestone-plan.md and confirm: all 4 milestone Frontend Scope sections updated, backend/admin/dependency/not-in sections unchanged, credit cost tables and tier summary table unchanged, COLL-01/COLL-02 gap callouts present in v0.9, WHAT-05/WHAT-06 deferred callouts present in v0.11.</verify>
  <done>Pulse-req-milestone-plan.md Frontend Scope sections accurately describe the v0.7.12 mockup UX. No backend, admin, or data model content changed. Gap callouts added where relevant.</done>
</task>

</tasks>

<verification>
After both files are saved:
1. Grep for "opportunity" severity in the updated docs — it should no longer appear in screen flow descriptions (data model may still reference it — that is OK if it was there originally).
2. Confirm COLL-01 and COLL-02 appear at least once each.
3. Confirm WHAT-05 and WHAT-06 deferred status is noted in v0.11 frontend scope.
4. Confirm no changes were made to pulse-mockup/ or any codebase file.
</verification>

<success_criteria>
- requirements/Spectra-Pulse-Requirement.md Section 6 describes the exact implemented mockup UX flow, including the 4-tab collection detail page, Detection Results as a separate page, Investigation closing-question flow → report generation, What-If objective page → loading → 3-panel session page, and report viewer with What-If CTA.
- requirements/Pulse-req-milestone-plan.md all four milestone Frontend Scope sections reflect the mockup implementation with accurate component names, layouts, and interaction patterns.
- COLL-01 (no archive action UI) and COLL-02 (no limit display UI) are explicitly documented as known mockup gaps.
- WHAT-05 and WHAT-06 are noted as deferred in v0.11 frontend scope.
- Product rationale, data model ER diagram, backend scope, admin portal spec, credit cost tables, and tier access tables are completely untouched.
- No files outside requirements/ were modified.
</success_criteria>

<output>
No SUMMARY.md required for quick tasks.
</output>
