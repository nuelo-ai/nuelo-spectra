# Feature Landscape: Multi-File Conversation Support (v0.3)

**Domain:** AI-powered data analytics platform -- chat-session-centric UX with multi-file linking
**Researched:** 2026-02-11
**Confidence:** MEDIUM-HIGH
**Supersedes:** Previous FEATURES.md (v0.2 intelligence features, 2026-02-06)

---

## Executive Summary

This research maps the feature landscape for Spectra v0.3, which restructures the platform from a file-tab-centric model (each file has its own chat) to a chat-session-centric model (ChatGPT-style, where conversations are independent entities that can reference multiple files). This is the most architecturally significant change since v0.1, affecting the data model, agent pipeline, frontend layout, and UX paradigm.

**Key findings from ecosystem research:**

- **Chat-session-centric UX is now the dominant pattern** across AI tools (ChatGPT, Claude, Gemini, Julius AI). Spectra's current file-tab model is the minority approach. Migrating is not a differentiator -- it is catching up to table stakes.
- **Multi-file context per conversation** is where the real value lies. Julius AI supports multiple files per conversation with cross-dataset analysis. ChatGPT allows up to 10 file attachments per message. This is the feature that transforms Spectra from "single-file Q&A" to "multi-source analytics workspace."
- **Chat history sidebar with chronological grouping** (Today, This Week, This Month) is the universal pattern adopted by ChatGPT, Claude, Gemini, and virtually every modern AI chat tool. PatternFly has formalized this into a reusable component pattern.
- **The hardest engineering problem is not UI -- it is multi-file agent context.** The existing LangGraph pipeline assumes single-file context (one file_id, one data_summary, one file_path). Extending to N files requires changes to the agent state schema, sandbox file handling, code generation prompts, and memory checkpointing.
- **"My Files" as a separate management screen** is standard in tools that decouple files from conversations (Google Drive model). It must feel lightweight -- not a separate app -- with quick actions: upload, view context, start chat, delete, download.

**Competitive context:** Julius AI (closest competitor) already supports multi-file conversations with cross-dataset merge/join. ChatGPT supports file attachments within conversations. Spectra v0.2's file-tab model is a known limitation blocking competitive parity. v0.3 closes this gap.

---

## Table Stakes

Features users expect from a chat-based analytics tool in 2026. Missing any of these makes Spectra feel incomplete or dated.

| Feature | Why Expected | Complexity | Dependencies on Existing |
|---------|--------------|------------|--------------------------|
| **Chat session as primary entity** | ChatGPT, Claude, Gemini all center on "conversations," not files. Users now expect to create a chat, then bring context into it. File-first is the exception, not the norm. | HIGH | Requires new `ChatSession` model, migration of existing `ChatMessage` from `file_id` FK to `session_id` FK, new frontend routing (`/chat/[sessionId]` instead of file tabs), replacement of `tabStore` with `sessionStore`. |
| **Chat history sidebar** | Every major AI chat tool has a left sidebar listing past conversations grouped chronologically (Today, Yesterday, This Week, This Month, Older). Users expect to click a conversation to resume it. PatternFly has formalized this as a standard component pattern. | MEDIUM | Replaces current `FileSidebar` component. Requires new API endpoint `GET /sessions` with pagination. Must integrate with existing auth (user isolation). Session titles auto-generated from first user message or AI summary. |
| **New Chat button** | Universal affordance in AI chat tools. Prominent button at top of sidebar. Creates empty session, optionally with file prompt. | LOW | Trivial UI addition once session model exists. Route to new empty session state. |
| **File linking to chat sessions** | Users must be able to attach files to conversations. At minimum: select from previously uploaded files. This is the core mechanism that replaces file tabs. At least one file required before chatting (per requirements). | HIGH | Requires new `session_files` junction table (many-to-many). File selection modal showing user's uploaded files. API endpoint to link/unlink files from sessions. Agent pipeline must receive list of file contexts instead of single file. |
| **File upload within chat** | ChatGPT allows file attachment via button below input. Drag-and-drop onto chat area is expected. Upload triggers onboarding, then links to current session. | MEDIUM | Reuses existing `FileUploadZone` component and onboarding pipeline. New: trigger from chat input area (not just sidebar), auto-link to current session after onboarding completes. Drag-drop overlay on chat area. |
| **Linked files displayed in session** | Users need to see which files are attached to current conversation. ChatGPT shows file chips/pills in the message. Claude shows project files in sidebar. Requirements specify: display at top of chat or in right sidebar with (i) icon for context. | LOW-MEDIUM | File pill/badge components showing filename + info icon. Click (i) opens existing `FileInfoModal`. Could be a horizontal strip above chat or a collapsible right panel. |
| **Session title auto-generation** | ChatGPT auto-titles conversations from first message. Users expect this. Manual rename is a nice-to-have but auto-title is table stakes. | LOW | Generate title from first user query (truncate to 50 chars) or ask LLM for a 3-5 word summary. Store as `title` field on `ChatSession` model. |
| **"My Files" management screen** | When files are decoupled from conversations, users need a dedicated place to see all their files. Standard pattern: list view with upload, delete, download, view context, start new chat actions. Google Drive / Dropbox model. | MEDIUM | New route `/files` with new page component. Reuses existing `FileService` APIs (`list_user_files`, `delete_file`, `download_file`). New: "Start Chat" action that creates session + links file. Grid or list view with sort/filter. |
| **Preserve existing conversation memory** | v0.2 already has multi-turn memory via LangGraph PostgreSQL checkpointing. v0.3 must preserve this. Thread IDs need to change from `file_{id}_user_{id}` to `session_{id}`. | MEDIUM | Migration of checkpoint thread IDs. Existing conversations from v0.2 either migrated (create session per file) or archived. LangGraph checkpointer config update. |
| **Single-file analysis (baseline)** | Even with multi-file support, most conversations will reference one file. The single-file path must remain fast and simple. No regression from v0.2. | LOW | Existing agent pipeline works for single file. Multi-file is additive, not replacing. Ensure single-file path has zero overhead from multi-file abstractions. |

