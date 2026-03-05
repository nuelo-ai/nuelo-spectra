# Architecture Research: v0.8 Spectra Pulse (Detection)

**Domain:** Adding Pulse Analysis module to an existing FastAPI + LangGraph + Next.js platform
**Researched:** 2026-03-05
**Confidence:** HIGH (direct codebase inspection — models, agents, routers, frontend routes, services all read)

---

## Standard Architecture

### System Overview — v0.8 Integration Layer

```
┌──────────────────────────────────────────────────────────────────────┐
│                    NEXT.JS FRONTEND (frontend/src/)                   │
├──────────────────────────────────────────────────────────────────────┤
│  (auth)/ routes    │  (dashboard)/ routes          │  Workspace routes │
│  login, register   │  sessions/[id], my-files,     │  /workspace       │
│  invite, reset     │  settings, dashboard           │  /workspace/      │
│                    │                               │  collections/[id] │
│                    │  ChatSidebar (modified: add    │  /[id]/signals    │
│                    │  "Pulse Analysis" nav entry)  │  (NEW v0.8)       │
├──────────────────────────────────────────────────────────────────────┤
│  Zustand: sessionStore, tabStore (unchanged)                          │
│  TanStack Query: existing hooks + NEW useCollections, useCollection  │
│  New components: frontend/src/components/workspace/ (migrated)       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP (route handler proxies, unchanged pattern)
┌────────────────────────────▼─────────────────────────────────────────┐
│                    FASTAPI BACKEND (backend/app/)                      │
├──────────────────────────────────────────────────────────────────────┤
│  Routers: auth, chat, chat_sessions, files, health, search, version  │
│           admin/*, api_v1/*, mcp (all UNCHANGED)                     │
│           + NEW: /collections router (v0.8)                          │
├──────────────────────────────────────────────────────────────────────┤
│  Services: auth, file, credit, chat_session, platform_settings, ...  │
│            (all UNCHANGED)                                           │
│            + NEW: collection_service, pulse_service (v0.8)          │
├──────────────────────────────────────────────────────────────────────┤
│  Agents (LangGraph):                                                  │
│    Chat pipeline (graph.py): manager, coding, code_checker,          │
│    data_analysis, visualization, onboarding — ALL UNCHANGED           │
│    + NEW: pulse/graph.py — independent Pulse pipeline (v0.8)        │
│    + NEW: pulse/agent.py — PulseAgent node                           │
│    + NEW: pulse/analyzers.py — E2B statistical analysis scripts      │
├──────────────────────────────────────────────────────────────────────┤
│  E2B Sandbox: UNCHANGED — reused by Pulse Agent as-is               │
│  Credit system: CreditService.deduct_credit() UNCHANGED              │
│                 + NEW platform_settings key: workspace_credit_cost_pulse │
├──────────────────────────────────────────────────────────────────────┤
│  SQLAlchemy Models (PostgreSQL):                                      │
│  Existing: User, File, ChatSession, ChatMessage, UserCredit,         │
│            CreditTransaction, PlatformSetting, ApiKey, ... UNCHANGED │
│  NEW (v0.8): Collection, CollectionFile, Signal                      │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ AsyncSession (SQLAlchemy 2.0 — unchanged)
┌────────────────────────────▼─────────────────────────────────────────┐
│                         PostgreSQL                                     │
│  Existing tables: users, files, chat_sessions, chat_messages,        │
│    user_credits, credit_transactions, platform_settings, api_keys,   │
│    admin_audit_log, ... (ALL UNCHANGED)                              │
│  NEW tables (v0.8): collections, collection_files, signals           │
│  Local filesystem: uploads/{user_id}/ (existing, UNCHANGED)          │
│  NEW: uploads/collections/{collection_id}/ (new path prefix)        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Question 1: Where Do New Models Go in the Existing SQLAlchemy Structure?

### Answer: Three New Model Files, Same Pattern as All Existing Models

Every model in `backend/app/models/` is its own file, extends `Base` from `app.models.base`, uses SQLAlchemy 2.0 `Mapped` / `mapped_column` syntax, UUID primary keys with `uuid4`, and timezone-aware datetimes. The new models follow this exactly.

**New files to create:**

```
backend/app/models/
├── collection.py          # Collection — workspace container owned by a user
├── collection_file.py     # CollectionFile — data files attached to a Collection
└── signal.py              # Signal — individual Pulse finding within a Collection
```

**`collection.py` shape:**

```python
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="collections")
    files: Mapped[list["CollectionFile"]] = relationship(
        "CollectionFile", back_populates="collection", cascade="all, delete-orphan"
    )
    signals: Mapped[list["Signal"]] = relationship(
        "Signal", back_populates="collection", cascade="all, delete-orphan"
    )
