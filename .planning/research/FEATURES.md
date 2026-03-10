# Feature Research

**Domain:** Pulse/Detection module — data analytics platform (v0.8 Spectra Pulse)
**Researched:** 2026-03-05
**Confidence:** MEDIUM-HIGH
**Supersedes:** Previous FEATURES.md (v0.7 API Services and MCP, 2026-02-23)

---

## Context: Subsequent Milestone Scope

This research covers only the NEW v0.8 features. The following already exist and must NOT be re-planned:

- Chat Sessions with multi-file analysis, LangGraph agent system, E2B code execution
- File upload and management for user files (My Files screen)
- Admin portal with tier-based credit system and platform_settings
- Authentication, credit deduction infrastructure, user_classes.yaml

v0.8 adds four new surfaces:
1. **Collections** — workspace container (create, list, view detail with 4-tab layout, archive)
2. **File attachment to Collections** — upload or select existing files, view column profile, remove
3. **Pulse detection** — trigger analysis via Pulse Agent, full-page loading state, credit deduction
4. **Signal results** — list by severity, detail panel with chart + evidence, admin access gating

The v0.7.12 pulse-mockup is the authoritative UI contract. Features below are mapped to that
mockup and classified by ecosystem pattern (table stakes vs. differentiator vs. anti-feature).

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that analytics/detection tools universally provide. Missing any of these makes the product
feel unfinished or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Severity classification (critical / warning / info) | Every analytics alert tool (Datadog, Power BI, Tableau) uses severity tiers so users know what to act on first. | LOW | Mockup: critical=red, warning=amber, info=blue. Three tiers is correct — more tiers add confusion without value. |
| Anomaly detection signals | Core reason Pulse exists. Users expect outlier identification as the baseline output. | HIGH | Table-stakes method: statistical outlier detection (z-score / IQR). Must be present as a signal category. |
| Trend analysis signals | Users expect "is this going up or down?" as a baseline output. Period-over-period change is universally expected. | HIGH | Time-series delta (direction, % change) is expected at any analytics maturity level. |
| Signal list sorted by severity | Users assume critical signals appear first. An unsorted flat list feels broken — users should not have to hunt for urgent findings. | LOW | Mockup correctly implements: critical first, then warning, then info. Auto-select highest severity signal on page load. |
| Pre-action cost estimate shown in UI | Users on credit-based systems expect to see the cost before committing. This is table stakes for any credit-consuming AI action (established by OpenAI, Midjourney, and similar products). | LOW | Mockup: "Run Detection (5 credits)" on button label + "~N credits" in sticky action bar. Both are correct pattern. |
| Progress feedback during long-running analysis | NNG research: for operations exceeding 10 seconds, a progress bar is strongly recommended. A spinner alone is insufficient. Users need to know the system is working and how much longer to wait. | LOW | Mockup: 4-step animated indicator + determinate progress bar + "Estimated time: 15-30 seconds" text. This matches NNG recommendations. |
| Collection creation via dialog | SaaS workspace-type entities (projects, boards, workspaces) always require a name before entry. Users expect to identify their workspace before working in it. | LOW | Mockup: name-only creation dialog. Correct — description can be added later. Navigation to detail page immediately after creation. |
| Collection list with status badges | Users expect to see active vs. archived at a glance. Grid card layout is standard for workspace containers in SaaS. | LOW | Mockup: grid of collection cards with Active=emerald, Archived=muted gray. Standard pattern. |
| File attachment to workspace | Without data files, the workspace cannot run analysis. Users expect to bring their own data. | MEDIUM | Mockup: FileUploadZone + FileTable with row checkboxes. File selection activates sticky action bar. |
| Column profile / data summary on file view | Any data analytics tool that accepts uploads shows a schema preview. Users need to verify "is this the right file?" before running analysis. This is especially important before a 5-credit operation. | MEDIUM | Mockup: DataSummaryPanel slide-out sheet on file row click. Correct pattern — reuses existing Onboarding Agent profiling data. |
| Tier-based workspace access gating | SaaS users expect free and trial tiers to have restricted access to premium features. The upgrade prompt is expected UX when a limit is hit. | LOW | user_classes.yaml extension: workspace_access (boolean) + max_active_collections (int, -1=unlimited) per tier. |
| Admin credit cost configuration | Admins managing a credit-based product expect to tune costs per feature without a redeploy. | LOW | platform_settings entries for workspace_credit_cost_*. Follows existing pattern. |

