# Spectra

## What This Is

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. Users upload datasets (Excel/CSV), ask questions in natural language through a conversational chat interface, and receive instant insights, visualizations, and exportable reports presented as interactive Data Cards. The platform makes data analysis accessible to anyone, regardless of technical expertise, by combining intuitive file management with AI-driven Python code generation executed in a secure sandbox.

## Core Value

Accurate data analysis. The AI must generate correct, safe Python code that produces reliable results. If the code is wrong or the sandbox isn't secure, the entire product fails. Everything else—polish, features, exports—depends on users trusting the analysis is accurate.

## Current State

**Shipped:** v0.1 Beta MVP (2026-02-06)
**Status:** Production-ready beta release
**Codebase:** 10,011 LOC (4,433 Python, 5,578 TypeScript/TSX)
**Tech Stack:** FastAPI + PostgreSQL + LangChain + E2B (backend), Next.js 16 + React 19 + TanStack + shadcn/ui (frontend)

**What works:**
- ✅ Complete authentication system with JWT and refresh tokens
- ✅ File upload with AI-powered data profiling (Excel/CSV up to 50MB)
- ✅ Multi-file management with tabbed interface and independent chat histories
- ✅ 4-agent AI system generating validated Python code in E2B sandbox
- ✅ Real-time SSE streaming showing AI thinking process
- ✅ Interactive Data Cards with sortable tables and CSV/Markdown exports
- ✅ Settings page with profile editing and password change

**Known limitations:**
- PostgreSQL checkpointing temporarily disabled (each query starts fresh - no conversation memory across queries)
- E2B sandboxes created per-execution (no warm pools - ~150ms cold start per query)
- Basic mobile responsiveness (functional but not optimized)

**Next milestone goals:** UI/UX polish, additional export features (PDF, collections), performance optimizations, conversation memory

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

**Total: 42/42 requirements satisfied (100%)**

### Active

(None — define requirements for next milestone using `/gsd:new-milestone`)

**Chat with Data:**
- [ ] User can ask questions about their data in natural language
- [ ] System streams AI responses in real-time (show thinking process)
- [ ] Coding Agent generates Python scripts based on user queries
- [ ] Code Checker Agent validates generated code for safety and correctness
- [ ] Python code executes in secure sandbox environment
- [ ] Data Analysis Agent interprets results and generates explanations

**Interactive Data Cards:**
- [ ] Results display as Data Cards with streaming responses
- [ ] Data Cards show: Query Brief, Data Table, AI Explanation
- [ ] Data tables are sortable and filterable
- [ ] Visual polish: smooth animations, loading states, transitions

**Settings:**
- [ ] User can view and edit profile (first name, last name)
- [ ] User can view account details (email, creation date)
- [ ] User can change password

### Out of Scope

- **Email verification on signup** — Deferred to v2. Let users in immediately; add verification later for security.
- **Save Data Cards to Collections** — Deferred to v2. Focus on real-time analysis first; saving for later review is polish.
- **CSV/PDF export from Data Cards** — Deferred to v2. View results in-app for v1; export proves less critical than analysis accuracy.
- **Full Collections organization** — Deferred to v2. Basic file list sufficient for v1; organizing into collections adds complexity.
- **Bulk file download** — Deferred to v2. Users can delete individual files; bulk operations not essential for MVP.
- **Google OAuth authentication** — Deferred to v2. Email/password sufficient for MVP validation.
- **Visualization Agent** — Deferred to v2. Focus on accurate analysis first; charts can come later.
- **PowerPoint export** — Deferred to v2. PDF export (also deferred) proves the concept; PowerPoint adds significant complexity.
- **Billing and subscription management** — Deferred to v2. Need to validate product-market fit before building payment infrastructure.
- **Credit tracking system** — Deferred to v2. No billing means no credits needed yet.
- **S3/cloud file storage** — Deferred to v2. Local storage sufficient for MVP; cloud storage adds deployment complexity.
- **Real-time collaboration** — Not planned. Single-user experience for v1.
- **Mobile native apps** — Not planned. Web-responsive design only.
- **Data source integrations (APIs, databases)** — Not planned. File upload only for v1.

