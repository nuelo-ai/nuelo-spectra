# Project Research Summary

**Project:** Spectra — Docker + Dokploy Deployment (v0.5.1)
**Domain:** Containerizing a FastAPI + 2x Next.js monorepo for self-hosted Dokploy PaaS
**Researched:** 2026-02-18
**Confidence:** HIGH

## Executive Summary

Spectra v0.5.1 is a "wrap the existing app" milestone, not a new feature build. The app is already production-functional; the goal is to containerize three services (FastAPI backend, Next.js public frontend, Next.js admin frontend) and deploy them to a self-hosted Dokploy instance. All three services get their own multi-stage Dockerfile. Dokploy is configured as three independent Application services — one per Dockerfile — sharing a common Docker overlay network (`dokploy-network`) and a Dokploy-managed PostgreSQL database. The recommended deployment model uses individual Dokploy Applications rather than a single Docker Compose deployment, enabling independent rollback and update cadences per service.

The most important finding from codebase inspection is that two pre-work changes must happen before any Dockerfile is valid: (1) two hardcoded `http://localhost:8000` direct fetch calls in `useSSEStream.ts` and `register/page.tsx` must be changed to relative `/api/...` paths, and (2) both `next.config.ts` files must get `output: 'standalone'` added and have their rewrite destinations updated to read `process.env.BACKEND_URL` instead of the hardcoded localhost URL. Without these two pre-work items, Docker images will build successfully but fail silently at runtime — the hardest class of bug to diagnose.

The principal risks are all configuration-correctness problems, not capability gaps. Docker and Dokploy are mature, well-documented technologies. The risks are: secrets baked into image layers from missing `.dockerignore` files (critical security), file uploads lost on redeploy from missing volume mounts (data loss), backend starting before PostgreSQL is ready from missing `pg_isready` wait logic (intermittent deployment failure), and wrong `SPECTRA_MODE` per service silently breaking routing or exposing admin routes publicly (security and feature breakage). Every one of these risks has a clear, low-effort prevention pattern documented in PITFALLS.md.

---

## Key Findings

### Recommended Stack

See full details in `.planning/research/STACK-docker-dokploy.md`.

The technology choices are narrow and well-established. `python:3.12-slim` (Debian bookworm-slim, not Alpine) is the only viable base image for the backend: asyncpg and psycopg-binary ship manylinux binary wheels that require glibc; Alpine's musl libc is incompatible and would force compiling from source. `node:22-alpine` is the correct base for both Next.js frontends — Next.js has no native modules requiring glibc, so Alpine is safe and saves ~100MB per image. The `uv` binary is copied from `ghcr.io/astral-sh/uv:latest` into the backend builder stage; `uv sync --locked --no-dev` provides reproducible, fast dependency installation from the existing `uv.lock` file. All three Dockerfiles use multi-stage builds: a builder stage installs dependencies and compiles assets, a leaner runner stage copies only what is needed for runtime.

Dokploy v0.26.x is the deployment platform. The Dockerfile build type (not Nixpacks) is required because uv lock files are not understood by Nixpacks v1.x and multi-stage builds are not supported by Nixpacks. There is no `dokploy.yml` config file — all Dokploy configuration lives in the web UI. Traefik (bundled with Dokploy) handles TLS termination and domain routing automatically; no manual Traefik configuration is needed.

**Core technologies:**
- `python:3.12-slim`: Backend base image — glibc required for asyncpg/psycopg binary wheels; `-slim` reduces image size ~200MB vs full image
- `node:22-alpine`: Frontend base image (both apps) — Node 22 is active LTS; Alpine safe for Next.js; saves ~100MB per image
- `uv` (via `ghcr.io/astral-sh/uv:latest`): Python dep management in Docker — project already uses uv.lock; `uv sync --locked` is reproducible and fast
- `output: 'standalone'` (Next.js built-in): Reduces Next.js image from ~7GB to ~300MB by tracing and copying only required files
- Dokploy v0.26.x: Self-hosted PaaS — manages 3 services as independent Applications with Traefik-based routing; Dockerfile build type required
- Docker Compose v2 (no `version:` field): Local dev orchestration — `version:` field is officially obsolete in Compose v2 and triggers warnings in Docker 25+

