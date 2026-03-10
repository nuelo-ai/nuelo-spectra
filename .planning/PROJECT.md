# Spectra

## What This Is

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. Users upload datasets (Excel/CSV), create chat sessions, link multiple files, and ask questions in natural language — receiving instant insights as interactive Data Cards with AI-generated Plotly charts. A ChatGPT-style session-centric UX with sidebar navigation enables multi-file conversations and cross-file analysis. A 6-agent AI system with intelligent query routing generates validated Python code in a secure sandbox, automatically creating visualizations when analysis benefits from charts. Multi-turn conversation memory, web search integration, smart query suggestions, 7 chart types with PNG/SVG export, and theme-aware Nord palette across 5 LLM providers. Fully deployable via Docker Compose (local) or Dokploy (production) with automatic admin seeding and fail-fast startup validation. Exposes a public REST API and MCP server for programmatic access and AI agent integrations. Now includes Spectra Pulse: users create Collections, attach CSV/Excel files, and run AI-powered anomaly detection that generates severity-sorted Signal cards with Plotly chart visualizations, statistical evidence, and downloadable Markdown reports — the foundation of the Detect → Explain → What-If analysis pipeline.

## Core Value

Accurate data analysis. The AI must generate correct, safe Python code that produces reliable results. If the code is wrong or the sandbox isn't secure, the entire product fails. Everything else—polish, features, exports—depends on users trusting the analysis is accurate.

## Repository

**GitHub:** https://github.com/marwazihs/nuelo-spectra.git (private)
**Remote:** origin
**Branch:** master
**Latest Tag:** v0.8 (2026-03-10)

## Previous Milestones

**v0.8 Spectra Pulse (Detection) (Shipped 2026-03-10):** Full Pulse Analysis module — Collections, file upload, AI-powered anomaly detection pipeline (multi-agent orchestrator + E2B sandbox), Signal cards with Plotly visualizations and statistical evidence, Markdown reports, tier-based workspace access gating, and delete/rename collection management. Establishes the Detect foundation of the Detect → Explain → What-If pipeline.

**v0.7.12 Spectra Pulse Mockup (Shipped 2026-03-05):** Standalone Next.js mockup (`pulse-mockup/`) covering full Analysis Workspace — Pulse detection, Collections, Guided Investigation, What-If Scenarios, and Admin Workspace Management. Design reference for v0.8–v0.12 implementation milestones.

**v0.7 API Services & MCP (Shipped 2026-02-25):** Public REST API and MCP server exposing Spectra's data analysis capabilities for programmatic access and AI agent integrations, with API key management, credit deduction, and usage logging.

## Current State

**Shipped:** v0.8 Spectra Pulse (Detection) (2026-03-10)
**Status:** Milestone complete — planning next milestone (v0.9)
**Codebase:** ~96,000 LOC (Python app + TypeScript/TSX across public frontend + admin frontend + pulse-mockup + Docker/shell infra)
**Tech Stack:** FastAPI + PostgreSQL + LangGraph + E2B + Tavily + Plotly + APScheduler (backend), Next.js 16 + React 19 + TanStack + Zustand + shadcn/ui + next-themes + Plotly.js + Recharts + Sonner (frontend + admin frontend), Docker + Dokploy + Tailscale (deployment), Next.js + shadcn/ui + Recharts (pulse-mockup)

