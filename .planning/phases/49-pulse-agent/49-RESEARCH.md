# Phase 49: Pulse Agent - Research

**Researched:** 2026-03-06
**Domain:** LangGraph multi-agent pipeline, Pydantic structured output, E2B sandbox orchestration, credit management
**Confidence:** HIGH

## Summary

Phase 49 builds the Pulse Agent pipeline -- the core intelligence that takes CSV data files, profiles them deterministically in E2B sandboxes, reasons about findings via an LLM "brain" agent, dispatches N parallel (Coder -> Checker -> E2B) pipelines for statistical validation, synthesizes results into schema-validated Signal JSON, delegates chart generation to the existing Visualization Agent, and auto-generates a detection summary report. The pipeline is wrapped in a `PulseService` that handles credit pre-check/deduction, async background execution, signal persistence, and refund-on-failure.

The codebase already has all building blocks: `E2BSandboxRuntime` with multi-file upload, `coding_agent()` and `validate_code()` reusable with custom prompts, `visualization_agent_node` for chart generation, `CreditService.deduct_credit()` and `CreditService.refund()` for atomic credit operations, `StateGraph` from LangGraph for pipeline composition, and per-agent YAML configuration via `agents/config.py` + `prompts.yaml`. The new code is primarily wiring these together with Pulse-specific state, prompts, and orchestration logic.

**Primary recommendation:** Build the Pulse pipeline as a new LangGraph `StateGraph` in `backend/app/agents/pulse.py` with three core nodes (`profile_data_node`, `run_analyses_node`, `generate_signals_node`), a dedicated `PulseAgentState` TypedDict, Pydantic `PulseAgentOutput` for strict schema validation, and a `PulseService` in `backend/app/services/pulse.py` that orchestrates the full lifecycle (credit check -> create PulseRun -> background task -> persist signals -> generate report -> refund on failure).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Multi-agent architecture:** Pulse Agent (brain) reasons about data, generates 5-8 signal candidates, dispatches each to Coder pipeline for validation. Coder Agent (reused `coding_agent()`) and Code Checker (reused `validate_code()`) with Pulse-specific prompts from `prompts.yaml`. Visualization Agent (reused) generates Recharts-compatible chart data per signal. Fan-out parallel execution for all N candidates simultaneously.
- **Deep profiling approach:** Deterministic Python script (no AI) runs in E2B sandbox for comprehensive statistical profiling. Output is structured JSON. Cached on File model (`deep_profile` nullable JSON column). Each file profiled independently. Skip profiling if `file.deep_profile is not None`.
- **User context input:** Optional free-text `user_context` on PulseRun model (nullable Text column). Guides but does not limit the Pulse Agent.
- **Pulse Agent LLM configuration:** Dedicated `pulse_agent` entry in `prompts.yaml` with its own provider/model/temperature/max_tokens.
- **Signal output:** Capped at 5-8 signals per run (configurable in `pulse_config.yaml`). Severity thresholds externalized to `pulse_config.yaml`. Evidence grid per signal: 4 cells (Metric, Context, Benchmark, Impact). Chart data delegated to Visualization Agent.
- **Async execution model:** `POST /collections/{id}/pulse` returns 202 Accepted. Background task via `asyncio.create_task()`. Frontend polls for status.
- **PulseRun status transitions:** pending -> profiling -> analyzing -> completed/failed.
- **Credit handling:** Deduct before background task (synchronous in HTTP handler). Pre-check balance >= `workspace_credit_cost_pulse`. Atomic deduction via `CreditService.deduct_credit()`. try/finally refund on any exception. One active run per collection (409 Conflict).
- **E2B sandbox management:** One sandbox per signal candidate. Separate sandbox for profiling. `PULSE_SANDBOX_TIMEOUT_SECONDS=300`.
- **Detection summary report:** LLM-generated markdown stored as Report row with `report_type='pulse_detection'` and `pulse_run_id` FK.

