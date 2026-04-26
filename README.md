# Spectra

AI-powered data analytics platform. Chat with your data through natural language, or run Pulse anomaly detection to automatically surface severity-sorted signals with statistical evidence and Plotly visualizations.

## What is Spectra?

Spectra bridges the gap between raw data and actionable insights. Upload your datasets, and a multi-agent AI system analyzes data structure, generates Python code, executes it in a secure sandbox, and presents results — either through a conversational chat interface or the Pulse Analysis workspace.

![Spectra screenshot](spectra-screenshot.png)

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
- **Theming**: Dark/light mode with Nord palette (chat) and Hex.tech palette (workspace)
- **Spectra Pulse**: Collection management, CSV/Excel file upload with column profiling, AI anomaly detection with Plotly signal cards, downloadable Markdown reports, tier-based access gating
- **Admin Portal**: Separate admin app for user management, credits, invitations, platform settings (including Pulse credit cost), and audit logging
- **REST API v1**: File upload/list/download/delete, file context, synchronous query — all with Bearer token auth and credit deduction
- **MCP Server**: FastMCP 3.0.2 with Streamable HTTP transport at `/mcp/`, 6 `spectra_` tools for AI agent integrations
- **API Key Management**: Create, view, revoke keys from Settings page; admin manages keys for all users
- **Stripe Billing**: Subscription management (Basic/Premium), credit top-ups, trial expiration enforcement, webhook-driven lifecycle, admin billing tools with discount codes and refunds

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
| `SPECTRA_MODE` | Router mode: `dev` (all routes), `public` (user-facing only), `admin` (admin-only), `api` (external API + MCP). Default: `dev` |
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
2. LLM health: `http://localhost:8000/health/llm` *(dev/public/admin modes only — not available in `SPECTRA_MODE=api`)*
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

## Current Status (v0.10)

### v0.10 Streamline Pricing Configuration (April 2026)
- **Config-driven pricing** — subscription pricing fields (`has_plan`, `price_cents`) added to `user_classes.yaml`; default credit packages defined in config; zero manual setup on first deployment
- **Startup sync** — on first startup, subscription pricing seeded to `platform_settings` and credit packages seeded to `credit_packages` table from config defaults; Stripe Products/Prices auto-created for any tier or package missing a Stripe Price ID; existing admin-customized Stripe Price IDs never overwritten (fills gaps only)
- **Admin Pricing Management UI** — admin can view subscription pricing with config defaults vs current DB values side by side, edit pricing (auto-creates new Stripe Prices), and reset to config defaults; same view/edit/reset for credit packages; password confirmation on destructive actions
- **Dynamic plan rendering** — Plan Selection page renders subscription plans from tiers with `has_plan: true` instead of hardcoded entries; Billing page displays credit packages from database
- **Upgrading from v0.9:**

```bash
git pull origin master
cd backend && uv sync
uv run alembic upgrade head
cd ../admin-frontend && npm install
```

### v0.9 Monetization (April 2026)
- **Stripe billing integration** — full payment infrastructure with Checkout Sessions for subscriptions and credit top-ups, webhook-driven subscription lifecycle (checkout.session.completed, invoice.paid, invoice.payment_failed, customer.subscription.updated/deleted)
- **Tier restructure** — 4 consumer tiers: Free Trial (14-day), On Demand, Basic, Premium; dual-balance credit tracking (subscription + purchased credits); subscription-first deduction
- **Trial expiration** — backend 402 enforcement, countdown banner with amber urgency, blocking overlay on expiration, configurable duration and credits
- **Billing UI** — Plan Selection page with live pricing and upgrade/downgrade confirmation with Stripe proration preview; Manage Plan page with subscription status, credit balances, top-up purchase, billing history
- **Admin billing tools** — user billing detail (subscription, payments, Stripe events), force-set tier with Stripe sync, refund with proportional credit deduction, billing settings (trial duration, pricing with Stripe Price auto-creation), discount codes with Stripe Coupon/Promotion Code sync
- **Settings restructured** — tab navigation (Profile, API Keys, Plan, Billing)
- **Upgrading from v0.8.2:**

```bash
git pull origin master
cd backend && uv sync
uv run alembic upgrade head  # Creates Subscription, PaymentHistory, CreditPackage, StripeEvent, DiscountCode tables
cd ../frontend && npm install
```

### v0.8.2 Chat Query Suggestions Redesign (March 2026)
- **Query suggestion cards** — redesigned from pill chips to Signal-card-style bordered cards with icon, bold category title, and per-suggestion cards
- **Column layout** — grouped by category in a responsive multi-column grid (3 columns default); expands to show more via "View more" toggle when categories exceed 3
- **Upgrading from v0.8.1:** No migrations required — UI-only changes. Pull and rebuild frontend.

```bash
git pull origin master
cd frontend && npm install
```

### v0.8.1 UI Fixes & Enhancement (March 2026)
- **Leftbar toggle visibility** — SidebarTrigger added to all Pulse workspace sub-views (Collection Detail, Signal View, Report pages); toggle always accessible regardless of active sub-view
- **Nav icon alignment** — Sidebar nav items aligned correctly with chat history list; SidebarGroup wrapper restores shadcn `p-2` padding context
- **Logo cleanup** — Spectra logo removed from Chat and Files main panel headers; present only in the app shell sidebar
- **Chat rightbar toggles** — Expand button visible at top right after collapse (WelcomeScreen); collapse/expand toggle pinned to top right in active chat (not top middle)
- **Credits Used accuracy** — Collection Overview stat card now shows actual cumulative credit spend from completed Pulse runs (via PostgreSQL aggregate subquery); no longer hardcoded
- **Mobile-responsive Signal View** — Signal detail panel accessible on small screens via show/hide toggle; back button returns user to signal list
- **Chat bridge button** — "Chat with Spectra" button in Signal detail links collection files to a new Chat session, opening in a new tab
- **Timestamps** — Activity history and file added lists display both date and time (not date only)
- **Upgrading from v0.8:** No migrations required — UI-only changes. Pull and rebuild frontend.