### Expected Features

See full details in `.planning/research/FEATURES.md`.

This milestone is primarily infrastructure work. There are no new user-facing capabilities. The feature set is defined entirely by what is required for a working, production-safe Docker deployment.

**Must have (table stakes — P1, all blocking):**
- Fix hardcoded `localhost:8000` in `useSSEStream.ts` (line 112) and `register/page.tsx` (line 26) — without this, SSE chat streaming and signup status check fail in Docker
- `output: 'standalone'` in both `next.config.ts` files — required for Next.js Docker images to exist at all
- `process.env.BACKEND_URL` in both `next.config.ts` rewrite destinations — required for inter-service routing in Docker
- Health check API routes in both frontends (`/api/health` returning `{status: "ok"}`) — required for Dokploy health monitoring
- Backend Dockerfile (multi-stage, uv-based, non-root user, HEALTHCHECK, volume declaration at `/app/uploads`)
- Public frontend Dockerfile (3-stage standalone, non-root user, HEALTHCHECK)
- Admin frontend Dockerfile (3-stage standalone, non-root user, HEALTHCHECK)
- `docker-compose.yml` for local dev (all 3 services + postgres with health check, uploads named volume)
- `DEPLOYMENT.md` step-by-step Dokploy guide

**Should have (P2 — production hardening, low effort):**
- `.dockerignore` for each service — prevents secrets leakage and bloated build contexts; non-negotiable security item
- Alembic migration in backend entrypoint before uvicorn starts — prevents broken schema on first deploy
- `pg_isready` wait loop in backend entrypoint — prevents race condition startup failures on cold deploys
- Build cache layer optimization (copy dependency files before app source)
- `NEXT_TELEMETRY_DISABLED=1` and `UV_COMPILE_BYTECODE=1` — minor production polish

**Defer (not this milestone):**
- Redis for in-memory state (token revocation, admin lockout) — single-instance limitation documented in PROJECT.md; only matters at 2+ replicas
- CI/CD image registry pipeline — Dokploy direct-from-git is sufficient at single-developer scale
- Structured JSON logging — current logging is readable; not needed at 1-user scale
- Read-only root filesystem — security enhancement; complex to configure for marginal single-instance benefit

### Architecture Approach

See full details in `.planning/research/ARCHITECTURE.md`.

All three Dockerfiles sit at the monorepo root and use the repo root as the Docker build context. This is the correct configuration for Dokploy: "Docker Context Path" is set to `.` (repo root) for all three services, and "Dockerfile Path" differs per service (`Dockerfile.backend`, `Dockerfile.frontend`, `Dockerfile.admin`). Each Dockerfile COPYs only from its own subdirectory. All three Dokploy Application services join `dokploy-network` automatically, enabling inter-service communication via Docker service names as DNS hostnames (e.g., `http://spectra-backend:8000`). The key architectural insight is that Next.js `rewrites()` in `next.config.ts` are evaluated at Node.js server startup — not at build time — meaning `process.env.BACKEND_URL` is a runtime environment variable, not a build-time ARG. This eliminates the `NEXT_PUBLIC_` bake-in problem for the backend URL entirely.

The backend entrypoint script is the critical sequencing mechanism: `pg_isready` wait loop then `alembic upgrade head` then `exec uvicorn`. The `exec` prefix replaces the shell with uvicorn as PID 1 so Docker SIGTERM signals reach uvicorn directly for graceful shutdown. File uploads use a named Docker volume (`spectra_uploads`) mounted at `/app/uploads` — named volumes persist independently of container lifecycle and Dokploy redeployments.

