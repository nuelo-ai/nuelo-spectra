# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** - Phases 1-6 (shipped 2026-02-06)
- 🚧 **v0.2 Intelligence & Integration** - Phases 7-12 (in progress)

## Phases

<details>
<summary>✅ v0.1 Beta MVP (Phases 1-6) - SHIPPED 2026-02-06</summary>

### Phase 1: Foundation Setup
**Goal**: Project scaffolding with database, authentication foundation, and development environment
**Plans**: 6 plans

Plans:
- [x] 01-01: Initialize Next.js project with TypeScript and Tailwind CSS
- [x] 01-02: Set up PostgreSQL database with SQLAlchemy ORM and Alembic migrations
- [x] 01-03: Implement JWT authentication with access and refresh tokens
- [x] 01-04: Create user signup endpoint with password hashing
- [x] 01-05: Build login endpoint with token generation
- [x] 01-06: Add password reset email flow (dev mode - console logging)

### Phase 2: File Upload & AI Profiling
**Goal**: Users can upload files and receive AI-powered data structure analysis
**Plans**: 6 plans

Plans:
- [x] 02-01: Build file upload endpoint with Excel/CSV validation (50MB limit)
- [x] 02-02: Implement Onboarding Agent with YAML-configured system prompts
- [x] 02-03: Create data profiling logic (column analysis, type detection, statistics)
- [x] 02-04: Add optional user context input during upload
- [x] 02-05: Enable refinement of AI's data understanding after profiling
- [x] 02-06: Store file metadata and profiling results in PostgreSQL

### Phase 3: Multi-File Management
**Goal**: Users can manage multiple datasets with independent chat histories
**Plans**: 4 plans

Plans:
- [x] 03-01: Build file listing endpoint with metadata (name, size, date)
- [x] 03-02: Implement file deletion with confirmation
- [x] 03-03: Create tabbed interface (one tab per file) in frontend
- [x] 03-04: Enable tab switching with independent chat state per file

### Phase 4: AI Agent System & Code Generation
**Goal**: 4-agent system generates and validates safe Python code for data queries
**Plans**: 8 plans

Plans:
- [x] 04-01: Set up LangGraph graph structure for multi-agent orchestration
- [x] 04-02: Implement Coding Agent with code generation prompts
- [x] 04-03: Build Code Checker Agent with AST-based safety validation
- [x] 04-04: Create Data Analysis Agent for result interpretation
- [x] 04-05: Add allowed library configuration (YAML allowlist)
- [x] 04-06: Implement intelligent retry logic (max 3 attempts with error context)
- [x] 04-07: Build chat endpoint with natural language query processing
- [x] 04-08: Externalize all agent prompts to YAML files

### Phase 5: Secure Code Execution & E2B Integration
**Goal**: Python code executes safely in isolated E2B sandbox with resource limits
**Plans**: 6 plans

Plans:
- [x] 05-01: Integrate E2B SDK for microVM sandbox creation
- [x] 05-02: Implement file upload to E2B sandbox (per-user isolation)
- [x] 05-03: Add code execution with timeout and resource limits
- [x] 05-04: Build result extraction from sandbox (stdout, dataframes)
- [x] 05-05: Handle execution failures with detailed error reporting
- [x] 05-06: Add sandbox cleanup and lifecycle management

### Phase 6: Interactive Data Cards & Frontend Polish
**Goal**: Query results display as polished, interactive Data Cards with exports
**Plans**: 6 plans

Plans:
- [x] 06-01: Build Data Card component (Query Brief, Data Table, AI Explanation)
- [x] 06-02: Implement real-time SSE streaming for AI responses
- [x] 06-03: Add sortable/filterable data tables in Data Cards
- [x] 06-04: Enable CSV export from Data Cards
- [x] 06-05: Enable Markdown report export from Data Cards
- [x] 06-06: Build Settings page (profile editing, password change)

</details>

---

### 🚧 v0.2 Intelligence & Integration (In Progress)

**Milestone Goal:** Enhance AI agent capabilities with memory persistence and multi-provider LLM support, add intelligent query suggestions, and complete production email infrastructure.

#### Phase 7: Multi-LLM Provider Infrastructure

**Goal:** System supports multiple LLM providers (Ollama, OpenRouter) with per-agent configuration, enabling cost optimization and vendor flexibility.

**Depends on:** Phase 6 (v0.1 complete)

