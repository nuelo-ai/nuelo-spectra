# Project Milestones: Spectra

## v0.8.1 UI Fixes & Enhancement (Shipped: 2026-03-10)

**Delivered:** Closed UI polish gaps across app shell, Chat, Files, and Pulse Analysis — leftbar toggle visible in all workspace sub-views, nav icons aligned, Spectra logo removed from Chat/Files panels, chat rightbar toggles pinned to correct corners, Credits Used card shows actual spend, Signal View mobile-responsive with Chat bridge button, and timestamps show date+time throughout.

**Phases completed:** 53–54 (2 phases, 10 plans)

**Stats:**
- 2 phases (53–54)
- 10 plans executed
- 71 files changed (+8,274 / -567 lines)
- Timeline: 2 days (2026-03-09 → 2026-03-10)
- Git range: `565bdda` → `65f0103`

**Key accomplishments:**
- Fixed leftbar collapse toggle visibility in all Pulse workspace sub-views (Collection Detail, Signal View, Report) — SidebarTrigger added to every render state (LBAR-01)
- Corrected sidebar nav icon alignment by wrapping nav in `SidebarGroup` to restore shadcn `p-2` padding context (LBAR-02)
- Removed Spectra logo from Chat and Files panel headers; fixed Chat rightbar toggle placement to viewport right edge (CHAT-01, CHAT-02, CHAT-03, FILES-01, FILES-02)
- Wired Credits Used stat card to actual cumulative credit spend via PostgreSQL `COALESCE(SUM(credit_cost), 0.0)` aggregate subquery (PULSE-01)
- Added mobile-responsive Signal View with show/hide panel toggle and back button (PULSE-02)
- Added Chat bridge button in Signal detail linking collection files to a new Chat session in a new tab; fixed all timestamps to show date+time (PULSE-03, PULSE-04, PULSE-05)

**Requirements:** 12/12 satisfied (100%)

**Git range:** `565bdda` → `65f0103`

---

## v0.8 Spectra Pulse (Detection) (Shipped: 2026-03-10)

**Delivered:** Full Pulse Analysis module — users can create Collections, attach CSV/Excel files, run AI-powered Pulse detection, and view severity-sorted Signals with Plotly chart visualizations and statistical evidence. Establishes the Detect foundation of the Detect → Explain → What-If pipeline.

**Phases completed:** 47–52.1 (8 phases, 20 plans)

**Stats:**
- 8 phases (47–52.1, including 2 inserted decimal phases: 51.1, 52.1)
- 20 plans executed
- 168 files changed (+23,418 / -345 lines)
- Timeline: 4 days (2026-03-06 → 2026-03-09)
- Git range: `d6fe76d` → `7b4bb19` (144 commits)

**Key accomplishments:**
- Built 5 new SQLAlchemy models (Collection, CollectionFile, Signal, Report, PulseRun) with Alembic migration, tier config (workspace_access, max_active_collections), and runtime-configurable workspace_credit_cost_pulse platform setting
- Shipped 11 collection endpoints with WorkspaceAccess tier gating (403 for non-workspace plans), file upload/profile, and report storage with Markdown download
- Built LangGraph Pulse Agent pipeline with E2B sandbox (300s timeout), Pydantic-validated Signal output (severity/chartType Literals), credit pre-check (402) + atomic deduction + automatic refund on failure
- Migrated all pulse-mockup workspace screens to main Next.js app: Hex.tech dark palette, (workspace) route group with own sidebar layout, Collection list/detail 4-tab, Detection Results split-panel with Plotly charts
- Refactored Pulse pipeline from monolith to multi-agent orchestrator pattern with Pydantic structured output on all LLM calls, inline progress banner, sonner toast on detection completion, and re-run confirmation dialog
- Delivered tier gating E2E verification across all 5 tiers, admin settings for Pulse credit cost (runtime configurable), and delete/rename collection with cascade handling and query cache invalidation

**Requirements:** 35/35 satisfied (100%)

**Git range:** `d6fe76d` → `7b4bb19`

---

## v0.7.12 Spectra Pulse Mockup (Shipped: 2026-03-05)

**Delivered:** Standalone Next.js UI/UX mockup covering the full Analysis Workspace feature set — Pulse detection through Explain, What-If Scenarios, and Admin Workspace Management — as static design reference for v0.8–v0.12 implementation milestones