**What works:**
- ✅ Complete authentication system with JWT, refresh tokens, and SMTP password reset
- ✅ File upload with AI-powered data profiling (Excel/CSV up to 50MB)
- ✅ ChatGPT-style session-centric UX with sidebar navigation and chronological chat history
- ✅ Multi-file linking per session with cross-file analysis (ContextAssembler + named DataFrames)
- ✅ My Files screen with TanStack Table, drag-and-drop upload, bulk delete, download, and Start Chat
- ✅ In-chat file linking via paperclip button, file selection modal, and drag-and-drop overlay
- ✅ Right sidebar panel showing linked files with info and remove actions
- ✅ File requirement enforcement (at least one file per session) with dual feedback
- ✅ LLM-powered session title auto-generation with manual rename lock
- ✅ 6-agent AI system (Onboarding, Manager, Coding, Code Checker, Data Analysis, Visualization) with LangGraph orchestration
- ✅ Multi-turn conversation memory with PostgreSQL checkpointing and token counting
- ✅ Manager Agent with intelligent 3-path query routing (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS)
- ✅ Smart query suggestions on welcome screen and follow-up chips on DataCards
- ✅ Tavily-powered web search tool with transparent source citations and quota tracking
- ✅ 5 LLM providers (Anthropic, OpenAI, Google, Ollama, OpenRouter) with per-agent YAML config
- ✅ Real-time SSE streaming showing AI thinking process
- ✅ Interactive Data Cards with sortable tables, code display, and CSV/Markdown exports
- ✅ AI-generated Plotly charts with intelligent visualization discretion (7 types: bar, line, scatter, histogram, box, pie, donut)
- ✅ Interactive charts with zoom, pan, hover tooltips, responsive resizing, and PNG/SVG export (1200x800)
- ✅ Chart type switcher for compatible types (bar ↔ line ↔ scatter) with client-side instant rendering
- ✅ Dark/light theme toggle with Nord palette for all UI surfaces including charts (persists across sessions)
- ✅ Production SMTP email service with DB-backed single-use password reset tokens
- ✅ Admin portal with split-horizon architecture (SPECTRA_MODE: public/admin/dev)
- ✅ Credit system with atomic deduction, tier-based allocations, and APScheduler auto-resets
- ✅ User management (list, search, filter, activate/deactivate, password reset, tier change, credit adjust, delete)
- ✅ Email invitation system with time-limited single-use tokens and invite-only registration
- ✅ Platform settings with runtime configuration (signup toggle, default tier, invite expiry, credit cost)
- ✅ Admin dashboard with metrics, Recharts trend charts, credit distribution, and audit log
- ✅ Separate admin Next.js frontend (admin-frontend/) with shadcn/ui + Recharts
- ✅ Production Dockerfiles for all 3 services (backend multi-stage uv, frontend/admin standalone Next.js)
- ✅ Docker Compose for local full-stack dev (single `docker compose up --build`)
- ✅ 4 Dokploy services with Tailscale split-horizon (public HTTPS, admin VPN-only)
- ✅ Fail-fast startup validation: backend refuses to boot in dev/admin mode without ADMIN_EMAIL/ADMIN_PASSWORD
- ✅ Automatic admin seeding on container startup (after migrations, before uvicorn)
- ✅ DEPLOYMENT.md — step-by-step Dokploy + Tailscale deployment guide
- ✅ API key management with SHA-256 hashing, `spe_` prefix, user self-service + admin management
- ✅ Public REST API v1: file upload/list/download/delete, file context get/update, synchronous query with credit deduction
- ✅ API usage logging per user and per API key (endpoint, credits used, status code)
- ✅ `SPECTRA_MODE=api` as 5th deployment mode with Bearer token auth and wildcard CORS
- ✅ MCP server with 6 curated `spectra_` tools via FastMCP 3.0.2, mounted at `/mcp/`
- ✅ MCP Bearer token auth middleware with per-request validation on tool calls and tool listing
- ✅ Spectra Pulse: Collection and file management (create/list/detail/rename/delete, CSV/Excel upload with column profiling)
- ✅ Spectra Pulse: AI-powered anomaly detection pipeline — multi-agent orchestrator (brain/orchestrator + coder/validator/interpreter/viz sub-agents) with E2B sandbox (300s timeout), Pydantic structured output on all LLM calls
- ✅ Spectra Pulse: Signal output with severity tiers (critical/warning/info), Plotly chart visualizations, 2x2 statistical evidence grid, and Markdown reports with download
- ✅ Spectra Pulse: Inline detection progress banner, sonner toast on completion with signal count, re-run confirmation dialog, credit cost pre-check (402) + atomic deduction + automatic refund
- ✅ Spectra Pulse: Tier-based workspace access gating (workspace_access + max_active_collections per tier in user_classes.yaml), runtime-configurable credit cost via Admin Portal
- ✅ Spectra Pulse: (workspace) route group with own sidebar layout and Hex.tech dark palette (independent of chat interface)

**Known limitations:**
- E2B sandboxes created per-execution (no warm pools - ~150ms cold start per query)
- Basic mobile responsiveness (functional but not optimized)
- No query safety filter in Manager Agent (PII extraction, prompt injection not blocked)
- Agent JSON responses not using Pydantic structured output (inconsistent across providers)
- In-memory admin login lockout (upgrade to Redis for multi-instance)
- In-memory token revocation set (same single-instance caveat)
- Bulk credit adjustment by user class not yet implemented (CREDIT-11)
- Per-tier credit overrides not yet in admin UI (SETTINGS-06, TIER-02)

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

**✅ v0.3 Multi-file Conversation Support — Shipped 2026-02-12**

**Chat Sessions (9/9):**
- ✓ User can create a new chat session from the left sidebar "New Chat" button — v0.3
- ✓ User is greeted with a welcome screen when opening a new chat session — v0.3
- ✓ User must link at least one file to a chat session before sending messages — v0.3
- ✓ User can view chat history in the left sidebar grouped chronologically — v0.3
- ✓ User can click a chat from the sidebar to open that session — v0.3
- ✓ Chat sessions persist across browser sessions — v0.3
- ✓ User can have multiple independent chat sessions — v0.3
- ✓ Chat session title is auto-generated from the first user message — v0.3
- ✓ User is greeted with a new chat session upon login — v0.3

**File Linking (8/8):**
- ✓ User can upload a new file within a chat session via paperclip button — v0.3
- ✓ User can link an existing file to a chat session via file selection modal — v0.3
- ✓ User can drag and drop a file into the chat session to upload and link — v0.3
- ✓ Linked files displayed in collapsible right sidebar panel — v0.3
- ✓ User can view file context via info icon on each linked file — v0.3
- ✓ AI agents can perform cross-file analysis across all linked files — v0.3
- ✓ User can add additional files to an existing chat session — v0.3
- ✓ Maximum 10 files per session enforced at API level — v0.3

