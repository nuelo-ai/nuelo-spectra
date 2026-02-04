# Roadmap: Spectra v1.0 MVP

**Milestone:** v1.0 MVP — Ship minimum viable product that proves core value
**Core Value:** Accurate data analysis through correct, safe Python code generation
**Total Phases:** 6
**Requirements Coverage:** 42/42 (100%)
**Created:** 2026-02-02

## Overview

This roadmap delivers Spectra's MVP in 6 phases, structured to prove the core value proposition (accurate AI-powered data analysis) while maintaining security and user experience quality. The phase order follows a strict dependency chain: authentication enables file upload, file upload enables AI analysis, streaming infrastructure supports real-time UX, sandbox security protects code execution, and frontend UI brings it all together. Each phase delivers a complete, verifiable capability with observable success criteria.

**Phase strategy:** Backend-first to prove core value before polishing UI. Authentication and security are designed from day one to avoid costly retrofits. Multi-agent orchestration built before UI to validate accuracy promise. Streaming infrastructure tested independently before frontend integration.

## Phases

### Phase 1: Backend Foundation & Authentication
**Goal:** Users can securely access platform with isolated data storage

**Dependencies:** None (foundation phase)

**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05

**Plans:** 4 plans

Plans:
- [x] 01-01-PLAN.md -- Project skeleton, config, database models, Alembic migrations
- [x] 01-02-PLAN.md -- Auth endpoints (signup, login, refresh), JWT security, get_current_user dependency
- [x] 01-03-PLAN.md -- Password reset flow, email service, health check, CORS, final wiring
- [x] 01-04-PLAN.md -- Gap closure: Fix email service dev mode detection for password reset

**Success Criteria:**
1. User can create account with email and password
2. User can log in with email and password and session persists across browser refresh
3. User can reset forgotten password via email link
4. User data is fully isolated (each user sees only their own files and chat history)
5. Backend API is deployed with health check endpoint responding

**Deliverables:**
- FastAPI application skeleton with async SQLAlchemy 2.0
- PostgreSQL database with Users, Files, ChatMessages tables
- JWT-based authentication (email/password using PyJWT + pwdlib Argon2)
- User-isolated file storage paths (/uploads/{user_uuid}/)
- Password reset via email flow
- Session persistence with JWT refresh tokens
- Database migrations with Alembic

**Technical Notes:**
- Use PyJWT and pwdlib (passlib/python-jose are abandoned as of 2026)
- Design user_id filters from start to prevent IDOR vulnerabilities
- All database queries include mandatory user_id scoping

---

### Phase 2: File Upload & Management
**Goal:** Users can upload and manage multiple data files with tabbed interface

**Dependencies:** Phase 1 (requires authentication for user isolation)

**Requirements:** FILE-01, FILE-02, FILE-03, FILE-07, FILE-08, FILE-09, FILE-10

**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md -- Install dependencies (aiofiles, pandas, openpyxl, xlrd), extend config, create file schemas and file service
- [x] 02-02-PLAN.md -- File router, chat message support (schemas/service/router), main.py wiring with MultiPartParser config

**Success Criteria:**
1. User can upload Excel (.xlsx, .xls) and CSV files up to 50MB
2. System validates file format and structure before accepting upload
3. User can view list of uploaded files with metadata (name, size, upload date)
4. User can delete files with confirmation dialog
5. Each file has its own chat tab in the interface
6. User can switch between file tabs with independent chat histories maintained

**Deliverables:**
- File upload endpoint with format validation (pandas read_csv/read_excel)
- User-isolated storage with UUID filenames
- File metadata persistence (Files table)
- Per-file chat history schema (ChatMessage.file_id foreign key)
- File list API with metadata
- File deletion endpoint with cascade delete for chat history
- 50MB upload size limit enforcement

**Technical Notes:**
- ChatMessage table references both user_id and file_id for isolation
- Validate file structure on upload (catch corrupted files early)
- Use UUIDs for file storage paths to prevent enumeration attacks

---