**Phases completed:** 42–46 (5 phases, 17 plans)

**Key accomplishments:**
- Built standalone `pulse-mockup/` Next.js app with full app shell (Sidebar, Header, credit indicator, theme toggle) and Hex.tech dark palette; 7,869 LOC TypeScript/TSX across 62 files
- Implemented Analysis Workspace with Collection list/detail, Run Detection flow with credit estimate and loading state, and Signal results page with severity-sorted signal list and chart detail panel
- Built Collections & Reports hub with four-tab Collection detail, full-page report reader with markdown typography, Chat-to-Collection modal bridge, and running credit total display
- Delivered Guided Investigation (Explain) flow: doctor-style Q&A with progress indicator, root cause summary card, investigation history list, and related signals cross-link display
- Built What-If Scenarios flow: objective selection with command-palette search, scenario cards (impact/assumptions/confidence), per-scenario refinement chat overlay, and What-If report section
- Delivered Admin Workspace Management extension: activity dashboard (line/donut/bar/funnel/stacked charts), per-user Workspace tab with credit breakdown, and Settings page with 8 editable credit cost inputs and dismissable alerts

**Stats:**
- 5 phases (42–46), 17 plans
- 91 commits, 200 files changed (+28,242 / -3,389 lines)
- 7,869 LOC TypeScript/TSX (pulse-mockup/src — 62 files)
- Timeline: 3 days (2026-03-03 → 2026-03-05)

**Requirements:** 32/34 satisfied (94%)
- Known gaps: COLL-01 (archive/unarchive status indicators), COLL-02 (collection limit usage display)

**Git range:** `cd1431c` (milestone docs start) → `6343cf8` (v0.7.12 UI polish)

---

## v0.1 Beta MVP (Shipped: 2026-02-06)

**Delivered:** AI-powered data analytics platform with natural language querying, secure code execution, and interactive data visualization

**Phases completed:** 1-6 (36 plans total)

**Key accomplishments:**

- Built complete authentication system with JWT, refresh tokens, and password reset via email
- Implemented file upload with AI-powered data profiling and multi-file management with independent chat histories
- Created 4-agent AI system (Onboarding, Coding, Code Checker, Data Analysis) with LangGraph orchestration and YAML-configurable prompts
- Integrated real-time SSE streaming showing AI thinking process with atomic chat persistence
- Deployed E2B Firecracker sandbox with multi-layer security (AST validation + microVM isolation) and intelligent retry logic
- Built Next.js frontend with interactive Data Cards, sortable tables, code display, CSV/Markdown downloads, and complete settings management

**Stats:**

- 4,433 lines of Python (backend)
- 5,578 lines of TypeScript/TSX (frontend)
- 10,011 total lines of code
- 6 phases, 36 plans executed
- 5 days from project start to beta ship (Feb 1-6, 2026)

**Git range:** `9ea2714 (Phase 5)` → `ddee5af (Phase 6 final)`

**Requirements:** 42/42 satisfied (100%)
- Authentication: 5/5 ✓
- File Management: 10/10 ✓
- AI Agents & Chat: 9/9 ✓
- Code Execution & Security: 7/7 ✓
- Interactive Data Cards: 8/8 ✓
- Settings & Profile: 3/3 ✓

**Testing:** UAT Round 6 passed (3/3 tests) - All E2E flows verified

**What's next:** v0.2 will focus on enhancing AI agents with memory persistence and additional LLM providers (Ollama and OpenRouter)

---


## v0.2 Intelligence & Integration (Shipped: 2026-02-10)

**Delivered:** Enhanced AI agent capabilities with multi-provider LLM support, conversation memory, intelligent query routing, web search integration, and production email infrastructure

**Phases completed:** 7-13 (19 plans total)

**Key accomplishments:**

- Added 5-provider LLM support (Anthropic, OpenAI, Google, Ollama, OpenRouter) with per-agent YAML configuration, fail-fast startup validation, and empty response handling for reasoning models
- Enabled multi-turn conversation memory with PostgreSQL checkpointing, tiktoken-based token counting, context usage display, and tab close warnings
- Built Manager Agent with intelligent 3-path query routing (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS) reducing response time ~40% for simple queries
- Implemented LLM-generated smart query suggestions on new chat tabs and follow-up suggestion chips on DataCards
- Integrated Tavily-powered web search tool with transparent source citations, daily per-user quota tracking, and configurable toggle
- Deployed production SMTP email service with DB-backed single-use password reset tokens, Jinja2 HTML/text templates, and startup validation