### Claude's Discretion
- Exact LangGraph StateGraph design and node wiring for the Pulse pipeline
- Deterministic profiling script contents (which specific statistical tests to include)
- Pulse Agent system prompt design and hypothesis generation strategy
- Error handling granularity within fan-out pipelines (partial success handling)
- Exact `pulse_config.yaml` structure and additional threshold values

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PULSE-02 | System pre-checks credit balance before execution and blocks run if insufficient | CreditService.deduct_credit() returns `CreditDeductionResult(success=False)` when balance < cost; PulseService reads `workspace_credit_cost_pulse` from platform_settings; 402 response on insufficient credits |
| PULSE-03 | System deducts flat credit cost before execution and refunds on failure | CreditService.deduct_credit() for atomic deduction, CreditService.refund() for failure path; try/finally pattern in background task; flat cost from `workspace_credit_cost_pulse` platform setting (default "5.0") |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | >=1.0.7 | StateGraph pipeline for Pulse Agent flow | Already used for chat pipeline in `graph.py` |
| pydantic | >=2.0.0 | `PulseAgentOutput` schema validation for Signal JSON | Already used throughout codebase (pydantic-settings) |
| e2b-code-interpreter | >=1.0.2 | Sandbox execution for profiling scripts and signal validation code | Already used via `E2BSandboxRuntime` |
| langchain-core | >=0.3.0 | Message types (SystemMessage, HumanMessage), LLM interface | Already used by all agents |
| sqlalchemy | (existing) | Async DB operations for PulseRun/Signal/Report persistence | Already used throughout |
| PyYAML | (existing) | Load `pulse_config.yaml` thresholds | Already used for `prompts.yaml` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | stdlib | `asyncio.create_task()` for background execution, `asyncio.gather()` for fan-out parallelism | Background task launch, parallel signal candidate processing |
| decimal | stdlib | Credit cost precision for CreditService operations | Credit pre-check and deduction |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| asyncio.create_task | Celery | Celery adds infrastructure complexity; E2B is the real bottleneck, not task queuing (explicitly out of scope) |
| LangGraph StateGraph | Plain async functions | StateGraph provides structured state passing, retry patterns, and LangSmith observability for free |
| YAML config for thresholds | DB settings | YAML is simpler for day-one externalization; can migrate to DB later if needed |

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── agents/
│   ├── pulse.py              # NEW: PulseAgentState, pulse_agent_node, run_analyses_node,
│   │                         #       generate_signals_node, build_pulse_graph()
│   └── state.py              # EXTEND: Add PulseAgentState TypedDict
├── config/
│   ├── prompts.yaml          # EXTEND: Add pulse_agent entry
│   └── pulse_config.yaml     # NEW: Thresholds, signal caps, profiling config
├── schemas/
│   └── pulse.py              # NEW: PulseAgentOutput, SignalOutput, PulseRunResponse
├── services/
│   └── pulse.py              # NEW: PulseService (run_detection, credit logic, persistence)
└── config.py                 # EXTEND: Add PULSE_SANDBOX_TIMEOUT_SECONDS setting
```

### Pattern 1: LangGraph StateGraph for Pulse Pipeline
**What:** A dedicated `StateGraph(PulseAgentState)` with three core nodes wired linearly: `profile_data_node` -> `run_analyses_node` -> `generate_signals_node`. The `run_analyses_node` internally handles fan-out parallelism via `asyncio.gather()`.
**When to use:** This is the only pipeline pattern for Phase 49.
**Example:**
```python
# Source: Existing pattern from backend/app/agents/graph.py
from langgraph.graph import StateGraph

class PulseAgentState(TypedDict):
    collection_id: str
    user_id: str
    pulse_run_id: str
    user_context: str
    file_profiles: list[dict]       # Deep profile JSON per file
    data_summaries: list[str]       # data_summary per file
    signal_candidates: list[dict]   # Hypotheses from Pulse Agent brain
    validated_signals: list[dict]   # Confirmed signals after code execution
    signals_output: list[dict]      # Final PulseAgentOutput-validated signals
    error: str