### Differentiators (Competitive Advantage)

Features that go beyond what users passively expect — reasons to choose Spectra Pulse over
competing tools (Julius.ai, Power BI anomaly detection, Datadog alerts).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Concentration analysis (Pareto/80-20 signals) | Julius.ai and Akkio focus on anomalies and trends. Concentration analysis — "3 customers account for 71% of revenue" — surfaces strategic risk/opportunity that statistical outlier detectors miss. It answers business questions, not just statistical ones. | HIGH | Requires Pareto chart output (sorted bar + cumulative % line). Mockup defines "concentration" as a distinct signal category. Differentiating if executed well in the Pulse Agent. |
| Data quality as a signal type | Tools like Power BI and Tableau focus on business metric anomalies. Surfacing missing data patterns and inconsistencies as signals helps users trust the analysis — a meta-layer others skip. It also unblocks investigation: a user cannot diagnose a trend anomaly if they don't know 30% of the dates are missing. | MEDIUM | Defined in Pulse Agent scope: data quality checks as a signal category. Should surface null %, outlier %, inconsistent format counts in the statistical evidence grid. |
| Category-aware chart type per signal | Competitors show anomalies as generic line charts. Mapping chart type to signal category (area/line for trends, bar for concentration, scatter for outliers) makes findings immediately comprehensible without user configuration. | MEDIUM | Mockup: signal.chartType field drives SignalChart component, switching between LineSignalChart (area), BarSignalChart, ScatterSignalChart. The Pulse Agent must emit the correct chartType per signal category. |
| Statistical evidence grid in signal detail | Most detection tools say "anomaly detected." Spectra shows the actual statistical values behind the finding (e.g., "Z-Score: 3.8 | Confidence: 94% | Method: IQR | Baseline: 2,847"). This builds user trust and enables non-technical users to evaluate whether a signal is meaningful. | MEDIUM | Mockup: 2x2 grid of label:value pairs from signal.statisticalEvidence. The Pulse Agent must populate this grid meaningfully per signal category. This is the key differentiator in the signal detail panel. |
| Full-page detection loading state (not inline spinner) | Analytics tools typically use modal spinners or background toast notifications for analysis. Spectra's full-page step checklist creates a "something important is happening" moment that primes the user to engage with results. It frames the wait as productive, not dead time. | LOW | Mockup: DetectionLoading component with 4 steps (Analyzing files, Detecting patterns, Scoring signals, Finalizing results) + progress bar + time estimate. Psychologically effective — the animated step completion sequence makes the wait feel structured. |
| Two-panel signal viewer (list + detail) | Competitors show signal cards in a feed. The SignalListPanel + SignalDetailPanel split lets users compare signals while keeping context — more efficient for reviewing 5-15 findings than opening each card separately. This is the standard pattern for email clients and code review tools; analytics tools rarely implement it. | MEDIUM | Mockup: fixed left panel (scrollable list sorted by severity) + right detail panel (chart, analysis, evidence, investigation actions). Auto-selects highest severity signal on load. |
| Inline credit balance transparency | Pre-run estimate + running total in collection header reduces bill-shock and builds trust. This is the pattern OpenAI uses in its interface (usage dashboard) but competitors in the data analytics space do not implement at this granularity. | LOW | Mockup: "Credits used: N" Zap-icon pill in collection header. Sticky bar shows "~N credits for N files selected" before run. Both patterns are correct and should be wired to live credit balance. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time monitoring / scheduled re-runs | "Can it monitor my data automatically?" is a common ask for detection tools. | Requires data source integrations (database connectors, APIs), scheduling infrastructure, and change-detection logic. Out of scope through v0.12 per Decision #6. Implementing it early forces premature infrastructure decisions before the core workflow is validated. | Deferred to post-v0.12 backlog. Manual "Run Detection" keeps complexity bounded and user intent explicit. |
| Sensitivity threshold sliders (user-controlled algorithm tuning) | Power BI and Tableau expose sensitivity controls. Users ask for this to reduce false positives. | Sensitivity controls require users to understand statistical significance — expertise most Spectra users lack. Incorrect tuning produces misleading signals and destroys trust. | Let the Pulse Agent determine confidence from statistical evidence. Surface confidence as an attribute (high/medium/low) in the evidence grid. Users filter by severity tier instead of tuning algorithms. |
| Global alert notifications (email/push for new signals) | "Alert me when anomalies are found" is a natural next ask after detection. | Requires notification infrastructure (SMTP hooks, push) and persistent monitoring. Alerting on a one-time manual run is meaningless — you'd alert immediately after every "Run Detection." Tied to the deferred monitoring module. | Keep results in-product for v0.8-v0.12. Users navigate to their Collection to see results. Alerts are a v2+ concern tied to the monitoring module. |
| Signal export as PDF | Users always ask for PDF output. | PDF generation (Kaleido or headless Chrome) adds server-side infrastructure. Signals are work-in-progress artifacts — the input to Investigation and What-If, not a final deliverable. PDF export belongs on compiled Reports (v0.9), not raw Signals. | Download as Markdown for Signal data. Full PDF export on compiled Reports in v0.9 (already planned, present-but-disabled in mockup). |
| Bulk detection across all collections | "Run detection on everything at once" saves time. | Multiplies credit costs without user review of scope. Users may trigger unexpected large deductions. Also voids the per-run cost transparency pattern (the sticky bar is per-collection by design). | Single-collection detection with clear per-file credit estimates. Users queue runs manually. |
| "Opportunity" as a fourth severity level | The original product brainstorm listed opportunity/warning/critical/info. | The mockup correctly collapsed this to three levels. Adding "opportunity" creates cognitive ambiguity: is an opportunity more or less urgent than a warning? Severity should map to urgency, not valence (positive vs. negative). | Use signal title and description text to convey whether a finding is positive or negative. Keep severity as a pure urgency signal. |
| Confidence threshold configuration in admin | Admins may want to tune the statistical sensitivity of Pulse across all users. | Global confidence tuning changes what every user sees in their signals. This is an algorithm change, not a configuration change, and requires validated statistical expertise to tune responsibly. | Tune via the Pulse Agent prompt and method parameters in YAML config (dev-level change). Do not expose in admin UI. |

