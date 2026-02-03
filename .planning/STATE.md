# Project State: Spectra v1.0 MVP

**Last Updated:** 2026-02-03
**Milestone:** v1.0 MVP
**Status:** Phase 3 In Progress

---

## Project Reference

**Core Value:**
Accurate data analysis through correct, safe Python code generation. If the code is wrong or the sandbox isn't secure, the entire product fails.

**Current Focus:**
Phase 3 in progress. Building AI agent orchestration system with LangGraph foundation complete (plan 03-01). Next: Onboarding Agent implementation.

**Key Constraint:**
Timeline: 2-4 weeks for MVP delivery. Single developer. Security (sandbox isolation) is non-negotiable for production.

---

## Current Position

**Phase:** 3 of 6 - AI Agents & Orchestration
**Plan:** 03-02 complete (Onboarding Agent)
**Status:** In progress

**Progress Bar:**
```
[█████████████░░░░░░░] 33% (14/42 requirements completed)

Phase 1: [██████████] 3/3 plans COMPLETE (database + auth + password reset)
Phase 2: [██████████] 2/2 plans COMPLETE (file service + API routers)
Phase 3: [████░░░░░░] 2/7 plans COMPLETE (agent foundation + onboarding agent)
Phase 4: [░░░░░░░░░░] 0/3 requirements
Phase 5: [░░░░░░░░░░] 0/8 requirements
Phase 6: [░░░░░░░░░░] 0/12 requirements
```

**Last activity:** 2026-02-03 - Completed 03-02: Onboarding Agent (pandas profiling + LLM summarization)

**Next Action:**
Execute plan 03-03 (Code Safety & Validation)

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
| 2026-02-03 | data_summary/user_context nullable on File model | Populated asynchronously after upload; NULL until Onboarding Agent runs |
| 2026-02-03 | asyncio.to_thread for pandas profiling | Prevents event loop blocking during data analysis operations |
| 2026-02-03 | v1 always appends user context | Simple append pattern; v2 will ask user to re-run or append |
| 2026-02-03 | Agent service layer pattern | Service functions bridge API endpoints and agent logic for clean separation |
| 2026-02-03 | LangGraph TypedDict for state (not Pydantic) | LangGraph requires TypedDict; compatible with StateGraph |
| 2026-02-03 | Multi-provider LLM factory pattern | Agents work with Anthropic/OpenAI/Google via BaseChatModel interface |
| 2026-02-03 | YAML for agent prompts and allowlists | Externalized config enables prompt iteration without deployment |
| 2026-02-03 | agent_max_retries=3 default | Circuit breaker prevents infinite retry loops and runaway costs |
| 2026-02-03 | Lazy imports in LLM factory | Users only need SDK for their chosen provider |
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

**Immediate (Phase 3 Execution):**
- [ ] Setup API keys for Phase 3 execution (see `.planning/todos/pending/2026-02-03-setup-api-keys-for-phase-3.md`)

**Phase 3 Enhancements:**
- [ ] Add OpenRouter and Ollama LLM provider support (see `.planning/todos/pending/2026-02-03-add-openrouter-and-ollama-llm-support.md`)

**Research Needed:**
- Phase 5: E2B vs self-hosted gVisor decision (complexity vs cost tradeoff for single developer)

**Completed:**
- [x] Make agent LLM provider configurable - integrated into Phase 3 plans (03-01, 03-02, 03-04)

**Deferred to Later Phases:**
- Frontend UI components (Phase 6)
- Data Card visualization design (Phase 6)
- Settings page implementation (Phase 6)

### Blockers

**None currently.**

**Potential Future Blockers:**
- Phase 5: gVisor setup complexity may require pivot to E2B Cloud (will validate during planning)
- Budget: LLM token costs with 4-agent orchestration (mitigation: monitoring + rate limits from day one)

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

**Last session:** 2026-02-03T15:17:11Z
**Stopped at:** Completed 03-02: Onboarding Agent
**Resume file:** None

**Current session status:**
- Phase 1 COMPLETE: All 3 plans executed successfully
- Phase 2 COMPLETE: All 2 plans executed and verified (19/19 must-haves passed)
- Phase 3 IN PROGRESS: Plans 03-01 and 03-02 complete
- Plan 03-01: LangGraph foundation, multi-provider LLM factory, YAML configs (172s)
- Plan 03-02: Onboarding Agent with pandas profiling + LLM summarization (164s)
  - OnboardingAgent: profile_data (pandas analysis), generate_summary (LLM), run (orchestration)
  - agent_service.py: run_onboarding, update_user_context service functions
  - File model extended: data_summary and user_context columns (nullable, async populated)
  - Requirements covered: FILE-04, FILE-05, FILE-06, AGENT-03
- Next: Plan 03-03 (Code Safety & Validation)

---

*State persists across sessions. Update after completing each phase.*
