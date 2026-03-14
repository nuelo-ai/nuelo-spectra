# Phase 49: Pulse Agent - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Independent Pulse Agent pipeline that takes CSV data files, profiles them, runs statistical analyses, and produces schema-validated Signal JSON. Includes PulseService orchestrating credit pre-check/deduction, async background execution, signal persistence, report auto-generation, and refund on failure. No frontend, no API endpoint wiring (Phase 50), no signal display UI (Phase 51).

</domain>

<decisions>
## Implementation Decisions

### Multi-agent architecture
- **Pulse Agent (brain):** Reads deep profile JSON + data_summary + optional user_context, reasons about the data's nature, generates up to 5-8 signal candidates (hypotheses), then dispatches each to the Coder pipeline for validation. After results return, confirms/rejects each hypothesis, assigns severity/category, generates Signal metadata, and delegates chart generation to the Visualization Agent
- **Coder Agent (reused):** Existing `coding_agent()` function with Pulse-specific system prompts loaded from `prompts.yaml`. Receives instructions from Pulse Agent to write statistical test code for each signal candidate
- **Code Checker (reused):** Existing `validate_code()` function with Pulse-specific prompts. Validates code follows guardrails, then executes in E2B sandbox. Results sent back to Pulse Agent
- **Visualization Agent (reused):** Existing Viz Agent generates Recharts-compatible chart data per signal. Pulse Agent provides analysis results + chart hint (e.g., "show bar chart of monthly revenue")
- Fan-out parallel execution: Pulse Agent generates all N candidates first, then kicks off N parallel (Coder -> Checker -> E2B) pipelines. All results come back for synthesis at once

### Deep profiling approach
- **Deterministic Python script** (no AI) runs in E2B sandbox — always executes the same comprehensive analyses regardless of data type: column types, distributions (mean/median/std/skew/kurtosis), correlation matrix, missing value patterns, outlier counts (IQR), time series detection, cardinality analysis
- Output is structured JSON consumed by the Pulse Agent to form hypotheses
- Profiling is the "lab equipment" (raw measurements); the Pulse Agent is the "scientist" (interpretation)
- **Cached on File model:** New `deep_profile` nullable JSON column on `File`. Profile computed once per file, reused across all collections and future Pulse Runs. Skip profiling if `file.deep_profile is not None`
- Each file profiled independently — Pulse Agent receives all per-file profiles and reasons about cross-file patterns itself

### User context input
- Optional free-text `user_context` on PulseRun model (nullable Text column) — user can provide instructions like "check Q4 revenue anomalies" or "look for correlation between marketing spend and churn"
- Passed to Pulse Agent prompt alongside deep profiles and data summaries
- **Guides but does not limit** the Pulse Agent — user context is a priority lens, not a filter. Agent still surfaces other significant findings
- Empty = fully autonomous analysis

### Pulse Agent LLM configuration
- Dedicated `pulse_agent` entry in `prompts.yaml` with its own provider/model/temperature/max_tokens — this is the "super smart" reasoning agent, likely needs a stronger model and higher token limits than other agents
- Follows existing per-agent YAML config pattern from `agents/config.py`

### Signal output
- Capped at 5-8 signals per run (configurable in `pulse_config.yaml`)
- Severity thresholds externalized to `pulse_config.yaml` from day one: `z_score_critical: 3.0`, `z_score_warning: 2.0`, `p_value_threshold: 0.05`, `correlation_strong: 0.7` — tunable post-launch without code changes
- Evidence grid per signal: 4 cells matching SIGNAL-03's 2x2 layout:
  1. **Metric** — key statistical value (e.g., "Z-Score: 3.4")
  2. **Context** — what it means (e.g., "Outlier in Q4 revenue")
  3. **Benchmark** — expected range (e.g., "Expected: $1.2M-$1.5M")
  4. **Impact** — scope of effect (e.g., "Affects 12% of records")
- Chart data delegated to Visualization Agent — Pulse Agent provides chart hint, Viz Agent generates Recharts-compatible JSON stored in `Signal.chart_data`

### Async execution model
- `POST /collections/{id}/pulse` returns **202 Accepted** immediately with `pulse_run_id`
- Background task via `asyncio.create_task()` (existing pattern, no Celery)
- Frontend polls `GET /pulse-runs/{id}` for status updates — user can navigate away and return later
- PulseRun keeps running regardless of frontend state

### PulseRun status transitions
- 5-state model mapping to PULSE-04 loading animation steps:
  - `pending` — PulseRun created, credits deducted
  - `profiling` — deep profile scripts running in E2B
  - `analyzing` — signal candidates fanning out to Coder pipelines
  - `completed` — signals + report saved to DB
  - `failed` — error stored in `error_message`, credits refunded

