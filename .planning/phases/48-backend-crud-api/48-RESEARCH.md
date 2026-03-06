# Phase 48: Backend CRUD API - Research

**Researched:** 2026-03-06
**Domain:** FastAPI CRUD endpoints, tier-based access control, file upload integration
**Confidence:** HIGH

## Summary

Phase 48 builds a collections router with full CRUD endpoints, file upload/link to collection, report retrieval, and tier-based workspace access gating. The codebase has well-established patterns from existing routers (`files.py`, `credits.py`, `chat_sessions.py`) that provide a clear template: `APIRouter` with typed `CurrentUser`/`DbSession` dependencies, service layer with static methods, Pydantic schemas with `ConfigDict(from_attributes=True)`, and `asyncio.create_task()` for background processing.

All data models (Collection, CollectionFile, Report, Signal, PulseRun) already exist from Phase 47. The File model and FileService are fully operational. The primary work is: (1) a new `WorkspaceAccess` dependency that checks `user_classes.yaml` config, (2) a `CollectionService` with static methods for CRUD + count aggregations, (3) Pydantic schemas for request/response, (4) a single `collections.py` router file, and (5) router registration in `main.py`.

**Primary recommendation:** Follow the exact patterns from `backend/app/routers/files.py` and `backend/app/services/file.py` -- static service methods, typed dependencies, schema validation via `model_validate()`. The workspace access dependency should be a FastAPI `Depends()` function injected at router level.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Full lockout for users without workspace_access -- ALL /collections endpoints return 403, not just creation
- WorkspaceAccess dependency injected at router level (applies to every collection endpoint)
- max_active_collections checked only on POST /collections (create) -- users at limit can still use existing collections
- HTTP 403 for tier-based access denial ("workspace access not available on your plan")
- HTTP 402 reserved for credit-related blocks (Phase 49/50)
- Files are a shared pool -- one `files` table, one upload directory, files belong to a user
- Collections and Sessions both link to files via junction tables (collection_files, session_files) -- same file can appear in multiple collections AND multiple sessions
- POST /collections/{id}/files: upload new file via FileService.upload_file() + create CollectionFile link + trigger Onboarding Agent background task
- POST /collections/{id}/files/link: link an existing file (by file_id) to a collection -- creates CollectionFile row only, no re-upload
- FILE-02 column profile uses existing File.data_summary from Onboarding Agent -- no new profiling endpoint
- FILE-03 file selection for detection is frontend-only state -- selected file IDs sent in POST /collections/{id}/pulse body
- Reports are auto-generated internally by PulseService on detection completion -- no user-facing POST create endpoint in v0.8
- GET /collections/{id}/reports: list with metadata only (id, title, report_type, created_at, pulse_run_id) -- no markdown content in list
- GET /collections/{id}/reports/{reportId}: detail includes full markdown content + source info (pulse_run_id, signal count from that run)
- GET /collections/{id}/reports/{reportId}/download: raw markdown with Content-Disposition: attachment header
- REPORT-04 (PDF download disabled) is frontend-only -- no backend PDF endpoint in v0.8
- Single collections.py router file with all nested sub-routes (~200-300 lines)
- URL prefix: /collections (matches existing /files, /auth, /chat pattern)
- Collection detail response includes inline aggregated counts (file_count, signal_count, report_count) via SQL COUNT subqueries
- Collection list also includes counts per collection (file_count, signal_count)

### Claude's Discretion
- Pydantic schema field names and nesting
- SQL query optimization for count subqueries
- CollectionService class method signatures
- Error message wording for edge cases

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COLL-01 | User can create a new Collection (name-only) | POST /collections endpoint with name field, WorkspaceAccess + max_active_collections check |
| COLL-02 | User can view their Collections as grid cards (name, status, date, file_count, signal_count) | GET /collections with COUNT subqueries for file_count, signal_count |
| COLL-03 | User can view Collection detail with 4-tab layout | GET /collections/{id} with file_count, signal_count, report_count aggregations |
| COLL-04 | User can update Collection name/description | PATCH /collections/{id} with partial update schema |
| FILE-01 | User can upload CSV/Excel files to a Collection | POST /collections/{id}/files reusing FileService.upload_file() + CollectionFile link |
| FILE-02 | User can view column profile via DataSummaryPanel | Uses existing File.data_summary -- no new endpoint, file detail already has this |
| FILE-03 | User can select files for detection (frontend state) | No backend work -- file IDs sent in POST /collections/{id}/pulse (Phase 50) |
| FILE-04 | User can remove a file from a Collection | DELETE /collections/{id}/files/{file_id} -- deletes CollectionFile row only, not the file |
| REPORT-01 | User can view Reports tab listing reports | GET /collections/{id}/reports returning metadata list |
| REPORT-02 | User can open full-page report viewer | GET /collections/{id}/reports/{reportId} returning full markdown content |
| REPORT-03 | User can download report as Markdown | GET /collections/{id}/reports/{reportId}/download with Content-Disposition |
| REPORT-04 | PDF download button disabled | Frontend-only -- no backend endpoint needed |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115.0 | Web framework, router, dependency injection | Already in use project-wide |
| SQLAlchemy | >=2.0.0 (async) | ORM, queries, relationships | Already in use, async with asyncpg |
| Pydantic | v2 (via FastAPI) | Request/response schemas | Already in use, `ConfigDict(from_attributes=True)` pattern |
| asyncpg | >=0.29.0 | PostgreSQL async driver | Already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiofiles | >=25.0.0 | Async file writes for upload | Already used in FileService |
| pandas | >=2.0.0 | CSV/Excel validation on upload | Already used in FileService |
| PyYAML | >=6.0.0 | Load user_classes.yaml config | Already used in UserClassService |

