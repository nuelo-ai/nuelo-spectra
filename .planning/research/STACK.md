# Technology Stack: v0.3 Multi-File Conversation Support

**Project:** Spectra - AI-powered data analytics platform
**Researched:** 2026-02-11
**Confidence:** HIGH (existing stack validated in production, additions are well-understood patterns)

## Overview

This research focuses exclusively on stack changes needed for v0.3 multi-file conversation support. The existing stack (FastAPI, PostgreSQL, SQLAlchemy, LangGraph, E2B, Next.js 16, React 19, TanStack Query, shadcn/ui, Zustand) is validated and unchanged. The v0.3 transformation is primarily **architectural and schema-level** -- not a library addition problem.

Key insight: **v0.3 requires zero new backend dependencies and minimal frontend additions.** The transformation is about restructuring data models, API routes, frontend navigation, and agent state -- all achievable with the existing stack.

## What Changes (and What Does Not)

### Does NOT Change
- FastAPI backend framework
- PostgreSQL database
- SQLAlchemy ORM
- Alembic migrations
- LangGraph agent orchestration
- E2B sandbox execution
- All 5 LLM providers
- Next.js 16 / React 19 / TanStack Query
- JWT authentication
- SSE streaming
- Tailwind CSS 4

### Changes Required

| Layer | What Changes | Why |
|-------|-------------|-----|
| Database schema | New `chat_sessions` table, new `session_files` junction table, `chat_messages.file_id` becomes nullable + add `session_id` | Chat sessions become first-class entities decoupled from files |
| Backend API routes | New `/sessions/*` router, modify `/chat/*` to use session_id, new file-linking endpoints | Chat-centric API replacing file-centric API |
| LangGraph state | `ChatAgentState` gains multi-file fields (`file_ids`, `data_summaries`, `file_paths`), thread_id changes from `file_{id}_user_{id}` to `session_{id}` | Agent must reference multiple files in one conversation |
| Frontend state | Replace `tabStore` with `sessionStore`, new `chatSessionStore` for sidebar navigation | Chat-session-centric navigation replacing file-tab-centric |
| Frontend layout | Replace `FileSidebar` with chat history sidebar, add right panel for linked files, new "My Files" page | ChatGPT-style layout |
| Frontend components | New shadcn/ui components: `sidebar`, `resizable`, `sheet` | Collapsible sidebar, resizable panels, file context panel |

---

## Recommended Stack Additions

### Frontend: shadcn/ui Components (3 new components)

| Component | Install Command | Purpose | Why Needed |
|-----------|----------------|---------|------------|
| Sidebar | `npx shadcn@latest add sidebar` | Collapsible left sidebar with chat history + "My Files" navigation | shadcn/ui's official Sidebar component provides SidebarProvider, collapsible state, cookie persistence, keyboard shortcuts, and mobile responsiveness out of the box. The current `FileSidebar` is a custom div -- this replaces it with a proper composable sidebar. |
| Resizable | `npx shadcn@latest add resizable` | Three-panel layout: left sidebar + main chat + right file context panel | Built on react-resizable-panels v4.5.0. Provides ResizablePanelGroup, ResizablePanel, ResizableHandle with drag mechanics, keyboard accessibility, min/max constraints, and layout persistence. Essential for the right sidebar file context panel that users can resize. |
| Sheet | `npx shadcn@latest add sheet` | Mobile-friendly slide-over panel for file context on small screens | Extends Dialog to display content as a side panel. Used as a responsive fallback -- on desktop the file context panel is a resizable panel, on mobile it becomes a Sheet slide-over. Also useful for file selection modals. |

**Rationale for shadcn/ui Sidebar over custom div:** The current `FileSidebar` is a plain 260px div. The v0.3 sidebar is more complex: it needs collapsible state, "New Chat" button, grouped chat history (Today/Yesterday/This Week), "My Files" navigation item, and responsive behavior. shadcn/ui's Sidebar component handles all of this with cookie-based state persistence and accessible keyboard navigation.

**Rationale for Resizable over fixed layout:** The v0.3 layout has three regions (left sidebar, main chat, right file panel). Fixed widths waste space on large screens and break on small ones. react-resizable-panels provides drag handles, min/max constraints, and persists user-preferred sizes via localStorage.

### Frontend: No New npm Dependencies Required

