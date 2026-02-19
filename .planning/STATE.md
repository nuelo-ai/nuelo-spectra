# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 36 — Dokploy Deployment and DEPLOYMENT.md

## Current Position

Phase: 36 of 36 (Dokploy Deployment and DEPLOYMENT.md)
Plan: 2 of 3 in current phase (plan 36-01 complete)
Status: Phase 36 in progress — public backend deployed to Dokploy
Last activity: 2026-02-19 — Completed plan 36-01 (Prerequisites + public backend deployment)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 ✅ | v0.6 🚧

## Performance Metrics

**Velocity (v0.5):**
- Total plans completed: 24 (Phases 26-32 complete)
- Total execution time: ~2 days (Feb 16-17, 2026)
- Plans per day: ~12 plans/day

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

Recent decisions affecting v0.6:
- 3 separate Dokploy Application services (not single Compose stack) — independent rollback per service
- `python:3.12-slim` for backend base image — glibc required for asyncpg/psycopg binary wheels; Alpine incompatible
- `node:22-alpine` for both frontend base images — Alpine safe for Next.js; saves ~100MB per image
- `output: 'standalone'` in both Next.js configs — required for multi-stage Docker images
- Dokploy-managed PostgreSQL — simpler, managed backups, no containerization needed
- `.dockerignore` before any `docker build` — non-negotiable security gate
- [Phase 33]: BACKEND_URL uses nullish coalescing fallback to localhost:8000 for local dev compatibility
- [Phase 33]: Dual-mount version router at / and /api prefix for proxy compatibility with both frontends
- [Phase 33]: APP_VERSION in Pydantic Settings (moved from os.getenv) — validates at startup, consistent with other config
- [Phase 33 post-test]: Replaced next.config.ts rewrites with catch-all route handler proxies — rewrites buffer SSE, bake BACKEND_URL at build time, strip trailing slashes
- [Phase 33 post-test]: Backend middleware strips trailing slashes + redirect_slashes=False — consistent routing regardless of caller
- [Phase 33 post-test]: BACKEND_URL is now runtime env var (read by route handler at request time) — no build-arg needed for Docker, better than original rewrite approach
- [Phase 34-01]: BuildKit per-Dockerfile .dockerignore naming — each service excludes other service dirs to minimize build context
- [Phase 34-01]: Entrypoint uses /app/.venv/bin/python explicitly (uv installs to .venv)
- [Phase 34-01]: 30 retries x 2s = 60s max PostgreSQL wait in entrypoint
- [Phase 34-02]: uv binary from ghcr.io/astral-sh/uv:latest, UV_COMPILE_BYTECODE=1 for faster startup
- [Phase 34-02]: No CMD in backend Dockerfile — entrypoint handles everything
- [Phase 34-02]: postgresql-client installed via apt-get for pg_isready (resolved blocker)
- [Phase 34-03]: BACKEND_URL as runtime ENV not build ARG in frontend Dockerfiles — route handler proxies read at request time
- [Phase 34-03]: admin-frontend Dockerfile skips public/ COPY (no public assets exist)
- [Phase 35-01]: Modern compose.yaml naming (no version field, not docker-compose.yml)
- [Phase 35-01]: env_file for secrets with inline environment overrides for non-secret config
- [Phase 35-01]: Admin frontend maps host 3001 to container 3000 (no PORT env var override)
- [Phase 35-01]: Backend healthcheck via depends_on service_healthy for startup ordering
- [Phase 36-01]: iptables DOCKER-USER chain instead of VPS cloud firewall — Hostinger VPS, Docker bypasses UFW
- [Phase 36-01]: Tailscale subnet routing not needed — dokploy-network is Swarm overlay (VXLAN), published host ports sufficient
- [Phase 36-01]: Dokploy branch set to develop for testing deployment before final merge to master

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment) — this milestone
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)

### Blockers/Concerns

- ~~Dokploy internal service hostname format: MEDIUM confidence~~ RESOLVED — verified after public backend deploy; Dokploy uses Docker Swarm overlay network, published host ports accessible via Tailscale IP
- ~~SSE streaming through Next.js rewrite proxy in Docker~~ RESOLVED — route handler proxy streams SSE correctly, verified with curl
- ~~`pg_isready` availability in `python:3.12-slim`: not included by default~~ RESOLVED — `postgresql-client` installed via apt-get in Dockerfile.backend runtime stage
- ~~Phase 34 plans reference BACKEND_URL as Docker build-arg for rewrites~~ RESOLVED — 34-03 used ENV not ARG, adjusted during execution

## Session Continuity

Last session: 2026-02-19
Stopped at: Completed 36-01-PLAN.md (Prerequisites + public backend deployment)
Resume with: Continue Phase 36, Plan 36-02 (Admin backend + both frontends deployment)
