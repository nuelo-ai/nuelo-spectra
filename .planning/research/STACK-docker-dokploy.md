# Stack Research: Docker + Dokploy Deployment

**Domain:** Docker containerization + Dokploy PaaS deployment (multi-service app)
**Researched:** 2026-02-18
**Confidence:** HIGH (verified with Dokploy official docs, Next.js official upgrade guide, uv official docs, Docker official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `python:3.12-slim` | 3.12.x (Debian bookworm-slim) | Backend base image | Matches `requires-python = ">=3.12"` in pyproject.toml. 3.12 is current LTS with active security patches through 2028. `-slim` strips unnecessary packages (curl, git, man pages) saving ~200MB vs full image. 3.13 is too new — asyncpg, psycopg-binary, and LangGraph binary wheels need explicit 3.13 verification. |
| `node:22-alpine` | 22.x LTS (Alpine 3.21) | Both frontend base images (build + runtime) | Next.js 16 requires Node.js 20.9+ minimum (confirmed in official Next.js 16 upgrade guide, verified 2026-02-16). Node 22 is current LTS (active support until 2027). Alpine saves ~100MB vs Debian-based `node:22-slim`. |
| Docker Compose v2 (no version field) | CLI v2.x (latest: v5.0.2 as of 2026-02-03) | Local dev orchestration | The top-level `version:` field is officially obsolete in Compose v2. Docker Compose v2 ignores it entirely and emits warnings if present. Omit the field entirely. |
| Dokploy | v0.26.x (latest: v0.26.7 as of 2026-01-31) | Self-hosted PaaS | Manages 3 services as independent Application entries, each with their own Dockerfile build, env vars, port config, and deployment pipeline. Built-in Traefik proxy, no vendor lock-in. |

---

## Per-Service Docker Base Images

| Service | Base Image | Why |
|---------|-----------|-----|
| FastAPI backend | `python:3.12-slim` | Binary wheels available for asyncpg 0.31+, psycopg-binary 3.3.x. The `-slim` (Debian bookworm-slim) image has glibc which is required by manylinux binary wheels. Alpine (musl libc) would break asyncpg and psycopg binary packages. |
| Public frontend (`frontend/`) | `node:22-alpine` (build) + `node:22-alpine` (runtime) | Multi-stage standalone output. Final image ~150MB vs 800MB+ with full node_modules. Alpine is fine for Next.js — no native Node modules that require glibc. |
| Admin frontend (`admin-frontend/`) | `node:22-alpine` (build) + `node:22-alpine` (runtime) | Same pattern as public frontend. Admin runs on port 3001. |

---

## Supporting Tools

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `uv` | latest (via `ghcr.io/astral-sh/uv:latest`) | Python dependency management in Docker | Project already uses `uv.lock`. Copy uv binary into build stage: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/`. Use `uv sync --locked --no-dev` in Dockerfile for reproducible, fast installs. |
| `.dockerignore` | n/a | Exclude node_modules, .venv, .next, uploads from build context | Required per service. Without it, build context can be several GB (node_modules alone). |
| Next.js `output: 'standalone'` | Built into Next.js | Minimal self-contained Node.js server | Official Vercel recommendation for Docker. Copies only required files into `.next/standalone` — final image ~150MB. Must add `output: 'standalone'` to `next.config.ts` for both frontend apps. |
| Traefik (via Dokploy) | Bundled with Dokploy | Reverse proxy, TLS termination, domain routing | No manual Traefik config needed. Dokploy configures Traefik automatically per Application via its UI. |

---

## Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `docker-compose.yml` (project root) | Local dev orchestration of all 3 services + local PostgreSQL | Use Compose v2 syntax (no `version:` field). Mount source directories as volumes for hot reload in dev mode. |
| `.env` per service | Runtime configuration | Keep secrets out of Dockerfiles and source control. Use `.env.example` files in git, actual `.env` only on servers. |
| `multi-stage Dockerfile` | Separate build dependencies from runtime | Standard pattern. Builder stage installs all deps + builds. Runner stage copies only artifacts — no build tools, no dev deps in production image. |

---

## Dokploy Deployment Model

### How Dokploy Manages 3 Independent Services

Dokploy treats each service as a standalone **Application** with its own:
- Git source + branch configuration
- Build type (Dockerfile, Nixpacks, Buildpack, Railpack, or Static)
- Environment variables (service-level — completely isolated from other services)
- Port configuration (Dokploy routes traffic via Traefik)
- Deployment history + logs per service
- Volume/mount configuration per service

**There is no `dokploy.yml` or `.dokploy/` config file.** All configuration lives in the Dokploy web UI. Unlike Railway (`railway.toml`) or Fly.io (`fly.toml`), Dokploy does not use a project-level config file. The UI is the configuration surface.

### Application Structure in Dokploy UI

```
Dokploy Project: Spectra
├── Application: spectra-backend
│   ├── Source: Git repo root
│   ├── Build type: Dockerfile
│   ├── Dockerfile path: backend/Dockerfile
│   ├── Docker context: backend/
│   ├── Port: 8000
│   └── Env vars: DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY, SPECTRA_MODE=public, etc.
│
├── Application: spectra-frontend
│   ├── Source: Git repo root
│   ├── Build type: Dockerfile
│   ├── Dockerfile path: frontend/Dockerfile
│   ├── Docker context: frontend/
│   ├── Port: 3000
│   └── Env vars: NEXT_PUBLIC_API_URL=https://api.example.com, SPECTRA_MODE=public
│
└── Application: spectra-admin
    ├── Source: Git repo root
    ├── Build type: Dockerfile
    ├── Dockerfile path: admin-frontend/Dockerfile
    ├── Docker context: admin-frontend/
    ├── Port: 3001
    └── Env vars: NEXT_PUBLIC_API_URL=https://api.example.com, SPECTRA_MODE=admin
```

### Why Dockerfile Build Type (Not Nixpacks)

Use **Dockerfile** build type in Dokploy because:
- The project uses `uv` with `uv.lock` — Nixpacks does not understand uv lock files as of early 2026
- Multi-stage builds are required for Next.js standalone output — Nixpacks cannot do multi-stage
- Explicit layer caching control reduces build times significantly for repeated deploys
- `psycopg[binary]` and asyncpg need specific handling that Nixpacks may not handle correctly

Nixpacks is appropriate for rapid prototyping or simpler apps. Use Dockerfile for production control.

---

## Environment Variables in Dokploy

Dokploy supports a three-tier variable hierarchy (introduced in v0.25.0):

| Scope | Syntax in UI | Use Case |
|-------|-------------|---------|
| Project-level | `${{project.VAR_NAME}}` | Shared across all 3 services (e.g., `DOMAIN_BASE`) |
| Environment-level | `${{environment.VAR_NAME}}` | Staging vs production differentiation |
| Service-level | Plain `VAR_NAME=value` | Service-specific secrets (API keys, DB credentials) |

**For Application deployments:** Env vars set in the Dokploy UI are injected directly into the container environment. They do NOT need to be referenced in `docker-compose.yml` format.

**For Docker Compose deployments:** Dokploy writes vars to a `.env` file alongside `docker-compose.yml`. You must explicitly reference them via `env_file: .env` or `${VAR_NAME}` interpolation in the Compose file.

**Recommendation:** Use service-level vars for all secrets (DATABASE_URL, JWT_SECRET, API keys). Use project-level only for shared config like `DOMAIN_BASE=example.com`.

**Special var:** Dokploy auto-provides `DOKPLOY_DEPLOY_URL` for preview deployments (the deployment's public URL).

---

## Dockerfile Patterns

### Backend: FastAPI + uv (multi-stage)

```dockerfile
# ---- Stage 1: Dependency builder ----
FROM python:3.12-slim AS builder

# Copy uv from official image (avoids curl install)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies FIRST (cached layer — only rebuilds when lock file changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy application code and install project itself
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --compile-bytecode

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

WORKDIR /app

# Create non-root user and uploads directory
RUN adduser --disabled-password --gecos '' appuser && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app

# Copy only the virtual environment and app code from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app
COPY --from=builder --chown=appuser:appuser /app/alembic /app/alembic
COPY --from=builder --chown=appuser:appuser /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=appuser:appuser /app/pyproject.toml /app/pyproject.toml

USER appuser

# Activate virtualenv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Note on psycopg binary:** The project uses `psycopg[binary]>=3.1.0`. The `psycopg-binary` package (v3.3.2+, available for manylinux x86-64 and ARM64 as of Dec 2025) bundles its own libpq. No system-level `libpq-dev` is needed in the slim image. This is the correct choice for containerized deployments.

**Note on asyncpg:** asyncpg 0.31.0 provides manylinux binary wheels for Python 3.9-3.13. Works in `python:3.12-slim` (glibc) without any build tools.

### Frontend: Next.js standalone (multi-stage)

Required change to `next.config.ts` (both `frontend/` and `admin-frontend/`):
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  // ... existing config
}

