# Architecture Patterns: Multi-File Conversation Support (v0.3)

**Domain:** AI Data Analytics Platform - Chat-Session-Centric Multi-File Architecture
**Researched:** 2026-02-11
**Confidence:** HIGH (based on thorough codebase analysis + verified patterns)

---

## Executive Summary

Spectra v0.3 restructures from a file-centric model (1 file = 1 chat) to a chat-session-centric model (1 chat = N files). This requires changes at every layer: database schema, API endpoints, LangGraph agent state, E2B sandbox execution, LangGraph checkpointing, and frontend state management.

The current architecture has clean separation of concerns which makes this migration feasible without a full rewrite. The key architectural challenge is **multi-file context aggregation**: how to assemble data summaries, profiles, and file bytes from N files and pass them through the agent pipeline that currently assumes a single file.

---

## Current Architecture (v0.2) - Baseline

### Data Model

```
User --1:N--> File --1:N--> ChatMessage
                   (file_id is the chat identity)
                   (LangGraph thread_id = "file_{file_id}_user_{user_id}")
```

### Key Coupling Points (What Must Change)

| Layer | Current Coupling to Single File | Impact |
|-------|-------------------------------|--------|
| `ChatMessage.file_id` | Messages belong to a file, not a session | Schema change |
| `ChatAgentState.file_id` | State carries single file_id, file_path, data_summary | State schema change |
| `agent_service.run_chat_query_stream` | Loads 1 file record, builds 1-file context | Service refactor |
| `execute_in_sandbox` | Uploads 1 file, generates `df = pd.read_csv(...)` | Execution refactor |
| `coding agent` prompt | `{data_profile}` is single-file JSON | Prompt change |
| `useSSEStream.startStream` | Posts to `/chat/{file_id}/stream` | URL change |
| `useChatMessages` | Queries by `file_id` | Key change |
| `useTabStore` | Tabs are file-based, `currentTabId` is `fileId` | Full replacement |
| `thread_id` | `f"file_{file_id}_user_{user_id}"` | Thread ID scheme change |
| Dashboard layout | FileSidebar (left) + tab bar (top) + ChatInterface | Layout restructure |

---

## Target Architecture (v0.3)

### Data Model Transformation

```
User --1:N--> ChatSession --M:N--> File  (via SessionFile association)
                   |
                   +--1:N--> ChatMessage  (messages belong to session)
```

### High-Level Component Diagram

```
+----------+  +-------------------------------+  +-----------+
| Chat     |  |  Main Content Area            |  | Linked    |
| Sidebar  |  |                               |  | Files     |
| (left)   |  |  +-------------------------+  |  | Panel     |
|          |  |  | ChatView (per session)  |  |  | (right)   |
| [New]    |  |  | - LinkedFilesBar (top)  |  |  |           |
| [History]|  |  | - MessageList           |  |  | File 1    |
| [Files]  |  |  | - ChatInput + Actions   |  |  | File 2    |
+----------+  |  +-------------------------+  |  +-----------+
              +-------------------------------+

Backend:
+--------------+     +-----------------+     +------------------+
| FastAPI      |     | LangGraph       |     | E2B Sandbox      |
| /sessions/*  |---->| Multi-file      |---->| N files uploaded  |
| /chat/*      |     | ChatAgentState  |     | N named DFs      |
| /files/*     |     | Coding/Analysis |     | Cross-file code  |
+--------------+     +-----------------+     +------------------+
       |                    |
       v                    v
+--------------+     +-----------------+
| PostgreSQL   |     | Checkpointer    |
| chat_sessions|     | thread_id =     |
| session_files|     | session_{id}_   |
| chat_messages|     | user_{id}       |
+--------------+     +-----------------+
```

---

## Component Boundaries

### NEW Components

| Component | Layer | Responsibility | Communicates With |
|-----------|-------|---------------|-------------------|
| `ChatSession` model | Backend/DB | First-class chat entity with title, timestamps | `SessionFile`, `ChatMessage`, `User` |
| `SessionFile` association | Backend/DB | Many-to-many join between sessions and files with link metadata | `ChatSession`, `File` |
| `sessions` router | Backend/API | CRUD for chat sessions, link/unlink files | `ChatSessionService`, `FileService` |
| `ChatSessionService` | Backend/Service | Business logic for session management | DB models, `AgentService` |
| `ContextAssembler` | Backend/Service | Builds multi-file context for agent state from session files | `FileService`, `OnboardingAgent` |
| `useChatSessionStore` | Frontend/Store | Zustand store replacing `useTabStore` | API client, components |
| `ChatSidebar` | Frontend/Component | Left sidebar with chat history, "New Chat", "My Files" | `useChatSessionStore`, router |
| `LinkedFilesPanel` | Frontend/Component | Right sidebar showing files linked to current session | Session hooks, file hooks |
| `LinkedFilesBar` | Frontend/Component | Compact bar at top of chat showing linked file badges | Session hooks |
| `FileManagerPage` | Frontend/Page | Full-page file listing at `/dashboard/files` route | `useFileManager` hook |
| `FileLinkModal` | Frontend/Component | Modal to select existing files to link to session | File hooks, session hooks |
| `useChatSessions` hook | Frontend/Hook | TanStack Query hooks for session CRUD | API client |

