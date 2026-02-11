# Domain Pitfalls: v0.3 Multi-File Conversation Support

**Domain:** AI Data Analytics Platform -- UX restructure from file-tab-centric to chat-session-centric architecture
**Researched:** 2026-02-11
**Confidence:** HIGH (derived from direct codebase analysis + verified technical sources)

**Context:** Spectra v0.3 transforms the application from a file-tab-centric model (each file = one chat tab, 1:1 relationships) to a chat-session-centric model (ChatGPT-style conversations that can link multiple files, many-to-many relationships). This touches every layer: database schema, API routes, agent state, sandbox execution, frontend layout, and state management. The existing codebase has 96 validated requirements across v0.1 and v0.2 that must continue working.

---

## Critical Pitfalls

Mistakes at this level cause data loss, broken existing functionality, or require significant rewrites.

### Pitfall 1: Data Migration Destroys LangGraph Checkpoint Thread IDs

**What goes wrong:**
The current `thread_id` format in LangGraph checkpoints is `file_{file_id}_user_{user_id}` (see `agent_service.py` line 175 and 336). When v0.3 introduces a `ChatSession` model with its own UUID, the thread_id scheme must change to `session_{session_id}_user_{user_id}`. If the migration creates new chat sessions for existing file-chat relationships but does NOT migrate the corresponding LangGraph checkpoint records in the `checkpoint` and `checkpoint_blobs` PostgreSQL tables, **all existing conversation memory is silently lost**. Users will open their migrated chats and find the AI has no memory of previous interactions, despite chat messages still being visible from the `chat_messages` table.

**Why it happens:**
LangGraph's `AsyncPostgresSaver` stores checkpoints keyed by `thread_id` in its own tables (`checkpoint`, `checkpoint_blobs`, `checkpoint_writes`). These tables are NOT part of the application's SQLAlchemy model -- they are managed by LangGraph's `setup()` method. Developers naturally focus on migrating the application tables (`files`, `chat_messages`) and forget that LangGraph has its own state tables with thread_id as the primary lookup key.

**Consequences:**
- All v0.1/v0.2 conversation context is lost (Manager Agent cannot route to MEMORY_SUFFICIENT or CODE_MODIFICATION for existing conversations)
- Users must re-explain context that the AI previously understood
- The context usage display (`/chat/{file_id}/context-usage`) will show 0% for migrated sessions

**Prevention:**
1. Write the migration in three steps: (a) create new tables, (b) populate junction table from existing 1:1 relationships AND update LangGraph checkpoint thread_ids, (c) drop old foreign keys
2. The checkpoint migration must UPDATE the `thread_id` column in LangGraph's `checkpoint`, `checkpoint_blobs`, and `checkpoint_writes` tables to map from `file_{file_id}_user_{user_id}` to `session_{session_id}_user_{user_id}`
3. Write a verification query that counts checkpoints before and after migration to ensure no records were lost
4. Test the migration on a database dump before running against production

**Detection:**
- After migration, open an existing chat session and ask a follow-up question. If the Manager Agent routes to NEW_ANALYSIS instead of MEMORY_SUFFICIENT for a question that clearly references prior context, the checkpoint migration failed
- Check `SELECT COUNT(*) FROM checkpoint` before and after migration -- the count should remain the same

**Phase to address:** Database Migration phase (must be the first phase of v0.3 implementation)

---

### Pitfall 2: Chat Messages Table Migration Breaks `cascade="all, delete-orphan"`

**What goes wrong:**
Currently, `ChatMessage` has a required `file_id` FK with `ondelete="CASCADE"` and `nullable=False` (see `chat_message.py` lines 25-29). The `File` model has `cascade="all, delete-orphan"` on its `chat_messages` relationship (see `file.py` lines 45-49). In v0.3, messages belong to a chat **session**, not a file. If the migration simply adds a `session_id` FK and makes `file_id` nullable (or removes it), the cascade delete behavior changes in dangerous ways:

- If `file_id` is made nullable without removing the cascade, deleting a file will CASCADE-delete messages that belong to a session with multiple files, destroying messages about other files
- If cascade is changed to only work on sessions, deleting a file no longer cleans up messages about that file (orphaned analysis results referencing a deleted file)
- The junction table (`session_files`) adds a third entity. Deleting a file must remove it from all sessions' file lists, but should NOT delete the session or its messages

**Why it happens:**
The 1:1 assumption is baked deep into the data model. `cascade="all, delete-orphan"` works perfectly when one file owns all its messages. In a many-to-many world, "ownership" is ambiguous -- messages belong to sessions, files are linked to sessions, and deleting a file should not destroy an entire session's conversation history.

**Consequences:**
- Data loss: deleting File A cascades to delete all messages in Session X, even though Session X also contains analysis of File B
- Orphan data: sessions reference deleted files, causing 404 errors when trying to load file context
- Broken file deletion: users delete a file expecting cleanup, but the relationship topology prevents clean deletion