---

## Feature Dependencies

```
Collection CRUD (create, list, view)
    └──requires──> Authentication + user session (EXISTING)
    └──requires──> Tier check: workspace_access flag in user_classes.yaml (NEW — v0.8)

File Attachment to Collection
    └──requires──> Collection exists
    └──requires──> File upload infrastructure (EXISTING — user file upload system)
    └──enhances──> DataSummaryPanel reads existing column_profile from Onboarding Agent

Pulse Detection (Run Detection)
    └──requires──> Collection exists with at least 1 file attached
    └──requires──> Credit balance >= workspace_credit_cost_pulse (EXISTING credit infra)
    └──requires──> E2B sandbox (EXISTING)
    └──requires──> Pulse Agent (NEW — extends existing agent base class)
    └──produces──> Signal objects stored to DB

Detection Loading State
    └──requires──> Pulse detection API call initiated
    └──best case──> SSE progress events from backend
    └──fallback──> timer simulation (mockup pattern)

Signal Results View
    └──requires──> Pulse detection has run and produced Signals
    └──requires──> signal.chartType populated by Pulse Agent (one of: line, bar, scatter)
    └──requires──> signal.statisticalEvidence populated by Pulse Agent (pipe-delimited label:value pairs)

Admin: workspace_access tier gating
    └──requires──> user_classes.yaml extended with workspace_access + max_active_collections
    └──requires──> Collection creation API endpoint enforces tier check

Admin: Pulse credit cost setting
    └──requires──> platform_settings table (EXISTING)
    └──requires──> New setting key: workspace_credit_cost_pulse

Investigation (v0.10 — NOT in v0.8)
    └──requires──> Signals exist (v0.8 Pulse output)

What-If (v0.11 — NOT in v0.8)
    └──requires──> Complete investigation exists for the signal (v0.10 output)
    └──enforced──> "What-If" button disabled in SignalDetailPanel until hasCompleteInvestigation
```