def build_pulse_graph():
    graph = StateGraph(PulseAgentState)
    graph.add_node("profile_data", profile_data_node)
    graph.add_node("run_analyses", run_analyses_node)
    graph.add_node("generate_signals", generate_signals_node)
    graph.set_entry_point("profile_data")
    graph.add_edge("profile_data", "run_analyses")
    graph.add_edge("run_analyses", "generate_signals")
    graph.set_finish_point("generate_signals")
    return graph.compile()
```

### Pattern 2: Pydantic Structured Output for Signal Validation
**What:** A `PulseAgentOutput` Pydantic model with strict Literal types for severity and chartType. Every signal emitted by the pipeline MUST pass this validation before DB persistence.
**When to use:** Final validation gate before writing signals to the database.
**Example:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class SignalEvidence(BaseModel):
    metric: str          # e.g., "Z-Score: 3.4"
    context: str         # e.g., "Outlier in Q4 revenue"
    benchmark: str       # e.g., "Expected: $1.2M-$1.5M"
    impact: str          # e.g., "Affects 12% of records"

class SignalOutput(BaseModel):
    id: str
    title: str
    severity: Literal["critical", "warning", "info"]
    category: str
    chartType: Literal["bar", "line", "scatter"]
    analysis_text: str
    statistical_evidence: SignalEvidence
    chart_data: dict | None = None

class PulseAgentOutput(BaseModel):
    signals: list[SignalOutput]
```

### Pattern 3: PulseService Lifecycle Orchestration
**What:** A static-method service class (matching `CollectionService`, `CreditService` patterns) that owns the full Pulse detection lifecycle: credit pre-check, PulseRun creation, background task launch, pipeline invocation, signal persistence, report generation, and error/refund handling.
**When to use:** Called from the HTTP handler (Phase 50) and for Phase 49 testing.
**Example:**
```python
class PulseService:
    @staticmethod
    async def run_detection(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
        file_ids: list[UUID],
        user_context: str | None = None,
    ) -> PulseRun:
        """Full lifecycle: check credits -> deduct -> create run -> launch background."""
        # 1. Read cost from platform_settings
        cost = Decimal(str(await platform_settings.get(db, "workspace_credit_cost_pulse")))

        # 2. Atomic deduction (pre-check built into deduct_credit)
        result = await CreditService.deduct_credit(db, user_id, cost)
        if not result.success:
            raise HTTPException(status_code=402, detail=result.error_message)

        # 3. Check no active run (409 Conflict)
        # 4. Create PulseRun(status="pending")
        # 5. Commit (makes run visible for polling)
        # 6. asyncio.create_task(_run_pipeline(pulse_run_id, ...))
        # 7. Return pulse_run for 202 response

    @staticmethod
    async def _run_pipeline(pulse_run_id: UUID, ...):
        """Background task with try/finally refund."""
        async with async_session_maker() as db:
            try:
                # Update status: profiling -> analyzing -> completed
                # Invoke build_pulse_graph()
                # Persist signals
                # Generate report
            except Exception as e:
                # Update status: failed, store error_message
                await CreditService.refund(db, user_id, cost, reason="Pulse detection failed")
            finally:
                await db.commit()
```

### Pattern 4: Fan-Out Parallel Signal Validation
**What:** The `run_analyses_node` receives N signal candidates from the Pulse Agent brain, then dispatches N parallel pipelines (each: Coder -> Checker -> E2B execute) using `asyncio.gather()`. Each pipeline gets its own fresh E2B sandbox with the 300s timeout.
**When to use:** Inside the `run_analyses_node` graph node.
**Example:**
```python
async def _validate_single_candidate(candidate: dict, file_data: list, settings) -> dict | None:
    """Run one candidate through Coder -> Checker -> E2B pipeline."""
    # 1. coding_agent()-style LLM call with Pulse-specific prompt
    # 2. validate_code() AST check
    # 3. E2B execution with PULSE_SANDBOX_TIMEOUT_SECONDS=300
    # Returns validated result or None on failure

async def run_analyses_node(state: PulseAgentState) -> dict:
    candidates = state["signal_candidates"]
    tasks = [_validate_single_candidate(c, ...) for c in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    validated = [r for r in results if r is not None and not isinstance(r, Exception)]
    return {"validated_signals": validated}
```