**Prevention:**
1. Messages must move from `file_id` FK to `session_id` FK. The `file_id` on `ChatMessage` should be removed entirely (or kept only as an optional metadata field for "which file was this message primarily about")
2. Define clear cascade rules:
   - Deleting a session: CASCADE delete all messages in that session
   - Deleting a file: remove from junction table (`session_files`), do NOT cascade to sessions or messages
   - If a file is the ONLY file in a session, optionally warn the user before deletion
3. Write explicit tests for every combination: delete file with single-session, delete file with multi-session, delete session, delete user (should cascade through sessions to messages)
4. Execute the migration as a three-step process (per PostgreSQL best practice): first migration adds the new table and column, second migration copies data, third migration removes old column

**Detection:**
- After migration, delete a file that is linked to multiple sessions. Check that the other session's messages are intact
- Run `SELECT COUNT(*) FROM chat_messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE ...)` before and after file deletion

**Phase to address:** Database Migration phase (same migration as Pitfall 1)

---

### Pitfall 3: Agent State Assumes Single File Context -- Multi-File Breaks Code Generation

**What goes wrong:**
The entire agent pipeline is built around a single file. The evidence is pervasive:

- `ChatAgentState` has singular `file_id`, `file_path`, `data_summary`, `data_profile`, `user_context` fields (see `state.py` lines 60-79)
- `execute_in_sandbox` reads ONE file from disk and uploads it as `df` to the sandbox (see `graph.py` lines 286-356)
- The Coding Agent's system prompt uses `{data_profile}` singular (see `coding.py` line 170)
- Manager Agent builds thread_id from a single `file_id` (see `agent_service.py` line 175)
- The sandbox injects `df = pd.read_csv(...)` as a single dataframe (see `graph.py` lines 340-355)

When a session has 3 linked files, the system must load 3 data profiles, upload 3 files to the sandbox, and generate code that references `df_sales`, `df_customers`, `df_products` instead of just `df`. Simply passing all 3 profiles as `data_profile` will work for small files but will **blow through the LLM context window** for files with many columns.

**Why it happens:**
The original architecture was designed for "one file, one conversation" and this assumption permeates every layer. Changing the state schema, prompt templates, sandbox file loading, and code generation patterns all at once creates a massive blast radius.

**Consequences:**
- Code generation produces code referencing `df` when there are 3 dataframes, causing `NameError` in the sandbox
- Data profiles for 3 large files (each with 50+ columns) can consume 3,000-5,000 tokens of context, leaving less room for conversation history
- Manager Agent routing breaks because the routing prompt no longer has a clear "this is the file" context
- CODE_MODIFICATION route fails because previous code referenced `df` but new code needs named dataframes

**Prevention:**
1. Extend `ChatAgentState` to support lists: `file_ids: list[str]`, `file_paths: list[str]`, `data_summaries: dict[str, str]` (keyed by file_id), `data_profiles: dict[str, str]` (keyed by file_id)
2. Change the sandbox file loading to iterate over all linked files and assign named dataframes: `df_{sanitized_filename}` or `df_1`, `df_2`, etc.
3. Build a compact "multi-file context block" for prompts that summarizes all files in ~500 tokens total (file name + column count + key columns), with full profiles available on-demand via a separate tool or only for the primary file being referenced
4. Implement a "file relevance filter" in the Coding Agent prompt that asks the LLM which files are relevant to the query before loading full profiles
5. Keep backward compatibility: if a session has exactly 1 file, continue using `df` as the dataframe name to avoid breaking user expectations

**Detection:**
- Create a session with 2+ files and ask a cross-file question like "Compare sales in file A with customers in file B". If the generated code references `df` instead of named dataframes, the multi-file support is incomplete

**Phase to address:** Agent System Enhancement phase (after database migration, before frontend restructure)

---

### Pitfall 4: E2B Sandbox Memory Overflow with Multiple Large Files

**What goes wrong:**
E2B sandboxes have **512 MiB RAM by default** with 2 vCPU (confirmed via E2B pricing documentation). The current system uploads one file to the sandbox per execution. With multi-file support, uploading 3 CSV files of 20-30MB each means pandas needs to load all three into memory simultaneously. A 30MB CSV can easily consume 100-300MB of RAM in pandas (due to object dtype overhead, index allocation, and type inference). Three such files would require 300-900MB -- exceeding the default 512MB sandbox limit and causing `MemoryError` or silent OOM kills.

**Why it happens:**
The per-execution sandbox model (see `e2b_runtime.py`) creates a fresh sandbox, uploads data, runs code, and tears down. There is no persistent sandbox state or file caching. Every query re-uploads all files, and pandas must re-parse all of them from scratch.