The resizable panels library (`react-resizable-panels`) is automatically installed by `npx shadcn@latest add resizable`. No manual npm install needed beyond the shadcn CLI commands above.

**What about Zustand?** Already installed (v5.0.11). The `persist` middleware (from `zustand/middleware`) will be used for the new session store to persist the active session ID across page reloads. No version change needed.

**What about next-themes?** Already installed (v0.4.6). Supports the light/dark mode toggle requirement.

**What about date formatting for chat history grouping?** Use native `Intl.RelativeTimeFormat` and `Date` methods. No date-fns or dayjs needed for simple "Today/Yesterday/This Week" grouping.

---

## Backend: No New Dependencies Required

### Database Schema Changes (SQLAlchemy + Alembic)

All schema changes use existing SQLAlchemy ORM and Alembic migrations. No new packages needed.

**New model: `ChatSession`**

```python
# backend/app/models/chat_session.py
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    files: Mapped[list["File"]] = relationship(
        secondary="session_files", back_populates="sessions"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
```

**New association table: `session_files`**

```python
# backend/app/models/session_file.py
session_files = Table(
    "session_files",
    Base.metadata,
    Column("session_id", ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", ForeignKey("files.id", ondelete="CASCADE"), primary_key=True),
    Column("linked_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)
```

**Why `secondary` Table (not Association Object):** The session-file relationship only needs the link itself plus a timestamp. No additional columns (like "role" or "order") are needed. SQLAlchemy's `secondary` pattern handles INSERT/DELETE automatically when objects are added/removed from the collection. If we later need ordering, we can add a `position` column and migrate to an Association Object pattern.

**Modified model: `ChatMessage`**

```python
# Modify existing chat_message.py
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    # ... existing fields ...
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        index=True, nullable=True  # Changed from NOT NULL
    )
    # file_id becomes nullable because messages belong to sessions,
    # not files. A message may reference no specific file (general chat).

    # New relationship
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
```

### API Route Changes (FastAPI)

No new packages. New router file + modifications to existing routers.

**New router: `backend/app/routers/sessions.py`**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /sessions/` | Create | Create new chat session (optionally with file_ids) |
| `GET /sessions/` | List | List user's chat sessions (for sidebar, ordered by updated_at desc) |
| `GET /sessions/{session_id}` | Detail | Get session with linked files |
| `DELETE /sessions/{session_id}` | Delete | Delete session and all its messages |
| `PATCH /sessions/{session_id}` | Update | Update session title |
| `POST /sessions/{session_id}/files` | Link | Link existing file(s) to session |
| `DELETE /sessions/{session_id}/files/{file_id}` | Unlink | Remove file from session |

**Modified router: `backend/app/routers/chat.py`**

| Current | New | Change |
|---------|-----|--------|
| `GET /chat/{file_id}/messages` | `GET /chat/{session_id}/messages` | Key lookup changes from file_id to session_id |
| `POST /chat/{file_id}/stream` | `POST /chat/{session_id}/stream` | Stream queries now scoped to session |
| `GET /chat/{file_id}/context-usage` | `GET /chat/{session_id}/context-usage` | Context is per-session |
| `POST /chat/{file_id}/trim-context` | `POST /chat/{session_id}/trim-context` | Trim is per-session |

### LangGraph State Changes

No new packages. Modify `ChatAgentState` and `agent_service.py`.

**Modified state: `ChatAgentState`**

```python
class ChatAgentState(TypedDict):
    # CHANGED: single file_id -> list of file_ids
    file_ids: list[str]          # Was: file_id: str
    file_paths: list[str]        # Was: file_path: str
    data_summaries: list[str]    # Was: data_summary: str
    data_profiles: list[str]     # Was: data_profile: str
    user_contexts: list[str]     # Was: user_context: str

    # CHANGED: session-based thread ID
    session_id: str              # New: replaces implicit file-based thread_id

    # UNCHANGED: all other fields remain the same
    user_id: str
    user_query: str
    generated_code: str
    # ... rest unchanged ...
```

**Thread ID change:**
```python
# v0.2 (current):
thread_id = f"file_{file_id}_user_{user_id}"

