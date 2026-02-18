# Feature Research: Docker and Dokploy Deployment (v0.5.1)

**Domain:** Docker containerization and Dokploy deployment for FastAPI + Next.js multi-service app
**Researched:** 2026-02-18
**Confidence:** HIGH (official Next.js docs verified, Dokploy docs verified, codebase inspected)
**Supersedes:** Previous FEATURES.md (v0.5 Admin Portal features, 2026-02-16)

---

## Executive Summary

Spectra v0.5.1 packages an existing, fully functional production app into Docker containers for Dokploy deployment. This is a "wrap the existing app" milestone, not a "build new features" milestone. The risk is not capability -- Docker + Dokploy is well-understood -- the risk is configuration correctness: wrong environment variable strategy, broken SSE streaming through proxies, missed volume mounts, or misconfigured inter-service networking.

Three services need Dockerfiles: FastAPI backend, Next.js public frontend, Next.js admin frontend. The backend uses uv for dependency management, so multi-stage builds leverage uv's venv copy pattern. Both Next.js apps use Next.js standalone output mode to reduce image size dramatically (from ~7GB to ~300MB typical). A Docker Compose file covers local development with all services + PostgreSQL.

**Critical discovery from codebase inspection:** Both frontends currently use Next.js rewrites (`/api/*` -> backend) for almost all API calls, meaning they do NOT use `NEXT_PUBLIC_API_URL`. However, there are two hardcoded `localhost:8000` direct fetch calls in the public frontend (`useSSEStream.ts` line 112 and `register/page.tsx` line 26) that bypass the rewrite proxy. These must be fixed as part of this milestone -- they will fail in Docker where the backend is not at `localhost:8000`.

**NEXT_PUBLIC_ variable strategy for Spectra:** Because both frontends already use relative `/api/` paths (proxied via Next.js rewrites), the `NEXT_PUBLIC_API_URL` approach is NOT needed for the rewrite-based API calls. The rewrite destination URL in `next.config.ts` IS the only thing that needs updating for Docker -- it is a server-side Next.js config value read at build time, but the destination hostname is the Docker service name (e.g., `http://backend:8000`). For Dokploy production, because services communicate over the dokploy-network, the rewrite destination changes to the backend's internal Dokploy hostname.

---

## Service Architecture Reference

```
3 Dokploy services + 1 Dokploy-managed PostgreSQL:

  [public-frontend]     [admin-frontend]
     port 3000            port 3000 (container)
        |                      |
        | Next.js rewrite      | Next.js rewrite
        v                      v
     [backend]              [backend]
     port 8000
        |
     [PostgreSQL]  -- Dokploy-managed database
     [/app/uploads] -- Docker volume (file uploads persistence)
```

All three services connect to `dokploy-network`. Services reference each other by their Dokploy application service name as DNS hostname.

---

## Table Stakes

Features every production Docker deployment must have. Missing any of these means the deployment is not production-ready.

### Backend (FastAPI)

