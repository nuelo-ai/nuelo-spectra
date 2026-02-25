# Phase 34: Dockerfiles and Entrypoint - Research

**Researched:** 2026-02-18
**Domain:** Docker containerization (Python backend + Next.js frontends)
**Confidence:** HIGH

## Summary

This phase creates three production Docker images: a Python backend (FastAPI/uvicorn), a public Next.js frontend, and an admin Next.js frontend. The backend uses `python:3.12-slim` with `uv` for dependency management in a multi-stage build, includes an entrypoint script that waits for PostgreSQL and runs Alembic migrations before starting uvicorn. Both frontends use `node:22-alpine` with Next.js standalone output in 3-stage builds. Each service gets its own `.dockerignore` to prevent secrets from leaking into image layers.

A critical finding from this research: **`next.config.ts` rewrites are evaluated at build time, not runtime**. The current `BACKEND_URL` approach using `process.env.BACKEND_URL` in rewrites will bake the value at `docker build` time. This is acceptable for the Dokploy deployment model (each service builds independently), but the value must be provided as a build arg, not a runtime env var.

**Primary recommendation:** Use the official `uv` Docker pattern for the backend (multi-stage with `--no-editable`), the Vercel-recommended Next.js standalone Docker pattern for both frontends, and install `postgresql-client` via apt-get in the backend image for `pg_isready`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOCK-01 | `.dockerignore` files excluding secrets, build artifacts, venvs | Standard Docker security pattern; documented exclusion list below |
| DOCK-02 | `docker-entrypoint.sh` with pg_isready loop, alembic migrate, exec uvicorn | pg_isready from postgresql-client package; alembic env.py uses asyncpg; entrypoint pattern documented |
| DOCK-03 | Backend Dockerfile: python:3.12-slim, uv multi-stage, non-root, healthcheck, volume | Official uv Docker guide provides exact pattern; verified with astral docs |
| DOCK-04 | Frontend Dockerfile: node:22-alpine, 3-stage standalone, non-root, healthcheck | Vercel official with-docker example provides exact pattern; health route exists at /api/health |
| DOCK-05 | Admin Dockerfile: identical pattern to DOCK-04 | Same Dockerfile pattern; admin-frontend has same next.config.ts structure |
</phase_requirements>

## Standard Stack

### Core
| Image | Version | Purpose | Why Standard |
|-------|---------|---------|--------------|
| python:3.12-slim | 3.12 (bookworm) | Backend base | glibc required for asyncpg/psycopg binary wheels; Alpine incompatible |
| node:22-alpine | 22 LTS | Frontend base | Alpine safe for Next.js; saves ~100MB vs debian |
| ghcr.io/astral-sh/uv:latest | latest | Python package installer | Copies uv binary into builder stage; 10-100x faster than pip |

### Supporting
| Package | Purpose | When to Use |
|---------|---------|-------------|
| postgresql-client | Provides `pg_isready` binary | Backend entrypoint for DB readiness check |
| libc6-compat | Alpine compatibility shim | Frontend images (required by some Node native modules) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| postgresql-client (apt) | Pure Python TCP socket check | Avoids apt-get but ~20 lines of Python; pg_isready is battle-tested and 2 lines |
| uv multi-stage | pip install | Works but 10x slower builds and no lockfile verification |

**Installation (backend Dockerfile):**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
```

## Architecture Patterns

### Recommended Project Structure (Dockerfiles at project root)
```
spectra-dev/
├── Dockerfile.backend          # Backend image
├── Dockerfile.frontend         # Public frontend image
├── Dockerfile.admin            # Admin frontend image
├── backend/
│   ├── .dockerignore           # Backend-specific ignores
│   ├── docker-entrypoint.sh    # Entrypoint script
│   ├── pyproject.toml
│   ├── uv.lock
│   └── app/
├── frontend/
│   ├── .dockerignore           # Frontend-specific ignores
│   ├── package.json
│   └── src/
└── admin-frontend/
    ├── .dockerignore           # Admin-specific ignores
    ├── package.json
    └── src/