# v0.3 (new):
thread_id = f"session_{session_id}"
```

**Agent prompt changes:** The Coding Agent and Data Analysis Agent prompts must be updated to receive context from multiple files. The prompt template will iterate over all linked files' summaries and profiles.

**Execution changes:** The `execute_in_sandbox` node currently uploads one file. For multi-file, it must upload all linked files to the E2B sandbox. The coding agent's file-loading preamble must reference all files.

### Migration Strategy (Alembic)

Single Alembic migration with the following operations:

1. Create `chat_sessions` table
2. Create `session_files` junction table
3. Add `session_id` column to `chat_messages` (nullable initially)
4. Data migration: For each existing (user_id, file_id) pair in chat_messages, create a ChatSession and link the file
5. Set `session_id` NOT NULL after data migration
6. Make `chat_messages.file_id` nullable
7. Change `chat_messages.file_id` ondelete from CASCADE to SET NULL

---

## Frontend Architecture Changes

### State Management (Zustand)

**Replace `tabStore.ts` with `sessionStore.ts`:**

```typescript
// stores/sessionStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SessionStore {
  activeSessionId: string | null;
  setActiveSession: (sessionId: string | null) => void;
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      activeSessionId: null,
      setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
    }),
    { name: "spectra-session" }
  )
);
```

**Why persist middleware?** Unlike tabs (ephemeral), the active session should survive page reloads. User expects to return to their last conversation. Cookie-based persistence (via shadcn Sidebar's built-in mechanism) handles sidebar collapse state; localStorage (via Zustand persist) handles active session ID.

### TanStack Query Keys

```typescript
// New query key patterns:
["sessions"]                          // List all sessions
["sessions", sessionId]               // Single session detail
["sessions", sessionId, "files"]      // Files linked to session
["chat", "messages", sessionId]       // Messages for session (was fileId)
["files"]                             // All user files (unchanged)
["files", fileId, "summary"]          // File summary (unchanged)
```

### Routing (Next.js App Router)

```
Current:
  /dashboard                         -> DashboardPage (tab-based)

v0.3:
  /dashboard                         -> New chat (empty state with greeting)
  /dashboard/chat/[sessionId]        -> Chat session view
  /dashboard/files                   -> My Files management page
```

**Why dynamic routes for sessions?** Enables direct linking to conversations (shareable URLs later), browser back/forward navigation between sessions, and page-level code splitting. The current approach of switching state within a single page breaks browser navigation expectations.

### Component Tree (New Layout)

```
DashboardLayout
  +-- SidebarProvider (shadcn/ui)
  |   +-- AppSidebar (left)
  |   |   +-- SidebarHeader: "Spectra" logo + "New Chat" button
  |   |   +-- SidebarContent
  |   |   |   +-- SidebarGroup: "Chat History"
  |   |   |   |   +-- ChatHistoryList (grouped by Today/Yesterday/This Week)
  |   |   |   +-- SidebarGroup: "Navigation"
  |   |   |       +-- "My Files" nav item
  |   |   +-- SidebarFooter: User menu
  |   +-- SidebarInset (main content)
  |       +-- ResizablePanelGroup (horizontal)
  |           +-- ResizablePanel (main chat area)
  |           |   +-- ChatInterface (modified for session-centric)
  |           +-- ResizableHandle
  |           +-- ResizablePanel (right sidebar: linked files)
  |               +-- LinkedFilesPanel
  |                   +-- FileChip per linked file
  |                   +-- "Add File" button
  |                   +-- FileContextDrawer (expandable per file)
