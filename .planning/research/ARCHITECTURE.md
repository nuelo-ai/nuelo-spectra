# Architecture Research: Docker + Dokploy Multi-Service Deployment

**Domain:** Docker containerization and Dokploy deployment for an existing FastAPI + Next.js monorepo
**Researched:** 2026-02-18
**Confidence:** MEDIUM-HIGH (Dokploy internals partially from community sources; Next.js and Docker patterns from official docs)

---

## Executive Summary

The three Spectra services (backend, frontend, admin-frontend) each get their own Dockerfile in the monorepo root. Dokploy is configured three times — one application per service — each pointing to a different Dockerfile path but the same Git repo. All three containers join the `dokploy-network` Docker overlay network and communicate using Docker service names as internal hostnames.

The most critical integration constraint is that **Next.js `rewrites` destinations are evaluated at server startup, not build time** — meaning `process.env.BACKEND_URL` works in `next.config.ts`. This eliminates the NEXT_PUBLIC_ bake-in problem for the backend URL. However, two files in `frontend/src` use hardcoded `http://localhost:8000` directly (bypassing the rewrite proxy) and must be migrated to relative `/api/` paths before containerization.

Alembic migrations run in a Docker ENTRYPOINT script before uvicorn starts. The persistent upload volume is a named Docker volume mounted at `/app/uploads` in the backend container. PostgreSQL is Dokploy-managed — backend connects via the internal connection URL provided in the Dokploy database panel.

---

## System Overview: Before (Local Dev) vs After (Docker + Dokploy)

```
LOCAL DEV (current):
  browser
    |
    +-> frontend/    (localhost:3000)
    |     next.config.ts rewrites /api/* -> http://localhost:8000/*
    |
    +-> admin-frontend/  (localhost:3001)
    |     next.config.ts rewrites /api/* -> http://localhost:8000/api/*
    |
    +-> backend/     (localhost:8000, SPECTRA_MODE=dev)
          |
          -> uploads/ (local disk)
          -> PostgreSQL (localhost:5432)


DOCKER + DOKPLOY (target):
  browser
    |
    +-> spectra-frontend   (Dokploy service, HTTPS domain, e.g. app.spectra.io)
    |     Traefik -> Next.js container (port 3000)
    |     next.config.ts rewrites /api/* -> http://[backend-service-name]:8000/*
    |
    +-> spectra-admin      (Dokploy service, HTTPS domain, e.g. admin.spectra.io)
    |     Traefik -> Next.js container (port 3000)
    |     next.config.ts rewrites /api/* -> http://[backend-service-name]:8000/api/*
    |
    +-> spectra-backend    (Dokploy service, internal only OR with HTTPS domain)
          Traefik -> FastAPI container (port 8000)
          SPECTRA_MODE=public (or =admin for admin backend)
          |
          -> named volume: spectra_uploads -> /app/uploads
          -> Dokploy-managed PostgreSQL (internal connection URL)
```

---

## Component Boundaries

### New Files (Created This Milestone)

| File | Purpose | Build Context |
|------|---------|---------------|
| `Dockerfile.backend` | Backend container | Repo root (needs `backend/`) |
| `Dockerfile.frontend` | Public frontend container | Repo root (needs `frontend/`) |
| `Dockerfile.admin` | Admin frontend container | Repo root (needs `admin-frontend/`) |
| `backend/docker-entrypoint.sh` | Run migrations then start uvicorn | Copied into backend image |
| `.dockerignore` | Exclude node_modules, venv, .env from build context | Repo root |

### Modified Files (Existing Code Changes Required)

| File | Change Required | Reason |
|------|----------------|--------|
| `frontend/next.config.ts` | Change destination from `http://localhost:8000` to `process.env.BACKEND_URL` | Hardcoded localhost won't work in Docker |
| `admin-frontend/next.config.ts` | Change destination from `http://localhost:8000` to `process.env.BACKEND_URL` | Same reason |
| `frontend/src/hooks/useSSEStream.ts` | Change `http://localhost:8000/chat/sessions/...` to `/api/chat/sessions/...` | Bypasses rewrite proxy — will fail in Docker |
| `frontend/src/app/(auth)/register/page.tsx` | Change `http://localhost:8000/auth/signup-status` to `/api/auth/signup-status` | Same reason |