### Pattern 5: Deep Profiling with Cache-on-File
**What:** A deterministic Python script executed in E2B that produces comprehensive statistical profiles. Results cached as `deep_profile` JSON column on the `File` model. Profile computed once, skipped on subsequent runs.
**When to use:** First node in the Pulse pipeline.
**Example:**
```python
async def profile_data_node(state: PulseAgentState) -> dict:
    profiles = []
    for file_info in state["files"]:
        if file_info["deep_profile"] is not None:
            profiles.append(file_info["deep_profile"])
            continue
        # Run deterministic profiling script in E2B
        runtime = E2BSandboxRuntime(timeout_seconds=300)
        result = await asyncio.to_thread(
            runtime.execute, code=PROFILING_SCRIPT, timeout=300.0,
            data_files=[(file_bytes, filename)]
        )
        profile = json.loads(result.stdout[-1])  # structured JSON
        profiles.append(profile)
        # Cache on File model (persisted by caller)
    return {"file_profiles": profiles}
```

### Anti-Patterns to Avoid
- **Forking agent modules:** Do NOT copy `coding.py` or `code_checker.py` to create Pulse versions. Reuse the existing functions with Pulse-specific prompts loaded from `prompts.yaml`.
- **Synchronous pipeline execution:** Do NOT run the Pulse pipeline synchronously in the HTTP handler. It will timeout. Always use `asyncio.create_task()` and return 202.
- **Global sandbox timeout:** Do NOT use the global `sandbox_timeout_seconds=60` for Pulse operations. Pulse needs `PULSE_SANDBOX_TIMEOUT_SECONDS=300`.
- **Skipping Pydantic validation:** Do NOT persist signals without passing them through `PulseAgentOutput` validation first. Invalid data will break the frontend (Phase 51).
- **Sharing DB sessions across task boundaries:** The background task MUST create its own `async_session_maker()` session. The HTTP handler's session will be closed by the time the background task runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Credit pre-check & deduction | Custom SQL balance check | `CreditService.deduct_credit()` | Already handles SELECT FOR UPDATE, unlimited users, insufficient balance |
| Credit refund on failure | Custom balance increment | `CreditService.refund()` | Already handles atomic refund with transaction logging |
| Code generation for stats | Custom code template engine | Reuse `coding_agent()` with Pulse prompts | Handles retry, code extraction, provider-agnostic LLM |
| Code validation | Custom AST walker | Reuse `validate_code()` | Handles AST + LLM validation, error classification |
| Sandbox execution | Custom Docker/subprocess | `E2BSandboxRuntime.execute()` | Handles file upload, timeout, error wrapping, cleanup |
| Chart generation | Custom chart code builder | Reuse `visualization_agent_node` pattern | Already generates Recharts-compatible JSON |
| LLM initialization | Direct API calls | `get_llm()` factory + per-agent YAML config | Provider-agnostic, handles all 5 providers |
| Platform setting reads | Direct DB query | `platform_settings.get(db, "workspace_credit_cost_pulse")` | TTL-cached, JSON-parsed, default-merged |

**Key insight:** Phase 49 is an orchestration phase, not a capabilities phase. Every capability (sandbox, LLM, credit, validation) already exists. The work is wiring them together correctly with Pulse-specific prompts, state management, and error handling.

## Common Pitfalls

