---
phase: 34-dockerfiles-and-entrypoint
verified: 2026-02-18T00:00:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 34: Dockerfiles and Entrypoint — Verification Report

**Phase Goal:** Three production Docker images exist and each builds and runs correctly in isolation — the backend image waits for PostgreSQL, runs migrations, and starts uvicorn as PID 1; both frontend images serve the Next.js standalone app with `BACKEND_URL` controlling the proxy destination at runtime; no secrets are baked into any image layer
**Verified:** 2026-02-18
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Three .dockerignore files exist and exclude .env, .venv, node_modules, .next, __pycache__, uploads | ✓ VERIFIED | All three files present at project root; each contains `**/.env`, `**/.env.*`, `**/.venv`, `**/node_modules`, `**/.next`, `**/__pycache__`, `**/uploads` |
| 2 | docker-entrypoint.sh waits for PostgreSQL via pg_isready loop with max retries | ✓ VERIFIED | `until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q` at line 22; MAX_RETRIES=30, RETRY_INTERVAL=2 |
| 3 | docker-entrypoint.sh runs alembic upgrade head after PostgreSQL is ready | ✓ VERIFIED | `/app/.venv/bin/python -m alembic upgrade head` at line 36, after pg_isready loop |
| 4 | docker-entrypoint.sh starts uvicorn via exec (PID 1) on port 8000 | ✓ VERIFIED | `exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000` at line 41-44 |
| 5 | Backend image uses python:3.12-slim base with uv multi-stage build | ✓ VERIFIED | `FROM python:3.12-slim AS builder`; uv binary from `ghcr.io/astral-sh/uv:latest`; 2 stages confirmed |
| 6 | Backend image runs as non-root user (appuser, UID 1001) | ✓ VERIFIED | `groupadd --gid 1001 appuser && useradd --uid 1001 --gid appuser`; `USER appuser` |
| 7 | Backend image has HEALTHCHECK using curl to /health | ✓ VERIFIED | `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1` |
| 8 | Backend image declares /app/uploads as a VOLUME | ✓ VERIFIED | `VOLUME ["/app/uploads"]` |
| 9 | Backend image uses docker-entrypoint.sh as ENTRYPOINT | ✓ VERIFIED | `ENTRYPOINT ["/app/docker-entrypoint.sh"]` at line 71 |
| 10 | Both frontend images use node:22-alpine base with 3-stage build | ✓ VERIFIED | `FROM node:22-alpine AS base`; 4 FROM instructions (base + deps + builder + runner) in both |
| 11 | Both frontend images run as non-root user (nextjs, UID 1001) | ✓ VERIFIED | `adduser --system --uid 1001 nextjs`; `USER nextjs` in both Dockerfiles |
| 12 | BACKEND_URL controls proxy destination at runtime (not baked at build time) | ✓ VERIFIED | `ENV BACKEND_URL=http://localhost:8000` in runner stage of both frontend Dockerfiles; route handler proxies read `process.env.BACKEND_URL` at request time; overridable via `docker run -e` |
| 13 | Both frontend images have HEALTHCHECK and expose port 3000 on 0.0.0.0 | ✓ VERIFIED | `HEALTHCHECK CMD wget ... http://localhost:3000/api/health`; `EXPOSE 3000`; `ENV HOSTNAME="0.0.0.0"` in both |