**Major components:**
1. `Dockerfile.backend` — multi-stage Python image; entrypoint handles DB readiness + Alembic migrations before uvicorn starts
2. `Dockerfile.frontend` — 3-stage Next.js standalone image; `BACKEND_URL` env var controls rewrite destination at runtime
3. `Dockerfile.admin` — identical pattern to frontend; connects to same backend via `BACKEND_URL`; `SPECTRA_MODE=admin` on the backend it targets
4. `backend/docker-entrypoint.sh` — `pg_isready` wait + `alembic upgrade head` + `exec uvicorn`; ensures deployment never starts a broken backend
5. `docker-compose.yml` — local dev orchestration; postgres with health check; named volume `uploads_data`; `depends_on: condition: service_healthy`
6. `DEPLOYMENT.md` — step-by-step Dokploy configuration guide covering all 3 services, env vars, volumes, and domain assignment

### Critical Pitfalls

See full details in `.planning/research/PITFALLS.md`.

1. **No `.dockerignore` in the repo — secrets baked into image layers** — The repo currently has no `.dockerignore` file anywhere. Without one, `COPY . .` in any Dockerfile pulls in `.env` files containing `ANTHROPIC_API_KEY`, `E2B_API_KEY`, `TAVILY_API_KEY`, `SECRET_KEY` (JWT), `SMTP_PASS`, and `ADMIN_PASSWORD`. These are permanently stored in Docker layer history, recoverable with `docker history --no-trunc`. Prevention: write `.dockerignore` for each service before writing any `COPY` instruction. Exclude `.env`, `.env.*`, `.venv`, `node_modules`, `__pycache__`, `.next`, `uploads/`.

2. **Hardcoded `localhost:8000` in `useSSEStream.ts` and `register/page.tsx`** — These two files bypass the Next.js rewrite proxy and directly fetch `http://localhost:8000`. In Docker, `localhost` resolves to the frontend container itself. SSE streaming fails; signup status check fails with `ECONNREFUSED`. Both failures produce no obvious error at the UI layer. Fix: change both to relative `/api/...` paths. This must happen before any Docker image is built.

3. **Alembic migration + `pg_isready` must be in entrypoint before uvicorn** — FastAPI's `lifespan()` in `main.py` creates an `AsyncConnectionPool` and runs `checkpointer.setup()` at startup. If PostgreSQL is not ready, the entire lifespan throws, uvicorn never starts, and Dokploy marks the deployment failed. The backend entrypoint script must: (1) loop `pg_isready` until PostgreSQL accepts connections, (2) run `alembic upgrade head`, then (3) `exec uvicorn`. Running Alembic inside FastAPI lifespan creates async/sync event loop conflicts and is the wrong approach.

4. **`SPECTRA_MODE` set incorrectly per service causes silent failure or security breach** — `SPECTRA_MODE=public` on the admin backend means all admin API calls return 404 (admin router not mounted). `SPECTRA_MODE=dev` on the public-facing backend exposes `/api/admin/*` endpoints to the public internet. Neither failure produces an obvious error at startup — the backend starts normally and appears healthy. Prevention: explicitly set and verify `SPECTRA_MODE` for each Dokploy service as a named deployment checklist item.

5. **File uploads volume mount is non-negotiable** — The backend writes user uploads to `/app/uploads`. Without a named Docker volume (`spectra_uploads` mounted at `/app/uploads`), all user files are lost on every Dokploy redeploy. This creates a broken state: PostgreSQL retains file records but the files are gone from disk. File download endpoints return 404 for files that appear in the list. Prevention: configure the named volume in Dokploy Advanced → Mounts before the first production deployment.

---

## Implications for Roadmap

The research strongly suggests a 4-phase delivery structure with strict sequencing driven by dependencies. Phases 1 and 2 are the core of the milestone; Phase 3 validates end-to-end; Phase 4 produces the documentation artifact and the live production deployment.

### Phase 1: Pre-Work Code Changes

**Rationale:** Two source code changes must exist in the repository before any Dockerfile is written. They are both blocking for Docker correctness, and fixing them first keeps the Dockerfile authoring phase clean — no Dockerfile needs to contain workarounds for application-layer bugs. These are the easiest items in the milestone (simple string replacements and a `next.config.ts` update) and must be first because everything downstream depends on them.

