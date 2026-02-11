# Project Research Summary

**Project:** Spectra v0.3 - Multi-File Conversation Support
**Domain:** AI-powered data analytics platform (chat-session-centric architecture transformation)
**Researched:** 2026-02-11
**Confidence:** HIGH

## Executive Summary

Spectra v0.3 represents the most architecturally significant change since the platform's inception, transforming from a file-tab-centric model (where each uploaded file has its own isolated chat) to a chat-session-centric model (ChatGPT-style conversations that can reference multiple files). This is not merely a UI restructure -- it requires changes at every layer: database schema, LangGraph agent state, E2B sandbox execution, API endpoints, and frontend state management.

The recommended approach leverages Spectra's existing clean separation of concerns. The current stack (FastAPI, PostgreSQL, SQLAlchemy, LangGraph, E2B, Next.js 16, React 19, TanStack Query, shadcn/ui, Zustand) requires zero new backend dependencies and only three new shadcn/ui components on the frontend (Sidebar, Resizable, Sheet). The transformation is primarily architectural and schema-level, not a library addition problem. The critical path is: (1) database schema migration with LangGraph checkpoint thread_id migration, (2) multi-file agent state extension with context assembly service, (3) frontend layout restructure with session-based navigation.

The highest risk is data loss during migration. The LangGraph checkpoint tables store conversation memory keyed by `thread_id = file_{file_id}_user_{user_id}`. This thread_id format must change to `session_{session_id}_user_{user_id}` while preserving conversation context, or all existing memory is silently lost. The second critical risk is multi-file context overflow: with 5 files at ~800 tokens of metadata each, the agent prompt can reach 4K tokens before a single user query is processed, leaving insufficient room for conversation history within the 12K token context window. Mitigation: tiered metadata inclusion (full profile for primary file, compact summaries for secondary files) and a hard 10-file limit per session.

## Key Findings

### Recommended Stack

The v0.3 transformation requires **zero new backend dependencies** and minimal frontend additions. The existing stack is validated in production (96 requirements across v0.1 and v0.2) and well-suited for this architectural change.

**Core technologies (unchanged):**
- FastAPI 0.115+ -- handles new `/sessions/*` router, session-based `/chat/*` endpoints
- PostgreSQL + SQLAlchemy 2.0+ -- new `chat_sessions` table, `session_files` junction table, modified `chat_messages` FK from `file_id` to `session_id`
- LangGraph 1.0.7+ -- state changes to support multi-file context (lists instead of singular file fields)
- E2B Sandbox -- extends to upload N files per execution, creates named DataFrames (`df_sales`, `df_customers`) instead of single `df`
- Next.js 16 + React 19 -- dynamic routes (`/dashboard/chat/[sessionId]`) replace tab-based navigation

**Frontend additions (3 shadcn/ui components):**
- **Sidebar** (via `npx shadcn@latest add sidebar`) -- replaces current `FileSidebar` with collapsible chat history sidebar featuring SidebarProvider, cookie-based state persistence, and keyboard shortcuts
- **Resizable** (via `npx shadcn@latest add resizable`) -- three-panel layout: left sidebar + main chat + right file context panel. Built on react-resizable-panels v4.5.0 with drag mechanics and layout persistence
- **Sheet** (via `npx shadcn@latest add sheet`) -- mobile-friendly slide-over panel for file context on small screens

**Supporting libraries (already installed):**
- Zustand 5.0.11 with `persist` middleware -- new `useChatSessionStore` replaces `useTabStore`, persists active session ID across page reloads
- TanStack Query 5.90.20 -- new query keys `["sessions"]`, `["sessions", sessionId, "messages"]`
- Radix UI 1.4.3 -- unified package already supports new shadcn components

**Version compatibility:** All existing packages (Next.js 16.1.6, React 19.2.3, SQLAlchemy 2.0+, FastAPI 0.115+) are compatible with v0.3 changes. No version upgrades needed.

### Expected Features

