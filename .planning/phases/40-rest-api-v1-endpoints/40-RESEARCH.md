# Phase 40: REST API v1 Endpoints - Research

**Researched:** 2026-02-24
**Domain:** FastAPI REST endpoint implementation, credit billing, usage logging
**Confidence:** HIGH

## Summary

Phase 40 implements the external-facing REST API v1 endpoints under the existing `api_v1_router` in `backend/app/routers/api_v1/`. The infrastructure is already in place from Phases 38-39: the `APIRouter` with `/v1` prefix, dual-mounting at `/v1/*` and `/api/v1/*`, `ApiAuthUser` dependency for unified JWT/API-key auth, `SPECTRA_MODE=api` CORS config, and the Dokploy deployment setup. This phase adds the actual business endpoints (files, context, chat/query) plus credit deduction and per-request usage logging.

The existing codebase provides all the reusable building blocks: `FileService` for CRUD operations, `agent_service.run_onboarding()` and `agent_service.run_chat_query()` for AI pipeline execution, `CreditService.deduct_credit()` for atomic billing, and `ContextAssembler` for multi-file queries. The primary new work is: (1) thin API router modules that wrap these services with the `ApiAuthUser` dependency and API envelope response format, (2) a new `api_usage_logs` table for per-request structured logging, (3) a credit refund mechanism for failed analyses, and (4) a stateless query path that bypasses LangGraph checkpointing.