**Consequences:**
- `MemoryError` during `pd.read_csv()` or `pd.read_excel()` for the second or third file
- Sandbox timeout as pandas struggles with large files in low-memory environments
- Retry loop wastes 3 attempts on the same OOM condition (the Code Checker cannot detect memory issues pre-execution)
- Users with large files cannot use cross-file analysis at all
- E2B cost increases if sandbox compute needs upgrading (Pro plan required for custom RAM)

**Prevention:**
1. Implement a file size budget: calculate total memory estimate before uploading (rule of thumb: CSV file size * 3-5x for pandas memory). If estimated memory exceeds 400MB, either:
   - Warn the user and suggest sampling
   - Only load columns needed for the query (selective column loading in generated code)
   - Upgrade sandbox compute for that execution (Pro plan allows custom CPU/RAM via `--memory-mb` flag on template build)
2. Generate smarter code that loads only required columns: `pd.read_csv(file, usecols=['col_a', 'col_b'])`
3. For cross-file analysis, consider loading files sequentially and aggregating results rather than loading all into memory simultaneously
4. Add a pre-flight memory estimation step that checks `sum(file_sizes) * 5` against sandbox RAM and returns an early error with actionable guidance instead of burning 3 retries on an OOM

**Detection:**
- Upload 3 files each >15MB, link to same session, ask a cross-file question. If the sandbox times out or returns MemoryError, this pitfall is active
- Monitor E2B execution times -- if they spike significantly when multiple files are involved, memory pressure is the likely cause

**Phase to address:** Agent System Enhancement phase (alongside Pitfall 3)

---

### Pitfall 5: Frontend Navigation Restructure Breaks SSE Stream Lifecycle

**What goes wrong:**
The current architecture has `ChatInterface` as a child of `DashboardPage` (see `dashboard/page.tsx` lines 88-93), with the SSE stream managed by `useSSEStream` hook inside `ChatInterface`. When the layout restructures from tab-based to sidebar-based chat navigation, switching between chat sessions will **unmount and remount** `ChatInterface`. If an SSE stream is active during a session switch, the stream must be properly aborted and cleaned up. The current `useSSEStream` hook has an `AbortController` cleanup in `useEffect` (see `useSSEStream.ts` lines 266-272), but there are several failure modes:

1. The stream's save logic in `run_chat_query_stream` (which saves chat history to the database, see `agent_service.py` lines 409-453) may not execute if the client disconnects mid-stream
2. The `request.is_disconnected()` check in the router (see `chat.py` line 206) may not trigger fast enough
3. If the user switches away during the stream and back to the same session, they will see stale state (the stream completed but the component re-mounted without the completion data)

**Why it happens:**
In the current tab-based UI, switching tabs does NOT unmount `ChatInterface` -- it just hides/shows it (tabs are rendered conditionally by `currentTabId` but the component stays in the React tree for the active tab). In the new sidebar navigation model, clicking a different chat session likely causes a route change via Next.js App Router, which unmounts the current page component and mounts a new one. This fundamentally changes the stream lifecycle. The Next.js documentation confirms that "layouts preserve state, remain interactive, and do not rerender on navigation" but **pages do not** -- they unmount and remount.

**Consequences:**
- Chat messages are not saved to the database (the stream was aborted before the save logic ran)
- LangGraph checkpoint is in an inconsistent state (partial execution saved, but no completion)
- Users lose AI responses that were generating when they switched sessions
- Returning to the session shows a stale message list (missing the response that was in-flight)

**Prevention:**
1. Design the chat session view as a **layout-level component** that persists across session switches, not a page-level component that unmounts. Use a `[sessionId]` dynamic route with the chat interface in the layout
2. Alternatively, keep `ChatInterface` mounted for the active session using CSS `display: none` instead of conditional rendering, and use Zustand to track which session is visible
3. Add a server-side safety net: if the backend detects a client disconnect during streaming (via `request.is_disconnected()`), save whatever progress was made with a `status: "interrupted"` flag in the message metadata
4. Show a confirmation dialog before allowing session switch during active streaming: "AI is still processing. Switch anyway?"
5. After switching back to a session, always refetch messages from the server to catch any that were saved during disconnection

**Detection:**
- Start a long-running query (cross-file analysis), immediately switch to another session via sidebar, then switch back. If the response is missing, this pitfall is active
- Check the database: if `chat_messages` is missing the assistant response for queries that were visually generating, the save-on-disconnect is failing

**Phase to address:** Frontend Restructure phase (must be designed before implementing sidebar navigation)

---

## Moderate Pitfalls

### Pitfall 6: Context Window Token Explosion with Multi-File Metadata