**Delivers:** A codebase where no hardcoded localhost URLs exist, both Next.js apps are configured for standalone output, both rewrite destinations read `process.env.BACKEND_URL`, and both frontends have a `/api/health` route for Dokploy health checks.

**Addresses (from FEATURES.md):**
- Fix `frontend/src/hooks/useSSEStream.ts` line 112: `http://localhost:8000/chat/...` → `/api/chat/...`
- Fix `frontend/src/app/(auth)/register/page.tsx` line 26: `http://localhost:8000/auth/signup-status` → `/api/auth/signup-status`
- Add `output: 'standalone'` to `frontend/next.config.ts` and `admin-frontend/next.config.ts`
- Update rewrite destinations to `process.env.BACKEND_URL || 'http://localhost:8000'` in both `next.config.ts` files
- Create `frontend/src/app/api/health/route.ts` returning `{status: "ok"}`
- Create `admin-frontend/src/app/api/health/route.ts` returning `{status: "ok"}`

**Avoids (from PITFALLS.md):**
- Pitfall 1 (NEXT_PUBLIC_ baked as `undefined`): rewrite destination now reads from env var
- SSE streaming failure in Docker: localhost hardcode removed
- Missing standalone output: would make the multi-stage Dockerfile pattern non-functional

**Research flag:** None needed. These are direct, unambiguous code changes.

---

### Phase 2: Dockerfiles and .dockerignore

**Rationale:** Writing the three Dockerfiles is the core infrastructure work of the milestone. The backend Dockerfile is built first because both frontends depend on the backend being deployed (needed to confirm `BACKEND_URL`). The entrypoint script (`docker-entrypoint.sh`) is written alongside the backend Dockerfile as an inseparable deliverable. `.dockerignore` files must be written before or simultaneously with the Dockerfiles — never after, because any `docker build` run without `.dockerignore` risks baking secrets into layers permanently.

**Delivers:** Three production-ready Docker images that build and run locally. The backend image starts cleanly against a local PostgreSQL (waits for readiness, runs migrations, then starts uvicorn). Both frontend images serve the Next.js app correctly with `BACKEND_URL` controlling the rewrite destination at runtime.

**Build order within this phase:**
1. `.dockerignore` files (all three service directories, before any `docker build` is run)
2. `backend/docker-entrypoint.sh` (`pg_isready` wait + `alembic upgrade head` + `exec uvicorn`)
3. `Dockerfile.backend` (`python:3.12-slim`, multi-stage, uv-based, non-root `appuser`, HEALTHCHECK at `/health`, `/app/uploads` volume)
4. `Dockerfile.frontend` (`node:22-alpine`, 3-stage standalone, non-root `nextjs:nodejs`, HEALTHCHECK at `/api/health`, PORT=3000)
5. `Dockerfile.admin` (identical pattern to frontend, PORT=3000 in container / 3001 on host in Compose)

**Uses (from STACK.md):**
- `python:3.12-slim` for backend (glibc required for asyncpg and psycopg binary wheels; Alpine would break both)
- `ghcr.io/astral-sh/uv:latest` binary copy pattern for fast, reproducible Python deps
- `node:22-alpine` for both frontends (Node 22 active LTS; Alpine safe for Next.js; no glibc-dependent native modules)
- Multi-stage build pattern for all three services (builder stage + lean runtime stage)
- `uv sync --locked --no-dev --compile-bytecode` for production backend dep install

**Implements (from ARCHITECTURE.md):**
- Monorepo build context strategy: all Dockerfiles at repo root, Docker context = `.`, explicit subdirectory COPYs
- Entrypoint script with `exec` for SIGTERM signal forwarding to uvicorn (PID 1)
- Named volume declaration for `/app/uploads` in Dockerfile.backend
- Non-root users in all images (security baseline)