**File Management (7/7):**
- ✓ User can access "My Files" screen from the left sidebar — v0.3
- ✓ User can view all uploaded files with metadata (name, size, type, date) — v0.3
- ✓ User can upload a new file from My Files screen — v0.3
- ✓ User can view file context/details from My Files — v0.3
- ✓ User can start a new chat session with a selected file from My Files — v0.3
- ✓ User can delete a file from My Files with confirmation — v0.3
- ✓ User can download a previously uploaded file — v0.3

**Layout & Navigation (5/5):**
- ✓ Left sidebar with New Chat, chat history, and My Files — v0.3
- ✓ Main content area displays active chat or My Files — v0.3
- ✓ Right sidebar panel shows linked files (collapsible) — v0.3
- ✓ File-tab navigation replaced by sidebar session navigation — v0.3
- ✓ Left sidebar is collapsible — v0.3

**Data Model & Backend (6/6):**
- ✓ Chat sessions as first-class database entities — v0.3
- ✓ Many-to-many file-session relationship — v0.3
- ✓ Chat messages belong to sessions (not files) — v0.3
- ✓ v0.2 conversations migrated to session model — v0.3
- ✓ LangGraph checkpoints preserved during migration — v0.3
- ✓ File deletion removes from sessions but preserves messages — v0.3

**Appearance (2/2):**
- ✓ Light/dark theme toggle — v0.3
- ✓ Theme preference persists across sessions — v0.3

**v0.3 Total: 37/37 requirements satisfied (100%)**

**✅ v0.4 Data Visualization — Shipped 2026-02-15**

**Infrastructure (4/4):**
- ✓ Plotly added to allowed libraries in allowlist.yaml — v0.4
- ✓ State schema extended with visualization fields — v0.4
- ✓ E2B sandbox Plotly 6.0.1 availability verified — v0.4
- ✓ Sandbox output parser modified to capture chart JSON — v0.4

**Visualization Agent (6/6):**
- ✓ Visualization Agent module created with LangGraph integration — v0.4
- ✓ Agent prompt configured in prompts.yaml with LLM settings — v0.4
- ✓ Agent generates Plotly Python code from execution results — v0.4
- ✓ Agent embeds data as Python literal (no file uploads) — v0.4
- ✓ Agent includes chart type selection heuristics — v0.4
- ✓ Chart code outputs JSON via fig.to_json() to stdout — v0.4

**Chart Generation (11/11):**
- ✓ System supports bar chart generation — v0.4
- ✓ System supports line chart generation — v0.4
- ✓ System supports scatter plot generation — v0.4
- ✓ System supports histogram generation — v0.4
- ✓ System supports box plot generation — v0.4
- ✓ System supports pie chart generation — v0.4
- ✓ System supports donut chart generation — v0.4
- ✓ Data Analysis Agent decides when visualization adds value — v0.4
- ✓ Manager Agent hints visualization intent during routing — v0.4
- ✓ Chart generation errors are non-fatal — v0.4
- ✓ Charts include meaningful titles and axis labels — v0.4

**Graph Integration (6/6):**
- ✓ Visualization Agent node added to LangGraph — v0.4
- ✓ viz_execute node executes chart code in sandbox — v0.4
- ✓ viz_response node handles chart results — v0.4
- ✓ should_visualize() conditional edge routes based on flag — v0.4
- ✓ da_response modified for conditional routing — v0.4
- ✓ Chart JSON streams to frontend via SSE events — v0.4

**Chart Display (7/7):**
- ✓ Frontend installs plotly.js-dist-min package — v0.4
- ✓ ChartRenderer component created with dynamic import — v0.4
- ✓ ChartRenderer uses Plotly.newPlot() with React hooks — v0.4
- ✓ DataCard renders chart above table when specs exist — v0.4
- ✓ Charts are interactive (zoom, pan, hover tooltips) — v0.4
- ✓ Charts are responsive (resize with container) — v0.4
- ✓ Chart skeleton loader displays during generation — v0.4

**Export & Customization (5/5):**
- ✓ User can download chart as PNG via Plotly.downloadImage() — v0.4
- ✓ User can download chart as SVG — v0.4
- ✓ Download buttons appear below chart in DataCard — v0.4
- ✓ User can switch chart type after generation — v0.4
- ✓ Chart type switcher only shows applicable types — v0.4

**Theme & Polish (4/4):**
- ✓ Charts respect light/dark theme toggle — v0.4
- ✓ Charts use transparent backgrounds in dark mode — v0.4
- ✓ Chart colors match Nord palette in dark mode — v0.4
- ✓ Chart text colors adjust for theme (readable both modes) — v0.4

**v0.4 Total: 43/43 requirements satisfied (100%)**

**✅ v0.5 Admin Portal — Shipped 2026-02-18**

**Admin Authentication (7/7):**
- ✓ Admin accounts via is_admin flag, CLI seed, email+password auth — v0.5
- ✓ Admin-only API access with 403 for non-admins — v0.5
- ✓ Session timeout after configurable inactivity (default 30 min) — v0.5
- ✓ All admin actions audit-logged (admin_id, action, target, timestamp, details) — v0.5