---

## Differentiators

Features that set Spectra apart from competitors. Not expected, but create meaningful value.

| Feature | Value Proposition | Complexity | Dependencies on Existing |
|---------|-------------------|------------|--------------------------|
| **Cross-file analysis (joins/merges)** | Ask "Compare sales data from Q1.csv with Q2.csv" and get a merged analysis. Julius AI supports this. ChatGPT Code Interpreter supports this with uploaded files. This is the killer feature that justifies the multi-file architecture. | HIGH | Agent state must include multiple file paths and data profiles. Coding Agent prompts must instruct pandas merge/join operations. Sandbox must receive all linked files. Data Analysis Agent must understand multi-source context. Significant prompt engineering. |
| **Right sidebar file context panel** | Dedicated panel showing linked files with summaries, column info, row counts. Always visible during chat. More discoverable than hidden modals. Like VS Code's Explorer panel or Notion's page properties. | MEDIUM | New `FileContextPanel` component. Collapsible right sidebar (3-column layout: chat history / main chat / file context). Responsive: collapses to overlay on smaller screens. Shows file metadata from existing `data_summary`. |
| **File linking "link existing" flow** | Quick modal to browse and link already-uploaded files. Includes search/filter, file type indicators, preview of data summary. Avoids re-uploading same file for different analyses. | MEDIUM | File picker modal with search. API: `POST /sessions/{id}/files/{file_id}`. UI: dropdown from "Add File" button below chat input with "Upload new" and "Link existing" options. |
| **Chat session rename** | Right-click or inline edit to rename conversations. Helps organize analysis threads. Claude and ChatGPT both support this. | LOW | Inline edit on sidebar item. API: `PATCH /sessions/{id}` with `title` field. Standard UX pattern. |
| **Chat session delete** | Remove old conversations from history. Conversations pile up fast. Must confirm before delete (destructive action). | LOW | Dropdown menu on sidebar item. API: `DELETE /sessions/{id}` with cascade to messages and file links. Confirmation dialog. |
| **Drag-and-drop file onto chat** | Drop a file directly onto the chat area to upload and link in one step. ChatGPT supports this. Reduces friction for adding context mid-conversation. | MEDIUM | Global drag overlay on chat area. Detect `dragenter`/`dragleave`/`drop` events. On drop: trigger upload flow, then auto-link to current session. Reuse `FileUploadZone` logic with new visual treatment. |
| **Smart file suggestion in empty chat** | When starting a new chat with no files, suggest recently uploaded or frequently used files. Reduces clicks to start analyzing. | LOW | Query recent files from `FileService`. Display as clickable cards in empty chat state. One click to link and start. |
| **Session-level query suggestions** | Extend v0.2's data-aware suggestions to work with multi-file context. Suggest cross-file queries when multiple files are linked ("Compare column X from File A with column Y from File B"). | HIGH | Requires new suggestion generation that considers all linked files' schemas. Must detect joinable columns (same name or similar content). Prompt engineering for cross-file suggestion generation. |
| **Light/dark mode toggle** | Explicitly requested in requirements. Modern UX expectation. Most AI tools support theme switching. | LOW | Tailwind dark mode classes (already partially supported via `shadcn/ui` components). Theme toggle in settings or header. Persist preference in localStorage. |

