# Project Research Summary

**Project:** Spectra Pulse v0.8 — Detection Module
**Domain:** Statistical analysis module additive to existing LLM-powered data analytics SaaS
**Researched:** 2026-03-05
**Confidence:** HIGH

## Executive Summary

Spectra v0.8 (Pulse) is a statistical detection module built entirely on top of an existing production platform (FastAPI, LangGraph, E2B, Next.js, PostgreSQL). The scope is deliberately additive: 3 new Python libraries, 3 new SQLAlchemy models, 9 new API endpoints, a new LangGraph pipeline, and a frontend component migration from an already-completed mockup. Nothing in the existing stack changes. The primary engineering challenge is building a high-quality Pulse Agent that produces structured, schema-validated Signal outputs — not building infrastructure, which is already in place.

The recommended approach is a strict build-order that lets each layer validate before the next begins: data models and migrations first, backend CRUD API second, Pulse Agent third (with its own validation milestone before frontend wiring), and frontend migration last. The pulse-mockup in the repo is the authoritative UI contract — 20 components should be migrated (not rebuilt) with only import paths, mock data, and setTimeout stubs swapped for live API calls. The frontend migration also requires two mandatory setup steps before any component is copied: a globals.css token update (Nord palette to Hex.tech palette) and a ThemeProvider addition to the main app's provider tree.

The two highest risks in v0.8 are both in the backend. First, the Pulse Agent must emit schema-validated JSON Signals — this is a known gap in the existing agent system and the only agent in the codebase where Pydantic structured output is essential (Signals are schema-sensitive in a way that chat code generation is not). Second, E2B sandbox timeout defaults (60 seconds) are sized for interactive chat queries and will consistently fail on multi-file statistical analysis — a Pulse-specific 300-second timeout must be set before writing any Pulse execution code. Both risks are avoidable with explicit early decisions and are not blockers to launching v0.8.

---

## Key Findings

### Recommended Stack

The existing stack is locked (FastAPI, PostgreSQL, LangGraph, E2B, Next.js 16, React 19, shadcn/ui, TanStack Query, Zustand, Plotly.js). v0.8 adds three Python libraries and one frontend package.

**Core technology additions:**

- `scipy >=1.11.0`: univariate anomaly detection (Z-score, IQR) and data quality checks — pre-installed in E2B default Python environment; no sandbox config changes needed
- `statsmodels >=0.14.0`: trend analysis with statistical significance (OLS regression, Augmented Dickey-Fuller) — produces p-values and confidence intervals that populate Signal `statistical_evidence` fields
- `scikit-learn >=1.3.0`: multi-column anomaly detection (Isolation Forest) and concentration analysis — handles cross-column interactions that per-column statistics miss
- `recharts ^2.15.3`: Signal visualizations (AreaChart for trends, BarChart for concentration, ScatterChart for anomalies) — already present in pulse-mockup at this version; Recharts v3 was alpha as of March 2026, stay on v2.x

All three Python libraries are compatible with the existing pandas dependency and share the same numpy transitive dependency without conflicts. Version requirements verified on PyPI (scipy 1.17.1, statsmodels 0.14.6, sklearn 1.8.0). See `.planning/research/STACK-pulse-v0.8.md` for installation commands and full compatibility matrix.

**What NOT to add:** `prophet` (requires Stan/C++ build toolchain), `pyod` (wraps sklearn with unnecessary overhead), Plotly in Signal visualization JSON (conflicts with chat DataCard format), Celery (E2B execution is the bottleneck; async task queue adds infrastructure without UX improvement).

### Expected Features

**Must have (table stakes) — v0.8 launch:**

- Collection CRUD (create, list, view with 4-tab layout) — workspace entry point; no Pulse without it
- File attachment to Collection (upload CSV/Excel, view column profile, remove) — Pulse requires data
- Pulse detection trigger (Run Detection button, credit pre-check, deduction, refund on failure) — core v0.8 deliverable
- Full-page detection loading state with 4-step animated indicator — mandatory per NNG guidelines for 5-30s operations
- Signal list sorted by severity (critical first, auto-select highest on page load) — unsorted results feel broken
- Signal detail panel with chart, analysis text, and statistical evidence grid — signal without evidence is unactionable
- Pre-run credit cost estimate in button label and sticky action bar — table stakes for credit-based systems
- Tier-based workspace access gating (workspace_access + max_active_collections per tier) — must be live at launch