**Must have (table stakes):**
- **Chat session as primary entity** -- ChatGPT, Claude, Gemini all center on "conversations," not files. Users expect to create a chat, then bring context into it. File-first is the exception, not the norm.
- **Chat history sidebar** -- chronological grouping (Today, Yesterday, This Week, This Month, Older) is universal across AI chat tools and formalized by PatternFly as a standard component pattern
- **File linking to chat sessions** -- users must attach files to conversations. At minimum: select from previously uploaded files. At least one file required before chatting.
- **Session title auto-generation** -- ChatGPT auto-titles conversations from first message. Users expect this.
- **"My Files" management screen** -- when files are decoupled from conversations, users need a dedicated place to see all their files (Google Drive model)
- **Preserve existing conversation memory** -- v0.2 has multi-turn memory via LangGraph PostgreSQL checkpointing. v0.3 must preserve this.

**Should have (competitive differentiators):**
- **Cross-file analysis (joins/merges)** -- ask "Compare sales data from Q1.csv with Q2.csv" and get merged analysis. Julius AI supports this. This is the killer feature that justifies the multi-file architecture.
- **Right sidebar file context panel** -- dedicated panel showing linked files with summaries, column info, row counts. Always visible during chat.
- **Drag-and-drop file onto chat** -- drop a file directly onto the chat area to upload and link in one step (ChatGPT supports this)
- **Light/dark mode toggle** -- explicitly requested in requirements, modern UX expectation

**Defer (v0.3.1 or v0.4):**
- Session-level multi-file query suggestions (requires cross-file schema analysis)
- Smart file suggestion in empty chat (low priority UX polish)
- Advanced cross-file join intelligence (complex prompt engineering)

**Anti-features (explicitly avoid):**
- **Automatic cross-file joins without user intent** -- silently merging datasets leads to wrong results. Schema mismatches, duplicate columns, Cartesian products.
- **Real-time collaborative editing** -- multi-user on same session adds massive complexity. Not in requirements.
- **Folder/directory organization for files** -- over-engineering file management. Users will have 5-50 files, not thousands.
- **Conversation branching/forking** -- extremely complex UX and data model. Not requested.
- **Embedding/vector search across files** -- architecturally different from structured data analysis. Different product direction.

### Architecture Approach

The v0.3 architecture transforms the data model from `User --1:N--> File --1:N--> ChatMessage` to `User --1:N--> ChatSession --M:N--> File` with `ChatSession --1:N--> ChatMessage`. This requires changes at every layer while preserving the clean separation of concerns that makes the migration feasible without a full rewrite.

**Major components:**

1. **Database Schema (NEW)**
   - `ChatSession` model -- first-class chat entity with `id`, `user_id`, `title`, `created_at`, `updated_at`
   - `SessionFile` association -- many-to-many join between sessions and files with `linked_at` timestamp and optional `alias` (DataFrame variable name)
   - `ChatMessage` FK change -- from required `file_id` to required `session_id`, messages now belong to sessions not files
   - Migration strategy: two-phase Alembic migration (Phase 1: add tables + nullable `session_id`, Phase 2: data migration + thread_id update + drop `file_id`)

2. **Agent Pipeline (MODIFIED)**
   - `ContextAssembler` service -- builds aggregated multi-file context from session files. Auto-detects join hints by finding matching column names across files.
   - `ChatAgentState` extension -- singular `file_id`, `file_path`, `data_summary` become lists: `file_contexts: list[dict]`, `combined_data_summary: str`, `combined_data_profile: str`
   - Thread ID change -- from `file_{file_id}_user_{user_id}` to `session_{session_id}_user_{user_id}`
   - E2B sandbox multi-file execution -- uploads N files, creates named DataFrames (`df_sales`, `df_customers`), backward-compatible `df` alias for single-file sessions
   - Coding Agent prompt -- receives multi-file profile JSON with `join_hints` array, generates code using named DataFrames

3. **API Endpoints (NEW + MODIFIED)**
   - **NEW:** `/sessions/*` router -- CRUD for chat sessions, link/unlink files
   - **MODIFIED:** `/chat/{file_id}/*` becomes `/chat/sessions/{session_id}/*` (6 endpoints)
   - Session list response -- includes `file_count`, `message_count`, `last_message_preview` for sidebar

