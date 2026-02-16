# Spectra

## What This Is

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. Users upload datasets (Excel/CSV), create chat sessions, link multiple files, and ask questions in natural language — receiving instant insights as interactive Data Cards with AI-generated Plotly charts. A ChatGPT-style session-centric UX with sidebar navigation enables multi-file conversations and cross-file analysis. A 6-agent AI system with intelligent query routing generates validated Python code in a secure sandbox, automatically creating visualizations when analysis benefits from charts. Multi-turn conversation memory, web search integration, smart query suggestions, 7 chart types with PNG/SVG export, and theme-aware Nord palette across 5 LLM providers.

## Core Value

Accurate data analysis. The AI must generate correct, safe Python code that produces reliable results. If the code is wrong or the sandbox isn't secure, the entire product fails. Everything else—polish, features, exports—depends on users trusting the analysis is accurate.

## Repository

**GitHub:** https://github.com/marwazihs/nuelo-spectra.git (private)
**Remote:** origin
**Branch:** master
**Latest Tag:** v0.3 (2026-02-12)

## Current Milestone: Planning Next

**Status:** v0.4 Data Visualization shipped (2026-02-15). Ready for `/gsd:new-milestone` to define v0.5.

## Current State

**Shipped:** v0.4 Data Visualization (2026-02-15)
**Status:** Planning next milestone
**Codebase:** 23,177 LOC (9,173 Python app + 2,949 Python tests + 11,055 TypeScript/TSX)
**Tech Stack:** FastAPI + PostgreSQL + LangGraph + E2B + Tavily + Plotly (backend), Next.js 16 + React 19 + TanStack + Zustand + shadcn/ui + next-themes + Plotly.js (frontend)

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

**Known limitations:**
- E2B sandboxes created per-execution (no warm pools - ~150ms cold start per query)
- Basic mobile responsiveness (functional but not optimized)
- No query safety filter in Manager Agent (PII extraction, prompt injection not blocked)
- Agent JSON responses not using Pydantic structured output (inconsistent across providers)
- No Docker deployment package yet (local development only)

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

### Active

(No active requirements - ready for `/gsd:new-milestone` to define v0.5)

### Out of Scope

- **Email verification on signup** — Let users in immediately; add verification later for security
- **Save Data Cards to Collections** — Focus on real-time analysis; saving for review is polish
- **Full Collections organization** — Basic file list sufficient; collections add complexity
- **Google OAuth authentication** — Email/password sufficient for current validation
- **PowerPoint export** — PDF export proves the concept first
- **Billing and subscription management** — Validate product-market fit before payment infrastructure
- **Credit tracking system** — No billing means no credits needed yet
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
- Frontend: Next.js 16 (React 19, TanStack Query, Zustand, shadcn/ui, next-themes)
- Agent framework: LangGraph with PostgreSQL checkpointing (AsyncPostgresSaver)
- LLM providers: Anthropic (default), OpenAI, Google, Ollama, OpenRouter
- Deployment: Docker-based (package not yet created)

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
| Tabbed file interface with per-file chat history | More intuitive than shared history | ✓ Replaced — session-centric UX shipped in v0.3 |
| Session-scoped memory (no cross-session) | Avoid context pollution, clean slate per tab | ✓ Good — users get clean analysis per session |
| Manager Agent for query routing | Reduce response time ~40%, skip code gen for simple queries | ✓ Good — MEMORY_SUFFICIENT path is significantly faster |
| Tavily over Serper.dev for web search | Serper returns URLs only; Tavily returns full page content | ✓ Good — higher quality analysis with actual content |
| Per-agent LLM configuration via YAML | Enable cost optimization and vendor flexibility | ✓ Good — agents can use different models per use case |
| PostgreSQL checkpointing for memory | Native LangGraph integration, reliable persistence | ✓ Good — AsyncPostgresSaver works with proper lifecycle |
| DB-backed password reset tokens (not JWT) | Single-use, revocable, auditable | ✓ Good — more secure than JWT-based resets |
| LLM-generated query suggestions | Dataset-specific, not hardcoded templates | ✓ Good — suggestions reflect actual data structure |
| Local file storage (defer S3) | Simpler deployment, fewer dependencies | — Pending |
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

---
*Last updated: 2026-02-15 after completing v0.4 Data Visualization milestone*