---

## Anti-Features

Features to explicitly NOT build in v0.3. Building these would waste effort, add complexity, or create UX problems.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Automatic cross-file joins without user intent** | Silently merging datasets leads to wrong results. Schema mismatches, duplicate columns, Cartesian products. Users must explicitly ask for cross-file operations. Research shows key mismatch is the #1 cross-dataset pitfall. | Let the AI agent perform joins only when the user explicitly asks. Never auto-merge on session creation. Show files as separate contexts until user requests comparison. |
| **Real-time collaborative editing** | Multi-user on same session adds massive complexity (CRDT/OT, conflict resolution, presence indicators). Not in requirements. Not expected for analytics tools. | Single-user sessions. Per-user file/session isolation (already exists). Collaboration is a future milestone, not v0.3. |
| **File versioning** | Tracking file revisions adds storage cost and UX complexity. Users upload new files, they don't update existing ones. | Each upload is a new file. Users can delete old versions. No version history tracking. |
| **Folder/directory organization for files** | Over-engineering file management. Users will have 5-50 files, not thousands. Folders add navigation depth without value at this scale. | Flat file list with sort by date/name/type. Search/filter is sufficient for expected file counts. |
| **Conversation branching/forking** | ChatGPT experimented with edit-and-branch. Extremely complex UX and data model. Not requested. Confuses most users. | Linear conversation history. Users can start a new chat to explore a different direction. Copy previous context forward if needed. |
| **Inline file editing/spreadsheet view** | Building a spreadsheet editor is a massive scope expansion. Not what users come to Spectra for. | Show data previews (read-only tables from existing DataCard). Link out to original file download for editing. |
| **Embedding/vector search across files** | RAG-style search across all uploaded files is architecturally different from structured data analysis. Would require vector DB, embeddings pipeline, retrieval chain. Different product direction. | Spectra analyzes structured data via code execution. Cross-file works through pandas operations in sandbox, not semantic search. Keep focused on tabular data analysis. |
| **Session sharing via URL** | Public links to sessions create security concerns (data exposure). Not in requirements. | Sessions are private to authenticated user. Export results (existing DataCard export) for sharing. |

---

## Feature Dependencies

```
                    ChatSession Model (DB)
                    /        |          \
                   /         |           \
    Chat History Sidebar   Session-File   "My Files" Screen
          |              Junction Table        |
          |               /    |    \          |
     Session CRUD     Link   Unlink  Upload+Link
          |            File   File   in Chat
          |               \    |    /
          |            Agent Pipeline
          |            Multi-File Support
          |               /         \
          |     Cross-File       Right Sidebar
          |     Analysis         File Context Panel
          |         |
          |   Multi-File Sandbox
          |   (upload N files)
          |
    Auto-Title Generation
          |
    Session Rename/Delete
```

**Critical path (must be sequential):**
1. `ChatSession` model + `session_files` junction table (DB migration)
2. Session CRUD APIs (create, list, get, update, delete)
3. File linking APIs (link, unlink files to sessions)
4. Agent pipeline multi-file support (state schema, sandbox, prompts)
5. Frontend session-centric layout (sidebar, main chat, file context)

**Can be parallelized:**
- "My Files" screen (independent of session-centric chat)
- Light/dark mode (independent CSS/theme work)
- Chat session rename/delete (after session model exists)
- Drag-and-drop upload in chat (after basic upload-in-chat works)

---

## MVP Recommendation

### Must Have (v0.3 Core)

Prioritize these features in this order:

1. **ChatSession data model + migration** -- Foundation for everything else. New `chat_sessions` table, `session_files` junction table. Migrate existing `ChatMessage` from `file_id` to `session_id`. Create migration script that auto-creates sessions for existing file conversations.

2. **Session CRUD + file linking APIs** -- Backend endpoints for creating sessions, listing user sessions, linking/unlinking files. These APIs unblock all frontend work.

3. **Chat history sidebar** -- Replace `FileSidebar` with session-list sidebar. Chronological grouping (Today, This Week, This Month, Older). New Chat button. Click to load session.

4. **File linking UX in chat** -- "Add File" button below chat input with dropdown (Upload new / Link existing). File picker modal for linking existing files. Linked file pills/badges displayed above chat area.

5. **Agent pipeline multi-file adaptation** -- Extend `ChatAgentState` to accept list of files. Modify `run_chat_query_stream` to load all linked file contexts. Sandbox receives all file data. Coding Agent prompt updated for multi-file awareness.

