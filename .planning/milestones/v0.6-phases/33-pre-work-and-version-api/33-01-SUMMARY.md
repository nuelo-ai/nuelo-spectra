---
phase: 33-pre-work-and-version-api
plan: 01
subsystem: infra
tags: [nextjs, docker, standalone, proxy, sse, backend-url]

# Dependency graph
requires: []
provides:
  - "No hardcoded localhost:8000 in any frontend source file"
  - "Standalone output mode in both Next.js configs for Docker multi-stage builds"
  - "Runtime-configurable BACKEND_URL via process.env with localhost fallback"
affects: [34-docker-builds, 35-dokploy-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Next.js /api/ rewrite proxy for all backend calls (no direct localhost)"
    - "process.env.BACKEND_URL ?? fallback pattern for configurable backend hostname"
    - "output: standalone for Docker-compatible Next.js builds"

key-files:
  created: []
  modified:
    - frontend/src/hooks/useSSEStream.ts
    - frontend/src/app/(auth)/register/page.tsx
    - frontend/next.config.ts
    - admin-frontend/next.config.ts

key-decisions:
  - "BACKEND_URL uses nullish coalescing fallback to localhost:8000 -- works for local dev without env var"
  - "Rewrites baked at build time in standalone mode -- BACKEND_URL must be set at build time for Docker"

patterns-established:
  - "All frontend API calls use /api/ prefix routed through Next.js rewrite proxy"
  - "next.config.ts backend URL configurable via BACKEND_URL env var"

requirements-completed: [PRE-01, PRE-02, PRE-03]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 33 Plan 01: Pre-Work - Localhost Removal and Standalone Config Summary

**Removed hardcoded localhost:8000 from 2 frontend files, added standalone output and BACKEND_URL env var to both Next.js configs for Docker readiness**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T01:03:25Z
- **Completed:** 2026-02-19T01:04:22Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Eliminated all hardcoded `http://localhost:8000` references from frontend source (useSSEStream.ts and register/page.tsx now use `/api/` proxy)
- Added `output: "standalone"` to both `frontend/next.config.ts` and `admin-frontend/next.config.ts` for Docker multi-stage builds
- Made backend URL configurable via `process.env.BACKEND_URL` with localhost:8000 fallback in both rewrite configs

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix hardcoded localhost:8000 in useSSEStream.ts and register/page.tsx** - `1d63839` (fix)
2. **Task 2: Add standalone output and BACKEND_URL rewrite to both next.config.ts files** - `63fc340` (feat)

## Files Created/Modified
- `frontend/src/hooks/useSSEStream.ts` - SSE streaming fetch URL changed from direct localhost to /api/ proxy path
- `frontend/src/app/(auth)/register/page.tsx` - Signup status fetch URL changed from direct localhost to /api/ proxy path
- `frontend/next.config.ts` - Added standalone output mode and BACKEND_URL env var in rewrite destination (strips /api/)
- `admin-frontend/next.config.ts` - Added standalone output mode and BACKEND_URL env var in rewrite destination (keeps /api/)

## Decisions Made
- BACKEND_URL uses `??` (nullish coalescing) with `"http://localhost:8000"` fallback so local dev works without setting env vars
- In standalone mode, rewrites are baked at build time -- BACKEND_URL must be provided at `docker build` time, not container runtime. Acceptable per planning decision; Phase 35 will verify SSE streaming behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All frontend source files clean of hardcoded localhost -- ready for Docker containerization in Phase 34
- Both Next.js apps produce standalone builds -- ready for multi-stage Docker images
- BACKEND_URL configurable at build time -- Dokploy can set this per-service

---
*Phase: 33-pre-work-and-version-api*
*Completed: 2026-02-19*