### Unchanged Files

| Component | Why Unchanged |
|-----------|--------------|
| `backend/app/` (all Python) | No Docker-specific code changes needed |
| `frontend/src/lib/api-client.ts` | Already uses relative `const BASE_URL = "/api"` — correct |
| `admin-frontend/src/lib/admin-api-client.ts` | Already uses relative paths — correct |
| `backend/alembic/` | Alembic command runs in entrypoint, no code change needed |
| `backend/app/config.py` | `upload_dir` is already configurable via env var |

---

## Dockerfile Structure

### Monorepo Build Context Strategy

All three Dockerfiles sit in the **repo root** and use the **repo root as build context**. This is required because:
- Each Dockerfile needs to COPY from its respective subdirectory
- Dokploy lets you specify `Dockerfile Path` and `Docker Context Path` separately
- Setting `Docker Context Path = .` (repo root) and `Dockerfile Path = Dockerfile.backend` is the correct configuration in Dokploy

```
spectra-dev/              <- Dokploy Docker Context Path for all 3 services
  Dockerfile.backend      <- Dokploy Dockerfile Path for backend service
  Dockerfile.frontend     <- Dokploy Dockerfile Path for frontend service
  Dockerfile.admin        <- Dokploy Dockerfile Path for admin service
  .dockerignore
  backend/
  frontend/
  admin-frontend/
```

### Dockerfile.backend (recommended structure)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (cache layer)
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies (cached unless pyproject.toml/uv.lock changes)
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ .

# Copy entrypoint script
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create uploads directory (volume mount point)
RUN mkdir -p /app/uploads

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
```

### backend/docker-entrypoint.sh

```bash
#!/bin/sh
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Spectra backend..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The `exec` prefix replaces the shell process with uvicorn, ensuring Docker signals (SIGTERM) go directly to uvicorn for graceful shutdown.

### Dockerfile.frontend (recommended structure)

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .
# BACKEND_URL is NOT needed at build time (rewrites read it at runtime)
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

Note: The Next.js standalone output mode (`output: 'standalone'` in next.config.ts) is required for this Dockerfile pattern. It produces a minimal self-contained server.

### Dockerfile.admin (identical pattern to Dockerfile.frontend)

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY admin-frontend/package.json admin-frontend/package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY admin-frontend/ .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Dokploy Service Configuration

### Three Dokploy Application Services

| Dokploy Service Name | Dockerfile Path | Docker Context Path | Domain Example |
|---------------------|----------------|---------------------|----------------|
| `spectra-backend` | `Dockerfile.backend` | `.` | `api.spectra.io` (or internal only) |
| `spectra-frontend` | `Dockerfile.frontend` | `.` | `app.spectra.io` |
| `spectra-admin` | `Dockerfile.admin` | `.` | `admin.spectra.io` |

All three services use the same Git repo and branch. Dokploy deploys them independently and each gets its own environment variable panel.

---

## Inter-Service Networking (Dokploy Network)

### How dokploy-network Works

Dokploy runs all managed services on a shared Docker overlay network called `dokploy-network`. Each application service automatically joins this network when deployed via Dokploy's Application type (not Docker Compose). Containers on the same network resolve each other by Docker service name.

The internal hostname for each Dokploy application service follows the pattern Dokploy assigns — typically based on the service's app name slug (e.g., `spectra-backend`). The exact internal hostname is visible in the Dokploy UI under the service's network/container settings.

**MEDIUM confidence** — Dokploy does not publicly document the exact container naming convention. Community sources confirm service names are used as hostnames on dokploy-network. The safe approach is to configure `BACKEND_URL` in each frontend service's environment variables via the Dokploy UI, using the internal hostname confirmed post-deploy.

### Internal Connection Flow

```
spectra-frontend container
  next.config.ts rewrites:
    source:      /api/:path*
    destination: http://[BACKEND_URL]/:path*
    (BACKEND_URL = http://spectra-backend:8000 on dokploy-network)

spectra-admin container
  next.config.ts rewrites:
    source:      /api/:path*
    destination: http://[BACKEND_URL]/api/:path*
    (BACKEND_URL = http://spectra-backend:8000 on dokploy-network)

spectra-backend container
  DATABASE_URL = [Dokploy internal PostgreSQL connection URL]
  (Dokploy provides this in Database > Connection > Internal Connection URL)
```