### Alternatives Considered
None -- this phase uses exclusively existing project libraries. No new dependencies needed.

**Installation:**
No new packages required. All dependencies already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── routers/
│   └── collections.py          # NEW: all collection CRUD + nested file/report routes
├── services/
│   └── collection.py           # NEW: CollectionService static methods
├── schemas/
│   └── collection.py           # NEW: Pydantic schemas for collections, files-in-collection, reports
├── models/
│   ├── collection.py           # EXISTS: Collection, CollectionFile models
│   ├── report.py               # EXISTS: Report model
│   └── signal.py               # EXISTS: Signal model
├── dependencies.py             # MODIFY: add WorkspaceAccess dependency
└── main.py                     # MODIFY: register collections router
```

### Pattern 1: Router with Typed Dependencies
**What:** Every endpoint uses `CurrentUser` and `DbSession` typed dependencies for auth and DB access
**When to use:** All endpoints in the collections router
**Example:**
```python
# Source: backend/app/routers/files.py (existing pattern)
from app.dependencies import CurrentUser, DbSession

@router.get("", response_model=list[CollectionListItem])
async def list_collections(
    current_user: CurrentUser,
    db: DbSession
) -> list[CollectionListItem]:
    collections = await CollectionService.list_user_collections(db, current_user.id)
    return [CollectionListItem.model_validate(c) for c in collections]
```

### Pattern 2: WorkspaceAccess Router-Level Dependency
**What:** A FastAPI dependency that checks `workspace_access` from `user_classes.yaml` for the current user's tier, raising 403 if false. Applied at router level so ALL endpoints are gated.
**When to use:** The collections router definition
**Example:**
```python
# New dependency in dependencies.py
from app.services.user_class import get_class_config

async def require_workspace_access(current_user: CurrentUser) -> User:
    """Verify user's tier has workspace_access=True. Raises 403 if not."""
    config = get_class_config(current_user.user_class)
    if not config or not config.get("workspace_access", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="workspace access not available on your plan"
        )
    return current_user

# Use at router level:
WorkspaceUser = Annotated[User, Depends(require_workspace_access)]

# In collections.py, use WorkspaceUser instead of CurrentUser
@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(
    body: CollectionCreate,
    current_user: WorkspaceUser,  # <-- ensures workspace access
    db: DbSession
) -> CollectionResponse: ...
```

### Pattern 3: Service Layer with Static Methods
**What:** All business logic in service classes with `@staticmethod` async methods
**When to use:** All database operations
**Example:**
```python
# Source: backend/app/services/file.py (existing pattern)
class CollectionService:
    @staticmethod
    async def create_collection(
        db: AsyncSession, user_id: UUID, name: str, description: str | None = None
    ) -> Collection:
        collection = Collection(user_id=user_id, name=name, description=description)
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection
```

### Pattern 4: COUNT Subqueries for Aggregated Responses
**What:** Use SQLAlchemy `func.count()` with correlated subqueries for file_count, signal_count, report_count in list/detail responses
**When to use:** Collection list and detail endpoints
**Example:**
```python
from sqlalchemy import func, select

# Subquery approach for counts
file_count_sq = (
    select(func.count(CollectionFile.id))
    .where(CollectionFile.collection_id == Collection.id)
    .correlate(Collection)
    .scalar_subquery()
    .label("file_count")
)

signal_count_sq = (
    select(func.count(Signal.id))
    .where(Signal.collection_id == Collection.id)
    .correlate(Collection)
    .scalar_subquery()
    .label("signal_count")
)

