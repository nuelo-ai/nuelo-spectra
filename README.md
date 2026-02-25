# Spectra

AI-powered conversational data analytics platform. Create chat sessions, link multiple files, ask questions in natural language, and receive instant insights with full code transparency and cross-file analysis.

## What is Spectra?

Spectra bridges the gap between raw data and actionable insights. Upload your datasets, and a multi-agent AI system analyzes the data structure, generates Python code, executes it in a secure sandbox, and presents results as interactive Data Cards — all through a conversational chat interface.

**Key Differentiators:**
- **Code Transparency**: See and verify the Python code generated for each analysis
- **Multi-File Analysis**: Link multiple datasets to a single conversation for cross-file queries
- **Multi-Agent Accuracy**: 6 specialized AI agents ensure accurate, safe results
- **Intelligent Visualization**: AI determines when charts enhance analysis and generates interactive Plotly visualizations
- **Intelligent Routing**: Manager Agent skips code generation for simple queries (~40% faster)
- **Multi-Provider LLM**: Choose from Anthropic, OpenAI, Google, Ollama, or OpenRouter per agent
- **Production Security**: E2B Firecracker microVM isolation for safe code execution
- **Admin Portal**: Internal admin dashboard with user management, credit system, invitations, and platform settings
- **Public REST API**: Versioned API v1 for programmatic file management, context retrieval, and synchronous data analysis
- **MCP Server**: 6 curated tools for Claude Desktop, Claude Code, and any MCP-compatible AI agent
- **API Key Management**: User self-service and admin key management with SHA-256 hashing and credit tracking

## Features

- **Session Management**: ChatGPT-style UX with sidebar navigation and multi-file linking
- **Natural Language Queries**: Real-time SSE streaming with intelligent routing
- **File Upload**: CSV/Excel up to 50MB with AI-powered data profiling
- **Conversation Memory**: Multi-turn memory with PostgreSQL checkpointing
- **Data Visualization**: AI-generated Plotly charts (7 types) with export and customization
- **Interactive Results**: Sortable tables, code display, CSV/Markdown export
- **Web Search**: Tavily integration with source citations
- **Multi-LLM Support**: 6 providers with per-agent configuration
- **Authentication**: JWT with refresh tokens and secure password reset
- **Theming**: Dark/light mode with Nord palette
- **Admin Portal**: Separate admin app for user management, credits, invitations, platform settings, and audit logging
- **REST API v1**: File upload/list/download/delete, file context, synchronous query — all with Bearer token auth and credit deduction
- **MCP Server**: FastMCP 3.0.2 with Streamable HTTP transport at `/mcp/`, 6 `spectra_` tools for AI agent integrations
- **API Key Management**: Create, view, revoke keys from Settings page; admin manages keys for all users

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, Python 3.12+, PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg, APScheduler, FastMCP 3.0.2 |
| **AI/Agents** | LangGraph, LangChain, 6 agents with YAML prompts, Tavily web search |
| **LLM Providers** | Anthropic (default), OpenAI, Google, Ollama, OpenRouter |
| **Sandbox** | E2B Firecracker microVMs, AST validation, library allowlisting |
| **Frontend** | Next.js 16, React 19, TypeScript 5, TanStack Query, Zustand, shadcn/ui, next-themes, Tailwind CSS 4 |
| **Admin Frontend** | Next.js 16, React 19, TanStack Query, Zustand, shadcn/ui, Recharts |
| **Email** | aiosmtplib, Jinja2 templates, DB-backed reset tokens |

## AI Agent Architecture

Spectra uses 6 specialized agents orchestrated by LangGraph:

1. **Manager Agent** — Routes queries to optimal path: memory-only response, code modification, or fresh analysis
2. **Onboarding Agent** — Analyzes uploaded file structure, generates data summary and query suggestions
3. **Coding Agent** — Generates or modifies Python pandas code from natural language queries
4. **Code Checker Agent** — Validates code via AST analysis, checks library allowlist and unsafe operations
5. **Data Analysis Agent** — Interprets execution results, generates explanations, optionally searches web for context
6. **Visualization Agent** — Generates Plotly chart code when analysis benefits from visual representation