### Why rewrites Work for Internal Backend URL (Not NEXT_PUBLIC_)

Next.js `rewrites()` in `next.config.ts` is an async function evaluated at **Node.js server startup**, not at `next build`. This means `process.env.BACKEND_URL` is read from the container's environment at runtime. The frontend image does NOT bake in the backend URL — the same image can be pointed at any backend by changing a single environment variable.

This eliminates the "NEXT_PUBLIC_ baked at build time" problem entirely, because the backend URL never needs to reach the browser. The browser only ever makes requests to the frontend's own domain (`/api/*`), which the Next.js server proxies to the backend internally.

```typescript
// frontend/next.config.ts — AFTER this milestone
const nextConfig: NextConfig = {
  output: 'standalone',  // Required for Docker minimal image
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
};
```

```typescript
// admin-frontend/next.config.ts — AFTER this milestone
const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};
```

---

## Environment Variable Flow

### Backend Service (spectra-backend) — Set in Dokploy UI

| Variable | Source | Example Value |
|----------|--------|---------------|
| `DATABASE_URL` | Dokploy DB panel > Internal Connection URL | `postgresql+asyncpg://user:pass@postgres-host:5432/spectra` |
| `SPECTRA_MODE` | Set manually | `public` (or `admin` if running separate admin backend) |
| `SECRET_KEY` | Generated secret | `<32+ char random string>` |
| `ANTHROPIC_API_KEY` | Secret | `sk-ant-...` |
| `UPLOAD_DIR` | Volume mount path | `/app/uploads` |
| `CORS_ORIGINS` | Frontend domain | `["https://app.spectra.io"]` |
| `ADMIN_CORS_ORIGIN` | Admin domain | `https://admin.spectra.io` |
| `FRONTEND_URL` | Frontend domain | `https://app.spectra.io` |
| `ENABLE_SCHEDULER` | Toggle | `true` |

### Frontend Service (spectra-frontend) — Set in Dokploy UI

| Variable | Source | Example Value |
|----------|--------|---------------|
| `BACKEND_URL` | Internal Dokploy hostname | `http://spectra-backend:8000` |
| `NODE_ENV` | Static | `production` |

### Admin Service (spectra-admin) — Set in Dokploy UI

| Variable | Source | Example Value |
|----------|--------|---------------|
| `BACKEND_URL` | Internal Dokploy hostname | `http://spectra-backend:8000` |
| `NODE_ENV` | Static | `production` |

### SPECTRA_MODE and the Two Frontends

`SPECTRA_MODE` differentiates the two frontends at the **backend layer, not the frontend layer**. Both `frontend/` and `admin-frontend/` are independently deployed Next.js apps — they never know about each other. The distinction is:

- `spectra-frontend` container always hits the backend's public routes (`/auth/`, `/files/`, `/chat/`, etc.)
- `spectra-admin` container always hits the backend's admin routes (`/api/admin/...`)

The backend configured with `SPECTRA_MODE=public` serves only public routes. The backend configured with `SPECTRA_MODE=admin` serves only admin routes. In a single-backend deployment, use `SPECTRA_MODE=dev` to serve both from one container.

**Recommended production configuration:**
- Single backend: `SPECTRA_MODE=dev` — simpler, both frontends share one backend process
- Split backends: `SPECTRA_MODE=public` + `SPECTRA_MODE=admin` — deploy two backend instances, each frontend hits its own backend. Adds complexity, only justified if security isolation between admin and public traffic is required.

---

## File Upload Volume Strategy

### Named Docker Volume (not bind mount)

Use a named Docker volume (`spectra_uploads`) mounted at `/app/uploads` in the backend container. Named volumes persist across container restarts and redeployments. They are managed by Docker on the host filesystem.

**Dokploy configuration:** In the backend service > Advanced > Volumes/Mounts, add:
- Volume name: `spectra_uploads`
- Mount path: `/app/uploads`
- Type: Docker volume (not bind mount)

**Why named volume over bind mount:**
- Named volumes survive `docker rm`, container recreations, and Dokploy redeployments
- No dependency on specific host paths or directory permissions
- Dokploy's Advanced > Volumes UI creates named volumes cleanly
- Bind mounts require the host directory to exist with correct permissions before container starts