6. **"My Files" management screen** -- Dedicated route for file list, upload, delete, download, view context, start new chat. Reuses existing file service layer.

7. **Single-file compatibility** -- Ensure the common case (one file per session) works with zero friction. Auto-link file when session is created from "My Files" or direct upload.

### Defer to Later

- **Cross-file joins/analysis** -- Complex prompt engineering. Ship multi-file linking first, add cross-file intelligence iteratively. v0.3.1 or v0.4.
- **Right sidebar file context panel** -- Nice-to-have. Start with file pills above chat area + existing modal on click. Full sidebar panel in v0.3.1.
- **Session-level multi-file query suggestions** -- Requires cross-file schema analysis. Ship single-file suggestions (already working from v0.2) first.
- **Smart file suggestion in empty chat** -- Low priority UX polish. Empty state can show "Upload or link a file to get started" prompt.

---

## Detailed Feature Specifications

### 1. Chat Session Model

**What exists today:**
- `ChatMessage` has direct `file_id` FK (one file per conversation)
- `tabStore` manages open file tabs in frontend
- Thread ID format: `file_{file_id}_user_{user_id}`
- No concept of "session" independent of file

**What needs to change:**
- New `ChatSession` table: `id`, `user_id`, `title`, `created_at`, `updated_at`
- New `session_files` junction table: `session_id`, `file_id`, `linked_at`
- `ChatMessage` changes: add `session_id` FK, make `file_id` FK nullable
- LangGraph thread ID changes to: `session_{session_id}`
- Migration: For each unique `(user_id, file_id)` pair in existing messages, create a session and link the file

**Complexity:** HIGH -- touches data model, migration, agent pipeline, and frontend state.

### 2. Chat History Sidebar

**Industry pattern (from research):**
- Left sidebar, collapsible
- Grouped by time: Today, Yesterday, This Week, This Month, Older
- Each item: session title (truncated), optional file icon
- Right-click or hover: rename, delete actions
- "New Chat" button at top (prominent, blue/primary color)
- Optional search input for filtering conversations
- PatternFly formalized: drawer overlay in default mode, inline in fullscreen

**Implementation for Spectra:**
- Replace `FileSidebar` component entirely with shadcn/ui Sidebar
- New `AppSidebar` component with SidebarProvider for state management
- API: `GET /sessions?page=1&limit=50` with date-based grouping in frontend
- Session items show: title, linked file count badge, timestamp
- Collapsible on mobile (SidebarTrigger button)
- Cookie-based sidebar collapse state persistence (built into shadcn Sidebar)

**Complexity:** MEDIUM -- mostly frontend UI work, straightforward API.

### 3. File Linking in Chat

**How ChatGPT does it:**
- Paperclip/attachment icon next to message input
- Click opens file picker (local files)
- Files appear as chips in message input area
- Up to 10 files per message

**How Spectra should do it (per requirements):**
- "Add File" button below chat input (next to send button area)
- Click shows dropdown: "Upload new file" / "Link existing file"
- "Upload new file": triggers existing upload + onboarding flow, then auto-links
- "Link existing file": opens modal with user's file list, search, click to link
- Linked files shown as horizontal strip above chat (or in right panel)
- Each file pill: filename + (i) icon for context modal
- Files can be unlinked (x button on pill)

**Complexity:** MEDIUM -- UI components are straightforward, backend linking API is simple.

### 4. Agent Pipeline Multi-File Support

**What exists today:**
- `ChatAgentState` has single `file_id`, `data_summary`, `data_profile`, `file_path`
- `run_chat_query_stream` loads one file record
- Sandbox receives one data file
- Coding Agent prompt references "the dataset" (singular)
- Thread ID: `file_{file_id}_user_{user_id}`

**What needs to change:**
- `ChatAgentState` extended: `file_ids: list[str]`, `file_paths: list[str]`, `data_summaries: list[str]`, `data_profiles: list[str]`
- `run_chat_query_stream` loads all linked files for session
- Sandbox receives multiple data files (one per linked file)
- Coding Agent prompt updated: "You have access to the following datasets: df_1 (filename.csv): {summary}, df_2 (filename2.xlsx): {summary}"
- Code generation must use named DataFrames (df_1, df_2, etc.) instead of single `df`
- File loading code in sandbox prepends N DataFrame reads instead of one
- Thread ID: `session_{session_id}`

**Complexity:** HIGH -- touches the entire agent pipeline. Most complex feature in v0.3.

### 5. "My Files" Management Screen