stmt = (
    select(Collection, file_count_sq, signal_count_sq)
    .where(Collection.user_id == user_id)
    .order_by(Collection.created_at.desc())
)
```

### Pattern 5: Background Task for Onboarding Agent
**What:** After file upload to collection, trigger onboarding in background using `asyncio.create_task()`
**When to use:** POST /collections/{id}/files (upload endpoint)
**Example:**
```python
# Source: backend/app/routers/files.py lines 79-88 (existing pattern)
async def _run_onboarding_background(file_id: UUID, user_id: UUID, context: str):
    async with async_session_maker() as background_db:
        try:
            await agent_service.run_onboarding(background_db, file_id, user_id, context)
        except Exception as e:
            print(f"Background onboarding failed for file {file_id}: {e}")

asyncio.create_task(_run_onboarding_background(file_record.id, current_user.id, user_context))
```

### Pattern 6: Markdown Download Response
**What:** Return markdown content as a downloadable file with Content-Disposition header
**When to use:** GET /collections/{id}/reports/{reportId}/download
**Example:**
```python
from fastapi.responses import Response

@router.get("/{collection_id}/reports/{report_id}/download")
async def download_report(
    collection_id: UUID,
    report_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession
) -> Response:
    report = await CollectionService.get_report(db, report_id, collection_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    filename = f"{report.title.replace(' ', '_')}.md"
    return Response(
        content=report.content or "",
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

### Anti-Patterns to Avoid
- **Eager-loading relationships for counts:** Do NOT use `selectinload(Collection.collection_files)` just to get `len()` -- use COUNT subqueries instead. Loading all related rows is an N+1 problem.
- **Separate ownership check queries:** Do NOT query collection then separately verify user_id -- combine in a single WHERE clause (`Collection.user_id == user_id`).
- **Deleting the File on collection file removal:** DELETE /collections/{id}/files/{file_id} removes the CollectionFile junction row, NOT the File itself. Files are shared pool resources.
- **Using `model_config = ConfigDict(from_attributes=True)` with aggregated columns:** When query returns `(Collection, file_count, signal_count)` tuples, you cannot use `model_validate()` directly -- manually construct the response schema from the row tuple.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File upload + validation | Custom upload handler | `FileService.upload_file()` | Handles chunked writes, size limits, pandas validation, disk cleanup on error |
| AI data profiling | Custom profiling logic | `agent_service.run_onboarding()` | Existing background task populates File.data_summary |
| Tier config loading | Direct YAML parsing | `UserClassService.get_class_config()` | Has 30s TTL cache, tested |
| Auth + user extraction | Manual JWT parsing | `CurrentUser` typed dependency | Handles JWT verification, user lookup, active check |
| Database sessions | Manual session management | `DbSession` typed dependency | Auto-cleanup via `get_db()` generator |

**Key insight:** Nearly all infrastructure for this phase already exists. The only new code is the collections service/router/schemas and the WorkspaceAccess dependency. Everything else is composition of existing components.

## Common Pitfalls

### Pitfall 1: MissingGreenlet Error on Lazy-Loaded Relationships
**What goes wrong:** Accessing `collection.collection_files` or `collection.reports` outside async context raises `MissingGreenlet`
**Why it happens:** SQLAlchemy async requires explicit eager loading or separate queries for relationships
**How to avoid:** Use `selectinload()` when you need relationship data, or use separate COUNT subqueries (preferred for counts). The project already sets `expire_on_commit=False` in `database.py` which helps but doesn't prevent lazy load attempts.
**Warning signs:** `sqlalchemy.exc.MissingGreenlet` or `greenlet_spawn has not been called`

### Pitfall 2: Forgetting User Isolation on Nested Resources
**What goes wrong:** `/collections/{id}/files/{file_id}` endpoint checks collection ownership but not that the file link belongs to that collection
**Why it happens:** Multi-level nesting makes it easy to skip a WHERE clause
**How to avoid:** Always filter by both `collection_id` and verify the collection belongs to `current_user.id`. For file operations, verify `CollectionFile.collection_id == collection_id` AND the parent collection's `user_id == current_user.id`.
**Warning signs:** Users accessing other users' files through collection endpoints

### Pitfall 3: max_active_collections Check Race Condition
**What goes wrong:** Two concurrent POST /collections requests both pass the count check and exceed the limit
**Why it happens:** Read-then-write without a lock
**How to avoid:** Use `SELECT COUNT(*) ... FOR UPDATE` on the collections table, or use a UNIQUE constraint approach. For v0.8 with low concurrency, the simple count check is acceptable -- document as known limitation.
**Warning signs:** Users with more collections than their tier allows

### Pitfall 4: File Upload to Non-Owned Collection
**What goes wrong:** User uploads a file to someone else's collection if only file_id is checked
**Why it happens:** Endpoint validates file ownership but not collection ownership
**How to avoid:** First verify collection belongs to current_user, then proceed with file upload/link
**Warning signs:** Cross-user data exposure

### Pitfall 5: Report Signal Count from Wrong Source
**What goes wrong:** Report detail shows incorrect signal count
**Why it happens:** Counting all collection signals instead of signals from the specific pulse_run that generated the report
**How to avoid:** Count signals WHERE `pulse_run_id == report.pulse_run_id`, not where `collection_id == report.collection_id`
**Warning signs:** Signal count doesn't match what the detection run actually found

## Code Examples

### Collection Create with Tier Check
```python
# CollectionService.create_collection
@staticmethod
async def create_collection(
    db: AsyncSession, user_id: UUID, name: str, description: str | None = None
) -> Collection:
    collection = Collection(user_id=user_id, name=name, description=description)
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection

# Router endpoint with max_active_collections check
@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionResponse:
    # Check collection limit
    config = get_class_config(current_user.user_class)
    max_collections = config.get("max_active_collections", 0)
    if max_collections != -1:  # -1 = unlimited
        count = await CollectionService.count_user_collections(db, current_user.id)
        if count >= max_collections:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Collection limit reached ({max_collections} active collections)"
            )
    collection = await CollectionService.create_collection(db, current_user.id, body.name, body.description)
    return CollectionResponse.model_validate(collection)
```

### Collection List with Count Subqueries
```python
# CollectionService.list_user_collections
@staticmethod
async def list_user_collections(db: AsyncSession, user_id: UUID) -> list[dict]:
    file_count = (
        select(func.count(CollectionFile.id))
        .where(CollectionFile.collection_id == Collection.id)
        .correlate(Collection)
        .scalar_subquery()
    )
    signal_count = (
        select(func.count(Signal.id))
        .where(Signal.collection_id == Collection.id)
        .correlate(Collection)
        .scalar_subquery()
    )
    stmt = (
        select(
            Collection,
            file_count.label("file_count"),
            signal_count.label("signal_count"),
        )
        .where(Collection.user_id == user_id)
        .order_by(Collection.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "collection": row[0],
            "file_count": row[1],
            "signal_count": row[2],
        }
        for row in rows
    ]
```

### File Link to Collection (No Re-upload)
```python
@router.post("/{collection_id}/files/link", status_code=status.HTTP_201_CREATED)
async def link_file_to_collection(
    collection_id: UUID,
    body: FileLinkRequest,  # { file_id: UUID }
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionFileResponse:
    # Verify collection ownership
    collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    # Verify file ownership
    file = await FileService.get_user_file(db, body.file_id, current_user.id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    # Check for duplicate link
    existing = await CollectionService.get_collection_file(db, collection_id, body.file_id)
    if existing:
        raise HTTPException(status_code=409, detail="File already in collection")
    # Create link
    link = await CollectionService.add_file_to_collection(db, collection_id, body.file_id)
    return CollectionFileResponse.model_validate(link)
```

### Pydantic Schema Examples
```python
from pydantic import BaseModel, ConfigDict, Field

class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None

class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

class CollectionListItem(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    file_count: int
    signal_count: int
    model_config = ConfigDict(from_attributes=True)

class CollectionDetailResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    file_count: int
    signal_count: int
    report_count: int
    model_config = ConfigDict(from_attributes=True)

class ReportListItem(BaseModel):
    id: UUID
    title: str
    report_type: str
    created_at: datetime
    pulse_run_id: UUID | None
    model_config = ConfigDict(from_attributes=True)

class ReportDetailResponse(BaseModel):
    id: UUID
    title: str
    report_type: str
    content: str | None
    created_at: datetime
    pulse_run_id: UUID | None
    signal_count: int  # count of signals from same pulse_run
    model_config = ConfigDict(from_attributes=True)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `class Config` | Pydantic v2 `model_config = ConfigDict(...)` | Pydantic v2 (2023) | Project already uses v2 throughout |
| `Session.query()` (sync) | `select()` + `await db.execute()` (async) | SQLAlchemy 2.0 | Project already uses async patterns |
| Function-based deps | `Annotated[User, Depends()]` typed deps | FastAPI 0.95+ | Project already uses `CurrentUser`, `DbSession` |

**Deprecated/outdated:**
- None relevant -- project is on current FastAPI/SQLAlchemy/Pydantic stack

## Open Questions

1. **CollectionListItem `from_attributes` with tuple rows**
   - What we know: COUNT subqueries return `(Collection, int, int)` tuples, not plain model instances
   - What's unclear: Whether to use `from_attributes=True` or manual dict construction
   - Recommendation: Return dicts from service, construct schema manually in router. This is what the codebase does for complex queries.

2. **Report signal_count source**
   - What we know: Report has `pulse_run_id`, signals have `pulse_run_id`
   - What's unclear: If `pulse_run_id` is None (SET NULL after PulseRun deletion), signal_count should be 0
   - Recommendation: Use `COALESCE(COUNT(...), 0)` and handle None pulse_run_id gracefully

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0.0 + pytest-asyncio >=0.23.0 |
| Config file | backend/pyproject.toml (dependencies only, no [tool.pytest] section) |
| Quick run command | `cd backend && python -m pytest tests/test_collections.py -x` |
| Full suite command | `cd backend && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COLL-01 | Create collection with name, 403 for free tier | unit | `cd backend && python -m pytest tests/test_collections.py::test_create_collection -x` | No -- Wave 0 |
| COLL-02 | List collections with file_count, signal_count | unit | `cd backend && python -m pytest tests/test_collections.py::test_list_collections -x` | No -- Wave 0 |
| COLL-03 | Collection detail with all counts | unit | `cd backend && python -m pytest tests/test_collections.py::test_collection_detail -x` | No -- Wave 0 |
| COLL-04 | Update collection name/description | unit | `cd backend && python -m pytest tests/test_collections.py::test_update_collection -x` | No -- Wave 0 |
| FILE-01 | Upload file to collection | unit | `cd backend && python -m pytest tests/test_collections.py::test_upload_file_to_collection -x` | No -- Wave 0 |
| FILE-02 | Column profile via data_summary | manual-only | Existing File.data_summary -- no new endpoint; verify via FILE-01 response | N/A |
| FILE-03 | File selection for detection | manual-only | Frontend-only state -- no backend test needed | N/A |
| FILE-04 | Remove file from collection | unit | `cd backend && python -m pytest tests/test_collections.py::test_remove_file_from_collection -x` | No -- Wave 0 |
| REPORT-01 | List reports for collection | unit | `cd backend && python -m pytest tests/test_collections.py::test_list_reports -x` | No -- Wave 0 |
| REPORT-02 | Report detail with markdown | unit | `cd backend && python -m pytest tests/test_collections.py::test_report_detail -x` | No -- Wave 0 |
| REPORT-03 | Download report as markdown | unit | `cd backend && python -m pytest tests/test_collections.py::test_download_report -x` | No -- Wave 0 |
| REPORT-04 | PDF download disabled | manual-only | Frontend-only -- no backend endpoint | N/A |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_collections.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_collections.py` -- covers COLL-01 through COLL-04, FILE-01, FILE-04, REPORT-01 through REPORT-03
- [ ] Test for WorkspaceAccess dependency (403 for free tier users)
- [ ] Test for max_active_collections limit enforcement
- [ ] Test for file link (POST /collections/{id}/files/link) duplicate prevention

Note: Tests will be unit tests with mocked DB (matching existing test patterns in `test_user_classes_workspace.py` and `test_routing.py`). No integration test fixtures exist for full HTTP testing -- tests should focus on service logic and dependency behavior.

## Sources

### Primary (HIGH confidence)
- `backend/app/routers/files.py` -- complete reference router implementation pattern
- `backend/app/services/file.py` -- service layer pattern with static methods
- `backend/app/dependencies.py` -- typed dependency injection pattern (CurrentUser, DbSession)
- `backend/app/models/collection.py` -- Collection, CollectionFile models (from Phase 47)
- `backend/app/models/report.py` -- Report model with pulse_run_id FK
- `backend/app/models/signal.py` -- Signal model for count subqueries
- `backend/app/config/user_classes.yaml` -- tier config with workspace_access, max_active_collections
- `backend/app/services/user_class.py` -- UserClassService with get_class_config()
- `backend/app/schemas/file.py` -- Pydantic v2 schema patterns
- `backend/app/main.py` (lines 388-397) -- router registration in public/dev modes
- `backend/app/database.py` -- async_session_maker for background tasks

### Secondary (MEDIUM confidence)
- FastAPI dependency injection docs -- router-level dependencies via `dependencies=[Depends()]` parameter on APIRouter

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- exact patterns exist in codebase (files.py, file.py service)
- Pitfalls: HIGH -- based on direct code inspection of models and relationships
- Validation: MEDIUM -- no existing HTTP-level test fixtures; unit test patterns exist

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable -- no external dependency changes expected)