**Avoids (from PITFALLS.md):**
- Pitfall 4: Secrets in image layers — `.dockerignore` written first, `.env` excluded before any `COPY`
- Pitfall 3: Migration race condition — `pg_isready` loop in entrypoint before `alembic upgrade head`
- Pitfall 6: Wrong monorepo build context — Dockerfiles at root with explicit `COPY backend/` scoping
- Pitfall 2: File upload loss — volume declared in Dockerfile.backend and verified with smoke test

**Research flag:** None needed. All three Dockerfile patterns are from official documentation (uv Docker integration guide, Next.js official Docker example, official Python Docker Hub). HIGH confidence.

---

### Phase 3: Docker Compose and Local Validation

**Rationale:** The `docker-compose.yml` is the integration test for the three Dockerfiles. It proves all services start correctly together, that inter-service networking works, that the uploads volume persists across `docker-compose down && up`, and that the local dev workflow is viable. Writing Compose after the Dockerfiles (not simultaneously) ensures each Dockerfile is independently validated before adding the orchestration layer. The smoke test checklist in this phase serves as the acceptance criteria for the entire milestone.

**Delivers:** A working `docker-compose.yml` at the repo root that brings up all 3 services plus local PostgreSQL with `docker compose up`. Validated smoke tests: login works, SSE chat streaming works through the Next.js rewrite proxy, file upload persists after `docker-compose down && up`, admin frontend reaches admin API routes.

**Addresses (from FEATURES.md):**
- `docker-compose.yml` with all 3 services plus `postgres:16-alpine` with healthcheck
- Named volume `uploads_data` at `/app/uploads` for upload persistence
- `depends_on: condition: service_healthy` on backend (waits for postgres healthcheck to pass)
- Standardized port mapping: backend 8000, public frontend 3000, admin frontend 3001:3000
- `restart: unless-stopped` for all services

**Avoids (from PITFALLS.md):**
- Pitfall 2: File upload loss — verified by uploading a file, running `docker-compose down && up`, confirming file still accessible
- Pitfall 3: Migration race condition — postgres healthcheck + `depends_on: condition: service_healthy` handles startup ordering
- Pitfall 5: Wrong SPECTRA_MODE — `SPECTRA_MODE` explicitly set per service in Compose env vars and verified against expected behavior

**Research flag:** None needed. Docker Compose v2 patterns are thoroughly documented. The `depends_on: condition: service_healthy` pattern is standard.

---

### Phase 4: Dokploy Deployment and DEPLOYMENT.md

**Rationale:** DEPLOYMENT.md comes last because it documents a process that cannot be written accurately until Dockerfiles and Compose are fully validated. Dokploy deployment configuration lives entirely in the UI (no config files exist), so the DEPLOYMENT.md is the only artifact from this phase beyond the live production deployment itself. Writing documentation before the implementation is known leads to inaccurate guides.

**Delivers:** A production deployment on Dokploy with all three services running behind HTTPS domains. `DEPLOYMENT.md` captures every manual step: Dokploy project creation, 3 Application service configurations (Dockerfile path, context path, port), environment variable tables per service, volume mount configuration (`spectra_uploads` → `/app/uploads`), domain assignment, SSL, and a post-deploy verification checklist.

**Addresses (from FEATURES.md):**
- `DEPLOYMENT.md` step-by-step Dokploy guide
- `SPECTRA_MODE` explicitly set per service in Dokploy env vars UI (deployment checklist item)
- `ENABLE_SCHEDULER=true` on backend
- `CORS_ORIGINS` configured with actual production frontend domains
- Named volume `spectra_uploads` at `/app/uploads` configured in Dokploy Advanced → Mounts
- `SECRET_KEY` generated once (`python -c "import secrets; print(secrets.token_hex(32))"`) and documented

**Avoids (from PITFALLS.md):**
- Pitfall 5: Wrong SPECTRA_MODE — deployment checklist includes per-service mode verification and smoke test
- Pitfall 7: JWT secret changes on restart — `SECRET_KEY` generated once and stored only in Dokploy env vars UI
- Pitfall 4: Secrets not in Dockerfiles or committed files — all secrets injected via Dokploy env vars panel