export default nextConfig
```

```dockerfile
# ---- Stage 1: Builder ----
FROM node:22-alpine AS builder

WORKDIR /app

# Install deps (cached — only rebuilds when package-lock.json changes)
COPY package.json package-lock.json ./
RUN npm ci

# Build Next.js app (requires output: 'standalone' in next.config.ts)
COPY . .
RUN npm run build

# ---- Stage 2: Runtime (lean) ----
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output only (excludes node_modules, source files)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

**Admin frontend Dockerfile** is identical but with `ENV PORT=3001` and `EXPOSE 3001`.

---

## Local Dev: docker-compose.yml

```yaml
# Docker Compose v2 — no version: field (obsolete, triggers warnings)
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app          # Hot reload: mount source code
      - uploads_data:/app/uploads        # Persistent uploads across restarts
    env_file:
      - ./backend/.env
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env.local

  admin-frontend:
    build:
      context: ./admin-frontend
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    env_file:
      - ./admin-frontend/.env.local

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: spectra
      POSTGRES_PASSWORD: spectra_dev
      POSTGRES_DB: spectra
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U spectra"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  uploads_data:
```

**Production note:** The `db` service is local dev only. In Dokploy production, PostgreSQL is Dokploy-managed. Remove `db` service from any production compose file. The `DATABASE_URL` env var points to Dokploy's PostgreSQL instance.