4. **Frontend Structure (RESTRUCTURED)**
   - Layout: `ChatSidebar` (left, 260px) + Main Content + `LinkedFilesPanel` (right, 240px, conditional)
   - State: `useChatSessionStore` replaces `useTabStore`, TanStack Query keys change to `["sessions", sessionId, "messages"]`
   - Routes: `/dashboard` (empty state) + `/dashboard/chat/[sessionId]` (chat view) + `/dashboard/files` (file management)
   - Components: `ChatSidebar` with history grouping, `LinkedFilesBar` showing file badges, `FileLinkModal` for selecting existing files

**Key patterns:**
- **Context Assembler** -- dedicated service for multi-file aggregation (keeps `agent_service` from becoming a god function)
- **Session-First, Files-Second** -- sessions start empty, files linked explicitly before first AI query (matches ChatGPT-style UX)
- **Backward-Compatible DataFrame Naming** -- single-file sessions get both named DataFrame and generic `df` alias (existing patterns continue working)
- **Additive Two-Phase Migration** -- Phase 1 adds new tables/columns (nullable), Phase 2 migrates data and removes old columns (reduces blast radius)
- **File Limit Enforcement** -- cap at 10 files per session at API level (prevents context window overflow and sandbox timeouts)

**Build order (dependency-aware):**
```
Phase A: Database Foundation (sequential, critical path)
  1-7: ChatSession + SessionFile models → Alembic migrations → ChatSessionService → API

Phase B: Agent Pipeline (depends on A.1-A.3, sequential)
  8-14: ContextAssembler → ChatAgentState changes → Prompt updates → E2B multi-file → Agent service refactor

Phase C: Frontend Structure (can start parallel with B)
  15-19: Route structure → ChatSessionStore → Hooks → ChatSidebar → Layout restructure

Phase D: Frontend Features (depends on C + B.13)
  20-27: ChatView → LinkedFilesBar/Panel → FileManagerPage → FileLinkModal → Hook refactors

Phase E: Polish
  28-31: Auto-title → Empty state → Light/dark mode → Migration testing
```

**Critical path:** A.1 → A.2 → A.3 → B.8 → B.9 → B.12 → B.13 → D.20 → D.26

### Critical Pitfalls

1. **Data Migration Destroys LangGraph Checkpoint Thread IDs**
   - LangGraph stores conversation memory in its own tables (`checkpoint`, `checkpoint_blobs`) keyed by `thread_id`. Current format: `file_{file_id}_user_{user_id}`. New format: `session_{session_id}_user_{user_id}`.
   - If migration creates new sessions but does NOT update thread_ids in LangGraph tables, all existing conversation memory is silently lost (Manager Agent cannot route to MEMORY_SUFFICIENT for existing conversations).
   - Prevention: Migration must UPDATE thread_id in LangGraph tables alongside application table migration. Write verification query counting checkpoints before/after.

2. **Chat Messages Table Migration Breaks Cascade Delete**
   - Currently: `ChatMessage.file_id` FK with `cascade="all, delete-orphan"`. Deleting a file cascades to delete all its messages.
   - In v0.3: messages belong to sessions (M:N with files). Deleting a file should NOT cascade to delete session messages (would destroy analysis of other files in same session).
   - Prevention: Messages move from `file_id` FK to `session_id` FK. Define clear cascade rules: delete session → cascade delete messages; delete file → remove from junction table only.

3. **Agent State Assumes Single File Context -- Multi-File Breaks Code Generation**
   - Current pipeline assumes singular `file_id`, `file_path`, `data_summary`. Evidence: `execute_in_sandbox` uploads ONE file as `df`, Coding Agent prompt uses singular `{data_profile}`.
   - With 3 linked files, system must load 3 data profiles, upload 3 files, generate code referencing `df_sales`, `df_customers`, `df_products`.
   - Prevention: Extend `ChatAgentState` to support lists. Build compact multi-file context block (~500 tokens total) with full profiles available on-demand. Keep backward compatibility: single-file sessions continue using `df`.