**Primary recommendation:** Build new router modules under `backend/app/routers/api_v1/` (files.py, context.py, query.py) that delegate to existing services, wrapping responses in the `{ success, credits_used, data }` envelope. Add an `ApiUsageLog` model and a FastAPI middleware or dependency for per-request logging. The query endpoint needs a modified `run_chat_query` path that passes `checkpointer=None` (or a throwaway thread_id) to avoid polluting session memory.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Mirror internal `ChatAgentResponse` structure with thin API envelope: `{ success, credits_used, data: {...} }`
- Analysis response `data` contains existing field names unchanged: `user_query`, `generated_code`, `execution_result`, `analysis`, `chart_specs`, `chart_error`, `follow_up_suggestions`, `search_sources`
- File list endpoint returns all files at once -- no pagination (users won't have hundreds of files)
- Separate endpoints for lightweight file list vs heavy context: `GET /files` returns id/name/dates; `GET /files/{id}/context` returns data brief, summary, suggestions
- **Stateless** -- no session history, no LangGraph checkpoints. Each API call is self-contained
- Single endpoint: `POST /api/v1/chat/query` with file_ids in the request body
- Request body: `{ "query": "...", "file_ids": ["uuid-1", ...], "web_search_enabled": false }`
- Single file_id uses direct file context loading; multiple file_ids triggers `ContextAssembler`
- Max files per request = `max_files_per_session` from settings.yaml (currently 5)
- Max file size = existing `MAX_FILE_SIZE_MB` limit (currently 50MB)
- New code path that reuses the agent graph but bypasses session/checkpoint system
- Backend loads all context (data_summary, data_profile, user_context) from DB -- API caller only sends query + file_ids
- Synchronous upload -- waits for onboarding (data brief + suggestions) to complete before responding
- One file per upload request: `POST /api/v1/files/upload`
- Same validation as frontend: `.csv`, `.xlsx`, `.xls` only; 50MB max; pandas format validation
- Synchronous only -- no SSE streaming for API. Returns complete JSON when analysis finishes
- Configurable request timeout in settings.yaml, default 120 seconds
- Credits deducted **before** invoking the agent (same as frontend)
- Refund on failure -- if analysis fails (agent error, timeout, retries exhausted), credit is refunded
- Same cost as frontend: 1 credit per query (per APISEC-03)
- Zero credits returns HTTP 402 Payment Required with clear message
- Per-request usage logging: timestamp, endpoint, method, API key ID, user ID, credits used, status code, response time
- Simple JSON error format matching success envelope: `{ "success": false, "error": { "code": "INSUFFICIENT_CREDITS", "message": "..." } }`
- Machine-readable error codes for programmatic handling
- Actionable error messages that include what went wrong AND what to do

### Claude's Discretion
- Per-request usage log schema and storage (DB table vs structured log file)
- Exact error code catalog (beyond the key ones listed above)
- Internal refund mechanism implementation
- How to handle agent graph invocation without checkpoints (thread_id strategy or None)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APIF-01 | API caller can upload CSV/Excel, triggering onboarding (data brief + suggestions) | Reuse `FileService.upload_file()` + `agent_service.run_onboarding()` synchronously (await instead of `asyncio.create_task`) |
| APIF-02 | API caller can list all files for authenticated user | Reuse `FileService.list_user_files()` with `ApiAuthUser` dependency |
| APIF-03 | API caller can delete a file by ID | Reuse `FileService.delete_file()` with `ApiAuthUser` dependency |
| APIF-04 | API caller can download a file by ID | Reuse `FileService.get_user_file()` + `FileResponse` pattern from existing `files.py` |
| APIC-01 | API caller can get file detail including data brief, summary, context | Reuse `FileService.get_user_file()`, return `data_summary`, `user_context`, `query_suggestions` |
| APIC-02 | API caller can update file data summary or context | Reuse `agent_service.update_user_context()` or direct DB update |
| APIC-03 | API caller can get query suggestions for a file | Return `file.query_suggestions` from existing DB column |
| APIQ-01 | API caller can send query and receive full analysis result synchronously | Reuse `agent_service.run_chat_query()` with `checkpointer=None` bypass, wrap in envelope |
| APISEC-03 | API calls deduct credits (same cost as chat) | Reuse `_deduct_credits_or_raise()` pattern from `chat.py`, add refund-on-failure |
| APISEC-04 | API usage logged per user and per API key | New `api_usage_logs` DB table + FastAPI middleware/dependency for per-request logging |
| APIINFRA-04 | API requests and errors are logged (structured, per-request) | Combine DB usage log with Python structured logging (existing `logging` pattern) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | API framework | Already used throughout the project |
| SQLAlchemy 2.0 | existing | ORM + async DB | Already used for all models and services |
| Pydantic v2 | existing | Request/response schemas | Already used for all schemas |
| Alembic | existing | DB migrations | Already used for all schema changes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiofiles | existing | Async file I/O | File upload streaming (already in deps) |
| pandas | existing | File validation | CSV/Excel validation on upload (already in deps) |

### Alternatives Considered
No new libraries needed. This phase builds entirely on the existing stack. The API endpoints are thin wrappers around existing services.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/routers/api_v1/
├── __init__.py         # api_v1_router (exists, add new router includes)
├── api_keys.py         # Existing - API key CRUD (Phase 38)
├── health.py           # Existing - Health check (Phase 39)
├── files.py            # NEW - File upload, list, delete, download
├── context.py          # NEW - File context, suggestions, update
├── query.py            # NEW - Chat/query endpoint
└── schemas.py          # NEW - API v1 envelope schemas

backend/app/models/
├── api_usage_log.py    # NEW - Usage log model

backend/app/services/
├── api_usage.py        # NEW - Usage logging service
```

### Pattern 1: API Envelope Response
**What:** Wrap all API v1 responses in a standard envelope for consistency.
**When to use:** Every API v1 endpoint response.
**Example:**
```python
# backend/app/routers/api_v1/schemas.py
from pydantic import BaseModel
from typing import Any

class ApiResponse(BaseModel):
    """Standard API v1 response envelope."""
    success: bool = True
    credits_used: float | None = None
    data: Any = None

class ApiErrorDetail(BaseModel):
    code: str
    message: str

class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ApiErrorDetail
```

### Pattern 2: Stateless Agent Invocation (No Checkpoint)
**What:** Invoke the LangGraph agent graph without persisting conversation history.
**When to use:** `POST /api/v1/chat/query` -- each API call is self-contained.
**Key insight:** The existing `run_chat_query()` accepts an optional `checkpointer` parameter. Passing `checkpointer=None` to `get_or_create_graph()` creates a graph with no checkpoint persistence. However, the function also calls `graph.aupdate_state()` with a thread_id, which will fail without a checkpointer. The solution is to create a new function `run_api_query()` that:
1. Accepts file_ids instead of session_id/file_id
2. Loads file context the same way
3. Invokes `graph.ainvoke()` with `checkpointer=None` (in-memory only)
4. Skips chat message saving (no session to save to)
5. Returns the same result dict
```python
# Approach: Use graph.ainvoke() directly without aupdate_state or chat saving
from app.agents.graph import compile_graph  # Need a function that compiles without checkpointer

async def run_api_query(
    db: AsyncSession,
    file_ids: list[UUID],
    user_id: UUID,
    user_query: str,
    web_search_enabled: bool = False,
) -> dict:
    """Stateless agent invocation for API endpoint."""
    # Compile a fresh graph with no checkpointer
    graph = compile_graph(checkpointer=None)

    # Build initial_state with HumanMessage in messages list
    # (no aupdate_state needed -- messages go in initial_state directly)
    from langchain_core.messages import HumanMessage
    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        # ... same fields as run_chat_query ...
    }

    # Use a random thread_id (required by LangGraph but not persisted)
    import uuid
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = await graph.ainvoke(initial_state, config)
    # NO chat message saving, NO checkpoint persistence
    return {
        "user_query": user_query,
        "generated_code": result.get("generated_code"),
        "execution_result": result.get("execution_result"),
        "analysis": result.get("final_response") or result.get("analysis", ""),
        "chart_specs": result.get("chart_specs", ""),
        "chart_error": result.get("chart_error", ""),
        "follow_up_suggestions": result.get("follow_up_suggestions", []),
        "search_sources": result.get("search_sources", []),
    }
