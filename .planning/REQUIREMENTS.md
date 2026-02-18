# Requirements: Spectra

**Defined:** 2026-02-18
**Milestone:** v0.6 Docker and Dokploy Support
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.6 Requirements

Requirements for Docker containerization and Dokploy production deployment. Continues numbering from v0.5.

### Pre-Work Fixes (PRE)

Code changes that must land before any Dockerfile is valid. Two confirmed localhost:8000 hardcodes bypass the Next.js rewrite proxy and silently fail in Docker.

- [ ] **PRE-01**: Developer can verify the public frontend makes all API calls via `/api/` proxy — no hardcoded `http://localhost:8000` in `useSSEStream.ts` (line 112) or `register/page.tsx` (line 26)
- [ ] **PRE-02**: Both Next.js apps support standalone build output compatible with multi-stage Docker images (`output: 'standalone'` added to both `next.config.ts` files)
- [ ] **PRE-03**: Both Next.js apps read the backend URL from `process.env.BACKEND_URL` at startup rather than hardcoding `localhost:8000` in rewrite destinations (defaults to `http://localhost:8000` for local dev without Docker)
- [ ] **PRE-04**: Public frontend exposes `GET /api/health` returning `{status: "ok"}` for Dokploy health monitoring
- [ ] **PRE-05**: Admin frontend exposes `GET /api/health` returning `{status: "ok"}` for Dokploy health monitoring

### Docker Images (DOCK)

Production Docker images for all three services. `.dockerignore` files are written before any `docker build` is run to prevent secrets leaking into image layers.

- [ ] **DOCK-01**: Each service has a `.dockerignore` that excludes `.env` files, `.venv`, `node_modules`, `.next`, `__pycache__`, and `uploads/` — no secrets baked into image layers
- [ ] **DOCK-02**: Backend has `backend/docker-entrypoint.sh` that waits for PostgreSQL readiness (`pg_isready`), runs `alembic upgrade head`, then starts uvicorn as PID 1 via `exec` (graceful shutdown)
- [ ] **DOCK-03**: Developer can build `Dockerfile.backend` to produce a production Python image (`python:3.12-slim` base, uv multi-stage, non-root user, `GET /health` HEALTHCHECK, `/app/uploads` volume declaration)
- [ ] **DOCK-04**: Developer can build `Dockerfile.frontend` to produce a production Next.js standalone image (`node:22-alpine`, 3-stage build, non-root user, `GET /api/health` HEALTHCHECK)
- [ ] **DOCK-05**: Developer can build `Dockerfile.admin` to produce a production Next.js standalone image (identical pattern to `Dockerfile.frontend`, container port 3000)

### Docker Compose (COMP)

Local development orchestration. Validates all three Dockerfiles work together before Dokploy configuration.

- [ ] **COMP-01**: Developer can bring up the full local stack with `docker compose up` — backend on port 8000, public frontend on port 3000, admin frontend on port 3001, PostgreSQL on port 5432
- [ ] **COMP-02**: File uploads survive `docker compose down && docker compose up` — named volume `uploads_data` mounted at `/app/uploads` in backend service
- [ ] **COMP-03**: Backend service starts only after PostgreSQL passes its healthcheck (`depends_on: condition: service_healthy` — not just `depends_on` without condition)
- [ ] **COMP-04**: Docker Compose sets correct `SPECTRA_MODE` per service (`public` for backend serving public frontend, `dev` for local dev to serve both) and `BACKEND_URL=http://backend:8000` for inter-service routing

### Version Display (VER)

App version visible on settings/profile page in both frontends, fetched from backend at runtime. No rebuild required to update the displayed version.

- [ ] **VER-01**: Backend exposes `GET /version` endpoint returning `{"version": "<APP_VERSION env var>", "environment": "<SPECTRA_MODE>"}` — `APP_VERSION` defaults to `"dev"` if env var not set
- [ ] **VER-02**: User can view the app version on the public frontend settings/profile page (fetched from `GET /api/version`)
- [ ] **VER-03**: Admin can view the app version on the admin frontend settings page (fetched from `GET /api/version`)

### Dokploy Deployment (DPLY)