**Admin Dashboard (7/7):**
- ✓ Dashboard with total users, signups, sessions, files, messages, credit summary — v0.5
- ✓ Recharts trend charts for signups and messages over time — v0.5

**User Management (13/13):**
- ✓ User list with pagination, search, filter, sort — v0.5
- ✓ User profile, status, tier, credits, file/session counts — v0.5
- ✓ Activate/deactivate, password reset, tier change, credit adjust, delete — v0.5

**Signup Control (4/4):**
- ✓ Global toggle, invite-only message, token-only registration, immediate effect — v0.5

**User Invitation (8/8):**
- ✓ Email invites with time-limited single-use links, revoke/resend — v0.5
- ✓ Registration with pre-filled locked email, auto-login — v0.5

**User Class Management (6/7):**
- ✓ Static tiers in YAML, tier summary with user counts, tier assignment — v0.5
- ⚠ TIER-02 deferred: Admin editing tier credit amounts via UI

**Credit Management (12/13):**
- ✓ Atomic deduction, zero-credits blocking, balance/history views, manual adjust/reset — v0.5
- ✓ APScheduler auto-resets, idempotent reset tracking — v0.5
- ⚠ CREDIT-11 deferred: Bulk-adjust credits by user class

**Platform Settings (7/8):**
- ✓ Centralized settings, signup toggle, default tier, invite expiry, credit cost — v0.5
- ⚠ SETTINGS-06 deferred: Per-tier credit overrides

**Architecture (10/10):**
- ✓ Split-horizon SPECTRA_MODE, mode-aware CORS, separate admin frontend — v0.5
- ✓ Defense-in-depth: network isolation + JWT + role enforcement + audit — v0.5

**Database (9/9):**
- ✓ 5 new tables, is_admin + user_class fields, Alembic migration with backfill — v0.5

**v0.5 Total: 82/86 requirements satisfied (95%, 3 consciously deferred)**

**✅ v0.6 Docker and Dokploy Support — Shipped 2026-02-21**

**Pre-Work (5/5):**
- ✓ No hardcoded localhost URLs in frontend source — v0.6
- ✓ Both Next.js apps build with `output: standalone` for Docker multi-stage builds — v0.6
- ✓ BACKEND_URL is a runtime env var (not baked at build time) — v0.6
- ✓ `/api/health` route handler on both frontends for Dokploy health monitoring — v0.6
- ✓ Route handler proxies replace next.config.ts rewrites (SSE streaming, runtime BACKEND_URL, trailing slash fix) — v0.6

**Version API (3/3):**
- ✓ `GET /version` returns version and environment on backend — v0.6
- ✓ Version displayed live on public frontend settings page — v0.6
- ✓ Version displayed live on admin frontend settings page — v0.6

**Docker (5/5):**
- ✓ .dockerignore files for all 3 services (no secrets, no node_modules) — v0.6
- ✓ `docker-entrypoint.sh` with pg_isready wait, alembic migrations, exec uvicorn as PID 1 — v0.6
- ✓ Dockerfile.backend (multi-stage uv build, non-root appuser) — v0.6
- ✓ Dockerfile.frontend (3-stage standalone Next.js build) — v0.6
- ✓ Dockerfile.admin (3-stage standalone Next.js build) — v0.6

**Docker Compose (4/4):**
- ✓ `compose.yaml` runs full stack with single `docker compose up --build` — v0.6
- ✓ Health-ordered startup: db healthy → backend → frontends — v0.6
- ✓ Named volumes for PostgreSQL data and file uploads persistence — v0.6
- ✓ `.env.docker.example` documents all required config vars — v0.6

**Dokploy (8/8):**
- ✓ Public backend deployed (SPECTRA_MODE=public, migrations applied, health 200) — v0.6
- ✓ Public frontend at HTTPS domain with valid Let's Encrypt cert — v0.6
- ✓ Admin backend reachable only via Tailscale (SPECTRA_MODE=admin) — v0.6
- ✓ Admin frontend reachable only via Tailscale — v0.6
- ✓ File uploads persist across Dokploy redeployments (named volume) — v0.6
- ✓ Tailscale installed, iptables DOCKER-USER rules blocking ports 8001/3001 from public — v0.6
- ✓ Full smoke test passed (8 points: public HTTPS, admin VPN, isolation, file persistence) — v0.6
- ✓ DEPLOYMENT.md (401 lines) — step-by-step guide — v0.6

**Admin Seed (3/3):**
- ✓ Backend refuses to start in dev/admin mode without ADMIN_EMAIL/ADMIN_PASSWORD (Pydantic model_validator) — v0.6
- ✓ Admin user automatically seeded on container startup after migrations — v0.6
- ✓ `.env.docker.example` accurately documents credentials as required for dev/admin modes — v0.6

**v0.6 Total: 28/28 requirements satisfied (100%)**

**✅ v0.7 API Services & MCP — Shipped 2026-02-25**

**API Key Management (8/8):**
- ✓ User can view, create, and revoke API keys from Settings page — v0.7
- ✓ Admin can view, create, and revoke API keys for any user — v0.7
- ✓ API keys stored securely with SHA-256 hashing, full key shown only once — v0.7