### Phase 3: AI Agents & Orchestration
**Goal:** AI agents accurately analyze data and generate validated Python code

**Dependencies:** Phase 2 (requires uploaded files to analyze)

**Requirements:** AGENT-03, AGENT-04, AGENT-05, AGENT-06, AGENT-08, FILE-04, FILE-05, FILE-06

**Plans:** 5 plans

Plans:
- [x] 03-01-PLAN.md -- Install LangGraph dependencies, YAML configs (prompts + allowlist), state schemas, config loader
- [x] 03-02-PLAN.md -- Onboarding Agent with data profiling and LLM summary, File model migration, agent service layer
- [x] 03-03-PLAN.md -- Code Checker AST validation (TDD) with allowlist enforcement
- [x] 03-04-PLAN.md -- Coding Agent, Data Analysis Agent, LangGraph chat workflow with conditional routing
- [x] 03-05-PLAN.md -- Wire agents into file upload and chat routers, full API integration

**Success Criteria:**
1. Onboarding Agent analyzes uploaded data structure and generates natural language summary
2. User can provide optional context during upload to improve AI interpretation
3. User can refine AI's understanding of the data after initial analysis
4. Coding Agent generates Python scripts based on user queries
5. Code Checker Agent validates generated code for safety and correctness before execution
6. Data Analysis Agent interprets code execution results and generates explanations
7. AI agent system prompts are stored in YAML configuration files for easy tuning

**Deliverables:**
- LangGraph workflow orchestrating 4 agents (Onboarding, Coding, Code Checker, Data Analysis)
- Onboarding Agent with data profiling logic (pandas describe, dtypes, missing values)
- Coding Agent with Python code generation from natural language
- Code Checker Agent with AST validation and function allowlist checking
- Data Analysis Agent for result interpretation
- YAML configuration files for agent system prompts
- LangSmith integration for agent debugging and tracing
- Token usage monitoring and max_tokens caps

**Technical Notes:**
- LangGraph conditional edges: Code Checker validates -> execute or regenerate
- Code Checker uses AST analysis to detect hallucinated pandas functions
- YAML prompt configs enable fast iteration without code changes
- Monitor token costs from day one (output tokens 3-10x input)

---

### Phase 4: Streaming Infrastructure
**Goal:** Users see AI responses stream in real-time with reliable connection handling

**Dependencies:** Phase 3 (requires AI agents to generate streaming content)

**Requirements:** AGENT-01, AGENT-02, AGENT-07

**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md -- SSE event types, streaming config, sse-starlette install, inject stream writers into agent nodes
- [x] 04-02-PLAN.md -- Streaming service function (astream), SSE endpoint, atomic chat history persistence with metadata

**Success Criteria:**
1. User can ask questions about their data in natural language through chat interface
2. System streams AI responses in real-time showing thinking process
3. Chat history persists per file across browser sessions
4. Streaming connections auto-reconnect if network drops during long queries
5. Failed streams save nothing to database (clean failure state, no partial results)

**Deliverables:**
- FastAPI SSE streaming endpoint (/chat/stream) with sse-starlette
- Next.js API route proxy for SSE to frontend
- EventSource client with auto-reconnect logic
- Atomic chat history persistence on stream completion (save nothing on failure)
- Disconnect detection with graceful error handling
- Chat history persistence to PostgreSQL
- Streaming error event types (code_error, network_error, timeout)

**Technical Notes:**
- SSE preferred over WebSockets (simpler, auto-reconnect built-in)
- Save on completion only: atomic writes after successful stream, clean rollback on failure
- Test with mobile networks to validate reconnection behavior
- Yield error events instead of raising exceptions (keeps stream alive)

---

### Phase 5: Sandbox Security & Code Execution
**Goal:** Python code executes securely with multi-layer isolation protecting user data

**Dependencies:** Phase 3 (requires generated code to execute), Phase 4 (requires streaming to show execution progress)

**Requirements:** EXEC-01, EXEC-02, EXEC-03, EXEC-04, EXEC-05, EXEC-06, EXEC-07, AGENT-09