### MODIFIED Components

| Component | Current Behavior | New Behavior | Change Scope |
|-----------|-----------------|-------------|-------------|
| `ChatMessage` model | `file_id` FK required | `session_id` FK required, `file_id` removed | Schema change |
| `ChatAgentState` | Single `file_id`, `file_path`, `data_summary`, `data_profile` | `session_id`, `file_contexts` list, `combined_data_summary`, `combined_data_profile` | State schema change |
| `agent_service.run_chat_query_stream` | Loads single file, builds single-file context | Loads session + all linked files, uses `ContextAssembler` | Major refactor |
| `execute_in_sandbox` in `graph.py` | Uploads 1 file, creates single `df` | Uploads N files, creates N named DataFrames | Major refactor |
| `E2BSandboxRuntime` | `execute(data_file, data_filename)` | `execute_multi_file(files: list[tuple])` | Method addition |
| `coding agent` prompt | Assumes single `df` variable | Receives multi-file profile, generates code using named DataFrames | Prompt + format change |
| `code_checker` prompt | Validates single-df code | Validates multi-df code | Prompt change |
| `data_analysis` prompt | Single execution context | Multi-file execution context | Prompt change |
| `manager` prompt | Single-file routing context | Multi-file routing context | Prompt change |
| `chat` router | Endpoints keyed by `file_id` | New endpoints keyed by `session_id` | API refactor |
| `ChatInterface` | Receives `fileId`/`fileName` | Receives `sessionId`, fetches linked files | Major refactor |
| `useChatMessages` hook | Queries by `file_id`, key `["chat", "messages", fileId]` | Queries by `session_id`, key `["sessions", sessionId, "messages"]` | Hook refactor |
| `useSSEStream` hook | Posts to `/chat/{file_id}/stream` | Posts to `/chat/sessions/{session_id}/stream` | URL change |
| `ChatService` | `list_file_messages(file_id)`, `create_message(file_id)` | `list_session_messages(session_id)`, `create_message(session_id)` | Parameter change |
| Chat schemas | `ChatMessageResponse.file_id` | `ChatMessageResponse.session_id` | Schema change |
| Dashboard layout | `FileSidebar` (left) + tabs (top) + content | `ChatSidebar` (left) + content + optional `LinkedFilesPanel` (right) | Layout restructure |
| Dashboard page | Tab bar with file tabs, empty upload state | Session-based view, greeting empty state | Major refactor |
| LangGraph thread_id | `f"file_{file_id}_user_{user_id}"` | `f"session_{session_id}_user_{user_id}"` | Thread ID change |
| `File` model | `chat_messages` relationship | `session_files` relationship (messages go through sessions) | Relationship change |

### UNCHANGED Components

| Component | Why Unchanged |
|-----------|--------------|
| `User` model (mostly) | Add `chat_sessions` relationship back_populates only |
| `OnboardingAgent` | Still processes one file at a time during upload |
| `FileUploadZone` component | Upload UX stays the same, trigger context changes |
| Authentication system | No changes needed |
| `SandboxRuntime` protocol | Interface extends (new method), old method kept |
| `LLM factory` | No changes needed |
| Agent config YAML structure | Structure stays, prompt content changes |
| `FileService` | File CRUD unchanged, still works independently |
| Search quota system | Unchanged |
| Context window management | Works the same, just with session-based thread IDs |

---

## Database Schema Design

### New Tables

```python
# backend/app/models/chat_session.py

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.models.base import Base

class ChatSession(Base):
    """Chat session - the primary workspace entity in v0.3."""
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    session_files: Mapped[list["SessionFile"]] = relationship(
        "SessionFile", back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionFile.linked_at"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
```

```python
# backend/app/models/session_file.py

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.models.base import Base

class SessionFile(Base):
    """Association table: ChatSession <-> File (many-to-many with metadata)."""
    __tablename__ = "session_files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    # Alias: user-friendly name for the DataFrame variable
    # Auto-generated from filename, e.g., "sales" for "Q4_2025_sales.csv"
    alias: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="session_files")
    file: Mapped["File"] = relationship("File", back_populates="session_files")

    # Same file cannot be linked twice to same session
    __table_args__ = (
        UniqueConstraint("session_id", "file_id", name="uq_session_file"),
    )
```

### Modified Tables

**ChatMessage:** Replace `file_id` FK with `session_id` FK.

```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    # CHANGED: session_id replaces file_id
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # CHANGED relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_messages")
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
```

**File model:** Replace `chat_messages` relationship with `session_files`.

```python
class File(Base):
    # ... all existing columns unchanged ...

    # CHANGED: Replace chat_messages relationship with session_files
    session_files: Mapped[list["SessionFile"]] = relationship(
        "SessionFile", back_populates="file",
        cascade="all, delete-orphan"
    )
    # REMOVED: chat_messages relationship
```

### Migration Strategy: Two-Phase Approach

**Migration 1: Add new tables, keep old columns (safe, reversible)**