---

## File Storage (uploads/) in Docker

The backend writes user-uploaded files to `./uploads/` relative to the app root (`/app/uploads/` in the container).

| Environment | Storage Approach |
|-------------|-----------------|
| Local dev | Named volume `uploads_data` mounted at `/app/uploads` |
| Dokploy production | Configure volume mount in Dokploy UI: Advanced → Mounts → `/app/uploads` (container path) |

**Critical Dokploy note:** Dokploy's AutoDeploy performs a fresh `git clone` on each deployment, which wipes the repository directory. Any uploads stored inside the cloned directory are lost on re-deploy. Volume mounts persist independently of deployments. Use Dokploy's bind mount recommendation: `../files/uploads:/app/uploads` (host path uses `../files/` prefix which is outside the git clone directory and persists).

---

## .dockerignore Files (Required per Service)

**`backend/.dockerignore`:**
```
.venv
venv
__pycache__
*.pyc
*.pyo
.pytest_cache
uploads/
.env
.git
```

**`frontend/.dockerignore` and `admin-frontend/.dockerignore`:**
```
node_modules
.next
.env
.env.local
.git
*.log
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `python:3.12-slim` | `python:3.13-slim` | When all critical deps (LangGraph, e2b-code-interpreter, asyncpg) confirm Python 3.13 binary wheel support. Check ~late 2026. |
| `python:3.12-slim` | `python:3.12-alpine` | Never for this project. asyncpg and psycopg-binary use manylinux wheels (glibc). Alpine uses musl libc — binary wheels are incompatible. Would require compiling from source with build tools. |
| `node:22-alpine` | `node:22-slim` (Debian-slim) | If Alpine's musl libc causes runtime issues with any native Node add-ons. Next.js itself has no such issues with Alpine. |
| Dockerfile build type (Dokploy) | Nixpacks build type (Dokploy) | Use Nixpacks only for rapid prototyping or if you want zero-config builds and don't need multi-stage. Nixpacks v1.x does not understand uv.lock files. |
| Individual Applications (3 separate Dokploy apps) | Single Docker Compose deployment (1 Dokploy compose app) | Use Compose deployment if services need to communicate via internal Docker network names (e.g., `http://backend:8000`). Individual apps communicate via public URLs or Dokploy-assigned internal hostnames. |
| uv for dependency management | pip in Dockerfile | pip works but is slower and has no lock file guarantee. The project already uses `uv.lock` — `uv sync --locked` is the correct and reproducible approach. |
| No `version:` field in Compose | `version: "3.8"` or any version | Never include a version field. It is officially obsolete in Compose v2 and triggers deprecation warnings in Docker Engine 25+. |
| Next.js `output: 'standalone'` | Standard Next.js build (no standalone) | If you need to run `next start` with a separate `node_modules` available. Standalone is strictly better for Docker — smaller image, self-contained. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `tiangolo/uvicorn-gunicorn-fastapi` base image | Deprecated. Not maintained for modern FastAPI (0.100+). Uses gunicorn multi-worker pattern which conflicts with FastAPI's async lifespan manager and single-process APScheduler. | Custom Dockerfile starting from `python:3.12-slim` |
| `python:3.12-alpine` | musl libc incompatibility with asyncpg and psycopg manylinux binary wheels. Would force compile-from-source, adding build tools and complexity. | `python:3.12-slim` (Debian bookworm-slim, has glibc) |
| `node:18-alpine` or `node:20-alpine` | Node 18 is end-of-life (April 2025). Node 20 works but is in maintenance mode. Next.js 16 supports both, but Node 22 is the active LTS. | `node:22-alpine` |
| `version: "3.x"` field in docker-compose.yml | Officially obsolete in Docker Compose v2. Compose always uses latest schema regardless of this field. Triggers `WARNING: version is obsolete` in Docker 25+. | Omit the field entirely |
| Uploads stored in container filesystem (no volume) | Container filesystem is ephemeral. Files are lost on restart, re-deploy, or container recreation. | Named Docker volume or Dokploy persistent mount at `/app/uploads` |
| `.env` files committed to git | Exposes API keys, DB passwords, JWT secrets. | `.env.example` with placeholder values in git; actual `.env` only on server/in Dokploy UI |
| Build-time `NEXT_PUBLIC_*` vars as ARGs without awareness | `NEXT_PUBLIC_*` vars are baked into the Next.js bundle at build time. If you change them in Dokploy after build, the change won't apply until next build. Set them correctly before triggering build. | Always set `NEXT_PUBLIC_*` vars in Dokploy UI before rebuilding |
| Running containers as root | Security risk. If container is compromised, attacker has root on the container. | Create and use a non-root user in all Dockerfiles (shown in patterns above) |

