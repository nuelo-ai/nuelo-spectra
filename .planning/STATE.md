# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 10 - Smart Query Suggestions (v0.2 milestone)

## Current Position

Phase: 9 of 12 (Manager Agent with Intelligent Query Routing)
Plan: 3 of 3 complete
Status: Phase complete
Branch: develop (v0.2 development branch)
Last activity: 2026-02-08 — Completed 09-03-PLAN.md (Routing test suite - 28 tests)

Progress: [███████████████████░░░░░░░░░] 65% (45/~69 estimated total plans)

## Performance Metrics

**Velocity (v0.1):**
- Total plans completed: 36
- Total execution time: ~5 days (Feb 1-6, 2026)
- Plans per day: ~7 plans/day

**By Phase (v0.1):**

| Phase | Plans | Status |
|-------|-------|--------|
| 1. Foundation Setup | 6/6 | Complete |
| 2. File Upload & AI Profiling | 6/6 | Complete |
| 3. Multi-File Management | 4/4 | Complete |
| 4. AI Agent System | 8/8 | Complete |
| 5. Secure Code Execution | 6/6 | Complete |
| 6. Interactive Data Cards | 6/6 | Complete |

**By Phase (v0.2 - in progress):**

| Phase | Plans | Status |
|-------|-------|--------|
| 7. Multi-LLM Provider Infrastructure | 4/4 | Complete |
| 8. Session Memory with PostgreSQL Checkpointing | 2/2 | Complete (UAT passed) |
| 9. Manager Agent with Intelligent Query Routing | 3/3 | Complete |
| 10. Smart Query Suggestions | 0/TBD | Not started |
| 11. Web Search Tool Integration | 0/TBD | Not started |
| 12. Production Email Infrastructure | 0/TBD | Not started |

**Recent Trend:**
- v0.1 completed in 5 days with aggressive execution
- v0.2 Phase 7 Plan 1: 3 min execution (provider infrastructure foundation)
- v0.2 Phase 7 Plan 2: 2 min execution (agent wiring migration)
- v0.2 Phase 7 Plan 3: 2 min execution (validation & observability)
- v0.2 Phase 7 Plan 4: 5 min execution (test scenarios - 34 tests, all 5 providers)
- v0.2 Phase 8 Plan 1: 4 min execution (PostgreSQL checkpointing infrastructure)
- v0.2 Phase 8 Plan 2: 3 min execution (token counting & context management)
- v0.2 Phase 9 Plan 1: 4 min execution (Manager Agent core with RoutingDecision and graph wiring)
- v0.2 Phase 9 Plan 2: 4 min execution (route-aware agents and frontend routing events)
- v0.2 Phase 9 Plan 3: 3 min execution (routing test suite - 28 tests, fully mocked)
- Trend: Stable, high velocity maintained (Phase 7 complete in ~12 min, Phase 8 ~7 min, Phase 9 complete in ~11 min)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

**Git Branching Strategy (2026-02-06):**
- Using development branch workflow for v0.2+ (see .planning/VERSIONING.md)
- `master` branch: stable releases only (v0.1, v0.2, etc.)
- `develop` branch: active development for current milestone
- All Phase 7-11 commits go to `develop` branch
- When v0.2 complete: merge develop → master, tag v0.2, optionally delete develop

Recent decisions affecting v0.2 work:

- v0.1: 4-agent architecture validated (Onboarding, Coding, Code Checker, Data Analysis)
- v0.1: PostgreSQL checkpointing temporarily disabled due to async issues (will be fixed in Phase 8)
- v0.1: YAML-externalized prompts enables per-agent configuration (foundation for Phase 7)
- v0.2: Multi-LLM infrastructure prioritized first (Phase 7) as foundation for all other features
- v0.2: Session-scoped memory over persistent cross-session (Phase 8) to avoid context pollution
- **Phase 7 Plan 1 (2026-02-07):** Anthropic (Claude Sonnet 4.0) as default provider, temperature defaults to 0.0 (deterministic), stateless factory pattern (agents pass provider-specific options)
- **Phase 7 Plan 2 (2026-02-07):** Shared get_api_key_for_provider() helper in agents/config.py for centralized API key resolution, temperature passed via kwargs to get_llm() for all agents
- **Phase 7 Plan 3 (2026-02-07):** Fail-fast startup validation with connectivity tests (5-second timeout per provider), 60-second cached health checks, structured JSON logging for LLM calls (metadata only, not full content)
- **Phase 7 Plan 4 (2026-02-07):** 34 comprehensive test scenarios covering all 5 providers (Anthropic, OpenAI, Google, Ollama, OpenRouter) with factory, config, validation, error classification, health endpoint, and invoke logging tests. All tests fully mocked - zero live API keys required (LLM-06 satisfied)
- **Phase 8 Plan 1 (2026-02-07):** AsyncPostgresSaver initialized in FastAPI lifespan with connection pooling, add_messages reducer for message accumulation, thread-based conversation isolation per file tab. AsyncPostgresSaver is NOT an async context manager (use direct instantiation). Database URL conversion required (postgresql+asyncpg → postgresql for psycopg). Messages initialized as [HumanMessage(content=user_query)] for proper reducer behavior. Context window defaults: 12000 tokens, 85% warning threshold.
- **Phase 8 Plan 2 (2026-02-07):** Tiktoken-based token counting with provider-specific scaling factors (1.1x Anthropic, 1.05x Google, 1.0x OpenAI/others) for fast UI updates without expensive API calls. Two-phase trimming flow: check → user confirmation → trim to 90% of limit. Context usage displayed in ChatInterface header ("X / 12,000 tokens" with orange warning at 85%, red at exceeded). Browser tab close warning via beforeunload when hasContext (>2 messages). GET /context-usage and POST /trim-context endpoints for frontend integration.
- **Manager Agent Architecture Decision (2026-02-07):** Insert Manager Agent as new Phase 9 (renumber subsequent phases 9→10, 10→11, 11→12). Manager Agent intelligently routes queries to 3 paths: MEMORY_SUFFICIENT (answer from history, ~87% faster), CODE_MODIFICATION (modify existing code), NEW_ANALYSIS (fresh code generation). Use Sonnet model (configurable via YAML like Phase 7), analyze last 10 messages, default to NEW_ANALYSIS on uncertainty. No route override or hybrid routes in v0.2 (design for future flexibility). Expected impact: ~40% cost reduction, significantly faster responses for simple queries. Architecture doc: .planning/architecture/manager-agent-routing.md
- **Phase 9 Plan 1 (2026-02-08):** RoutingDecision Pydantic model defined in state.py (avoids circular imports). Manager Agent uses with_structured_output for reliable JSON parsing. Command-based routing (same pattern as code_checker_node). Fallback to NEW_ANALYSIS on any routing failure. routing_context_messages configurable via YAML (default: 10). Routing decision included in stream events and chat history metadata.
- **Phase 9 Plan 2 (2026-02-08):** Data Analysis Agent checks routing_decision at function top for MEMORY_SUFFICIENT mode (answers from conversation history, returns empty generated_code/execution_result). Coding Agent checks for CODE_MODIFICATION mode (modifies previous_code instead of generating from scratch). Both use internal branching per RESEARCH.md guidance (single node, no graph topology changes). Frontend adds routing_started/routing_decided to StreamEventType, detects MEMORY_SUFFICIENT route to render as plain ChatMessage (no DataCard).
- **Phase 9 Plan 3 (2026-02-08):** 28 fully-mocked pytest tests covering routing classification (6), fallback behavior (4), route-specific agent behavior (3), graph topology (4), configuration (4), structured logging (2), RoutingDecision model (3), and stream events (2). Uses _patch_manager_dependencies helper pattern for test boilerplate reduction. All 99 tests (28 routing + 37 code checker + 34 LLM provider) pass with zero regressions.

### Pending Todos

**From v0.1 (now integrated into v0.2 roadmap):**
- [x] Agent memory persistence → Phase 8: Session Memory
- [x] OpenRouter and Ollama support → Phase 7: Multi-LLM Infrastructure
- [x] SMTP email migration → Phase 11: Production Email

**New v0.2 features:**
- [ ] Query suggestions (Phase 10)
- [ ] Web search integration (Phase 11)
- [ ] Query safety filter in Manager Agent (security — block PII extraction, prompt injection, etc.)

### Blockers/Concerns

**From v0.1 known limitations (to be fixed in v0.2):**
- ~~PostgreSQL checkpointing was disabled due to async issues~~ — **FIXED in Phase 8 Plan 1:** AsyncPostgresSaver now enabled with proper lifecycle management
- E2B sandboxes created per-execution (no warm pools) — acceptable for v0.2, optimization deferred to v0.3+

**v0.2 phase dependencies:**
- Phase 8 (Memory) depends on Phase 7 (LLM infrastructure) being stable
- Phase 9 (Manager Agent) depends on Phase 8 (memory infrastructure) for conversation context
- Phase 10 (Suggestions) depends on Phase 9 (Manager Agent) for optimal conversation flow
- Phase 11 (Web Search) can be parallelized with Phase 10 but sequenced after for safety
- Phase 12 (SMTP) is independent (can run anytime after Phase 7)

## Session Continuity

Last session: 2026-02-08
Stopped at: Phase 8 UAT complete (4/4 passed), Phase 9 complete — ready for Phase 10
Resume with: Plan Phase 10 (Smart Query Suggestions)
Resume file: .planning/phases/08-session-memory-with-postgresql-checkpointing/08-UAT.md
Next decision: Plan Phase 10 (Smart Query Suggestions)
