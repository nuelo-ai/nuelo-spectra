# Technology Stack Research

**Project:** Spectra - AI-powered data analytics platform
**Domain:** AI agent orchestration + data analysis SaaS
**Researched:** 2026-02-02
**Confidence:** HIGH

## Executive Summary

This stack recommendation prioritizes **single-developer maintainability**, **2-4 week timeline feasibility**, and **security for AI-generated code execution**. Key decisions: async-first FastAPI with modern tooling (uvicorn workers, Pydantic v2), LangGraph over vanilla LangChain for agent orchestration, E2B for production-grade code sandboxing, and Next.js 16 with streaming via server-sent events.

**Critical finding:** Python-level sandboxing (RestrictedPython) is fundamentally insecure for 2026. Production code execution requires OS-level isolation (E2B microVMs, Docker containers, or gVisor).

---

## Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **FastAPI** | 0.115+ | Backend API framework | Async-first ASGI, native Pydantic v2 integration, excellent performance (5-10x faster than Flask), built-in OpenAPI docs, ideal for AI streaming responses. Dominant choice for Python AI/ML APIs in 2026. |
| **Next.js** | 16.x | Frontend framework | React 19 compatible, built-in SSR/streaming support, App Router for server components, excellent DX for single developer. Native streaming makes AI response rendering trivial. |
| **PostgreSQL** | 16.x | Primary database | Industry-standard relational DB, excellent JSON support for chat history, robust transaction support, works seamlessly with async SQLAlchemy 2.0. |
| **LangGraph** | 0.2.65+ | AI agent orchestration | **Recommended over LangChain agents**. Graph-based architecture supports loops/branching (needed for Code Checker retries), explicit state management (critical for multi-agent coordination), production-ready with rollback/backtracking. LangChain is fine for prototypes but LangGraph scales better for 4-agent system. |
| **E2B** | 1.0+ | Code execution sandbox | **Production-grade microVM isolation** using Firecracker (~150ms boot). Purpose-built for AI-generated code. Alternatives like RestrictedPython are fundamentally insecure (too many escape vectors via Python introspection). E2B provides the security guarantees this product requires. |
| **Python** | 3.12+ | Backend language | Latest stable, excellent async support, required for FastAPI/LangGraph ecosystem. 3.13 is available but 3.12 has better library compatibility as of Feb 2026. |
| **TypeScript** | 5.6+ | Frontend language | Type safety critical for AI streaming interfaces, reduces bugs in single-developer context, excellent Next.js integration. |

---

## Backend Stack

### API Layer

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **fastapi** | 0.115+ | Web framework | Always. Core framework. |
| **uvicorn[standard]** | 0.34+ | ASGI server | Always. Production server with `--workers` for multi-process. Replaces older Gunicorn+Uvicorn pattern—uvicorn now has built-in process manager. |
| **pydantic** | 2.10+ | Data validation | Always. FastAPI native integration. v2 offers 5-17x performance improvement over v1. |
| **pydantic-settings** | 2.7+ | Environment config | Always. Clean `.env` management without hardcoding. |

### Database & ORM

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **sqlalchemy[asyncio]** | 2.0.36+ | ORM | Always. **Use SQLAlchemy 2.0 style** (not 1.x legacy). Async-first for FastAPI. |
| **asyncpg** | 0.30+ | PostgreSQL driver | Always. Async driver for SQLAlchemy. Much faster than psycopg2. |
| **alembic** | 1.14+ | Database migrations | Always. Never use `Base.metadata.create_all()`—Alembic maintains migration history. |