**Backend config alignment:** `backend/app/config.py` has `upload_dir: str = "uploads"` as default. Set `UPLOAD_DIR=/app/uploads` in the Dokploy environment variable panel to use the absolute path inside the container. The existing `Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)` in `main.py` handles directory creation safely.

---

## Alembic Migration Strategy

### ENTRYPOINT Script Pattern (Recommended)

Run `alembic upgrade head` in a shell entrypoint script before starting uvicorn. This is the standard pattern for FastAPI + Alembic in Docker.

```bash
# backend/docker-entrypoint.sh
#!/bin/sh
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting uvicorn..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Why not a separate migration service/container:**
- The Alembic migration in this project is fast (schema-only, no heavy data migrations)
- A separate "migration job" container complicates Dokploy setup (requires ordered deployment)
- The entrypoint approach is idempotent — re-running `alembic upgrade head` when already at head is a no-op
- `set -e` ensures the container fails fast if migration fails (rather than starting uvicorn against a broken schema)

**Why not run migrations in FastAPI lifespan startup:**
- SQLAlchemy async engine + Alembic sync engine creates event loop conflicts
- Migration output disappears into the uvicorn startup log noise
- Lifespan runs after uvicorn is already accepting connections — other services could send requests before migration completes

**Working directory requirement:** The entrypoint runs in `/app` (WORKDIR), where `alembic.ini` and `alembic/` directory reside after `COPY backend/ .`. This matches the existing `alembic.ini` configuration (`script_location = %(here)s/alembic`).

---

## Recommended Build Order for Phases

Dependencies between services determine build order:

```
Phase 1: Backend container
  - Prerequisite for everything
  - Test: health check endpoint responds, migrations run, DB connects

Phase 2: Public frontend container
  - Depends on: backend URL is known (set BACKEND_URL)
  - Test: Next.js proxy rewrites reach backend, login flow works

Phase 3: Admin frontend container
  - Depends on: backend serving admin routes (SPECTRA_MODE=dev or =admin)
  - Test: admin login, /api/admin/dashboard accessible through frontend proxy
```

**Why backend before frontends:**
- Both frontends' `next.config.ts` rewrites must point to a real backend URL
- Without a deployed backend, `BACKEND_URL` has no valid target to test against
- Backend Dockerfile is simpler (no multi-stage) — build confidence before the more complex frontend Dockerfiles

---

## Patterns to Follow

### Pattern 1: Monorepo Dockerfile at Repo Root with Subdirectory COPY

**What:** Each Dockerfile lives in the repo root and COPYs only its subdirectory.
**When:** Always for this monorepo.
**Trade-offs:** Simple configuration in Dokploy (all services use same context path `.`); slightly larger initial build context transfer (mitigated by `.dockerignore`).

```dockerfile
# In Dockerfile.backend (at repo root):
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/ .
# NOT: COPY . .  (would copy all 3 frontends into backend image)
```

### Pattern 2: Next.js `output: 'standalone'` for Minimal Images

**What:** Add `output: 'standalone'` to `next.config.ts`. This generates a self-contained server in `.next/standalone/` with only the necessary Node.js modules.
**When:** Always when containerizing Next.js for production.
**Trade-offs:** Build output is ~90% smaller than a full `node_modules` copy. Required for the multi-stage Dockerfile pattern above.

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  output: 'standalone',
  // ... rest of config
};
```

### Pattern 3: `exec` in Entrypoint for Signal Forwarding

**What:** Use `exec uv run uvicorn ...` (not `uv run uvicorn ...`) in the entrypoint script.
**When:** Always in Docker entrypoint scripts.
**Why:** Without `exec`, the shell script becomes PID 1 and swallows Docker's SIGTERM, preventing graceful uvicorn shutdown. With `exec`, uvicorn becomes PID 1 and receives signals directly.

### Pattern 4: Relative API Paths in Frontend Code

**What:** All fetch calls in frontend code use relative paths (`/api/...`) not absolute URLs (`http://localhost:8000/...`).
**When:** Always — enforced by code migration in this milestone.
**Why:** Relative paths go through the Next.js rewrite proxy, which handles the Docker internal routing. Absolute localhost URLs break in any non-local environment.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: NEXT_PUBLIC_BACKEND_URL for Backend Communication