**What goes wrong:**
The current context window is configured at 12,000 tokens (see PROJECT.md line 142). Each file's data profile (generated by `OnboardingAgent.profile_data()`) typically consumes 400-1,200 tokens depending on column count and data types. The Manager Agent's routing prompt already includes conversation history, previous code, and execution results (see `manager.py` lines 121-130). Adding metadata for 3-5 linked files could push the prompt from ~3,000 tokens to ~6,000 tokens, leaving only 6,000 tokens for conversation history -- a 50% reduction in effective conversation memory.

Research confirms this is a known pattern: "A single metadata query for millions of labels with their associated attributes can easily produce tens of millions of tokens, far beyond any LLM's context window." While Spectra's scale is smaller, the same principle applies -- multi-file metadata accumulates fast and degrades model performance even before hitting hard token limits (attention concentrates on beginning and end of input, causing "context rot").

**Why it happens:**
The 12,000 token limit was sized for single-file conversations. Nobody recalibrated for multi-file contexts where each file contributes metadata overhead.

**Prevention:**
1. Implement tiered metadata inclusion: full profile for the "primary" file being discussed, compact summaries (name + column list only, ~100 tokens each) for secondary files
2. Consider increasing the context window to 16,000-20,000 tokens for sessions with 3+ files
3. Add a `file_count` check in the routing prompt builder -- if >2 files, use compressed profiles
4. Generate a "multi-file summary" at session-link time that summarizes all files in one block (~200-300 tokens) instead of concatenating individual profiles

**Detection:**
- Add 4 files to a session, have a 10-message conversation, then check context usage. If it hits 85% warning after only a few exchanges, the metadata overhead is too high

**Phase to address:** Agent System Enhancement phase

---

### Pitfall 7: Thread ID Collision When Same File Appears in Multiple Sessions

**What goes wrong:**
If the old thread_id format `file_{file_id}_user_{user_id}` is kept but sessions are introduced, two sessions linking the same file would share the same checkpoint. This means conversation history from Session A bleeds into Session B. The Manager Agent in Session B would see Session A's messages and make routing decisions based on the wrong context. The new format `session_{session_id}_user_{user_id}` solves this, but only if it is adopted consistently across ALL code paths.

The specific code paths that construct or use thread_id:
- `agent_service.py` line 175: `thread_id = f"file_{file_id}_user_{user_id}"`
- `agent_service.py` line 336: same pattern for stream version
- `chat.py` line 264: context-usage endpoint uses same pattern
- `chat.py` line 316: trim-context endpoint uses same pattern

**Why it happens:**
Search-and-replace of the thread_id pattern is easy to get wrong. If even one endpoint retains the old format, it will look up the wrong checkpoint and produce confusing behavior.

**Prevention:**
1. Centralize thread_id construction into a single utility function: `def make_thread_id(session_id: UUID, user_id: UUID) -> str`
2. Use that function everywhere -- no inline string formatting
3. Add a grep-based CI check or test that scans all Python files for the old `file_{` pattern in thread_id construction
4. Write an integration test that creates 2 sessions with the same file, sends different messages to each, and verifies that checkpoint states are independent

**Detection:**
- Open the same file in two different sessions, have different conversations. If the context bleeds across sessions, the thread_id is still file-based

**Phase to address:** Database Migration phase (define the utility function) + Agent System Enhancement phase (adopt everywhere)

---

### Pitfall 8: API Route Structure Break -- `/chat/{file_id}/...` Becomes `/chat/{session_id}/...`

**What goes wrong:**
All current chat endpoints use `file_id` as the path parameter:
- `GET /chat/{file_id}/messages` (chat.py line 26)
- `POST /chat/{file_id}/messages` (chat.py line 68)
- `POST /chat/{file_id}/query` (chat.py line 108)
- `POST /chat/{file_id}/stream` (chat.py line 151)
- `GET /chat/{file_id}/context-usage` (chat.py line 238)
- `POST /chat/{file_id}/trim-context` (chat.py line 288)

The frontend's `useSSEStream` hardcodes the URL pattern (see `useSSEStream.ts` line 94): `fetch(\`http://localhost:8000/chat/${fileId}/stream\`...)`. The `useChatMessages` hook uses `apiClient.get(\`/chat/${fileId}/messages\`)` (see `useChatMessages.ts` line 14). The `ChatMessageResponse` type includes `file_id` (see `types/chat.ts` line 8).

Changing from `{file_id}` to `{session_id}` requires updating 6 backend routes, 3+ frontend hooks, all TypeScript types, and the Pydantic response schemas simultaneously. If the frontend and backend are not updated atomically, the application breaks entirely.

**Why it happens:**
The API contract is tightly coupled to the 1:1 file-chat model. There is no API versioning, and the parameter name `file_id` is used in URLs, function signatures, and type definitions.