**Requirements:** LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06, LLM-07, CONFIG-01, CONFIG-02, CONFIG-03, CONFIG-04, CONFIG-05

**Success Criteria** (what must be TRUE):
1. User can configure system to use Ollama (local or remote) as LLM provider
2. User can configure system to use OpenRouter gateway for 100+ model options
3. Each AI agent (Onboarding, Coding, Code Checker, Data Analysis) can use different LLM provider/model via YAML config
4. System maintains current behavior with Sonnet 4.0 as default for all agents
5. System displays clear error messages when LLM provider configuration is invalid or unavailable

**Plans:** 4 plans

Plans:
- [x] 07-01-PLAN.md — Provider registry, LLM factory extension (Ollama + OpenRouter), per-agent YAML config (provider/model/temperature)
- [x] 07-02-PLAN.md — Migrate all 4 agents to per-agent provider/model/temperature config
- [x] 07-03-PLAN.md — Fail-fast startup validation, structured logging, /health/llm endpoint
- [x] 07-04-PLAN.md — Test scenarios for all LLM providers (LLM-06)

---

#### Phase 8: Session Memory with PostgreSQL Checkpointing

**Goal:** Users can maintain multi-turn conversations within chat tabs, with context persisting across queries until tab is closed.

**Depends on:** Phase 7 (agents have working LLM instances)

**Requirements:** MEMORY-01, MEMORY-02, MEMORY-03, MEMORY-04, MEMORY-05, MEMORY-06, MEMORY-07, MEMORY-08

**Success Criteria** (what must be TRUE):
1. User can ask follow-up questions without re-explaining context (e.g., "add a column" works after previous query)
2. User's conversation context persists after browser refresh as long as tab remains open
3. User receives warning dialog before closing chat tab explaining context will be lost
4. User sees current context usage displayed in chat interface (e.g., "8,543 / 12,000 tokens used")
5. User receives warning when context reaches 85% of token limit with option to continue

**Plans:** 4 plans (estimated)

Plans:
- [x] 08-01-PLAN.md — Enable AsyncPostgresSaver checkpointing, add_messages reducer, graph wiring, context window config
- [x] 08-02-PLAN.md — Token counting, context management endpoints, frontend tab close warning and context usage display

---

#### Phase 9: Manager Agent with Intelligent Query Routing

**Goal:** Implement Manager Agent to intelligently route queries between memory-only responses, code modification, and fresh code generation, reducing response time by ~40% and improving conversation UX.

**Depends on:** Phase 8 (conversation memory infrastructure)

**Requirements:** ROUTING-01, ROUTING-02, ROUTING-03, ROUTING-04, ROUTING-05, ROUTING-06, ROUTING-07, ROUTING-08, ROUTING-09, ROUTING-10

**Success Criteria** (what must be TRUE):
1. Manager Agent analyzes user queries and routes to one of three paths: MEMORY_SUFFICIENT, CODE_MODIFICATION, or NEW_ANALYSIS
2. Memory-only queries (e.g., "What were the columns?") respond in <3 seconds without code generation
3. Manager Agent uses configurable LLM provider (default: Sonnet) via YAML config consistent with Phase 7
4. System defaults to NEW_ANALYSIS fallback when routing decision is uncertain
5. Manager Agent logs all routing decisions with reasoning for monitoring and optimization

**Plans:** 3 plans

Plans:
- [x] 09-01-PLAN.md — Manager Agent node with RoutingDecision schema, Command-based routing, YAML config, graph entry point change
- [x] 09-02-PLAN.md — Route-aware agent behavior (memory mode for Data Analysis, modification mode for Coding), frontend routing event handling
- [x] 09-03-PLAN.md — TDD test suite for routing classification, fallback behavior, route-specific agents, graph topology

---

#### Phase 10: Smart Query Suggestions

**Goal:** New chat tabs display intelligent, context-aware query suggestions grouped by analysis intent, reducing blank-page intimidation.

**Depends on:** Phase 9 (Manager Agent enables better conversation flow)

**Requirements:** SUGGEST-01, SUGGEST-02, SUGGEST-03, SUGGEST-04, SUGGEST-05, SUGGEST-06

**Success Criteria** (what must be TRUE):
1. User sees 5-6 query suggestions when opening new chat tab
2. Suggestions are grouped into 3 categories: General Analysis (2), Benchmarking (2), Trend/Predictive (2)
3. User can click any suggestion to immediately start chat with that query
4. Suggestions adapt to actual dataset structure (use real column names and data types)
5. Suggestions persist and display consistently until file is re-analyzed

