---
phase: 34-dockerfiles-and-entrypoint
plan: 01
subsystem: infra
tags: [docker, dockerignore, entrypoint, postgresql, alembic, uvicorn]

# Dependency graph
requires:
  - phase: 33-runtime-env-and-config
    provides: "Runtime env vars (BACKEND_URL, DATABASE_URL) and alembic migration setup"
provides:
  - "Three per-Dockerfile .dockerignore files excluding secrets and cross-service dirs"
  - "Backend docker-entrypoint.sh with pg wait, alembic migrate, exec uvicorn"
affects: [34-02-PLAN, 34-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["BuildKit per-Dockerfile .dockerignore naming", "Bounded pg_isready retry loop in entrypoint", "exec for PID 1 signal handling"]

key-files:
  created:
    - Dockerfile.backend.dockerignore
    - Dockerfile.frontend.dockerignore
    - Dockerfile.admin.dockerignore
    - backend/docker-entrypoint.sh
  modified: []

key-decisions:
  - "Used BuildKit per-Dockerfile naming (Dockerfile.{service}.dockerignore) for service-specific exclusions"
  - "Entrypoint uses /app/.venv/bin/python explicitly (uv installs to .venv, not system python)"
  - "30 retries x 2s = 60s max PostgreSQL wait — sufficient for cold-start without blocking indefinitely"

patterns-established:
  - "Per-Dockerfile .dockerignore: each service excludes other service directories to minimize build context"
  - "Entrypoint pattern: parse DATABASE_URL -> wait for DB -> run migrations -> exec app server"

requirements-completed: [DOCK-01, DOCK-02]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 34 Plan 01: Dockerignore and Entrypoint Summary

**Three BuildKit .dockerignore files excluding secrets/cross-service dirs, plus backend entrypoint with pg_isready wait, alembic migrations, and exec uvicorn as PID 1**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T03:22:29Z
- **Completed:** 2026-02-19T03:23:41Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Three per-Dockerfile .dockerignore files prevent secrets (.env), virtual envs, node_modules, and cross-service directories from leaking into Docker build context
- Backend entrypoint script parses DATABASE_URL (supports asyncpg scheme), waits for PostgreSQL with bounded retries, runs alembic migrations, starts uvicorn via exec as PID 1

## Task Commits

Each task was committed atomically:

1. **Task 1: Create per-Dockerfile .dockerignore files** - `1203910` (feat)
2. **Task 2: Create backend docker-entrypoint.sh** - `23b7108` (feat)

## Files Created/Modified
- `Dockerfile.backend.dockerignore` - Build context exclusions for backend image (excludes frontend/, admin-frontend/)
- `Dockerfile.frontend.dockerignore` - Build context exclusions for frontend image (excludes backend/, admin-frontend/)
- `Dockerfile.admin.dockerignore` - Build context exclusions for admin image (excludes backend/, frontend/)
- `backend/docker-entrypoint.sh` - Container entrypoint: pg wait, alembic migrate, exec uvicorn

## Decisions Made
- Used BuildKit per-Dockerfile naming convention (`Dockerfile.{service}.dockerignore`) — each service gets its own ignore file with targeted cross-service exclusions
- Entrypoint uses `/app/.venv/bin/python` explicitly since uv installs to .venv (not system python)
- 30 retries x 2s sleep = 60s max PostgreSQL wait — sufficient for container cold-start without blocking indefinitely
- `!**/.env.example` negation ensures example env files are available in images for reference

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- .dockerignore files ready for Dockerfiles in plan 34-02
- docker-entrypoint.sh ready to be COPYed and set as ENTRYPOINT in backend Dockerfile
- Note: backend Dockerfile must `apt-get install postgresql-client` to provide pg_isready

## Self-Check: PASSED

All 4 created files verified on disk. Both task commits (1203910, 23b7108) verified in git log.

---
*Phase: 34-dockerfiles-and-entrypoint*
*Completed: 2026-02-19*