4. **E2B Sandbox Memory Overflow with Multiple Large Files**
   - E2B sandboxes have 512 MiB RAM by default. A 30MB CSV consumes 100-300MB in pandas (object dtype overhead). Three such files require 300-900MB -- exceeding sandbox limit, causing MemoryError.
   - Prevention: Pre-flight memory estimation (`sum(file_sizes) * 5` against sandbox RAM). Generate code with selective column loading (`pd.read_csv(file, usecols=[...])`). Hard file size budget per session.

5. **Frontend Navigation Restructure Breaks SSE Stream Lifecycle**
   - Current: tab-based UI hides/shows `ChatInterface` without unmounting. New: sidebar navigation via Next.js App Router unmounts page component on route change.
   - If SSE stream is active during session switch, stream aborts before save logic runs. Messages not saved, checkpoint inconsistent.
   - Prevention: Design chat session view as layout-level component (persists across navigation) OR show confirmation dialog before session switch during active streaming. Server-side safety net: save progress with `status: "interrupted"` on disconnect.

**Additional moderate pitfalls:**
- Context window token explosion (multi-file metadata can consume 4K tokens before first user query)
- Thread ID collision when same file appears in multiple sessions (fixed by consistent `session_{id}` format)
- API route structure break (`/chat/{file_id}/*` → `/chat/{session_id}/*` requires atomic frontend/backend update)
- Zustand TabStore replacement creates state synchronization bugs (single commit for all imports, delete old store)
- Query suggestions break for multi-file sessions (merge suggestions or use most-recent file's)

## Implications for Roadmap

Based on research, the critical dependency graph and pitfall severity analysis suggest a **4-phase sequential roadmap** with optional polish phase:

### Phase 1: Database Foundation & Migration
**Rationale:** The entire v0.3 transformation depends on the data model change. This phase is the foundation for all subsequent work. Must be completed first because both backend agent changes (Phase 2) and frontend changes (Phase 3) require the new schema to exist.

**Delivers:**
- `chat_sessions` and `session_files` tables
- Alembic migration infrastructure (if not already set up)
- Data migration from v0.2 file-chat model to v0.3 session model
- LangGraph checkpoint thread_id migration (CRITICAL: prevents conversation memory loss)
- Session CRUD APIs (`POST /sessions`, `GET /sessions`, etc.)
- File linking/unlinking APIs

**Addresses:**
- Table stakes: "Chat session as primary entity"
- Architecture: Database schema transformation
- Pitfall 1: LangGraph checkpoint thread_id orphaning
- Pitfall 2: Chat messages cascade delete topology

**Avoids:**
- Pitfall 16: Manual schema migration without Alembic versioning
- Pitfall 7: Thread ID collision across sessions (centralize thread_id construction)

**Research flag:** STANDARD PATTERNS -- database migration with Alembic is well-documented. LangGraph checkpoint table structure is documented in official persistence docs. SQLAlchemy many-to-many via association table is standard pattern. No additional research needed.

---

### Phase 2: Agent System Enhancement (Multi-File Support)
**Rationale:** Extending the LangGraph agent pipeline to support multi-file context is the most technically complex part of v0.3. This phase must follow database migration (depends on `ChatSession` model existing) but can precede frontend restructure. Building the backend capability first allows testing multi-file agent behavior independently of UI changes.

**Delivers:**
- `ContextAssembler` service (aggregates multi-file context from session files)
- `ChatAgentState` schema changes (multi-file fields)
- E2B sandbox multi-file execution (`execute_multi_file` method)
- Coding Agent, Code Checker, Manager Agent prompt updates for multi-file awareness
- `agent_service.run_chat_query_stream` refactor (session-based, uses ContextAssembler)
- Chat router refactor (`/chat/sessions/{session_id}/stream`)
- Thread ID pattern migration to `session_{session_id}_user_{user_id}`

**Uses:**
- Existing LangGraph 1.0.7+ (state changes backward-compatible)
- Existing E2B runtime (extends with new method, keeps old method for compatibility)
- Existing SQLAlchemy (ContextAssembler queries session files via relationships)

**Implements:**
- Architecture: Multi-file agent state, context assembly service, named DataFrame sandbox execution
- Differentiator: Cross-file analysis foundation (joins/merges)

**Addresses:**
- Pitfall 3: Single-file assumptions in agent state (extend to lists, build compact context)
- Pitfall 4: E2B sandbox memory overflow (pre-flight estimation, selective column loading)
- Pitfall 6: Context window token explosion (tiered metadata, compressed profiles)
- Pitfall 11: Deleted file orphans in code history (clear stale state on unlink)

**Avoids:**
- Anti-pattern: Storing file bytes in LangGraph state (use metadata only, read bytes at execution time)
- Anti-pattern: Concatenating all files into one DataFrame (preserve semantic distinction)

**Research flag:** NEEDS DEEPER RESEARCH -- multi-file prompt engineering patterns for coding agents, cross-file join hint detection strategies, memory estimation heuristics for pandas DataFrames. Recommend targeted `/gsd:research-phase` on "multi-file code generation patterns for data analytics LLMs" and "E2B sandbox resource limits with multiple file uploads."

---

### Phase 3: Frontend Restructure (Session-Centric UX)
**Rationale:** Frontend restructure can begin in parallel with Phase 2 (agent work) but converges when chat functionality is integrated. The sidebar navigation and layout changes are independent of agent internals until the point where chat messages need to be displayed. Must come after database foundation (Phase 1) because it depends on session APIs existing.

**Delivers:**
- New route structure: `/dashboard` (empty) + `/dashboard/chat/[sessionId]` + `/dashboard/files`
- `ChatSessionStore` (Zustand, replaces `useTabStore`)
- `useChatSessions` hooks (TanStack Query for session CRUD)
- `ChatSidebar` component (left sidebar with chat history, "New Chat", "My Files")
- Layout restructure (sidebar + main + optional right panel for linked files)
- `ChatView` (session-based `ChatInterface`)
- `LinkedFilesBar` and `LinkedFilesPanel` (show linked files with context)
- `FileManagerPage` (/dashboard/files)
- `FileLinkModal` (select existing files to link to session)
- `useChatMessages` refactor (sessionId-based)
- `useSSEStream` refactor (session-based URL)
- Upload-and-chat flow integration

**Uses:**
- shadcn/ui Sidebar, Resizable, Sheet components (new installations)
- Zustand 5.0.11 with persist middleware (already installed)
- TanStack Query 5.90.20 (new query keys)
- Next.js 16 dynamic routes (already supported)

**Implements:**
- Architecture: Frontend session-centric layout, Zustand session store, TanStack Query session hooks
- Table stakes: Chat history sidebar, file linking UX, "My Files" screen, drag-and-drop file upload

**Addresses:**
- Pitfall 5: SSE stream lifecycle on navigation (layout-level component or confirmation dialog)
- Pitfall 8: API route structure break (backend and frontend updated together)
- Pitfall 9: Zustand store replacement state sync (single commit, delete old store)
- Pitfall 10: Query suggestions for multi-file sessions (merge suggestions from linked files)
- Pitfall 12: Hardcoded localhost URL (centralize base URL)

**Avoids:**
- Pitfall 13: Chat history sidebar performance (paginate sessions, load minimal metadata)
- Pitfall 14: File list dual-mode confusion (prop-driven onSelect callback)

**Research flag:** STANDARD PATTERNS -- Next.js App Router dynamic routes, Zustand store migration, shadcn/ui component integration are all well-documented with official examples. SSE stream cleanup in React components has established patterns. No additional research needed.

---

### Phase 4: Integration & Testing
**Rationale:** After database, backend agent, and frontend are independently built, this phase integrates all three layers and validates that existing v0.1/v0.2 functionality (96 validated requirements) continues working. This is the phase where end-to-end multi-file flows are tested and regressions are caught.

**Delivers:**
- End-to-end multi-file analysis testing (upload 2+ files, link to session, cross-file query)
- Migration validation (verify old conversations restored with correct context)
- Regression testing (v0.1 and v0.2 requirement validation in new architecture)
- Performance testing (context window usage with 5+ files, sandbox execution time)
- Session title auto-generation (LLM-based or first-query truncation)
- Error handling for edge cases (session with no files, deleted file references in code)
- Cleanup script for orphaned LangGraph checkpoints (old `file_*` thread_ids)

**Addresses:**
- Regression risk: "Each file has its own chat tab" (v0.1 File-10) -- verify files create their own session
- Regression risk: "Chat history persists per file across browser sessions" (v0.1 AI-07) -- verify messages in correct session
- Regression risk: "Independent conversation memory per file tab" (v0.2 Memory-04) -- verify sessions have independent checkpoints
- Regression risk: "New chat tabs display 5-6 query suggestions" (v0.2 Suggest-01) -- verify suggestions appear when file linked

**Research flag:** NO RESEARCH NEEDED -- this is implementation testing, not architecture research.

---

### Phase 5: Polish & Dark Mode (Optional)
**Rationale:** After core functionality is stable, visual polish and light/dark mode can be added. Implementing dark mode after layout restructure is complete avoids compounding CSS complexity (Pitfall 15).

**Delivers:**
- Light/dark mode toggle (Tailwind dark mode classes, next-themes integration)
- Empty state UX refinements (greeting message, file suggestion cards)
- Session rename UX (inline edit in sidebar)
- Smart file suggestion in empty chat (show recently uploaded files)
- UI polish (animations, loading states, responsive refinements)

**Addresses:**
- Should-have: "Light/dark mode toggle"
- Table stakes: Session title auto-generation (if not completed in Phase 4)

**Avoids:**
- Pitfall 15: Dark mode + layout restructure CSS conflict (implement after layout is stable)

**Research flag:** STANDARD PATTERNS -- Tailwind dark mode with next-themes is well-documented in shadcn/ui setup guides. No research needed.

---

### Phase Ordering Rationale

**Why this order:**
- **Database first (Phase 1)** because both backend (Phase 2) and frontend (Phase 3) depend on the new schema existing. Migration must happen before any code references `ChatSession` model.
- **Backend agent before frontend (Phase 2 → Phase 3)** allows testing multi-file agent behavior independently. Frontend can be built against stable backend APIs.
- **Integration after both (Phase 4)** validates that independently built layers work together and existing functionality is preserved.
- **Polish last (Phase 5)** avoids compounding complexity. Dark mode after layout restructure prevents CSS conflicts.

**Why this grouping:**
- **Phase 1** is purely data model -- no agent or UI work. Clean separation.
- **Phase 2** is agent pipeline only -- can be tested with direct API calls before UI exists.
- **Phase 3** is frontend structure -- can be built against API contracts even if full agent implementation is incomplete.
- **Phase 4** is integration -- brings all layers together.
- **Phase 5** is additive polish -- no architectural changes.

**How this avoids pitfalls:**
- The two-phase database migration (add schema → migrate data) reduces blast radius (Pitfall 1, Pitfall 2).
- Building agent multi-file support in isolation allows memory estimation testing before UI is built (Pitfall 4).
- Restructuring frontend after backend APIs are stable prevents frontend-backend contract mismatches (Pitfall 8).
- Testing SSE stream lifecycle during integration catches navigation-related state issues (Pitfall 5).

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Agent System Enhancement):** Multi-file prompt engineering is a niche domain with sparse documentation. Specific research needed:
  - How to structure coding agent prompts for multi-DataFrame pandas code generation
  - Cross-file join hint detection strategies (beyond basic column name matching)
  - Token budget allocation strategies when context includes N file profiles
  - Memory estimation heuristics for pandas DataFrame size prediction
  - Recommend: `/gsd:research-phase` on "multi-file code generation for data analytics LLMs" and "E2B sandbox resource optimization"

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Database Foundation):** Alembic migrations, SQLAlchemy many-to-many relationships, PostgreSQL FK changes -- all well-documented with official guides and established patterns.
- **Phase 3 (Frontend Restructure):** Next.js App Router dynamic routes, Zustand store migration, shadcn/ui component integration, TanStack Query key patterns -- extensive official documentation and community examples.
- **Phase 4 (Integration & Testing):** No research needed -- implementation testing phase.
- **Phase 5 (Polish & Dark Mode):** Tailwind dark mode, next-themes -- standard patterns in shadcn/ui documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations use existing validated dependencies (v0.1/v0.2 production stack) or official shadcn/ui components. Zero speculative packages. Version compatibility verified across all libraries. |
| Features | MEDIUM-HIGH | Feature landscape based on ChatGPT, Claude, Julius AI UX patterns (well-documented) and PatternFly component standards. Cross-file analysis patterns validated via Julius AI documentation. Minor uncertainty around optimal query suggestion merging for multi-file sessions. |
| Architecture | HIGH | Based on direct codebase analysis (all source files inspected with line-number references). LangGraph state management patterns verified via official persistence docs. SQLAlchemy many-to-many via association table is standard pattern. Next.js App Router layout/page semantics confirmed in official docs. |
| Pitfalls | HIGH | All critical pitfalls verified against actual codebase with line-number references. LangGraph checkpoint thread_id structure confirmed in official docs. E2B sandbox memory limits (512 MiB default) from official pricing page. PostgreSQL migration best practices from multiple verified sources (Miro Engineering, Shelf.io Engineering). SSE stream lifecycle issues confirmed in Next.js GitHub discussions. |