### Dependency Notes

- **File attachment requires Collection to exist first.** Files are attached to a specific Collection, not standalone. Users can reuse files from My Files OR upload new files directly to a Collection. The Collection FILE table is an association to existing user files, not a copy.
- **Pulse detection requires at least one file selected.** The "Run Detection" button is disabled when no files are selected (enforced in sticky action bar UI and at the API level).
- **Signal chart display requires Pulse Agent to emit valid chartType.** The SignalChart component switches behavior on signal.chartType. If the Pulse Agent does not emit one of {"line", "bar", "scatter"}, the chart falls through to an "Unsupported chart type" fallback. This is a hard agent output contract.
- **What-If (v0.11) requires Investigation (v0.10).** The "What-If" button is disabled until at least one complete investigation exists for the signal. This dependency is enforced in the mockup (hasCompleteInvestigation check) and must be enforced at the API level.
- **Admin access gating must be live at v0.8 launch.** Users on free tier must see the upgrade prompt on first Collection creation attempt. Access gating cannot be deferred to a later admin milestone.
- **DataSummaryPanel does not require new backend profiling.** The column_profile JSON is already generated by the existing Onboarding Agent on file upload. DataSummaryPanel reads this existing data. No new profiling call is needed for v0.8.

---

## MVP Definition

### Launch With (v0.8)

The goal for v0.8 is a working Detect phase: users can create a Collection, attach data, run Pulse, and review Signals. This is the foundation for the v0.8-v0.12 pipeline.

- [ ] COLL-01: User can create a Collection with a name — required; workspace entry point
- [ ] COLL-02: User can view list of their Collections — required; navigation requires a list
- [ ] COLL-03: User can view Collection detail with 4-tab layout (Overview, Files, Signals, Reports) — required; the workspace container UX
- [ ] FILE-01: User can upload files (CSV/Excel) to a Collection — required; Pulse has no input without files
- [ ] FILE-02: User can view column profile of an uploaded file (DataSummaryPanel) — required; users need to verify file content before committing 5 credits
- [ ] FILE-03: User can remove a file from a Collection — required; correcting mis-attached files
- [ ] PULSE-01: User can select files and trigger Pulse detection (Run Detection button) — core v0.8 deliverable
- [ ] PULSE-02: User sees full-page detection loading state with animated steps — required; 5-30s operation requires progress feedback per NNG guidelines
- [ ] PULSE-03: User can view Signal cards on Detection Results page sorted by severity — core v0.8 deliverable
- [ ] PULSE-04: User can view Signal detail (visualization, analysis text, statistical evidence) — required; a signal without evidence is unactionable
- [ ] PULSE-05: Credit cost pre-check and deduction before Pulse run — required; existing credit infrastructure must be respected; refund on failure
- [ ] ADMIN-01: Admin can configure workspace access per tier in user_classes.yaml — required from launch; gating must be present when feature goes live
- [ ] ADMIN-02: Admin can configure Pulse credit cost via platform_settings — required; cost must be runtime-tunable from day one

### Add After Validation (v0.9)

These extend the v0.8 foundation once the core Pulse workflow is validated with users.

- [ ] Collection archiving (archive/unarchive actions) — COLL-01 mockup gap; needed when users accumulate collections and hit tier limits
- [ ] Collection limit usage display ("X of Y active collections") — COLL-02 mockup gap; needed when users approach their tier limit
- [ ] Report compilation from Signals — the output layer for the workspace
- [ ] Chat-to-Collection bridge — connect existing Chat Sessions to workspace
- [ ] PDF export on reports — planned, "present but disabled" state already in mockup report viewer

### Future Consideration (v2+)