**Stats:**

- 6,574 lines of Python (app) + 2,077 lines of Python (tests)
- 6,827 lines of TypeScript/TSX (frontend)
- 15,478 total lines of code
- 7 phases, 19 plans executed
- 110 commits over 4 days (Feb 7-10, 2026)

**Git range:** `adbfed0 (feat(07-01))` → `7dab5cc (docs: todo)`

**Requirements:** 53/53 mapped (100%)
- Multi-LLM Provider: 12/12 (LLM + CONFIG)
- Session Memory: 8/8 (MEMORY)
- Manager Agent Routing: 10/10 (ROUTING)
- Smart Query Suggestions: 6/6 (SUGGEST)
- Web Search Integration: 7/7 (SEARCH)
- Production Email: 11/11 (SMTP + PWRESET)

**Testing:** UAT passed for all phases — 106 total tests (34 LLM provider + 28 routing + 44 other)

**What's next:** v0.3 will focus on visualization capabilities, advanced memory features, and production hardening

---


## v0.3 Multi-file Conversation Support (Shipped: 2026-02-12)

**Delivered:** Restructured UX from file-tab-centric to chat-session-centric, enabling multi-file conversations and cross-file analysis with ChatGPT-style navigation

**Phases completed:** 14-19 (23 plans total)

**Key accomplishments:**

- Migrated database from file-centric to session-centric architecture with ChatSession model, M2M file-session linking, and three-part Alembic migration chain preserving all v0.2 conversation history
- Built ContextAssembler service enabling cross-file analysis with progressive token budget, join hint detection, and dual-mode single/multi-file agent pipeline
- Restructured frontend to ChatGPT-style session-centric UX with Zustand session store, shadcn sidebar navigation, chronological chat history grouping, and linked files right panel
- Implemented My Files screen with TanStack Table, drag-and-drop upload, bulk operations, file download, and "Start Chat" action linking files to new sessions
- Added dark/light theme toggle (Nord palette), file requirement enforcement with dual feedback, last-file protection, and LLM-powered session title auto-generation
- Closed all 9 UAT gaps including sidebar double-click rename, drag-drop file forwarding, bulk delete UUID fix, Spectra branding placement, and sidebar auto-open on file link

**Stats:**

- 8,589 lines of Python (app) + 2,077 lines of Python (tests)
- 10,230 lines of TypeScript/TSX (frontend)
- 20,896 total lines of code
- 6 phases, 23 plans executed
- 117 commits over 3 days (Feb 10-12, 2026)
- 159 files changed (+26,349 / -3,347 lines)

**Git range:** `v0.2` → `e4b9bb1 (Phase 19 final)`

**Requirements:** 37/37 satisfied (100%)
- Chat Sessions: 9/9 (CHAT)
- File Linking: 8/8 (LINK)
- File Management: 7/7 (FILE)
- Layout & Navigation: 5/5 (NAV)
- Data Model & Backend: 6/6 (DATA)
- Appearance: 2/2 (THEME)

**Testing:** UAT 25 tests (16 initial pass + 9 gaps closed in Phase 19), all passing after gap closure

**What's next:** v0.4 will be defined via `/gsd:new-milestone`

---


## v0.4 Data Visualization (Shipped: 2026-02-15)

**Delivered:** Intelligent data visualization with AI-generated interactive Plotly charts that automatically appear when analysis benefits from visual representation

**Phases completed:** 20-25 (6 phases, 11 plans total)

**Key accomplishments:**

- Added 6th AI agent (Visualization Agent) that generates Plotly Python code with chart type selection heuristics embedded in LLM prompts
- Implemented 7 chart types (bar, line, scatter, histogram, box plot, pie, donut) with automatic chart type selection based on data shape analysis
- Built intelligent chart discretion system — Manager Agent hints visualization intent, Data Analysis Agent confirms when charts add value, conditional LangGraph routing skips visualization when not needed
- Integrated Plotly.js with interactive charts (zoom, pan, hover tooltips), responsive resizing, and theme-aware Nord palette for dark/light modes
- Added PNG/SVG chart export (1200x800 resolution) and chart type switcher for compatible types (bar ↔ line ↔ scatter) with instant client-side rendering
- Implemented non-fatal error handling — chart generation failures preserve analysis text and data table with graceful degradation and subtle user notification

