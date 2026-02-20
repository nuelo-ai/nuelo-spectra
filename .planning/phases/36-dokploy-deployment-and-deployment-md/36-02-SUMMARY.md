---
phase: 36-dokploy-deployment-and-deployment-md
plan: 02
subsystem: infra
tags: [dokploy, docker-swarm, tailscale, split-horizon, next.js]

requires:
  - phase: 36-01
    provides: Public backend deployed, Tailscale installed, VPS firewall configured
provides:
  - Admin backend Dokploy service (SPECTRA_MODE=admin, Tailscale-only on port 8001)
  - Public frontend Dokploy service (proxying to public backend via Swarm DNS)
  - Admin frontend Dokploy service (proxying to admin backend via Swarm DNS, Tailscale-only on port 3001)
  - Split-horizon routing verified end-to-end
affects: [36-03]

tech-stack:
  added: []
  patterns: [docker-swarm-service-dns-for-inter-container-routing]

key-files:
  created: []
  modified:
    - Dockerfile.frontend
    - Dockerfile.admin
    - admin-frontend/src/components/layout/AdminHeader.tsx
    - backend/app/config.py
    - backend/app/services/admin/auth.py
    - backend/app/cli/__main__.py

key-decisions:
  - "BACKEND_URL uses Docker Swarm service names (not overlay IPs) — IPs change on every redeploy, service names are stable"
  - "Healthcheck uses 127.0.0.1 not localhost — Alpine wget resolves localhost to IPv6 [::1] but Next.js listens IPv4 only"
  - "seed-admin populates first_name/last_name with defaults — prevents null crash in admin header initials"

patterns-established:
  - "Swarm DNS: use service name as hostname for inter-container communication on dokploy-network"
  - "Container port 8000 for backend-to-backend, not published host port"

requirements-completed: [DPLY-02, DPLY-03, DPLY-04, DPLY-05]

duration: ~45min
completed: 2026-02-19
---

# Plan 36-02: Admin Backend + Both Frontends Summary

**Four Dokploy services running with split-horizon isolation — admin services Tailscale-only, public frontend proxying via Swarm DNS, all healthchecks passing**

## Performance

- **Duration:** ~45 min
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- All 4 Dokploy Application services running and healthy
- Admin backend and admin frontend reachable only via Tailscale (ports 8001/3001 blocked from public internet)
- Public frontend proxies to public backend via Docker Swarm service DNS
- Split-horizon routing verified: 5/5 tests passing

## Task Commits

1. **Task 1: Deploy admin backend** — Manual Dokploy deployment (no code commit)
2. **Task 2: Deploy both frontends** — Manual Dokploy deployment
3. **Task 3: Verify split-horizon routing** — 5 tests confirmed

**Bug fixes during execution:**
- `a25c243` — fix: use 127.0.0.1 in frontend healthchecks (IPv6 resolution)
- `d2fa0ef` — fix: handle null first_name/last_name in admin header
- `5be2fde` — fix: seed-admin populates first_name and last_name

## Decisions Made
- **Swarm service DNS over overlay IPs:** Container overlay IPs (e.g., 10.0.1.23) change on every redeploy. Using service names (e.g., `nuelo-spectra-publicbackend-ltiq2m`) as hostnames is stable and automatic via Docker Swarm DNS.
- **127.0.0.1 over localhost in healthchecks:** Alpine's BusyBox wget resolves localhost to [::1] (IPv6) first, but Next.js standalone only listens on 0.0.0.0 (IPv4). Using 127.0.0.1 forces IPv4.
- **seed-admin backfills names:** Admin users created without first/last names crashed the avatar initials component. Added ADMIN_FIRST_NAME/ADMIN_LAST_NAME env vars with defaults.

## Deviations from Plan

### Auto-fixed Issues

**1. Healthcheck IPv6 resolution failure**
- **Found during:** Task 2 (frontend deployment)
- **Issue:** Containers stuck at "health: starting" — wget connecting to [::1]:3000 which Next.js doesn't listen on
- **Fix:** Changed healthcheck URL from localhost to 127.0.0.1 in both frontend Dockerfiles
- **Files modified:** Dockerfile.frontend, Dockerfile.admin
- **Committed in:** `a25c243`

**2. Null admin name crash**
- **Found during:** Task 3 (admin frontend login test)
- **Issue:** `Cannot read properties of null (reading '0')` in AdminHeader initials when first_name is null
- **Fix:** Added null-safety in AdminHeader + seed-admin now populates names
- **Files modified:** AdminHeader.tsx, config.py, admin/auth.py, cli/__main__.py
- **Committed in:** `d2fa0ef`, `5be2fde`

---

**Total deviations:** 2 auto-fixed (both blocking)
**Impact on plan:** Both fixes necessary for services to reach healthy state. No scope creep.

## Issues Encountered
- Dokploy first-deploy timing: `.env` write before code directory exists — resolved by redeploying
- BACKEND_URL with overlay IPs broke on redeploy — switched to Swarm service DNS permanently

## Next Phase Readiness
- All 4 services running, ready for HTTPS domain configuration in Plan 36-03
- Public frontend BACKEND_URL will be updated to HTTPS domain after SSL provisioning
- Admin frontend BACKEND_URL stays as Swarm service DNS (no public domain)

---
*Phase: 36-dokploy-deployment-and-deployment-md*
*Completed: 2026-02-19*