```

---

## Supporting Libraries (Already Installed)

| Library | Current Version | Role in v0.3 | Notes |
|---------|----------------|--------------|-------|
| `zustand` | ^5.0.11 | Session store with `persist` middleware | No change needed. Persist middleware built-in. |
| `@tanstack/react-query` | ^5.90.20 | Session queries, file queries, message queries | No change needed. New query keys for sessions. |
| `radix-ui` | ^1.4.3 | Primitives for new shadcn components (sidebar, resizable, sheet) | Already using unified package. New components auto-import from it. |
| `lucide-react` | ^0.563.0 | Icons for sidebar, file chips, navigation | New icons: `MessageSquare`, `FolderOpen`, `Link`, `Plus`, `PanelRightOpen` |
| `next-themes` | ^0.4.6 | Light/dark mode toggle | Already installed. Wire into sidebar footer settings. |
| `sonner` | ^2.0.7 | Toast notifications for file link/unlink actions | Already installed. No change needed. |
| `react-dropzone` | ^14.4.0 | File upload (drag & drop in chat + My Files page) | Already installed. Reuse `FileUploadZone` component. |
| `class-variance-authority` | ^0.7.1 | Variant styling for new components | Already installed. Used by shadcn/ui components. |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Left sidebar | shadcn/ui Sidebar | Custom div (current approach) | Current FileSidebar is a plain div with no collapse, no responsive behavior, no keyboard shortcuts. shadcn Sidebar provides all of these plus cookie state persistence. |
| Right panel | shadcn/ui Resizable + Panel | Fixed-width div | Users need control over panel width. Fixed layout wastes space on wide screens. Resizable is more professional. |
| Right panel (mobile) | shadcn/ui Sheet | Always-visible panel | On mobile, a fixed right panel would leave no room for chat. Sheet slides over as needed. |
| Session state | Zustand persist | URL-only (no store) | Active session ID in URL handles routing, but sidebar highlight state, collapse state, etc. benefit from Zustand. Both are needed: URL for routing, Zustand for UI state. |
| Chat history grouping | Native Intl.RelativeTimeFormat | date-fns / dayjs | "Today", "Yesterday", "This Week" grouping is 10 lines of native JS. No dependency needed for this. |
| File-session relationship | SQLAlchemy secondary table | Association Object | No extra columns needed beyond FK pair + timestamp. secondary is simpler and auto-manages inserts/deletes. |
| Chat session routing | Dynamic routes `/chat/[sessionId]` | Client-side state switching | Dynamic routes enable browser back/forward, deep linking, and page-level code splitting. State switching (current tab approach) breaks navigation. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `react-sidebar` or similar npm package | shadcn/ui Sidebar covers all needs natively with Radix primitives | `npx shadcn@latest add sidebar` |
| `date-fns` or `dayjs` | Only need simple date grouping (Today/Yesterday/etc.) | Native `Intl.RelativeTimeFormat` + `Date` |
| `react-dnd` or drag-and-drop library | No drag reordering of files or sessions in v0.3 requirements | Not needed |
| `socket.io` or WebSocket library | SSE streaming (existing) handles all real-time needs | Existing `sse-starlette` + `useSSEStream` hook |
| `react-router` | Next.js App Router handles all routing | Next.js built-in routing |
| Additional ORM library | SQLAlchemy 2.0 handles all new models/relationships | Existing SQLAlchemy |
| Redis for session state | PostgreSQL checkpointing + Zustand persist handle everything | Existing AsyncPostgresSaver + Zustand |
| `@tanstack/react-virtual` | Chat message lists won't be long enough to need virtualization in v0.3 | Standard scroll. Reconsider if sessions exceed 500+ messages. |

---

## Installation

### Frontend (3 shadcn/ui components)

```bash
cd frontend
npx shadcn@latest add sidebar
npx shadcn@latest add resizable
npx shadcn@latest add sheet
```

These commands will:
1. Add component files to `src/components/ui/`
2. Install `react-resizable-panels` as a dependency (for Resizable)
3. No other npm dependencies added

### Backend (no new packages)

```bash
# No new pip installs needed for v0.3
# All schema changes use existing SQLAlchemy + Alembic
```

### Database Migration

```bash
cd backend
alembic revision --autogenerate -m "add_chat_sessions_and_multi_file_support"
alembic upgrade head
```

---

## Integration Points

### 1. Session Creation Flow

```
User clicks "New Chat" -> POST /sessions/ -> Returns session_id
  -> Frontend navigates to /dashboard/chat/{session_id}
  -> Empty chat with greeting + "Link a file" prompt
  -> User uploads/links file -> POST /sessions/{session_id}/files
  -> File onboarding runs (existing flow)
  -> Chat ready for queries
```

### 2. Multi-File Agent Context

```
User sends query in session with 3 linked files
  -> Backend loads all 3 files' data_summary + data_profile
  -> Builds combined prompt: "You have access to 3 datasets: [file1: summary], [file2: summary], [file3: summary]"
  -> Agent generates code that loads all 3 files
  -> E2B sandbox receives all 3 data files
  -> Code can reference df1, df2, df3 (or named by filename)
```

### 3. Thread ID Migration

```
v0.2 checkpoints: thread_id = "file_{file_id}_user_{user_id}"
v0.3 checkpoints: thread_id = "session_{session_id}"