## Context

**Target market:** Commercial SaaS product. Planning to offer subscriptions to customers who need accessible data analysis tools without coding skills.

**User experience priority:** The platform's success depends on making data analysis feel natural and accessible. Interactive UI, especially streaming responses and polished Data Cards, is critical. Users should see the AI "thinking" (generating code in real-time) and interact fluidly with results (sort, filter, explore).

**AI Agent architecture:** Multiple specialized agents work together:
- **Onboarding Agent:** Analyzes uploaded data structure, generates metadata, suggests initial analyses
- **Coding Agent:** Generates Python code from natural language queries
- **Code Checker Agent:** Validates code for security (no risky operations like file deletion, drop tables) and correctness (enforces deterministic execution, avoids infinite loops)
- **Data Analysis Agent:** Interprets code execution results and generates natural language explanations

**Security considerations:**
- Sandbox must prevent risky operations (file deletion, table drops, network access)
- Code execution must be deterministic (no infinite loops, time limits)
- User data must be isolated (segregated by user in file storage)
- Agent execution must be traceable (consider LangSmith for debugging)

**Technical ecosystem:**
- Backend: Python ecosystem (FastAPI, LangChain, pandas)
- Frontend: Next.js (chosen for streaming support, modern DX)
- Agent framework: LangChain provides structured AI agent patterns
- Deployment: Docker-based, considering separate containers for frontend, backend, and AI agent engine

## Constraints

- **Timeline:** Aggressive (2-4 weeks). Need to ship MVP quickly to validate concept. Scope must remain ruthlessly focused on core workflow.
- **Team:** Single developer. Architecture must be simple enough for one person to build and maintain. Avoid over-engineering.
- **Budget:** Limited. Minimize LLM API calls during development. Choose efficient models where possible.
- **Tech stack:** Python backend (LangChain + FastAPI), Next.js frontend, PostgreSQL database, local file storage. These are locked in based on existing requirements and ecosystem expertise.
- **Security:** Code execution sandbox is non-negotiable. Generated Python code runs user-uploaded data; must prevent malicious or accidental damage.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js for frontend | Supports streaming AI responses natively, modern full-stack framework, handles SSR and API routes | — Pending |
| 4 AI agents for v1 (skip Visualization) | Timeline constraint. Onboarding, Coding, Code Checker, Data Analysis are core to accuracy. Visualization can be added later. | — Pending |
| Email auth only (defer Google OAuth) | Reduces complexity, faster to ship. OAuth is polish, not core value. | — Pending |
| Skip email verification for v1 | Let users in immediately after signup. Verification adds friction and complexity not needed to validate core value. | — Pending |
| Tabbed file interface with per-file chat history | Each file gets its own chat tab. More intuitive than single shared history, validates multi-file workflow without full Collections. | — Pending |
| Basic file management (no Collections) | File list with metadata (name, size, date), delete, and tabs. Proves file handling without collection organization complexity. | — Pending |
| Skip export features for v1 | No CSV/PDF export, no saved Data Cards. Focus on real-time analysis accuracy first; export is polish for later. | — Pending |
| Skip billing for v1 | Need product validation before building payment infrastructure. Avoids Stripe integration, credit tracking, subscription logic. | — Pending |
| Local file storage (defer S3) | Simpler deployment, fewer dependencies. S3 adds cost and configuration complexity not needed for MVP. | — Pending |
| Explore AG-UI for Data Cards | Mentioned in architecture requirements for dynamic AI-generated components. Worth researching but not a hard requirement—any solution achieving interactive, polished Data Cards works. | — Pending |

---
*Last updated: 2026-02-06 after v0.1 Beta MVP milestone completion*