**API Authentication & Security (4/4):**
- ✓ API requests authenticate via Bearer token, invalid/revoked keys return 401 — v0.7
- ✓ API calls deduct credits, usage logged per user and per API key — v0.7

**REST API v1 (8/8):**
- ✓ File management: upload, list, download, delete — v0.7
- ✓ File context: get detail, update summary/context, get suggestions — v0.7
- ✓ Synchronous query with full analysis result (code, chart spec, explanation) — v0.7

**API Infrastructure (5/5):**
- ✓ SPECTRA_MODE=api enables API routes, deployable as 5th Dokploy service — v0.7
- ✓ API routes versioned under /api/v1/, active in dev mode alongside existing routes — v0.7
- ✓ Structured request/error logging for all API requests — v0.7

**MCP Server (5/5):**
- ✓ 6 curated spectra_ tools for upload, query, list, delete, download, get context — v0.7
- ✓ MCP server authenticates using Bearer token API keys — v0.7

**v0.7 Total: 30/30 requirements satisfied (100%)**

**✅ v0.7.12 Spectra Pulse Mockup — Shipped 2026-03-05**

- ✓ Mockup: Analysis Workspace entry and Collection list page — v0.7.12
- ✓ Mockup: Collection detail page with file selection and Run Detection flow — v0.7.12
- ✓ Mockup: Signal cards UI (left panel list + main detail panel with chart, severity, evidence) — v0.7.12
- ✓ Mockup: Guided Investigation Q&A flow (structured choices, progress indicator, root cause card) — v0.7.12
- ✓ Mockup: What-If Scenarios (objective setting, scenario cards, refinement chat, comparison view) — v0.7.12
- ✓ Mockup: Collections reports viewer with download options — v0.7.12
- ✓ Mockup: Chat-to-Collection bridge (Add to Collection action on data cards) — v0.7.12
- ✓ Mockup: Admin Workspace Activity Dashboard (charts, funnel, KPI cards) — v0.7.12
- ✓ Mockup: Admin per-user Workspace tab extension — v0.7.12
- ✓ Mockup: Admin Workspace Credit Costs settings section — v0.7.12
- ⚠ COLL-01: Archive/unarchive status indicators — deferred (known gap, not fully implemented)
- ⚠ COLL-02: Collection limit usage display ("3 of 5 active collections") — deferred (known gap)

**v0.7.12 Total: 32/34 requirements satisfied (94%)**

**✅ v0.8 Spectra Pulse (Detection) — Shipped 2026-03-10**

- ✓ COLL-01: User can create a Collection with a name — v0.8
- ✓ COLL-02: User can view list of their Collections — v0.8
- ✓ COLL-03: User can view Collection detail with 4-tab layout (Overview, Files, Signals, Reports) — v0.8
- ✓ COLL-04: User can update (rename) a Collection — v0.8
- ✓ COLL-DELETE: User can delete a Collection with cascade — v0.8
- ✓ FILE-01: User can upload CSV/Excel files to a Collection — v0.8
- ✓ FILE-02: User can view column profile of an uploaded file (DataSummaryPanel slide-out) — v0.8
- ✓ FILE-03: User can select files via checkboxes to activate Run Detection — v0.8
- ✓ FILE-04: User can remove a file from a Collection — v0.8
- ✓ PULSE-01: User can trigger Pulse detection on selected files (Run Detection button with credit cost) — v0.8
- ✓ PULSE-02: System pre-checks credit balance, blocks run if insufficient (402) — v0.8
- ✓ PULSE-03: System deducts flat credit cost before execution and refunds on failure — v0.8
- ✓ PULSE-04: Inline detection progress banner with animated steps on Overview tab — v0.8
- ✓ PULSE-05: After detection, user navigated to Detection Results page with Signals — v0.8
- ✓ SIGNAL-01: Signal list sorted by severity (critical → warning → info) on Detection Results page — v0.8
- ✓ SIGNAL-02: Highest-severity Signal auto-selected on Detection Results load — v0.8
- ✓ SIGNAL-03: Signal detail panel with severity/category badges, Plotly chart, analysis text, statistical evidence grid, Investigation + What-If buttons (disabled) — v0.8
- ✓ SIGNAL-04: Signal chart type driven by chartType field (bar/line/scatter via Plotly) — v0.8
- ✓ REPORT-01: Reports tab listing all reports with type badge, title, source, date, View Report button — v0.8
- ✓ REPORT-02: Full-page report viewer with sticky header, markdown-rendered content — v0.8
- ✓ REPORT-03: Markdown report download — v0.8
- ✓ REPORT-04: PDF download button present but disabled (v0.9) — v0.8
- ✓ NAV-01 through NAV-04: Workspace sidebar nav, Overview stat cards, Signals tab, credit usage pill — v0.8
- ✓ ADMIN-01: Tier-based workspace access (workspace_access + max_active_collections in user_classes.yaml) — v0.8
- ✓ ADMIN-02: workspace_credit_cost_pulse configurable via Admin Portal (runtime, no redeploy) — v0.8
- ✓ PIPE-01–08: Multi-agent orchestrator pipeline with Pydantic structured output, inline UX, toast notifications, re-run dialog — v0.8