```python
def upgrade():
    # 1. Create chat_sessions table
    op.create_table("chat_sessions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("title", sa.String(255), default="New Chat"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # 2. Create session_files association table
    op.create_table("session_files",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("session_id", sa.UUID(),
                  sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("file_id", sa.UUID(),
                  sa.ForeignKey("files.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("linked_at", sa.DateTime(timezone=True)),
        sa.Column("alias", sa.String(100), nullable=True),
        sa.UniqueConstraint("session_id", "file_id", name="uq_session_file"),
    )

    # 3. Add session_id to chat_messages (NULLABLE initially)
    op.add_column("chat_messages",
        sa.Column("session_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_chat_messages_session_id", "chat_messages",
        "chat_sessions", ["session_id"], ["id"], ondelete="CASCADE")
```

**Migration 2: Data migration + column swap (requires careful testing)**

```python
def upgrade():
    conn = op.get_bind()

    # For each unique (user_id, file_id) pair in chat_messages,
    # create a ChatSession and link the file
    results = conn.execute(text(
        "SELECT DISTINCT user_id, file_id FROM chat_messages"
    ))
    for row in results:
        session_id = str(uuid4())
        # Create session titled after the file
        conn.execute(text("""
            INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
            SELECT :sid, :uid, f.original_filename, NOW(), NOW()
            FROM files f WHERE f.id = :fid
        """), {"sid": session_id, "uid": str(row.user_id), "fid": str(row.file_id)})

        # Link file to session
        conn.execute(text("""
            INSERT INTO session_files (id, session_id, file_id, linked_at)
            VALUES (:id, :sid, :fid, NOW())
        """), {"id": str(uuid4()), "sid": session_id, "fid": str(row.file_id)})

        # Update messages to point to session
        conn.execute(text("""
            UPDATE chat_messages SET session_id = :sid
            WHERE user_id = :uid AND file_id = :fid
        """), {"sid": session_id, "uid": str(row.user_id), "fid": str(row.file_id)})

    # Make session_id NOT NULL
    op.alter_column("chat_messages", "session_id", nullable=False)
    # Create index for session_id queries
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    # Drop old file_id column
    op.drop_constraint("chat_messages_file_id_fkey", "chat_messages", type_="foreignkey")
    op.drop_index("ix_chat_messages_file_id", "chat_messages")
    op.drop_column("chat_messages", "file_id")
```

---

## LangGraph Agent State Changes

### Multi-File State Schema

```python
class ChatAgentState(TypedDict):
    """State for the multi-file chat analysis pipeline (v0.3)."""

    # CHANGED: Session-based identity (was file_id)
    session_id: str
    """Chat session UUID."""

    user_id: str
    """User UUID for access control."""

    user_query: str
    """User's natural language data analysis query."""

    # CHANGED: Multi-file context replaces single-file fields
    file_contexts: list[dict]
    """Per-file context list. Each dict contains:
    {
        "file_id": str,
        "filename": str,
        "alias": str,           # DataFrame variable name (e.g., "df_sales")
        "file_path": str,       # Absolute path on disk
        "data_summary": str,    # Onboarding agent summary
        "data_profile": str,    # JSON string with column info
        "user_context": str,    # User-provided context
    }
    """

    combined_data_summary: str
    """Merged summary of all linked files, formatted for prompt injection."""

    combined_data_profile: str
    """Merged data profile JSON with file boundaries clearly marked."""

    # UNCHANGED: Pipeline execution fields
    generated_code: str
    validation_result: str
    validation_errors: list[str]
    error_count: int
    max_steps: int
    execution_result: str
    analysis: str
    messages: Annotated[list[AnyMessage], add_messages]
    routing_decision: RoutingDecision | None
    previous_code: str
    follow_up_suggestions: list[str]
    web_search_enabled: bool
    search_sources: list[dict]
    final_response: str
    error: str
```

### Context Assembler Service

A dedicated service builds multi-file context before graph invocation:

```python
# backend/app/services/context_assembler.py

import json
import os
from app.models.file import File
from app.models.session_file import SessionFile

class ContextAssembler:
    """Builds aggregated multi-file context for the LangGraph agent state."""

    @staticmethod
    def build_file_contexts(
        session_files: list[SessionFile],
    ) -> list[dict]:
        """Build per-file context dicts from session-file associations."""
        contexts = []
        for sf in session_files:
            f = sf.file
            alias = sf.alias or ContextAssembler._generate_alias(f.original_filename)
            contexts.append({
                "file_id": str(f.id),
                "filename": f.original_filename,
                "alias": alias,
                "file_path": f.file_path,
                "data_summary": f.data_summary or "",
                "data_profile": "",  # populated separately via profiling
                "user_context": f.user_context or "",
            })
        return contexts

    @staticmethod
    def build_combined_summary(file_contexts: list[dict]) -> str:
        """Merge per-file summaries into a combined prompt-ready string."""
        if len(file_contexts) == 1:
            ctx = file_contexts[0]
            return (
                f"**File: {ctx['filename']}** (DataFrame: `{ctx['alias']}`)\n"
                f"{ctx['data_summary']}\n"
                f"User context: {ctx['user_context'] or 'None'}"
            )

        parts = []
        for i, ctx in enumerate(file_contexts, 1):
            parts.append(
                f"### File {i}: {ctx['filename']} (DataFrame: `{ctx['alias']}`)\n"
                f"{ctx['data_summary']}\n"
                f"User context: {ctx['user_context'] or 'None'}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def build_combined_profile(file_contexts: list[dict]) -> str:
        """Merge per-file data profiles into structured JSON for coding agent."""
        files_data = []
        for ctx in file_contexts:
            profile = json.loads(ctx["data_profile"]) if ctx["data_profile"] else {}
            files_data.append({
                "name": ctx["alias"],
                "filename": ctx["filename"],
                **profile,
            })

        # Auto-detect join hints by finding matching column names
        join_hints = ContextAssembler._detect_join_hints(files_data)

        return json.dumps({
            "files": files_data,
            "join_hints": join_hints,
        }, indent=2)

    @staticmethod
    def _generate_alias(filename: str) -> str:
        """Generate a DataFrame alias from filename.
        'Q4_2025_Sales_Data.csv' -> 'df_q4_2025_sales_data'
        """
        name = os.path.splitext(filename)[0]
        # Replace spaces and hyphens with underscores, lowercase
        alias = name.lower().replace(" ", "_").replace("-", "_")
        # Remove non-alphanumeric characters except underscores
        alias = "".join(c for c in alias if c.isalnum() or c == "_")
        return f"df_{alias}"

    @staticmethod
    def _detect_join_hints(files_data: list[dict]) -> list[str]:
        """Find columns with matching names across files for join suggestions."""
        hints = []
        if len(files_data) < 2:
            return hints

        for i in range(len(files_data)):
            cols_i = set(files_data[i].get("columns", {}).keys())
            for j in range(i + 1, len(files_data)):
                cols_j = set(files_data[j].get("columns", {}).keys())
                common = cols_i & cols_j
                for col in common:
                    hints.append(
                        f"{files_data[i]['name']}.{col} <-> {files_data[j]['name']}.{col}"
                    )
        return hints
```

### Thread ID Strategy

**Current:** `thread_id = f"file_{file_id}_user_{user_id}"`
**New:** `thread_id = f"session_{session_id}_user_{user_id}"`

Old checkpoints keyed by `file_*` thread IDs become orphaned. This is acceptable because:
1. Sessions are new entities -- no collision with old thread IDs
2. Old checkpoints can be garbage-collected with a cleanup script later
3. No need to migrate checkpoint data (fragile, undocumented internal schema)

---

## E2B Sandbox Multi-File Execution

### Current Single-File Flow (in `execute_in_sandbox`, graph.py line 250-434)

```python
# Current: Read 1 file, upload 1 file, create 1 `df`
file_path = state.get("file_path", "")
data_filename = os.path.basename(file_path)
with open(file_path, "rb") as f:
    data_file = f.read()
# ... uploads to sandbox, generates: df = pd.read_csv('/home/user/file.csv')
```

### New Multi-File Flow

```python
async def execute_in_sandbox(state: ChatAgentState) -> dict | Command:
    """Execute code with multiple data files in E2B sandbox."""
    writer = get_stream_writer()
    settings = get_settings()

    file_contexts = state.get("file_contexts", [])
    if not file_contexts:
        # Fallback: no files linked
        writer({"type": "error", "event": "error",
                "message": "No files linked to this chat session."})
        return Command(goto="halt", update={
            "error": "no_files_linked",
            "execution_result": "Error: No data files available",
        })

    # Read all files from disk
    file_data = []
    for ctx in file_contexts:
        file_path = ctx["file_path"]
        filename = os.path.basename(file_path)
        alias = ctx["alias"]
        try:
            with open(file_path, "rb") as f:
                file_data.append({
                    "bytes": f.read(),
                    "filename": filename,
                    "alias": alias,
                })
        except (FileNotFoundError, IOError) as e:
            writer({"type": "error", "event": "error",
                    "message": f"Cannot read file: {filename}"})
            return Command(goto="halt", update={
                "error": "file_read_error",
                "execution_result": f"Error: Cannot read {filename}: {e}",
            })

    # Build loading preamble: create named DataFrames
    loading_lines = ["import pandas as pd", "import json", ""]
    for fd in file_data:
        ext = os.path.splitext(fd["filename"])[1].lower()
        sandbox_path = f"/home/user/{fd['filename']}"
        if ext in ('.xlsx', '.xls'):
            loading_lines.append(f'{fd["alias"]} = pd.read_excel("{sandbox_path}")')
        else:
            loading_lines.append(
                f'try:\n'
                f'    {fd["alias"]} = pd.read_csv("{sandbox_path}", encoding="utf-8")\n'
                f'except UnicodeDecodeError:\n'
                f'    try:\n'
                f'        {fd["alias"]} = pd.read_csv("{sandbox_path}", encoding="latin-1")\n'
                f'    except UnicodeDecodeError:\n'
                f'        {fd["alias"]} = pd.read_csv("{sandbox_path}", encoding="cp1252")'
            )

    # Backward compatibility: single file also gets `df` alias
    if len(file_data) == 1:
        loading_lines.append(f'df = {file_data[0]["alias"]}')

    preamble = "\n".join(loading_lines) + "\n\n"
    full_code = preamble + state.get("generated_code", "")

    # Execute with all files
    runtime = E2BSandboxRuntime(timeout_seconds=settings.sandbox_timeout_seconds)
    result = await asyncio.to_thread(
        runtime.execute_multi_file,
        code=full_code,
        timeout=float(settings.sandbox_timeout_seconds),
        files=[(fd["bytes"], fd["filename"]) for fd in file_data],
    )
    # ... result handling same as current execute_in_sandbox
```

