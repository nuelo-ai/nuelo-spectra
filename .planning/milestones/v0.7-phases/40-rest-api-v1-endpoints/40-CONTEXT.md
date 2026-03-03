# Phase 40: REST API v1 Endpoints - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

External callers can programmatically manage files, retrieve file context, and run synchronous analysis queries — all authenticated by API key with credit deduction and usage logging. Endpoints are served under `/api/v1/`. MCP server wrapping these endpoints is a separate phase (Phase 41).

</domain>

<decisions>
## Implementation Decisions

### Response Shapes
- Mirror internal `ChatAgentResponse` structure with thin API envelope: `{ success, credits_used, data: {...} }`
- Analysis response `data` contains existing field names unchanged: `user_query`, `generated_code`, `execution_result`, `analysis`, `chart_specs`, `chart_error`, `follow_up_suggestions`, `search_sources`
- File list endpoint returns all files at once — no pagination (users won't have hundreds of files)
- Separate endpoints for lightweight file list vs heavy context: `GET /files` returns id/name/dates; `GET /files/{id}/context` returns data brief, summary, suggestions

### Query Flow Architecture
- **Stateless** — no session history, no LangGraph checkpoints. Each API call is self-contained
- Single endpoint: `POST /api/v1/chat/query` with file_ids in the request body
- Request body: `{ "query": "...", "file_ids": ["uuid-1", ...], "web_search_enabled": false }`
- Single file_id uses direct file context loading; multiple file_ids triggers `ContextAssembler`
- Max files per request = `max_files_per_session` from settings.yaml
- Max file size = existing `MAX_FILE_SIZE_MB` limit
- New code path that reuses the agent graph but bypasses session/checkpoint system
- Backend loads all context (data_summary, data_profile, user_context) from DB — API caller only sends query + file_ids

### Upload Flow
- Synchronous upload — waits for onboarding (data brief + suggestions) to complete before responding
- One file per upload request: `POST /api/v1/files/upload`
- Same validation as frontend: `.csv`, `.xlsx`, `.xls` only; 50MB max; pandas format validation

### Query Execution
- Synchronous only — no SSE streaming for API. Returns complete JSON when analysis finishes
- Configurable request timeout in settings.yaml, default 120 seconds

### Credit & Usage Billing
- Credits deducted **before** invoking the agent (same as frontend)
- Refund on failure — if analysis fails (agent error, timeout, retries exhausted), credit is refunded
- Same cost as frontend: 1 credit per query (per APISEC-03)
- Zero credits returns HTTP 402 Payment Required with clear message
- Per-request usage logging: timestamp, endpoint, method, API key ID, user ID, credits used, status code, response time

### Error Contract
- Simple JSON error format matching success envelope: `{ "success": false, "error": { "code": "INSUFFICIENT_CREDITS", "message": "..." } }`
- Machine-readable error codes for programmatic handling (e.g., `INSUFFICIENT_CREDITS`, `FILE_NOT_FOUND`, `INVALID_FILE_TYPE`, `ANALYSIS_FAILED`, `ANALYSIS_TIMEOUT`)
- Actionable error messages that include what went wrong AND what to do (e.g., "File not found. Verify the file_id exists and belongs to your account.")

### Claude's Discretion
- Per-request usage log schema and storage (DB table vs structured log file)
- Exact error code catalog (beyond the key ones listed above)
- Internal refund mechanism implementation
- How to handle agent graph invocation without checkpoints (thread_id strategy or None)

</decisions>

<specifics>
## Specific Ideas

- Query endpoint URL: `POST /api/v1/chat/query` — not nested under files, since it accepts file_ids in body
- File context split mirrors requirements: APIF-02 (list) is lightweight, APIC-01 (detail) is heavy — separate endpoints
- Phase 41 MCP tools should map cleanly to these endpoints (e.g., `spectra_run_analysis` wraps `/chat/query`, `spectra_list_files` wraps `/files`)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 40-rest-api-v1-endpoints*
*Context gathered: 2026-02-24*