```

**Note on Dockerfile location:** Dockerfiles live at project root because both frontends and backend are subdirectories. Build context is the project root (`.`), and each Dockerfile uses relative paths from root. The `.dockerignore` files go in each service's subdirectory.

**IMPORTANT correction:** `.dockerignore` should be at the build context root (project root), not in subdirectories. Since `docker build -f Dockerfile.backend .` uses `.` as context, the `.dockerignore` at project root applies. Use one `.dockerignore` at root OR use the newer `.dockerignore` per-Dockerfile feature (Docker BuildKit: `.dockerignore` named `Dockerfile.backend.dockerignore`).

### Pattern 1: Backend Multi-Stage with uv
**What:** Two-stage build: builder installs deps with uv, runtime copies only the venv
**When to use:** All Python projects using uv
**Example:**
```dockerfile
# Source: https://docs.astral.sh/uv/guides/integration/docker/
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install dependencies first (better caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy source and install project
COPY backend/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Runtime stage
FROM python:3.12-slim
# Install pg_isready for entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app
COPY backend/docker-entrypoint.sh /app/docker-entrypoint.sh
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

RUN chmod +x /app/docker-entrypoint.sh

VOLUME ["/app/uploads"]
USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

### Pattern 2: Next.js 3-Stage Standalone
**What:** deps stage, builder stage, runner stage -- minimal final image
**When to use:** Next.js 16 with `output: 'standalone'`
**Example:**
```dockerfile
# Source: https://github.com/vercel/next.js/tree/canary/examples/with-docker
FROM node:22-alpine AS base

# Stage 1: Install dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Stage 2: Build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

ARG BACKEND_URL=http://localhost:8000
ENV BACKEND_URL=${BACKEND_URL}

RUN npm run build

# Stage 3: Production
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

### Pattern 3: Entrypoint Script
**What:** Shell script that waits for PostgreSQL, runs migrations, then exec's uvicorn
**When to use:** Backend container startup
**Example:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Parse DB host/port from DATABASE_URL
# Format: postgresql+asyncpg://user:pass@host:port/dbname
DB_HOST="${DB_HOST:-$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')}"
DB_PORT="${DB_PORT:-$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')}"
DB_PORT="${DB_PORT:-5432}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
    echo "PostgreSQL not ready, retrying in 2s..."
    sleep 2
done

echo "PostgreSQL is ready. Running migrations..."
cd /app
# alembic needs to run from the directory with alembic.ini
.venv/bin/python -m alembic upgrade head

echo "Starting uvicorn..."
exec .venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-1}"
```

### Anti-Patterns to Avoid
- **Baking .env files into images:** Use `.dockerignore` to exclude; secrets via runtime env vars only
- **Running as root:** Always create non-root user; security scanners flag root containers
- **Using `CMD` instead of `exec` in entrypoint:** Without `exec`, uvicorn runs as child of bash (PID != 1), missing SIGTERM for graceful shutdown
- **Installing dev dependencies in production image:** Use `--no-install-project` and `--no-editable` for uv; `npm ci` (not `npm install`) for Node
- **Single-stage builds:** Bloats image with build tools, compilers, caches

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PostgreSQL readiness check | Custom Python TCP socket loop | `pg_isready` from postgresql-client | Handles auth methods, SSL, connection params correctly |
| Python dependency install in Docker | pip install -r requirements.txt | uv sync --locked | Lockfile verification, 10x faster, reproducible builds |
| Next.js production server | Custom Node.js server | `node server.js` (standalone output) | Auto-generated by Next.js, handles all framework features |
| Docker health checks | Custom monitoring | HEALTHCHECK instruction | Built into Docker, works with orchestrators |
| .dockerignore patterns | Manual file exclusion | Standard .dockerignore file | Prevents accidental secret inclusion |

**Key insight:** Docker containerization has well-established patterns. Every component here has a "blessed" approach from the tool's official documentation.

## Common Pitfalls

### Pitfall 1: next.config.ts Rewrites are Build-Time, Not Runtime
**What goes wrong:** Developer expects `BACKEND_URL` in `rewrites()` to be read at container startup, but it is baked at `docker build` time
**Why it happens:** `next.config.ts` is evaluated during `next build` and the rewrite rules are serialized into the build output
**How to avoid:** Pass `BACKEND_URL` as a Docker build arg (`ARG BACKEND_URL`), set it via `ENV` before `npm run build`. For true runtime flexibility, use Next.js middleware instead of rewrites
**Warning signs:** API calls work in dev but fail in production container; changing env var at `docker run` has no effect
**Source:** [Confirmed by Next.js team](https://github.com/vercel/next.js/issues/21888)

### Pitfall 2: Alembic Needs Database URL Without asyncpg Prefix
**What goes wrong:** `alembic upgrade head` fails because `env.py` already handles the URL via `get_settings()`
**Why it happens:** The alembic `env.py` in this project uses `async_engine_from_config` with the `postgresql+asyncpg://` URL from settings
**How to avoid:** Ensure `DATABASE_URL` env var is set in the container (same as development); the existing `env.py` handles it correctly via `get_settings()`
**Warning signs:** Migration failures on container startup

### Pitfall 3: uv venv Path Mismatch Between Stages
**What goes wrong:** Python can't find installed packages after copying .venv from builder
**Why it happens:** Virtual environment paths are baked into the venv; if WORKDIR differs between stages, imports break
**How to avoid:** Use the same WORKDIR (`/app`) in both builder and runtime stages; use `--no-editable` so no source references remain
**Warning signs:** `ModuleNotFoundError` on container startup
**Source:** [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/)

### Pitfall 4: Missing .next/static in Standalone Copy
**What goes wrong:** CSS/JS assets return 404 in production
**Why it happens:** Next.js standalone output doesn't include `.next/static` -- it must be copied separately
**How to avoid:** Always copy both `.next/standalone` AND `.next/static` into the runner stage
**Warning signs:** Unstyled page, console 404 errors for _next/static files

### Pitfall 5: HOSTNAME Must Be 0.0.0.0 in Container
**What goes wrong:** Container health checks pass internally but fail from Docker network / external
**Why it happens:** Next.js defaults to listening on 127.0.0.1, not accessible from outside container
**How to avoid:** Set `ENV HOSTNAME="0.0.0.0"` in Dockerfile
**Warning signs:** `wget` or `curl` to container port times out from host

### Pitfall 6: Docker BuildKit Cache Mount Requires BuildKit
**What goes wrong:** `--mount=type=cache` syntax error during build
**Why it happens:** Cache mounts require Docker BuildKit (default since Docker 23.0+)
**How to avoid:** Ensure `DOCKER_BUILDKIT=1` or use Docker 23.0+; add `# syntax=docker/dockerfile:1` at top of Dockerfile
**Warning signs:** Parse error on `RUN --mount=type=cache`

### Pitfall 7: pg_isready Not Installed in python:3.12-slim
**What goes wrong:** Entrypoint script fails with `pg_isready: command not found`
**Why it happens:** `python:3.12-slim` does not include PostgreSQL client tools
**How to avoid:** Install `postgresql-client` via apt-get in the runtime stage
**Warning signs:** Container crashes immediately on startup

## Code Examples

### .dockerignore (Root Level)
```
# Secrets
**/.env
**/.env.*
!**/.env.example

# Python
**/.venv
**/venv
**/__pycache__
**/*.pyc
**/*.pyo

# Node
**/node_modules
**/.next

# Uploads (user data)
**/uploads

# Development
**/.git
**/.gitignore
**/README.md
**/*.md
**/.planning
**/tests
**/.pytest_cache

# IDE
**/.vscode
**/.idea
```

### docker-entrypoint.sh (Backend)
```bash
#!/usr/bin/env bash
set -euo pipefail

# Extract DB host/port from DATABASE_URL
# Handles: postgresql+asyncpg://user:pass@host:port/dbname
# Also handles: postgresql://user:pass@host:port/dbname
DB_HOST="${DB_HOST:-$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')}"
DB_PORT="${DB_PORT:-$(echo "$DATABASE_URL" | sed -E 's|.*@[^:]+:([0-9]+)/.*|\1|')}"
DB_PORT="${DB_PORT:-5432}"

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

retries=0
max_retries=30
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$max_retries" ]; then
        echo "[entrypoint] ERROR: PostgreSQL not ready after ${max_retries} attempts. Exiting."
        exit 1
    fi
    echo "[entrypoint] PostgreSQL not ready (attempt ${retries}/${max_retries}), retrying in 2s..."
    sleep 2
done

echo "[entrypoint] PostgreSQL is ready. Running migrations..."
/app/.venv/bin/python -m alembic upgrade head

echo "[entrypoint] Migrations complete. Starting uvicorn..."
exec /app/.venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-1}"
```

### BACKEND_URL as Build Arg in Frontend Dockerfiles
```dockerfile
# In builder stage:
ARG BACKEND_URL=http://localhost:8000
ENV BACKEND_URL=${BACKEND_URL}
RUN npm run build
```

At build time:
```bash
docker build -f Dockerfile.frontend --build-arg BACKEND_URL=http://backend:8000 .
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pip install | uv sync --locked | 2024 | 10-100x faster, reproducible |
| requirements.txt | pyproject.toml + uv.lock | 2024 | Lockfile verification, no drift |
| node:18 | node:22-alpine | 2024 (LTS) | Smaller image, current LTS |
| next start | node server.js (standalone) | Next.js 12+ | 97% smaller images |
| Custom wait-for-it.sh | pg_isready | Always available | Native PostgreSQL tool |

**Deprecated/outdated:**
- `serverRuntimeConfig`/`publicRuntimeConfig`: Removed from Next.js, do not use
- `pip freeze > requirements.txt`: Use `uv.lock` instead
- `node:XX-slim` for Next.js: Alpine is preferred (smaller, sufficient)

## Open Questions

1. **Build-arg vs middleware for BACKEND_URL**
   - What we know: Rewrites are build-time; build-arg works for Dokploy (one image per deploy)
   - What's unclear: Whether Dokploy rebuilds on env change or reuses images
   - Recommendation: Use build-arg for now (matches Dokploy model); document that middleware would be needed for true "build once, deploy many"

2. **uv.lock location relative to build context**
   - What we know: `uv.lock` is at `backend/uv.lock`, build context is project root
   - What's unclear: Whether `--mount=type=bind` works with relative paths from build context
   - Recommendation: Use `COPY backend/pyproject.toml backend/uv.lock ./` instead of bind mounts for simplicity; bind mounts add complexity with subdirectory contexts

3. **Alembic working directory in container**
   - What we know: `alembic.ini` has `script_location = %(here)s/alembic` and `prepend_sys_path = .`
   - What's unclear: Whether the entrypoint needs to `cd /app` before running alembic
   - Recommendation: Set WORKDIR to /app and copy alembic.ini + alembic/ directory there; run alembic from /app

## Sources

### Primary (HIGH confidence)
- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/) - Multi-stage pattern, env vars, cache mounts
- [Next.js official deploying docs](https://nextjs.org/docs/app/getting-started/deploying) - Docker template reference
- [Next.js self-hosting guide](https://nextjs.org/docs/app/guides/self-hosting) - Runtime env vars, HOSTNAME config
- [Vercel with-docker example](https://github.com/vercel/next.js/tree/canary/examples/with-docker) - Official 3-stage Dockerfile
- [Next.js issue #21888](https://github.com/vercel/next.js/issues/21888) - Confirmation that rewrites are build-time

### Secondary (MEDIUM confidence)
- [Depot.dev uv Dockerfile guide](https://depot.dev/docs/container-builds/how-to-guides/optimal-dockerfiles/python-uv-dockerfile) - Verified against official uv docs
- WebSearch results for pg_isready in python:3.12-slim - Confirmed apt-get install postgresql-client works

### Tertiary (LOW confidence)
- None - all findings verified against official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All base images and tools are explicitly specified in prior decisions and verified against official docs
- Architecture: HIGH - Official patterns from uv docs and Vercel examples; project structure examined in detail
- Pitfalls: HIGH - Build-time rewrites confirmed by Next.js team; uv path issues documented in official guide
- Entrypoint: HIGH - pg_isready pattern is widely documented; alembic env.py examined and understood

**Research date:** 2026-02-18
**Valid until:** 2026-04-18 (stable technologies, 60-day validity)