**Should have (differentiators) — v0.8 if time allows, else v0.9:**

- Concentration analysis (Pareto/80-20 signals) — answers business questions that statistical outlier detection misses; not present in Julius.ai or Power BI
- Data quality as a signal type — surfaces missing data patterns that block investigation of other signals
- Category-aware chart type per signal (agent-determined; no user configuration) — competitors show anomalies as generic line charts
- Statistical evidence grid (method, values, confidence, baseline) — "anomaly detected" is insufficient; Spectra shows the statistical proof
- Inline credit balance transparency — pre-run estimate plus running total in collection header

**Defer to v0.9:**

- Collection archiving and limit display ("X of Y active collections")
- Report compilation from Signals
- Chat-to-Collection bridge (add-to-collection-modal.tsx exists in mockup but is deferred)
- PDF export on compiled Reports (button is "present but disabled" in mockup — correct for v0.8)

**Permanent anti-features (do not build):**

- Real-time monitoring / scheduled re-runs — requires scheduling infrastructure; deferred post-v0.12
- Sensitivity threshold sliders — users lack statistical expertise to tune safely; filter by severity tier instead
- "Opportunity" as a fourth severity level — severity must map to urgency, not valence; signal valence belongs in title text

See `.planning/research/FEATURES.md` for full feature prioritization matrix, behavioral clarifications, and statistical method recommendations.

### Architecture Approach

v0.8 adds a completely independent module to the existing platform. No existing router, model, service, or agent file is modified. The Pulse pipeline is a separate LangGraph `StateGraph` with its own `PulseAgentState` TypedDict — it shares E2B sandbox runtime and the LLM factory with the chat pipeline, but has no shared state or graph nodes. Frontend workspace routes are placed in a new `(workspace)` route group (parallel to the existing `(dashboard)` group), with their own layout, rather than inheriting the Chat sidebar layout.

**Major components:**

1. `Collection`, `CollectionFile`, `Signal` models — three new SQLAlchemy models; `CollectionFile` uses `__tablename__ = "collection_files"` (never "files" — name collision with existing model)
2. `CollectionService` and `PulseService` — service layer between router and agent; routers own HTTP concerns only
3. `pulse/graph.py` — independent LangGraph pipeline: `profile_data_node` → `run_analyses_node` → `generate_signals_node`; separate E2B executions per analysis type
4. `pulse/analyzers.py` — E2B-executable Python scripts for anomaly, trend, concentration, quality checks
5. `/collections` router — 9 endpoints with `WorkspaceAccess` FastAPI dependency for tier and collection limit enforcement
6. `frontend/src/components/workspace/` — 15 migrated components from pulse-mockup (copy-and-wire, not rebuild)
7. `(workspace)/` route group — 3 new pages: `/workspace`, `/workspace/collections/[id]`, `/workspace/collections/[id]/signals`

**Critical path:** data models → Alembic migration → CollectionService → collections router → Pulse Agent validation → Pulse endpoint → frontend migration.

See `.planning/research/ARCHITECTURE.md` for complete data flow diagrams, component responsibility table, anti-patterns, and build-order dependency chain.

### Critical Pitfalls

1. **CollectionFile model named "File" — import collision with existing `app.models.file.File`** — Name the new model `CollectionFile` with `__tablename__ = "collection_files"`. Phase 1 decision; all downstream work depends on it being correct.

2. **E2B sandbox timeout (60s default) too short for multi-file statistical analysis** — Create `PULSE_SANDBOX_TIMEOUT_SECONDS` config (default: 300). Instantiate `E2BSandboxRuntime(timeout_seconds=300)` in the Pulse Agent. Must be set before writing any Pulse execution code.

3. **Pulse Agent LLM output inconsistency breaks Signal parsing** — Known gap in the existing agent system. For Pulse specifically: use a strict `PulseAgentOutput` Pydantic model with `Literal["critical", "warning", "info"]` for severity. A Signal schema with missing or invalid fields silently discards user-paid results.