**Plans:** 2 plans

Plans:
- [x] 10-01-PLAN.md — Backend: DB migration, onboarding prompt extension for LLM-generated suggestions, Data Analysis Agent follow-up suggestions, API response changes
- [x] 10-02-PLAN.md — Frontend: QuerySuggestions component, ChatInterface empty state integration, DataCard follow-up chips, human verification

---

#### Phase 11: Web Search Tool Integration

**Goal:** Data Analysis Agent can search web via Serper.dev to answer benchmarking queries that require external data, with transparent source citations.

**Depends on:** Phase 8 (memory and tool binding infrastructure)

**Requirements:** SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04, SEARCH-05, SEARCH-06, SEARCH-07

**Success Criteria** (what must be TRUE):
1. Data Analysis Agent autonomously decides when to search web based on query content (not mandatory for all queries)
2. User sees search queries and source links transparently in chat responses
3. System continues gracefully when web search quota exceeded or API unavailable (displays clear message, continues without search)
4. Web search functionality can be enabled/disabled via configuration file
5. All web search queries are logged for debugging and cost tracking

**Plans:** 3 plans

Plans:
- [x] 11-01-PLAN.md — Backend search infrastructure: SearchService, SearchQuota model, config, state/schema extensions, search config router
- [x] 11-02-PLAN.md — Agent integration: @tool definition, graph topology (da_with_tools/search_tools/da_response), manager routing, service wiring, quota tracking
- [x] 11-03-PLAN.md — Frontend search UI: search toggle, SSE events, DataCard sources section, ChatInterface wiring, human verification

---

#### Phase 12: Production Email Infrastructure

**Goal:** System uses standard SMTP for all email operations with production-ready password reset flow, replacing dev-mode console logging.

**Depends on:** Phase 7 (independent of memory/search features)

**Requirements:** SMTP-01, SMTP-02, SMTP-03, SMTP-04, SMTP-05, SMTP-06, PWRESET-01, PWRESET-02, PWRESET-03, PWRESET-04, PWRESET-05

**Success Criteria** (what must be TRUE):
1. Password reset emails send via standard SMTP (host/port/user/pass configured in settings)
2. Reset emails use professional HTML template with branding and secure link format
3. System automatically disables dev mode (console logging) when SMTP is properly configured
4. System validates SMTP configuration at startup and displays connection status
5. Reset links expire after configurable time (default: 10 minutes)

**Plans:** TBD

Plans:
- [ ] 12-01: TBD
- [ ] 12-02: TBD

### Phase 13: Migrate Web Search from Serper.dev to Tavily

**Goal:** Replace Serper.dev search provider with Tavily API so the Analyst AI agent receives full page content (not just URL links), enabling higher-quality analysis grounded in actual search result content.

**Depends on:** Phase 11 (Web Search Tool Integration)
**Plans:** 1 plan

Plans:
- [ ] 13-01-PLAN.md — Rewrite SearchService for Tavily (AsyncTavilyClient, synthesized answer in tool output, config swap, full Serper.dev cleanup)

---

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10 → 11 → 12 → 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation Setup | v0.1 | 6/6 | Complete | 2026-02-06 |
| 2. File Upload & AI Profiling | v0.1 | 6/6 | Complete | 2026-02-06 |
| 3. Multi-File Management | v0.1 | 4/4 | Complete | 2026-02-06 |
| 4. AI Agent System & Code Generation | v0.1 | 8/8 | Complete | 2026-02-06 |
| 5. Secure Code Execution & E2B | v0.1 | 6/6 | Complete | 2026-02-06 |
| 6. Interactive Data Cards | v0.1 | 6/6 | Complete | 2026-02-06 |
| 7. Multi-LLM Infrastructure | v0.2 | 4/4 | Complete | 2026-02-07 |
| 8. Session Memory | v0.2 | 2/2 | Complete | 2026-02-08 |
| 9. Manager Agent Routing | v0.2 | 3/3 | Complete | 2026-02-08 |
| 10. Smart Query Suggestions | v0.2 | 2/2 | Complete | 2026-02-08 |
| 11. Web Search Integration | v0.2 | 3/3 | Complete | 2026-02-09 |
| 12. Production Email | v0.2 | 0/TBD | Not started | - |
| 13. Migrate Web Search (Tavily) | v0.2 | 0/TBD | Not started | - |
