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
  - "Replaced next.config.ts rewrites with catch-all route handler proxies -- rewrites buffer SSE, bake BACKEND_URL at build time, strip trailing slashes"
  - "BACKEND_URL is now a runtime env var (read by route handler at request time) -- no build-arg needed for Docker"

patterns-established:
  - "All frontend API calls use /api/ prefix routed through Next.js catch-all route handler proxy"
  - "BACKEND_URL configurable at runtime via process.env (not build-time)"

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
- Made backend URL configurable via `process.env.BACKEND_URL` with localhost:8000 fallback

### Post-Testing Update (proxy rewrite → route handler)
- Replaced `next.config.ts` rewrites with catch-all route handler proxies (`app/api/[...slug]/route.ts`) in both frontends
- Rewrites had 3 critical issues: (1) SSE buffering, (2) build-time BACKEND_URL, (3) trailing slash stripping causing auth header loss
- Route handlers solve all 3: stream SSE via ReadableStream, read BACKEND_URL at runtime, preserve request paths
- Backend middleware strips trailing slashes + `redirect_slashes=False` for consistent routing
- BACKEND_URL is now a **runtime** env var — no Docker build-arg needed (better than original approach)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix hardcoded localhost:8000 in useSSEStream.ts and register/page.tsx** - `1d63839` (fix)
2. **Task 2: Add standalone output and BACKEND_URL rewrite to both next.config.ts files** - `63fc340` (feat)

## Files Created/Modified
- `frontend/src/hooks/useSSEStream.ts` - SSE streaming fetch URL changed from direct localhost to /api/ proxy path
- `frontend/src/app/(auth)/register/page.tsx` - Signup status fetch URL changed from direct localhost to /api/ proxy path
- `frontend/next.config.ts` - Standalone output mode only (rewrites removed, replaced by route handler)
- `admin-frontend/next.config.ts` - Standalone output mode only (rewrites removed, replaced by route handler)
- `frontend/src/app/api/[...slug]/route.ts` - Catch-all proxy: strips /api/ prefix, streams SSE, reads BACKEND_URL at runtime
- `admin-frontend/src/app/api/[...slug]/route.ts` - Catch-all proxy: keeps /api/ prefix, forwards X-Admin-Token header
- `backend/app/main.py` - Added trailing slash middleware + redirect_slashes=False
- `backend/app/routers/chat_sessions.py` - Routes changed from "/" to "" on prefixed router
- `backend/app/routers/files.py` - Routes changed from "/" to "" on prefixed router

## Decisions Made
- BACKEND_URL uses `??` (nullish coalescing) with `"http://localhost:8000"` fallback so local dev works without setting env vars
- Replaced rewrites with route handler proxies after testing revealed 3 critical issues (SSE buffering, build-time BACKEND_URL, trailing slash stripping)
- BACKEND_URL is now runtime — no Docker build-arg needed, change URL without rebuilding image

## Deviations from Plan

- **Major:** next.config.ts rewrites replaced with catch-all route handler proxies after post-testing revealed SSE buffering, auth header loss from trailing slash 307 redirects, and build-time BACKEND_URL limitation. This is architecturally better for Docker deployment.

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
