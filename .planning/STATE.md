# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 34 — Dockerfiles and Entrypoint

## Current Position

Phase: 34 of 36 (Dockerfiles and Entrypoint)
Plan: 3 of 3 in current phase (phase 34 complete)
Status: Phase 34 complete — all Dockerfiles and entrypoint created
Last activity: 2026-02-19 — Completed plan 34-03 (frontend Dockerfiles)

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

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment) — this milestone
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)

### Blockers/Concerns

- Dokploy internal service hostname format: MEDIUM confidence — verify in Dokploy UI after first backend deploy before setting `BACKEND_URL` in frontend services; fallback is public HTTPS domain for `BACKEND_URL`
- ~~SSE streaming through Next.js rewrite proxy in Docker~~ RESOLVED — route handler proxy streams SSE correctly, verified with curl
- ~~`pg_isready` availability in `python:3.12-slim`: not included by default~~ RESOLVED — `postgresql-client` installed via apt-get in Dockerfile.backend runtime stage
- Phase 34 plans reference BACKEND_URL as Docker build-arg for rewrites — this is no longer needed; BACKEND_URL is runtime env var now. Plans (especially 34-03) need adjustment during execution.

## Session Continuity

Last session: 2026-02-19
Stopped at: Completed 34-02-PLAN.md (backend Dockerfile)
Resume with: `/gsd:execute-phase 34` (continues with plan 34-03)
Note: Phase 34 plans reference BACKEND_URL as Docker build-arg — this is no longer needed; BACKEND_URL is runtime env var now. Plans (especially 34-03) need adjustment during execution.