**Prevention:**
1. **Do NOT introduce API versioning** for a single-developer project. Just change the routes.
2. Create a comprehensive checklist of every file that references `file_id` in a chat context:
   - Backend: `routers/chat.py`, `services/chat.py`, `services/agent_service.py`, `schemas/chat.py`
   - Frontend: `hooks/useChatMessages.ts`, `hooks/useSSEStream.ts`, `types/chat.ts`, `components/chat/ChatInterface.tsx`
3. Update backend and frontend in the same commit/phase
4. Use TypeScript compiler as verification: rename `file_id` to `session_id` in the types and let `tsc --noEmit` find every broken reference

**Detection:**
- After changing backend routes, run the frontend and check browser DevTools Network tab. Any 404s on `/chat/` endpoints indicate missed updates
- Run `tsc --noEmit` to catch TypeScript type mismatches

**Phase to address:** API + Frontend Migration (backend and frontend updated together in same phase)

---

### Pitfall 9: Zustand TabStore Replacement Creates State Synchronization Bugs

**What goes wrong:**
The current `useTabStore` (see `tabStore.ts`) manages `tabs: FileTab[]` and `currentTabId`. The v0.3 replacement needs a `useChatSessionStore` managing `sessions: ChatSession[]` and `currentSessionId`. During the transition, if both stores coexist temporarily, components may read from the wrong store. The dashboard page (`dashboard/page.tsx`), file sidebar (`FileSidebar.tsx`), and chat interface (`ChatInterface.tsx`) all import from `useTabStore`. Forgetting to migrate even one component creates a state synchronization bug where clicking a sidebar item updates the new store but the main content area still reads from the old store.

Additionally, Zustand stores are singletons -- if a component imports `useTabStore` and another imports `useChatSessionStore`, they are completely independent state trees with no synchronization.

**Why it happens:**
Zustand stores are imported by reference. If `useTabStore` is still imported in even one component while others use the new `useChatSessionStore`, the UI becomes inconsistent. The visual result is that clicking navigation does nothing in some parts of the UI.

**Prevention:**
1. Create the new store first, then do a single commit that replaces ALL imports of `useTabStore` with the new store
2. Delete `tabStore.ts` when all imports are removed -- the TypeScript compiler will catch any remaining references as import errors
3. Use `tsc --noEmit` as your verification tool: it will fail if any component still imports the deleted store
4. The new store must also handle the "no session selected" empty state that maps to the greeting screen requirement