```

**`collection_file.py` shape:**

```python
class CollectionFile(Base):
    __tablename__ = "collection_files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))  # UUID-based on disk
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))   # csv | xlsx | xls
    column_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # populated at Pulse run
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)

    collection: Mapped["Collection"] = relationship("Collection", back_populates="files")
```

**`signal.py` shape:**

```python
class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20))   # critical | warning | info
    category: Mapped[str] = mapped_column(String(50))   # anomaly | trend | concentration | quality
    visualization: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # Recharts config
    statistical_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)

    collection: Mapped["Collection"] = relationship("Collection", back_populates="signals")
```

**Registration:** The existing `backend/app/models/__init__.py` may need these imports added. Alembic auto-detects new models only when they are imported before `Base.metadata` is accessed. Check whether the existing `__init__.py` imports models explicitly or relies on the models being imported via `main.py` imports.

**Migration pattern:** For completely new tables there is no backfill step needed. Use the standard `alembic revision --autogenerate` → inspect → `alembic upgrade head` flow.

---

## Question 2: How Should the Pulse Agent Be Structured?

### Answer: Independent LangGraph Graph, Separate From the Chat Pipeline

The existing chat pipeline in `backend/app/agents/graph.py` is a stateful LangGraph workflow with PostgreSQL checkpointing, built around `ChatAgentState` and designed for streaming LLM output. The Pulse Agent's requirements are fundamentally different:

- **Input:** list of CollectionFile paths + metadata (not a user query)
- **Output:** list of structured Signal dicts (not a conversational response)
- **No conversation memory:** each Pulse run is stateless — no PostgreSQL checkpointing needed
- **No SSE streaming:** Pulse is a request-response job, not a streaming response
- **Multiple E2B passes:** runs 4+ distinct statistical analysis passes, not one code execution

**Recommended structure:**

```
backend/app/agents/
├── graph.py              # Existing chat pipeline — DO NOT MODIFY
├── state.py              # Add PulseAgentState here alongside existing TypedDicts
├── coding.py             # UNCHANGED
├── manager.py            # UNCHANGED
├── data_analysis.py      # UNCHANGED
├── visualization.py      # UNCHANGED
├── onboarding.py         # UNCHANGED
├── code_checker.py       # UNCHANGED
└── pulse/
    ├── __init__.py
    ├── agent.py          # generate_signals_node — LLM call to structure raw results into Signals
    ├── graph.py          # pulse_graph: StateGraph assembling the Pulse pipeline
    └── analyzers.py      # E2B-executable Python scripts for each analysis type
```

**`PulseAgentState` TypedDict (add to `state.py`):**

```python
class PulseAgentState(TypedDict):
    collection_id: str
    user_id: str
    file_records: list[dict]        # [{id, path, filename, file_type, column_profile}]
    profiled_data: dict             # column stats from profiling pass
    analysis_results: list[dict]    # raw output dicts from each E2B analysis method
    signals: list[dict]             # structured Signal objects (title, severity, etc.)
    error: str
```

**The Pulse LangGraph graph — linear pipeline, no routing:**

```
profile_data_node
    ↓
run_analyses_node   (runs anomaly, trend, concentration, quality checks in E2B)
    ↓
generate_signals_node   (LLM call: structure raw analysis output into Signal objects)
    ↓
END
```

**Reuse existing infrastructure — no new components needed:**
- `E2BSandboxRuntime` from `app.services.sandbox` — import and use exactly as `graph.py` does
- `get_llm()` from `app.agents.llm_factory` — same factory; add `pulse_agent` to `prompts.yaml`
- `get_agent_prompt()` from `app.agents.config` — same YAML config; add `pulse_agent` entry

**Add to `prompts.yaml`:**

```yaml
agents:
  pulse_agent:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.1
    max_tokens: 4096
    system: |
      You are a statistical analysis agent. Given raw analysis results from
      data profiling and statistical tests, structure them into Signal objects
      with clear titles, severity levels, and evidence summaries.
```

**`pulse_service.py` as the glue layer:**

```python
# backend/app/services/pulse.py
from app.agents.pulse.graph import pulse_graph
from app.models.signal import Signal

async def run_pulse_detection(
    collection_id: UUID, user_id: UUID, db: AsyncSession
) -> list[Signal]:
    # 1. Load CollectionFile records from DB
    file_records = await load_collection_files(db, collection_id)

    # 2. Run the Pulse graph
    result = await pulse_graph.ainvoke({
        "collection_id": str(collection_id),
        "user_id": str(user_id),
        "file_records": file_records,
        "analysis_results": [],
        "signals": [],
        "error": "",
    })

    # 3. Persist signals to DB
    signal_objects = []
    for sig_data in result["signals"]:
        signal = Signal(collection_id=collection_id, **sig_data)
        db.add(signal)
        signal_objects.append(signal)
    await db.commit()

    return signal_objects