| Feature | Why Required | Complexity | Dependencies on Existing Code |
|---------|-------------|------------|-------------------------------|
| **Multi-stage Dockerfile (uv-based)** | Single-stage images are 3-5x larger, include build tools in production, and are slow to rebuild. uv-based builds are the established Python production pattern as of 2025. | LOW | Backend uses uv (uv.lock exists). Builder stage: install uv, sync deps. Runtime stage: copy .venv only. Run as non-root `app` user. |
| **Non-root user in container** | Running as root inside Docker is a security anti-pattern. If the container is compromised, attacker gets root access. Industry standard is a non-root `app` or `appuser`. | LOW | No existing dependency. Add `RUN adduser --system --uid 1001 app` and `USER app` before CMD. |
| **HEALTHCHECK instruction in Dockerfile** | Dokploy uses HEALTHCHECK to determine if a container is healthy before routing traffic and for auto-restart decisions. The backend already has `GET /health` endpoint. | LOW | Backend already has `GET /health` at `app/routers/health.py`. Uses `curl -f http://localhost:8000/health`. |
| **Volume mount for uploads** | File uploads stored at `/app/uploads` (configured via `UPLOAD_DIR` env var) must persist across container restarts and redeploys. Without a volume, all user-uploaded files are lost on every deploy. | LOW | Backend `config.py` has `upload_dir: str = "uploads"`. In Docker, mount `/app/uploads` as a named volume or bind mount. Set `UPLOAD_DIR=/app/uploads`. |
| **Environment variable injection (all secrets)** | `DATABASE_URL`, `SECRET_KEY`, `E2B_API_KEY`, `ANTHROPIC_API_KEY`, `SMTP_*`, `TAVILY_API_KEY` etc. must be injected via Dokploy environment variable UI, not baked into the image. | LOW | All config already in `app/config.py` via pydantic-settings. No code changes needed -- just populate Dokploy env vars. |
| **SPECTRA_MODE=public for backend** | Backend routes are conditionally mounted based on `SPECTRA_MODE`. For production, the backend serving both public and admin frontends should use `SPECTRA_MODE=dev` or separate backend instances per mode. For simplest single-backend deployment, use `SPECTRA_MODE=dev`. | LOW | `SPECTRA_MODE` already in `app/config.py`. Set to `dev` for single backend instance, or `public` for a public-only backend. |
| **ENABLE_SCHEDULER=true for backend** | APScheduler runs inside the backend process. Must be explicitly enabled in production via env var. APScheduler is already integrated in `app/scheduler.py` but defaults to `False`. | LOW | `enable_scheduler: bool = False` in `app/config.py`. Set `ENABLE_SCHEDULER=true` in Dokploy. |
| **CORS origins configured** | Backend `CORS_ORIGINS` env var must include the actual deployed frontend URLs. Without correct CORS, browser requests from production frontend to backend will fail with CORS error. | LOW | `cors_origins` in `app/config.py` accepts JSON array string. Set `CORS_ORIGINS=["https://app.example.com","https://admin.example.com"]`. |
| **Graceful shutdown (SIGTERM handling)** | FastAPI + uvicorn handle SIGTERM natively. The lifespan context manager in `main.py` already shuts down APScheduler and disposes the database engine on shutdown. No additional code needed, but the CMD must use uvicorn correctly so SIGTERM propagates (not shell form). | LOW | `main.py` already has lifespan context manager. Use `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (exec form, not shell form). |
| **Database connection via DATABASE_URL** | In Dokploy, PostgreSQL is a managed database with an internal hostname. `DATABASE_URL` must point to the internal Dokploy database hostname (not `localhost`). | LOW | `database_url: str` in `app/config.py`. Inject Dokploy's internal DB connection string. |

### Public Frontend (Next.js)

| Feature | Why Required | Complexity | Dependencies on Existing Code |
|---------|-------------|------------|-------------------------------|
| **Multi-stage Dockerfile (standalone mode)** | Next.js standalone output (`output: 'standalone'` in next.config.ts) reduces image from ~7GB to ~300MB by tracing only required dependencies. Official Next.js Docker pattern. | LOW | Must add `output: 'standalone'` to `frontend/next.config.ts`. Three-stage build: deps -> builder -> runner. |
| **Non-root user in container** | Same security rationale as backend. Next.js official Dockerfile example uses `nextjs:nodejs` non-root user with uid 1001. | LOW | Add `RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs` and `USER nextjs`. |
| **HEALTHCHECK instruction** | Dokploy needs to verify the Next.js app is serving before routing traffic. Next.js has no built-in `/health` endpoint -- must add one as an API route. | LOW | Need to create `frontend/src/app/api/health/route.ts` that returns `{status: "ok"}`. Uses Next.js App Router route handler pattern. |
| **Backend URL in Next.js rewrite (server-side)** | Both frontends proxy `/api/*` to the backend via `next.config.ts` rewrites. The destination URL (`http://localhost:8000`) must be changed to the backend's Docker service hostname. This is a server-side config value -- NOT a NEXT_PUBLIC_ variable. | MEDIUM | Change `frontend/next.config.ts` rewrite destination from `http://localhost:8000` to env-var-driven value: `process.env.BACKEND_URL ?? 'http://localhost:8000'`. Then set `BACKEND_URL=http://backend:8000` in Docker. |
| **SSE stream URL fix (hardcoded localhost bug)** | `frontend/src/hooks/useSSEStream.ts` line 112 has `fetch('http://localhost:8000/chat/...')` hardcoded. This bypasses the Next.js rewrite. In Docker, this call fails. Must fix to use relative `/api/chat/sessions/${sessionId}/stream` path OR use a `NEXT_PUBLIC_BACKEND_URL` env var. | MEDIUM | Direct code fix in `useSSEStream.ts`. SSE via Next.js rewrite works -- the rewrite is a server-side proxy, not a client-side redirect. Change to `fetch('/api/chat/sessions/${sessionId}/stream', ...)`. |
| **Signup status URL fix (hardcoded localhost bug)** | `frontend/src/app/(auth)/register/page.tsx` line 26 has `fetch('http://localhost:8000/auth/signup-status')` hardcoded. Same issue. Must fix. | LOW | Change to `fetch('/api/auth/signup-status')`. Same relative-path pattern as all other API calls. |
| **NODE_ENV=production** | Next.js enables production optimizations only when `NODE_ENV=production`. In standalone mode, set at runtime (not build time). | LOW | Set `ENV NODE_ENV=production` in runner stage of Dockerfile. |
| **PORT and HOSTNAME env vars** | Next.js standalone `server.js` reads `PORT` and `HOSTNAME` env vars. Must set `HOSTNAME=0.0.0.0` so server binds to all interfaces (not just localhost), making it reachable inside Docker. | LOW | Set `ENV PORT=3000` and `ENV HOSTNAME=0.0.0.0` in Dockerfile runner stage. |

### Admin Frontend (Next.js)

| Feature | Why Required | Complexity | Dependencies on Existing Code |
|---------|-------------|------------|-------------------------------|
| **Multi-stage Dockerfile (standalone mode)** | Same rationale as public frontend. Admin frontend in `admin-frontend/` is a separate Next.js app. | LOW | Must add `output: 'standalone'` to `admin-frontend/next.config.ts`. Same 3-stage pattern. |
| **Non-root user in container** | Same as public frontend. | LOW | Same pattern: nextjs:nodejs non-root user. |
| **HEALTHCHECK instruction** | Same need as public frontend. Admin frontend needs its own health endpoint. | LOW | Create `admin-frontend/src/app/api/health/route.ts`. |
| **Backend URL in Next.js rewrite** | `admin-frontend/next.config.ts` rewrites `/api/*` to `http://localhost:8000/api/*`. Must be updated for Docker service name. | MEDIUM | Change rewrite destination to `${process.env.BACKEND_URL ?? 'http://localhost:8000'}/api/*`. Set `BACKEND_URL=http://backend:8000` in Docker. |
| **SPECTRA_MODE context** | Backend must be in `admin` or `dev` mode to serve admin routes. The admin frontend connects to the same backend as the public frontend (single backend in `dev` mode), or a separate backend in `admin` mode. For simplest deployment: single backend in `dev` mode serves both. | LOW | No frontend code change. Backend env var `SPECTRA_MODE=dev`. |
| **Admin CORS origin** | Backend `ADMIN_CORS_ORIGIN` must be set to the admin frontend's production URL. | LOW | Set `ADMIN_CORS_ORIGIN=https://admin.example.com` in backend Dokploy env vars. |

### Shared / Cross-Service

| Feature | Why Required | Complexity | Dependencies on Existing Code |
|---------|-------------|------------|-------------------------------|
| **Docker Compose for local dev** | Single-command local development with all services + PostgreSQL. Developers must be able to run the full stack locally via `docker compose up`. | MEDIUM | New `docker-compose.yml` at repo root. Services: `backend`, `frontend`, `admin-frontend`, `postgres`. Backend depends on postgres. Both frontends depend on backend. |
| **DEPLOYMENT.md guide** | Deployment of a multi-service app to Dokploy is not self-evident. Step-by-step guide covering Dokploy project creation, 3 service configurations, environment variables, volume setup, domain assignment, and SSL. | LOW | New document. No code dependencies. |
| **Port assignments** | Standardized ports prevent conflicts. Backend: 8000. Public frontend: 3000. Admin frontend: 3001 (host-mapped, container port is 3000). | LOW | In Docker Compose, map `3001:3000` for admin-frontend. In Dokploy, each service gets its own container and domain -- port conflicts don't apply at container level. |
| **Restart policy** | Containers should auto-restart on crash. Dokploy supports restart policies (`always`, `on-failure`, etc.). Set `unless-stopped` for all services. | LOW | Dokploy UI restart policy setting. In Docker Compose, `restart: unless-stopped`. |

---

## Differentiators

Production hardening extras beyond the minimum. Each is independently valuable for a single-developer project.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Build cache optimization (Docker layer ordering)** | Dependency installation in a separate layer means code changes don't trigger dep reinstalls. Reduces build time from 3-5 min to 30-60 sec after first build. | LOW | In backend Dockerfile: COPY pyproject.toml uv.lock FIRST, RUN uv sync, THEN COPY app/. In frontend Dockerfile: COPY package.json package-lock.json FIRST, RUN npm ci, THEN COPY src/. Official best practice. |
| **Alembic migration in Docker entrypoint** | Running `alembic upgrade head` before starting uvicorn ensures database schema is always up to date on deployment. Prevents "table doesn't exist" errors on first deploy. | LOW | Backend Dockerfile CMD or entrypoint.sh: `alembic upgrade head && uvicorn app.main:app ...`. Alternatively, run migration as a separate Dokploy job before deploying. |
| **libc6-compat in Alpine Next.js image** | Alpine Linux with Node.js sometimes requires `libc6-compat` for native modules. Without it, certain npm packages fail at startup. Official Next.js Dockerfile includes it. | LOW | `RUN apk add --no-cache libc6-compat` in deps stage. One line. |
| **NEXT_TELEMETRY_DISABLED=1** | Next.js collects anonymous usage telemetry. In production Docker containers, this creates unnecessary outbound network calls at build time and startup. | LOW | `ENV NEXT_TELEMETRY_DISABLED=1` in Dockerfile builder and runner stages. |
| **curl installed for health checks** | The backend Docker image (Python slim) does not include curl by default. HEALTHCHECK instruction using `curl` requires it to be installed. | LOW | `RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*` in runtime stage. Alternatively, use Python urllib for health check (no extra dep needed). |
| **.dockerignore files** | Without .dockerignore, the Docker build context includes `node_modules/`, `.next/`, `__pycache__/`, `.env` files, and `venv/`. This slows build and can leak secrets. | LOW | New `.dockerignore` for each service directory. Key exclusions: `node_modules`, `.next`, `__pycache__`, `*.pyc`, `.env`, `venv`, `uploads`. |
| **UV_COMPILE_BYTECODE=1** | Compiles Python to .pyc at build time for faster container startup. Production-only optimization. | LOW | `ENV UV_COMPILE_BYTECODE=1` in builder stage. |
| **ReadOnly root filesystem (partial)** | Limit writable areas to explicit volume mounts and `/tmp`. Reduces attack surface. Only applies to backend (needs `/app/uploads` writable). Frontend containers can be fully read-only with `/tmp` tmpfs. | MEDIUM | Requires carefully mounting all writable paths. Skip for v0.5.1 -- too complex for marginal single-instance benefit. |
| **Structured JSON logging** | Container logs go to stdout/stderr and are captured by Dokploy's log viewer. JSON-structured logs are more parseable but require additional config. | MEDIUM | Backend currently uses Python `logging.basicConfig`. Skip for v0.5.1 -- existing logs are readable and the product has 1 user (the developer). Add when log volume increases. |

---

## Anti-Features

Features to explicitly NOT build. These seem helpful but add complexity for no real benefit at single-developer scale.

| Anti-Feature | Why Requested | Why It's Wrong Here | Alternative |
|--------------|---------------|---------------------|-------------|
| **Runtime NEXT_PUBLIC_ injection via entrypoint script** | "One Docker image deployable to multiple environments without rebuilding" -- the classic argument for runtime env injection. | Spectra's frontends already use relative `/api/` paths via Next.js rewrites. They do NOT use `NEXT_PUBLIC_API_URL`. The only environment-specific config is the backend URL in `next.config.ts`, which is a server-side value read at startup (not baked at build time in standalone mode's `server.js`). A sed-based entrypoint to replace bundle strings is fragile, hard to debug, and unnecessary. | Set `BACKEND_URL` as a server-side env var (not NEXT_PUBLIC_). Next.js rewrites destination reads `process.env.BACKEND_URL` at startup. No rebuild needed between environments -- just set different env vars. |
| **Gunicorn + uvicorn workers** | "Production needs multiple workers for performance." | Spectra has one production instance. APScheduler runs inside the process. Multiple uvicorn workers with APScheduler would cause duplicate scheduled jobs. E2B sandbox calls are the bottleneck, not Python workers. Multi-worker adds scheduler complexity for zero throughput benefit at current scale. | Single uvicorn worker: `uvicorn app.main:app --workers 1`. If horizontal scaling becomes needed, move APScheduler to Redis-backed Celery Beat instead of in-process. |
| **Separate Docker image registry with CI/CD push** | "Build images in GitHub Actions, push to GHCR, Dokploy pulls from registry." | Valid for teams. Unnecessary for single-developer project. Dokploy can build directly from the Git repository on the Dokploy server. Eliminates GitHub Actions setup, registry authentication, and additional moving parts. | Dokploy builds from Git repo directly using the Dockerfile. No external registry needed. |
| **Redis for session state and token revocation** | "Move in-memory token revocation and admin lockout to Redis for multi-instance safety." | PROJECT.md documents in-memory token revocation and admin lockout as known limitations. Adding Redis for a single-instance deployment is over-engineering. The "limitation" only matters at 2+ instances. | Keep in-memory. Accept the single-instance limitation. Document it in DEPLOYMENT.md. Add Redis if/when horizontal scaling is needed. |
| **Kubernetes / Docker Swarm** | "Container orchestration for high availability." | Dokploy is the deployment target. Dokploy runs Docker Swarm under the hood, but it manages that. Using raw Swarm configs or Kubernetes configs would bypass Dokploy and add massive complexity. | Use Dokploy's built-in service management. Dokploy handles swarm details internally. |
| **Separate nginx reverse proxy container** | "Put nginx in front of each service for static file serving and caching." | Next.js standalone mode includes its own Node.js HTTP server that serves static files correctly. Adding nginx adds a service, config, and potential SSE streaming issues (nginx requires `proxy_buffering off` for SSE). Dokploy's Traefik already handles TLS termination and routing. | Let Dokploy Traefik handle routing. Next.js serves its own static files. No additional nginx needed. |
| **Multi-architecture Docker builds (arm64/amd64)** | "Build for both Mac M1 and Linux x86 servers." | The Dokploy server runs Linux x86. Development on M1 Mac can use the docker build with `--platform linux/amd64` flag. Multi-arch builds via buildx require additional CI setup. | Use `--platform linux/amd64` flag for local Mac builds targeting production. Or just build on the Dokploy server directly. |
| **Docker secrets / secret management** | "Use Docker secrets instead of environment variables for sensitive values." | Docker secrets (Swarm secrets) require Swarm mode and additional secret creation steps. Dokploy's environment variable injection is encrypted at rest and sufficient for a single-developer project. | Use Dokploy's environment variable UI. All env vars are stored encrypted. This is appropriate for the scale. |

---

## NEXT_PUBLIC_ Variable Strategy (Critical Decision)

This deserves its own section because it is the most commonly misunderstood Docker + Next.js topic.

### The Problem

`NEXT_PUBLIC_` variables are inlined as string literals into the JavaScript bundle at `next build` time. After building, they cannot be changed without rebuilding. This means if you bake `NEXT_PUBLIC_API_URL=http://localhost:8000` into the image, that URL is frozen forever in the built bundle.

### Spectra's Actual Situation

**Spectra does NOT need `NEXT_PUBLIC_API_URL`.** Here is why:

1. Both frontends use relative paths: `fetch('/api/...')` goes to the Next.js server, not directly to the backend
2. The Next.js server then proxies `/api/*` to the backend via the `rewrites()` in `next.config.ts`
3. The rewrite destination URL (`http://localhost:8000` in development) is read by `next.config.ts` on server startup -- this is NOT baked into the client bundle
4. In Docker, simply set `BACKEND_URL=http://backend:8000` as a server-side environment variable, and update `next.config.ts` to read `process.env.BACKEND_URL`

This means:
- Build the Docker image once (no environment-specific builds)
- Set `BACKEND_URL` at deploy time in Dokploy's env vars UI
- No `NEXT_PUBLIC_` variables needed at all

### The Two Hardcoded Bugs

Two places in the public frontend bypass the rewrite proxy and directly fetch `localhost:8000`:

1. `frontend/src/hooks/useSSEStream.ts` line 112: SSE stream endpoint
2. `frontend/src/app/(auth)/register/page.tsx` line 26: Signup status check

**Fix:** Change both to relative paths (`/api/...`). The Next.js rewrite proxy correctly handles SSE streams -- it streams the response through. No `NEXT_PUBLIC_` variable needed.

### When NEXT_PUBLIC_ IS Actually Needed

Only use `NEXT_PUBLIC_` if the frontend code runs entirely on the client side (pure SPA) with no server-side proxy. Since Spectra uses Next.js server-side rewrites, this does not apply.

---

## Feature Dependencies

```
next.config.ts BACKEND_URL support (both frontends)
    |
    +---> Docker Compose: sets BACKEND_URL=http://backend:8000
    |
    +---> Dokploy: sets BACKEND_URL=http://<backend-service-name>:8000

Hardcoded localhost:8000 fixes (useSSEStream.ts, register/page.tsx)
    |
    +---> Must be done BEFORE building Docker images
    |     (otherwise SSE streaming and signup status fail in Docker)

Backend Dockerfile
    |
    +---> needs: HEALTHCHECK (GET /health already exists)
    |
    +---> needs: Volume for /app/uploads
    |
    +---> needs: Alembic migration before uvicorn start

Next.js Health Endpoints (new API routes)
    |
    +---> Must be created BEFORE building Docker images
    |
    +---> frontend/src/app/api/health/route.ts  (new file)
    +---> admin-frontend/src/app/api/health/route.ts  (new file)

next.config.ts output: 'standalone' (both frontends)
    |
    +---> Required for Dockerfile to use .next/standalone
    |     Without this, standalone build output doesn't exist

Docker Compose (local dev)
    |
    +---> Depends on all three Dockerfiles working
    |
    +---> Uses postgres:16-alpine as managed DB substitute
```

### Build Order

1. Fix `useSSEStream.ts` and `register/page.tsx` hardcoded URLs
2. Add `output: 'standalone'` to both `next.config.ts` files
3. Update rewrite destination to use `process.env.BACKEND_URL` in both `next.config.ts` files
4. Create health check API routes in both frontends
5. Write Dockerfiles (backend, public frontend, admin frontend)
6. Write `docker-compose.yml` for local dev
7. Write `DEPLOYMENT.md`

Steps 1-4 are code changes. Steps 5-7 are new files.

---

## Port Assignments

| Service | Container Port | Local Dev Host Port | Dokploy |
|---------|---------------|--------------------|---------|
| Backend (FastAPI) | 8000 | 8000 | Assigned via Dokploy domain config |
| Public Frontend (Next.js) | 3000 | 3000 | Assigned via Dokploy domain config |
| Admin Frontend (Next.js) | 3000 | 3001 | Assigned via Dokploy domain config |
| PostgreSQL (local dev only) | 5432 | 5432 | Dokploy-managed, no host port needed |

In Dokploy, each service gets its own container and its own domain. Port conflicts are irrelevant -- each container's port 3000 is independent. The public frontend gets `app.example.com:443`, admin gets `admin.example.com:443`. Traefik handles TLS termination and routing.

---

## Health Check Requirements

### Backend Health Check (already exists)

```
GET /health
Returns: {"status": "healthy", "version": "0.1.0"}
HTTP 200

Dockerfile HEALTHCHECK:
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

`--start-period=30s` is important: the backend performs LLM provider validation at startup (can take 5-15 seconds). Without a start period, Docker marks the container unhealthy before it finishes starting.

### Public Frontend Health Check (needs to be created)

```
GET /api/health
Returns: {"status": "ok"}
HTTP 200

New file: frontend/src/app/api/health/route.ts

Dockerfile HEALTHCHECK:
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1
```

### Admin Frontend Health Check (needs to be created)

```
GET /api/health
Returns: {"status": "ok"}
HTTP 200

New file: admin-frontend/src/app/api/health/route.ts

Dockerfile HEALTHCHECK:
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1
```

---

## Dokploy-Specific Configuration

### Service Networking

All three services are deployed as separate Dokploy "Application" services within the same Dokploy project. They communicate via the `dokploy-network` Docker overlay network using service names as DNS hostnames.

Dokploy assigns each application a container name based on the service name. When the public frontend needs to reach the backend, it uses `http://backend:8000` (where `backend` is the Dokploy service name, not `localhost`).

**Key implication:** The `BACKEND_URL` environment variable set in each frontend Dokploy service must use the backend's Dokploy internal service name, not `localhost` and not the public domain.

### Managed PostgreSQL

Dokploy provides a managed PostgreSQL service with an internal connection URL. The backend's `DATABASE_URL` should use the internal Dokploy database hostname (displayed in Dokploy's database connection settings as "Internal Host"). This keeps database traffic inside the Docker network.

### Volumes for File Uploads

The backend needs a persistent volume mounted at `/app/uploads`. Configure in Dokploy's advanced settings > Volumes. Use a Docker-managed volume (not a bind mount) for reliability across server moves.

### Environment Variable Scoping (Dokploy)

Dokploy supports three variable scopes:
- **Project-level**: Shared across all services (e.g., database connection string)
- **Service-level**: Specific to one service (e.g., `SPECTRA_MODE`, `E2B_API_KEY`)

For Spectra, use project-level variables for shared config and service-level variables for service-specific secrets.

---

## MVP Definition (This Milestone)

### Must Have for Functioning Docker Deployment

1. **Fix hardcoded `localhost:8000` in public frontend** (useSSEStream.ts, register/page.tsx) -- without this, SSE chat streaming fails in Docker
2. **Add `output: 'standalone'` to both next.config.ts files** -- required for Next.js Docker images
3. **Update rewrite destinations to use `BACKEND_URL` env var** -- required for Docker service communication
4. **Create health check route in both frontend apps** -- required for Dokploy health checks
5. **Backend Dockerfile** (multi-stage, uv-based, non-root user, healthcheck, volume at /app/uploads)
6. **Public Frontend Dockerfile** (3-stage standalone, non-root user, healthcheck)
7. **Admin Frontend Dockerfile** (3-stage standalone, non-root user, healthcheck)
8. **docker-compose.yml for local dev** (all 3 services + postgres, with correct env vars and volumes)
9. **DEPLOYMENT.md** (step-by-step Dokploy deployment guide)

### Add During Development (v0.5.1)

- **Alembic migration in backend CMD** (run `alembic upgrade head` before uvicorn)
- **.dockerignore for each service**
- **Build cache layer optimization** (copy dependency files before app code)
- **NEXT_TELEMETRY_DISABLED=1** (minor but good practice)

### Defer (Not This Milestone)

- **Redis for in-memory state** -- documented limitation, not urgent
- **CI/CD image registry push** -- Dokploy direct-from-git is sufficient
- **Structured JSON logging** -- current logging is readable
- **Read-only root filesystem** -- security enhancement, complex to configure

---

## Feature Prioritization Matrix

| Feature | Deployment Value | Implementation Cost | Priority |
|---------|-----------------|---------------------|----------|
| Fix hardcoded localhost:8000 (2 files) | CRITICAL | LOW | P1 |
| Backend Dockerfile | HIGH | LOW | P1 |
| Public frontend Dockerfile | HIGH | LOW | P1 |
| Admin frontend Dockerfile | HIGH | LOW | P1 |
| output: 'standalone' in next.config.ts | HIGH | LOW | P1 |
| BACKEND_URL in next.config.ts rewrites | HIGH | LOW | P1 |
| Health check API routes (both frontends) | HIGH | LOW | P1 |
| Docker Compose for local dev | HIGH | MEDIUM | P1 |
| DEPLOYMENT.md guide | HIGH | LOW | P1 |
| .dockerignore files | MEDIUM | LOW | P2 |
| Alembic migration before uvicorn start | MEDIUM | LOW | P2 |
| Build cache layer optimization | MEDIUM | LOW | P2 |
| NEXT_TELEMETRY_DISABLED | LOW | LOW | P2 |
| UV_COMPILE_BYTECODE=1 | LOW | LOW | P2 |
| Structured JSON logging | LOW | MEDIUM | P3 |
| Redis for in-memory state | LOW | HIGH | P3 |

**Priority key:**
- P1: Required for any working Docker/Dokploy deployment
- P2: Production hardening, include in v0.5.1 with minimal effort
- P3: Nice to have, defer to future milestone

---

## Sources

### High Confidence (Official Documentation)

- [Next.js Self-Hosting Official Guide](https://nextjs.org/docs/app/guides/self-hosting) -- Authoritative source on standalone mode, environment variable handling, SIGTERM graceful shutdown
- [Next.js Docker Official Deployment Docs](https://nextjs.org/docs/app/building-your-application/deploying) -- Confirms Docker is fully supported, links to official templates
- [Official Next.js Docker Example Dockerfile](https://raw.githubusercontent.com/vercel/next.js/canary/examples/with-docker/Dockerfile) -- Authoritative 3-stage Dockerfile with standalone mode, non-root user
- [Uvicorn Production Settings](https://www.uvicorn.org/) -- SIGTERM handling, --timeout-graceful-shutdown option
- [Dokploy Environment Variables Docs](https://docs.dokploy.com/docs/core/variables) -- Project/environment/service variable scopes, templating syntax
- [Dokploy Applications Docs](https://docs.dokploy.com/docs/core/applications) -- Volume mounts, port config, restart policies
- [Dokploy Going Production](https://docs.dokploy.com/docs/core/applications/going-production) -- Health check JSON config, update/rollback policy

### Medium Confidence (Verified Against Multiple Sources)

- [Runtime Next.js Environment Variables in Docker](https://nemanjamitic.com/blog/2025-12-13-nextjs-runtime-environment-variables/) -- Explains NEXT_PUBLIC_ build-time baking; runtime injection strategy; confirms server-side env vars work at container startup without rebuild
- [Dokploy Network Discussion](https://github.com/Dokploy/dokploy/discussions/1067) -- dokploy-network behavior, inter-service communication via service name DNS
- [Dokploy Database Connection Docs](https://docs.dokploy.com/docs/core/databases/connection) -- Internal host for managed databases; internal vs external connection strings
- [uv Docker Multi-Stage Builds](https://digon.io/en/blog/2025_07_28_python_docker_images_with_uv) -- UV_LINK_MODE=copy, UV_COMPILE_BYTECODE=1, .venv copy pattern for runtime stage

### Low Confidence (Single Source / Verify During Implementation)

- Dokploy service-name DNS resolution for inter-service communication -- confirmed by Dokploy community (AnswerOverflow thread) but should be verified with actual deployment. Claimed: `http://backend:8000` where `backend` is the Dokploy application service name.
- Next.js rewrite proxy correctly streams SSE -- claimed by Next.js docs (rewrites proxy all request types), but should be verified. If SSE doesn't stream through the Next.js rewrite, the `useSSEStream.ts` fix must use a different approach (NEXT_PUBLIC_BACKEND_URL for the SSE endpoint specifically).

---

*Feature research for: Docker and Dokploy deployment (v0.5.1)*
*Researched: 2026-02-18*