### SandboxRuntime Extension

```python
# Add new method to E2BSandboxRuntime (keep existing execute() for compatibility)

def execute_multi_file(
    self,
    code: str,
    timeout: float = 60.0,
    files: list[tuple[bytes, str]] | None = None,
) -> ExecutionResult:
    """Execute code with multiple data files uploaded to sandbox.

    Args:
        code: Full Python code including file loading preamble
        timeout: Maximum execution time
        files: List of (file_bytes, filename) tuples
    """
    start_time = time.time()
    settings = get_settings()

    try:
        with Sandbox.create(
            timeout=int(timeout),
            api_key=settings.e2b_api_key
        ) as sandbox:
            # Upload all files (E2B has no batch API, sequential upload)
            if files:
                for file_bytes, filename in files:
                    sandbox.files.write(f"/home/user/{filename}", file_bytes)

            # Execute code
            execution = sandbox.run_code(code, timeout=timeout)

            # ... same result parsing as existing execute() method
    except Exception as e:
        # ... same error handling
```

### Combined Data Profile Format

The `combined_data_profile` injected into the coding agent prompt:

```json
{
  "files": [
    {
      "name": "df_sales",
      "filename": "Q4_2025_sales.csv",
      "columns": {
        "order_id": {"dtype": "int64", "sample": [1001, 1002, 1003]},
        "customer_id": {"dtype": "int64", "sample": [501, 502, 503]},
        "revenue": {"dtype": "float64", "sample": [150.00, 200.50, 75.25]}
      },
      "row_count": 5000
    },
    {
      "name": "df_customers",
      "filename": "customers_master.xlsx",
      "columns": {
        "customer_id": {"dtype": "int64", "sample": [501, 502, 503]},
        "region": {"dtype": "object", "sample": ["East", "West", "North"]}
      },
      "row_count": 1200
    }
  ],
  "join_hints": [
    "df_sales.customer_id <-> df_customers.customer_id"
  ]
}
```

The `join_hints` are auto-detected by `ContextAssembler._detect_join_hints()` -- matching column names across files gives the coding agent structural awareness.

---

## Agent Prompt Changes

### Coding Agent: Multi-File Awareness

```yaml
coding:
  system_prompt: |
    Generate Python code for data analysis.

    **Available DataFrames:**
    {data_profile}

    Each file is loaded as a separate DataFrame with the variable name shown above.
    For cross-file analysis, use merge/join operations between DataFrames.

    **User context:** {user_context}

    **Rules:**
    - Use exact DataFrame variable names as shown (e.g., df_sales, df_customers)
    - Use exact column names from the profile (case-sensitive)
    - For cross-file joins: pd.merge(df_a, df_b, on='common_column')
    - Convert results to Python types: int(), float(), str()
    - For DataFrame/Series results: use .to_dict('records')
    - End with: print(json.dumps({"result": result}))
    - Libraries allowed: {allowed_libraries}
    - Use .fillna(0) for missing values
    - NEVER check if DataFrames exist or use locals()/globals()

    **Single-file example:**
    ```python
    import json
    result = int(df_sales['revenue'].sum())
    print(json.dumps({"result": result}))
    ```

    **Cross-file example:**
    ```python
    import json
    merged = pd.merge(df_sales, df_customers, on='customer_id')
    result = merged.groupby('region')['revenue'].sum().reset_index().to_dict('records')
    print(json.dumps({"result": result}))
    ```

    Return only code, no explanations.
```

### Code Checker: Multi-DataFrame Validation

Add to the code checker prompt:
```
8. If multiple DataFrames are available, does the code use the correct DataFrame variable names?
9. For cross-file operations, are merge/join keys valid columns in both DataFrames?
```

### Manager Agent: Multi-File Context

The manager routing prompt should include file count and names:
```
**Session Context:**
- Files linked: {file_count} ({file_names})
- Messages in history: {msg_count}
- Has previous code: {has_code}
```

---

## API Endpoint Design

### New Session Endpoints

```python
# backend/app/routers/sessions.py

router = APIRouter(prefix="/sessions", tags=["Sessions"])

POST   /sessions/                              # Create new chat session
GET    /sessions/                              # List user's sessions (chat history sidebar)
GET    /sessions/{session_id}                  # Get session details + linked files
PATCH  /sessions/{session_id}                  # Update session (title)
DELETE /sessions/{session_id}                  # Delete session + all messages

POST   /sessions/{session_id}/files            # Link file(s) to session
DELETE /sessions/{session_id}/files/{file_id}  # Unlink file from session
POST   /sessions/{session_id}/generate-title   # Auto-generate title from first query
```