**Critical setup note:** Configure Alembic to read `DATABASE_URL` from environment variables, not hardcoded in `alembic.ini`. See [TestDriven.io async SQLAlchemy guide](https://testdriven.io/blog/fastapi-sqlmodel/).

### AI Agent Framework

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **langgraph** | 0.2.65+ | Agent orchestration | **Primary agent framework**. Use for Coding, Code Checker, Onboarding, Data Analysis agents. Graph structure handles retry loops (Code Checker validates → fails → Coding regenerates). |
| **langchain** | 0.3.20+ | LLM utilities | Supporting library. LangGraph builds on LangChain core. Use for prompt templates, output parsers, base abstractions. |
| **langchain-openai** | 0.2.14+ | OpenAI integration | Always (primary LLM provider). Handles ChatGPT API calls for all 4 agents. |
| **langsmith** | 0.2+ | Tracing/debugging | **Strongly recommended for development**. Agent debugging without LangSmith is painful. New 2026 features: Polly (AI assistant for trace analysis), LangSmith Fetch (CLI tool pulls traces into terminal for Claude/Cursor debugging). Set `LANGCHAIN_TRACING_V2=true` env var. |

**LangGraph vs LangChain decision:** LangChain agents work for linear workflows, but this project needs:
- **Loops:** Code Checker → Coding Agent retry cycles
- **State persistence:** Track which file user is analyzing, chat history per file
- **Multi-agent coordination:** 4 agents sharing context

LangGraph provides these natively. See [LangChain vs LangGraph 2026 comparison](https://langchain-tutorials.github.io/langgraph-vs-langchain-2026/).

### Code Execution Sandbox

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **e2b** | 1.0+ | Secure Python sandbox | **Always. Non-negotiable.** Executes AI-generated pandas/matplotlib code in isolated Firecracker microVMs. Alternative approaches (RestrictedPython, codejail) are insufficient—Python-level sandboxing has too many escape vectors. |

**Why not alternatives:**
- **RestrictedPython:** Abandoned approach. Python Wiki warns: "Too many ways to escape using introspection features." Not secure for 2026. See [RestrictedPython documentation](https://restrictedpython.readthedocs.io/).
- **Docker containers:** Viable but slower (~1-2s boot vs E2B's 150ms). Adds deployment complexity for single developer.
- **Modal/Replicate:** Good but overkill for MVP. E2B pricing ($0.05/hour per sandbox) is reasonable for v1.0.

**E2B setup:** Install `e2b` SDK, configure API key, use Python sandbox template. See [E2B documentation](https://e2b.dev/docs) and [Northflank AI sandbox comparison](https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents).

### Data Processing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pandas** | 2.2+ | Data analysis | Always. Industry standard, users expect pandas syntax in generated code. |
| **openpyxl** | 3.1+ | Excel file parsing | Always. Reads/writes .xlsx files. Pandas uses openpyxl backend. |
| **xlrd** | 2.0+ | Legacy Excel support | If supporting .xls (Excel 97-2003). Openpyxl only handles .xlsx. |

**Polars consideration:** Polars is 5-10x faster than pandas and uses less memory. However:
- **Deferred to v2.0.** Pandas is the expected interface for data users. Generated code using Polars syntax would confuse users.
- **Future optimization:** Consider Polars for internal processing (e.g., Onboarding Agent analyzing file structure) while generating pandas code for user-facing results.

See [Polars vs Pandas 2026 performance comparison](https://www.linkedin.com/pulse/reading-xlsx-files-quickly-python-amged-elsheikh-su7ic).

### File Upload & Storage

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **python-multipart** | 0.0.20+ | Multipart form parsing | Always. Required for `File` uploads in FastAPI. |
| **aiofiles** | 24.1+ | Async file I/O | Always. Async file operations prevent blocking during upload/save. |

**Storage for v1.0:** Local filesystem (`./uploads/{user_id}/`). S3/cloud storage deferred to v2.0 (adds deployment complexity).

### Authentication & Security

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pwdlib** | 0.2+ | Password hashing | **Always. Replaces deprecated passlib.** FastAPI docs updated to use pwdlib. Supports Argon2, scrypt, bcrypt. Recommendation: `PasswordHash.recommended()` uses Argon2 (more secure than bcrypt, no 72-char password limit). |
| **PyJWT** | 2.10+ | JWT tokens | **Always. Replaces abandoned python-jose.** FastAPI docs now recommend PyJWT. Actively maintained, lightweight, focused API. |
| **python-dotenv** | 1.0+ | Environment variables | Always. Load `.env` for local development. |

**Security updates (critical):**
- **passlib is dead.** Last release 3 years ago, throws deprecation errors on Python 3.11+ (crypt module removed). Use **pwdlib** instead. See [FastAPI discussion #11773](https://github.com/fastapi/fastapi/discussions/11773).
- **python-jose is abandoned.** Use **PyJWT** as drop-in replacement. See [FastAPI PR #11589](https://github.com/fastapi/fastapi/pull/11589).

### Email (Password Reset)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **resend** | 2.8+ | Email sending | **Recommended.** Modern API, generous free tier (3,000 emails/month), native FastAPI examples. Simpler than SendGrid for single developer. |

**Alternative:** SendGrid (more established, higher free tier limits but more complex setup). Resend has cleaner DX. See [Resend FastAPI docs](https://resend.com/fastapi).

### API Communication & Streaming

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **sse-starlette** | 2.2+ | Server-sent events | **Always for AI streaming.** Production-ready SSE for FastAPI. Handles client disconnect detection, graceful shutdown, thread safety. Released Jan 2026 with W3C SSE spec compliance. |
| **httpx** | 0.28+ | HTTP client | If making external API calls (e.g., to E2B API, OpenAI directly). Async support. |

**Why SSE over WebSockets:** SSE is unidirectional (server → client), simpler than WebSockets for AI streaming use case. No need for bidirectional communication. See [sse-starlette PyPI](https://pypi.org/project/sse-starlette/).

### Testing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | 8.3+ | Test framework | Always. |
| **pytest-asyncio** | 0.25+ | Async test support | Always (FastAPI is async). Set `asyncio_default_fixture_loop_scope = "function"` in `pyproject.toml` for test isolation. |
| **httpx** | 0.28+ | Test client | Always. FastAPI recommends `AsyncClient` from httpx for async tests (replaces `TestClient`). |

See [FastAPI async testing docs](https://fastapi.tiangolo.com/advanced/async-tests/).

---

## Frontend Stack

### Core Framework

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **next** | 16.x | React framework | Always. App Router (not Pages Router). React 19 compatible. |
| **react** | 19.x | UI library | Always. Required by Next.js 16. |
| **react-dom** | 19.x | React renderer | Always. |
| **typescript** | 5.6+ | Type system | Always. |

### State Management & Data Fetching

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **@tanstack/react-query** | 5.62+ | Server state management | **Strongly recommended.** Handles API caching, background refetch, optimistic updates. Let React Query manage client cache while Next.js handles server cache. Reduces redundant network requests by ~70%. See [Next.js 16 + React Query guide](https://medium.com/@bendesai5703/next-js-16-react-query-the-ultimate-guide-to-modern-data-fetching-caching-performance-ac13a62d727d). |
| **zustand** | 5.0+ | Client state | For UI state (sidebar open/closed, active file tab). Lightweight (1.5kb), simpler than Redux for single developer. |

**React Query rationale:** Eliminates boilerplate for loading states, error handling, refetching. Critical for chat interface where messages update frequently.

### AI Streaming & Real-time

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **ai** (Vercel AI SDK) | 4.1+ | AI streaming utilities | **Recommended for OpenAI streaming.** Provides `useChat` hook for streaming chat UIs. Handles SSE connection, message buffering, error recovery. **Caveat:** Requires Edge runtime (not Node.js). If this conflicts with other requirements, use raw SSE with `EventSource` API instead. |

**Alternative approach (more control):** Use browser's native `EventSource` API to consume SSE from FastAPI's `sse-starlette`. Vercel AI SDK is convenient but adds Edge runtime constraint.

See [Vercel AI SDK vs OpenAI SDK comparison](https://strapi.io/blog/openai-sdk-vs-vercel-ai-sdk-comparison).

### UI Components

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **shadcn/ui** | latest | Component library | **Strongly recommended.** Copy-paste components (not npm dependency), full ownership, Tailwind v4 compatible, React 19 ready. Perfect for single developer—no fighting with component library abstractions. |
| **tailwindcss** | 4.1+ | CSS framework | Always. Tailwind v4 released late 2025, shadcn/ui updated for compatibility. Faster build, OKLCH colors. |
| **tw-animate-css** | latest | Animations | shadcn/ui now uses this (replaces deprecated tailwindcss-animate). |
| **lucide-react** | 0.468+ | Icons | shadcn/ui uses Lucide. Clean, consistent icon set. |

**shadcn/ui rationale:** Not a traditional component library—you copy components into your project. Means you can modify without ejecting, perfect for polishing Data Cards UI. See [shadcn/ui Next.js docs](https://ui.shadcn.com/docs/installation/next).

### Forms & Validation

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **react-hook-form** | 7.54+ | Form management | Always. Used by shadcn/ui forms. Minimal re-renders, excellent DX. |
| **zod** | 3.24+ | Schema validation | Always. TypeScript-first validation, integrates with react-hook-form and Pydantic (backend). Shared validation schemas possible. |

### Data Visualization (Future)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **recharts** | 2.15+ | Charts | **Deferred to v2.0** (Visualization Agent not in v1.0). When added, Recharts is simpler than D3.js for standard charts. |

---

## Development Tools

| Tool | Purpose | Configuration Notes |
|------|---------|---------------------|
| **uv** | Python package manager | **Recommended over pip/poetry for 2026.** FastAPI team now recommends uv for reproducible builds. Uses `pyproject.toml` + `uv.lock`. Faster than pip, simpler than poetry. See [uv-based FastAPI setup](https://blog.devops.dev/a-scalable-approach-to-fastapi-projects-with-postgresql-alembic-pytest-and-docker-using-uv-78ebf6f7fb9a). |
| **npm** | Node package manager | Standard for Next.js. Use `package-lock.json` for reproducibility. |
| **Docker** | Containerization | **Critical for production.** Multi-stage builds for frontend + backend. Separate containers: `frontend`, `backend`, `postgres`. Use `python:3.12-slim` base for smaller attack surface. See [FastAPI Docker best practices](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/). |
| **docker-compose** | Multi-container orchestration | Development environment. Define `frontend`, `backend`, `db`, `redis` (if added later) services. |
| **ruff** | Python linter/formatter | Replaces flake8 + black. 10-100x faster, single tool. Configure in `pyproject.toml`. |
| **prettier** | TypeScript/JSX formatter | Enforces consistent frontend code style. |
| **eslint** | TypeScript linter | Use Next.js ESLint config (`next/core-web-vitals`). |

**Docker note:** Container adoption hit 92% in 2025 (up from 80% in 2024). Containerization is table stakes for 2026 deployment. See [Docker Python trends 2026](https://www.programming-helper.com/tech/docker-containers-2026-python-containerization-cloud-native).

---

## Installation

### Backend (Python)

```bash
# Install uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with uv
uv init backend
cd backend

# Core dependencies
uv add "fastapi[standard]>=0.115" \
       "uvicorn[standard]>=0.34" \
       "pydantic>=2.10" \
       "pydantic-settings>=2.7" \
       "sqlalchemy[asyncio]>=2.0.36" \
       "asyncpg>=0.30" \
       "alembic>=1.14" \
       "langgraph>=0.2.65" \
       "langchain>=0.3.20" \
       "langchain-openai>=0.2.14" \
       "langsmith>=0.2" \
       "e2b>=1.0" \
       "pandas>=2.2" \
       "openpyxl>=3.1" \
       "python-multipart>=0.0.20" \
       "aiofiles>=24.1" \
       "pwdlib>=0.2" \
       "PyJWT>=2.10" \
       "python-dotenv>=1.0" \
       "resend>=2.8" \
       "sse-starlette>=2.2" \
       "httpx>=0.28"

# Dev dependencies
uv add --dev "pytest>=8.3" \
             "pytest-asyncio>=0.25" \
             "ruff>=0.8"
```

### Frontend (Node.js)

```bash
# Create Next.js app with TypeScript
npx create-next-app@latest frontend --typescript --tailwind --app --use-npm

cd frontend

# Core dependencies
npm install @tanstack/react-query@5.62 \
            zustand@5.0 \
            ai@4.1 \
            react-hook-form@7.54 \
            zod@3.24 \
            lucide-react@0.468

# shadcn/ui (interactive CLI)
npx shadcn@latest init

# Add shadcn components as needed
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add table
# ... etc

# Dev dependencies (if not already installed by create-next-app)
npm install -D prettier eslint
```

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| **Backend framework** | FastAPI | Flask | Never for this project. Flask is synchronous, poor for AI streaming. FastAPI is async-first. |
| **Backend framework** | FastAPI | Django | Only if you need Django admin UI or complex auth. Overkill for API-only backend. FastAPI is 5-10x faster. |
| **Agent framework** | LangGraph | LangChain (vanilla) | Only for simple linear workflows. This project needs loops/branching—LangGraph is better fit. |
| **Code sandbox** | E2B | RestrictedPython | Never. RestrictedPython is fundamentally insecure (too many Python escape vectors). |
| **Code sandbox** | E2B | Docker containers | If you need more control or have existing Docker expertise. Slower boot times (~1-2s vs 150ms). |
| **Code sandbox** | E2B | Modal/Replicate | If scaling beyond thousands of concurrent users. Overkill for MVP. |
| **Frontend framework** | Next.js | Create React App | Never. CRA is unmaintained as of 2023. React docs recommend Next.js. |
| **Frontend framework** | Next.js | Remix | If you prefer nested routing and simpler mental model. Next.js has better AI SDK ecosystem in 2026. |
| **Password hashing** | pwdlib (Argon2) | bcrypt | Only if you have legacy bcrypt hashes to support. Argon2 is more secure (no 72-char limit). |
| **JWT library** | PyJWT | python-jose | Never. python-jose is abandoned (last release 3 years ago). PyJWT is drop-in replacement. |
| **Email service** | Resend | SendGrid | If you need >3,000 emails/month free tier. SendGrid has higher limits but more complex setup. |
| **Data processing** | pandas | Polars | Consider for v2.0 internal processing. For user-facing code generation, pandas is expected standard. |
| **UI components** | shadcn/ui | Material UI | If you need pre-built complex components (data grids, date pickers). shadcn/ui gives more control. |
| **UI components** | shadcn/ui | Ant Design | Same as Material UI. shadcn/ui is better for custom designs. |
| **State management** | TanStack Query + zustand | Redux Toolkit | Only if you have existing Redux expertise. Zustand is simpler for single developer. |
| **Package manager (Python)** | uv | poetry | If you need advanced dependency resolution. uv is faster, simpler for most cases. |
| **Package manager (Python)** | uv | pip | If you're working with very simple projects. uv provides reproducibility via lock file. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **passlib** | Abandoned. Last release 3 years ago. Throws deprecation errors on Python 3.11+ (crypt module removed in 3.13). FastAPI docs updated away from it. | **pwdlib** with Argon2 algorithm |
| **python-jose** | Abandoned. Barely maintained, last release ~3 years ago. Less secure than PyJWT. FastAPI docs now recommend PyJWT. | **PyJWT** (drop-in replacement) |
| **RestrictedPython** | Fundamentally insecure. Python Wiki warns: "Too many ways to escape via introspection." Not viable for production code execution in 2026. | **E2B** (microVM isolation) |
| **Gunicorn + Uvicorn** | Outdated pattern. Uvicorn now has built-in `--workers` multi-process support (since ~v0.30). Gunicorn adds unnecessary complexity. | **uvicorn --workers 4** |
| **SQLAlchemy 1.x style** | Legacy. Use 2.0 style with async. 1.x patterns still work but miss performance benefits and future deprecation. | **SQLAlchemy 2.0** with asyncpg |
| **Pydantic v1** | Superseded. v2 is 5-17x faster. FastAPI 0.119+ supports gradual migration but new projects should start with v2. | **Pydantic v2** |
| **Create React App** | Unmaintained since 2023. React docs no longer recommend it. | **Next.js** or Vite |
| **tailwindcss-animate** | Deprecated as of Tailwind v4. shadcn/ui migrated away from it. | **tw-animate-css** |
| **Pages Router (Next.js)** | Legacy. App Router (introduced Next.js 13, stable in 14+) is the future. Better streaming, server components. | **App Router** |
| **Flask** | Synchronous framework, poor fit for AI streaming responses. FastAPI is async-first. | **FastAPI** |

---

## Version Compatibility Matrix

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.115+ | Pydantic 2.10+ | FastAPI 0.115+ requires Pydantic v2. Migration guide available for v1 apps. |
| Next.js 16.x | React 19.x | Next.js 16 requires React 19. Breaking change from 15.x (React 18). |
| shadcn/ui (latest) | Tailwind v4.1+, React 19+ | Updated Feb 2026 for Tailwind v4 and React 19 compatibility. |
| LangGraph 0.2.65+ | LangChain 0.3.20+ | LangGraph builds on LangChain core. Both must be ≥0.2 and ≥0.3 respectively. |
| SQLAlchemy 2.0.36+ | asyncpg 0.30+ | Use asyncpg for PostgreSQL async. Don't mix with psycopg2 (sync driver). |
| pytest-asyncio 0.25+ | pytest 8.3+ | Async test support requires recent pytest versions. |
| uvicorn 0.34+ | FastAPI 0.115+ | Uvicorn bundled with FastAPI via `fastapi[standard]` or install separately. |
| pwdlib 0.2+ | Python 3.11+ | Replaces passlib. Works on 3.9+ but 3.11+ recommended (crypt module removed). |
| Vercel AI SDK 4.1+ | Next.js (Edge runtime only) | **Hard requirement:** AI SDK's StreamingTextResponse requires Edge runtime. Cannot use with Node.js runtime. |

---

## Stack Patterns by Variant

**If deploying to Vercel/Netlify (serverless):**
- Use Vercel AI SDK for streaming (Edge runtime compatible)
- Backend: Deploy FastAPI to separate service (Railway, Render, Fly.io)
- Database: Use managed PostgreSQL (Neon, Supabase, Railway)
- E2B sandbox: Use cloud-hosted (no self-hosting in serverless)

**If self-hosting (VPS, AWS EC2, etc.):**
- Backend: Docker containers with uvicorn multi-worker
- Frontend: Docker container with Next.js standalone build
- Database: PostgreSQL in Docker or managed service
- Reverse proxy: Nginx for TLS termination, static file serving
- E2B sandbox: Can self-host E2B if needed (complex, not recommended for v1.0)

**If single-machine development:**
- Use docker-compose with services: `frontend`, `backend`, `db`
- E2B: Cloud-hosted during development (free tier sufficient)
- LangSmith: Enable tracing for agent debugging
- Hot reload: `uvicorn --reload` for backend, `npm run dev` for frontend

---

## Security Considerations

### Code Execution Sandbox (Critical)

**Threat model:** AI generates Python code based on user queries. Malicious user could prompt: "Delete all my files" or "Drop the users table." AI might generate:

```python
import os
os.system('rm -rf /uploads/*')  # Catastrophic
```

**Mitigation:** E2B sandboxes run in isolated Firecracker microVMs with:
- No network access (can't exfiltrate data)
- No filesystem access outside sandbox
- Resource limits (CPU, memory, timeout)
- Syscall filtering via seccomp

**Alternative approach (not recommended for v1.0):** Code Checker Agent validates for risky operations (`os.system`, `subprocess`, `eval`, `exec`, file I/O). This is defense-in-depth but NOT sufficient alone—static analysis can't catch all exploits. OS-level isolation (E2B) is non-negotiable.

See [secure Python sandbox guide](https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents).

### Authentication & Secrets

- **Password hashing:** Use pwdlib with Argon2 (not bcrypt). Argon2 resists GPU attacks better.
- **JWT tokens:** Use PyJWT with HS256 (symmetric) for MVP. RS256 (asymmetric) if you need multiple services verifying tokens later.
- **Secret key:** Generate with `openssl rand -hex 32`. Store in `.env`, never commit.
- **Database passwords:** Use strong random passwords. Store in `.env` or container secrets.
- **API keys (OpenAI, E2B, Resend):** Environment variables only. Never hardcode.

### Docker Security

- **Run as non-root:** Add `USER appuser` to Dockerfile (after installing deps as root)
- **Minimal base image:** Use `python:3.12-slim` (not `python:3.12-full`)
- **No `.env` in image:** Pass secrets via Docker secrets or environment variables at runtime
- **Proxy headers:** If behind Nginx/Traefik, add `--proxy-headers` to uvicorn

See [FastAPI Docker security](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/).

---

## Timeline Feasibility (2-4 Weeks, Single Developer)

| Week | Focus Area | Stack Components Used |
|------|------------|----------------------|
| **Week 1** | Backend foundation + auth | FastAPI, SQLAlchemy, Alembic, PostgreSQL, PyJWT, pwdlib |
| **Week 2** | AI agents + sandbox | LangGraph, LangChain, OpenAI, E2B, LangSmith (debugging) |
| **Week 3** | Frontend + streaming | Next.js, shadcn/ui, TanStack Query, SSE integration |
| **Week 4** | Integration + polish | Full stack testing, Docker deployment, Data Card UI refinement |

**Risk factors:**
- **E2B learning curve:** If unfamiliar, budget 2-3 days for sandbox setup/testing
- **LangGraph multi-agent:** Graph design takes time. Start simple (2 agents), add Code Checker later if behind schedule
- **Next.js streaming:** SSE integration is straightforward but test early (Week 2 backend prototype)

**Scope flexibility:** If running behind, defer:
1. Password reset email (keep signup/login only)
2. Code Checker Agent (validation can be simpler for v1.0)
3. Advanced Data Card features (sortable tables → simple tables)

---

## Maintainability for Single Developer

**Positive factors (stack simplifies maintenance):**
- **FastAPI auto-docs:** OpenAPI spec at `/docs` reduces documentation burden
- **Pydantic validation:** Catches type errors at API boundary
- **TypeScript:** Prevents entire classes of frontend bugs
- **shadcn/ui:** Components in your codebase (no "magic" in node_modules)
- **LangSmith tracing:** Debugging agents without tracing is nightmare fuel
- **Docker:** Reproducible deployments, no "works on my machine"

**Potential complexity (plan mitigation):**
- **LangGraph state management:** Graph definitions can get complex. Keep state schema simple. Use LangSmith to visualize execution.
- **Async SQLAlchemy:** Mixing async/sync code causes subtle bugs. Be disciplined—all DB operations must be `async`.
- **Multi-container deployment:** Docker Compose works for dev, but production needs orchestration (Railway/Render handle this for you).

**Documentation strategy:**
- **Don't document what's standard:** FastAPI/Next.js patterns are well-documented online
- **DO document:** LangGraph graph definitions, E2B sandbox config, agent prompt templates, database schema decisions

---

## Sources

### High Confidence (Context7, Official Docs)
- [FastAPI official documentation](https://fastapi.tiangolo.com/) — Core framework features, deployment
- [Next.js 16 documentation](https://nextjs.org/docs) — App Router, React 19 compatibility
- [LangChain/LangGraph documentation](https://langchain-tutorials.github.io/langgraph-vs-langchain-2026/) — Agent framework comparison
- [E2B documentation](https://e2b.dev/docs) — Sandbox setup and API
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/) — Validation features
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/) — Async patterns
- [shadcn/ui documentation](https://ui.shadcn.com/) — Component installation
- [TanStack Query documentation](https://tanstack.com/query/latest) — React integration
- [Resend FastAPI guide](https://resend.com/fastapi) — Email integration
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) — SSE library

### Medium Confidence (WebSearch Verified with Official Sources)
- [Better Stack: Best Sandbox Runners 2026](https://betterstack.com/community/comparisons/best-sandbox-runners/) — E2B alternatives comparison
- [Northflank: Best Code Execution Sandbox for AI Agents](https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents) — Security approaches
- [TestDriven.io: FastAPI with Async SQLAlchemy](https://testdriven.io/blog/fastapi-sqlmodel/) — Database setup patterns
- [FastAPI Docker Best Practices (Better Stack)](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/) — Containerization
- [FastAPI GitHub Discussion #11773](https://github.com/fastapi/fastapi/discussions/11773) — passlib deprecation
- [FastAPI GitHub PR #11589](https://github.com/fastapi/fastapi/pull/11589) — PyJWT migration
- [Medium: FastAPI at Scale in 2026](https://medium.com/@kaushalsinh73/fastapi-at-scale-in-2026-pydantic-v2-uvloop-http-3-which-knob-moves-latency-vs-throughput-cd0a601179de) — Performance tuning
- [Strapi: OpenAI SDK vs Vercel AI SDK 2026](https://strapi.io/blog/openai-sdk-vs-vercel-ai-sdk-comparison) — AI SDK tradeoffs
- [Programming Helper: Docker Python 2026](https://www.programming-helper.com/tech/docker-containers-2026-python-containerization-cloud-native) — Container trends
- [dida.do: Secure Python Sandbox for LLM Agents](https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents) — Security architecture
- [Andrew Healey: Running Untrusted Python Code](https://healeycodes.com/running-untrusted-python-code) — Sandbox approaches
- [Polars vs Pandas Performance](https://www.linkedin.com/pulse/reading-xlsx-files-quickly-python-amged-elsheikh-su7ic) — Data processing benchmarks

---

*Stack research for: Spectra AI-powered data analytics platform*
*Researched: 2026-02-02*
*Confidence: HIGH (all critical components verified with official documentation or recent authoritative sources)*
