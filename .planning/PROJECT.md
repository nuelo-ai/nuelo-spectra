# Spectra

## What This Is

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. Users upload datasets (Excel/CSV), ask questions in natural language through a conversational chat interface, and receive instant insights presented as interactive Data Cards. A 5-agent AI system with intelligent query routing generates validated Python code in a secure sandbox, with multi-turn conversation memory, web search integration, and smart query suggestions. The platform supports 5 LLM providers with per-agent configuration, making it adaptable to different deployment scenarios.

## Core Value

Accurate data analysis. The AI must generate correct, safe Python code that produces reliable results. If the code is wrong or the sandbox isn't secure, the entire product fails. Everything else—polish, features, exports—depends on users trusting the analysis is accurate.

## Repository

**GitHub:** https://github.com/marwazihs/nuelo-spectra.git (private)
**Remote:** origin
**Branch:** master
**Latest Tag:** v0.2 (2026-02-10)

## Current State

**Shipped:** v0.2 Intelligence & Integration (2026-02-10)
**Status:** Production-ready with intelligent agent capabilities
**Codebase:** 15,478 LOC (6,574 Python app + 2,077 Python tests + 6,827 TypeScript/TSX)
**Tech Stack:** FastAPI + PostgreSQL + LangGraph + E2B + Tavily (backend), Next.js 16 + React 19 + TanStack + shadcn/ui (frontend)

**What works:**
- ✅ Complete authentication system with JWT, refresh tokens, and SMTP password reset
- ✅ File upload with AI-powered data profiling (Excel/CSV up to 50MB)
- ✅ Multi-file management with tabbed interface and independent chat histories
- ✅ 5-agent AI system (Onboarding, Manager, Coding, Code Checker, Data Analysis) with LangGraph orchestration
- ✅ Multi-turn conversation memory with PostgreSQL checkpointing and token counting
- ✅ Manager Agent with intelligent 3-path query routing (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS)
- ✅ Smart query suggestions on new chat tabs and follow-up chips on DataCards
- ✅ Tavily-powered web search tool with transparent source citations and quota tracking
- ✅ 5 LLM providers (Anthropic, OpenAI, Google, Ollama, OpenRouter) with per-agent YAML config
- ✅ Real-time SSE streaming showing AI thinking process
- ✅ Interactive Data Cards with sortable tables, code display, and CSV/Markdown exports
- ✅ Production SMTP email service with DB-backed single-use password reset tokens

**Known limitations:**
- E2B sandboxes created per-execution (no warm pools - ~150ms cold start per query)
- Basic mobile responsiveness (functional but not optimized)
- No query safety filter in Manager Agent (PII extraction, prompt injection not blocked)
- Agent JSON responses not using Pydantic structured output (inconsistent across providers)

**Next milestone goals:** Visualization capabilities, advanced memory features, production hardening

## Requirements

### Validated

**✅ v0.1 Beta MVP — Shipped 2026-02-06**

**Authentication (5/5):**
- ✓ User can sign up with email and password — v0.1
- ✓ User can log in with email and password — v0.1
- ✓ User can reset password via email link — v0.1
- ✓ User session persists across browser refresh — v0.1
- ✓ User data is isolated (each user sees only their own files and chat history) — v0.1

**File Management (10/10):**
- ✓ User can upload Excel (.xlsx, .xls) and CSV files up to 50MB — v0.1
- ✓ System validates file format and structure before acceptance — v0.1
- ✓ AI Onboarding Agent analyzes data structure and generates natural language summary — v0.1
- ✓ User can provide optional context during upload to improve AI interpretation — v0.1
- ✓ User can refine AI's understanding of the data after initial analysis — v0.1
- ✓ User can view list of uploaded files with metadata (name, size, upload date) — v0.1
- ✓ User can delete files with confirmation dialog — v0.1
- ✓ Each file has its own chat tab in the interface — v0.1
- ✓ User can switch between file tabs with independent chat histories — v0.1
- ✓ Current active file is clearly displayed — v0.1

**AI Agents & Chat (9/9):**
- ✓ User can ask questions about their data in natural language — v0.1
- ✓ System streams AI responses in real-time (shows thinking process) — v0.1
- ✓ Coding Agent generates Python scripts based on user queries — v0.1
- ✓ Code Checker Agent validates generated code for safety and correctness before execution — v0.1
- ✓ Data Analysis Agent interprets code execution results and generates explanations — v0.1
- ✓ AI agent system prompts are externalized to YAML configuration files for easy tuning — v0.1
- ✓ Chat history persists per file across browser sessions — v0.1
- ✓ When code execution fails, system automatically analyzes error, regenerates code, and retries — v0.1
- ✓ Generated code only imports allowed libraries from YAML allowlist — v0.1