### Modified Chat Endpoints (Session-Based)

```python
# backend/app/routers/chat.py -- session-based versions

GET    /chat/sessions/{session_id}/messages         # List messages
POST   /chat/sessions/{session_id}/stream           # Stream AI query
GET    /chat/sessions/{session_id}/context-usage     # Context window usage
POST   /chat/sessions/{session_id}/trim-context      # Trim context
```

### Session List Response Shape

```python
class ChatSessionListItem(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    file_count: int
    message_count: int
    last_message_preview: str | None  # First 100 chars of last message

class ChatSessionDetail(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    files: list[SessionFileResponse]  # Linked files with aliases

class SessionFileResponse(BaseModel):
    file_id: UUID
    filename: str
    alias: str | None
    file_type: str
    linked_at: datetime
    has_summary: bool
```

---

## Frontend Architecture Changes

### State Management: ChatSessionStore Replaces TabStore

```typescript
// frontend/src/stores/chatSessionStore.ts

interface ChatSessionStore {
  currentSessionId: string | null;
  setCurrentSession: (sessionId: string | null) => void;
}

export const useChatSessionStore = create<ChatSessionStore>((set) => ({
  currentSessionId: null,
  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
}));
```

The store is minimal because TanStack Query handles session list caching and refetching. The store only tracks which session is currently active (needed for sidebar highlighting and URL sync).

### TanStack Query Key Structure

```typescript
// NEW keys
["sessions"]                                    // session list for sidebar
["sessions", sessionId]                         // session detail + linked files
["sessions", sessionId, "messages"]             // session messages
["sessions", sessionId, "context-usage"]        // context window usage

// UNCHANGED keys
["files"]                                       // user's file list
["files", fileId, "summary"]                    // file summary (for info modal)
```

### New Hooks

```typescript
// frontend/src/hooks/useChatSessions.ts

export function useChatSessions()                      // List all sessions
export function useChatSession(sessionId: string)      // Single session + files
export function useCreateSession()                     // Mutation: create session
export function useDeleteSession()                     // Mutation: delete session
export function useUpdateSessionTitle()                // Mutation: update title
export function useLinkFile()                          // Mutation: link file to session
export function useUnlinkFile()                        // Mutation: unlink file
export function useGenerateSessionTitle()              // Mutation: auto-title

// MODIFIED hooks
export function useChatMessages(sessionId: string | null)  // Changed param
export function useAddLocalMessage()                        // Changed: uses sessionId
export function useInvalidateChatMessages()                 // Changed: query key
// useSSEStream.startStream(sessionId, message, webSearchEnabled) -- changed param
```

### Route Structure

```
/dashboard                        -> Empty state with greeting
/dashboard/chat/{sessionId}       -> Specific chat session
/dashboard/files                  -> My Files management page
```

Navigation uses Next.js App Router. `sessionId` comes from URL params.

### Layout Restructure

**Current layout** (`DashboardLayout` in `frontend/src/app/(dashboard)/layout.tsx`):
```
Header
+--------+----------------------------------+
| File   | Tab Bar (file tabs)              |
| Side   | +----------------------------+   |
| bar    | | ChatInterface (per file)   |   |
| 260px  | +----------------------------+   |
+--------+----------------------------------+
```

**New layout:**
```
Header
+--------+-------------------------------+---------+
| Chat   | Main Content Area             | Linked  |
| Side   |                               | Files   |
| bar    | (dynamic based on route)      | Panel   |
| 260px  |                               | 240px   |
|        | /dashboard -> Empty greeting  | (cond)  |
| [New]  | /dashboard/chat/:id -> Chat   |         |
| [Hist] | /dashboard/files -> Files     |         |
| [Files]|                               |         |
+--------+-------------------------------+---------+
```

The right panel (`LinkedFilesPanel`) is **conditional** -- only shows when a chat session is active and has linked files. On the Files page, it is hidden.

### Component Tree

```
DashboardLayout
  +-- Header (logo, user menu) [MODIFIED: same structure]
  +-- ChatSidebar (left, 260px) [NEW: replaces FileSidebar]
  |     +-- NewChatButton [NEW]
  |     +-- ChatHistoryList [NEW: session list, sorted by updated_at]
  |     +-- Separator
  |     +-- MyFilesButton [NEW: navigates to /dashboard/files]
  +-- MainContent (flex-1)
  |     +-- ChatPage (for /dashboard/chat/:sessionId) [MODIFIED from DashboardPage]
  |     |     +-- LinkedFilesBar (top of chat, shows file badges) [NEW]
  |     |     +-- MessageList [MODIFIED: sessionId-based]
  |     |     +-- ChatInput [MODIFIED: add file action button]
  |     |     |     +-- AddFileDropdown [NEW: upload or link existing]
  |     |     |     +-- SearchToggle [UNCHANGED]
  |     |     +-- LinkedFilesPanel (right sidebar, collapsible) [NEW]
  |     +-- FileManagerPage (for /dashboard/files) [NEW]
  |     |     +-- FileList [MODIFIED from FileSidebar's file list]
  |     |     +-- FileUploadButton [REUSE FileUploadZone]
  |     |     +-- FileActions (delete, download, start chat) [NEW]
  |     +-- EmptyState (for /dashboard) [MODIFIED: greeting message]
  +-- Dialogs/Modals
        +-- FileUploadZone [REUSE existing]
        +-- FileLinkModal [NEW: select existing files to link]
        +-- FileInfoModal [REUSE existing]
```