Migration: Old checkpoints become orphaned (acceptable -- users start fresh sessions).
No need to migrate checkpoint data.
```

### 4. Chat History Sidebar

```
GET /sessions/ returns:
[
  { id, title, updated_at, file_count, preview_message }
]

Frontend groups by date:
  Today: [session1, session2]
  Yesterday: [session3]
  This Week: [session4, session5]

Title auto-generated from first user message (truncated)
  or explicit rename via PATCH /sessions/{id}
```

---

## Configuration Changes

### Backend Settings (app/config.py)

```python
# New settings for multi-file support
max_files_per_session: int = 10  # Limit linked files per session
max_total_file_size_mb: int = 100  # Total file size limit per session
session_title_max_length: int = 100  # Auto-generated title length
```

### Frontend Environment

No new environment variables needed. All API endpoints use the same base URL.

---

## Version Compatibility

| Existing Package | Current Version | v0.3 Compatible | Notes |
|-----------------|-----------------|-----------------|-------|
| Next.js | 16.1.6 | Yes | Dynamic routes supported |
| React | 19.2.3 | Yes | No React-specific changes |
| shadcn/ui (radix-ui) | 1.4.3 | Yes | New components install via CLI |
| zustand | 5.0.11 | Yes | persist middleware available in 5.x |
| @tanstack/react-query | 5.90.20 | Yes | New query keys, same patterns |
| SQLAlchemy | 2.0+ | Yes | Many-to-many secondary table pattern supported |
| FastAPI | 0.115+ | Yes | New routers, same patterns |
| LangGraph | 1.0.7+ | Yes | State changes are backward-compatible |
| langgraph-checkpoint-postgres | 2.0.0+ | Yes | Thread ID format change only |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Alembic data migration corrupts existing messages | Low | High | Write migration as reversible. Test on DB copy first. Back up production DB before running. |
| Multi-file agent prompts exceed context window | Medium | Medium | Implement summary truncation. Limit files per session (10). Monitor token counts per prompt. |
| E2B sandbox file upload time increases with multiple files | Low | Low | Files are small (CSV/Excel). Upload in parallel via threads. Set reasonable timeout. |
| shadcn Sidebar conflicts with existing layout | Low | Low | Full layout rewrite planned anyway. No incremental integration concerns. |
| Old LangGraph checkpoints break with new thread_id format | None | None | Old checkpoints simply become unreachable. New sessions create new checkpoints. |

---

## Sources

**shadcn/ui Components:**
- [Sidebar Component](https://ui.shadcn.com/docs/components/radix/sidebar) -- Official shadcn/ui documentation
- [Resizable Component](https://ui.shadcn.com/docs/components/radix/resizable) -- Built on react-resizable-panels
- [Sheet Component](https://ui.shadcn.com/docs/components/radix/sheet) -- Side panel overlay
- [Sidebar Building Blocks](https://ui.shadcn.com/blocks/sidebar) -- Pre-built sidebar examples
- [February 2026 Radix UI Unified Package](https://ui.shadcn.com/docs/changelog/2026-02-radix-ui) -- Unified import pattern

**react-resizable-panels:**
- [npm: react-resizable-panels](https://www.npmjs.com/package/react-resizable-panels) -- v4.5.0 (current)
- [GitHub: bvaughn/react-resizable-panels](https://github.com/bvaughn/react-resizable-panels) -- Source and API docs

**Zustand:**
- [Persist Middleware](https://zustand.docs.pmnd.rs/middlewares/persist) -- Official Zustand v5 documentation

**SQLAlchemy:**
- [Many-to-Many Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html) -- Secondary table pattern
- [Association Object Pattern](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many) -- When extra columns needed

**LangGraph:**
- [Thread-Based State Management](https://medium.com/@vinodkrane/mastering-persistence-in-langgraph-checkpoints-threads-and-beyond-21e412aaed60) -- Thread isolation patterns
- [State Management Best Practices](https://medium.com/@bharatraj1918/langgraph-state-management-part-1-how-langgraph-manages-state-for-multi-agent-workflows-da64d352c43b) -- Multi-agent state

**Next.js:**
- [Dynamic Route Segments](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes) -- App Router dynamic routes

---
*Stack research for: Spectra v0.3 Multi-File Conversation Support*
*Researched: 2026-02-11*
*Confidence: HIGH -- All recommendations use existing dependencies or official shadcn/ui components. No speculative packages.*