**Industry pattern:**
- Grid or list view of all files
- Sort by: date uploaded, filename, file size, type
- Actions per file: view context, start new chat, download, delete
- Upload button (triggers existing upload flow)
- File type icons (CSV, XLSX)
- File size display (human-readable)
- Empty state: "No files yet. Upload your first dataset."

**Implementation for Spectra:**
- New route: `/dashboard/files` (within dashboard layout)
- Left sidebar "My Files" button navigates here
- Reuses existing `FileService` APIs (already has list, delete)
- New: "Start Chat" action creates session + links file + navigates to chat
- Table view using existing `@tanstack/react-table` with columns: Name, Type, Size, Uploaded, Actions
- Search/filter by filename

**Complexity:** MEDIUM -- mostly frontend. Backend APIs largely exist.

---

## Complexity Budget

| Feature Category | Estimated Complexity | Risk Level |
|-----------------|---------------------|------------|
| Data model migration (sessions, junction table) | HIGH | HIGH -- breaking change to existing schema |
| Agent pipeline multi-file support | HIGH | HIGH -- touches entire AI pipeline |
| Chat history sidebar | MEDIUM | LOW -- well-understood UI pattern |
| File linking UX | MEDIUM | LOW -- straightforward UI |
| "My Files" screen | MEDIUM | LOW -- reuses existing APIs |
| File upload in chat (button + drag-drop) | MEDIUM | MEDIUM -- drag-drop edge cases |
| Cross-file analysis | HIGH | HIGH -- prompt engineering, schema detection |
| Right sidebar file panel | MEDIUM | LOW -- UI component work |
| Light/dark mode | LOW | LOW -- Tailwind dark mode |
| Session rename/delete | LOW | LOW -- CRUD operations |

**Total budget estimate:** This is a significant milestone. The two HIGH-risk items (data model migration and agent pipeline multi-file support) are on the critical path and cannot be parallelized. Plan for these first, with generous time buffers.

---

## Competitive Landscape for These Features

| Feature | ChatGPT | Claude | Julius AI | Spectra v0.2 | Spectra v0.3 Target |
|---------|---------|--------|-----------|---------------|-------------------|
| Chat-session-centric | Yes | Yes | Yes | NO (file tabs) | Yes |
| Multi-file per session | Yes (10/msg) | Yes (Projects) | Yes | NO | Yes |
| Chat history sidebar | Yes (grouped) | Yes (grouped) | Limited | NO | Yes (grouped) |
| Cross-file analysis | Yes (code interp) | Limited | Yes (merge/join) | NO | Partial (v0.3.1) |
| File management screen | No (in-chat only) | No (Projects) | Limited | Sidebar list | Yes (dedicated) |
| File context panel | No | Artifacts sidebar | Limited | Modal only | Right sidebar |
| Drag-drop file in chat | Yes | Yes | Yes | NO | Yes |
| Auto-title sessions | Yes | Yes | No | N/A | Yes |
| Dark mode | Yes | Yes | Yes | NO | Yes |

---

## Sources

### High Confidence (Official docs, established patterns)
- PatternFly Chatbot Conversation History: https://www.patternfly.org/patternfly-ai/chatbot/chatbot-conversation-history/
- OpenAI File Uploads FAQ: https://help.openai.com/en/articles/8555545-file-uploads-faq
- OpenAI UX Principles: https://developers.openai.com/apps-sdk/concepts/ux-principles/
- LangGraph State Management: https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025

### Medium Confidence (Verified across multiple sources)
- Julius AI multi-file analysis: https://julius.ai/articles/13-powerful-features-that-make-julius-ai-the-top-data-analysis-tool
- Julius AI merge/join guide: https://julius.ai/guides/merging_datasets
- ChatGPT file upload limits: https://www.datastudios.org/post/chatgpt-5-file-upload-limits-maximum-sizes-frequency-caps-and-plan-differences-in-late-2025
- Cross-dataset merging challenges: https://dataladder.com/merging-data-from-multiple-sources/
- AI integration across multiple data sources: https://medium.com/axel-springer-tech/ai-integration-across-multiple-data-sources-c8dbd84ffc4b
- Conversational AI UI comparison: https://intuitionlabs.ai/articles/conversational-ai-ui-comparison-2025
- Data table UX patterns: https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables

### Low Confidence (Single-source, verify during implementation)
- AI UX of analytics (GoodData): https://www.gooddata.com/blog/ux-of-ai-data-analytics/
- Chat UI design trends: https://multitaskai.com/blog/chat-ui-design/
- Session management for AI apps: https://medium.com/@aslam.develop912/master-session-management-for-ai-apps-a-practical-guide-with-backend-frontend-code-examples-cb36c676ea77