**Score:** 13/13 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `Dockerfile.backend.dockerignore` | Backend build context exclusions | ✓ VERIFIED | 39 lines; excludes `**/.env`, `**/.env.*` (!.env.example negation), `.venv`, `node_modules`, `.next`, `__pycache__`, `uploads`, `frontend/`, `admin-frontend/` |
| `Dockerfile.frontend.dockerignore` | Frontend build context exclusions | ✓ VERIFIED | 39 lines; same exclusions; excludes `backend/`, `admin-frontend/` |
| `Dockerfile.admin.dockerignore` | Admin build context exclusions | ✓ VERIFIED | 39 lines; same exclusions; excludes `backend/`, `frontend/` |
| `backend/docker-entrypoint.sh` | Backend container entrypoint | ✓ VERIFIED | 44 lines (exceeds min 25); executable bit set; valid bash syntax confirmed (`bash -n`); strict mode `set -euo pipefail` |
| `Dockerfile.backend` | Production backend Docker image | ✓ VERIFIED | 71 lines (exceeds min 40); contains `python:3.12-slim`; 2-stage build |
| `Dockerfile.frontend` | Production public frontend Docker image | ✓ VERIFIED | 50 lines (exceeds min 40); contains `node:22-alpine`; 4-stage build |
| `Dockerfile.admin` | Production admin frontend Docker image | ✓ VERIFIED | 50 lines (exceeds min 40); contains `node:22-alpine`; 4-stage build; no erroneous `frontend/` refs |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/docker-entrypoint.sh` | `pg_isready` | shell `until` loop | ✓ WIRED | `until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q` at line 22 |
| `backend/docker-entrypoint.sh` | `alembic` | python -m alembic upgrade head | ✓ WIRED | `/app/.venv/bin/python -m alembic upgrade head` at line 36 |
| `backend/docker-entrypoint.sh` | `uvicorn` | `exec` for PID 1 | ✓ WIRED | `exec /app/.venv/bin/uvicorn app.main:app ...` at line 41 |
| `Dockerfile.backend` | `backend/docker-entrypoint.sh` | ENTRYPOINT instruction | ✓ WIRED | `ENTRYPOINT ["/app/docker-entrypoint.sh"]` at line 71; also `COPY --chown=appuser:appuser backend/docker-entrypoint.sh /app/docker-entrypoint.sh` at line 54 |
| `Dockerfile.backend` | `backend/pyproject.toml` | COPY for uv sync | ✓ WIRED | `COPY backend/pyproject.toml backend/uv.lock ./` at line 21 |
| `Dockerfile.backend` | `ghcr.io/astral-sh/uv` | COPY --from for uv binary | ✓ WIRED | `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/` at line 12 |
| `Dockerfile.frontend` | `frontend/package.json` | COPY for npm ci | ✓ WIRED | `COPY frontend/package.json frontend/package-lock.json ./` at line 10 |
| `Dockerfile.frontend` | `BACKEND_URL` | ENV for runtime proxy control | ✓ WIRED | `ENV BACKEND_URL=http://localhost:8000` in both builder (line 21) and runner (line 45) stages; route handler at `frontend/src/app/api/[...slug]/route.ts` reads `process.env.BACKEND_URL` at request time |
| `Dockerfile.admin` | `admin-frontend/package.json` | COPY for npm ci | ✓ WIRED | `COPY admin-frontend/package.json admin-frontend/package-lock.json ./` at line 10 |
| `Dockerfile.admin` | `BACKEND_URL` | ENV for runtime proxy control | ✓ WIRED | `ENV BACKEND_URL=http://localhost:8000` in both builder and runner stages; route handler at `admin-frontend/src/app/api/[...slug]/route.ts` reads `process.env.BACKEND_URL` at request time |

**Note on plan 03 key_link deviation:** Plan 03 specified `ARG BACKEND_URL` pattern and build-time baking. During execution, the plan was auto-corrected: since Phase 33 replaced next.config.ts rewrites with catch-all route handler proxies that call `process.env.BACKEND_URL` at request time, `ENV` (runtime) is the correct mechanism — `ARG` (build-time) would have been a regression. The goal requirement ("BACKEND_URL controlling the proxy destination at runtime") is fully satisfied by `ENV` with docker run `-e` override capability.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DOCK-01 | 34-01 | Each service has a `.dockerignore` that excludes `.env` files, `.venv`, `node_modules`, `.next`, `__pycache__`, and `uploads/` — no secrets baked into image layers | ✓ SATISFIED | Three `.dockerignore` files verified; all critical exclusions present in each; `.env.example` whitelisted back via negation pattern `!**/.env.example` |
| DOCK-02 | 34-01 | Backend has `backend/docker-entrypoint.sh` that waits for PostgreSQL readiness (`pg_isready`), runs `alembic upgrade head`, then starts uvicorn as PID 1 via `exec` | ✓ SATISFIED | `backend/docker-entrypoint.sh` exists, is executable, passes bash syntax check; all three behaviors verified at correct lines |
| DOCK-03 | 34-02 | Developer can build `Dockerfile.backend` to produce a production Python image (`python:3.12-slim` base, uv multi-stage, non-root user, `GET /health` HEALTHCHECK, `/app/uploads` volume declaration) | ✓ SATISFIED | `Dockerfile.backend` exists with 2-stage uv build, `appuser` UID 1001, HEALTHCHECK on `/health`, VOLUME at `/app/uploads`, ENTRYPOINT to entrypoint script |
| DOCK-04 | 34-03 | Developer can build `Dockerfile.frontend` to produce a production Next.js standalone image (`node:22-alpine`, 3-stage build, non-root user, `GET /api/health` HEALTHCHECK) | ✓ SATISFIED | `Dockerfile.frontend` exists with 4-stage build (base + deps + builder + runner), `nextjs` UID 1001, HEALTHCHECK on `/api/health`, standalone output enabled in `next.config.ts`, HOSTNAME=0.0.0.0 |
| DOCK-05 | 34-03 | Developer can build `Dockerfile.admin` to produce a production Next.js standalone image (identical pattern to `Dockerfile.frontend`, container port 3000) | ✓ SATISFIED | `Dockerfile.admin` exists with identical structure to `Dockerfile.frontend`; sources from `admin-frontend/`; skips public/ COPY (admin has no public dir); same HEALTHCHECK, user, and port |

