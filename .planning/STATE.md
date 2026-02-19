# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 33 — Pre-Work and Version API

## Current Position

Phase: 33 of 36 (Pre-Work and Version API)
Plan: 1 of 2 in current phase
Status: Executing
Last activity: 2026-02-19 — Completed 33-01-PLAN.md (pre-work localhost removal + standalone config)

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
- Runtime `process.env.BACKEND_URL` in rewrites (not build-time `NEXT_PUBLIC_`) — no image rebuild on URL change
- Dokploy-managed PostgreSQL — simpler, managed backups, no containerization needed
- `.dockerignore` before any `docker build` — non-negotiable security gate
- [Phase 33]: BACKEND_URL uses nullish coalescing fallback to localhost:8000 for local dev compatibility

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment) — this milestone
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)

### Blockers/Concerns

- Dokploy internal service hostname format: MEDIUM confidence — verify in Dokploy UI after first backend deploy before setting `BACKEND_URL` in frontend services; fallback is public HTTPS domain for `BACKEND_URL`
- SSE streaming through Next.js rewrite proxy in Docker: LOW confidence — verify during Phase 35 smoke test; if proxy doesn't stream correctly, `useSSEStream.ts` may need `NEXT_PUBLIC_BACKEND_URL` approach
- `pg_isready` availability in `python:3.12-slim`: not included by default — install `postgresql-client` via apt-get OR use pure-Python TCP loop; decide in Phase 34

## Session Continuity

Last session: 2026-02-19
Stopped at: Completed 33-01-PLAN.md
Resume with: `/gsd:execute-phase 33` (plan 02 next)