```

### Pattern 3: Synchronous Upload (Await Onboarding)
**What:** Unlike the frontend which fires onboarding as a background task, the API waits for onboarding to complete.
**When to use:** `POST /api/v1/files/upload`
**Example:**
```python
# Instead of asyncio.create_task(_run_onboarding_background(...))
# Directly await:
data_summary = await agent_service.run_onboarding(db, file_record.id, user.id, "")
# Then return file record with populated data_summary and query_suggestions
```

### Pattern 4: Credit Deduction with Refund on Failure
**What:** Deduct credits before agent execution, refund if analysis fails.
**When to use:** `POST /api/v1/chat/query`
**Example:**
```python
# Step 1: Deduct credit
deduction = await CreditService.deduct_credit(db, user_id, credit_cost)
if not deduction.success:
    raise HTTPException(status_code=402, ...)
await db.commit()

# Step 2: Run analysis
try:
    result = await run_api_query(db, file_ids, user_id, query, web_search_enabled)
except Exception:
    # Step 3: Refund on failure
    await CreditService.admin_adjust(db, user_id, credit_cost, "API query refund", user_id)
    # Or: create a dedicated refund method that's simpler
    await db.commit()
    raise

# Return result wrapped in envelope with credits_used
```

### Pattern 5: Per-Request Usage Logging via Dependency
**What:** Log every API v1 request with timing, credits, status.
**When to use:** All API v1 endpoints.
**Approach options:**

**Option A: Middleware** -- intercepts all requests, measures timing, logs after response. Pros: automatic, no per-endpoint code. Cons: harder to get credits_used per-request (need to thread it through).

**Option B: Explicit dependency + post-endpoint call** -- each endpoint calls a log function. Pros: precise control, easy access to credits_used. Cons: boilerplate per endpoint.

**Recommendation: Middleware for request/response logging + explicit credit tracking in query endpoint.** The middleware captures timing, status code, endpoint, method, and API key ID. The query endpoint adds `credits_used` to the log record after execution.

### Anti-Patterns to Avoid
- **Reusing session-based thread_ids for API:** Would pollute frontend users' conversation history. API must use isolated or no checkpoints.
- **Background onboarding for API upload:** Unlike frontend, API callers expect the response to contain the data brief. Synchronous is mandatory.
- **Swallowing errors silently:** API callers need machine-readable error codes to handle failures programmatically. Never return generic 500.
- **Committing credit deduction inside the service transaction:** Credit deduction must commit independently before agent execution (same pattern as `_deduct_credits_or_raise`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File upload validation | Custom parser | Existing `FileService.upload_file()` + `_validate_file()` | Already handles size limits, pandas validation, cleanup |
| Agent pipeline | New agent chain | Existing `agent_service.run_chat_query()` pattern | 6-agent graph with retry, error handling, all validated |
| Credit deduction | Manual balance math | Existing `CreditService.deduct_credit()` | SELECT FOR UPDATE atomic deduction, unlimited user support |
| Multi-file context | Manual file loading | Existing `ContextAssembler.assemble()` | Token budget management, join hint detection |
| Auth dependency | New auth logic | Existing `ApiAuthUser` (`get_authenticated_user`) | JWT + API key dual auth, already tested |

**Key insight:** Phase 40 is primarily a wiring phase. Almost all business logic exists. The new code is thin router modules, an envelope schema, a usage log model, and a stateless variant of the query function.

## Common Pitfalls

### Pitfall 1: Checkpointer Leakage in Stateless API Queries
**What goes wrong:** Using the app-level checkpointer for API queries creates orphaned checkpoint entries in PostgreSQL, and if the API caller reuses the same file, LangGraph loads stale conversation context.
**Why it happens:** `run_chat_query()` uses `app.state.checkpointer` and builds a thread_id from file/session IDs.
**How to avoid:** Create a new `run_api_query()` function that compiles the graph with `checkpointer=None`. LangGraph supports `None` checkpointer -- it runs the graph without persistence.
**Warning signs:** API responses containing context from previous queries; growing checkpoint table size.

### Pitfall 2: Synchronous Upload Timeout
**What goes wrong:** Onboarding Agent can take 10-30 seconds for large files. With synchronous upload, the HTTP request may timeout.
**Why it happens:** `run_onboarding()` calls the LLM for data brief generation, which has variable latency.
**How to avoid:** Set the API request timeout to 120s (per user decision). Document that large file uploads may take up to 60s. Consider adding a timeout wrapper around `run_onboarding()`.
**Warning signs:** 504 Gateway Timeout on uploads; uvicorn request timeout errors.

### Pitfall 3: Credit Refund Race Condition
**What goes wrong:** If the refund uses `CreditService.admin_adjust()`, it requires an admin_id parameter. The refund is a system action, not an admin action.
**Why it happens:** The existing refund-like method is designed for admin operations.
**How to avoid:** Create a lightweight `CreditService.refund()` method that uses `transaction_type="api_refund"` and doesn't require admin_id. Use the same SELECT FOR UPDATE pattern.
**Warning signs:** Refund transactions showing NULL admin_id with "admin_adjustment" type.

### Pitfall 4: ApiKeyService.authenticate() Doesn't Return API Key ID
**What goes wrong:** Usage logging needs the `api_key_id` to track per-key usage (APISEC-04), but `authenticate()` only returns the `User` object.
**Why it happens:** Phase 38 designed `authenticate()` for auth-only; it discards the ApiKey after getting the user.
**How to avoid:** Modify `get_authenticated_user()` to also store the api_key_id on the request state, or modify `authenticate()` to return both user and api_key record. Recommended: attach `api_key_id` to `request.state` in the dependency, or return a tuple.
**Warning signs:** Usage log entries with NULL api_key_id.

### Pitfall 5: DB Session Lifetime During Long Query Execution
**What goes wrong:** The FastAPI-injected `db` session may timeout during a 30-120s analysis query.
**Why it happens:** Database connection pool has a max idle time; the session sits idle during LLM processing.
**How to avoid:** Use the same pattern as `run_chat_query_stream()` -- use the injected session for initial validation/credit deduction, then use `async_session_maker()` for any post-execution DB operations (refund, logging).
**Warning signs:** "connection already closed" errors after long queries.

### Pitfall 6: Missing File Ownership Check on Multi-File Queries
**What goes wrong:** API caller sends file_ids belonging to another user. Without ownership check, they get unauthorized data access.
**Why it happens:** `ContextAssembler.assemble()` takes user_id for ownership checks, but individual file_ids must all belong to the caller.
**How to avoid:** Verify all file_ids belong to the authenticated user before passing to ContextAssembler. `FileService.get_user_file()` does per-file ownership checks.
**Warning signs:** API returning data from files the caller didn't upload.

### Pitfall 7: Envelope Response vs FileResponse Mismatch
**What goes wrong:** The download endpoint returns `FileResponse` (binary stream), not a JSON envelope. Wrapping it in `ApiResponse` would corrupt the file data.
**Why it happens:** Not all endpoints fit the JSON envelope pattern.
**How to avoid:** The download endpoint is the exception -- it returns `FileResponse` directly, not wrapped in the envelope. Document this clearly.
**Warning signs:** Corrupted file downloads; content-type mismatches.

## Code Examples

### API v1 Router Registration
```python
# backend/app/routers/api_v1/__init__.py (updated)
from fastapi import APIRouter
from app.routers.api_v1 import api_keys, health, files, context, query