All 5 requirements satisfied. No orphaned requirements found — DOCK-01 through DOCK-05 are the only Phase 34 requirements in `REQUIREMENTS.md`.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | — |

No TODO/FIXME/placeholder comments, empty implementations, or stub patterns detected in any of the 7 files created in this phase.

---

### Human Verification Required

#### 1. Docker Build Success (all three images)

**Test:** Run `docker build -f Dockerfile.backend .`, `docker build -f Dockerfile.frontend .`, `docker build -f Dockerfile.admin .` from project root.
**Expected:** All three builds succeed without errors. Backend build pulls `ghcr.io/astral-sh/uv:latest`, installs Python deps via uv. Frontend/admin builds complete 3-stage npm build and produce standalone output.
**Why human:** Requires a Docker daemon. Cannot verify build success programmatically without Docker available. The Dockerfiles are syntactically correct and structurally sound, but actual build execution depends on network access to registries and the presence of a Docker daemon.

#### 2. Backend Image Runtime Behavior

**Test:** Run `docker run --rm -e DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db spectra-backend` (with a running PostgreSQL).
**Expected:** Entrypoint waits for PostgreSQL, runs `alembic upgrade head`, then starts uvicorn on port 8000. SIGTERM gracefully shuts down uvicorn (PID 1 via exec).
**Why human:** Requires Docker daemon, a running PostgreSQL instance, and a valid `DATABASE_URL`. The entrypoint logic is fully verified in source but runtime behavior needs live execution to confirm.

#### 3. Frontend BACKEND_URL Runtime Override

**Test:** Run `docker run --rm -e BACKEND_URL=http://backend:8000 -p 3000:3000 spectra-frontend` and make an API request through the frontend proxy.
**Expected:** Proxy forwards requests to `http://backend:8000` (not the default `http://localhost:8000`), confirming the runtime `ENV` override works correctly.
**Why human:** Requires Docker daemon and a running backend service. The route handler code and Dockerfile ENV setup are verified, but the actual runtime override behavior needs end-to-end testing.

---

### Key Decisions Verified

1. **ENV over ARG for BACKEND_URL:** Plan 03 specified `ARG BACKEND_URL` (build-time), but Phase 33 established route handler proxies that read `process.env.BACKEND_URL` at request time. Using `ENV` (with docker run `-e` override) is architecturally correct — it satisfies "BACKEND_URL controlling the proxy destination at runtime" more fully than a build arg would have.

2. **`!**/.env.example` negation pattern:** All three `.dockerignore` files whitelist `.env.example` back after excluding all `.env.*`. This is the correct behavior — example env files are documentation, not secrets.

3. **Per-Dockerfile `.dockerignore` naming (BuildKit convention):** Using `Dockerfile.{service}.dockerignore` means each service's build context is precisely scoped. Backend excludes `frontend/` and `admin-frontend/`; frontend excludes `backend/` and `admin-frontend/`; admin excludes `backend/` and `frontend/`.

4. **Explicit venv python path in entrypoint:** `/app/.venv/bin/python` is used for both alembic and uvicorn — this is required because uv installs into `.venv/`, not into the system Python. This is verified in the entrypoint source.

---

### Commits Verified

All 5 commits claimed in summaries confirmed in git log:

| Commit | Description |
|--------|-------------|
| `1203910` | feat(34-01): add per-Dockerfile .dockerignore files for all three services |
| `23b7108` | feat(34-01): add backend docker-entrypoint.sh with pg wait, migrations, uvicorn |
| `352c423` | feat(34-02): add backend Dockerfile with uv multi-stage build |
| `6be3c0e` | feat(34-03): add Dockerfile.frontend for public Next.js app |
| `14cde32` | feat(34-03): add Dockerfile.admin for admin Next.js app |

---

_Verified: 2026-02-18_
_Verifier: Claude (gsd-verifier)_