**Detection:**
- Click a chat session in the sidebar. If the main content area does not update (still shows the old tab's chat or the empty state), the stores are out of sync
- Run `tsc --noEmit` after deleting the old store file

**Phase to address:** Frontend Restructure phase

---

### Pitfall 10: Query Suggestions Break When Session Has No Files or Multiple Files

**What goes wrong:**
Currently, query suggestions are generated during file onboarding and stored on the `File` model as `query_suggestions` (see `file.py` line 31). The `ChatInterface` loads suggestions via `useFileSummary(fileId)` (see `ChatInterface.tsx` line 65). In v0.3, a new chat session starts with no files linked. The requirements state: "Before user can initiate a chat, user will be asked to link or add a file to the chat" (requirement 1 in milestone-03-req.md). But the query suggestions only exist on files, not sessions.

When a file is linked to a session, the suggestions must be loaded for that file. When multiple files are linked, whose suggestions should be shown? Showing all suggestions from all files creates a confusing, overly long list. Showing none until files are linked is acceptable but needs a clear empty state.

**Why it happens:**
Suggestions are a file-level concern in v0.1/v0.2 and there is no session-level suggestion concept. The hook `useFileSummary(fileId)` is called with a single file ID.

**Prevention:**
1. When the first file is linked to a session, display that file's suggestions
2. When multiple files are linked, merge suggestions by de-duplicating similar queries, or only show suggestions for the most recently linked file
3. Show a clear "Link a file to start chatting" state for empty sessions, with the "Add File" button prominently displayed
4. Do NOT generate new "cross-file" suggestions at link time -- too expensive (requires LLM call) and slow. Reuse existing per-file suggestions

**Detection:**
- Create a new session, link 2 files. If suggestions are blank or only from one file with no indication of the other, the suggestion merging is incomplete

**Phase to address:** Frontend Restructure phase

---

### Pitfall 11: File Deletion Orphans Sandbox File References in Stored Code

**What goes wrong:**
When a user deletes a file, the file is removed from disk and its database record is deleted. However, existing `chat_messages` for sessions that used this file contain `metadata_json.generated_code` referencing the deleted file's path (e.g., `pd.read_csv('/home/user/sales_data.csv')`). If a user later asks a follow-up question that triggers CODE_MODIFICATION route, the Coding Agent will attempt to modify code that references a non-existent file, and the sandbox will fail with `FileNotFoundError`.

In the multi-file world, this is worse: deleting one of three linked files means existing code that references all three files is now partially broken. The other two files still work, but any cross-file analysis that included the deleted file will fail on re-execution.

**Why it happens:**
Generated code is stored as a string in `metadata_json` and contains hardcoded file paths. There is no mechanism to invalidate or update stored code when files are deleted or unlinked from sessions.

**Prevention:**
1. When a file is removed from a session (unlinked) or deleted entirely, update the session's agent state to clear `previous_code` so the Manager Agent cannot route to CODE_MODIFICATION referencing the deleted file
2. Add a visual indicator to affected DataCards: "File [name] is no longer available. Results shown are from the original analysis."
3. The Manager Agent should be aware of linked files: when `previous_code` references a file that is no longer linked, route to NEW_ANALYSIS instead of CODE_MODIFICATION
4. Consider storing the list of files referenced by each code execution in the message metadata, so the frontend can cross-reference against currently linked files

**Detection:**
- Link a file to a session, run a query, then unlink the file. Ask a follow-up that triggers code modification. If the sandbox crashes with FileNotFoundError and retries 3 times before halting, the file unlinking is not clearing stale state

**Phase to address:** Agent System Enhancement phase + Frontend Restructure phase (visual indicators)

---

## Minor Pitfalls

### Pitfall 12: SSE Stream URL Hardcoded to localhost

**What goes wrong:**
The `useSSEStream` hook hardcodes `http://localhost:8000` (see `useSSEStream.ts` line 94) instead of using the centralized `apiClient`. This already exists in v0.2, but during v0.3's frontend restructure, if this URL is not centralized, the new session-based stream endpoint will perpetuate the pattern and block any future deployment to a non-localhost environment.

**Prevention:**
While restructuring the stream hook for session-based URLs, also extract the base URL into a shared constant or use `apiClient`'s configured base URL. This is an opportunistic fix during the required URL changes.

**Phase to address:** Frontend Restructure phase (fix alongside the `file_id` to `session_id` URL change)

---

### Pitfall 13: Chat History Sidebar Performance with Many Sessions

**What goes wrong:**
The v0.3 requirements call for a chat history sidebar showing all sessions. If a user creates 50+ sessions over time, loading all session metadata on every page load creates unnecessary API overhead and slow sidebar rendering. The current `FileSidebar` loads all files at once (see `FileSidebar.tsx` using `useFiles()` hook), which works for files (users rarely have >20) but may not scale for chat sessions.

**Prevention:**
1. Paginate chat sessions in the API (load last 20, with "Load more" button or virtual scroll)
2. Only load session title and last message timestamp for the sidebar -- not full message lists or file details
3. Use TanStack Query's `staleTime` to prevent re-fetching on every navigation
4. Group sessions by date (Today, Yesterday, Last 7 days, Older) for easier scanning

**Phase to address:** Frontend Restructure phase

---

### Pitfall 14: "My Files" Screen and Chat File Modal Share Component but Expect Different Behavior

**What goes wrong:**
The v0.3 requirements introduce a "My Files" screen accessible from the sidebar AND a file selection modal within chat sessions. Both need to show a list of files. The existing `FileSidebar` component (see `FileSidebar.tsx`) currently serves as the file list -- clicking a file opens a tab. In v0.3:
- Clicking a file in "My Files" should navigate to file detail or start a new chat
- Clicking a file in the "Link File" modal should link the file to the current session and close the modal

If the same file list component is reused in both contexts without a clear mode differentiation, clicking a file will perform the wrong action in one of the two contexts.

**Prevention:**
1. Build the file list as a reusable component with an `onSelect` callback prop
2. In "My Files" context: `onSelect` navigates to file detail or creates new session
3. In "Link File" modal context: `onSelect` calls the session-file linking API and closes modal
4. Do NOT couple file list behavior to a global store or hardcoded navigation -- keep it prop-driven
5. Each context should clearly indicate its purpose with different headers ("My Files" vs "Link a file to this chat")

**Phase to address:** Frontend Restructure phase

---

### Pitfall 15: Dark Mode Added During Layout Restructure Compounds CSS Complexity

**What goes wrong:**
The v0.3 requirements mention "Allow users to switch between light and dark mode" (milestone-03-req.md line 93). If dark mode is implemented alongside the layout restructure, the CSS changes compound. New sidebar components, chat history items, file linking modals, and the "My Files" screen all need dark mode variants tested simultaneously with the new layout.

**Why it happens:**
Two large UI changes at the same time (layout restructure + theme system) make it impossible to tell whether a visual bug is from the layout change or the dark mode implementation.

**Prevention:**
1. Use shadcn/ui's built-in dark mode support (already in the stack via Tailwind CSS)
2. Implement dark mode AFTER the layout restructure is complete and visually verified in light mode
3. All new components should use Tailwind semantic colors (`bg-background`, `text-foreground`, `border`) rather than hardcoded colors -- this makes dark mode nearly automatic when the theme is toggled
4. The existing components already follow this pattern (verified in `ChatInterface.tsx`, `DashboardLayout.tsx`), so maintain consistency in all new components

**Phase to address:** Final polish phase (after all structural changes are stable)

---

### Pitfall 16: Alembic Not Set Up -- Manual Schema Migration Risk

**What goes wrong:**
The project does not currently have Alembic configured for database migrations (no `alembic/` directory found in the project root, only in `.venv`). Previous schema changes likely used `Base.metadata.create_all()` or manual SQL. The v0.3 migration requires adding a `chat_sessions` table, a `session_files` junction table, migrating `chat_messages.file_id` to `chat_messages.session_id`, and updating LangGraph checkpoint thread_ids -- all while preserving existing data. Without Alembic, these changes are manual SQL scripts that cannot be rolled back, version-tracked, or tested incrementally.

**Prevention:**
1. Set up Alembic before starting any v0.3 database work
2. Create an initial migration that captures the current schema as the baseline
3. Write all v0.3 schema changes as Alembic migrations with proper `upgrade()` and `downgrade()` functions
4. Test migrations on a copy of production data before applying

**Phase to address:** Database Migration phase (prerequisite: set up Alembic first)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Severity | Mitigation |
|---|---|---|---|
| Database Migration | Pitfall 1: LangGraph checkpoint thread_id orphaning | CRITICAL | Write checkpoint migration alongside schema migration |
| Database Migration | Pitfall 2: Cascade delete topology change | CRITICAL | Redefine ownership: sessions own messages, not files |
| Database Migration | Pitfall 7: Thread ID collision across sessions | MODERATE | Centralize thread_id construction in utility function |
| Database Migration | Pitfall 16: No Alembic setup | MODERATE | Set up Alembic before any schema changes |
| Agent System Enhancement | Pitfall 3: Single-file assumptions in agent state | CRITICAL | Extend state schema to support file lists + multi-profile prompts |
| Agent System Enhancement | Pitfall 4: Sandbox memory overflow with multiple files | CRITICAL | Pre-flight memory estimation, selective column loading |
| Agent System Enhancement | Pitfall 6: Context window token explosion | MODERATE | Tiered metadata, compressed file profiles |
| Agent System Enhancement | Pitfall 11: Deleted file orphans in code history | MODERATE | Clear stale state on file unlink, visual indicators |
| API + Frontend Migration | Pitfall 8: Frontend-backend URL contract breakage | MODERATE | Update backend and frontend in same phase, use tsc as validator |
| Frontend Restructure | Pitfall 5: SSE stream lifecycle on navigation | CRITICAL | Layout-level chat component or CSS-based session switching |
| Frontend Restructure | Pitfall 9: Zustand store replacement state sync | MODERATE | Single commit for all store imports, delete old store |
| Frontend Restructure | Pitfall 10: Query suggestions for multi-file sessions | MODERATE | Merge suggestions or use most-recent file's |
| Frontend Restructure | Pitfall 12: Hardcoded localhost URL | MINOR | Fix alongside required URL pattern changes |
| Frontend Restructure | Pitfall 13: Chat history sidebar performance | MINOR | Paginate sessions, load minimal metadata |
| Frontend Restructure | Pitfall 14: File list dual-mode confusion | MINOR | Prop-driven onSelect callback, no global coupling |
| Final Polish | Pitfall 15: Dark mode + layout restructure CSS conflict | MINOR | Implement dark mode after layout is stable |

---

## Integration Risk Assessment

The highest risk in v0.3 is the **cross-cutting nature of the changes**. Unlike v0.2 (which added new capabilities to an existing structure), v0.3 **restructures the existing foundation**. Every layer depends on the 1:1 file-chat assumption:

| Layer | Current Assumption | v0.3 Change | Risk Level |
|---|---|---|---|
| Database | `ChatMessage.file_id` is required FK | Move to `ChatMessage.session_id` | HIGH -- data migration with cascade semantics |
| LangGraph Checkpoints | `thread_id = file_{file_id}_user_{user_id}` | Change to `session_{session_id}_user_{user_id}` | HIGH -- silent data loss if missed |
| Agent State | Singular `file_id`, `file_path`, `data_profile` | Lists of files, multi-profile context | HIGH -- prompt + code gen redesign |
| Sandbox Execution | Upload one file, inject `df = pd.read_csv(...)` | Upload N files, inject `df_1`, `df_2`, etc. | HIGH -- memory limits at 512MB |
| API Routes | `/chat/{file_id}/...` all 6 endpoints | `/chat/{session_id}/...` | MODERATE -- mechanical but many touchpoints |
| Frontend State | `useTabStore` with `FileTab[]` | New `useChatSessionStore` with `ChatSession[]` | MODERATE -- single commit replacement |
| Frontend Layout | Tabs in dashboard page, file sidebar | Sidebar chat history + session navigation | MODERATE -- but SSE lifecycle is critical |
| Chat Types | `ChatMessageResponse.file_id`, `useChatMessages(fileId)` | All references change to `session_id` | MODERATE -- TypeScript compiler catches most |

**Recommendation:** Do NOT attempt to change all layers simultaneously. The migration must proceed in strict dependency order:
1. **Database schema + migration** (new tables + data migration + LangGraph checkpoint migration)
2. **Backend API + Agent system** (new routes + multi-file agent state + sandbox changes)
3. **Frontend restructure** (new layout + state management + dark mode)

Each phase should be independently deployable and testable. The database can change while the backend still uses old routes (with a compatibility shim). The backend can change while the frontend still uses old URLs (briefly). But the frontend cannot change without the backend, and the backend cannot change without the database.

---

## Regression Risk: v0.1 and v0.2 Requirements

There are 96 validated requirements that must continue working. The highest-risk regressions:

| Requirement | Why At Risk | Regression Test |
|---|---|---|
| "Each file has its own chat tab" (v0.1 File-10) | Tabs are being removed. Existing behavior must map to sessions. | Verify files uploaded via "My Files" create their own session |
| "Chat history persists per file across browser sessions" (v0.1 AI-07) | Messages now belong to sessions, not files | Verify messages appear in the correct session after migration |
| "Independent conversation memory per file tab" (v0.2 Memory-04) | Memory now scoped to session, not file | Verify sessions have independent checkpoints |
| "Context persists after browser refresh" (v0.2 Memory-02) | New session routing must survive refresh | Verify URL includes session ID and restores state on refresh |
| "Warning dialog before closing chat tab" (v0.2 Memory-03) | No tabs to close. Sessions persist in sidebar. | Determine if this requirement still applies or is replaced |
| "New chat tabs display 5-6 query suggestions" (v0.2 Suggest-01) | Suggestions were per-file, now need per-session behavior | Verify suggestions appear when first file is linked to session |
| "User can switch between file tabs with independent chat histories" (v0.1 File-09) | Tabs replaced by sessions. Must still be able to switch. | Verify sidebar navigation switches between sessions independently |

**Phase to address:** Every phase should run the full test suite. Write migration-specific regression tests before starting.

---

## Sources

- **Codebase analysis:** Direct inspection of `agent_service.py`, `state.py`, `graph.py`, `chat_message.py`, `file.py`, `tabStore.ts`, `ChatInterface.tsx`, `useSSEStream.ts`, `useChatMessages.ts`, `coding.py`, `manager.py`, `e2b_runtime.py`, `chat.py` (router), `database.py`, and all schema/type files
- [E2B Pricing -- default 512 MiB RAM, 2 vCPU](https://e2b.dev/pricing)
- [E2B Custom Sandbox Compute](https://e2b.dev/blog/customize-sandbox-compute) -- Pro plan allows `--memory-mb` and `--cpu-count` customization
- [LangGraph Persistence Documentation](https://docs.langchain.com/oss/python/langgraph/persistence) -- checkpoint thread_id structure and management
- [LangGraph Threads Migration Tool](https://github.com/farouk09/langgraph-threads-migration) -- community tool for checkpoint data migration
- [PostgreSQL Migration Best Practices](https://medium.com/shelf-io-engineering/how-to-safely-migrate-millions-of-rows-across-postgres-production-tables-35de77322eb0) -- three-step migration pattern (schema, data, cleanup)
- [PostgreSQL Relationship Migration (Miro Engineering)](https://medium.com/miro-engineering/sql-migrations-in-postgresql-part-1-bc38ec1cbe75) -- separate schema and data migrations
- [Next.js Layouts and Pages](https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts) -- layouts preserve state, pages do not
- [Next.js Layout State Reset Discussion](https://github.com/vercel/next.js/discussions/49749) -- known issue with state reset on dynamic segment navigation
- [Context Window Overflow Patterns (Redis)](https://redis.io/blog/context-window-overflow/) -- multi-file metadata token explosion
- [Context Window Problem (Factory.ai)](https://factory.ai/news/context-window-problem) -- repository summary strategy for reducing token overhead
- [Zustand Store Persistence and Versioning](https://zustand.docs.pmnd.rs/integrations/persisting-store-data) -- migration functions for breaking store changes
- [Zustand with Next.js App Router](https://zustand.docs.pmnd.rs/guides/nextjs) -- setup patterns and state sharing
- [Pandas Scaling to Large Datasets](https://pandas.pydata.org/docs/user_guide/scale.html) -- memory management, chunked reading, selective column loading

---

*Pitfalls research for: Spectra v0.3 Multi-File Conversation Support*
*Researched: 2026-02-11*
*Confidence: HIGH -- All critical pitfalls verified against actual codebase with line-number references and corroborated by technical documentation*