**v0.8 Total: 35/35 requirements satisfied (100%)**

## Next Milestone

<!-- Requirements for next milestone defined in .planning/REQUIREMENTS.md after /gsd:new-milestone -->

### Active

*(No active requirements — start next milestone with `/gsd:new-milestone`)*

### Out of Scope

- **Email verification on signup** — Let users in immediately; add verification later for security
- **Save Data Cards to Collections** — Focus on real-time analysis; saving for review is polish
- **Full Collections organization** — Basic file list sufficient; collections add complexity
- **Google OAuth authentication** — Email/password sufficient for current validation
- **PowerPoint export** — PDF export proves the concept first
- **Billing and subscription management** — Validate product-market fit before payment infrastructure
- **S3/cloud file storage** — Local storage sufficient; cloud storage adds deployment complexity
- **Real-time collaboration** — Single-user experience for now
- **Mobile native apps** — Web-responsive design only
- **Data source integrations (APIs, databases)** — File upload only
- **Cross-session memory persistence** — Context pollution risk; session-scoped memory by design
- **Query safety filter** — Block PII extraction, prompt injection (deferred to future milestone)
- **Pydantic structured output for agents** — Eliminate inconsistent JSON across providers (deferred to future milestone)
- **Automatic cross-file joins without user intent** — Schema mismatches and Cartesian products risk wrong results
- **Conversation branching/forking** — Complex UX and data model, not requested
- **Folder/directory organization for files** — Over-engineering for 5-50 files

## Context

**Target market:** Commercial SaaS product. Planning to offer subscriptions to customers who need accessible data analysis tools without coding skills.

**User experience priority:** The platform's success depends on making data analysis feel natural and accessible. Interactive UI, especially streaming responses and polished Data Cards, is critical. Users should see the AI "thinking" (generating code in real-time) and interact fluidly with results (sort, filter, explore).

**AI Agent architecture:** 6 specialized agents work together via LangGraph:
- **Manager Agent:** Routes queries to optimal path (memory-only, code modification, or new analysis)
- **Onboarding Agent:** Analyzes uploaded data structure, generates metadata, suggests initial queries
- **Coding Agent:** Generates Python code from natural language queries (or modifies existing code)
- **Code Checker Agent:** Validates code for security and correctness
- **Data Analysis Agent:** Interprets execution results, generates explanations, optionally searches web for context
- **Visualization Agent:** Generates Plotly chart code when analysis benefits from visualization

**Security considerations:**
- Sandbox must prevent risky operations (file deletion, table drops, network access)
- Code execution must be deterministic (no infinite loops, time limits)
- User data must be isolated (segregated by user in file storage)
- Agent execution must be traceable (structured JSON logging for LLM calls)
- Admin routes protected by network isolation (Tailscale) + JWT + role enforcement + audit logging

**Technical ecosystem:**
- Backend: Python (FastAPI, LangGraph, LangChain, pandas, tiktoken, aiosmtplib, tavily-python)
- Frontend: Next.js 16 (React 19, TanStack Query, Zustand, shadcn/ui, next-themes)
- Agent framework: LangGraph with PostgreSQL checkpointing (AsyncPostgresSaver)
- LLM providers: Anthropic (default), OpenAI, Google, Ollama, OpenRouter
- Deployment: Docker + Dokploy + Tailscale (production), Docker Compose (local dev)

## Constraints