**Overall confidence:** HIGH

### Gaps to Address

**Multi-file prompt engineering strategies:**
- Research identified the pattern (extend state to lists, build compact context block) but optimal prompt structure for cross-file join generation needs validation during implementation.
- How to handle: Phase 2 includes targeted research on multi-file coding agent prompts. Start with basic approach (list all files with join hints), iterate based on actual LLM performance.

**Memory estimation heuristics:**
- Rule of thumb "CSV size * 3-5x for pandas memory" is a starting point but may not be accurate for all data types (heavy object dtype columns can exceed 5x).
- How to handle: Phase 2 includes empirical testing with real datasets. Build conservative estimate first (5x multiplier), refine based on sandbox execution logs.

**Context window budget allocation:**
- Research confirms multi-file metadata can consume 4K tokens, but optimal allocation strategy (which files get full profiles vs summaries) needs testing with real conversation flows.
- How to handle: Phase 2 implements tiered metadata (full profile for first file, compact summaries for others). Monitor context usage in Phase 4 integration testing, adjust strategy if needed.

**SSE stream cleanup on navigation:**
- Next.js documentation confirms pages unmount on navigation, but optimal pattern (layout-level component vs confirmation dialog vs server-side save-on-disconnect) needs UX validation.
- How to handle: Phase 3 implements server-side safety net (save progress on disconnect) as backstop. Frontend pattern (layout-level vs dialog) decided during implementation based on UX testing.