### Pitfall 1: DB Session Lifecycle in Background Tasks
**What goes wrong:** Background task uses the HTTP handler's DB session, which is already closed/committed by the time the task runs.
**Why it happens:** `asyncio.create_task()` captures the closure's variables, but the session is scoped to the request lifecycle.
**How to avoid:** Always create a fresh session inside the background task using `async_session_maker()`. The HTTP handler should only pass IDs (UUID), not ORM objects.
**Warning signs:** `DetachedInstanceError`, `SessionClosedError`, or stale data reads.

### Pitfall 2: Partial Fan-Out Failures
**What goes wrong:** One of N parallel signal validation pipelines fails (E2B timeout, LLM error), and the entire Pulse run is marked as failed.
**Why it happens:** Using `asyncio.gather()` without `return_exceptions=True` causes first exception to cancel all tasks.
**How to avoid:** Always use `asyncio.gather(*tasks, return_exceptions=True)`. Filter out exceptions from results. A Pulse run with 3/5 valid signals is still successful.
**Warning signs:** All signals missing when only one E2B sandbox timed out.

### Pitfall 3: Deep Profile Script Producing Invalid JSON
**What goes wrong:** The profiling script crashes or outputs non-JSON, and the pipeline proceeds with None/empty profile.
**Why it happens:** Edge cases in data (encoding issues, empty files, all-null columns, extremely wide tables).
**How to avoid:** Wrap the profiling script execution in error handling. Validate that stdout contains parseable JSON. Fall back to a minimal profile rather than None.
**Warning signs:** `json.JSONDecodeError` in profiling node, Pulse Agent receiving empty profiles.

### Pitfall 4: Credit Refund Race Condition
**What goes wrong:** Background task fails but refund is not executed because the exception handling path is incomplete.
**Why it happens:** Exception in the `finally` block itself (e.g., DB connection lost), or exception before the try block.
**How to avoid:** Wrap the entire background task in try/finally. The `finally` block should have its own try/except to ensure refund attempt is logged even if it fails. Use `CreditService.refund()` which is idempotent (no-ops for unlimited users).
**Warning signs:** Credits deducted but never refunded after pipeline failures.

### Pitfall 5: Pydantic Validation Rejecting Valid Signals
**What goes wrong:** The LLM generates signals with severity "Critical" (capitalized) or chartType "Bar" instead of the lowercase Literal values.
**Why it happens:** LLMs don't reliably respect case requirements in free-text generation.
**How to avoid:** Normalize severity and chartType to lowercase before Pydantic validation. Add `.lower()` mapping in the signal construction step.
**Warning signs:** All signals rejected by PulseAgentOutput validation despite containing valid data.

### Pitfall 6: PULSE_SANDBOX_TIMEOUT_SECONDS Not Wired
**What goes wrong:** Pulse sandboxes use the default 60s timeout, causing profiling scripts to timeout on large datasets.
**Why it happens:** Forgetting to add the config to `Settings` or using `settings.sandbox_timeout_seconds` instead.
**How to avoid:** Add `PULSE_SANDBOX_TIMEOUT_SECONDS: int = 300` to `config.py` Settings class. Use it explicitly in all Pulse E2B calls.
**Warning signs:** Profiling timeout errors on datasets > ~50K rows.

## Code Examples

### PulseAgentState TypedDict
```python
# Source: Pattern from backend/app/agents/state.py (ChatAgentState)
class PulseAgentState(TypedDict):
    """State for the Pulse Agent LangGraph pipeline."""
    collection_id: str
    user_id: str
    pulse_run_id: str
    user_context: str                # Optional user guidance text
    file_data: list[dict]            # [{file_id, filename, file_path, file_type, data_summary, deep_profile}]
    file_profiles: list[dict]        # Deep profile JSON per file (from profiling node)
    signal_candidates: list[dict]    # Hypotheses from Pulse Agent brain
    validated_signals: list[dict]    # Confirmed signals after Coder pipeline
    signals_output: list[dict]       # Final validated signal dicts
    report_content: str              # Generated markdown report
    error: str
```