### Credit handling
- Deduct **before** background task (synchronous in HTTP handler):
  1. Check balance >= `workspace_credit_cost_pulse` -> 402 if insufficient
  2. Atomic deduction via `CreditService.deduct_credit()`
  3. Create PulseRun (status: pending)
  4. Return 202
  5. `asyncio.create_task(run_detection)`
- Background task wraps pipeline in try/finally — refund credits on any exception
- One active run per collection enforced — reject with 409 Conflict if PulseRun with status pending/profiling/analyzing exists

### E2B sandbox management
- One sandbox per signal candidate — each fan-out (Coder -> Checker -> Execute) gets its own fresh sandbox
- Separate sandbox for initial deep profiling step
- All sandboxes use `PULSE_SANDBOX_TIMEOUT_SECONDS=300` (not the 60s default)
- Follows existing `E2BSandboxRuntime` pattern with `data_files` multi-upload support

### Detection summary report
- LLM-generated markdown summary after all signals are confirmed — executive summary, signal-by-signal breakdown, methodology notes
- Stored as Report row with `report_type='pulse_detection'` and `pulse_run_id` FK
- Auto-generated on PulseRun completion (no user action required)

### Claude's Discretion
- Exact LangGraph StateGraph design and node wiring for the Pulse pipeline
- Deterministic profiling script contents (which specific statistical tests to include)
- Pulse Agent system prompt design and hypothesis generation strategy
- Error handling granularity within fan-out pipelines (partial success handling)
- Exact `pulse_config.yaml` structure and additional threshold values

</decisions>

<specifics>
## Specific Ideas

- The Pulse Agent should act like a data scientist: look at measurements, form hypotheses, test them, interpret results — not just run generic statistical tests
- User context is a "priority lens" — if user says "check revenue trends" but agent spots a critical outlier elsewhere, it should still surface it
- The profiling result is cached on the File model so repeat Pulse Runs skip re-profiling — profile is a property of file content, not collection membership
- Fan-out parallel processing is critical for acceptable execution time — multiple signal candidates tested simultaneously via parallel (Coder -> Checker -> E2B) pipelines
- Reuse existing Coding Agent and Code Checker with Pulse-specific prompts rather than forking new agent modules

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coding_agent()` (`backend/app/agents/coding.py`): generates Python code from instructions — reuse with Pulse-specific prompts
- `validate_code()` (`backend/app/agents/code_checker.py`): validates code safety and correctness — reuse with Pulse-specific prompts
- `visualization_agent_node` (`backend/app/agents/visualization.py`): generates chart code from analysis results — reuse for Signal chart generation
- `E2BSandboxRuntime` (`backend/app/services/sandbox/e2b_runtime.py`): sandbox execution with `data_files` multi-upload support — reuse for profiling and signal analysis
- `CreditService.deduct_credit()` (`backend/app/services/credit.py`): SELECT FOR UPDATE atomic deduction — use for pre-deduction and refund
- `StateGraph` from LangGraph (`backend/app/agents/graph.py`): existing chat pipeline pattern — template for Pulse pipeline
- `agents/config.py` + `prompts.yaml`: per-agent LLM configuration pattern — add `pulse_agent` entry

### Established Patterns
- `asyncio.create_task()` for background processing (used by Onboarding Agent)
- Per-agent YAML config: provider, model, temperature, max_tokens, system prompt
- `E2BSandboxRuntime(timeout_seconds=N)` with fresh sandbox per execution
- Service layer with static methods (e.g., `CollectionService`, `FileService`)
- Pydantic schemas with `ConfigDict(from_attributes=True)` for response models

### Integration Points
- `backend/app/models/file.py`: add `deep_profile` JSON column (new Alembic migration)
- `backend/app/models/pulse_run.py`: add `user_context` Text column (new Alembic migration)
- `backend/app/config.py`: add `PULSE_SANDBOX_TIMEOUT_SECONDS` setting (or use existing `sandbox_timeout_seconds` with override)
- `backend/app/agents/config.py` + `prompts.yaml`: add `pulse_agent` entry with dedicated LLM config
- `backend/app/services/platform_settings.py`: `workspace_credit_cost_pulse` key already exists (Phase 47)
- New files: `backend/app/agents/pulse.py` (Pulse Agent), `backend/app/services/pulse.py` (PulseService), `backend/app/config/pulse_config.yaml` (thresholds)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 49-pulse-agent*
*Context gathered: 2026-03-06*