**Session title auto-generation:**
- Two approaches identified (truncate first user query vs LLM-based summarization) but optimal pattern for data analytics queries unclear.
- How to handle: Phase 4 implements simple approach first (truncate first query to 50 chars), evaluate if LLM summarization adds value during testing.

## Sources

### Primary (HIGH confidence)

**From STACK.md:**
- shadcn/ui Components: https://ui.shadcn.com/docs/components/radix/sidebar, /resizable, /sheet -- official shadcn/ui documentation
- react-resizable-panels: https://www.npmjs.com/package/react-resizable-panels (v4.5.0), https://github.com/bvaughn/react-resizable-panels
- Zustand Persist Middleware: https://zustand.docs.pmnd.rs/middlewares/persist -- official Zustand v5 documentation
- SQLAlchemy Many-to-Many: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html -- official SQLAlchemy 2.0 docs
- LangGraph State Management: https://medium.com/@vinodkrane/mastering-persistence-in-langgraph-checkpoints-threads-and-beyond-21e412aaed60
- Next.js Dynamic Routes: https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes

**From FEATURES.md:**
- PatternFly Chatbot Conversation History: https://www.patternfly.org/patternfly-ai/chatbot/chatbot-conversation-history/ -- formalized chat history sidebar pattern
- OpenAI File Uploads FAQ: https://help.openai.com/en/articles/8555545-file-uploads-faq
- OpenAI UX Principles: https://developers.openai.com/apps-sdk/concepts/ux-principles/
- LangGraph State Management: https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025