```

---

## Question 3: How Should the /collections Router Integrate?

### Answer: New Top-Level Router File, Registered in main.py Alongside Existing Routers

Every existing router follows the same pattern: a module in `backend/app/routers/`, `router = APIRouter(prefix="/...", tags=["..."])`, `CurrentUser` and `DbSession` dependencies, registered in `main.py`.

**New file:** `backend/app/routers/collections.py`

**Registration in `main.py`:**

```python
# In main.py imports — additive:
from app.routers import auth, chat, chat_sessions, files, health, search, version, collections

# In router registration block:
app.include_router(collections.router)
```

**Endpoint list for v0.8:**

```python
router = APIRouter(prefix="/collections", tags=["Collections"])

@router.post("", status_code=201)               # Create collection
@router.get("")                                  # List user's collections
@router.get("/{id}")                             # Get collection detail with signals
@router.patch("/{id}")                           # Update name/description
@router.delete("/{id}")                          # Delete collection
@router.post("/{id}/files", status_code=201)     # Upload file to collection
@router.delete("/{id}/files/{file_id}")          # Remove file from collection
@router.post("/{id}/pulse")                      # Trigger Pulse detection
@router.get("/{id}/signals")                     # List signals for collection
```

**Auth pattern — same as all existing routers:**

```python
from app.dependencies import CurrentUser, DbSession

