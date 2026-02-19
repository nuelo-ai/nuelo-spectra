---
phase: 34-dockerfiles-and-entrypoint
plan: 03
subsystem: infra
tags: [docker, nextjs, node-alpine, standalone, multi-stage]

# Dependency graph
requires:
  - phase: 34-dockerfiles-and-entrypoint
    plan: 01
    provides: "Per-Dockerfile .dockerignore files for build context exclusion"
provides:
  - "Dockerfile.frontend: production Docker image for public Next.js app"
  - "Dockerfile.admin: production Docker image for admin Next.js app"
affects: [35-docker-compose, 36-dokploy-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: ["3-stage Docker build (deps, builder, runner) for Next.js standalone", "Runtime ENV for BACKEND_URL (not build ARG)", "Non-root nextjs user UID 1001"]

key-files:
  created:
    - Dockerfile.frontend
    - Dockerfile.admin
  modified: []

key-decisions:
  - "BACKEND_URL as runtime ENV not build ARG — route handler proxies read at request time, no build-arg needed"
  - "ENV set in both builder and runner stages — builder needs it for any build-time references, runner needs it for runtime"
  - "admin-frontend skips public/ COPY — no public directory exists in admin app"

patterns-established:
  - "Next.js standalone Docker pattern: deps (npm ci) -> builder (npm run build) -> runner (node server.js)"
  - "Runtime BACKEND_URL via ENV default — override with docker run -e or Dokploy env config"

requirements-completed: [DOCK-04, DOCK-05]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 34 Plan 03: Frontend Dockerfiles Summary

**Two 3-stage node:22-alpine Dockerfiles for public and admin Next.js apps with runtime BACKEND_URL, non-root user, and wget healthcheck**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T03:25:53Z
- **Completed:** 2026-02-19T03:27:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Dockerfile.frontend: 3-stage standalone build for public Next.js app with public/ assets, non-root user, healthcheck
- Dockerfile.admin: identical pattern for admin app, skipping public/ COPY (no public assets)
- Both use runtime ENV BACKEND_URL (adjusted from plan's build ARG per Phase 33 route handler proxy changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write Dockerfile.frontend for public Next.js app** - `6be3c0e` (feat)
2. **Task 2: Write Dockerfile.admin for admin Next.js app** - `14cde32` (feat)

## Files Created/Modified
- `Dockerfile.frontend` - 3-stage production Docker image for public frontend (50 lines)
- `Dockerfile.admin` - 3-stage production Docker image for admin frontend (50 lines)

## Decisions Made
- Used `ENV BACKEND_URL=http://localhost:8000` instead of `ARG BACKEND_URL` as specified in the plan. Phase 33 replaced next.config.ts rewrites with catch-all route handler proxies that read BACKEND_URL at request time (runtime), so no build-arg is needed. ENV is set in both builder and runner stages.
- Skipped `COPY --from=builder /app/public ./public` in Dockerfile.admin since admin-frontend has no public/ directory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Changed BACKEND_URL from ARG to ENV**
- **Found during:** Task 1 (Dockerfile.frontend)
- **Issue:** Plan specified `ARG BACKEND_URL` for build-time rewrite baking, but Phase 33 replaced rewrites with route handler proxies that read BACKEND_URL at runtime
- **Fix:** Used `ENV BACKEND_URL=http://localhost:8000` in both builder and runner stages instead of ARG
- **Files modified:** Dockerfile.frontend, Dockerfile.admin
- **Verification:** Both Dockerfiles use ENV not ARG; confirmed next.config.ts has no rewrites
- **Committed in:** 6be3c0e, 14cde32

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Essential correction per Phase 33 architectural change. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three Dockerfiles now exist (backend from 34-02, frontend and admin from this plan)
- All .dockerignore files exist (from 34-01)
- Backend entrypoint exists (from 34-01)
- Ready for docker-compose or Dokploy deployment configuration

## Self-Check: PASSED

All 2 created files verified on disk. Both task commits (6be3c0e, 14cde32) verified in git log.

---
*Phase: 34-dockerfiles-and-entrypoint*
*Completed: 2026-02-19*