**From ARCHITECTURE.md:**
- Direct codebase analysis: `agent_service.py`, `state.py`, `graph.py`, `chat_message.py`, `file.py`, `tabStore.ts`, `ChatInterface.tsx`, `useSSEStream.ts`, `useChatMessages.ts`, all schema/type files
- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence -- official checkpoint and thread_id semantics
- LangGraph Persistence Deep Guide: https://pub.towardsai.net/persistence-in-langgraph-deep-practical-guide-36dc4c452c3b
- E2B Documentation: https://e2b.dev/docs -- sandbox file upload API
- Alembic Best Practices: https://medium.com/@pavel.loginov.dev/best-practices-for-alembic-and-sqlalchemy-73e4c8a6c205

**From PITFALLS.md:**
- Direct codebase analysis with line-number references
- E2B Pricing (512 MiB RAM default): https://e2b.dev/pricing
- E2B Custom Sandbox Compute: https://e2b.dev/blog/customize-sandbox-compute
- LangGraph Threads Migration Tool: https://github.com/farouk09/langgraph-threads-migration
- PostgreSQL Migration Best Practices: https://medium.com/shelf-io-engineering/how-to-safely-migrate-millions-of-rows-across-postgres-production-tables-35de77322eb0
- PostgreSQL Relationship Migration (Miro Engineering): https://medium.com/miro-engineering/sql-migrations-in-postgresql-part-1-bc38ec1cbe75
- Next.js Layouts and Pages: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts
- Next.js Layout State Reset Discussion: https://github.com/vercel/next.js/discussions/49749