Three separate Dokploy Application services, each built from its own Dockerfile at repo root. Dokploy-managed PostgreSQL (not containerized by us).

- [ ] **DPLY-01**: Backend is deployed as a Dokploy Application service with `Dockerfile.backend`, correct env vars (`SPECTRA_MODE`, `APP_VERSION`, `SECRET_KEY`, `DATABASE_URL`, API keys), and Alembic migration runs successfully against Dokploy-managed PostgreSQL on first deploy
- [ ] **DPLY-02**: Public frontend is deployed as a Dokploy Application service with `Dockerfile.frontend` and `BACKEND_URL` pointing to the backend service (internal Dokploy network hostname)
- [ ] **DPLY-03**: Admin frontend is deployed as a Dokploy Application service with `Dockerfile.admin`, `BACKEND_URL`, and backend deployed with `SPECTRA_MODE=admin` for admin API routing
- [ ] **DPLY-04**: User file uploads persist across Dokploy redeployments — Dokploy Advanced → Mounts configured with named volume at `/app/uploads` before first production deploy
- [ ] **DPLY-05**: All 3 services are accessible via custom HTTPS domains with SSL (Traefik certificates managed by Dokploy)
- [ ] **DPLY-06**: `DEPLOYMENT.md` covers complete setup — Dokploy project creation, all 3 service configurations with env var tables, volume mount steps, domain/SSL assignment, `SECRET_KEY` generation, and a post-deploy smoke test checklist

## v7 Requirements (Future)

Deferred from v0.6 — acknowledged but not in current roadmap.

### Infrastructure Hardening

- **INFRA-01**: Redis for in-memory state (admin login lockout, token revocation) — single-instance limitation currently documented; only needed at 2+ replicas
- **INFRA-02**: CI/CD pipeline with Docker image registry — Dokploy direct-from-git is sufficient at single-developer scale; add when team grows
- **INFRA-03**: Read-only root filesystem in Docker containers — security enhancement; complex to configure, marginal single-instance benefit
- **INFRA-04**: Structured JSON logging — current logging readable; needed when adding log aggregation (Loki, Datadog, etc.)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Containerize PostgreSQL | Dokploy managed DB is simpler; managed backups; no added value |
| Single Docker Compose stack for Dokploy | User chose 3 separate services for independent rollback per service |
| Nginx container | Dokploy Traefik handles routing and TLS — no manual nginx needed |
| Gunicorn multi-worker backend | Breaks APScheduler (in-process scheduler); uvicorn single-worker correct for this deployment |
| NEXT_PUBLIC_ version var baked at build | Runtime env var approach chosen — no rebuild on version bump |
| CI/CD image registry | Direct-from-git Dokploy is sufficient for single-developer deployment |
| Query safety filter | Deferred from v0.5, still deferred — separate security milestone |
| Pydantic structured output for agents | Deferred from v0.5, still deferred — consistency milestone |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRE-01 | Phase 33 | Pending |
| PRE-02 | Phase 33 | Pending |
| PRE-03 | Phase 33 | Pending |
| PRE-04 | Phase 33 | Pending |
| PRE-05 | Phase 33 | Pending |
| DOCK-01 | Phase 34 | Pending |
| DOCK-02 | Phase 34 | Pending |
| DOCK-03 | Phase 34 | Pending |
| DOCK-04 | Phase 34 | Pending |
| DOCK-05 | Phase 34 | Pending |
| COMP-01 | Phase 35 | Pending |
| COMP-02 | Phase 35 | Pending |
| COMP-03 | Phase 35 | Pending |
| COMP-04 | Phase 35 | Pending |
| VER-01 | Phase 33 | Pending |
| VER-02 | Phase 33 | Pending |
| VER-03 | Phase 33 | Pending |
| DPLY-01 | Phase 36 | Pending |
| DPLY-02 | Phase 36 | Pending |
| DPLY-03 | Phase 36 | Pending |
| DPLY-04 | Phase 36 | Pending |
| DPLY-05 | Phase 36 | Pending |
| DPLY-06 | Phase 36 | Pending |

**Coverage:**
- v0.6 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-18 after initial definition*