4. **Dashboard layout wraps workspace pages in Chat sidebar** — Create a `(workspace)` route group parallel to `(dashboard)`, with its own layout.tsx. Never nest `/workspace` inside `(dashboard)`. Must be established before any component migration.

5. **CSS token conflict: Nord palette (main frontend) vs. Hex.tech palette (mockup)** — Update `globals.css` dark mode tokens globally to the mockup's Hex.tech palette before migrating any components. Also add `ThemeProvider` from `next-themes` to `frontend/src/app/providers.tsx` (currently absent).

6. **Credit deduction with no atomic rollback on long-running Pulse failures** — Add an APScheduler orphan-refund job that scans for credit deductions with no matching Signal rows after N minutes. Implement before the Pulse endpoint goes live.

See `.planning/research/PITFALLS-v0.8-pulse.md` for full "Looks Done But Isn't" checklist, recovery strategies, integration gotchas, and security mistakes.

---

## Implications for Roadmap

The architecture research identifies a clear build-order based on hard layer dependencies. The phase structure below follows that order with pitfall-avoidance checkpoints at each transition.

### Phase 1: Data Foundation

**Rationale:** Every other phase depends on the data models and configuration. This is the critical path blocker. Must be done first and done correctly — the CollectionFile naming decision here affects import trees across all backend phases.

**Delivers:** Three new SQLAlchemy models (`Collection`, `CollectionFile`, `Signal`) with Alembic migration, user_classes.yaml extended with `workspace_access` and `max_active_collections` per tier, `workspace_credit_cost_pulse` added to platform_settings DEFAULTS and VALID_KEYS.

**Addresses:** COLL-01 through COLL-03 data layer, FILE-01 through FILE-03 data layer, ADMIN-01, ADMIN-02 data layer

**Avoids:**
- Pitfall 1 (CollectionFile name collision) — naming decision made before any downstream imports
- Pitfall 7 (Alembic migration table name inconsistency) — review autogenerated migration before running; confirm `__tablename__` matches migration exactly

### Phase 2: Backend CRUD API

**Rationale:** The frontend cannot develop against live APIs until CRUD endpoints exist. This phase unblocks parallel frontend work and provides a Postman/curl validation milestone before agent complexity is introduced.

**Delivers:** Full `/collections` router with CRUD endpoints, file upload, `WorkspaceAccess` dependency, Pydantic schemas. Frontend can list, create, and upload files before the Pulse Agent exists.

**Uses:** `CollectionService`, existing `CreditService` (deduct-before-execute pattern), `user_classes.yaml` tier enforcement via `WorkspaceAccess` dependency

**Avoids:**
- Pitfall 6 (credit deduction with no rollback) — design APScheduler orphan-refund safety net in this phase before wiring the Pulse endpoint

### Phase 3: Pulse Agent

**Rationale:** The Pulse Agent is the core value proposition of v0.8. It must be validated against real CSV data independently before the frontend signal display is built. Discovering agent output quality issues after building the UI wastes effort. Phase 3 can begin in parallel with Phase 2 after Phase 1 completes.

**Delivers:** `PulseAgentState` TypedDict, `pulse/analyzers.py` (per-analysis-type E2B scripts), `pulse/agent.py` (LLM structuring with Pydantic output), `pulse/graph.py` (3-node pipeline), `pulse_service.py`. Validates Signal generation from a test CSV before any frontend work begins.

**Uses:** scipy (anomaly/quality), statsmodels (trend), scikit-learn (concentration and multi-column anomaly), `E2BSandboxRuntime` with Pulse-specific 300s timeout, `get_llm()` factory with new `pulse_agent` entry in `prompts.yaml`

**Avoids:**
- Pitfall 2 (E2B timeout) — `PULSE_SANDBOX_TIMEOUT_SECONDS=300` set before first execution
- Pitfall 8 (LLM output inconsistency) — `PulseAgentOutput` Pydantic schema defined before writing the agent prompt; severity `Literal["critical", "warning", "info"]` enforced

### Phase 4: Pulse Endpoint Wire-Up

**Rationale:** Short phase connecting the validated Pulse Agent to the API layer. Only begins after Phase 3 produces confirmed Signal output from real data files.