### Secondary (MEDIUM confidence)

**From FEATURES.md:**
- Julius AI multi-file analysis: https://julius.ai/articles/13-powerful-features-that-make-julius-ai-the-top-data-analysis-tool
- Julius AI merge/join guide: https://julius.ai/guides/merging_datasets
- ChatGPT file upload limits: https://www.datastudios.org/post/chatgpt-5-file-upload-limits-maximum-sizes-frequency-caps-and-plan-differences-in-late-2025
- Cross-dataset merging challenges: https://dataladder.com/merging-data-from-multiple-sources/
- AI integration across multiple data sources: https://medium.com/axel-springer-tech/ai-integration-across-multiple-data-sources-c8dbd84ffc4b

**From PITFALLS.md:**
- Context Window Overflow Patterns (Redis): https://redis.io/blog/context-window-overflow/
- Context Window Problem (Factory.ai): https://factory.ai/news/context-window-problem
- Zustand Store Persistence and Versioning: https://zustand.docs.pmnd.rs/integrations/persisting-store-data
- Zustand with Next.js App Router: https://zustand.docs.pmnd.rs/guides/nextjs
- Pandas Scaling to Large Datasets: https://pandas.pydata.org/docs/user_guide/scale.html

### Tertiary (LOW confidence, verify during implementation)

**From FEATURES.md:**
- AI UX of analytics (GoodData): https://www.gooddata.com/blog/ux-of-ai-data-analytics/
- Chat UI design trends: https://multitaskai.com/blog/chat-ui-design/
- Session management for AI apps: https://medium.com/@aslam.develop912/master-session-management-for-ai-apps-a-practical-guide-with-backend-frontend-code-examples-cb36c676ea77

---
*Research completed: 2026-02-11*
*Ready for roadmap: yes*
