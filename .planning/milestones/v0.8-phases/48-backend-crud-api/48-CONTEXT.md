# Phase 48: Backend CRUD API - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Collections router with all CRUD endpoints, WorkspaceAccess tier enforcement dependency, file upload/link to collection, Report list/detail/download endpoints, Pydantic schemas. No frontend, no Pulse Agent, no detection execution.

</domain>

<decisions>
## Implementation Decisions

### Workspace access gating
- Full lockout for users without workspace_access — ALL /collections endpoints return 403, not just creation
- WorkspaceAccess dependency injected at router level (applies to every collection endpoint)
- max_active_collections checked only on POST /collections (create) — users at limit can still use existing collections
- HTTP 403 for tier-based access denial ("workspace access not available on your plan")
- HTTP 402 reserved for credit-related blocks (Phase 49/50)

### File upload to collection
- Files are a shared pool — one `files` table, one upload directory, files belong to a user
- Collections and Sessions both *link* to files via junction tables (collection_files, session_files) — same file can appear in multiple collections AND multiple sessions
- POST /collections/{id}/files: upload new file via FileService.upload_file() + create CollectionFile link + trigger Onboarding Agent background task (same as /files/upload)
- POST /collections/{id}/files/link: link an existing file (by file_id) to a collection — creates CollectionFile row only, no re-upload
- FILE-02 column profile uses existing File.data_summary from Onboarding Agent — no new profiling endpoint
- FILE-03 file selection for detection is frontend-only state — selected file IDs sent in POST /collections/{id}/pulse body

### Report endpoints
- Reports are auto-generated internally by PulseService on detection completion — no user-facing POST create endpoint in v0.8
- GET /collections/{id}/reports: list with metadata only (id, title, report_type, created_at, pulse_run_id) — no markdown content in list
- GET /collections/{id}/reports/{reportId}: detail includes full markdown content + source info (pulse_run_id, signal count from that run)
- GET /collections/{id}/reports/{reportId}/download: raw markdown with Content-Disposition: attachment header
- REPORT-04 (PDF download disabled) is frontend-only — no backend PDF endpoint in v0.8

### Router structure
- Single collections.py router file with all nested sub-routes (~200-300 lines)
- URL prefix: /collections (matches existing /files, /auth, /chat pattern)
- Collection detail response includes inline aggregated counts (file_count, signal_count, report_count) via SQL COUNT subqueries
- Collection list also includes counts per collection (file_count, signal_count) — matches mockup's collection cards

### Claude's Discretion
- Pydantic schema field names and nesting
- SQL query optimization for count subqueries
- CollectionService class method signatures
- Error message wording for edge cases

</decisions>

<specifics>
## Specific Ideas

- Files uploaded via collection must go through the existing Onboarding Agent process to ensure data_summary (data brief) is available for the DataSummaryPanel (FILE-02)
- The shared file pool concept is critical — files are not "owned" by collections or sessions, they are linked. Upload via any entry point (My Files, chat session, collection) makes the file available everywhere
- Report source line should show context like "Generated from Pulse detection - 5 signals found" in the detail response

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FileService.upload_file()` (`backend/app/services/file.py`): handles disk write, pandas validation, File row creation — reuse for collection file upload
- `agent_service.run_onboarding()`: background task for AI data profiling — trigger after collection file upload
- `CreditService.deduct_credit()` (`backend/app/services/credit.py`): SELECT FOR UPDATE atomic deduction — used by Phase 49/50
- `CurrentUser` / `DbSession` typed dependencies (`backend/app/dependencies.py`): inject in all endpoints
- Pydantic schemas with `ConfigDict(from_attributes=True)` pattern (`backend/app/schemas/`)

### Established Patterns
- Router: `APIRouter(prefix="/resource", tags=["Resource"])` with typed dependency injection
- Service layer: static methods on service class (e.g., `FileService.list_user_files()`)
- Schemas: separate response models for list items vs detail views
- UUID primary keys, `DateTime(timezone=True)` timestamps
- Background tasks via `asyncio.create_task()` for non-blocking operations

### Integration Points
- `backend/app/routers/__init__.py` or main app: register new collections router
- `backend/app/models/collection.py`: Collection, CollectionFile models (created in Phase 47)
- `backend/app/models/report.py`: Report model (created in Phase 47)
- `backend/app/services/user_class.py` + `user_classes.yaml`: workspace_access and max_active_collections config
- `backend/app/services/platform_settings.py`: workspace_credit_cost_pulse key (for Phase 49/50, not this phase)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 48-backend-crud-api*
*Context gathered: 2026-03-06*
