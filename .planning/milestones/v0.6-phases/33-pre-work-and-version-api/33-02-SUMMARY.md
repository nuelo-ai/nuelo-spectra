---
phase: 33-pre-work-and-version-api
plan: 02
subsystem: api, ui
tags: [nextjs, fastapi, health-check, version-endpoint, tanstack-query, dokploy]

# Dependency graph
requires:
  - phase: 33-pre-work-and-version-api
    provides: "next.config.ts standalone output and rewrites"
provides:
  - "GET /api/health on both frontends for Dokploy health monitoring"
  - "GET /version and GET /api/version backend endpoints"
  - "useAppVersion hook for both frontends"
  - "Version display in public and admin settings pages"
affects: [34-dockerfiles-and-compose, 35-dokploy-config-and-smoke-test]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Next.js App Router route handler for health checks", "Dual-mount FastAPI router for proxy compatibility"]

key-files:
  created:
    - frontend/src/app/api/health/route.ts
    - admin-frontend/src/app/api/health/route.ts
    - backend/app/routers/version.py
    - frontend/src/hooks/useAppVersion.ts
    - admin-frontend/src/hooks/useAppVersion.ts
  modified:
    - backend/app/main.py
    - backend/.env.example
    - frontend/src/components/settings/AccountInfo.tsx
    - admin-frontend/src/components/settings/SettingsForm.tsx

key-decisions:
  - "Dual-mount version router at / and /api prefix for proxy compatibility with both frontends"
  - "os.getenv for APP_VERSION instead of Pydantic Settings — deployment metadata with dev default"

patterns-established:
  - "Next.js route handlers take priority over rewrites for service-local endpoints"
  - "Dual-mount FastAPI routers when public and admin frontends use different proxy path structures"

requirements-completed: [PRE-04, PRE-05, VER-01, VER-02, VER-03]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 33 Plan 02: Health & Version API Summary

**Next.js health route handlers for Dokploy monitoring, backend version endpoint at /version and /api/version, and live version display in both frontend settings pages**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T01:03:32Z
- **Completed:** 2026-02-19T01:04:54Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Health route handlers on both frontends for Dokploy health check compatibility
- Backend version endpoint serving APP_VERSION and SPECTRA_MODE at dual paths
- Live version display in public frontend AccountInfo and admin frontend SettingsForm

## Task Commits

Each task was committed atomically:

1. **Task 1: Add health route handlers and backend version endpoint** - `0ffd30d` (feat)
2. **Task 2: Add useAppVersion hook and version display to both frontends** - `3caca06` (feat)

## Files Created/Modified
- `frontend/src/app/api/health/route.ts` - Next.js health check returning {status: "ok"}
- `admin-frontend/src/app/api/health/route.ts` - Next.js health check returning {status: "ok"}
- `backend/app/routers/version.py` - GET /version endpoint with APP_VERSION and SPECTRA_MODE
- `backend/app/main.py` - Added version router import and dual include_router calls
- `backend/.env.example` - Documented APP_VERSION env var
- `frontend/src/hooks/useAppVersion.ts` - TanStack Query hook fetching version via apiClient
- `admin-frontend/src/hooks/useAppVersion.ts` - TanStack Query hook fetching version via adminApiClient
- `frontend/src/components/settings/AccountInfo.tsx` - Added App Version field
- `admin-frontend/src/components/settings/SettingsForm.tsx` - Added App Version card with version and environment

## Decisions Made
- Dual-mounted version router at both `/` and `/api` prefix to support both proxy path structures (public strips /api/, admin keeps /api/)
- Used `os.getenv` directly for APP_VERSION instead of Pydantic Settings -- deployment metadata with simple default
- Show only version in public frontend, but both version and environment in admin frontend for operational visibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Health endpoints ready for Dokploy health check configuration
- Version endpoint ready for Docker build-arg injection of APP_VERSION
- All pre-work for Phase 34 (Dockerfiles) is complete

---
*Phase: 33-pre-work-and-version-api*
*Completed: 2026-02-19*