**Research flag:** LOW — one targeted verification needed at deployment time. The exact internal Docker hostname Dokploy assigns to each service on `dokploy-network` is MEDIUM confidence (community-confirmed but not officially documented by Dokploy). Resolution: inspect the Dokploy UI → service → Network settings for the actual internal hostname after first backend deployment, then update `BACKEND_URL` in the frontend services accordingly. Fallback: use the backend's public domain URL for `BACKEND_URL` (goes through Traefik instead of internal network, slightly higher latency but fully functional).

---

### Phase Ordering Rationale

- **Pre-work first, non-negotiable:** The two localhost hardcodes and `output: 'standalone'` must be in the repo before any Docker image is built. There is no Dockerfile-level workaround for these application-layer issues.
- **`.dockerignore` before `docker build`, absolute:** Any `docker build` run without `.dockerignore` risks writing API keys and JWT secrets permanently into image layer history. This cannot be undone without deleting and rebuilding the image. Treat `.dockerignore` authoring as a prerequisite gating step, not a follow-up.
- **Backend Dockerfile before frontend Dockerfiles:** Both frontend images need `BACKEND_URL` to be a known value for validation. The backend Dockerfile is also simpler (no 3-stage pattern) and builds confidence before the more complex frontend multi-stage builds.
- **Docker Compose before Dokploy:** Local validation catches configuration errors cheaply (no VPS required, fast iteration). Finding that the entrypoint script fails or the volume mount is misconfigured during local testing is far cheaper than debugging on a remote Dokploy instance.
- **DEPLOYMENT.md last:** Documentation written before the implementation is validated is speculation. Write it last, against a working deployment.

### Research Flags

Phases with standard patterns (no research-phase needed — research is complete):
- **Phase 1 (Pre-Work):** Direct code changes with no ambiguity
- **Phase 2 (Dockerfiles):** All patterns from official documentation; HIGH confidence
- **Phase 3 (Docker Compose):** Standard Compose v2 patterns; HIGH confidence

Phases needing one targeted verification during implementation:
- **Phase 4 (Dokploy):** Verify the exact internal service hostname format on `dokploy-network` after first deployment before setting `BACKEND_URL` in frontend services. MEDIUM confidence on the specific naming convention.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technology choices verified against official docs (Next.js upgrade guide, uv Docker guide, Python Speed, Dokploy docs, Docker Hub). Versions confirmed as of 2026-02-18. |
| Features | HIGH | Code inspection of actual files confirmed both hardcoded localhost bugs (line numbers verified). All other features are additive (new Dockerfiles, new config files). No feature ambiguity. |
| Architecture | MEDIUM-HIGH | Docker and Next.js standalone patterns are HIGH confidence from official docs. Dokploy inter-service networking via `dokploy-network` DNS is MEDIUM confidence — community-confirmed but not officially documented by Dokploy. |
| Pitfalls | HIGH | All 7 critical pitfalls verified against official Docker docs, official Next.js docs, and official Dokploy docs. Two pitfalls (no `.dockerignore`, hardcoded localhost) confirmed by direct codebase inspection. |

**Overall confidence:** HIGH

### Gaps to Address

- **Dokploy internal service hostname format:** Not officially documented. Community sources confirm services communicate by service name on `dokploy-network`. Verify in the Dokploy UI (Network/Container settings tab of each deployed service) before configuring `BACKEND_URL` in the frontend services. Fallback if internal hostname doesn't resolve: use the backend's public HTTPS domain for `BACKEND_URL` — this routes through Traefik and is fully functional, just slightly higher latency than the internal network path.

- **SSE streaming through Next.js rewrite proxy:** Next.js docs state rewrites proxy all request types including streaming responses. This is marked LOW confidence in FEATURES.md because it was not verified for POST-based SSE specifically in a Docker proxy chain. Verify during Phase 3 smoke testing by running a chat session end-to-end through the Docker Compose stack. If the Next.js rewrite does not stream SSE correctly, the `useSSEStream.ts` fix must use a `NEXT_PUBLIC_BACKEND_URL` env var for that one endpoint specifically (a larger change that requires understanding the build-time vs runtime distinction for `NEXT_PUBLIC_` vars).