**Delivers:** `POST /collections/{id}/pulse` endpoint with credit pre-check, atomic deduction, agent invocation, credit refund on failure (try/finally), returns signals list in response.

**Avoids:**
- Pitfall 6 continued — orphan-refund APScheduler job tested end-to-end; tier re-check on pulse trigger (not just on collection creation)

### Phase 5: Frontend Migration

**Rationale:** With Phases 1-4 complete, the backend contract is fully defined and stable. Frontend migration is low-risk: copy-and-wire from a completed mockup with only import paths, mock data, and setTimeout stubs changing.

**Delivers:** 15 workspace components in `frontend/src/components/workspace/`, 3 new route pages in `(workspace)/` group, TanStack Query hooks (useCollections, useCollection, usePulse), Next.js API route handlers, recharts installed, ChatSidebar "Pulse Analysis" nav entry.

**Uses:** recharts v2.15.3, existing TanStack Query patterns, existing Zustand stores (no new store needed)

**Build order within Phase 5:** globals.css token update → ThemeProvider addition → `(workspace)` route group and layout → workspace list page → collection detail (Files tab first, then Overview, then Signals tab, then Reports stub) → detection results page → sidebar nav entry

**Avoids:**
- Pitfall 4 (dashboard layout wrapping workspace) — `(workspace)` route group created before migrating any component
- Pitfall 5 (CSS token conflict) — globals.css updated to Hex.tech palette before any component copy
- Pitfall 6 (missing ThemeProvider) — added to providers.tsx before any component copy

### Phase 6: Admin and Tier Gating QA

**Rationale:** Access gating must be verified end-to-end before the feature is released. This is validation work, not new development — confirming that WorkspaceAccess dependency, tier config, and credit cost config all behave correctly for every tier.

**Delivers:** Confirmed tier access enforcement (free tier blocked, trial tier limited, premium unlimited), collection limit enforcement, workspace_credit_cost_pulse editable via admin settings page.

**Addresses:** ADMIN-01, ADMIN-02 verified end-to-end; tier re-check on Pulse trigger (not just Collection creation)

**Use the "Looks Done But Isn't" checklist** from `.planning/research/PITFALLS-v0.8-pulse.md` as the verification checklist for this phase.

---

### Phase Ordering Rationale

- Phase 1 blocks everything — no model means no migration, no service, no router, no frontend
- Phase 2 before Phase 5 — frontend needs stable API contracts; CRUD is low-risk and unblocks parallel mockup study
- Phase 3 can run in parallel with Phase 2 — agent work depends only on Phase 1 models, not on CRUD routes
- Phase 3 must complete with validated Signal output before Phase 5 Signals tab is built — this is the quality gate protecting the core v0.8 value proposition
- Phase 5 migration is copy-and-wire only when Phases 1-4 are stable — reduces rework risk significantly
- Phase 6 is QA and gating verification, not net-new development — correctly positioned last

### Research Flags

Phases needing deeper investigation during planning:

- **Phase 3 (Pulse Agent):** Agent prompt engineering for Signal generation quality is empirical. The statistical method-to-signal-category mapping in FEATURES.md is a recommendation, not a codified standard. Allocate iteration cycles for prompt development and multi-provider testing before declaring the agent done.
- **Phase 3 (Pulse Agent):** The split of analyses across separate E2B executions (one per detection type) reduces timeout risk but adds implementation complexity. Validate the exact split strategy against actual user file sizes before finalizing the analyzer design.

Phases with well-documented patterns (research phase can be skipped):

