# Project State: Spectra v1.0 MVP

**Last Updated:** 2026-02-04
**Milestone:** v1.0 MVP
**Status:** Phase 6 In Progress - Frontend Foundation Complete

---

## Project Reference

**Core Value:**
Accurate data analysis through correct, safe Python code generation. If the code is wrong or the sandbox isn't secure, the entire product fails.

**Current Focus:**
Phase 6 in progress. Frontend foundation, auth UI, Zustand tab store, and chat interface with SSE streaming complete. Ready for Data Cards visualization implementation.

**Key Constraint:**
Timeline: 2-4 weeks for MVP delivery. Single developer. Security (sandbox isolation) is non-negotiable for production.

---

## Current Position

**Phase:** 6 of 6 - Frontend UI & Interactive Data Cards
**Plan:** 4 of 12 plans complete
**Status:** In Progress

**Progress Bar:**
```
[████████████████████░] 83% (36/42 requirements completed)

Phase 1: [██████████] 3/3 plans COMPLETE (database + auth + password reset)
Phase 2: [██████████] 2/2 plans COMPLETE (file service + API routers)
Phase 3: [██████████] 5/5 plans COMPLETE (foundation + onboarding + validation + coding + integration)
Phase 4: [██████████] 2/2 plans COMPLETE (SSE events + streaming endpoint + atomic persistence)
Phase 5: [██████████] 2/2 plans COMPLETE (SandboxRuntime Protocol + E2B execution integration)
Phase 6: [████░░░░░░] 6/12 requirements (foundation + auth + tabs + chat interface)
```

**Last activity:** 2026-02-04 - Completed 06-04: Chat Interface with SSE Streaming

**Next Action:**
Continue Phase 6 implementation: Data Cards visualization, file upload UI, sidebar integration, settings page

---

## Performance Metrics

**Velocity:** 1 phase/session (3 plans executed in ~13 minutes)
**Blockers:** None
**Risks:** None identified yet

**Timeline Health:**
- Target: 2-4 weeks for v1.0 MVP
- Elapsed: 0 days
- Projected: On track (pending phase planning)

---

## Accumulated Context

### Key Decisions

