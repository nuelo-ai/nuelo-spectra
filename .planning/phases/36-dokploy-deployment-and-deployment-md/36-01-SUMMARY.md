---
phase: 36-dokploy-deployment-and-deployment-md
plan: 01
subsystem: infra
tags: [dokploy, postgresql, tailscale, docker, deployment, firewall, iptables]

# Dependency graph
requires:
  - phase: 35-docker-compose-and-local-validation
    provides: Validated Dockerfiles and compose.yaml for all 3 services
provides:
  - Dokploy-managed PostgreSQL (spectra-db) with asyncpg DATABASE_URL
  - Tailscale VPN overlay on Dokploy host (100.115.125.119) for admin service access
  - iptables DOCKER-USER firewall rules blocking ports 8001/3001 from public internet
  - Public backend Dokploy Application service (SPECTRA_MODE=public) with Alembic migrations applied
  - spectra-uploads named volume mounted at /app/uploads before first deploy
  - Shared SECRET_KEY generated for both backend services
affects: [36-02-PLAN, 36-03-PLAN]

# Tech tracking
tech-stack:
  added: [dokploy, tailscale]
  patterns: [dokploy-application-service, iptables-docker-user-chain, tailscale-vpn-overlay]

key-files:
  created: []
  modified: []

key-decisions:
  - "iptables DOCKER-USER chain instead of VPS cloud firewall — Hostinger VPS, Docker bypasses UFW"
  - "Tailscale subnet routing not needed — dokploy-network is Swarm overlay (VXLAN), published host ports sufficient"
  - "Dokploy branch set to develop for testing deployment before final merge to master"

patterns-established:
  - "Dokploy Application pattern: Git source, Dockerfile build, env vars in Environment tab, volume mounts in Advanced tab before first deploy"
  - "iptables DOCKER-USER chain: the correct firewall chain for Docker host port protection (UFW/iptables INPUT chain is bypassed by Docker)"

requirements-completed: [DPLY-01, DPLY-05, DPLY-06]

# Metrics
duration: manual (human-action tasks)
completed: 2026-02-19
---

# Phase 36 Plan 01: Prerequisites and Public Backend Deployment Summary

**Dokploy PostgreSQL + Tailscale VPN + iptables firewall + public backend deployed with spectra-uploads volume and Alembic migrations**

## Performance

- **Duration:** Manual execution (all 4 tasks were human-action checkpoints in Dokploy/server)
- **Started:** 2026-02-19
- **Completed:** 2026-02-19
- **Tasks:** 4
- **Files modified:** 0 (infrastructure-only plan, no code changes)

## Accomplishments
- Dokploy-managed PostgreSQL (spectra-db) running with asyncpg-compatible DATABASE_URL and shared SECRET_KEY generated
- Tailscale installed on Dokploy host (IP: 100.115.125.119), iptables DOCKER-USER rules blocking ports 8001/3001 from public internet
- Public backend (nuelo-spectra-publicbackend) deployed to Dokploy with SPECTRA_MODE=public, Alembic migrations applied, health endpoint returning 200
- spectra-uploads named volume mounted at /app/uploads before first deploy, LLM provider env vars validated

## Task Commits

This plan had no code commits — all 4 tasks were manual Dokploy/server infrastructure setup (checkpoint:human-action and checkpoint:human-verify).

1. **Task 1: Create Dokploy PostgreSQL database and generate SECRET_KEY** - No commit (manual Dokploy UI)
2. **Task 2: Install Tailscale on Dokploy host and configure VPS firewall** - No commit (manual server setup)
3. **Task 3: Deploy public backend to Dokploy with volume mount** - No commit (manual Dokploy UI)
4. **Task 4: Verify public backend foundational readiness** - No commit (verification only)

## Files Created/Modified

None — this was an infrastructure-only plan with no code changes.

## Decisions Made

1. **iptables DOCKER-USER chain instead of VPS cloud firewall** — Hostinger VPS does not offer a cloud-level firewall. Docker bypasses UFW/iptables INPUT chain, so DOCKER-USER chain is the correct place to block external access to published container ports.

2. **Tailscale subnet routing to Docker containers not needed** — dokploy-network is a Docker Swarm overlay network (VXLAN), not a standard bridge. Published host ports (8001, 3001) are sufficient for admin service access via Tailscale. No --advertise-routes needed.

3. **Dokploy branch set to `develop`** — Testing deployment pipeline against develop branch before final merge to master. Branch can be changed in Dokploy General tab later.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tailscale subnet routing skipped**
- **Found during:** Task 2
- **Issue:** Plan specified `--advertise-routes` for dokploy-network subnet, but dokploy-network is a Swarm overlay (VXLAN) — subnet routing would not work for overlay networks
- **Fix:** Skipped subnet routing entirely. Published host ports (8001/3001) accessible via Tailscale IP are sufficient for admin service access
- **Verification:** `curl http://100.115.125.119:8000/health` returns 200 from Tailscale client

**2. [Rule 3 - Blocking] iptables DOCKER-USER instead of VPS cloud firewall**
- **Found during:** Task 2
- **Issue:** Plan specified VPS cloud firewall, but Hostinger VPS has no cloud-level firewall feature. Docker bypasses UFW.
- **Fix:** Used `iptables -I DOCKER-USER` rules to drop incoming traffic on ports 8001 and 3001 from non-Tailscale sources
- **Verification:** External port scan shows ports 8001/3001 as filtered/closed

---

**Total deviations:** 2 auto-fixed (2 blocking issues — infrastructure reality vs plan assumptions)
**Impact on plan:** Both deviations were necessary adaptations to actual server environment. Security posture achieved matches plan intent.

## Issues Encountered

None beyond the deviations documented above.

## User Setup Required

None — all infrastructure setup was completed during plan execution.

## Next Phase Readiness
- Public backend is live and healthy — ready for admin backend deployment (Plan 36-02)
- Tailscale IP (100.115.125.119) is available for admin service BACKEND_URL configuration
- iptables rules protect admin ports — admin services can be deployed on ports 8001/3001
- DATABASE_URL and SECRET_KEY are ready to reuse for admin backend service
- spectra-uploads volume pattern established for reuse

## Self-Check: PASSED

- SUMMARY.md: FOUND
- No code commits expected (infrastructure-only plan)
- STATE.md: Updated (position, decisions, session)
- ROADMAP.md: Updated (1/3 plans, in progress)
- REQUIREMENTS.md: Updated (DPLY-01, DPLY-05, DPLY-06 marked complete)

---
*Phase: 36-dokploy-deployment-and-deployment-md*
*Completed: 2026-02-19*