**Code Execution & Security (8/8):**
- ✓ Python code executes in E2B microVM sandbox environment — v0.1
- ✓ Sandbox prevents risky operations (file deletion, table drops, network access) — v0.1
- ✓ Code execution is resource-limited (CPU, memory, timeout) — v0.1
- ✓ User data in sandbox is isolated (no access to other users' data) — v0.1
- ✓ Generated code is displayed with explanation before execution — v0.1
- ✓ Allowed Python libraries are defined in YAML configuration file — v0.1
- ✓ Code Checker Agent validates that generated code only imports allowed libraries — v0.1
- ✓ Execution failures trigger intelligent retry with error context (max 3 attempts) — v0.1

**Interactive Data Cards (8/8):**
- ✓ Query results display as Data Cards with streaming responses — v0.1
- ✓ Data Cards show Query Brief, Data Table, and AI Explanation sections — v0.1
- ✓ Data tables within cards are sortable and filterable — v0.1
- ✓ Results stream progressively (appear while AI is still processing) — v0.1
- ✓ Visual polish includes smooth animations, loading states, and transitions — v0.1
- ✓ User can view Python code generated for each analysis in Data Card — v0.1
- ✓ User can download data tables as CSV from Data Cards — v0.1
- ✓ User can download analysis report as Markdown from Data Cards — v0.1

**Settings & Profile (3/3):**
- ✓ User can view and edit profile information (first name, last name) — v0.1
- ✓ User can view account details (email address, account creation date) — v0.1
- ✓ User can change password from settings page — v0.1

**v0.1 Total: 42/42 requirements satisfied (100%)**

**✅ v0.2 Intelligence & Integration — Shipped 2026-02-10**

**Multi-LLM Provider Support (12/12):**
- ✓ System supports Ollama LLM provider (local and remote) — v0.2
- ✓ System supports OpenRouter gateway (100+ models) — v0.2
- ✓ LLM provider configuration externalized to YAML — v0.2
- ✓ System defaults to Sonnet 4.0 for all agents — v0.2
- ✓ Comprehensive test scenarios for each provider (34 tests) — v0.2
- ✓ Graceful error handling for LLM provider failures — v0.2
- ✓ Each agent configurable with different LLM provider — v0.2
- ✓ Each agent configurable with different model — v0.2
- ✓ Agent LLM configuration in YAML (provider, model, temperature) — v0.2
- ✓ Fail-fast startup validation for LLM configuration — v0.2
- ✓ Configuration changes require server restart — v0.2
- ✓ Empty response validation for all LLM invocations — v0.2

**Session Memory (8/8):**
- ✓ Multi-turn conversation context within same chat tab — v0.2
- ✓ Context persists after browser refresh (tab remains open) — v0.2
- ✓ Warning dialog before closing chat tab — v0.2
- ✓ Independent conversation memory per file tab — v0.2
- ✓ Configurable context window size (default: 12,000 tokens) — v0.2
- ✓ Warning at 85% context limit — v0.2
- ✓ Automatic pruning with user confirmation — v0.2
- ✓ Context usage display in chat interface — v0.2

**Manager Agent Routing (10/10):**
- ✓ Manager Agent routes to MEMORY_SUFFICIENT, CODE_MODIFICATION, or NEW_ANALYSIS — v0.2
- ✓ Configurable LLM provider for Manager Agent — v0.2
- ✓ Analyzes last 10 conversation messages for routing — v0.2
- ✓ Defaults to NEW_ANALYSIS on routing uncertainty — v0.2
- ✓ MEMORY_SUFFICIENT answers without code generation — v0.2
- ✓ CODE_MODIFICATION modifies existing code — v0.2
- ✓ NEW_ANALYSIS generates fresh code — v0.2
- ✓ Routing decisions logged with reasoning — v0.2
- ✓ Architecture designed for future route override commands — v0.2
- ✓ Single-route decision logic (no hybrid routes) — v0.2

**Smart Query Suggestions (6/6):**
- ✓ New chat tabs display 5-6 query suggestions — v0.2
- ✓ Suggestions grouped into 3 categories — v0.2
- ✓ Click suggestion to start chat — v0.2
- ✓ Suggestions based on data profiling results — v0.2
- ✓ Suggestions use real column names and data types — v0.2
- ✓ Suggestions persist until file re-analyzed — v0.2

**Web Search Integration (7/7):**
- ✓ Data Analysis Agent searches web via Tavily API — v0.2
- ✓ Agent decides when to search based on query content — v0.2
- ✓ Search results displayed with source citations — v0.2
- ✓ Web search configurable (API key, enabled/disabled) — v0.2
- ✓ Graceful degradation on quota exceeded — v0.2
- ✓ Graceful degradation on API unavailable — v0.2
- ✓ Search queries logged for cost tracking — v0.2

**Production Email (11/11):**
- ✓ SMTP protocol for email transport — v0.2
- ✓ SMTP config: host, port, username, password, TLS — v0.2
- ✓ SMTP config externalized to environment variables — v0.2
- ✓ Jinja2 email templates — v0.2
- ✓ Dev mode fallback when SMTP not configured — v0.2
- ✓ SMTP startup validation — v0.2
- ✓ Password reset via SMTP — v0.2
- ✓ Secure reset link format — v0.2
- ✓ Professional HTML email template — v0.2
- ✓ Dev mode auto-disabled when SMTP configured — v0.2
- ✓ Configurable reset link expiry (default: 10 min) — v0.2

**v0.2 Total: 54/54 requirements satisfied (100%)**

### Active

(No active requirements — define in next milestone via `/gsd:new-milestone`)

### Out of Scope

- **Email verification on signup** — Let users in immediately; add verification later for security
- **Save Data Cards to Collections** — Focus on real-time analysis; saving for review is polish
- **Full Collections organization** — Basic file list sufficient; collections add complexity
- **Google OAuth authentication** — Email/password sufficient for current validation
- **Visualization Agent** — Focus on accurate analysis first; charts can come later
- **PowerPoint export** — PDF export proves the concept first
- **Billing and subscription management** — Validate product-market fit before payment infrastructure
- **Credit tracking system** — No billing means no credits needed yet
- **S3/cloud file storage** — Local storage sufficient; cloud storage adds deployment complexity
- **Real-time collaboration** — Single-user experience for now
- **Mobile native apps** — Web-responsive design only
- **Data source integrations (APIs, databases)** — File upload only
- **Cross-session memory persistence** — Context pollution risk; session-scoped memory by design
- **Query safety filter** — Block PII extraction, prompt injection (deferred to v0.3)
- **Pydantic structured output for agents** — Eliminate inconsistent JSON across providers (deferred to v0.3)

## Context

**Target market:** Commercial SaaS product. Planning to offer subscriptions to customers who need accessible data analysis tools without coding skills.

**User experience priority:** The platform's success depends on making data analysis feel natural and accessible. Interactive UI, especially streaming responses and polished Data Cards, is critical. Users should see the AI "thinking" (generating code in real-time) and interact fluidly with results (sort, filter, explore).

**AI Agent architecture:** 5 specialized agents work together via LangGraph:
- **Manager Agent:** Routes queries to optimal path (memory-only, code modification, or new analysis)
- **Onboarding Agent:** Analyzes uploaded data structure, generates metadata, suggests initial queries
- **Coding Agent:** Generates Python code from natural language queries (or modifies existing code)
- **Code Checker Agent:** Validates code for security and correctness
- **Data Analysis Agent:** Interprets execution results, generates explanations, optionally searches web for context

**Security considerations:**
- Sandbox must prevent risky operations (file deletion, table drops, network access)
- Code execution must be deterministic (no infinite loops, time limits)
- User data must be isolated (segregated by user in file storage)
- Agent execution must be traceable (structured JSON logging for LLM calls)

**Technical ecosystem:**
- Backend: Python (FastAPI, LangGraph, LangChain, pandas, tiktoken, aiosmtplib, tavily-python)
- Frontend: Next.js 16 (React 19, TanStack Query, shadcn/ui)
- Agent framework: LangGraph with PostgreSQL checkpointing (AsyncPostgresSaver)
- LLM providers: Anthropic (default), OpenAI, Google, Ollama, OpenRouter
- Deployment: Docker-based, separate containers for frontend, backend, and AI agent engine

## Constraints

- **Team:** Single developer. Architecture must be simple enough for one person to build and maintain.
- **Budget:** Limited. Manager Agent routing reduces LLM costs ~40%. Choose efficient models where possible.
- **Tech stack:** Python backend (LangGraph + FastAPI), Next.js frontend, PostgreSQL database, local file storage. Locked in.
- **Security:** Code execution sandbox is non-negotiable. Generated Python code runs user-uploaded data.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js for frontend | Supports streaming AI responses natively, modern DX | ✓ Good — SSE streaming works excellently |
| 4 AI agents for v0.1 (skip Visualization) | Timeline constraint. Core agents are critical to accuracy. | ✓ Good — expanded to 5 agents in v0.2 with Manager Agent |
| Email auth only (defer Google OAuth) | Reduces complexity, faster to ship | ✓ Good — no user demand for OAuth yet |
| Skip email verification for v1 | Let users in immediately | ✓ Good — reduces signup friction |
| Tabbed file interface with per-file chat history | More intuitive than shared history | ✓ Good — natural UX, independent memory per tab |
| Session-scoped memory (no cross-session) | Avoid context pollution, clean slate per tab | ✓ Good — users get clean analysis per session |
| Manager Agent for query routing | Reduce response time ~40%, skip code gen for simple queries | ✓ Good — MEMORY_SUFFICIENT path is significantly faster |
| Tavily over Serper.dev for web search | Serper returns URLs only; Tavily returns full page content | ✓ Good — higher quality analysis with actual content |
| Per-agent LLM configuration via YAML | Enable cost optimization and vendor flexibility | ✓ Good — agents can use different models per use case |
| PostgreSQL checkpointing for memory | Native LangGraph integration, reliable persistence | ✓ Good — AsyncPostgresSaver works with proper lifecycle |
| DB-backed password reset tokens (not JWT) | Single-use, revocable, auditable | ✓ Good — more secure than JWT-based resets |
| LLM-generated query suggestions | Dataset-specific, not hardcoded templates | ✓ Good — suggestions reflect actual data structure |
| Local file storage (defer S3) | Simpler deployment, fewer dependencies | — Pending |
| Skip billing for v1 | Need product validation first | — Pending |

---
*Last updated: 2026-02-10 after v0.2 Intelligence & Integration milestone*
