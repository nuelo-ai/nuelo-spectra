# Requirements: Spectra

**Defined:** 2026-02-11
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.3 Requirements

Requirements for v0.3 Multi-file Conversation Support. Each maps to roadmap phases.

### Chat Sessions

- [ ] **CHAT-01**: User can create a new chat session from the left sidebar "New Chat" button
- [ ] **CHAT-02**: User is greeted with a welcome screen when opening a new chat session (friendly message asking what analysis to perform)
- [ ] **CHAT-03**: User must link at least one file to a chat session before sending messages
- [ ] **CHAT-04**: User can view chat history in the left sidebar grouped chronologically (Today, This Week, This Month, Older)
- [ ] **CHAT-05**: User can click a chat from the sidebar to open that session in the main content area
- [ ] **CHAT-06**: Chat sessions persist across browser sessions (messages and linked files preserved)
- [ ] **CHAT-07**: User can have multiple chat sessions, each with its own independent conversation context
- [ ] **CHAT-08**: Chat session title is auto-generated from the first user message
- [ ] **CHAT-09**: User is greeted with a new chat session upon login

### File Linking

- [ ] **LINK-01**: User can upload a new file directly within a chat session via an "Add File" button below the chat input
- [ ] **LINK-02**: User can link an existing (previously uploaded) file to a chat session via a file selection modal
- [ ] **LINK-03**: User can drag and drop a file from their local machine into the chat session to upload and link it
- [ ] **LINK-04**: Linked files for the current chat session are displayed in a collapsible right sidebar panel
- [ ] **LINK-05**: User can view file context (data summary, columns, row count) via an info icon on each linked file in the right sidebar
- [ ] **LINK-06**: AI agents can perform cross-file analysis across all linked files in a single query (e.g., "compare data from file A with file B")
- [ ] **LINK-07**: User can add additional files to an existing chat session (file is linked to current session after onboarding)
- [ ] **LINK-08**: Maximum of 10 files can be linked to a single chat session (enforced at API level)

### File Management

- [ ] **FILE-01**: User can access a "My Files" screen from the left sidebar
- [ ] **FILE-02**: User can view a list of all uploaded files with metadata (name, size, upload date)
- [ ] **FILE-03**: User can upload a new file from the My Files screen (triggers standard onboarding flow)
- [ ] **FILE-04**: User can view file context/details (data summary, columns, row count) for any file from My Files
- [ ] **FILE-05**: User can start a new chat session with a selected file from My Files (creates session and links file)
- [ ] **FILE-06**: User can delete a file from My Files with confirmation dialog
- [ ] **FILE-07**: User can download a previously uploaded file from My Files

### Layout & Navigation

- [ ] **NAV-01**: Left sidebar contains "New Chat" button, chronological chat history list, and "My Files" button
- [ ] **NAV-02**: Main content area displays the active chat session or My Files screen
- [ ] **NAV-03**: Right sidebar panel shows linked files for the current chat session (collapsible)
- [ ] **NAV-04**: File-tab-based navigation is replaced by sidebar-based chat session navigation
- [ ] **NAV-05**: Left sidebar is collapsible to maximize screen space

### Data Model & Backend

- [ ] **DATA-01**: Chat sessions exist as first-class database entities with their own ID, title, timestamps, and user ownership
- [ ] **DATA-02**: Files and chat sessions have a many-to-many relationship (a file can be linked to multiple sessions, a session can have multiple files)
- [ ] **DATA-03**: Chat messages belong to a session (not a file), with session-based conversation history
- [ ] **DATA-04**: Existing v0.2 conversations are migrated to the new session model (each existing file-chat becomes a session)
- [ ] **DATA-05**: LangGraph conversation memory (checkpoints) is preserved during migration to session-based thread IDs
- [ ] **DATA-06**: Deleting a file removes it from linked sessions but does not delete session messages or other linked files

### Appearance

- [ ] **THEME-01**: User can toggle between light and dark mode
- [ ] **THEME-02**: Theme preference persists across browser sessions

## Future Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Advanced Cross-File Intelligence

- **CROSS-01**: Session-level multi-file query suggestions based on cross-file schema analysis
- **CROSS-02**: Smart file suggestion when starting empty chat (recommend recently used files)
- **CROSS-03**: Advanced cross-file join intelligence with automatic relationship detection

### Production Hardening

- **PROD-01**: Query safety filter in Manager Agent (block PII extraction, prompt injection)
- **PROD-02**: Pydantic structured output for agent JSON responses
- **PROD-03**: Dokploy Docker deployment package

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Automatic cross-file joins without user intent | Silently merging datasets leads to wrong results (schema mismatches, Cartesian products) |
| Conversation branching/forking | Extremely complex UX and data model, not requested |
| Real-time collaborative editing | Multi-user on same session adds massive complexity |
| Folder/directory organization for files | Over-engineering — users will have 5-50 files, not thousands |
| Embedding/vector search across files | Architecturally different from structured data analysis |
| Session rename from sidebar | Can be added as polish in future milestone |
| Cross-session memory persistence | Context pollution risk; session-scoped memory by design |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (populated during roadmap creation) | | |

**Coverage:**
- v0.3 requirements: 30 total
- Mapped to phases: 0
- Unmapped: 30

---
*Requirements defined: 2026-02-11*
*Last updated: 2026-02-11 after initial definition*