### Credit Pre-Check and Deduction
```python
# Source: Pattern from backend/app/services/credit.py
from decimal import Decimal
from app.services import platform_settings
from app.services.credit import CreditService

# Read cost
cost_str = await platform_settings.get(db, "workspace_credit_cost_pulse")
cost = Decimal(str(cost_str))  # "5.0" -> Decimal("5.0")

# Atomic deduction (includes balance check)
result = await CreditService.deduct_credit(db, user_id, cost)
if not result.success:
    # result.error_message contains user-friendly message
    # result.next_reset contains next credit reset date
    raise HTTPException(status_code=402, detail=result.error_message)
```

### Refund on Failure
```python
# Source: Pattern from backend/app/services/credit.py
async def _run_pipeline(pulse_run_id, user_id, cost, ...):
    async with async_session_maker() as db:
        try:
            # ... pipeline execution ...
            await db.commit()
        except Exception as e:
            try:
                await CreditService.refund(
                    db, user_id, cost,
                    reason=f"Pulse detection failed: {str(e)[:200]}"
                )
                # Update PulseRun status to failed
                pulse_run.status = "failed"
                pulse_run.error_message = str(e)[:1000]
                await db.commit()
            except Exception as refund_err:
                logger.error(f"Refund failed for pulse_run {pulse_run_id}: {refund_err}")
```

### E2B Execution with Pulse Timeout
```python
# Source: Pattern from backend/app/services/sandbox/e2b_runtime.py
from app.config import get_settings

settings = get_settings()
pulse_timeout = settings.pulse_sandbox_timeout_seconds  # 300

runtime = E2BSandboxRuntime(timeout_seconds=pulse_timeout)
result = await asyncio.to_thread(
    runtime.execute,
    code=profiling_script,
    timeout=float(pulse_timeout),
    data_files=[(file_bytes, filename)],
)
```

### Adding pulse_agent to prompts.yaml
```yaml
# Source: Pattern from backend/app/config/prompts.yaml
  pulse_agent:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 8000
    system_prompt: |
      You are the Pulse Agent for Spectra analytics platform.
      You act as a senior data scientist examining statistical profiles...
      [full prompt design is Claude's discretion]
```

