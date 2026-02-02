# Spectra

## What This Is

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. Users upload datasets (Excel/CSV), ask questions in natural language through a conversational chat interface, and receive instant insights, visualizations, and exportable reports presented as interactive Data Cards. The platform makes data analysis accessible to anyone, regardless of technical expertise, by combining intuitive file management with AI-driven Python code generation executed in a secure sandbox.

## Core Value

Accurate data analysis. The AI must generate correct, safe Python code that produces reliable results. If the code is wrong or the sandbox isn't secure, the entire product fails. Everything else—polish, features, exports—depends on users trusting the analysis is accurate.

## Current Milestone: v1.0 MVP

**Goal:** Ship minimum viable product that proves the core value—users can upload data, ask questions, and get accurate AI-powered analysis.

**Target features:**
- Authentication (signup, login, password reset, session persistence)
- File upload with AI interpretation (Onboarding Agent)
- Tabbed file management (upload multiple files, switch between them, per-file chat history)
- Chat with data (4 AI agents: Onboarding, Coding, Code Checker, Data Analysis)
- Interactive Data Cards (streaming responses, sortable tables, visual polish)
- Basic settings (profile editing, password change)

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Authentication:**
- [ ] User can sign up with email and password
- [ ] User can log in with email and password
- [ ] User can reset password via email link
- [ ] User session persists across browser refresh

**File Upload & AI Interpretation:**
- [ ] User can upload Excel (.xlsx, .xls) and CSV files up to 50MB
- [ ] System validates file format and structure
- [ ] AI Onboarding Agent analyzes data structure and generates natural language summary
- [ ] User can provide optional context to improve AI interpretation
- [ ] User can refine AI's understanding of the data

**File Management:**
- [ ] User can view list of uploaded files with metadata (name, size, upload date)
- [ ] User can delete files with confirmation dialog
- [ ] Each file has its own chat tab
- [ ] User can switch between file tabs
- [ ] Chat history persists per file
- [ ] Current active file is clearly displayed

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
*Last updated: 2026-02-02 after v1.0 milestone scoping*
