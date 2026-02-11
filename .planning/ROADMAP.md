# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** — Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** — Phases 7-13 (shipped 2026-02-10)
- 🚧 **v0.3 Multi-file Conversation Support** — Phases 14-18 (in progress)

## Phases

<details>
<summary>✅ v0.1 Beta MVP (Phases 1-6) — SHIPPED 2026-02-06</summary>

- [x] Phase 1: Foundation Setup (6/6 plans) — completed 2026-02-06
- [x] Phase 2: File Upload & AI Profiling (6/6 plans) — completed 2026-02-06
- [x] Phase 3: Multi-File Management (4/4 plans) — completed 2026-02-06
- [x] Phase 4: AI Agent System & Code Generation (8/8 plans) — completed 2026-02-06
- [x] Phase 5: Secure Code Execution & E2B (6/6 plans) — completed 2026-02-06
- [x] Phase 6: Interactive Data Cards & Frontend Polish (6/6 plans) — completed 2026-02-06

</details>

<details>
<summary>✅ v0.2 Intelligence & Integration (Phases 7-13) — SHIPPED 2026-02-10</summary>

- [x] Phase 7: Multi-LLM Provider Infrastructure (5/5 plans) — completed 2026-02-09
- [x] Phase 8: Session Memory with PostgreSQL Checkpointing (2/2 plans) — completed 2026-02-08
- [x] Phase 9: Manager Agent with Intelligent Query Routing (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Smart Query Suggestions (2/2 plans) — completed 2026-02-08
- [x] Phase 11: Web Search Tool Integration (3/3 plans) — completed 2026-02-09
- [x] Phase 12: Production Email Infrastructure (2/2 plans) — completed 2026-02-09
- [x] Phase 13: Migrate Web Search from Serper.dev to Tavily (2/2 plans) — completed 2026-02-09

</details>

### v0.3 Multi-file Conversation Support

**Goal:** Restructure the UX from file-tab-centric to chat-session-centric, enabling multi-file conversations and cross-file analysis

#### Phase 14: Database Foundation & Migration

**Goal:** Chat sessions exist as first-class database entities with proper data model and migration strategy

**Dependencies:** None (foundational)

**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06

**Success Criteria:**
1. Chat sessions can be created, read, updated, and deleted via API endpoints
2. Files can be linked to multiple sessions and sessions can have multiple files (many-to-many relationship working)
3. Chat messages belong to sessions (not files) and display correctly when session is opened
4. Existing v0.2 conversations are accessible in the new session model with original messages intact
5. LangGraph conversation memory works with session-based thread IDs (old conversations can continue)

---

#### Phase 15: Agent System Enhancement (Multi-File Support)

**Goal:** AI agents can perform cross-file analysis across all linked files in a single query

**Dependencies:** Phase 14 (requires session model and file linking)

**Requirements:** LINK-06

**Success Criteria:**
1. User can ask "compare data from sales.csv with customers.xlsx" and agent generates code referencing both files
2. Agent-generated Python code uses named DataFrames (df_sales, df_customers) not generic df
3. E2B sandbox executes multi-file code without memory overflow for up to 5 files
4. Context Assembler service provides compact multi-file metadata within token budget
5. Manager Agent routes multi-file queries correctly (MEMORY_SUFFICIENT vs NEW_ANALYSIS)

---

#### Phase 16: Frontend Restructure (Session-Centric UX)

**Goal:** Users navigate via chat sessions in a sidebar, not file tabs

**Dependencies:** Phase 14 (requires session APIs)

**Requirements:** NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, CHAT-01, CHAT-02, CHAT-04, CHAT-05, CHAT-09

**Success Criteria:**
1. User sees left sidebar with "New Chat" button, chronological chat history, and "My Files" button
2. User can create a new chat session from sidebar and see welcome screen
3. User can click any chat from history sidebar to open that session in main content area
4. Chat history displays grouped by time (Today, This Week, This Month, Older) with most recent first
5. User sees collapsible right sidebar panel showing linked files when chat session is active
6. File-tab navigation is completely replaced by session-based navigation (no tabs visible)

---

#### Phase 17: File Management & Linking

**Goal:** Users can manage files independently and link them to chat sessions

**Dependencies:** Phase 14 (requires session model), Phase 16 (requires My Files route)

**Requirements:** FILE-01, FILE-02, FILE-03, FILE-04, FILE-05, FILE-06, FILE-07, LINK-01, LINK-02, LINK-03, LINK-04, LINK-05, LINK-07, LINK-08

**Success Criteria:**
1. User can access "My Files" screen from sidebar showing all uploaded files with metadata
2. User can upload a new file from My Files screen and it completes onboarding flow
3. User can view file context details (data summary, columns, row count) from My Files
4. User can start a new chat session with a selected file from My Files (creates session and links file)
5. User can delete a file with confirmation dialog and file is removed from linked sessions without deleting messages
6. User can add files to chat session via "Add File" button, file selection modal, or drag-and-drop
7. User sees file info icon in right sidebar panel showing context for each linked file
8. User cannot link more than 10 files to a single session (enforced with error message)

---

#### Phase 18: Integration & Polish

**Goal:** All features work together seamlessly with proper constraints and visual polish

**Dependencies:** Phase 14, Phase 15, Phase 16, Phase 17 (requires all layers complete)

**Requirements:** CHAT-03, CHAT-06, CHAT-07, CHAT-08, THEME-01, THEME-02

**Success Criteria:**
1. User cannot send messages to a chat session until at least one file is linked (enforced with clear message)
2. Chat sessions persist across browser sessions (messages and linked files preserved after login)
3. User can have multiple independent chat sessions each with its own conversation context
4. Chat session title is auto-generated from first user message and displays in sidebar
5. User can toggle between light and dark mode and theme preference persists across sessions

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation Setup | v0.1 | 6/6 | Complete | 2026-02-06 |
| 2. File Upload & AI Profiling | v0.1 | 6/6 | Complete | 2026-02-06 |
| 3. Multi-File Management | v0.1 | 4/4 | Complete | 2026-02-06 |
| 4. AI Agent System & Code Generation | v0.1 | 8/8 | Complete | 2026-02-06 |
| 5. Secure Code Execution & E2B | v0.1 | 6/6 | Complete | 2026-02-06 |
| 6. Interactive Data Cards | v0.1 | 6/6 | Complete | 2026-02-06 |
| 7. Multi-LLM Infrastructure | v0.2 | 5/5 | Complete | 2026-02-09 |
| 8. Session Memory | v0.2 | 2/2 | Complete | 2026-02-08 |
| 9. Manager Agent Routing | v0.2 | 3/3 | Complete | 2026-02-08 |
| 10. Smart Query Suggestions | v0.2 | 2/2 | Complete | 2026-02-08 |
| 11. Web Search Integration | v0.2 | 3/3 | Complete | 2026-02-09 |
| 12. Production Email | v0.2 | 2/2 | Complete | 2026-02-09 |
| 13. Migrate Web Search (Tavily) | v0.2 | 2/2 | Complete | 2026-02-09 |
| 14. Database Foundation & Migration | v0.3 | 0/? | Pending | — |
| 15. Agent System Enhancement | v0.3 | 0/? | Pending | — |
| 16. Frontend Restructure | v0.3 | 0/? | Pending | — |
| 17. File Management & Linking | v0.3 | 0/? | Pending | — |
| 18. Integration & Polish | v0.3 | 0/? | Pending | — |