@router.post("")
async def create_collection(
    body: CreateCollectionRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CollectionResponse:
    ...
```

**Pulse trigger endpoint design:** `POST /collections/{id}/pulse` must:
1. Verify collection belongs to `current_user`
2. Check workspace access for user's tier via new `workspace_access` field in `user_classes.yaml`
3. Check `max_active_collections` limit (count only `active` status collections)
4. Get `workspace_credit_cost_pulse` from `platform_settings` (new key, default `"5.0"`)
5. Call `CreditService.deduct_credit(db, user_id, cost)` — same atomic pattern as chat router
6. Call `pulse_service.run_pulse_detection(collection_id, user_id, db)` — synchronous
7. Return signals list on success; refund credits on failure via compensating transaction

**Synchronous vs. async for Pulse:** Run synchronously on first implementation. The frontend `DetectionLoading` component animates locally and does not need real-time progress events. FastAPI's default 60-second request timeout is sufficient for a 5-15 second Pulse run. Background tasks can be added in a later milestone if execution time grows.

**Tier access — use a FastAPI dependency to avoid copy-paste:**

```python
# backend/app/dependencies.py (additive)
async def require_workspace_access(
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    from app.services.user_class import get_class_config
    config = get_class_config(current_user.user_class)
    if not config.get("workspace_access", False):
        raise HTTPException(status_code=403, detail="Workspace access requires a higher plan.")

WorkspaceAccess = Annotated[None, Depends(require_workspace_access)]
```

Use `WorkspaceAccess` as a dependency on `POST /collections` and `POST /collections/{id}/pulse`.

---

## Question 4: Frontend Migration from pulse-mockup

### Answer: New Route Group Under (dashboard), Components in src/components/workspace/

**Current frontend route structure:**

```
frontend/src/app/
├── (auth)/                     # login, register, invite, reset-password
├── (dashboard)/                # protected routes with ChatSidebar layout
│   ├── layout.tsx              # ChatSidebar + LinkedFilesPanel — MODIFIED (add nav entry)
│   ├── dashboard/page.tsx
│   ├── my-files/page.tsx
│   ├── sessions/[sessionId]/page.tsx
│   ├── sessions/new/page.tsx
│   └── settings/page.tsx
└── api/                        # Next.js route handler proxies
```

**v0.8 additions — new routes under (dashboard):**

```
frontend/src/app/(dashboard)/
└── workspace/                                         # NEW — Pulse Analysis module
    ├── page.tsx                                       # Collections list (/workspace)
    └── collections/
        └── [id]/
            ├── page.tsx                               # Collection 4-tab detail
            └── signals/
                └── page.tsx                           # Detection Results
```

All three new pages live inside the existing `(dashboard)` route group. They inherit the `(dashboard)/layout.tsx` — which means they get the existing `SidebarProvider` + `ChatSidebar` wrapper automatically. The `LinkedFilesPanel` (right sidebar) renders only when `currentSessionId` is set in Zustand; workspace pages do not set a session ID, so the right panel will not appear on workspace routes.

**New component directory:**

```
frontend/src/components/workspace/          # NEW directory — migrated from pulse-mockup
├── collection-card.tsx
├── collection-list.tsx
├── create-collection-dialog.tsx
├── data-summary-panel.tsx
├── detection-loading.tsx
├── empty-state.tsx
├── file-table.tsx
├── file-upload-zone.tsx
├── overview-stat-cards.tsx
├── run-detection-banner.tsx
├── signal-card.tsx
├── signal-chart.tsx                        # uses Recharts (verify recharts in package.json)
├── signal-detail-panel.tsx
├── signal-list-panel.tsx
├── sticky-action-bar.tsx
└── activity-feed.tsx
```

**Mockup components deferred — do NOT migrate in v0.8:**
- `add-to-collection-modal.tsx` — v0.9 (Chat-to-Collection bridge)
- `investigation-qa-thread.tsx` — v0.10
- `investigation-checkpoint.tsx` — v0.10
- `whatif-refinement-chat.tsx` — v0.11

**What changes when migrating each component:**
1. Import paths — mockup uses relative (`../lib/utils`); main frontend uses `@/` aliases
2. Mock data arrays — replace with data from TanStack Query hooks
3. `setTimeout` loading stubs — replace with `isLoading` / `isPending` from hook responses
4. Static credit labels (`"5 credits"`) — wire to live `workspace_credit_cost_pulse` fetched from backend
5. `router.push()` calls — verify routes match the new `(dashboard)/workspace/` structure

**New TanStack Query hooks:**

```
frontend/src/hooks/
├── useCollections.ts     # list collections, create, delete
├── useCollection.ts      # single collection detail (tabs data, signals)
└── usePulse.ts           # trigger detection run, handle loading state
```

**New API route handlers (proxy to backend):**

```
frontend/src/app/api/collections/
├── route.ts                          # GET, POST /collections
└── [id]/
    ├── route.ts                      # GET, PATCH, DELETE /collections/[id]
    ├── files/
    │   ├── route.ts                  # POST /collections/[id]/files
    │   └── [fileId]/route.ts         # DELETE /collections/[id]/files/[fileId]
    ├── pulse/route.ts                # POST /collections/[id]/pulse
    └── signals/route.ts              # GET /collections/[id]/signals
```

**Sidebar modification:** `frontend/src/components/sidebar/ChatSidebar.tsx` needs one new navigation entry added — label "Pulse Analysis", route `/workspace`. This is the only required change to existing shared components. The credit balance pill in `UserSection.tsx` may need a Zap icon added to match the mockup's header pill — verify visually against the mockup.

**State management:** No new Zustand store needed for v0.8. TanStack Query cache handles Collection and Signal data. The selected Signal ID on the Detection Results page is local UI state — `useState` in the parent page component is sufficient.

**Recharts dependency:** The existing `frontend/package.json` must have Recharts installed. The pulse-mockup uses it for `SignalChart`. Verify with `cat frontend/package.json | grep recharts` before migrating `signal-chart.tsx`.

---

## Question 5: Collection Files vs. Existing FileContext — Are They the Same?

### Answer: They Are Separate Systems — Do Not Conflate Them

This is the most architecturally significant decision in v0.8. The two file systems serve different purposes and must remain separate.

| Dimension | Existing `files` table (user files) | New `collection_files` table |
|-----------|--------------------------------------|------------------------------|
| Ownership | `user_id` FK — belongs to user's library | `collection_id` FK — belongs to a workspace |
| Purpose | Files for Chat sessions and ad-hoc analysis | Data sources for Pulse statistical analysis |
| Profiling | `data_summary` (LLM-generated text), `query_suggestions` | `column_profile` (structured JSON), `row_count` |
| Profiling timing | Onboarding Agent runs immediately on upload | Pulse Agent populates column_profile at detection time |
| Storage path | `backend/uploads/{user_id}/` | `backend/uploads/collections/{collection_id}/` |
| Lifecycle | Independent; linked to ChatSessions via M2M join | CASCADE deleted when Collection is deleted |
| Agent use | Coding Agent + DataAnalysis Agent (chat pipeline) | Pulse Agent only |

**They are physically separate files on disk.** A user cannot link their existing Chat files into a Collection in v0.8. The Chat-to-Collection bridge is v0.9 scope, and that bridge imports chat result cards, not raw files.

**Design rationale:** Keeping them separate maintains clean ownership boundaries. The `File` model's schema is optimized for the Onboarding Agent output (human-readable summary, LLM query suggestions). The `CollectionFile` schema is optimized for the Pulse Agent (structured column types and distributions). Merging them would require adding nullable columns to the `files` table that are irrelevant for Chat files, and vice versa.

---

## Question 6: Build Order That Minimizes Risk

### Answer: Data Models First, Backend CRUD Second, Agent Third, Frontend Fourth

Each layer depends on the previous. The critical path runs through data models → backend CRUD → API endpoints → frontend.

```
Phase 1 — Data Foundation (blocks everything)
  1a. SQLAlchemy models: Collection, CollectionFile, Signal
  1b. Alembic migration: create the three new tables
  1c. user_classes.yaml: add workspace_access (bool) + max_active_collections (int)
  1d. platform_settings.py DEFAULTS: add workspace_credit_cost_pulse = "5.0"
      (also add to VALID_KEYS set)

Phase 2 — Backend CRUD API (enables frontend development)
  2a. Pydantic schemas: Collection, CollectionFile, Signal (request + response shapes)
  2b. CollectionService: create, list, get_by_id, update, delete CRUD
  2c. Collection file upload: write to disk at uploads/collections/{id}/ + DB record
  2d. /collections router: CRUD endpoints with CurrentUser + DbSession dependencies
  2e. WorkspaceAccess dependency: tier check + collection limit check
  MILESTONE: At this point the frontend can list, create, and upload files.
             Validate with Postman or curl before starting agent work.

Phase 3 — Pulse Agent (can run in parallel with Phase 2 after Phase 1)
  3a. PulseAgentState TypedDict added to backend/app/agents/state.py
  3b. pulse/analyzers.py: Python scripts for anomaly, trend, concentration, quality checks
  3c. pulse/agent.py: generate_signals_node — LLM call to structure results into Signals
  3d. pulse/graph.py: assemble the three-node pipeline
  3e. pulse_service.py: load files from DB, call graph, persist signals, credit refund on failure
  MILESTONE: Validate Pulse Agent produces real Signal objects from a test CSV file
             before wiring it to the API. This is the core value proposition — test it first.

Phase 4 — Wire Pulse Endpoint
  4a. POST /collections/{id}/pulse endpoint: credit pre-check → deduct → call pulse_service
  4b. Compensating credit transaction on failure
  4c. Return signals list in response

Phase 5 — Frontend Migration
  5a. Next.js API route handlers for /api/collections/*
  5b. TanStack Query hooks: useCollections, useCollection, usePulse
  5c. /workspace page: CollectionList + CreateCollectionDialog
  5d. /workspace/collections/[id] page: 4-tab layout
      - Tab 2 (Files) first: FileUploadZone + FileTable + DataSummaryPanel (needs Phase 2 only)
      - Tab 1 (Overview): stat cards + RunDetectionBanner (needs Phase 2 only)
      - Tab 3 (Signals): signal cards + DetectionLoading flow (needs Phase 4)
      - Tab 4 (Reports): empty state stub (v0.9 scope)
  5e. /workspace/collections/[id]/signals page: SignalListPanel + SignalDetailPanel
  5f. ChatSidebar: add "Pulse Analysis" nav entry (one line change)

Phase 6 — Admin and Tier Gating
  6a. Tier access enforcement: WorkspaceAccess dependency tested end-to-end
  6b. Collection limit enforcement: max_active_collections check
  6c. Confirm workspace_credit_cost_pulse is editable via existing Admin Settings page
      (if the admin frontend Settings page already renders unknown platform_settings keys
      dynamically, this may require zero new admin UI work)
```

**Critical path:** 1a → 1b → 2b → 2d → 4a → 5a → 5c

**Risk checkpoint:** Complete Phase 3 fully and validate Signal generation from a real CSV before building Phase 5 signal display UI. The quality of Pulse Agent output is the entire value proposition of v0.8. Discovering a prompt engineering problem after the frontend is built wastes effort.

---

## Component Responsibilities

| Component | Responsibility | Integration Point |
|-----------|---------------|-------------------|
| `Collection` model | Workspace container; owns status, user, timestamps | FK to users.id |
| `CollectionFile` model | Workspace data file; owns column_profile, row_count | FK to collections.id |
| `Signal` model | Pulse finding; owns severity, category, visualization JSON, evidence JSON | FK to collections.id |
| `CollectionService` | CRUD for Collections and CollectionFiles; tier/limit enforcement | Calls CreditService, PlatformSettingsService |
| `PulseService` | Orchestrates Pulse run; deducts credits, invokes graph, persists signals, refunds on failure | Calls pulse_graph.ainvoke(), CreditService |
| `pulse/graph.py` | LangGraph pipeline: profile → analyze → generate signals | Calls E2BSandboxRuntime, get_llm() |
| `pulse/analyzers.py` | Python scripts for anomaly/trend/concentration/quality checks in E2B | Called from pulse graph nodes |
| `/collections` router | FastAPI router; auth guard on all endpoints | Uses CurrentUser, DbSession, WorkspaceAccess |
| `WorkspaceAccess` dependency | Tier check + collection limit enforcement | Reads user_classes.yaml, counts active collections |
| `useCollections` hook | TanStack Query: list + create + delete | Calls /api/collections route handler |
| `useCollection` hook | TanStack Query: single collection detail with signals | Calls /api/collections/[id] |
| `usePulse` hook | Trigger Pulse run; manage loading state | Calls /api/collections/[id]/pulse |
| `/workspace` page | Collections list view | Renders CollectionList + CreateCollectionDialog |
| `/workspace/collections/[id]` | 4-tab collection detail | Renders Overview, Files, Signals, Reports tabs |
| `/workspace/collections/[id]/signals` | Detection Results | Renders SignalListPanel + SignalDetailPanel |
| `DetectionLoading` | Full-page loading state during Pulse run | Triggered by StickyActionBar "Run Detection" |
| `SignalChart` | Recharts chart driven by signal.visualization JSON | Inside SignalDetailPanel |

---

## Architectural Patterns

### Pattern 1: Independent LangGraph Graphs Per Workflow Type

**What:** Each distinct AI workflow (chat analysis vs. Pulse detection) has its own LangGraph `StateGraph` with its own `TypedDict` state, its own nodes, and its own invocation path. They share infrastructure (E2B sandbox, LLM factory, agent config YAML) but not state or graph structure.

**When to use:** Always when the input/output contract or execution pattern differs from the existing chat graph. Pulse and Chat are fundamentally different: Pulse is batch/stateless, Chat is conversational/stateful.

**Do not:** Extend `ChatAgentState` with Pulse fields. Do not add Pulse nodes to `graph.py`. This creates coupling that makes both pipelines harder to reason about and modify independently.

### Pattern 2: Service Layer Between Router and Agent

**What:** All router endpoints delegate immediately to a service function. Routers own HTTP concerns only (request parsing, response shaping, error codes). Services own business logic (credit checks, DB operations, file I/O, agent invocation).

**When to use:** Every endpoint — this is the existing pattern without exception across all routers.

**For v0.8:** `collections.py` router calls `CollectionService` and `PulseService`. The router never directly queries the DB, calls agent functions, or performs file I/O.

### Pattern 3: Credit Deduct-Before-Execute with Compensating Refund

**What:** Credits are deducted atomically before any expensive operation begins. If the operation fails, a compensating credit transaction is issued to restore the balance. This ensures no credits are lost on user-visible errors.

**Existing implementation:** `CreditService.deduct_credit()` uses `SELECT FOR UPDATE` on `user_credits`. Follow this exactly — do not write a new credit deduction path.

**New platform_settings additions:** Add to `DEFAULTS` dict and `VALID_KEYS` set in `platform_settings.py`:
- `"workspace_credit_cost_pulse": json.dumps("5.0")`

### Pattern 4: Migrate Mockup Components — Replace Data, Not Structure

**What:** Components from `pulse-mockup/src/components/workspace/` are copied into `frontend/src/components/workspace/`. Only mock data, `setTimeout` stubs, and import paths change. Component tree, prop names, and interaction patterns are preserved.

**When to use:** All v0.8 UI work. The mockup is the UI contract. Any deviation from its component structure requires explicit owner approval (per working rules).

**What changes during migration:**
- Import paths (`../lib/utils` → `@/lib/utils`)
- Mock data arrays → TanStack Query hook data
- `setTimeout` → `isLoading` / `isPending` from hooks
- Static credit labels → live `workspace_credit_cost_pulse` from backend settings endpoint
- Hardcoded route strings → verify against actual `(dashboard)/workspace/` route structure

---

## Data Flow

### Pulse Detection Flow

```
User checks files in FileTable + clicks "Run Detection" in StickyActionBar
    ↓
Frontend: POST /api/collections/{id}/pulse (Next.js route handler proxy)
    ↓
Backend /collections/{id}/pulse endpoint
    ↓ WorkspaceAccess dependency check (tier + collection limit)
    ↓
CreditService.deduct_credit(user_id, 5.0)  — SELECT FOR UPDATE, atomic
    ↓
PulseService.run_pulse_detection(collection_id, user_id, db)
    ↓ Load CollectionFile records from DB (paths, file_type)
    ↓
pulse_graph.ainvoke(PulseAgentState)
    ↓
  [profile_data_node] — E2B sandbox: load CSVs, compute column distributions
    ↓
  [run_analyses_node] — E2B sandbox: anomaly detection, trend analysis,
                        concentration analysis, data quality checks
    ↓
  [generate_signals_node] — LLM call (pulse_agent from prompts.yaml):
                            structure raw analysis output into Signal dicts
    ↓
PulseService: INSERT Signal rows into DB
    ↓
Return signal list to router
    ↓
Router: HTTP 200 with signals JSON
    ↓
Frontend usePulse hook: resolve → navigate to /workspace/collections/{id}/signals
    ↓
useCollection hook fetches signals → SignalListPanel renders, auto-selects first critical signal
```

### Collection File Upload Flow

```
User drops file on FileUploadZone in Files tab
    ↓
Frontend: POST /api/collections/{id}/files (multipart)
    ↓
Backend /collections/{id}/files endpoint
    ↓
Write file to backend/uploads/collections/{collection_id}/{uuid}.{ext}
    ↓
CollectionService: INSERT CollectionFile (filename, file_type, file_path)
    Note: column_profile is NULL at this point — populated by Pulse Agent at detection
    ↓
Return CollectionFile metadata → FileTable re-renders with new row
```

**Key distinction from existing file upload:** `POST /files/upload` triggers the Onboarding Agent immediately after upload (background task). Collection file upload does NOT run any agent — column profiling happens inside the Pulse Agent when detection runs. This means `DataSummaryPanel` will show empty/loading state until at least one Pulse run has completed.

---

## Integration Points

### New Components and Their Integration with Existing Systems

| New Component | Integrates With | Integration Mechanism |
|---------------|----------------|----------------------|
| `Collection` model | `User` model | FK: user_id → users.id |
| `CollectionFile` model | `Collection` model | FK: collection_id → collections.id |
| `Signal` model | `Collection` model | FK: collection_id → collections.id |
| Pulse graph | `E2BSandboxRuntime` | Direct import — zero changes to sandbox service |
| Pulse graph | `get_llm()` factory | Add `pulse_agent` entry to `prompts.yaml` only |
| `/collections` router | Credit system | `CreditService.deduct_credit()` — same call signature |
| `/collections` router | Platform settings | `platform_settings.get(db, "workspace_credit_cost_pulse")` |
| `/collections` router | Tier config | `user_classes.yaml` two new fields per tier |
| `ChatSidebar.tsx` | `/workspace` route | One new nav item — no structural sidebar refactor |
| `useCredits` hook | Collection header | Existing hook, no changes — same balance endpoint |

### What Existing Systems Are NOT Modified

| Existing System | Status |
|----------------|--------|
| `backend/app/agents/graph.py` (chat pipeline) | UNCHANGED — Pulse is a completely separate graph |
| `ChatAgentState` TypedDict | UNCHANGED — Pulse has its own `PulseAgentState` |
| `File` model (user Chat files) | UNCHANGED — Collection files are a separate table |
| `E2BSandboxRuntime` | UNCHANGED — reused as-is |
| Auth dependencies (`CurrentUser`, `DbSession`) | UNCHANGED — same dependencies on all collection endpoints |
| `CreditService` | UNCHANGED — reused via `deduct_credit()` |
| `platform_settings.py` | ADDITIVE ONLY — new keys added to `DEFAULTS` dict |
| Admin portal frontend | UNCHANGED in v0.8 — admin scope is YAML config only |
| All existing routers | UNCHANGED — `/collections` is a new addition, not a modification |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Adding Pulse Fields to ChatAgentState

**What people do:** Extend the existing `ChatAgentState` TypedDict with `collection_id`, `signals`, etc. to "reuse" the chat graph for Pulse.

**Why it's wrong:** The Pulse pipeline has a completely different state shape (batch file analysis vs. conversational query), different input contract, and no need for `messages`, `routing_decision`, or `visualization_requested`. Mixing the two pollutes both state schemas, makes both pipelines harder to reason about, and creates risk of accidental state bleed.

**Do this instead:** Create `PulseAgentState` as a separate TypedDict in `state.py`. Create `pulse/graph.py` as a separate `StateGraph`. The two graphs share only infrastructure imports (E2B, LLM factory) — not state or nodes.

### Anti-Pattern 2: Storing Collection Files in the Existing `files` Table

**What people do:** Add a nullable `collection_id` FK to the existing `File` model to avoid a new table.

**Why it's wrong:** The `File` model carries `data_summary` (Onboarding Agent text), `query_suggestions`, and `stored_filename` (opaque UUID-based). None of these fields apply to Collection files, which need `column_profile` (structured JSON schema) and `row_count`. Forcing a single table creates null columns, confused ownership semantics (user-scoped vs. collection-scoped), and makes the Onboarding Agent trigger logic ambiguous.

**Do this instead:** `CollectionFile` is a separate model in `collection_file.py`. File storage paths use a separate prefix (`uploads/collections/{collection_id}/`). The systems are parallel, not merged.

### Anti-Pattern 3: Rebuilding UI From Scratch Instead of Migrating

**What people do:** Treat the mockup as a "design reference" and rebuild components from scratch.

**Why it's wrong:** The 20 components in `pulse-mockup/src/components/workspace/` are production-ready Next.js + shadcn/ui + Recharts code. Rebuilding duplicates work, introduces divergence from the agreed UI contract, and takes significantly longer.

**Do this instead:** Copy component files. Update `@/` import aliases. Replace mock data with hook data. The component tree, prop names, and interaction patterns are the contract — not optional suggestions.

### Anti-Pattern 4: Streaming Pulse Progress via SSE

**What people do:** Use SSE (like the chat system) to stream Pulse analysis progress to the frontend because it "feels more live."

**Why it's wrong:** The Pulse Agent runs discrete E2B analysis passes, not a streaming LLM response. The frontend already has a clean solution: `DetectionLoading` is a full-page component with locally-animated steps. The backend returns when done. SSE would add significant implementation complexity (separate streaming infrastructure, connection management) for no user-visible benefit given the animated loading screen.

**Do this instead:** `POST /collections/{id}/pulse` runs synchronously and returns 200 with signals when done. `DetectionLoading` animates its steps locally. If Pulse runs start exceeding 30 seconds, introduce background task + polling endpoint at that point.

### Anti-Pattern 5: Copy-Pasting Tier Access Checks Into Every Endpoint

**What people do:** Write the `workspace_access` and `max_active_collections` check inline in every collection endpoint handler that needs it.

**Why it's wrong:** The same check is needed in at least two endpoints (`POST /collections`, `POST /collections/{id}/pulse`). Code duplication causes drift — if the check logic changes, it must be updated in multiple places.

**Do this instead:** Create a `WorkspaceAccess` FastAPI dependency that encapsulates both the tier check and the collection limit check. Inject it as a parameter on any endpoint that requires workspace access:

```python
@router.post("", status_code=201)
async def create_collection(
    body: CreateCollectionRequest,
    current_user: CurrentUser,
    db: DbSession,
    _: WorkspaceAccess,   # raises 403 if access denied
) -> CollectionResponse:
```

---

## Scaling Considerations

The platform is single-developer, single-instance, Dokploy-deployed. The table below identifies early risk signals, not targets for premature optimization.

| Scale | Concern | Approach |
|-------|---------|---------|
| Current (< 100 users) | Pulse runs block the request thread for 5-15s | Acceptable — synchronous is simpler; `DetectionLoading` covers the UX |
| 100-500 users | Multiple simultaneous Pulse runs | E2B creates isolated per-execution sandboxes; no shared state risk. Monitor E2B cold start latency (~150ms documented). |
| 500+ users | Pulse run queue contention on the backend process | Switch `POST /collections/{id}/pulse` to return a job ID; add polling endpoint `GET /collections/{id}/pulse/status`. FastAPI `BackgroundTasks` is the simplest step before Celery. |
| Any scale | Collection file storage in `uploads/collections/` | Same named Docker volume as existing file uploads. S3 migration deferred until storage volume justifies it. |

---

## Sources

All findings are HIGH confidence based on direct codebase inspection:

- `backend/app/agents/graph.py` — chat pipeline architecture, LangGraph usage pattern
- `backend/app/agents/state.py` — existing TypedDict patterns (`ChatAgentState`, `OnboardingState`)
- `backend/app/agents/coding.py` — agent node structure, LLM factory usage
- `backend/app/models/file.py`, `credit_transaction.py`, `user_credit.py`, `base.py` — model patterns
- `backend/app/services/credit.py` — `SELECT FOR UPDATE` credit deduction pattern
- `backend/app/services/platform_settings.py` — TTL cache, `DEFAULTS` dict, `VALID_KEYS` pattern
- `backend/app/routers/files.py` — router structure, dependency pattern
- `backend/app/main.py` — router registration, mode-based routing
- `frontend/src/app/(dashboard)/layout.tsx` — `(dashboard)` group layout with `ChatSidebar`
- `frontend/src/hooks/` — existing TanStack Query hook names and patterns
- `frontend/src/stores/` — Zustand store scope (sessionStore, tabStore)
- `pulse-mockup/src/components/workspace/` — 20 components available for migration
- `pulse-mockup/src/app/workspace/` — complete route structure for v0.8-v0.11 pages
- `requirements/Pulse-req-milestone-plan.md` — authoritative v0.8 scope specification
- `requirements/Spectra-Pulse-Requirement.md` — ER diagram, data model decisions, user journey

---

*Architecture research for: v0.8 Spectra Pulse (Detection) — Pulse Analysis module integration into existing Spectra platform*
*Researched: 2026-03-05*