**Stats:**

- 9,173 lines of Python (app) + 2,949 lines of Python (tests)
- 11,055 lines of TypeScript/TSX (frontend)
- 23,177 total lines of code
- 6 phases, 11 plans executed
- 76 files changed (+15,708 / -2,204 lines)
- 3 days development time (Feb 12-15, 2026)

**Git range:** `v0.3 (cb936bf)` → `e3cf117 (Phase 25 final)`

**Requirements:** 43/43 satisfied (100%)
- Infrastructure: 4/4 (INFRA)
- Visualization Agent: 6/6 (AGENT)
- Chart Generation: 11/11 (CHART)
- Graph Integration: 6/6 (GRAPH)
- Chart Display: 7/7 (DISPLAY)
- Export & Customization: 5/5 (EXPORT)
- Theme & Polish: 4/4 (THEME)

**Testing:** All chart types validated end-to-end, theme toggle verified in dark/light modes, export functionality tested

**What's next:** v0.5 will be defined via `/gsd:new-milestone`

---


## v0.5 Admin Portal (Shipped: 2026-02-18)

**Delivered:** Internal admin portal for platform management — user management, credit system, invitation flow, signup control, platform settings, and dashboard metrics — with split-horizon architecture and separate admin frontend

**Phases completed:** 26-32 (7 phases, 24 plans total)

**Key accomplishments:**

- Built split-horizon architecture with SPECTRA_MODE routing (public/admin/dev), mode-aware CORS, and defense-in-depth security (Tailscale + JWT + role enforcement + audit logging)
- Implemented credit system with NUMERIC(10,1) atomic deduction (SELECT FOR UPDATE), tier-based allocations from user_classes.yaml, APScheduler auto-resets, and admin manual adjustments
- Created platform settings with runtime configuration via key-value DB table (30s TTL cache), signup toggle with immediate effect, and configurable invite expiry
- Built full user management: paginated listing with search/filter/sort, activate/deactivate with token invalidation, password reset, tier change, credit adjust, and deletion with challenge codes
- Deployed email invitation system with SHA-256 hashed time-limited single-use tokens, branded email templates, revoke/resend, and invite-only registration flow
- Shipped complete admin Next.js frontend (admin-frontend/) with dashboard metrics, Recharts trend charts, credit distribution, user management, settings, invitations, and audit log pages

**Stats:**

- 7 phases, 24 plans executed
- 127 commits over 2 days (Feb 16-17, 2026)
- ~20,924 LOC across backend Python + admin-frontend TypeScript/TSX
- 5 new database tables + 2 user table fields via Alembic migration
- 1 new backend dependency (APScheduler), 1 new frontend library (Recharts)

**Git range:** `feat(26-02)` → `fix(32-01)`

**Requirements:** 82/86 satisfied (95%)
- Admin Authentication: 7/7 (AUTH)
- Admin Dashboard: 7/7 (DASH)
- User Management: 13/13 (USER)
- Signup Control: 4/4 (SIGNUP)
- User Invitation: 8/8 (INVITE)
- User Class Management: 6/7 (TIER) — TIER-02 deferred
- Credit Management: 12/13 (CREDIT) — CREDIT-11 deferred
- Platform Settings: 7/8 (SETTINGS) — SETTINGS-06 deferred
- Split-Horizon Architecture: 10/10 (ARCH)
- Database Changes: 9/9 (DB)

### Known Gaps

- **CREDIT-11**: Bulk-adjust credits by user class — deferred (admin adjusts individually for now)
- **SETTINGS-06**: Per-tier credit overrides in platform_settings — deferred (YAML defaults sufficient)
- **TIER-02**: Admin editing tier credit amounts via UI — deferred (requires SETTINGS-06)

**Testing:** UAT v1 (16 issues found, all fixed in gap closure) + UAT v2 (19 tests, 18 passed, 1 inline fix) + Phase 32 production readiness closure

**What's next:** v0.6 will be defined via `/gsd:new-milestone`

---