**What people do:** Add `NEXT_PUBLIC_BACKEND_URL=https://api.spectra.io` and use it in client-side fetch calls.
**Why it's wrong:** `NEXT_PUBLIC_` variables are inlined into the JS bundle at `next build`. The deployed image has the URL baked in — you cannot change it without rebuilding. Also exposes internal service URLs to browser clients unnecessarily.
**Do this instead:** Use `process.env.BACKEND_URL` (no NEXT_PUBLIC_ prefix) in `next.config.ts` rewrites. The browser never sees the backend URL — it only calls `/api/*` on its own domain.

### Anti-Pattern 2: Separate Migration Container in Dokploy

**What people do:** Create a 4th Dokploy service just for Alembic, set as a dependency of the backend.
**Why it's wrong:** Dokploy's application dependency ordering is not designed for one-shot jobs. Migration containers that exit 0 get restarted by Docker. Managing this in Dokploy adds complexity for no benefit given fast schema-only migrations.
**Do this instead:** Entrypoint script runs migrations before uvicorn starts. Same container, same image, zero added complexity.

### Anti-Pattern 3: Separate Dockerfiles Per Directory vs Monorepo Root

**What people do:** Put `Dockerfile` inside `backend/`, `frontend/`, `admin-frontend/` respectively and set Docker Context Path to the subdirectory.
**Why it's wrong (for this project):** No shared files need to cross directory boundaries, so it would work technically. But it means three separate Dokploy context paths (`backend/`, `frontend/`, `admin-frontend/`), making it harder to add any repo-root shared files later. Keeping Dockerfiles at root with explicit subdirectory COPYs is more explicit and flexible.
**Exception:** If the monorepo grows to add shared packages (e.g., `packages/shared-types/`), root-level Dockerfiles that can COPY cross-directory are already set up correctly.

### Anti-Pattern 4: Using `container_name` in Docker Configurations

**What people do:** Explicitly set container names in Docker Compose or Dokploy labels.
**Why it's wrong:** Dokploy's logging, metrics, and other management features rely on its own container naming scheme. Overriding container names breaks Dokploy's ability to track and manage the service.
**Do this instead:** Let Dokploy assign container names. Reference services by their Dokploy service name on dokploy-network.

### Anti-Pattern 5: Bind Mounting the Uploads Directory

**What people do:** Use a bind mount like `/var/spectra/uploads:/app/uploads` for file persistence.
**Why it's wrong:** Bind mounts require the host directory to exist with correct permissions before the container starts. Host path management is manual and error-prone across Dokploy redeployments.
**Do this instead:** Named Docker volume `spectra_uploads` mounted at `/app/uploads`. Docker manages the host storage location automatically.

---

## Data Flow

### Request Flow: Public Frontend → Backend

```
Browser
  |
  +-> HTTPS request to https://app.spectra.io/api/chat/sessions
  |
  v
Traefik (Dokploy managed)
  |
  v
spectra-frontend container (Next.js, port 3000)
  next.config.ts rewrites: /api/* -> http://spectra-backend:8000/*
  |
  +-> Server-side HTTP request (internal Docker network)
  v
spectra-backend container (FastAPI, port 8000)
  SPECTRA_MODE=public (or dev)
  |
  +-> PostgreSQL (Dokploy managed, internal connection)
  +-> Named volume: spectra_uploads (/app/uploads)
  +-> E2B cloud API (external, no container)
```

### Request Flow: SSE Streaming (Special Case)

The SSE streaming hook in `frontend/src/hooks/useSSEStream.ts` currently uses a hardcoded `http://localhost:8000/chat/sessions/${sessionId}/stream` URL that bypasses the Next.js rewrite proxy entirely. This must be changed to `/api/chat/sessions/${sessionId}/stream` to route through the proxy in Docker.

The rewrite proxy handles POST-based SSE streaming correctly — Next.js passes through the response stream without buffering.

### Migration Flow at Container Start