- **`pg_isready` availability in `python:3.12-slim`:** The entrypoint script uses `pg_isready` for the DB readiness check. `python:3.12-slim` does not include PostgreSQL client tools by default. Two options: (1) install `postgresql-client` via `apt-get` in the runtime stage (adds a layer, small image size increase, cleanest solution), or (2) use a pure-Python TCP connection loop instead of `pg_isready` (no extra dependency). Decide during Phase 2 when writing `docker-entrypoint.sh`.

---

## Sources

### Primary (HIGH confidence)
- Next.js official self-hosting guide — standalone mode, runtime env vars, Docker pattern — https://nextjs.org/docs/app/guides/self-hosting
- Next.js official upgrade guide (v16) — Node.js 20.9+ minimum requirement confirmed — https://nextjs.org/docs/app/guides/upgrading/version-16
- Next.js official Docker example Dockerfile — authoritative 3-stage standalone pattern — https://github.com/vercel/next.js/tree/canary/examples/with-docker
- uv official Docker integration guide — multi-stage build pattern, `uv sync --locked` — https://docs.astral.sh/uv/guides/integration/docker/
- Dokploy official docs — build types, env var scopes, volumes, Application model — https://docs.dokploy.com/docs/core/applications/build-type
- Docker official docs — `version:` field obsolete, build context, secrets in layers — https://docs.docker.com/reference/compose-file/version-and-name/
- psycopg official docs — binary package bundles its own libpq, no system libpq-dev needed — https://www.psycopg.org/psycopg3/docs/basic/install.html
- pythonspeed.com — `python:3.12-slim` recommendation for production Docker images — https://pythonspeed.com/articles/base-image-python-docker-images/
- Docker official build secrets docs — ARG/ENV secrets baked into layers — https://docs.docker.com/reference/build-checks/secrets-used-in-arg-or-env/

### Secondary (MEDIUM confidence)
- Dokploy `dokploy-network` inter-service communication — community source confirming service name DNS resolution — https://torchtree.com/en/post/dokploy-container-network-issue/
- Dokploy discussion on `dokploy-network` and domain configuration — https://github.com/Dokploy/dokploy/discussions/1067
- Runtime Next.js env vars in Docker — confirms server-side vars work at startup without image rebuild — https://nemanjamitic.com/blog/2025-12-13-nextjs-runtime-environment-variables/
- FastAPI + Alembic + Docker entrypoint pattern (uv-based, consistent with all other sources) — https://blog.devops.dev/a-scalable-approach-to-fastapi-projects-with-postgresql-alembic-pytest-and-docker-using-uv-78ebf6f7fb9a
- uv Docker multi-stage builds — `UV_COMPILE_BYTECODE=1`, `.venv` copy pattern — https://digon.io/en/blog/2025_07_28_python_docker_images_with_uv

### Tertiary (LOW confidence — verify during implementation)
- Dokploy service-name DNS resolution for `BACKEND_URL` — community thread, not official docs
- Next.js rewrite proxy correctly streams POST-based SSE responses — stated in Next.js docs but not explicitly verified in a Docker proxy chain scenario

### Codebase inspection (direct, HIGH confidence)
- `frontend/src/hooks/useSSEStream.ts` line 112 — confirmed hardcoded `http://localhost:8000/chat/...`
- `frontend/src/app/(auth)/register/page.tsx` line 26 — confirmed hardcoded `http://localhost:8000/auth/signup-status`
- `frontend/next.config.ts` and `admin-frontend/next.config.ts` — confirmed missing `output: 'standalone'` and hardcoded rewrite destinations
- `backend/app/config.py` — confirmed `upload_dir: str = "uploads"` default and `secret_key: str` with no default (correct: Pydantic raises ValidationError if not set)
- Repo root — confirmed no `.dockerignore` exists anywhere in the repository

---
*Research completed: 2026-02-18*
*Ready for roadmap: yes*