- **Team:** Single developer. Architecture must be simple enough for one person to build and maintain.
- **Budget:** Limited. Manager Agent routing reduces LLM costs ~40%. Choose efficient models where possible.
- **Tech stack:** Python backend (LangGraph + FastAPI), Next.js frontend, PostgreSQL database, local file storage. Locked in.
- **Security:** Code execution sandbox is non-negotiable. Generated Python code runs user-uploaded data.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js for frontend | Supports streaming AI responses natively, modern DX | ✓ Good — SSE streaming works excellently |
| 4 AI agents for v0.1 (skip Visualization) | Timeline constraint. Core agents are critical to accuracy. | ✓ Good — expanded to 6 agents by v0.4 |
| Email auth only (defer Google OAuth) | Reduces complexity, faster to ship | ✓ Good — no user demand for OAuth yet |
| Skip email verification for v1 | Let users in immediately | ✓ Good — reduces signup friction |
| Tabbed file interface with per-file chat history | More intuitive than shared history | ✓ Replaced — session-centric UX shipped in v0.3 |
| Session-scoped memory (no cross-session) | Avoid context pollution, clean slate per tab | ✓ Good — users get clean analysis per session |
| Manager Agent for query routing | Reduce response time ~40%, skip code gen for simple queries | ✓ Good — MEMORY_SUFFICIENT path is significantly faster |
| Tavily over Serper.dev for web search | Serper returns URLs only; Tavily returns full page content | ✓ Good — higher quality analysis with actual content |
| Per-agent LLM configuration via YAML | Enable cost optimization and vendor flexibility | ✓ Good — agents can use different models per use case |
| PostgreSQL checkpointing for memory | Native LangGraph integration, reliable persistence | ✓ Good — AsyncPostgresSaver works with proper lifecycle |
| DB-backed password reset tokens (not JWT) | Single-use, revocable, auditable | ✓ Good — more secure than JWT-based resets |
| LLM-generated query suggestions | Dataset-specific, not hardcoded templates | ✓ Good — suggestions reflect actual data structure |
| Local file storage (defer S3) | Simpler deployment, fewer dependencies | ✓ Good — named volumes work for current scale |
| Skip billing for v1 | Need product validation first | — Pending |
| Chat-session-centric UX (v0.3) | Enable multi-file analysis, ChatGPT-style conversations | ✓ Good — ChatGPT-style sidebar + sessions shipped, UAT passed |
| Cross-file analysis support | AI can reference all linked files in a single query | ✓ Good — ContextAssembler with named DataFrames and join hints works well |
| At least one file required per chat | Prevents empty chats, maintains data analysis focus | ✓ Good — dual feedback (toast + inline warning) provides clear UX |
| Session-based thread IDs for LangGraph | Enable session-scoped memory independent of files | ✓ Good — migration preserved all v0.2 conversation history |
| Nord palette for dark theme | Professional, muted aesthetic for dark mode | ✓ Good — consistent across all UI surfaces |
| Eager session creation on file link | Create session when file is linked at /sessions/new (not on first message) | ✓ Good — enables sidebar to open and file panel to render immediately |
| sessionStorage for cross-navigation state | Pass sidebar-open flag across router.replace navigations | ✓ Good — reliable mechanism where Zustand state may not persist |
| Client-side chart export | Plotly.downloadImage() instead of server-side Kaleido | ✓ Good — instant export, Kaleido requires Chrome and is 50x slower |
| Custom ChartRenderer | Build custom component instead of react-plotly.js wrapper | ✓ Good — react-plotly.js unmaintained (3 years), custom is more reliable |
| Chart failure non-fatal | Preserve analysis and data table on chart errors | ✓ Good — graceful degradation doesn't block core analytics value |
| LLM-based chart intelligence | Manager hints, DA confirms visualization_requested | ✓ Good — two-phase decision reduces false positives |
| Nord palette for charts | Consistent theme-aware colors across all UI | ✓ Good — professional aesthetic, readable in both modes |
| Split-horizon SPECTRA_MODE | Same codebase, env var controls routing (public/admin/dev) | ✓ Good — simple deployment, no code duplication |
| Separate admin Next.js app | admin-frontend/ not a route in public frontend | ✓ Good — independent deploy, no bundle bloat on public app |
| is_admin flag on users table | Binary admin/non-admin, not separate admin table | ✓ Good — simple, single-instance sufficient |
| NUMERIC(10,1) credits | Float precision for credit deduction | ✓ Good — avoids float rounding, supports 0.5 credit costs |
| SELECT FOR UPDATE for credits | Atomic deduction prevents overdraw | ✓ Good — race condition proof at DB level |
| Static tiers in YAML | user_classes.yaml, admin edits overrides | ✓ Good — version-controlled, simple for 3-5 tiers |
| Platform settings with TTL cache | 30s cache, runtime changes without restart | ✓ Good — immediate effect for signup toggle, invite expiry |
| String(20) for user_class | Not PostgreSQL ENUM | ✓ Good — avoids ALTER TYPE migration pain |
| Three-step migration pattern | Add nullable → backfill → alter NOT NULL | ✓ Good — safe for production with existing data |
| APScheduler for credit resets | In-process scheduler, not external cron | ✓ Good — single dep, configurable per tier |
| Challenge codes for delete | Backend-driven, not client-side | ✓ Good — prevents accidental bulk deletion |
| Deferred CREDIT-11, SETTINGS-06, TIER-02 | Bulk credit adjust + per-tier overrides | — Pending for future milestone |
| Route handler proxy over next.config.ts rewrites | Rewrites buffer SSE, bake BACKEND_URL at build time, strip trailing slashes causing auth loss | ✓ Good — SSE streams correctly, BACKEND_URL is runtime, no trailing slash issues |
| APP_VERSION in Pydantic Settings (not os.getenv) | Pydantic extra=forbid rejects unknown .env vars; consistent with other config | ✓ Good — validates at startup, single source of truth |
| model_validator(mode='after') for credential enforcement | Fires at lru_cache construction — process exits before uvicorn starts | ✓ Good — fail-fast at import time, clear error naming missing vars |
| Empty string defaults for admin_email/admin_password | Making them required= fields would break public mode | ✓ Good — validator provides explicit error; public mode passes silently |
| Conditional seed in docker-entrypoint.sh | `[ -n "${ADMIN_EMAIL:-}" ]` gates seed between migrations and uvicorn | ✓ Good — no manual seed-admin step needed for Docker deployments |
| Tailscale for admin service isolation | VPN-only access without reverse proxy complexity | ✓ Good — iptables DOCKER-USER rules block admin ports from public internet |
| 4 Dokploy Application services (not 1 Compose stack) | Independent deploy, scale, and restart per service | ✓ Good — cleaner than managing a remote compose stack |
| Backend has no public domain | Reduced attack surface; frontend proxies via Swarm DNS | ✓ Good — simpler than exposing backend directly |