```bash
git pull origin master
cd frontend && npm install
```

### v0.8 Spectra Pulse (Detection) (March 2026)
- **Spectra Pulse** — full AI-powered anomaly detection workspace: create Collections, upload CSV/Excel files, run Pulse detection, view severity-sorted Signal cards with Plotly chart visualizations and 2x2 statistical evidence grids
- **Multi-agent orchestrator pipeline** — brain/orchestrator calling independent coder, interpreter, viz, and report writer sub-agents; Pydantic structured output on all reasoning LLM calls; E2B sandbox with 300s timeout
- **Collection management** — create, rename, delete collections; file upload with column profile slide-out (DataSummaryPanel); cascade delete; query cache invalidation
- **Detection UX** — inline progress banner on Overview tab, sonner toast on completion with signal count and "View Signals" link, re-run confirmation dialog with credit cost warning
- **Reports** — auto-generated Markdown analysis reports per Pulse run; full-page report viewer with Markdown rendering and download
- **Tier-based access gating** — workspace_access + max_active_collections per tier in user_classes.yaml; workspace_credit_cost_pulse configurable via Admin Portal at runtime
- **Upgrading from v0.7:**

```bash
git pull origin master
cd backend && uv sync
uv run alembic upgrade head  # Creates collections, collection_files, signals, reports, pulse_runs tables
cd ../frontend && npm install
```

### v0.7.10 Admin Credit Usage Display Fix (February 2026)
- Fixed admin Activity Tab showing zero activity for API-only users — `get_user_activity()` now queries `api_usage_logs` by month and merges `api_query_count` into the monthly breakdown; "API Queries" column added to the activity table
- Fixed admin Sessions Tab stats excluding API query activity — `get_user_detail()` now aggregates `api_query_count` from `api_usage_logs`; `last_message_at` fixed to `MAX` across both `chat_messages` and `api_usage_logs` so pure API users no longer show "No session activity yet"; "API Queries" stat card added to the Sessions tab
- Added credit transaction source attribution — new nullable `api_key_id` column on `credit_transactions` (Alembic migration); `CreditService.deduct_credit()` accepts optional `api_key_id`; API query path (`POST /v1/chat/query`) threads the key through; Credits tab in admin now shows an "API" badge on transactions sourced from API key usage

### v0.7.9 Admin Users Activity Tab Fix (February 2026)
- Fixed `GET /api/admin/users/{id}/activity` returning HTTP 500 — SQLAlchemy generated separate bind parameters for each occurrence of `func.date_trunc("month", col)` in SELECT, GROUP BY, and ORDER BY, causing PostgreSQL to throw `GroupingError`. Fixed by using `text("1")` ordinal position reference for GROUP BY and ORDER BY on both the messages and sessions queries
- Fixed admin frontend `ActivityTab` component silently swallowing the 500 error — `isError` was never checked, so failures rendered as "No activity data available" with no indication of what went wrong. Added explicit error state with Retry button

### v0.7.8 MCP Chart Spec Binary Decoding + API Docs (February 2026)
- Fixed MCP `spectra_run_analysis` returning Plotly binary typed arrays (`{"dtype":"f8","bdata":"<base64>"}`) in chart specs — Plotly serializes numpy numeric arrays as binary for space efficiency, but this is opaque to AI agents. The MCP layer now decodes all binary nodes to plain JSON numbers before returning. Covers all dtypes (`f8`, `f4`, `i8`, `i4`, `u4`); unknown dtypes are passed through with a warning log. Blanket guarantee: all queries, all chart types
- Renamed `API-REFERENCE.md` → `API_MCP_REFERENCE.md` with full documentation update: mcp-remote setup for Claude Desktop, expanded `spectra_run_analysis` response format, HTML + CDN Plotly rendering guide for MCP chart output

### v0.7.7 MCP Execution Result Data Table (February 2026)
- Added `execution_result` data table as first content block in `spectra_run_analysis` MCP output — the raw computed result rows were returned by the backend but omitted from MCP tool output. AI agents now see the data as a markdown table (max 50 rows with truncation note) before the narrative analysis, enabling direct data reasoning and verification

### v0.7.6 MCP Bug Fixes (February 2026)
- Fixed MCP tools returning "Invalid token" — `set_state`/`get_state` are async but were called without `await`, causing the API key to never be stored or read from context state; header became `Bearer <coroutine ...>` which failed JWT validation
- Fixed MCP loopback calls hitting `/v1/*` instead of `/api/v1/*`, causing HTTP 404 on all tool calls in `SPECTRA_MODE=api`
- All 6 MCP tools (`spectra_list_files`, `spectra_upload_file`, `spectra_run_analysis`, `spectra_delete_file`, `spectra_download_file`, `spectra_get_context`) now fully functional against production API

### v0.7.5 API Surface Cleanup (February 2026)
- Removed duplicate "API v1" catch-all group from Swagger — endpoints now appear only under their own tagged groups
- `/api/v1/keys` (self-service key management) no longer exposed in `SPECTRA_MODE=api` — only available in `public`/`dev` modes
- `/health/llm` restricted to `dev`/`public`/`admin` modes only — not reachable externally in `SPECTRA_MODE=api`
- `/health` now returns `app_version` from settings instead of hardcoded `"0.1.0"`

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
- **Version**: v0.10 (April 2026)