---

## Data Flow: Complete Multi-File Chat Query

```
1. User sends message in session with 2 linked files
   POST /chat/sessions/{session_id}/stream
   Body: {content: "Compare sales by region", web_search_enabled: false}

2. Chat Router verifies session ownership
   -> Load session via ChatSessionService
   -> Verify session.user_id == current_user.id

3. AgentService.run_chat_query_stream()
   a. Load session + eager-load session_files -> files
   b. Verify all linked files have data_summary (onboarded)
   c. For each file: generate data_profile via OnboardingAgent.profile_data()
   d. ContextAssembler.build_file_contexts(session_files)
   e. ContextAssembler.build_combined_summary(file_contexts)
   f. ContextAssembler.build_combined_profile(file_contexts)
   g. Build initial_state with multi-file context
   h. thread_id = f"session_{session_id}_user_{user_id}"
   i. graph.aupdate_state(config, {messages: [HumanMessage(query)]})
   j. graph.astream(initial_state, config)

4. LangGraph Pipeline
   Manager -> routes (MEMORY_SUFFICIENT / CODE_MODIFICATION / NEW_ANALYSIS)
   Coding Agent -> sees combined_data_profile, generates multi-df code
   Code Checker -> validates multi-df references
   Execute -> uploads all files to E2B, runs code with named DataFrames
   DA Agent -> interprets results in multi-file context

5. Save messages with session_id (not file_id)
   ChatService.create_message(session_id=..., ...)

6. Frontend receives SSE events, renders in ChatView
```

---

## Patterns to Follow

### Pattern 1: Context Assembler (Dedicated Multi-File Aggregation)

**What:** A dedicated service class that takes session files and produces aggregated context for the agent state.

**When:** Every time a chat query is initiated.

**Why:** Keeps aggregation logic in one testable place. Prevents `agent_service` from becoming a god function. Makes it easy to add features like join hint detection, profile compression, or context budget allocation.

### Pattern 2: Session-First, Files-Second (Lazy Initialization)

**What:** Sessions start empty (no files). Files are linked explicitly before the first AI query. The first AI response triggers auto-title generation.

**When:** User creates new chat, uploads a file, or links an existing file.

**Why:** Matches ChatGPT-style UX from requirements. Sessions can exist in "empty" state. File linking is a separate action from session creation.

### Pattern 3: Backward-Compatible DataFrame Naming

**What:** When a session has exactly 1 file, create both the named DataFrame (e.g., `df_sales`) AND the generic `df` alias. When multiple files exist, only use named DataFrames.

**When:** Sandbox code preamble generation.

**Why:** Single-file sessions should feel identical to v0.2. The `df` alias means existing prompt patterns and any code the user has seen continues to work.

### Pattern 4: Additive Two-Phase Migration

**What:** Phase 1 adds new tables and columns (nullable). Phase 2 migrates data and removes old columns. Never drop old schema in the same migration that adds new schema.

**When:** Database migration from v0.2 to v0.3.

**Why:** Allows rollback if migration fails. Data migration is the riskiest step -- separating it from schema changes reduces blast radius.

### Pattern 5: File Limit Enforcement at API Level

**What:** Cap at 10 files per session. Enforce in `POST /sessions/{id}/files`.

**When:** File linking API endpoint.

**Why:** Prevents context window overflow (10 files x ~4K tokens/file = 40K tokens of context, approaching model limits). Also prevents sandbox timeout (uploading 20+ files adds significant startup time).

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing File Bytes in LangGraph State

**What:** Putting actual file content (bytes or DataFrames) into `ChatAgentState`.

**Why bad:** State is serialized to PostgreSQL checkpoints via `AsyncPostgresSaver`. Large files (100MB each x N files) would make checkpoints enormous, slow checkpoint writes, and potentially exceed JSONB/BYTEA limits.

**Instead:** Store only metadata (paths, summaries, profiles) in state. Read file bytes from disk only at execution time inside `execute_in_sandbox`.

### Anti-Pattern 2: Concatenating All Files Into One DataFrame

**What:** Auto-merging all linked files into a single `df` before sending to the agent.

**Why bad:** Files may have completely different schemas. A sales CSV and a customer list have no common structure. Concatenation destroys semantic distinction and makes cross-file joins impossible.

**Instead:** Each file becomes a separate named DataFrame. The coding agent decides how to combine them based on the user's query and join hints.

### Anti-Pattern 3: Auto-Creating Sessions on Every Upload

**What:** Implicitly creating a new chat session whenever a file is uploaded.

**Why bad:** Requirements say files live independently ("My Files" management). Users may upload files for later use without wanting to start a chat.

**Instead:** Session creation is explicit: "New Chat" button, or "Start Chat" from the file upload completion flow. The upload-to-chat flow creates a session + links the file + navigates to the session.