**Plans:** 2 plans

Plans:
- [x] 05-01-PLAN.md -- SandboxRuntime Protocol abstraction, E2BSandboxRuntime implementation, ExecutionResult models, sandbox config
- [x] 05-02-PLAN.md -- Replace execute_code_stub with E2B sandbox execution, wire file data, code display streaming, execution error retry

**Success Criteria:**
1. Python code executes in E2B microVM sandbox environment
2. Sandbox prevents risky operations (file deletion, table drops, network access)
3. Code execution is resource-limited (CPU, memory, timeout enforced)
4. User data in sandbox is isolated (no access to other users' data)
5. Generated code is displayed with explanation before execution
6. Only allowed Python libraries from YAML configuration are permitted
7. Code Checker validates that generated code only imports allowed libraries
8. When code execution fails, system automatically retries with regenerated code (max retry limit enforced)

**Deliverables:**
- E2B microVM integration with Firecracker runtime
- Multi-layer sandbox defense: RestrictedPython AST -> Docker -> E2B/gVisor
- Resource limits configuration (memory, CPU, timeout)
- Network isolation (--network=none for Docker layer)
- YAML library allowlist configuration
- Code Checker library validation against allowlist
- Auto-retry logic with error analysis and code regeneration
- Maximum retry limit (3 attempts) to prevent infinite loops
- Read-only filesystem for sandbox containers
- User data mounting with per-user isolation

**Technical Notes:**
- Multi-layer defense is non-negotiable (RestrictedPython alone is insecure)
- E2B provides VM-like isolation (~150ms boot time with Firecracker)
- Fallback to self-hosted gVisor if E2B pricing exceeds budget
- Code Checker validates AST before execution (detect unsafe patterns)
- Monitor CVE alerts for container runtime vulnerabilities

---

### Phase 6: Frontend UI & Interactive Data Cards
**Goal:** Users interact with polished interface featuring streaming Data Cards and file management

**Dependencies:** Phase 2 (file upload UI), Phase 4 (streaming integration), Phase 5 (code execution for Data Cards)

**Requirements:** CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06, CARD-07, CARD-08, SETT-01, SETT-02, SETT-03

**Plans:** 16 plans

Plans:
- [x] 06-01-PLAN.md -- Scaffold Next.js 16 project, install dependencies, shadcn/ui init, auth pages, API client, TypeScript types
- [x] 06-02-PLAN.md -- Backend settings endpoints (PATCH /auth/me, POST /auth/change-password)
- [x] 06-03-PLAN.md -- File sidebar, drag-drop upload with progress, file info modal, tab store (Zustand)
- [x] 06-04-PLAN.md -- Chat interface, SSE streaming hook, message rendering, typing indicator
- [x] 06-05-PLAN.md -- Data Cards with progressive rendering, TanStack Table (sorting/filtering/pagination)
- [x] 06-06-PLAN.md -- CSV/Markdown download buttons, Python code display with copy
- [x] 06-07-PLAN.md -- Settings page (profile editing, password change, account info)
- [x] 06-08-PLAN.md -- Visual polish (animations, loading states, transitions) + end-to-end verification
- [x] 06-09-PLAN.md -- Gap closure: Wire ChatInterface into dashboard page
- [x] 06-10-PLAN.md -- Gap closure: Backend logging config + PostgresSaver context manager fix
- [x] 06-11-PLAN.md -- Gap closure: FileUploadZone race condition fix + analysis display
- [x] 06-12-PLAN.md -- Gap closure: Profile update immediate nav refresh
- [x] 06-13-PLAN.md -- UAT retest: Re-verify all tests after gap closure fixes
- [x] 06-14-PLAN.md -- Gap closure: Fix useFileSummary query disabling + file list refetch
- [ ] 06-15-PLAN.md -- Gap closure: Markdown rendering, modal sizing, FILE-05/FILE-06 UI, sidebar double-refetch fix
- [ ] 06-16-PLAN.md -- UAT retest: Verify all upload flow fixes and FILE-05/FILE-06 implementation

**Success Criteria:**
1. Query results display as Data Cards with streaming responses appearing progressively
2. Data Cards show Query Brief, Data Table, and AI Explanation sections
3. Data tables within cards are sortable and filterable
4. Results stream progressively while AI is still processing
5. Visual polish includes smooth animations, loading states, and transitions
6. User can view Python code generated for each analysis in Data Card
7. User can download data tables as CSV from Data Cards
8. User can download analysis report as Markdown from Data Cards
9. User can view and edit profile information (first name, last name)
10. User can view account details (email, account creation date)
11. User can change password from settings page

**Deliverables:**
- Next.js 16 frontend with App Router and React 19
- File upload component with drag-and-drop UI
- Tabbed file interface with chat history per tab
- Chat UI with streaming message components
- Interactive Data Cards with progressive rendering
- Sortable/filterable data tables (TanStack Table)
- Code display component with syntax highlighting
- CSV export from Data Card tables
- Markdown export for analysis reports
- Settings page with profile editing
- Password change form
- Visual polish: animations, loading states, transitions

**Technical Notes:**
- Use shadcn/ui components for consistent design system
- TanStack Query for server state management
- Zustand for client state (current file tab, UI state)
- EventSource API for SSE streaming from Next.js API routes
- Progressive rendering for Data Cards (stream sections as they complete)
- Test streaming UX on slow networks (throttle to 3G for testing)

---

## Progress

| Phase | Status | Requirements | Completion |
|-------|--------|--------------|------------|
| **1 - Backend Foundation & Authentication** | Complete | 5/5 | 100% |
| **2 - File Upload & Management** | Complete | 7/7 | 100% |
| **3 - AI Agents & Orchestration** | Complete | 8/8 | 100% |
| **4 - Streaming Infrastructure** | Complete | 3/3 | 100% |
| **5 - Sandbox Security & Code Execution** | Complete | 8/8 | 100% |
| **6 - Frontend UI & Interactive Data Cards** | UAT Gap Closure | 12/12 | 95% (upload flow + FILE-05/FILE-06 UAT gaps) |

**Overall Progress:** 100% requirements coded (42/42) - UAT gap closure in progress for upload flow display + FILE-05/FILE-06 UI

---

## Dependency Graph

```
Phase 1: Backend Foundation & Authentication
    |
Phase 2: File Upload & Management
    |
Phase 3: AI Agents & Orchestration
    |
Phase 4: Streaming Infrastructure
    \
Phase 5: Sandbox Security & Code Execution
    |
Phase 6: Frontend UI & Interactive Data Cards
```

**Critical Path:** 1 -> 2 -> 3 -> 4 -> 5 -> 6 (strictly sequential)

**Rationale:**
- Phase 1 blocks all others (authentication required for user isolation)
- Phase 2 blocks Phase 3 (agents need files to analyze)
- Phase 3 blocks Phase 4 (streaming needs AI content to stream)
- Phase 4 and Phase 3 block Phase 5 (sandbox needs code to execute and streaming to show progress)
- Phase 5 blocks Phase 6 (Data Cards display code execution results)

---

## Success Metrics

**MVP success requires:**
- All 42 v1.0 requirements completed
- All phase success criteria verified as TRUE
- Security audit passed (sandbox escape testing, IDOR vulnerability testing)
- Performance benchmarks met (streaming latency <2s, file upload <10s for 50MB)

**Core value validation:**
- Users can upload data and get accurate analysis
- Generated Python code is correct (validated by Code Checker)
- Sandbox prevents security breaches
- Streaming UX feels responsive (ChatGPT-quality)

---

*Last updated: 2026-02-04 - Phase 6 UAT gap closure: Plans 06-15 and 06-16 revised to address diagnosed root causes (markdown rendering, modal sizing, FILE-05/FILE-06 UI, sidebar double-refetch)*
*Next step: Execute 06-15 then 06-16 to close remaining UAT gaps*
