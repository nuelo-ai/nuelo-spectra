# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 12 - Production Email Infrastructure (v0.2 milestone)

## Current Position

Phase: 12 of 13 (Production Email Infrastructure)
Plan: 1 of 2 complete
Status: In progress
Branch: develop (v0.2 development branch)
Last activity: 2026-02-09 — Phase 12 Plan 01 complete (SMTP email infrastructure, PasswordResetToken model)

Progress: [██████████████████████████░░░] 75% (52/~69 estimated total plans)

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
| 10. Smart Query Suggestions | 2/2 | Complete (UAT passed) |
| 11. Web Search Tool Integration | 3/3 | Complete (UAT passed) |
| 12. Production Email Infrastructure | 1/2 | In progress |
| 13. Migrate Web Search (Tavily) | 1/1 | Complete |

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
- v0.2 Phase 10 Plan 1: 4 min execution (backend query suggestions infrastructure - JSON prompts, DB migration, stream wiring)
- v0.2 Phase 10 Plan 2: 3 min execution (frontend suggestion UI - QuerySuggestions component, DataCard follow-ups, ChatInterface integration)
- v0.2 Phase 11 Plan 1: 3 min execution (backend search infrastructure - SearchService, SearchQuota, config, router)
- v0.2 Phase 11 Plan 2: 7 min execution (agent integration - bind_tools/ToolNode loop, da_with_tools/search_tools/da_response, service wiring)
- v0.2 Phase 11 Plan 3: 10 min execution (frontend search UI - useSearchToggle, ChatInput toggle, search activity, DataCard sources, UAT + 3 bug fix rounds)
- v0.2 Phase 13 Plan 1: 3 min execution (Tavily migration - SearchService rewrite, tool output update, Serper removal)
- v0.2 Phase 12 Plan 1: 4 min execution (SMTP email infrastructure - aiosmtplib, PasswordResetToken model, Jinja2 templates)
- Trend: Stable, high velocity maintained (Phase 7 ~12 min, Phase 8 ~7 min, Phase 9 ~11 min, Phase 10 ~7 min, Phase 11 ~20 min, Phase 13 ~3 min, Phase 12 ~4 min so far)

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
- **Phase 10 Plan 1 (2026-02-08):** JSON-structured LLM output with graceful fallback for both onboarding and data_analysis agents. Single LLM call for summary + suggestions (no separate API call). LLM-decided suggestion categories per dataset (not fixed templates). query_suggestions stored as JSON in files table. follow_up_suggestions as list[str] in ChatAgentState, included in stream event allowlist and chat_messages.metadata_json. suggestion_auto_send configurable via .env (default: True). Alembic migration cleaned to exclude LangGraph checkpoint tables.
- **Phase 10 Plan 2 (2026-02-08):** QuerySuggestions component with categorized chips, fade-out animation, ReactMarkdown for bold column names. Auto-send as default (clicking chip calls handleSend directly). ChatInput initialValue prop for non-auto-send fallback. DataCard follow-up chips with "Continue exploring" header, plain text (no markdown). Follow-up suggestions extracted from metadata_json (historical) and stream events (live). Conditional empty state: suggestions when available, generic fallback for older files.
- **Phase 11 Plan 1 (2026-02-09):** SearchService HTTP client for Serper.dev with httpx.AsyncClient (configurable timeout, domain blocking, structured JSON logging). SearchQuota model with composite PK (user_id, search_date) for daily per-user tracking. Search config settings (serper_api_key, search_max_per_query=5, search_daily_quota=7, search_num_results=5, search_timeout=10.0). search.yaml for feature defaults. ChatAgentState extended with web_search_enabled and search_sources. ChatQueryRequest extended with web_search_enabled. StreamEventType extended with search events and routing events. GET /search/config endpoint returns configured/enabled/quota status.
- **Phase 11 Plan 2 (2026-02-09):** First tool-calling pattern established using LangGraph bind_tools/ToolNode. data_analysis_agent split into da_with_tools_node (LLM with conditional tool binding), search_tools (ToolNode with handle_tool_errors=True), da_response_node (source extraction, JSON parsing). Manager routes MEMORY_SUFFICIENT to da_with_tools (not data_analysis). web_search_enabled flows end-to-end from ChatQueryRequest through agent_service to initial_state. Quota tracked per user query (not per Serper API call). Search sources included in SSE events and chat metadata. bind_tools wrapped in try/except for provider compatibility.
- **Phase 11 Plan 3 (2026-02-09):** Frontend search UI complete with useSearchToggle hook (config check, quota validation), custom toggle button below ChatInput (shadcn Switch not installed), real-time search activity indicator showing actual query text, DataCard Sources section with clickable page title links. Toggle resets to OFF after each query. UAT revealed bind_tools mode system prompt loss issue - da_response_node makes fresh LLM call when search was used for reliable JSON output and quality analysis. Phase 11 complete - full web search integration operational.

- **Phase 12 Plan 1 (2026-02-09):** aiosmtplib with start_tls=True for SMTP transport (replaces Mailgun HTTP API). SHA-256 hashing of reset tokens with secrets.compare_digest for constant-time verification. Dev mode console logging when SMTP_HOST is empty. PasswordResetToken model with token_hash, is_used, is_active, expires_at. Jinja2 HTML/text email templates with inline CSS. validate_smtp_connection() for startup health checks.
- **Phase 13 Plan 1 (2026-02-09):** Tavily API migration using tavily-python SDK (AsyncTavilyClient). SearchService rewritten with include_answer=True, max_results=3, configurable search_depth. search_web tool returns synthesized answer + source URLs (answer flows through existing search_results_text -> _generate_analysis_with_search -> system prompt path). search_num_results default changed 5->3. credits_used logged for SEARCH-07 cost tracking. All Serper.dev references removed from codebase. 100 tests pass.

### Roadmap Evolution

- Phase 13 added: Migrate Web Search from Serper.dev to Tavily (Serper.dev returns URL links only; Tavily returns full page content needed for quality AI analysis)

### Pending Todos

**From v0.1 (now integrated into v0.2 roadmap):**
- [x] Agent memory persistence → Phase 8: Session Memory
- [x] OpenRouter and Ollama support → Phase 7: Multi-LLM Infrastructure
- [x] SMTP email migration → Phase 11: Production Email

**New v0.2 features:**
- [x] Query suggestions (Phase 10)
- [x] Web search integration (Phase 11)
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

Last session: 2026-02-09
Stopped at: Completed 12-01-PLAN.md (SMTP email infrastructure, PasswordResetToken model, Jinja2 templates)
Resume with: Phase 12 Plan 02 (Wire email into auth endpoints)
Resume file: .planning/phases/12-production-email-infrastructure/12-01-SUMMARY.md
Next decision: Execute Phase 12 Plan 02