### Anti-Pattern 4: Migrating LangGraph Checkpoint Data

**What:** Trying to modify `checkpoint_blobs` or `checkpoints` tables to match new state schema.

**Why bad:** LangGraph's `AsyncPostgresSaver` manages its own internal tables. The serialization format is undocumented and version-coupled. Manipulating it risks corruption.

**Instead:** Let old checkpoints (keyed by `file_*` thread IDs) become orphans. New sessions get fresh checkpoints (keyed by `session_*` thread IDs). Run a cleanup script later to delete `file_*` rows from checkpoint tables.

### Anti-Pattern 5: Routing All Chat Endpoints Through Sessions First

**What:** Requiring a session to exist before any chat message can be sent, even for the upload-and-chat flow.

**Why bad:** Creates extra API round-trips. Upload -> Create Session -> Link File -> Send Message is 4 calls.

**Instead:** The upload-and-chat flow should be a single compound operation: `POST /files/upload-and-chat` that creates the file, creates a session, links them, and returns the session ID. The frontend navigates to the session after upload.

---

## Scalability Considerations

| Concern | 1 file/session | 5 files/session | 10 files/session |
|---------|---------------|-----------------|-----------------|
| Context tokens | ~2-4K per file summary | ~10-20K tokens | ~20-40K -- may approach model limits |
| Sandbox startup | ~3s (1 file upload) | ~5s (5 sequential uploads) | ~8-10s (consider parallel writes) |
| Agent code complexity | Simple single-df | Moderate join operations | Complex multi-join -- agent may need guidance |
| Data profile size | ~500 tokens | ~2.5K tokens | ~5K tokens in prompt |

**Recommendations:**
- Hard limit: 10 files per session (enforced at API level)
- Soft limit: 5 files recommended (show warning above 5)
- For sessions approaching context limits, compress data profiles (fewer sample rows, drop low-cardinality columns from profile)

---

## Build Order (Dependency-Aware)

The following dependency graph determines the safe build order:

```
Phase A: Database Foundation
  1. ChatSession + SessionFile models
  2. Alembic Migration 1 (add tables, add nullable session_id to chat_messages)
  3. ChatSessionService (CRUD for sessions, link/unlink files)
  4. Sessions router (API endpoints)
  5. Alembic Migration 2 (data migration, make session_id NOT NULL, drop file_id)
  6. ChatService refactor (session_id-based queries)
  7. Chat schemas update (session_id in response)

Phase B: Agent Pipeline (depends on A.1-A.3)
  8. ContextAssembler service
  9. ChatAgentState schema changes (multi-file fields)
  10. Prompt updates (coding, code_checker, manager, data_analysis)
  11. E2B sandbox multi-file execution (execute_multi_file)
  12. agent_service refactor (session-based, uses ContextAssembler)
  13. Chat router refactor (session-based stream endpoint)
  14. Thread ID migration (session_* pattern)

Phase C: Frontend Structure (can start parallel with B)
  15. Route structure (/dashboard/chat/:sessionId, /dashboard/files)
  16. ChatSessionStore (Zustand, replaces TabStore)
  17. useChatSessions hooks (TanStack Query)
  18. ChatSidebar component
  19. Layout restructure (sidebar + main + right panel)

Phase D: Frontend Features (depends on C + B.13)
  20. ChatView (session-based ChatInterface)
  21. LinkedFilesBar + LinkedFilesPanel
  22. FileManagerPage (/dashboard/files)
  23. FileLinkModal (link existing files to session)
  24. AddFileDropdown in ChatInput
  25. useChatMessages refactor (sessionId-based)
  26. useSSEStream refactor (session-based URL)
  27. Upload-and-chat flow integration

Phase E: Polish
  28. Auto-title generation
  29. Empty state / greeting UX
  30. Light/dark mode
  31. Migration testing + cleanup script for old checkpoints
```

**Critical path:** A.1 -> A.2 -> A.3 -> B.8 -> B.9 -> B.12 -> B.13 -> D.20 -> D.26

**Parallelizable:**
- Phase C (frontend structure) can proceed alongside Phase B (backend agent changes)
- They only converge at Phase D when the frontend needs working API endpoints

---

## Sources

- Codebase analysis: Direct inspection of all source files in `backend/app/` and `frontend/src/`
- Requirements: `/requirements/milestone-03-req.md` (direct inspection)
- [LangGraph State Management Patterns](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025) - TypedDict state schema design
- [LangGraph Persistence Deep Guide](https://pub.towardsai.net/persistence-in-langgraph-deep-practical-guide-36dc4c452c3b) - Thread ID and checkpoint patterns
- [LangGraph Persistence Official Docs](https://docs.langchain.com/oss/python/langgraph/persistence) - Checkpoint and thread_id semantics
- [E2B Documentation](https://e2b.dev/docs) - Sandbox file upload API, sandbox.files.write
- [E2B Code Interpreter SDK](https://pypi.org/project/e2b-code-interpreter/) - Multi-file sandbox patterns
- [Alembic Best Practices](https://medium.com/@pavel.loginov.dev/best-practices-for-alembic-and-sqlalchemy-73e4c8a6c205) - Two-phase migration patterns