## v0.6 Docker and Dokploy Support (Shipped: 2026-02-21)

**Delivered:** Full production deployment package — Docker Compose for local dev, Dockerfiles for all 3 services, 4 Dokploy services with Tailscale split-horizon architecture, fail-fast startup validation, automatic admin seeding, and DEPLOYMENT.md guide

**Phases completed:** 33-37 (5 phases, 10 plans)

**Key accomplishments:**

- Built production Dockerfiles for all 3 services (backend multi-stage uv, frontend/admin standalone Next.js) with .dockerignore and non-root users
- Created docker-entrypoint.sh with PostgreSQL readiness wait, Alembic migrations on startup, and uvicorn as PID 1
- Shipped Docker Compose for local full-stack development with health-ordered startup and named volumes
- Deployed 4 Dokploy Application services with Tailscale split-horizon architecture (public HTTPS, admin VPN-only)
- Added fail-fast startup validation requiring ADMIN_EMAIL/ADMIN_PASSWORD in dev/admin modes with automatic admin seeding
- Created DEPLOYMENT.md step-by-step guide for Dokploy + Tailscale deployment

**Stats:**

- 5 phases, 10 plans executed
- 3 days development time (Feb 19-21, 2026)

**Git range:** `v0.5` → `v0.6`

**Requirements:** 28/28 satisfied (100%)

**What's next:** v0.7 API Services & MCP

---


## v0.7 API Services & MCP (Shipped: 2026-02-25)

**Delivered:** Public REST API and MCP server exposing Spectra's data analysis capabilities for programmatic access and AI agent integrations, with API key management, credit deduction, and usage logging

**Phases completed:** 38-41 (4 phases, 15 plans)

**Key accomplishments:**

- Built API key infrastructure with SHA-256 hashing, `spe_` prefix format, user self-service management, and admin key management for all users
- Shipped public REST API v1 with file management (upload, list, download, delete), file context (get/update, suggestions), and synchronous query endpoint
- Implemented credit deduction and API usage logging on all `/v1/` requests with structured request/error logging and credit refund on failure
- Added `SPECTRA_MODE=api` as 5th deployment mode with its own CORS config, deployable as standalone Dokploy service
- Created MCP server with 6 curated `spectra_` tools via FastMCP 3.0.2, mounted at `/mcp/` with Streamable HTTP transport
- Implemented Bearer token auth middleware for MCP with per-request validation on both tool calls and tool listing

**Stats:**

- 4 phases, 15 plans executed
- 88 commits over 4 days (Feb 21-24, 2026)
- 129 files changed (+14,703 / -3,002 lines)

**Git range:** `v0.6` → `v0.7`

**Requirements:** 30/30 satisfied (100%)
- API Key Management: 8/8 (APIKEY)
- API Authentication & Security: 4/4 (APISEC)
- API Files: 4/4 (APIF)
- API File Context: 3/3 (APIC)
- API Chat/Query: 1/1 (APIQ)
- API Infrastructure: 5/5 (APIINFRA)
- MCP Server: 5/5 (MCP)

**Testing:** UAT passed for all phases — Phase 39 (8 tests, 2 rounds with gap closure), Phase 40 (11 tests, 2 rounds with gap closure), Phase 41 (6 tests, 1 bug fixed during UAT)

**Post-ship patches:**

| Version | Date | Summary |
|---------|------|---------|
| v0.7.4 | 2026-02-20 | MCP server initial implementation |
| v0.7.5 | 2026-02-20 | Fix /health/llm, /v1/keys SPECTRA_MODE=api, hardcoded version |
| v0.7.6 | 2026-02-25 | MCP auth fix (await set_state/get_state) + loopback URL fix |
| v0.7.7 | 2026-02-25 | MCP spectra_run_analysis: add execution_result as markdown data table |
| v0.7.8 | 2026-02-25 | MCP: decode Plotly binary typed arrays in chart spec; API_MCP_REFERENCE.md |
| v0.7.9 | 2026-02-25 | Admin users activity tab: fix backend GroupingError 500 + silent error swallowing |
| v0.7.10 | 2026-02-27 | Admin credit usage display: add API query counts to activity/sessions tabs + credit transaction source attribution |

**Final production state:** v0.7.10 (2026-02-27)

**What's next:** v0.8 will be defined via `/gsd:new-milestone`

---

