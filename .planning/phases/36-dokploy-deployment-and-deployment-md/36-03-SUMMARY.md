---
phase: 36-dokploy-deployment-and-deployment-md
plan: 03
subsystem: infra
tags: [dokploy, https, letsencrypt, deployment-guide, tailscale]

requires:
  - phase: 36-02
    provides: All 4 Dokploy services running with split-horizon isolation
provides:
  - Public frontend accessible via HTTPS with Let's Encrypt SSL
  - DEPLOYMENT.md production deployment guide (401 lines)
  - File upload volume persistence verified across redeployments
  - Full production smoke test passed (8/8)
affects: []

tech-stack:
  added: []
  patterns: [no-public-backend-domain, frontend-only-https-exposure]

key-files:
  created:
    - DEPLOYMENT.md
  modified:
    - Dockerfile.backend

key-decisions:
  - "No public domain for backend — all API traffic goes through frontend proxy via Swarm DNS, reducing attack surface"
  - "Single HTTPS domain (app.yourdomain.com) — only the frontend is publicly exposed"
  - "uploads dir created with chown before USER switch — Docker volumes inherit root ownership"

patterns-established:
  - "Frontend-only public exposure: backend has no public domain, frontend proxies all API calls internally"

requirements-completed: [DPLY-07, DPLY-08]

duration: ~30min
completed: 2026-02-19
---

# Plan 36-03: HTTPS Domains, Smoke Test, DEPLOYMENT.md Summary

**Public frontend live on HTTPS with Let's Encrypt SSL, backend internal-only via Swarm DNS, 8/8 smoke tests passed, DEPLOYMENT.md committed**

## Performance

- **Duration:** ~30 min
- **Tasks:** 4
- **Files created:** 1 (DEPLOYMENT.md)
- **Files modified:** 1 (Dockerfile.backend)

## Accomplishments
- Public frontend accessible at https://spectra.nuelo.ai with valid Let's Encrypt certificate
- Backend has no public domain — reduced attack surface vs original plan
- File upload persistence verified across Dokploy redeployments (named volume)
- Full 8-point production smoke test passed (public HTTPS, admin Tailscale, isolation)
- DEPLOYMENT.md written (401 lines) covering all deployment steps, env var tables, troubleshooting

## Task Commits

1. **Task 1: Configure HTTPS domain** — Manual DNS + Dokploy configuration
2. **Task 2: Full production smoke test** — 8/8 passed
3. **Task 3: Write DEPLOYMENT.md** — `1668e6b`
4. **Task 4: Final verification** — User approved

**Bug fix during execution:**
- `f9e8073` — fix: create uploads dir with appuser ownership before USER switch

## Decisions Made
- **No public backend domain:** Original plan called for `api.yourdomain.com`. User decided to keep backend internal-only since all API calls go through the frontend proxy. More secure, simpler DNS setup.
- **uploads dir ownership:** Docker named volumes inherit root ownership when the mount point doesn't pre-exist. Added `mkdir + chown` before `USER appuser` in Dockerfile.

## Deviations from Plan

### Architecture Change
**No public backend domain** — Plan specified `api.yourdomain.com` + `app.yourdomain.com`. User chose to expose only the frontend publicly, keeping backend accessible only via Swarm DNS internally. This is more secure and simplifies the deployment (one domain instead of two).

### Auto-fixed Issues

**1. Uploads permission denied**
- **Found during:** Task 2 (smoke test — file upload)
- **Issue:** `PermissionError: [Errno 13] Permission denied: 'uploads/...'` — named volume owned by root, container runs as appuser
- **Fix:** Added `mkdir -p /app/uploads && chown appuser:appuser /app/uploads` before USER switch in Dockerfile.backend
- **Committed in:** `f9e8073`

---

**Total deviations:** 1 architecture simplification + 1 auto-fixed bug
**Impact on plan:** Architecture change improves security. Bug fix necessary for file uploads to work.

## Issues Encountered
- None beyond the uploads permission fix

## Next Phase Readiness
- Phase 36 complete — all v0.6 requirements delivered
- v0.6 milestone ready for completion

---
*Phase: 36-dokploy-deployment-and-deployment-md*
*Completed: 2026-02-19*