api_v1_router = APIRouter(prefix="/v1", tags=["API v1"])
api_v1_router.include_router(api_keys.router)
api_v1_router.include_router(health.router)
api_v1_router.include_router(files.router)
api_v1_router.include_router(context.router)
api_v1_router.include_router(query.router)
```

### File Upload Endpoint (Synchronous)
```python
# backend/app/routers/api_v1/files.py
@router.post("/upload", status_code=201)
async def api_upload_file(
    file: UploadFile,
    user: ApiAuthUser,
    db: DbSession,
):
    """Upload CSV/Excel and wait for onboarding to complete."""
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        return ApiErrorResponse(...)

    # Upload file
    file_record = await FileService.upload_file(db, user.id, file, ext)

    # Synchronous onboarding (unlike frontend's asyncio.create_task)
    await agent_service.run_onboarding(db, file_record.id, user.id, "")

    # Refresh to get populated data_summary and suggestions
    await db.refresh(file_record)

    return ApiResponse(
        success=True,
        data={
            "id": str(file_record.id),
            "filename": file_record.original_filename,
            "data_brief": file_record.data_summary,
            "query_suggestions": file_record.query_suggestions,
        }
    )
```

### Query Endpoint with Credit Deduction + Refund
```python
# backend/app/routers/api_v1/query.py
@router.post("/chat/query")
async def api_query(
    body: ApiQueryRequest,
    user: ApiAuthUser,
    db: DbSession,
    request: Request,
):
    """Run analysis query against file(s), deduct credits, return result."""
    # Deduct credit
    cost = Decimal(str(await platform_settings.get(db, "default_credit_cost")))
    deduction = await CreditService.deduct_credit(db, user.id, cost)
    if not deduction.success:
        return JSONResponse(status_code=402, content=ApiErrorResponse(
            error=ApiErrorDetail(code="INSUFFICIENT_CREDITS", message=deduction.error_message)
        ).model_dump())
    await db.commit()

    # Run stateless query
    try:
        result = await run_api_query(db, body.file_ids, user.id, body.query, body.web_search_enabled)
    except Exception as e:
        # Refund credit on failure
        await CreditService.refund(db, user.id, cost)
        await db.commit()
        return JSONResponse(status_code=500, content=ApiErrorResponse(
            error=ApiErrorDetail(code="ANALYSIS_FAILED", message=str(e))
        ).model_dump())

    return ApiResponse(success=True, credits_used=float(cost), data=result)