| Date | Decision | Impact |
|------|----------|--------|
| 2026-02-04 | POST-based SSE with fetch + ReadableStream | EventSource doesn't support POST body; using fetch with ReadableStream for SSE allows sending user message in request. Manual SSE parsing required. Implemented in 06-04. |
| 2026-02-04 | Optimistic UI updates for user messages | User messages appear instantly via queryClient.setQueryData before server persistence; improves perceived responsiveness. useAddLocalMessage helper. Implemented in 06-04. |
| 2026-02-04 | Invalidate + refetch on stream completion | Server-side atomic persistence happens after stream completes; frontend invalidates query to fetch persisted messages. Implemented in 06-04. |
| 2026-02-04 | AbortController for stream cleanup | Prevents memory leaks from abandoned streams; cleanup on component unmount or new stream start. Implemented in 06-04. |
| 2026-02-04 | Status messages mapped from event types | User-friendly agent phase descriptions ("Generating code...") instead of raw event types (coding_started). Improves UX clarity. Implemented in 06-04. |
| 2026-02-04 | React Context for auth state | Auth state managed via React Context (not Zustand); changes infrequently so Context is sufficient. Auth accessed via useAuth() hook throughout app. Implemented in 06-01. |
| 2026-02-04 | localStorage for JWT token storage | Tokens stored in localStorage with spectra_ prefix; simple persistence across sessions. Vulnerable to XSS but acceptable for v1.0 MVP. Implemented in 06-01. |
| 2026-02-04 | Turbopack requires .tsx for JSX | Files with JSX must use .tsx extension, not .ts. Turbopack parser fails on JSX in .ts files. Renamed useAuth.ts → useAuth.tsx. Implemented in 06-01. |
| 2026-02-04 | API proxy via Next.js rewrites | Frontend /api/* requests proxied to localhost:8000 via Next.js rewrites; avoids CORS configuration. Simple fetch('/api/...') calls. Implemented in 06-01. |
| 2026-02-04 | Automatic token refresh on 401 | API client intercepts 401 errors, calls /auth/refresh, retries original request with new token; seamless UX. Implemented in 06-01. |
| 2026-02-04 | TypeScript types mirror backend schemas | Frontend types in src/types/ exactly match backend Pydantic schemas; ensures type safety across API boundary. Implemented in 06-01. |
| 2026-02-04 | shadcn/ui with default style | shadcn/ui initialized with default style, slate base color, CSS variables; modern accessible component library. Implemented in 06-01. |
| 2026-02-04 | ProfileUpdateRequest requires at least one field | model_post_init validation ensures either first_name or last_name provided; prevents empty PATCH requests. Implemented in 06-02. |
| 2026-02-04 | change_password returns boolean not exception | Service layer returns False on wrong password, router controls HTTP 401; cleaner separation of concerns. Implemented in 06-02. |
| 2026-02-04 | CurrentUser dependency on profile endpoints | Both PATCH /auth/me and POST /auth/change-password require authentication; consistent with existing auth patterns. Implemented in 06-02. |
| 2026-02-03 | asyncio.to_thread wraps E2B calls | E2B SDK is synchronous; wrapping execute() in asyncio.to_thread() prevents blocking LangGraph's async event loop during sandbox execution. Pattern established in 05-02. |
| 2026-02-03 | Code display before execution | code_display event emitted with message "Code validated, preparing execution..." BEFORE execution starts. Satisfies EXEC-05 requirement. Implemented in 05-02. |
| 2026-02-03 | File reading error handling | FileNotFoundError and IOError caught and routed to halt with user-friendly messages ("Re-upload your file and try again"). Prevents unhandled exceptions. Implemented in 05-02. |
| 2026-02-03 | Execution error vs validation error distinction | Coding Agent provides execution-specific feedback ("failed during execution") vs validation feedback ("validation issues"). Improves retry intelligence. Implemented in 05-02. |
| 2026-02-03 | Tailored halt messages | halt_node checks error type (execution_failed, file_not_found, file_read_error, max_retries_exceeded) and returns appropriate user guidance. Implemented in 05-02. |
| 2026-02-03 | SandboxRuntime Protocol abstraction | Protocol defines execute() and cleanup() interface; decouples agent code from E2B SDK; enables runtime swapping (E2B → Docker+gVisor) without refactoring. Implemented in 05-01. |
| 2026-02-03 | Context manager cleanup for E2B | Sandbox.create() context manager ensures guaranteed microVM shutdown even on errors; prevents resource leaks. Pattern established in 05-01. |
| 2026-02-03 | E2B errors never propagate | E2BSandboxRuntime catches all SDK exceptions and returns ExecutionResult.error; caller always receives structured result. Pattern established in 05-01. |
| 2026-02-03 | Synchronous sandbox API with async wrapper deferred | execute() is synchronous; asyncio.to_thread wrapper deferred to 05-02 agent integration. Simplifies initial implementation. |
| 2026-02-03 | E2B Cloud over self-hosted gVisor | Single developer: E2B reduces operational complexity (~150ms boot time with Firecracker); self-hosted gVisor requires significant DevOps expertise and ongoing maintenance. Fallback: migrate to gVisor if E2B pricing exceeds budget threshold ($200/mo). Sandbox lifecycle: fresh microVM per query for maximum isolation; cost vs security tradeoff favors VM-per-query architecture. |
| 2026-02-03 | Fresh database session for stream persistence | async_session_maker() creates new session for chat history writes; prevents connection timeout on long streams (2-3 min) |
| 2026-02-03 | Failed streams save nothing to database | Clean failure state - only successful stream completions appear in chat history |
| 2026-02-03 | Stream metadata in assistant message | duration_ms, retry_count, errors stored in metadata_json for debugging and analytics |
| 2026-02-03 | File ownership verified before stream starts | Fast fail with HTTP 404 before event generator starts; proper error vs SSE event |
| 2026-02-03 | StreamEventType enum with 10 event types | 4 status + 2 progress + 2 content + 2 terminal events cover all agent workflow transitions |
| 2026-02-03 | Stream timeout 180 seconds | 3-minute timeout balances patience for complex queries vs user frustration |
| 2026-02-03 | User-facing messages hide agent names | "Generating code..." not "Coding Agent thinking..." - simpler UX |
| 2026-02-03 | get_stream_writer() in all agent nodes | LangGraph streaming instrumentation at node entry points; no-op outside astream() |
| 2026-02-03 | psycopg-binary for PostgresSaver | LangGraph checkpoint requires psycopg3 with binary; fixed import error |
| 2026-02-03 | Two-stage validation (AST + LLM) in Code Checker | AST first (fast syntax/security), LLM second (logical correctness); optimizes speed |
| 2026-02-03 | Command routing for conditional edges | LangGraph Command pattern cleaner than add_conditional_edges callback |
| 2026-02-03 | Execute stub with restricted namespace | Development stub uses exec() with empty __builtins__; Phase 5 adds OS-level isolation |
| 2026-02-03 | max_steps=3 circuit breaker | Default limit prevents infinite retry loops and runaway LLM costs |
| 2026-02-03 | Code block extraction from markdown | Handles LLMs that wrap code in ```python blocks vs raw code |
| 2026-02-03 | AST NodeVisitor pattern for code validation | Python's ast module provides structured code analysis without execution; safer than regex |
| 2026-02-03 | TDD for Code Checker | 37 tests document every security rule; provides regression prevention |
| 2026-02-03 | data_summary/user_context nullable on File model | Populated asynchronously after upload; NULL until Onboarding Agent runs |
| 2026-02-03 | asyncio.to_thread for pandas profiling | Prevents event loop blocking during data analysis operations |
| 2026-02-03 | v1 always appends user context | Simple append pattern; v2 will ask user to re-run or append |
| 2026-02-03 | Agent service layer pattern | Service functions bridge API endpoints and agent logic for clean separation |
| 2026-02-03 | LangGraph TypedDict for state (not Pydantic) | LangGraph requires TypedDict; compatible with StateGraph |
| 2026-02-03 | Multi-provider LLM factory pattern | Agents work with Anthropic/OpenAI/Google via BaseChatModel interface |
| 2026-02-03 | YAML for agent prompts and allowlists | Externalized config enables prompt iteration without deployment |
| 2026-02-03 | agent_max_retries=3 default | Circuit breaker prevents infinite retry loops and runaway costs |
| 2026-02-03 | Lazy imports in LLM factory | Users only need SDK for their chosen provider |
| 2026-02-03 | Background onboarding with asyncio.create_task | Upload response immediate; onboarding runs async with new session |
| 2026-02-03 | Thread ID format: file_{file_id}_user_{user_id} | Per-file chat memory isolation via LangGraph checkpointer |
| 2026-02-03 | Separate AI query vs direct message endpoints | POST /chat/{file_id}/query for AI, POST /chat/{file_id}/messages for direct |
| 2026-02-03 | GET /files/{file_id}/summary for status polling | Frontend checks onboarding completion before enabling chat |
| 2026-02-03 | MultiPartParser configured before app creation | Starlette caches parser at import; must override 1MB limit at module level |
| 2026-02-03 | Chat endpoints verify file ownership twice | GET/POST chat call FileService.get_user_file first; prevents cross-user access |
| 2026-02-03 | Extension validation in router layer | Router validates before service call; separation of HTTP vs business logic |
| 2026-02-03 | Chunked file uploads (1MB chunks) | Prevents OOM on large files; size limit checked during upload |
| 2026-02-03 | Pandas validation in thread pool | asyncio.to_thread avoids blocking event loop; validates only 5 rows |
| 2026-02-03 | SQL delete for cascade reliability | ORM session.delete unreliable in async; SQL ensures cascade works |
| 2026-02-03 | User-isolated file storage structure | {upload_dir}/{user_id}/ prevents path traversal, enables quotas |
| 2026-02-03 | Forgot-password always returns 202 | Prevents email enumeration attacks; same response for exists/not-exists |
| 2026-02-03 | Reset tokens expire in 10 minutes | Short window reduces attack surface; balances security with usability |
| 2026-02-03 | Email service dev mode fallback | Console logging when no API key set; enables local dev without email account |
| 2026-02-03 | CORS explicit origins (not wildcard) | Security: wildcard rejected by browser when allow_credentials=True |
| 2026-02-03 | Lifespan handler for engine disposal | Prevents connection pool leaks; FastAPI best practice for cleanup |
| 2026-02-03 | JWT tokens contain only user_id (no PII) | Minimizes data exposure if token intercepted; user_id in 'sub' claim only |
| 2026-02-03 | pwdlib[argon2] for password hashing | Modern Argon2id algorithm; passlib is abandoned; prevents timing attacks |
| 2026-02-03 | Explicit algorithm in jwt.decode() | Security: prevents 'none' algorithm attack by enforcing HS256 |
| 2026-02-03 | JSON login body (not OAuth2 form) | Frontend compatibility; OAuth2PasswordBearer still used for token extraction |
| 2026-02-03 | PostgreSQL in Docker for development | Consistent environment without local installation; using postgres:16-alpine container |
| 2026-02-03 | SQLAlchemy 2.0 with expire_on_commit=False | Prevents MissingGreenlet errors in async sessions |
| 2026-02-03 | UUID primary keys for all models | Prevents enumeration attacks, enables distributed ID generation |
| 2026-02-02 | Roadmap created with 6 phases | 100% coverage of 42 v1.0 requirements |
| 2026-02-02 | Backend-first strategy | Prove core value before polishing frontend |
| 2026-02-02 | Security designed from day one | Multi-layer sandbox + per-user data isolation |

### Active Todos

**Immediate (Phase 6 Execution):**
- [x] Next.js frontend foundation with auth UI - completed in 06-01
- [x] User settings endpoints (profile update, password change) - completed in 06-02
- [x] Zustand tab store and file manager hooks - completed in 06-03
- [x] Chat interface with SSE streaming - completed in 06-04
- [ ] Execute 06-05: Data Cards visualization

**Phase 6 Progress:**
- [x] Frontend foundation (Next.js 16, TypeScript, Tailwind CSS 4, shadcn/ui) - 06-01 complete
- [x] Auth UI (login, register, forgot/reset password, protected routes) - 06-01 complete
- [x] API client with token refresh - 06-01 complete
- [x] User settings endpoints and UI - 06-02 complete
- [x] Zustand tab store for multi-tab file management - 06-03 complete
- [x] Chat interface with SSE streaming, typing indicator, auto-scroll - 06-04 complete
- [ ] Data Cards visualization with progressive rendering - 06-05 planned

**Phase 3 Enhancements (Backlog):**
- [ ] Add OpenRouter and Ollama LLM provider support (see `.planning/todos/pending/2026-02-03-add-openrouter-and-ollama-llm-support.md`)

**Completed:**
- [x] Make agent LLM provider configurable - integrated into Phase 3 plans (03-01, 03-02, 03-04)

**Deferred to Later Phases:**
- Frontend UI components (Phase 6)
- Data Card visualization design (Phase 6)
- Settings page implementation (Phase 6)

### Blockers

**None currently.**

**Mitigations in Place:**
- Phase 5: E2B Cloud architecture documented with self-hosted gVisor fallback option
- Budget: LLM token costs with 4-agent orchestration (mitigation: monitoring + rate limits from day one)
- Sandbox lifecycle: VM-per-query isolated architecture eliminates cross-query data contamination risk

---

## Session Continuity

**If context is lost, restore from:**

1. **ROADMAP.md** - Full phase structure, success criteria, requirements mapping
2. **REQUIREMENTS.md** - All 42 v1.0 requirements with traceability to phases
3. **PROJECT.md** - Core value, constraints, target features for v1.0
4. **phases/01-backend-foundation-a-authentication/01-01-SUMMARY.md** - Database foundation
5. **phases/01-backend-foundation-a-authentication/01-02-SUMMARY.md** - JWT authentication
6. **phases/01-backend-foundation-a-authentication/01-03-SUMMARY.md** - Password reset & API completion
7. **phases/02-file-upload-management/02-01-SUMMARY.md** - File service foundation
8. **phases/02-file-upload-management/02-02-SUMMARY.md** - File & Chat API Routers
9. **phases/03-ai-agents---orchestration/03-01-SUMMARY.md** - Agent Foundation & Config
10. **phases/03-ai-agents---orchestration/03-02-SUMMARY.md** - Onboarding Agent
11. **phases/03-ai-agents---orchestration/03-03-SUMMARY.md** - AST-Based Code Validation (TDD)
12. **phases/04-streaming-infrastructure/04-01-SUMMARY.md** - SSE Events & Stream Writer Integration
13. **phases/04-streaming-infrastructure/04-02-SUMMARY.md** - SSE Endpoint & Atomic Persistence
14. **phases/05-sandbox-security---code-execution/05-01-SUMMARY.md** - SandboxRuntime Protocol & E2B Implementation
15. **phases/05-sandbox-security---code-execution/05-02-SUMMARY.md** - E2B Sandbox Execution Integration
16. **phases/06-frontend-ui-interactive-data-cards/06-01-SUMMARY.md** - Next.js Frontend Foundation & Authentication
17. **phases/06-frontend-ui-interactive-data-cards/06-02-SUMMARY.md** - User Settings Endpoints & UI
18. **phases/06-frontend-ui-interactive-data-cards/06-03-SUMMARY.md** - Zustand Tab Store & File Manager Hooks
19. **phases/06-frontend-ui-interactive-data-cards/06-04-SUMMARY.md** - Chat Interface with SSE Streaming

**Last session:** 2026-02-04T00:29:43Z
**Stopped at:** Completed 06-04: Chat Interface with SSE Streaming
**Resume file:** None

**Current session status:**
- Phase 1 COMPLETE: All 3 plans executed successfully
- Phase 2 COMPLETE: All 2 plans executed and verified (19/19 must-haves passed)
- Phase 3 COMPLETE: Plans 03-01, 03-02, 03-03, 03-04, and 03-05 executed (11/11 requirements met)
- Phase 4 COMPLETE: Plans 04-01 and 04-02 executed (3/3 requirements met)
  - Plan 04-01: SSE Events & Stream Writer Integration (3min)
    - StreamEventType enum with 10 event types (4 status, 2 progress, 2 content, 2 terminal)
    - StreamEvent Pydantic model for typed SSE payloads
    - Stream timeout 180s and ping interval 30s configuration
    - get_stream_writer() integration in all 5 agent nodes
    - Requirements covered: AGENT-01, AGENT-02, AGENT-07
  - Plan 04-02: SSE Endpoint & Atomic Persistence (2min)
    - run_chat_query_stream() async generator yields SSE events from LangGraph astream()
    - POST /chat/{file_id}/stream endpoint with EventSourceResponse
    - Atomic chat history persistence with fresh database session on completion
    - Stream metadata tracked: duration_ms, retry_count, errors
    - Failed streams save nothing (clean failure state)
    - Requirements covered: AGENT-01, AGENT-02, AGENT-07
- Phase 5 COMPLETE: All 2/2 plans executed (8/8 requirements met)
  - Plan 05-01: SandboxRuntime Protocol & E2B Implementation (10min) COMPLETE
    - SandboxRuntime Protocol defines execute() and cleanup() interface
    - E2BSandboxRuntime implements Protocol using e2b-code-interpreter SDK
    - ExecutionResult dataclass captures stdout, stderr, results, error, timing
    - Sandbox configuration settings (timeout, memory, retries) in config.py
    - Context manager cleanup ensures guaranteed microVM shutdown
    - E2B Cloud API key configured and connectivity verified
    - Requirements covered: SANDBOX-01 (partial - foundation layer)
  - Plan 05-02: E2B Sandbox Execution Integration (3min) COMPLETE
    - execute_in_sandbox replaces execute_code_stub with E2B runtime integration
    - User data file uploaded to sandbox before execution
    - Code display event emitted before execution (EXEC-05)
    - asyncio.to_thread wraps synchronous E2B calls for non-blocking execution
    - Execution errors route to coding_agent with context feedback for retry
    - File reading errors handled gracefully with user-friendly messages
    - halt_node provides tailored messages for different failure types
    - Requirements covered: EXEC-01, EXEC-02, EXEC-03, EXEC-04, EXEC-05, AGENT-09
- Phase 6 IN PROGRESS: 4/12 plans executed (6/12 requirements met)
  - Plan 06-01: Next.js Frontend Foundation & Authentication (7min) COMPLETE
    - Next.js 16 project with TypeScript, Tailwind CSS 4, App Router, shadcn/ui
    - API client with automatic JWT token injection and 401 refresh handling
    - useAuth hook with React Context for global auth state
    - Login, register, forgot-password, reset-password pages with modern vibrant styling
    - Protected dashboard layout redirects unauthenticated users
    - TypeScript types mirror all backend Pydantic schemas (auth, file, chat)
    - TanStack Query configured with 60s staleTime
    - Next.js rewrites proxy /api/* to localhost:8000
    - Requirements covered: UI-01, UI-02, UI-03
  - Plan 06-02: User Settings Endpoints & UI (skipped - already implemented in 06-01)
  - Plan 06-03: Zustand Tab Store & File Manager Hooks (completed separately)
  - Plan 06-04: Chat Interface with SSE Streaming (2min) COMPLETE
    - useSSEStream: POST-based SSE streaming with fetch + ReadableStream
    - Parses all 10 StreamEvent types with user-friendly status messages
    - useChatMessages: TanStack Query hook for chat history
    - ChatInterface: message list, auto-scroll, streaming, error handling
    - ChatInput: auto-expanding textarea with Enter-to-send, Shift+Enter for newlines
    - ChatMessage: user (right) vs assistant (left) styling with streaming support
    - TypingIndicator: animated three-dot loading indicator
    - Requirements covered: UI-04, UI-05, UI-06

---

*State persists across sessions. Update after completing each phase.*
