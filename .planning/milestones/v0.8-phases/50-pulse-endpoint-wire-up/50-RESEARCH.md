# Phase 50: Pulse Endpoint Wire-Up - Research

**Researched:** 2026-03-07
**Domain:** FastAPI endpoint wiring, APScheduler orphan-refund job, Pydantic schema extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Response contract:**
- 202 Accepted (not 200 sync) — detection runs as background task, frontend polls for results
- Trigger response body: `{ pulse_run_id, status: "pending", credit_cost }` — minimal shape, separate schema from polling response
- 409 Conflict body includes `active_run_id` so frontend can seamlessly resume polling: `{ detail: "A detection run is already in progress", active_run_id: "..." }`
- 402 Insufficient Credits body includes balance context: `{ detail: "Insufficient credits", required: <live_platform_setting>, available: <user_balance> }` — `required` comes from live `workspace_credit_cost_pulse` platform setting (not hardcoded)

**Polling endpoint:**
- Included in Phase 50 (backend must be ready before Phase 51 frontend integration)
- URL: `GET /collections/{collection_id}/pulse-runs/{run_id}` — nested under collections, ownership verified via collection
- Response: full `PulseRunDetailResponse` including complete Signal objects (title, severity, category, chart_data, statistical_evidence) when `status='completed'`
- Includes `error_message` field (surfaced to frontend when `status='failed'`)
- Trigger and polling use different schemas: trigger returns a lean `PulseRunTriggerResponse`, polling returns `PulseRunDetailResponse`

**APScheduler orphan-refund job:**
- Scans for PulseRuns stuck in `pending/profiling/analyzing` with no Signals after configurable timeout
- Orphan timeout: 10 minutes — gives 2x buffer over the 5-min E2B sandbox timeout; configurable via `PULSE_ORPHAN_TIMEOUT_MINUTES` env var
- Scan interval: every 5 minutes
- Initialization: registered in FastAPI lifespan context manager (app startup/shutdown) — not a separate module
- Refunds credits for any orphaned runs found and marks their status as `failed`

### Claude's Discretion
- APScheduler library choice (AsyncIOScheduler vs BackgroundScheduler — pick what's compatible with FastAPI's async event loop)
- Exact SQL query for orphan detection (e.g., `WHERE status IN (...) AND created_at < NOW() - interval`)
- Whether to add a `GET /collections/{id}/pulse-runs` list endpoint (not required by success criteria)
- Error message wording for edge cases

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PULSE-01 | User can trigger Pulse detection on selected files via "Run Detection (N credits)" button showing the configured flat credit cost | `POST /collections/{id}/pulse` endpoint wires `PulseService.run_detection()` to HTTP; 202 response returns `credit_cost` from live platform setting |
| PULSE-04 | User sees full-page detection loading state with 4 animated steps replacing entire page content | Backend must return `pulse_run_id` in 202 response so frontend can enter polling loop; polling endpoint `GET /collections/{id}/pulse-runs/{run_id}` provides `status` transitions |
| PULSE-05 | After detection completes, user is navigated to Detection Results page with generated Signals | Polling endpoint `PulseRunDetailResponse` must include full Signal objects when `status='completed'`; frontend navigates on `completed` response |
</phase_requirements>

---

## Summary

Phase 50 is a pure API wire-up phase. `PulseService.run_detection()` and `PulseService.get_pulse_run()` are already built and tested. The work is: (1) add two endpoints to `collections.py`, (2) add `PulseRunTriggerResponse` schema and extend `PulseRunDetailResponse` with a `signals` list, (3) enhance `PulseService.run_detection()` to return the `active_run_id` in 409 responses and `available` balance in 402 responses, (4) add the orphan-refund job to the existing `scheduler.py` and register it in the lifespan.

The codebase already has APScheduler (`AsyncIOScheduler`) running via `app/scheduler.py` with the credit-reset job. The orphan-refund job should be added as a second job in `setup_scheduler()`, gated by the same `enable_scheduler` flag. This is the lowest-risk integration path.

**Primary recommendation:** Add endpoints to `collections.py`, extend schemas in `pulse.py`, add the orphan job to `scheduler.py`, and add `PULSE_ORPHAN_TIMEOUT_MINUTES` to `config.py`. No new files, no new routers, no new scheduler module.

---

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | installed | API routing | Established project framework |
| APScheduler | installed (`AsyncIOScheduler`) | Periodic jobs | Already used for credit reset — same instance, add second job |
| SQLAlchemy async | installed | Orphan query | `async_session_maker` pattern established |
| Pydantic v2 | installed | Response schemas | `ConfigDict(from_attributes=True)` pattern established in `pulse.py` |