```

### Usage Log Model
```python
# backend/app/models/api_usage_log.py
class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    api_key_id: Mapped[UUID | None] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int] = mapped_column()
    credits_used: Mapped[float] = mapped_column(Float, default=0.0)
    response_time_ms: Mapped[int] = mapped_column()
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
```

### Error Code Catalog
```python
# Recommended error codes
ERROR_CODES = {
    "INSUFFICIENT_CREDITS": "Not enough credits to perform this operation.",
    "FILE_NOT_FOUND": "File not found. Verify the file_id exists and belongs to your account.",
    "INVALID_FILE_TYPE": "Unsupported file type. Allowed: .csv, .xlsx, .xls",
    "FILE_TOO_LARGE": f"File exceeds maximum size of {MAX_MB}MB.",
    "FILE_VALIDATION_FAILED": "File could not be parsed. Ensure it is a valid CSV or Excel file.",
    "ONBOARDING_FAILED": "Data analysis failed during file processing. Please try uploading again.",
    "ANALYSIS_FAILED": "Analysis query failed. Credit has been refunded.",
    "ANALYSIS_TIMEOUT": "Analysis exceeded the maximum execution time. Credit has been refunded.",
    "FILE_NOT_ONBOARDED": "File has not been analyzed yet. Please wait or re-upload.",
    "TOO_MANY_FILES": "Too many files in request. Maximum is {max}.",
    "INVALID_REQUEST": "Request body is invalid. Check the documentation.",
    "UNAUTHORIZED": "Invalid or missing API key.",
    "FORBIDDEN": "Access denied.",
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate API gateway | Same codebase, mode-based routing | Phase 38 (SPECTRA_MODE=api) | No code duplication, shared services |
| API key in query params | Bearer token header | Phase 38 | Industry standard, more secure |
| Streaming API responses | Synchronous JSON (v0.7 decision) | Phase 40 context | Simpler for API consumers; SSE deferred |

**Deprecated/outdated:**
- None relevant. All existing patterns are current.

## Open Questions

1. **API Key ID in Authentication Flow**
   - What we know: `get_authenticated_user()` returns only `User`, not the `ApiKey` record. Usage logging needs `api_key_id`.
   - What's unclear: Best way to thread the api_key_id from auth to usage logging without breaking existing signatures.
   - Recommendation: Modify `get_authenticated_user()` to store `api_key_id` on `request.state` (requires injecting `Request` into the dependency), or create a separate dependency `get_api_key_context()` that returns both user and key info. The simpler path is to modify `ApiKeyService.authenticate()` to return `(user, api_key)` tuple and update callers.

2. **Graph Compilation Without Checkpointer**
   - What we know: `get_or_create_graph(checkpointer)` is cached with `lru_cache` based on the checkpointer identity. Passing `None` works for compilation but the function uses `graph.aupdate_state()` before `ainvoke()`.
   - What's unclear: Whether `graph.ainvoke()` works correctly with `checkpointer=None` and messages in `initial_state`.
   - Recommendation: Create a dedicated `compile_api_graph()` function or bypass `get_or_create_graph()` caching for the None case. Include `messages: [HumanMessage(content=query)]` directly in `initial_state` instead of using `aupdate_state()`. LangGraph supports this pattern -- the `add_messages` reducer handles initial messages.

3. **total_credits_used on ApiKey**
   - What we know: The `api_keys` table already has `total_credits_used` column (added in Phase 38 with comment "populated by Phase 40").
   - What's unclear: Whether to update it per-request (atomic increment) or compute it from `api_usage_logs` on demand.
   - Recommendation: Atomic increment per-request is simpler and faster for display. Update `total_credits_used` in the same transaction as usage log insertion.

## Sources

### Primary (HIGH confidence)
- Project codebase: `backend/app/routers/api_v1/__init__.py` -- existing router structure
- Project codebase: `backend/app/dependencies.py` -- `ApiAuthUser` dependency, `get_authenticated_user()`
- Project codebase: `backend/app/services/agent_service.py` -- `run_chat_query()`, `run_onboarding()`
- Project codebase: `backend/app/services/credit.py` -- `CreditService.deduct_credit()`
- Project codebase: `backend/app/routers/chat.py` -- `_deduct_credits_or_raise()` pattern
- Project codebase: `backend/app/routers/files.py` -- existing file CRUD endpoints
- Project codebase: `backend/app/models/api_key.py` -- `total_credits_used` column ready for Phase 40
- Project codebase: `backend/app/config.py` -- Settings model, SPECTRA_MODE validation
- Phase 40 CONTEXT.md -- all locked decisions

### Secondary (MEDIUM confidence)
- LangGraph documentation -- `checkpointer=None` invocation pattern (verified via training data, standard LangGraph pattern)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- extends existing proven patterns (router, service, dependency injection)
- Pitfalls: HIGH -- identified from direct codebase analysis of existing implementations
- Stateless query path: MEDIUM -- LangGraph `checkpointer=None` pattern needs validation at implementation time

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable -- no external dependency changes)