| v0.7.11 mockup as separate Next.js app (pulse-mockup/) | Zero interference with production codebase; mockup is design-only, not deployable alongside real app | ✓ Good — clean separation, 7,869 LOC in 62 files |
| SHA-256 API key hashing (not Argon2) | High-entropy random token; industry standard (GitHub, Stripe), no perf penalty | ✓ Good — fast auth with no brute-force risk on random tokens |
| `spe_` prefix for API keys | Recognizable in logs and configs | ✓ Good — easy to identify and route in auth middleware |
| MCP tools call REST API via httpx loopback | Preserves credit deduction and usage logging middleware chain | ✓ Good — single billing path for both REST and MCP |
| Unified get_authenticated_user() dependency | JWT fast path first, SHA-256 key fallback | ✓ Good — existing frontend auth unchanged, API keys "just work" |
| FastMCP 3.0.2 with manually curated tools | Auto-generation produces poor LLM tool descriptions | ✓ Good — better tool discovery by AI agents |
| Stateless HTTP transport for MCP | Each request independent, no session state | ✓ Good — simpler deployment, works behind load balancers |
| Hex.tech dark palette for pulse-mockup | #0a0e1a bg, #111827 cards, #1e293b borders, #3b82f6 accent | ✓ Good — visually distinctive and consistent across all mockup screens |
| Admin layout without Header component | Each admin page renders its own page title inline | ✓ Good — simpler layout, consistent with admin design pattern |
| CSS funnel chart (proportional divs) | No external library needed for funnel approximation | ✓ Good — zero dependency, adequate fidelity for mockup |
| key={selectedScenarioId} for WhatIfRefinementChat | React remount on scenario switch — no useEffect reset needed | ✓ Good — clean state isolation without manual cleanup |
| Violet color scheme for What-If UI | Distinguishes from blue Investigation theme | ✓ Good — clear visual hierarchy across feature areas |
| CollectionFile `__tablename__ = "collection_files"` | Avoid import collision with existing `app.models.file.File` | ✓ Good — zero collision, naming convention established |
| E2B Pulse sandbox timeout 300s | Pulse analysis is CPU/IO intensive; 60s default would time out all runs | ✓ Good — all runs complete reliably |
| Stateless LangGraph Pulse pipeline | Each ainvoke() starts fresh, no message history between runs | ✓ Good — clean slate per detection, no state bleed |
| Flat credit cost for Pulse (workspace_credit_cost_pulse) | Per-file pricing creates unpredictable costs for multi-file collections | ✓ Good — predictable billing, confirmed over per-file |
| Pulse endpoints in collections.py (not new router) | Consistent with existing file/report pattern in same router | ✓ Good — uniform namespace, no extra router registration |
| Multi-agent orchestrator over monolithic pipeline | Monolith: hard to test, hard to add per-signal retry; orchestrator: composable sub-agents | ✓ Good — each sub-agent independently testable; rerunnable per signal |
| with_structured_output() on reasoning LLM calls only | Coder/Viz agents produce code, not JSON — structured output incompatible | ✓ Good — Pydantic validation where possible, raw invocation where needed |
| (workspace) route group parallel to (dashboard) | Workspace sidebar must not inherit ChatSidebar layout | ✓ Good — clean routing isolation, no layout bleed |
| Inline progress banner (not full-page overlay) | Full-page overlay blocks user from navigating away; inline is non-blocking | ✓ Good — users can browse other collections while detection runs |
| Sonner toast on detection completion | User may navigate away during long-running detection; needs notification regardless of page | ✓ Good — global notification works on any workspace page |
| Re-run deletes signals and reports before persisting new ones | Stale signals from previous run would confuse results; clean slate required | ✓ Good — PulseRun audit records kept; signals/reports always reflect latest run |
| Signal chart_data is Plotly fig.to_json() | Reuses existing ChartRenderer infrastructure from chat analysis | ✓ Good — consistent rendering across chat and workspace |
| DropdownMenu trigger uses e.preventDefault() on collection cards | CollectionCard is wrapped in Link; clicking kebab menu triggered navigation | ✓ Good — reliable prevention without losing event bubbling |
| Zustand detection state scoped per collectionId | Global store caused all collection pages to show running state simultaneously | ✓ Good — reactive selectors required (not getter functions) for re-render triggers |

## Current Milestone: v0.8.1 UI Fixes & Enhancement

**Goal:** Fix UI polish issues across Leftbar, Pulse Analysis, Chat, and Files sections to improve usability and mobile responsiveness.

**Target features:**
- Leftbar toggle visibility and menu alignment fixes
- Pulse Analysis: credit used display, mobile-responsive Signal View, "Chat with Spectra" button, timestamps on history lists
- Chat: remove logo from main panel, rightbar toggle fixes
- Files: remove logo from main panel, leftbar toggle position fix

---
*Last updated: 2026-03-10 after v0.8.1 milestone started*