---

## Stack Patterns by Variant

**If deploying to Dokploy with Dokploy-managed PostgreSQL (recommended):**
- Do not include a `db` service in production Dockerfiles
- Set `DATABASE_URL` as a service-level env var in Dokploy UI for the backend application
- Dokploy's PostgreSQL connection string format: `postgresql+asyncpg://user:pass@hostname:5432/dbname`

**If using Dokploy Docker Compose deployment (all 3 services in one Compose file):**
- Define all 3 services in one root `docker-compose.yml`
- Use Traefik labels for domain routing per service
- Env vars in a single `.env` file managed by Dokploy
- Services can reach each other by service name (e.g., `http://backend:8000` from frontend during SSR)
- Better when services need internal communication without going through public URLs

**If using Dokploy Application deployment (3 separate apps — recommended approach):**
- Each service has its own Dockerfile
- Deployed and updated independently (update backend without redeploying frontends)
- Services communicate via public URLs (not internal Docker network)
- Better for different update cadences per service and independent rollbacks

**If Next.js frontend calls the backend during SSR/build time:**
- `NEXT_PUBLIC_API_URL` must be a public HTTPS URL (e.g., `https://api.spectra.example.com`)
- Build-time vars are baked into the JS bundle — set them in Dokploy before triggering a build
- Avoid internal Docker hostnames for `NEXT_PUBLIC_*` vars (they won't resolve outside the container build context)

**If the admin frontend must be network-isolated (Tailscale VPN access only):**
- Deploy admin frontend as a separate Dokploy Application
- Configure its domain to only be accessible on Tailscale network
- No code changes needed — isolation is at the infrastructure/DNS level

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Next.js 16.1.6 | Node.js 20.9+ minimum, Node.js 22 LTS recommended | Confirmed in official upgrade guide (verified 2026-02-16). Node 18 is EOL and unsupported by Next.js 16. |
| asyncpg 0.31.0 | Python 3.9–3.13 | manylinux binary wheels available. No build tools needed in `python:3.12-slim`. |
| psycopg[binary] 3.3.x | Python 3.8–3.13 | Binary package bundles its own libpq. No system `libpq-dev` needed. ARM64 and x86-64 wheels available as of Dec 2025. |
| uv (latest) | Python 3.8+ | `uv sync --locked` requires `uv.lock` present. Project already has one. `--compile-bytecode` flag recommended for production startup speed. |
| Docker Compose v2 (CLI v5.0.2) | Docker Engine 23+ | `docker compose` (no hyphen). `version:` field is obsolete. No schema version needed. |
| Dokploy v0.26.x | Docker Engine 23+ | Installs Traefik v3.5+ and Docker automatically. Self-hosted on VPS via one-liner install script. |
| `python:3.12-slim` | glibc 2.36+ (Debian bookworm) | All asyncpg and psycopg manylinux2014 (glibc 2.17+) wheels are compatible. |
| `node:22-alpine` | Alpine Linux 3.21, musl libc 1.2.5 | Next.js 16 has no native modules requiring glibc. Safe to use Alpine for Node.js apps. |

---

## Installation

No npm or pip packages are installed for the Docker/Dokploy tooling itself. The setup work is creating configuration files.

```bash
# Create Dockerfiles (one per service):
# backend/Dockerfile
# frontend/Dockerfile
# admin-frontend/Dockerfile

# Create .dockerignore (one per service):
# backend/.dockerignore
# frontend/.dockerignore
# admin-frontend/.dockerignore

# Create local dev Compose file:
# docker-compose.yml (project root)

# Modify next.config.ts in both frontends:
# Add: output: 'standalone'

# Install Dokploy on VPS (one-time server setup):
curl -sSL https://dokploy.com/install.sh | sh
# Opens on port 3000 by default, configure at http://<server-ip>:3000

# After Dokploy is running, create 3 Applications via Dokploy UI.
# No CLI or config files needed for Dokploy itself.
```

---

## Sources

- Dokploy official docs — build types, env var scopes, volumes, application model — HIGH confidence
  - https://docs.dokploy.com/docs/core/applications/build-type
  - https://docs.dokploy.com/docs/core/variables
  - https://docs.dokploy.com/docs/core/docker-compose
  - https://docs.dokploy.com/docs/core/applications/advanced
- Next.js official upgrade guide (verified 2026-02-16) — Node.js 20.9+ minimum requirement confirmed — HIGH confidence
  - https://nextjs.org/docs/app/guides/upgrading/version-16
- Next.js official deploying guide — Docker + standalone output — HIGH confidence
  - https://nextjs.org/docs/app/getting-started/deploying
- uv official Docker integration guide — multi-stage build pattern with uv — HIGH confidence
  - https://docs.astral.sh/uv/guides/integration/docker/
- Docker official docs — `version:` field obsolete in Compose v2 — HIGH confidence
  - https://docs.docker.com/reference/compose-file/version-and-name/
- pythonspeed.com "Best Docker base image for Python" (February 2026) — python:3.12-slim recommendation — HIGH confidence
  - https://pythonspeed.com/articles/base-image-python-docker-images/
- psycopg official docs — binary package bundles libpq — HIGH confidence
  - https://www.psycopg.org/psycopg3/docs/basic/install.html
- WebSearch: Dokploy v0.26.7 latest release confirmed (2026-01-31) — MEDIUM confidence
- WebSearch: Docker Compose CLI v5.0.2 latest (2026-02-03) — MEDIUM confidence

---

*Stack research for: Docker + Dokploy deployment of Spectra (FastAPI + 2x Next.js)*
*Researched: 2026-02-18*