All agents use YAML-configured prompts and support per-agent LLM provider/model configuration.

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended) — or Python 3.12+, Node.js 18+, PostgreSQL 16+ for manual setup
- [E2B](https://e2b.dev) API key
- LLM API key (Anthropic recommended, or OpenAI/Google/Ollama/OpenRouter)

### Option 1: Docker Compose (Recommended)

Runs the full stack — PostgreSQL, backend, public frontend, and admin frontend — in a single command. No local Python, Node.js, or PostgreSQL required.

```bash
# Clone
git clone https://github.com/marwazihs/nuelo-spectra.git
cd nuelo-spectra

# Set up environment
cp .env.docker.example .env.docker
# Edit .env.docker — fill in API keys, ADMIN_EMAIL, and ADMIN_PASSWORD
```

**Required entries in `.env.docker`:**
```env
ADMIN_EMAIL=admin@yourdomain.com      # Required — backend refuses to start without this
ADMIN_PASSWORD=your-secure-password   # Required — backend refuses to start without this
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
SECRET_KEY=your-secret-key            # Generate: openssl rand -hex 32
```

```bash
# Build and start all services
docker compose up --build
```

On first start, the backend automatically runs migrations and seeds the admin user before accepting requests. No manual steps needed.

| Service | URL |
|---------|-----|
| Public app | http://localhost:3000 |
| Admin portal | http://localhost:3001 |
| API / docs | http://localhost:8000 / http://localhost:8000/docs |

**Subsequent starts** (no rebuild needed unless code changed):
```bash
docker compose up
```

**Full reset** (wipes database volume):
```bash
docker compose down -v && docker compose up --build
```

---

### Option 2: Manual Setup

Use this if you need hot-reload during active development or prefer to run services individually.

**Prerequisites:** Python 3.12+, Node.js 18+, PostgreSQL 16+

```bash
# Clone
git clone https://github.com/marwazihs/nuelo-spectra.git
cd nuelo-spectra
```

**Set up PostgreSQL:**
```bash
# macOS
brew install postgresql@16 && brew services start postgresql@16 && createdb spectra

# Ubuntu/Debian
sudo apt install postgresql-16 && sudo systemctl start postgresql
sudo -u postgres createdb spectra

# Windows (using Chocolatey)
choco install postgresql16
# After installation, create database via pgAdmin or psql
```

**Backend:**
```bash
cd backend
pip install uv && uv sync
cp .env.example .env
# Edit .env with your configuration (see Environment Variables below)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# API at http://localhost:8000, docs at http://localhost:8000/docs
```

**Frontend (new terminal):**
```bash
cd frontend
npm install && npm run dev
# App at http://localhost:3000
```

**Admin Frontend (new terminal, optional):**
```bash
cd admin-frontend
npm install && npm run dev
# Admin portal at http://localhost:3001
# Requires backend running in dev mode (SPECTRA_MODE=dev)
```

**Seed Admin Account:**
```bash
# Set ADMIN_EMAIL and ADMIN_PASSWORD in backend/.env, then:
cd backend
uv run python -m app.cli seed-admin
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

**Required:**
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g., `postgresql+asyncpg://postgres:password@localhost:5432/spectra`) |
| `SECRET_KEY` | JWT signing key — generate with `openssl rand -hex 32` |
| `ALGORITHM` | JWT algorithm (use `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (e.g., `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (e.g., `30`) |
| `FRONTEND_URL` | Frontend URL (e.g., `http://localhost:3000`) |
| `CORS_ORIGINS` | Allowed CORS origins (e.g., `["http://localhost:3000"]`) |
| `E2B_API_KEY` | E2B sandbox API key from [e2b.dev](https://e2b.dev/dashboard) |
| `ANTHROPIC_API_KEY` | Anthropic API key (default LLM provider) |
| `SPECTRA_MODE` | Router mode: `dev` (all routes), `public` (user-facing only), `admin` (admin-only). Default: `dev` |
| `ADMIN_EMAIL` | Admin account email — **required when `SPECTRA_MODE=dev` or `admin`** |
| `ADMIN_PASSWORD` | Admin account password — **required when `SPECTRA_MODE=dev` or `admin`** |

**Optional:**
| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `OLLAMA_BASE_URL` | Ollama server URL (e.g., `http://localhost:11434`) |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `TAVILY_API_KEY` | Tavily web search API key |
| `SMTP_HOST` | SMTP server (leave empty for dev mode console logging) |
| `SMTP_PORT` | SMTP port |
| `SMTP_USER` / `SMTP_PASS` | SMTP credentials |
| `LANGSMITH_API_KEY` | LangSmith tracing key |

### Upgrading from v0.6 to v0.7

```bash
# 1. Pull latest code
git pull origin master

# 2. Install new backend dependencies (adds fastmcp)
cd backend
uv sync

# 3. Run database migrations (adds api_keys and api_usage_logs tables)
uv run alembic upgrade head

# 4. Optional: Add MCP_API_BASE_URL to backend/.env (defaults to http://localhost:8000)
#    Only needed if your API service runs on a different host/port

# 5. Rebuild frontend apps (API key management UI added to Settings)
cd ../frontend && npm install
cd ../admin-frontend && npm install
```

New endpoints available:
- REST API: `http://localhost:8000/api/v1/` (requires `SPECTRA_MODE=api` or `dev`)
- MCP Server: `http://localhost:8000/mcp/` (requires `SPECTRA_MODE=api` or `dev`)

For Docker/production deployment of the API service, see `DEPLOYMENT.md`.

### Upgrading from v0.5 to v0.6

```bash
# 1. Pull latest code
git pull origin master

# 2. No new backend dependencies — run migrations (no schema changes in v0.6)
cd backend
uv run alembic upgrade head

# 3. Add new env vars to backend/.env
#    APP_VERSION=v0.6.0       (optional — displayed on settings page)
#    SPECTRA_MODE=dev          (unchanged from v0.5)

# 4. Rebuild frontend apps (standalone output enabled)
cd ../frontend && npm install
cd ../admin-frontend && npm install
```

For Docker/production deployment, see `DEPLOYMENT.md`.

### Upgrading from v0.4 to v0.5

```bash
# 1. Pull latest code
git pull origin master

# 2. Install new backend dependencies (adds APScheduler)
cd backend
uv sync

# 3. Run database migration (adds 5 new tables, backfills existing users)
uv run alembic upgrade head

# 4. Add new env vars to backend/.env
#    SPECTRA_MODE=dev          (required — controls route mounting)
#    ADMIN_EMAIL=admin@...     (optional — for seeding admin account)
#    ADMIN_PASSWORD=...        (optional — for seeding admin account)

# 5. Seed admin account (optional, requires ADMIN_EMAIL and ADMIN_PASSWORD in .env)
uv run python -m app.cli seed-admin

# 6. Install admin frontend (optional)
cd ../admin-frontend
npm install
```

The migration automatically backfills existing users with `is_admin=false`, `user_class=free`, and a credit record with free-tier default balance. No manual data changes needed.

### Verify Installation

1. Backend health: `http://localhost:8000/health`
2. LLM health: `http://localhost:8000/health/llm`
3. Open `http://localhost:3000`, sign up, upload a CSV, and ask a question
4. Admin portal (optional): `http://localhost:3001`, log in with seeded admin credentials

## Configuration

### Changing LLM Provider per Agent (Optional)

Each AI agent can use a different LLM provider and model. Edit `backend/app/config/prompts.yaml`:

```yaml
agents:
  onboarding:
    provider: anthropic              # Options: anthropic, openai, google, ollama, openrouter
    model: claude-sonnet-4-20250514  # Model name from provider
    temperature: 0.0                 # 0.0 = deterministic, 1.0 = creative

  coding:
    provider: openai
    model: gpt-4o
    temperature: 0.0

  # ... other agents ...
```

**Provider-specific models:**
- Anthropic: `claude-sonnet-4-20250514`, `claude-opus-4-20250514`, `claude-haiku-4-20250514`
- OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Google: `gemini-2.0-flash-exp`, `gemini-1.5-pro`
- Ollama: `llama3.1:70b`, `qwen2.5:72b` (requires local Ollama server)
- OpenRouter: `anthropic/claude-3.5-sonnet`, `google/gemini-2.0-flash-exp:free`

After editing, restart the backend server.

### Advanced Configuration (Optional)

**Agent Parameters** (`backend/app/config/prompts.yaml`):
```yaml
agents:
  coding:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.0
    max_tokens: 4000        # Maximum response length
    top_p: 1.0             # Nucleus sampling (0.0-1.0)
    system_prompt: |       # Custom agent instructions
      You are a coding agent...
```

**Conversation Memory** (`backend/app/config/settings.yaml`):
```yaml
context:
  max_tokens: 12000        # Context window size
  warning_threshold: 0.85  # Warning at 85% capacity
```

**Multi-File Analysis** (`backend/app/config/settings.yaml`):
```yaml
multi_file:
  max_files_per_session: 10
  max_total_rows: 100000
  context_token_budget: 4000
```

**Code Execution** (`backend/app/config/allowlist.yaml`):
```yaml
allowed_libraries:
  - pandas
  - numpy
  - plotly
  # Add custom libraries here
```

Changes to YAML configs require server restart.

## Current Status (v0.7)

### v0.7 API Services & MCP (February 2026)
- API key infrastructure with SHA-256 hashing, `spe_` prefix, user self-service + admin management
- Public REST API v1: file upload/list/download/delete, file context get/update/suggestions, synchronous query
- Credit deduction and API usage logging on all `/v1/` requests with structured request/error logs
- `SPECTRA_MODE=api` as 5th deployment mode, deployable as standalone Dokploy service
- MCP server with 6 curated `spectra_` tools via FastMCP 3.0.2 at `/mcp/` with Streamable HTTP transport
- Bearer token auth middleware for MCP with per-request validation

### v0.6 Docker and Dokploy Support (February 2026)
- Production Dockerfiles for all 3 services (backend, public frontend, admin frontend)
- `docker-entrypoint.sh` with PostgreSQL readiness wait, Alembic migrations on startup, uvicorn as PID 1
- `compose.yaml` for local full-stack development with a single `docker compose up`
- Fail-fast startup validation: backend refuses to start when `SPECTRA_MODE=dev/admin` and `ADMIN_EMAIL`/`ADMIN_PASSWORD` are missing
- Automatic admin user seeding on container startup — no manual `seed-admin` step needed
- 4 Dokploy Application services deployed with split-horizon architecture:
  - Public frontend at `https://spectra.nuelo.ai` (HTTPS via Traefik/Let's Encrypt)
  - Public backend internal-only (no public domain — frontend proxies via Swarm DNS)
  - Admin backend and admin frontend accessible via Tailscale VPN only
- `GET /api/health` endpoints on both frontends for health monitoring
- `GET /version` endpoint — live version and environment display on settings pages
- `DEPLOYMENT.md` — step-by-step guide for Dokploy + Tailscale split-horizon deployment

### v0.5 Admin Portal (February 2026)
- Internal admin portal for platform management (separate Next.js app)
- Split-horizon architecture with `SPECTRA_MODE` routing (public/admin/dev)
- User management, credit system, email invitations, platform settings, audit logging
- Admin dashboard with metrics, trend charts, and credit distribution

### v0.4 Data Visualization (February 2026)
- 6th AI agent (Visualization Agent) generates Plotly chart code with intelligent discretion
- 7 chart types: bar, line, scatter, histogram, box plot, pie, donut
- Automatic chart type selection based on data shape and query intent
- Interactive charts with zoom, pan, hover tooltips, and responsive sizing
- PNG/SVG chart export (1200x800 resolution) with client-side instant rendering
- Chart type switcher for compatible types (bar ↔ line ↔ scatter)
- Theme-aware Nord palette for charts matching dark/light mode toggle
- Non-fatal error handling preserves analysis text and data table on chart failures

### v0.3 Multi-file Conversation Support (February 2026)
- ChatGPT-style session-centric UX with sidebar chat history navigation
- Multi-file linking per session with cross-file analysis (ContextAssembler + named DataFrames)
- My Files screen with TanStack Table, drag-and-drop upload, bulk delete, download
- In-chat file linking via paperclip button, file selection modal, and drag-and-drop overlay
- File requirement enforcement (at least one file per session) with dual feedback
- LLM-powered session title auto-generation with manual rename lock
- Dark/light theme toggle with Nord palette (persists across sessions)
- Right sidebar panel for linked file context (info, remove, count badge)

### v0.2 Intelligence & Integration (February 2026)
- Multi-LLM provider infrastructure (5 providers, per-agent YAML config)
- Session memory with PostgreSQL checkpointing (12K token window)
- Manager Agent with intelligent 3-path query routing
- Smart query suggestions on new chat tabs
- Web search integration with Tavily API
- Production SMTP email with DB-backed password reset

### v0.1 Beta MVP (February 2026)
- Full authentication system (JWT, refresh tokens, password reset)
- File upload with AI data profiling (CSV/Excel up to 50MB)
- 4-agent AI system with LangGraph orchestration
- E2B sandbox code execution with AST validation
- Interactive Data Cards with streaming, sorting, export

### Known Limitations
- E2B sandboxes created per-execution (~150ms cold start, no warm pools)
- Basic mobile responsiveness (functional but not optimized)
- No query safety filter (PII extraction, prompt injection)

## License

MIT License - See LICENSE file for details.

## Contact

- **GitHub**: [github.com/marwazihs/nuelo-spectra](https://github.com/marwazihs/nuelo-spectra)
- **Issues**: Report bugs or request features via GitHub Issues
- **Version**: v0.7 (February 2026)