- [ ] Monitoring module (recurring automated detection) — requires scheduling infrastructure and data source connectors; deferred post-v0.12
- [ ] Email/push alerts on new signals — tied to monitoring module; meaningless on one-time manual runs
- [ ] Sensitivity/confidence threshold controls — initial users lack statistical expertise to tune correctly; adds risk of misleading signals
- [ ] Cross-collection signal correlation — "same root cause across multiple collections" — requires cross-workspace analysis infrastructure

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Collection CRUD (create, list, view) | HIGH | LOW | P1 |
| File attachment + removal | HIGH | MEDIUM | P1 |
| DataSummaryPanel (column profile) | MEDIUM | LOW | P1 — reuses existing profiling data |
| Run Detection (Pulse Agent trigger) | HIGH | HIGH | P1 — core v0.8 deliverable |
| Detection loading state (4-step animated) | MEDIUM | LOW | P1 — UX requirement for 5-30s operations |
| Signal list sorted by severity | HIGH | LOW | P1 — results are unactionable without prioritization |
| Signal detail panel (chart + evidence) | HIGH | MEDIUM | P1 — evidence grid is the differentiator |
| Credit pre-check + estimate in sticky bar | HIGH | LOW | P1 — required by existing credit system contract |
| Tier-based access gating | HIGH | LOW | P1 — must be present at launch |
| Pulse credit cost admin setting | MEDIUM | LOW | P1 — runtime tunable from day one |
| Concentration analysis signals | HIGH | HIGH | P2 — differentiator; complexity is in Pulse Agent, not UI |
| Data quality signals | MEDIUM | MEDIUM | P2 — trust builder; implement after core anomaly/trend signals work |
| Collection archiving | MEDIUM | LOW | P2 — v0.9; needed when collections accumulate |
| Collection limit display ("X of Y") | LOW | LOW | P2 — v0.9; needed when users approach limits |

**Priority key:**
- P1: Must have for v0.8 launch
- P2: Should have — add in v0.9 or when first users request it
- P3: Nice to have — future consideration

---

## Statistical Method Recommendations for Pulse Agent

**Confidence: MEDIUM** — based on Adobe Analytics official documentation (ETS, GESD), general
industry practice (z-score, IQR, STL), and Pareto's known utility for business segment analysis.
The specific method-to-category mapping is a reasoned recommendation, not a codified standard.

### Table Stakes Methods (implement in v0.8)

These are the minimum analysis methods for a credible detection output. Users will recognize these findings as meaningful without needing to understand the statistics.

| Method | Signal Category | Recommended Chart Type | Key Evidence Fields to Populate |
|--------|----------------|------------------------|----------------------------------|
| IQR outlier detection | anomaly | scatter | Q1, Q3, IQR, outlier count, threshold |
| Z-score outlier detection | anomaly | scatter | Mean, Std Dev, Z-Score, % above threshold |
| Period-over-period delta | trend | line (area) | Previous period total, current period total, % change, direction |
| Cumulative % / Pareto | concentration | bar | Top-N items share %, total item count, items covering 80% |
| Missing data rate | quality | bar | Null % per column, affected row count, column name |

### Differentiating Methods (implement in v0.8 if time allows, else v0.9)

| Method | Signal Category | Chart Type | Key Evidence Fields |
|--------|----------------|------------|---------------------|
| Linear trend slope (regression) | trend | line (area) | Slope direction, R², start/end values, projected next period |
| Segment dominance | concentration | bar | Top segment share %, segment count, HHI-style concentration score |
| Distribution skew | anomaly | bar | Skewness coefficient, mode vs. mean delta, long-tail direction |

### Not in v0.8 (complexity without validated need)

- Time-series seasonal decomposition (STL/ETS) — requires sufficient date granularity and regular time intervals; most user uploads will not qualify
- ML-based anomaly detection (Isolation Forest, DBSCAN) — high complexity, hard to explain to non-technical users; save for when simpler methods fail to surface meaningful signals
- Cross-file correlation analysis — reserved for multi-file Collection scenarios; evaluate after v0.8 usage patterns emerge

---

## Behavioral Clarifications for v0.8

These are implementation decisions derived from the mockup and requirements that resolve ambiguities before development begins.

### Signal Severity Classification

Use exactly three severity levels: **critical**, **warning**, **info**. The Pulse Agent determines severity from statistical evidence:

- **critical** (red) — high-impact finding warranting immediate attention (e.g., z-score > 3, top-1 segment > 90% concentration, >30% missing data)
- **warning** (amber) — notable finding worth investigating (e.g., z-score 2-3, significant trend deviation, 10-30% missing data)
- **info** (green — per mockup #22c55e) — low-urgency pattern worth noting (e.g., mild skew, gradual trend, <10% missing data)

The "opportunity" severity from the original brainstorm is correctly dropped in the mockup. Do not reintroduce it. Signal valence (positive vs. negative) belongs in the title and description text, not the severity badge. Severity maps to urgency only.

The thresholds above should be externalized to YAML config so they can be tuned without code changes.

### Collection CRUD Behaviors

- **Create:** Name-only dialog. No description field on create (can edit after). Navigate immediately to the new Collection's detail page on creation. Default to the Overview tab.
- **List:** Grid of collection cards. Empty state when no collections exist (with "Create Collection" CTA). Status badges visible at a glance. Filter by status is a v0.9 addition — not needed in v0.8.
- **View Detail:** 4-tab layout (Overview, Files, Signals, Reports). Default to Overview. Tab state does not persist across navigation in v0.8.
- **Archive:** NOT in v0.8 scope. This is the COLL-01 mockup gap, planned for v0.9.
- **Delete:** NOT in v0.8 scope. The requirements do not specify collection deletion — archiving serves the lifecycle management need.
- **Search/Filter:** NOT in v0.8 scope. Collection counts will be small (1-5 per tier) — filtering is premature.

### Credit Cost Model

The mockup's `COST_PER_FILE` constant implies a per-file pricing model. The requirements specify a flat 5.0 credit cost for Pulse (not per-file). Resolve this:

- Use the flat `workspace_credit_cost_pulse` platform setting (default: 5.0) regardless of file count
- The sticky action bar should show the flat cost: "Run Detection (5 credits)" — not scaled by file count
- The credit estimate text in the sticky bar can show "Run Detection (5 credits)" to communicate the flat cost clearly
- If a per-file pricing model is later desired, it requires a platform_settings change and a UI change — not a code change

### Detection Loading UX

The mockup uses `setTimeout` simulation (3500ms per step, ~14s total). In production:

- Best case: advance steps via SSE progress events from the Pulse API endpoint
- Acceptable fallback: advance on polling (e.g., GET /collections/{id}/pulse/status every 2s)
- Degraded fallback: timer simulation with a longer timeout buffer (real E2B analysis may exceed 30s depending on file size and method count; use 45s buffer minimum)

The 4 step labels in the mockup are: "Analyzing files", "Detecting patterns", "Scoring signals", "Finalizing results". These are correct — do not change them. They correspond to the actual Pulse Agent pipeline phases.

### Signal Chart Type Assignment

The Pulse Agent must emit exactly one of: `"line"`, `"bar"`, `"scatter"` per signal. Use the following mapping:

| Signal Category | Default Chart Type | Rationale |
|----------------|-------------------|-----------|
| trend | line | Time-series data; area/line chart communicates direction and magnitude |
| concentration | bar | Categorical comparison; sorted bars communicate dominance |
| anomaly | scatter | Point-based; scatter shows the outlier position relative to the cluster |
| quality | bar | Column-level comparison; bars communicate relative severity per column |

If the Pulse Agent cannot determine the appropriate chart type from the data, default to `"bar"`. Do not emit null — the SignalChart component has no null handling.

---

## Competitor Feature Analysis

| Feature | Julius.ai | Power BI Anomaly Detection | Spectra Pulse v0.8 Approach |
|---------|-----------|---------------------------|------------------------------|
| Signal severity levels | Not applicable — chat-based, no signal concept | Sensitivity slider (not severity tiers) | 3-tier: critical/warning/info. Severity = urgency, not sensitivity setting. |
| Chart type per signal | User-selected from available chart types | Line chart only (time-series focused) | Agent-determined per category: area/line for trends, bar for concentration, scatter for outliers |
| Statistical evidence transparency | Shows data table + natural language explanation | Shows "expected range" band on chart | 2x2 evidence grid (method, values, confidence, baseline) — most transparent of the three |
| Workspace / collection concept | Chat sessions (no persistent structured workspace) | No workspace concept — anomalies embedded in reports | Collections as persistent workspaces with 4-tab layout — strongest workspace pattern of the three |
| Credit / cost transparency | Post-run usage counter | Not applicable (subscription) | Pre-run estimate in button label + sticky bar + header balance — comprehensive |
| Loading UX during analysis | Inline spinner | Progress bar during report refresh | Full-page step indicator + progress bar — most communicative for 5-30s waits |
| Tier-based access gating | No tier gating on core chat feature | No tier gating on anomaly detection | Workspace access per tier (free=no access, trial=1 collection, standard=5, premium=unlimited) |
| Concentration / Pareto signals | Not surfaced as a signal type | Not implemented | Planned as a distinct signal category — differentiator |
| Data quality as a signal type | Not surfaced | Separate data quality tooling | Integrated as a Pulse signal category — not siloed |

---

## Dependencies on Existing Spectra Features

| v0.8 Feature | Dependency on Existing System | Notes |
|---|---|---|
| File attachment to Collection | Existing file upload infrastructure (user file store) | Files are associated to a Collection, not copied. The Collection FILE table references the user's existing file. |
| DataSummaryPanel | Existing Onboarding Agent column profiling (column_profile JSON) | No new backend profiling call needed for v0.8. DataSummaryPanel reads already-computed data. |
| Pulse Agent execution | Existing E2B sandbox, existing agent base class | New agent, same execution infrastructure. Same allowlist.yaml governs permitted Python libraries. |
| Credit pre-check and deduction | Existing credit_transactions table + SELECT FOR UPDATE atomic deduction | Same pattern as chat message credit deduction. New platform_settings key for the cost amount. |
| Tier-based workspace gating | Existing user_classes.yaml + user.user_class field | Extend YAML schema. Collection creation API enforces workspace_access on every request. |
| Admin Pulse credit cost setting | Existing platform_settings table + admin settings UI | Add "Workspace Credit Costs" section to existing admin settings page. Same runtime-configurable pattern as default_credit_cost. |

---

## Sources

- Adobe Analytics Anomaly Detection Statistical Techniques: https://experienceleague.adobe.com/en/docs/analytics-platform/using/cja-workspace/anomaly-detection/statistics-anomaly-detection (MEDIUM confidence — verified ETS/GESD methodology; industry standard status extrapolated)
- NNG Skeleton Screens (loading UX for 10+ second operations): https://www.nngroup.com/articles/skeleton-screens/ (HIGH confidence — authoritative UX research; progress bars recommended for 10+ second waits)
- Smart Interface Design Patterns (loading UX): https://smart-interface-design-patterns.com/articles/designing-better-loading-progress-ux/ (MEDIUM confidence — aligns with NNG: progress bar + status updates for 10+ second waits)
- Power BI Anomaly Detection (UI/severity pattern): https://powerbi.microsoft.com/en-us/blog/anomaly-detection-preview/ (HIGH confidence — first-party documentation; sensitivity slider vs. severity tier design decision informed by this)
- IBM Databand (severity-prioritized signal view): https://www.ibm.com/products/databand/data-anomaly-detection (MEDIUM confidence — severity-prioritized alert view confirmed as industry pattern)
- Pareto Chart 101: https://mode.com/blog/pareto-chart-101/ (HIGH confidence — standard charting practice; sorted bar + cumulative line is the canonical Pareto output)
- Pyramid Analytics Pareto Analysis: https://www.pyramidanalytics.com/blog/pareto-analysis-using-the-80-20-rule/ (MEDIUM confidence — confirms Pareto chart as BI standard for concentration analysis)
- Spectra Pulse Requirement (Section 6 — User Journey): requirements/Spectra-Pulse-Requirement.md (HIGH confidence — primary source)
- Pulse Milestone Plan (v0.8 scope): requirements/Pulse-req-milestone-plan.md (HIGH confidence — primary source)
- pulse-mockup source code: pulse-mockup/src/components/workspace/ — detection-loading.tsx, signal-detail-panel.tsx, signal-chart.tsx, sticky-action-bar.tsx (HIGH confidence — authoritative UI contract per project decision in PROJECT.md)

---
*Feature research for: Spectra Pulse v0.8 (Detection module)*
*Researched: 2026-03-05*
