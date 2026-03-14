# Phase 50: Pulse Endpoint Wire-Up - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `POST /collections/{id}/pulse` to the existing collections router, wiring the already-built `PulseService.run_detection()` to HTTP. Includes a status polling endpoint and APScheduler orphan-refund job. `PulseService`, credit logic, and Pydantic schemas from Phase 49 are all in place — this phase is purely about surfacing them via API.

</domain>

<decisions>
## Implementation Decisions

### Response contract
- **202 Accepted** (not 200 sync) — detection runs as background task, frontend polls for results
- Trigger response body: `{ pulse_run_id, status: "pending", credit_cost }` — minimal shape, separate schema from polling response
- **409 Conflict** body includes `active_run_id` so frontend can seamlessly resume polling the existing run: `{ detail: "A detection run is already in progress", active_run_id: "..." }`
- **402 Insufficient Credits** body includes balance context: `{ detail: "Insufficient credits", required: <live_platform_setting>, available: <user_balance> }` — `required` comes from live `workspace_credit_cost_pulse` platform setting (not hardcoded)

### Polling endpoint
- Included in Phase 50 (backend must be ready before Phase 51 frontend integration)
- URL: `GET /collections/{collection_id}/pulse-runs/{run_id}` — nested under collections, ownership verified via collection
- Response: full `PulseRunDetailResponse` including complete Signal objects (title, severity, category, chart_data, statistical_evidence) when `status='completed'`
- Includes `error_message` field (surfaced to frontend when `status='failed'`)
- Trigger and polling use **different schemas**: trigger returns a lean `PulseRunTriggerResponse`, polling returns `PulseRunDetailResponse`

### APScheduler orphan-refund job
- Scans for PulseRuns stuck in `pending/profiling/analyzing` with no Signals after a configurable timeout
- **Orphan timeout:** 10 minutes — gives 2x buffer over the 5-min E2B sandbox timeout. Configurable via `PULSE_ORPHAN_TIMEOUT_MINUTES` env var
- **Scan interval:** every 5 minutes
- **Initialization:** registered in FastAPI lifespan context manager (app startup/shutdown) — not a separate module
- Refunds credits for any orphaned runs found and marks their status as `failed`

### Claude's Discretion
- APScheduler library choice (AsyncIOScheduler vs BackgroundScheduler — pick what's compatible with FastAPI's async event loop)
- Exact SQL query for orphan detection (e.g., `WHERE status IN (...) AND created_at < NOW() - interval`)
- Whether to add a `GET /collections/{id}/pulse-runs` list endpoint (not required by success criteria)
- Error message wording for edge cases

</decisions>

<specifics>
## Specific Ideas

- The `required` credit value in the 402 response must be fetched from `workspace_credit_cost_pulse` platform setting — not hardcoded — so it stays accurate if admin changes the setting
- The 409 `active_run_id` allows the frontend to skip showing an error and instead resume the loading state for the existing run

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PulseService.run_detection()` (`backend/app/services/pulse.py`): complete credit deduction, conflict check, PulseRun creation, and background task launch — just call this from the endpoint
- `PulseService.get_pulse_run()` (`backend/app/services/pulse.py`): fetch PulseRun by ID — use for polling endpoint
- `PulseRunCreate`, `PulseRunResponse`, `PulseRunDetailResponse` (`backend/app/schemas/pulse.py`): existing schemas — add `PulseRunTriggerResponse` (lean) and update `PulseRunDetailResponse` to include signals list
- `WorkspaceUser` dependency (`backend/app/dependencies.py`): already used throughout collections.py — inject in pulse endpoints too
- `collections.py` router: add pulse endpoints directly to existing router (no new router file needed)

### Established Patterns
- `asyncio.create_task()` background pattern — already used in Phase 49
- `APIRouter` with `WorkspaceUser` + `DbSession` injection — established in collections.py
- `HTTPException` with status codes — consistent pattern across all routers
- FastAPI lifespan for startup/shutdown hooks — check `backend/app/main.py` for existing lifespan

### Integration Points
- `backend/app/routers/collections.py`: add `POST /{collection_id}/pulse` and `GET /{collection_id}/pulse-runs/{run_id}` endpoints
- `backend/app/main.py`: register APScheduler job in lifespan context manager
- `backend/app/schemas/pulse.py`: add `PulseRunTriggerResponse` schema; extend `PulseRunDetailResponse` with `signals` list field
- `backend/app/config.py`: add `PULSE_ORPHAN_TIMEOUT_MINUTES` env var (default: 10)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 50-pulse-endpoint-wire-up*
*Context gathered: 2026-03-07*