- **Phase 1 (Data Foundation):** Standard SQLAlchemy 2.0 model plus Alembic migration. Existing codebase has clear, inspected examples for every pattern used.
- **Phase 2 (Backend CRUD):** Standard FastAPI router plus service layer. Pattern is identical to the existing files and sessions routers inspected in architecture research.
- **Phase 5 (Frontend Migration):** Copy-and-wire from completed mockup. Component tree, prop names, and interactions are fully defined in pulse-mockup source. No pattern research needed — only import and data wiring changes.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All new library versions verified on PyPI. recharts v2.15.3 confirmed working in pulse-mockup against React 19. scipy/statsmodels/sklearn compatibility matrix cross-verified. E2B pre-installation of all three confirmed. |
| Features | HIGH | Mockup directly inspected as authoritative UI contract. Feature classification informed by Adobe Analytics, Power BI, and NNG primary sources. Statistical method-to-category mapping is MEDIUM within overall HIGH confidence. |
| Architecture | HIGH | Based entirely on direct codebase inspection — every claim traced to a specific file. Build order derived from hard dependency analysis, not opinion. |
| Pitfalls | HIGH | All eight critical pitfalls verified against the actual codebase: existing File model import sites counted, sandbox timeout config confirmed, providers.tsx ThemeProvider absence confirmed, globals.css tokens directly compared. No speculative pitfalls. |

**Overall confidence:** HIGH

### Gaps to Address

- **Statistical severity thresholds:** The thresholds in FEATURES.md (Z-score > 3 = critical, etc.) are reasonable starting values but need empirical validation against real user data. Externalize to YAML config from day one so they can be tuned post-launch without code changes.
- **Pulse Agent prompt quality:** Cannot be fully specified in research — requires iteration against real CSV inputs. Allocate explicit time in Phase 3 for prompt development and multi-provider testing before treating the agent as production-ready.
- **Per-file vs. flat credit pricing:** The mockup implies per-file pricing but requirements specify flat cost (5.0 credits regardless of file count). FEATURES.md resolves this in favor of flat pricing, but confirm the decision with the owner before Phase 2 wires the credit check.
- **Detection Results page cancel UX:** PITFALLS.md flags that the full-page loading state blocks back navigation. FEATURES.md does not specify a cancel action. Decide before Phase 5 — either implement a cancel endpoint or allow navigation away with a "Detection running in background" toast.

---

## Sources

### Primary (HIGH confidence)

- `pulse-mockup/src/components/workspace/` — 20 component files, authoritative UI contract
- `pulse-mockup/src/lib/mock-data.ts` — `ChartType = "line" | "bar" | "scatter"` type definition
- `backend/app/models/file.py` — existing `File` model, 8+ import sites confirmed
- `backend/app/services/credit.py` — `SELECT FOR UPDATE` atomic deduction pattern
- `backend/app/services/sandbox/e2b_runtime.py` — 60s sandbox timeout confirmed
- `backend/app/config.py` — `sandbox_timeout_seconds: 60`, `stream_timeout_seconds: 180`
- `frontend/src/app/(dashboard)/layout.tsx` — ChatSidebar + LinkedFilesPanel hardcoded on all dashboard routes
- `frontend/src/app/providers.tsx` — ThemeProvider absence confirmed
- `pulse-mockup/src/app/globals.css` vs `frontend/src/app/globals.css` — Hex.tech vs. Nord palette difference confirmed
- `requirements/Pulse-req-milestone-plan.md` — authoritative v0.8 scope
- `requirements/Spectra-Pulse-Requirement.md` — ER diagram, user journey, data model decisions
- [SciPy 1.17.1 on PyPI](https://pypi.org/project/SciPy/) — current version verified
- [statsmodels 0.14.6 on PyPI](https://pypi.org/project/statsmodels/) — current version verified
- [scikit-learn 1.8.0 documentation](https://scikit-learn.org/stable/) — current version verified
- [Recharts API documentation](https://recharts.github.io/en-US/api/) — AreaChart, BarChart, ScatterChart API verified stable in v2.x

### Secondary (MEDIUM confidence)

- Adobe Analytics Anomaly Detection Statistical Techniques — ETS/GESD methodology; statistical method-to-category mapping informed by this
- NNG Skeleton Screens research — progress bars required for 10+ second waits; informs detection loading UX requirement
- Power BI Anomaly Detection documentation — severity tier vs. sensitivity slider design decision
- IBM Databand — severity-prioritized alert view confirmed as industry pattern
- Pareto Chart 101 (Mode.com) — sorted bar plus cumulative line as canonical Pareto output

### Tertiary (LOW confidence)

- Statistical severity thresholds (Z-score > 3 = critical, etc.) — reasoned starting values based on academic statistics conventions; require empirical validation against user data before treating as final

---

*Research completed: 2026-03-05*
*Ready for roadmap: yes*