```
Docker starts spectra-backend container
  |
  v
/docker-entrypoint.sh runs
  |
  +-> uv run alembic upgrade head
  |     (reads DATABASE_URL from environment)
  |     (connects to Dokploy-managed PostgreSQL via internal URL)
  |     (runs pending migrations idempotently)
  |     (exits 0 on success, exits non-0 on failure -> container stops)
  |
  v
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
  (uvicorn becomes PID 1, receives Docker signals directly)
  |
  +-> FastAPI lifespan starts
  +-> LangGraph checkpointer setup
  +-> LLM connectivity validation
  +-> APScheduler starts (if ENABLE_SCHEDULER=true)
  +-> Ready to serve requests
```

---

## Integration Points

### External Services (Unchanged by Containerization)

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| E2B code sandbox | HTTP API calls from backend | External cloud service, no Docker changes |
| Anthropic/OpenAI/etc. | HTTP API calls from backend | API keys as env vars in Dokploy UI |
| Tavily search | HTTP API calls from backend | API key as env var |
| LangSmith | HTTP API calls from backend | Optional, env var toggled |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| spectra-frontend -> spectra-backend | Server-side HTTP over dokploy-network | Via Next.js rewrite proxy |
| spectra-admin -> spectra-backend | Server-side HTTP over dokploy-network | Via Next.js rewrite proxy |
| spectra-backend -> PostgreSQL | TCP over dokploy-network | Dokploy internal connection URL |
| spectra-backend -> named volume | Docker volume mount | /app/uploads |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 instances | Current architecture: single backend with SPECTRA_MODE=dev |
| 10-100 instances | Split SPECTRA_MODE=public and =admin into separate backend containers; add replica count in Dokploy Advanced > Cluster |
| 100+ instances | Replace named volume with object storage (S3/R2) for uploads; backend becomes truly stateless |

### Scaling Priorities

1. **First bottleneck:** Named volume (`spectra_uploads`) — files are stored on a single host. Cannot scale backend to multiple replicas with a named volume. Migration to object storage (S3/Cloudflare R2) needed before horizontal scaling of the backend.
2. **Second bottleneck:** APScheduler runs inside the FastAPI process. With multiple replicas, credit reset jobs run N times (once per replica). Requires a distributed lock or moving the scheduler to a dedicated container before adding replicas.

---

## Sources

- Dokploy Build Type documentation (Dockerfile Path + Docker Context Path fields): [https://docs.dokploy.com/docs/core/applications/build-type](https://docs.dokploy.com/docs/core/applications/build-type) — HIGH confidence
- Dokploy database internal connection URL: [https://docs.dokploy.com/docs/core/databases/connection](https://docs.dokploy.com/docs/core/databases/connection) — HIGH confidence
- Dokploy dokploy-network inter-service communication: [https://torchtree.com/en/post/dokploy-container-network-issue/](https://torchtree.com/en/post/dokploy-container-network-issue/) — MEDIUM confidence (community source, not official docs)
- Next.js self-hosting with Docker (runtime env vars, standalone output): [https://nextjs.org/docs/app/guides/self-hosting](https://nextjs.org/docs/app/guides/self-hosting) — HIGH confidence (official docs, updated 2026-02-16)
- Next.js rewrites configuration: [https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites) — HIGH confidence (official docs)
- NEXT_PUBLIC_ baked at build time (confirmed): [https://github.com/vercel/next.js/discussions/17641](https://github.com/vercel/next.js/discussions/17641) — HIGH confidence (official Next.js discussion)
- FastAPI + Alembic entrypoint pattern: [https://blog.devops.dev/a-scalable-approach-to-fastapi-projects-with-postgresql-alembic-pytest-and-docker-using-uv-78ebf6f7fb9a](https://blog.devops.dev/a-scalable-approach-to-fastapi-projects-with-postgresql-alembic-pytest-and-docker-using-uv-78ebf6f7fb9a) — MEDIUM confidence (community, consistent with all other sources)
- Direct codebase analysis: `frontend/next.config.ts`, `admin-frontend/next.config.ts`, `frontend/src/lib/api-client.ts`, `admin-frontend/src/lib/admin-api-client.ts`, `frontend/src/hooks/useSSEStream.ts`, `frontend/src/app/(auth)/register/page.tsx`, `backend/app/config.py`, `backend/app/main.py`, `backend/alembic.ini`, `backend/pyproject.toml` — HIGH confidence

---
*Architecture research for: Docker + Dokploy multi-service deployment*
*Researched: 2026-02-18*