### No new libraries required
All tooling for this phase is already present. APScheduler's `AsyncIOScheduler` is already the correct choice for FastAPI's async event loop (as opposed to `BackgroundScheduler` which runs in a thread).

---

## Architecture Patterns

### Established Patterns to Follow

**Endpoint shape (from `collections.py`):**
```python
@router.post("/{collection_id}/pulse", response_model=PulseRunTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_pulse(
    collection_id: UUID,
    body: PulseRunCreate,
    current_user: WorkspaceUser,
    db: DbSession,
) -> PulseRunTriggerResponse:
    ...
```

**Ownership verification pattern (before service call):**
```python
collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
if collection is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
```

**Background task pattern (already in `pulse.py`):**
```python
asyncio.create_task(PulseService._run_pipeline(...))
```

**APScheduler job registration (from `scheduler.py`):**
```python
scheduler.add_job(
    orphan_refund_job,
    IntervalTrigger(minutes=5),
    id="pulse_orphan_refund_job",
    replace_existing=True,
    next_run_time=None,
)
```

### Schema Extension Pattern

`PulseRunDetailResponse` currently has `signal_count: int`. Per the CONTEXT.md decision, it needs a `signals: list[SignalDetailResponse]` field when `status='completed'`. The `get_pulse_run()` method already does `selectinload(PulseRun.signals)` so the relationship is already eager-loaded.

Signal fields from the `Signal` model: `id`, `title`, `severity`, `category`, `analysis`, `evidence` (JSON dict), `chart_data` (JSON dict), `chart_type`, `created_at`.

### 402 and 409 Enhancement

The current `PulseService.run_detection()` raises plain `HTTPException` for 402 and 409. The CONTEXT.md decisions require richer bodies:

- **402**: must include `required` (from live `workspace_credit_cost_pulse`) and `available` (user's current balance). The service already reads `cost` from platform settings; `CreditService` returns balance info via `result` from `deduct_credit()`. Need to verify what `result` exposes.
- **409**: must include `active_run_id`. The service already has `existing_run` available at the point of conflict.

These `HTTPException` raises need `detail` to be a dict (FastAPI serializes dict `detail` as-is to JSON):
```python
raise HTTPException(
    status_code=402,
    detail={"detail": "Insufficient credits", "required": float(cost), "available": float(available)},
)
```

### Orphan-Refund Job SQL Pattern

Following the existing credit-reset job pattern:

```python
async def process_orphan_refunds():
    timeout_minutes = int(os.environ.get("PULSE_ORPHAN_TIMEOUT_MINUTES", "10"))
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

    async with async_session_maker() as db:
        result = await db.execute(
            select(PulseRun).where(
                PulseRun.status.in_(["pending", "profiling", "analyzing"]),
                PulseRun.created_at < cutoff,
            )
        )
        orphans = result.scalars().all()
        for run in orphans:
            # Verify no signals exist for this run
            # Refund credits, set status='failed'
```

The job must check `~PulseRun.signals.any()` or count signals before refunding to avoid double-refunds on legitimate runs still in the `analyzing` phase that already produced signals.

---

## Integration Points (Confirmed by Code Review)

### 1. `backend/app/schemas/pulse.py`
- Add `SignalDetailResponse` schema (fields: id, title, severity, category, analysis, evidence, chart_data, chart_type, created_at)
- Add `PulseRunTriggerResponse` schema (fields: pulse_run_id, status, credit_cost)
- Extend `PulseRunDetailResponse` to include `signals: list[SignalDetailResponse]`

### 2. `backend/app/routers/collections.py`
- Add `POST /{collection_id}/pulse` — calls `PulseService.run_detection()`, returns 202
- Add `GET /{collection_id}/pulse-runs/{run_id}` — calls `PulseService.get_pulse_run()`, verifies collection ownership, returns polling response

### 3. `backend/app/services/pulse.py`
- Enhance 402 response: include `required` and `available` in detail dict
- Enhance 409 response: include `active_run_id` in detail dict
- Add `get_user_credit_balance()` helper or leverage CreditService to get `available` balance

### 4. `backend/app/scheduler.py`
- Add `process_orphan_refunds()` async function
- Register it in `setup_scheduler()` with 5-minute interval

### 5. `backend/app/config.py`
- Add `pulse_orphan_timeout_minutes: int = 10` to `Settings`

### 6. `backend/app/main.py`
- No changes needed — the orphan job registers via `setup_scheduler()`, which is already called in lifespan when `enable_scheduler=True`

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scheduled background jobs | Custom threading loop | `APScheduler AsyncIOScheduler` | Already in project, tested, handles interval triggers |
| Eager-loaded signals | Manual JOIN query | `selectinload(PulseRun.signals)` | Already done in `get_pulse_run()` |
| Ownership verification | Inline collection lookup | `CollectionService.get_user_collection()` | Established pattern in all collection endpoints |

---

## Common Pitfalls

### Pitfall 1: FastAPI dict-in-detail serialization
**What goes wrong:** `HTTPException(detail={"key": "val"})` — FastAPI wraps this in `{"detail": {"key": "val"}}` at the response level. If the client expects flat JSON, this double-wraps.
**How to avoid:** Test 402/409 responses in integration test. Confirm client parsing expectations align with FastAPI's envelope.

### Pitfall 2: Orphan job refunding runs that legitimately completed
**What goes wrong:** A run transitions to `analyzing` status, signals are being persisted, but the job fires between the status update and the signal insert commits. The job sees `status=analyzing` with no signals and refunds credits incorrectly.
**How to avoid:** In the orphan check, verify `signal_count = 0` AND `created_at < cutoff` AND `completed_at IS NULL`. The 10-minute timeout provides buffer. For extra safety, add a `SELECT COUNT(*) FROM signals WHERE pulse_run_id = :id` check before refunding.

### Pitfall 3: Orphan job and `_run_pipeline` racing on refund
**What goes wrong:** `_run_pipeline` catches an exception and calls `CreditService.refund()` at the same time the orphan job fires and also calls `CreditService.refund()` — double refund.
**How to avoid:** The orphan job should only touch runs where `status IN ('pending','profiling','analyzing')` — by the time `_run_pipeline`'s except block runs, it sets `status='failed'`. If the job fires first and sets `status='failed'`, `_run_pipeline`'s except block will still try to refund. Use `WITH FOR UPDATE` locking on the PulseRun row in the orphan job before refunding, and in `_run_pipeline` before refunding — prevents double-refund under concurrent access.

### Pitfall 4: Polling endpoint ownership bypass
**What goes wrong:** A user polls `GET /collections/{collection_id}/pulse-runs/{run_id}` with a `collection_id` they own but a `run_id` belonging to another collection. Without ownership cross-check, they can read another user's PulseRun if they guess the UUID.
**How to avoid:** Verify `pulse_run.collection_id == collection_id` after fetching by `run_id`. The `get_pulse_run()` method only looks up by `pulse_run_id` — the endpoint must add the collection ownership check.

### Pitfall 5: `asynccontextmanager` lifespan scope for APScheduler
**What goes wrong:** The orphan job registers new work inside the `async with AsyncConnectionPool(...)` block in the lifespan. If the job function itself tries to create a new `AsyncConnectionPool`, it will be outside the managed scope.
**How to avoid:** Use `async_session_maker` (not a new pool) inside the job function — same as `process_credit_resets()`. The `async_session_maker` is a module-level singleton.

---

## Code Examples

### PulseRunTriggerResponse schema
```python
# Source: inferred from existing pulse.py schema patterns
class PulseRunTriggerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pulse_run_id: UUID
    status: str
    credit_cost: float
```

### SignalDetailResponse schema
```python
class SignalDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    severity: str
    category: str
    analysis: str | None
    evidence: dict | None
    chart_data: dict | None
    chart_type: str | None
    created_at: datetime
```

### Extended PulseRunDetailResponse
```python
class PulseRunDetailResponse(PulseRunResponse):
    signal_count: int
    signals: list[SignalDetailResponse] = []
    error_message: str | None  # already on base, surfaced explicitly for polling
```

### 409 response with active_run_id
```python
raise HTTPException(
    status_code=409,
    detail={
        "detail": "A detection run is already in progress",
        "active_run_id": str(existing_run.id),
    },
)
```

### 402 response with balance context
```python
# Need available balance — fetch from CreditService before deduction attempt
# or capture from result object
raise HTTPException(
    status_code=402,
    detail={
        "detail": "Insufficient credits",
        "required": float(cost),
        "available": float(current_balance),
    },
)
```

### Orphan refund job (core pattern)
```python
async def process_orphan_refunds():
    from app.config import get_settings
    settings = get_settings()
    timeout_minutes = getattr(settings, "pulse_orphan_timeout_minutes", 10)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(PulseRun)
                .where(
                    PulseRun.status.in_(["pending", "profiling", "analyzing"]),
                    PulseRun.created_at < cutoff,
                    PulseRun.completed_at.is_(None),
                )
                .with_for_update(skip_locked=True)
            )
            orphans = result.scalars().all()
            for run in orphans:
                # Count signals to avoid refunding a run that completed partially
                signal_count_result = await db.execute(
                    select(func.count(Signal.id)).where(Signal.pulse_run_id == run.id)
                )
                signal_count = signal_count_result.scalar_one()
                if signal_count == 0:
                    await CreditService.refund(db, run.collection.user_id, ...)
                run.status = "failed"
                run.error_message = "Orphan timeout: no signals produced within timeout window"
            await db.commit()
        except Exception:
            logger.exception("Error during orphan refund processing")
            await db.rollback()
```

**Note:** The `user_id` for refund is not on `PulseRun` directly. Need to join through `Collection` to get `user_id`. The `collection` relationship is on `PulseRun` but it's not currently eager-loaded. Options: (a) add `selectinload(PulseRun.collection)` to the orphan query, or (b) join `Collection` in the query directly and carry `user_id`. Option (b) is safer and avoids N+1 queries.

---

## CreditService Verification

Need to verify what `CreditService.deduct_credit()` returns to know if `available` balance is accessible. Based on Phase 49 code:
```python
result = await CreditService.deduct_credit(db, user_id, cost)
if not result.success:
    raise HTTPException(status_code=402, ...)
```
The `result` object has `.success` and `.error_message`. If `result` also exposes `.available_balance` or similar, use it. Otherwise, need to query `UserCredit` directly before the deduction attempt to get current balance for the 402 body.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + httpx (AsyncClient) |
| Config file | `backend/pytest.ini` or `backend/pyproject.toml` (check existing) |
| Quick run command | `cd backend && pytest tests/test_pulse_endpoints.py -x -q` |
| Full suite command | `cd backend && pytest -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PULSE-01 | POST /collections/{id}/pulse returns 202 with pulse_run_id, status, credit_cost | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_202 -x` | ❌ Wave 0 |
| PULSE-01 | POST /collections/{id}/pulse with 0 credits returns 402 with required+available | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_402 -x` | ❌ Wave 0 |
| PULSE-01 | POST with active run in progress returns 409 with active_run_id | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_409 -x` | ❌ Wave 0 |
| PULSE-04 | GET /collections/{id}/pulse-runs/{run_id} returns status field for polling | integration | `pytest tests/test_pulse_endpoints.py::test_poll_pulse_run -x` | ❌ Wave 0 |
| PULSE-05 | GET returns full signals list when status=completed | integration | `pytest tests/test_pulse_endpoints.py::test_poll_pulse_run_completed -x` | ❌ Wave 0 |
| PULSE-05 | Orphan job marks stuck runs failed and refunds credits | unit | `pytest tests/test_orphan_refund.py::test_orphan_refund_job -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/test_pulse_endpoints.py -x -q`
- **Per wave merge:** `cd backend && pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_pulse_endpoints.py` — covers PULSE-01 (trigger 202/402/409), PULSE-04 (polling), PULSE-05 (signals in response)
- [ ] `backend/tests/test_orphan_refund.py` — covers orphan-refund job logic (PULSE-05 success criteria 4)
- [ ] Verify pytest is installed: `cd backend && python -m pytest --version`

---

## Open Questions

1. **CreditService.deduct_credit() result shape**
   - What we know: returns object with `.success` and `.error_message`
   - What's unclear: whether `.available_balance` (or equivalent) is exposed on failure
   - Recommendation: Read `backend/app/services/credit.py` at plan time to confirm; if not available, add a pre-deduction balance query or return it from the service

2. **Collection user_id for orphan refund**
   - What we know: `PulseRun` has `collection_id` but not `user_id` directly; `Collection` has `user_id`
   - What's unclear: whether `Collection` model has a `user_id` field (likely yes based on ownership pattern)
   - Recommendation: Confirm `Collection.user_id` exists; use a JOIN in the orphan query

3. **ENABLE_SCHEDULER flag scope for orphan job**
   - What we know: orphan job is gated by `enable_scheduler` (same as credit reset)
   - What's unclear: whether production deployment always has `ENABLE_SCHEDULER=true` on a single instance
   - Recommendation: Document in env var comments that both jobs share the flag; acceptable for Phase 50

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `backend/app/services/pulse.py` — PulseService implementation
- Direct code inspection: `backend/app/routers/collections.py` — endpoint patterns
- Direct code inspection: `backend/app/scheduler.py` — APScheduler setup
- Direct code inspection: `backend/app/schemas/pulse.py` — existing schemas
- Direct code inspection: `backend/app/models/pulse_run.py` + `signal.py` — model fields
- Direct code inspection: `backend/app/main.py` — lifespan and scheduler registration
- Direct code inspection: `backend/app/config.py` — settings structure

### Secondary (MEDIUM confidence)
- Phase 50 CONTEXT.md decisions — locked by product owner

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present in codebase
- Architecture patterns: HIGH — patterns confirmed by direct code inspection
- Schema design: HIGH — model fields confirmed, schema patterns established
- APScheduler integration: HIGH — existing job is identical pattern
- Pitfalls: HIGH — derived from direct inspection of service code
- CreditService result shape: MEDIUM — need to verify `.available_balance` presence

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable domain — FastAPI + APScheduler patterns unlikely to change)