### New Alembic Migration for deep_profile Column
```python
# Pattern: backend/alembic/versions/ (hand-written migration per Phase 47 decision)
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("files", sa.Column("deep_profile", sa.JSON(), nullable=True))
    op.add_column("pulse_runs", sa.Column("user_context", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("pulse_runs", "user_context")
    op.drop_column("files", "deep_profile")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sequential signal processing | Fan-out parallel `asyncio.gather()` | Phase 49 design | Critical for acceptable execution time (5-8 candidates x 60s each = 5-8 min serial vs ~60s parallel) |
| Generic sandbox timeout (60s) | Pulse-specific 300s timeout | Phase 49 design | Required for comprehensive profiling scripts on large datasets |
| Free-text LLM JSON output | Pydantic `PulseAgentOutput` validation | Phase 49 design | Guarantees Signal schema compliance before DB persistence |
| Single-agent pipeline | Multi-agent with brain + workers | Phase 49 design | Pulse Agent reasons holistically, Coder Agents validate individually |

## Open Questions

1. **Exact profiling script contents**
   - What we know: Should cover column types, distributions, correlation matrix, missing values, outlier counts, time series detection, cardinality analysis
   - What's unclear: Specific Python libraries to use inside E2B (scipy.stats, numpy, pandas profiling), exact output JSON schema
   - Recommendation: Claude's discretion per CONTEXT.md. Use pandas + numpy + scipy.stats (all available in E2B). Define a fixed output schema in `pulse_config.yaml`.

2. **Pulse Agent prompt design**
   - What we know: Should act like a data scientist -- examine profiles, form hypotheses, dispatch validation
   - What's unclear: Exact prompt structure, how to instruct the LLM to output structured hypothesis JSON
   - Recommendation: Claude's discretion. Use the existing `with_structured_output()` LangChain pattern or JSON-in-prompt approach.

3. **Partial success threshold**
   - What we know: Fan-out can have partial failures. A run with 3/5 valid signals should still be "completed".
   - What's unclear: Minimum number of valid signals to consider a run successful
   - Recommendation: Set minimum to 1 valid signal = completed. 0 valid signals = failed with error "No signals could be validated".

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `backend/pytest.ini` or pyproject.toml `[tool.pytest]` |
| Quick run command | `cd backend && python -m pytest tests/test_pulse_agent.py -x` |
| Full suite command | `cd backend && python -m pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PULSE-02 | Credit pre-check blocks run when balance insufficient | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_precheck_insufficient -x` | No - Wave 0 |
| PULSE-02 | Credit pre-check passes when balance sufficient | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_precheck_sufficient -x` | No - Wave 0 |
| PULSE-03 | Credit deduction before pipeline start | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_deduction_on_start -x` | No - Wave 0 |
| PULSE-03 | Credit refund on pipeline failure | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_refund_on_failure -x` | No - Wave 0 |
| SC-1 | Pipeline runs end-to-end (profile -> analyze -> signals) | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pipeline_end_to_end -x` | No - Wave 0 |
| SC-2 | PulseAgentOutput Pydantic validation (severity Literal, chartType Literal, no None fields) | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pydantic_validation -x` | No - Wave 0 |
| SC-3 | PULSE_SANDBOX_TIMEOUT_SECONDS=300 in config | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pulse_timeout_config -x` | No - Wave 0 |
| SC-4 | Active run conflict detection (409) | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_active_run_conflict -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_pulse_agent.py tests/test_pulse_service.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_pulse_agent.py` -- covers pipeline nodes, Pydantic validation, config
- [ ] `backend/tests/test_pulse_service.py` -- covers credit logic, lifecycle, active run conflict
- [ ] No new framework install needed (pytest already configured)
- [ ] No new conftest fixtures needed (existing `clear_config_caches` handles YAML cache clearing; all tests use `unittest.mock`)

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/app/agents/graph.py` -- existing LangGraph StateGraph pattern
- Codebase inspection: `backend/app/agents/config.py` -- per-agent YAML config pattern
- Codebase inspection: `backend/app/services/credit.py` -- CreditService.deduct_credit() and refund() APIs
- Codebase inspection: `backend/app/services/sandbox/e2b_runtime.py` -- E2BSandboxRuntime with multi-file upload
- Codebase inspection: `backend/app/services/platform_settings.py` -- workspace_credit_cost_pulse default "5.0"
- Codebase inspection: `backend/app/models/pulse_run.py` -- PulseRun model (Phase 47)
- Codebase inspection: `backend/app/models/signal.py` -- Signal model (Phase 47)
- Codebase inspection: `backend/app/models/file.py` -- File model (needs deep_profile column)
- Codebase inspection: `backend/app/config.py` -- Settings class (needs PULSE_SANDBOX_TIMEOUT_SECONDS)
- Codebase inspection: `backend/app/agents/state.py` -- TypedDict state pattern
- Codebase inspection: `backend/app/agents/coding.py` -- coding_agent() reusable function
- Codebase inspection: `backend/app/agents/visualization.py` -- visualization_agent_node pattern

### Secondary (MEDIUM confidence)
- LangGraph documentation (training data): StateGraph, Command routing, conditional edges
- Pydantic v2 documentation (training data): Literal types, model validation

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, versions pinned in pyproject.toml
- Architecture: HIGH -- all patterns derived from existing codebase patterns; new code is orchestration of existing capabilities
- Pitfalls: HIGH -- identified from direct code inspection of session lifecycle, asyncio patterns, and credit service behavior

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable -- no external dependencies changing)
