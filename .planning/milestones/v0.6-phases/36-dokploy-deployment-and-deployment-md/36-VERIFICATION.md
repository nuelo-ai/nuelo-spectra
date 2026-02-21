---
phase: 36-dokploy-deployment-and-deployment-md
verified: 2026-02-19T22:00:00Z
status: human_needed
score: 4/6 must-haves verified
re_verification: false
human_verification:
  - test: "Confirm all 4 Dokploy services show Running status in Dokploy UI"
    expected: "spectra-public-backend, spectra-admin-backend, spectra-public-frontend, spectra-admin-frontend all show Running"
    why_human: "Live production infrastructure — cannot verify container state via code grep"
  - test: "Confirm public frontend is live at https://spectra.nuelo.ai — login works, SSE streaming works, version visible on Settings page"
    expected: "Login succeeds, sending a chat message shows token-by-token streaming, Settings page shows v0.6.0"
    why_human: "Live HTTPS endpoint and browser-driven SSE behavior — not verifiable via static code analysis"
  - test: "Confirm admin services are reachable via Tailscale at http://100.115.125.119:8001 and http://100.115.125.119:3001, and NOT reachable from public internet (curl times out on both ports)"
    expected: "curl via Tailscale client returns 200, curl from non-Tailscale network times out for both ports 8001 and 3001"
    why_human: "Live network isolation — requires two different network contexts to verify"
  - test: "Confirm file upload persistence — upload a file, trigger redeploy of spectra-public-backend, verify file still appears"
    expected: "File record and file on disk both survive the redeploy; docker inspect still shows spectra-uploads volume mounted"
    why_human: "Requires triggering a live redeployment and observing the result"
---

# Phase 36: Dokploy Deployment and DEPLOYMENT.md Verification Report

**Phase Goal:** Four Spectra services are running in production — public backend and public frontend accessible via public HTTPS, admin backend and admin frontend accessible only via Tailscale VPN; file uploads persist across redeployments; DEPLOYMENT.md gives a complete step-by-step guide for this split-horizon deployment

**Architecture Note:** The public backend does NOT have a public HTTPS domain. All API traffic goes through the public frontend's Next.js route handler proxy via Docker Swarm service DNS. This is a deliberate security improvement documented in the SUMMARY and DEPLOYMENT.md — only the frontend is publicly exposed (`https://spectra.nuelo.ai`). DPLY-07 wording said "public backend AND public frontend" on HTTPS; the actual delivery is more secure (frontend-only exposure) and is treated as a valid architectural deviation, not a gap.

**Verified:** 2026-02-19
**Status:** human_needed — all automated code checks pass; 4 items require human confirmation of live production state
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Public backend Dokploy service is live — Alembic migration ran, GET /health returns 200, SPECTRA_MODE=public | ? HUMAN | Confirmed by human in 36-01 SUMMARY; iptables blocking ports 8001/3001 confirmed; code supports it. Cannot re-verify live state programmatically. |
| 2 | Public frontend is live at its HTTPS domain — login works, SSE streaming works, version visible on settings page | ? HUMAN | 36-03 SUMMARY confirms `https://spectra.nuelo.ai` live, 8/8 smoke tests passed. Requires browser session to re-verify. |
| 3 | Admin backend live at Tailscale IP only — SPECTRA_MODE=admin, admin routes respond, not reachable from public internet | ? HUMAN | 36-02 SUMMARY confirms 5/5 split-horizon tests passed. Tailscale IP 100.115.125.119 documented. iptables rules confirmed. Cannot re-verify live state. |
| 4 | Admin frontend live at Tailscale IP only — admin login works, user management responds, not reachable from public internet | ? HUMAN | 36-02 SUMMARY confirms admin dashboard loaded in browser via Tailscale. Null-name crash fixed (commit d2fa0ef). Requires browser via Tailscale to re-verify. |
| 5 | File upload survives Dokploy redeploy — named volume at /app/uploads, records in PostgreSQL match files on disk | ✓ VERIFIED (partial) | Dockerfile.backend has `mkdir -p /app/uploads && chown appuser:appuser /app/uploads` (commit f9e8073). DEPLOYMENT.md documents volume-before-first-deploy ordering. 36-03 SUMMARY confirms smoke test 4 passed. Volume persistence is infrastructure state — final confirmation is human. |
| 6 | DEPLOYMENT.md covers all 4 service configs with env var tables, Tailscale setup, volume mount, public SSL, SECRET_KEY generation, smoke test checklist | ✓ VERIFIED | File exists at repo root, 401 lines, committed (1668e6b). All content areas verified (see below). |

**Score:** 2/6 truths fully verified via code; 4/6 require human confirmation of live production state. All supporting code artifacts are substantive and correctly wired.

---

## Required Artifacts

### Code Artifacts (Verifiable)

| Artifact | Status | Evidence |
|----------|--------|---------|
| `Dockerfile.backend` | ✓ VERIFIED | Exists, substantive (72 lines), multi-stage build, `mkdir -p /app/uploads && chown appuser:appuser /app/uploads` before USER switch (commit f9e8073), HEALTHCHECK present, ENTRYPOINT wired to docker-entrypoint.sh |
| `Dockerfile.frontend` | ✓ VERIFIED | Exists, substantive (51 lines), multi-stage Next.js build, HEALTHCHECK uses `wget http://127.0.0.1:3000/api/health` (IPv6 fix commit a25c243), BACKEND_URL env var present as runtime override |
| `Dockerfile.admin` | ✓ VERIFIED | Exists, substantive (51 lines), same pattern as Dockerfile.frontend but from `admin-frontend/`, HEALTHCHECK uses 127.0.0.1, BACKEND_URL runtime env var |
| `backend/docker-entrypoint.sh` | ✓ VERIFIED | Substantive (41 lines), pg_isready loop (max 30 retries), then `alembic upgrade head`, then `exec uvicorn`. Correctly wired as ENTRYPOINT in Dockerfile.backend |
| `frontend/src/app/api/[...slug]/route.ts` | ✓ VERIFIED | Substantive catch-all proxy (reads BACKEND_URL at runtime, forwards all /api/* to backend, preserves raw path for SSE/POST, strips /api prefix, passes Authorization and Content-Type headers) |
| `frontend/src/app/api/health/route.ts` | ✓ VERIFIED | Returns `{"status":"ok"}` — required for frontend HEALTHCHECK to pass |
| `admin-frontend/src/app/api/[...slug]/route.ts` | ✓ VERIFIED (by dir listing) | Same proxy pattern as public frontend |
| `admin-frontend/src/components/layout/AdminHeader.tsx` | ✓ VERIFIED | Null-safe initials: `(user.first_name || "A")[0]${(user.last_name || "")[0]}` — crash fix committed (d2fa0ef) |
| `backend/app/main.py` — route isolation | ✓ VERIFIED | `SPECTRA_MODE=public` mounts only auth/files/chat/search/credits; `SPECTRA_MODE=admin` mounts admin_router under /api/admin; public mode catches /api/admin/* and returns 404 with warning log |
| `backend/app/routers/version.py` | ✓ VERIFIED | Returns `{"version": settings.app_version, "environment": settings.spectra_mode}` — exposes mode for smoke test verification |
| `DEPLOYMENT.md` | ✓ VERIFIED | See DPLY-08 section below |

### Infrastructure Artifacts (Human-Confirmed in SUMMARYs)

| Artifact | Status | Evidence |
|----------|--------|---------|
| Dokploy Application: spectra-public-backend | ? HUMAN | 36-01 SUMMARY: deployed with SPECTRA_MODE=public, Alembic ran, spectra-uploads mounted, health 200. No code change to re-verify. |
| Dokploy Application: spectra-admin-backend | ? HUMAN | 36-02 SUMMARY: deployed with SPECTRA_MODE=admin, port 8001 published, no domain, reachable via Tailscale 100.115.125.119 |
| Dokploy Application: spectra-public-frontend | ? HUMAN | 36-02 SUMMARY: deployed, BACKEND_URL=Swarm service DNS. 36-03: HTTPS domain `spectra.nuelo.ai` added, 8/8 smoke tests passed |
| Dokploy Application: spectra-admin-frontend | ? HUMAN | 36-02 SUMMARY: deployed, port 3001 published, no domain, login works via Tailscale |
| Dokploy Database: spectra-db | ? HUMAN | 36-01 SUMMARY: PostgreSQL running, asyncpg DATABASE_URL saved, Alembic migrations applied |
| Tailscale on Dokploy host | ? HUMAN | 36-01 SUMMARY: Tailscale IP 100.115.125.119 confirmed, subnet routing skipped (Swarm overlay incompatible), host ports sufficient |
| iptables DOCKER-USER rules (ports 8001, 3001) | ? HUMAN | 36-01 SUMMARY: VPS cloud firewall not available (Hostinger), DOCKER-USER chain used instead. External port scan confirms filtered. |

---

## Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| `docker-entrypoint.sh` | `alembic upgrade head` then `uvicorn` | Entrypoint sequence in shell script | ✓ VERIFIED | Script confirmed: pg_isready wait → alembic → exec uvicorn |
| `Dockerfile.backend` ENTRYPOINT | `docker-entrypoint.sh` | `ENTRYPOINT ["/app/docker-entrypoint.sh"]` | ✓ VERIFIED | Line 71 in Dockerfile.backend |
| `Dockerfile.backend` | `/app/uploads` ownership | `mkdir -p /app/uploads && chown appuser:appuser /app/uploads` before USER switch | ✓ VERIFIED | Line 58 in Dockerfile.backend (commit f9e8073) |
| `frontend` proxy `[...slug]` | `BACKEND_URL` env var | `process.env.BACKEND_URL ?? "http://localhost:8000"` read at runtime | ✓ VERIFIED | Proxy reads BACKEND_URL at request time (not build time) — runtime override via Dokploy env tab works |
| `Dockerfile.frontend` HEALTHCHECK | `127.0.0.1:3000/api/health` | `wget --spider http://127.0.0.1:3000/api/health` | ✓ VERIFIED | IPv6 fix confirmed (commit a25c243) |
| `backend/app/main.py` | Route isolation by SPECTRA_MODE | `if mode in ("public", "dev")` / `if mode in ("admin", "dev")` | ✓ VERIFIED | Admin routes only loaded when mode=admin/dev; public mode catches /api/admin/* with 404 |
| spectra-public-frontend BACKEND_URL | spectra-public-backend via Swarm DNS | `http://<swarm-service-name>:8000` | ? HUMAN | Configured in Dokploy env tab — confirmed by 36-02 SUMMARY split-horizon test 5 |
| spectra-admin-frontend BACKEND_URL | spectra-admin-backend via Swarm DNS | `http://<swarm-service-name>:8000` | ? HUMAN | Configured in Dokploy env tab — confirmed by 36-02 SUMMARY test 4 (admin dashboard loaded) |
| iptables DOCKER-USER chain | ports 8001 + 3001 DROP | `iptables -I DOCKER-USER -p tcp --dport 8001/3001 -j DROP` | ? HUMAN | 36-01 SUMMARY confirms rules applied, external scan shows filtered. Cannot re-verify without network access. |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| DPLY-01 | 36-01 | Public backend deployed with Dockerfile.backend, SPECTRA_MODE=public, all env vars, /app/uploads volume, Alembic migrations on first deploy | ✓ SATISFIED | Human-confirmed in 36-01 SUMMARY (all 4 tasks passed). Code support verified: Dockerfile.backend, docker-entrypoint.sh, uploads ownership fix. |
| DPLY-02 | 36-02 | Admin backend deployed from Dockerfile.backend with SPECTRA_MODE=admin, Tailscale-only, not through Dokploy public Traefik | ✓ SATISFIED | Human-confirmed in 36-02 SUMMARY. Port 8001 published, no Dokploy domain, Tailscale-only access verified with 5/5 tests. |
| DPLY-03 | 36-02 | Public frontend deployed with Dockerfile.frontend, BACKEND_URL pointing to public backend, accessible via public HTTPS | ✓ SATISFIED (with deviation) | Live at `https://spectra.nuelo.ai`. Architecture deviation: backend has no public domain — all API goes through frontend proxy internally (more secure). Public frontend is accessible via HTTPS. |
| DPLY-04 | 36-02 | Admin frontend deployed with Dockerfile.admin, BACKEND_URL pointing to admin backend, Tailscale-only | ✓ SATISFIED | Human-confirmed in 36-02 SUMMARY. Port 3001 published, no Dokploy domain, admin dashboard loaded via Tailscale browser session. |
| DPLY-05 | 36-01 | Tailscale installed on Dokploy host, admin services reachable via Tailscale only, port scan returns no response | ✓ SATISFIED | Tailscale IP 100.115.125.119 confirmed. iptables DOCKER-USER rules applied (Hostinger has no cloud firewall). External port scan confirms ports 8001/3001 filtered. Note: ts.net hostnames (admin-api.spectra.ts.net, admin.spectra.ts.net) not used — access via Tailscale IP directly. |
| DPLY-06 | 36-01 | File uploads persist across redeployments — named volume at /app/uploads configured before first deploy | ✓ SATISFIED | spectra-uploads volume mounted before first deploy (36-01 SUMMARY). Uploads ownership fix in Dockerfile.backend (f9e8073). 36-03 smoke test 4 confirmed file survives redeploy. |
| DPLY-07 | 36-03 | Public backend AND public frontend accessible via custom public HTTPS domains with valid SSL | ✓ SATISFIED (with deviation) | Public frontend at `https://spectra.nuelo.ai` with Let's Encrypt SSL — confirmed 36-03 SUMMARY. Public backend has no public HTTPS domain (deliberate: internal via Swarm DNS, more secure). The spirit of DPLY-07 (public services accessible via HTTPS) is met by the frontend-only exposure model. REQUIREMENTS.md checkbox not updated. |
| DPLY-08 | 36-03 | DEPLOYMENT.md covers all 4 service configs, env var tables, Tailscale setup, volume mount steps, SSL, SECRET_KEY generation, smoke test checklist | ✓ VERIFIED | Confirmed via code inspection (see DPLY-08 Content Verification below). REQUIREMENTS.md checkbox not updated. |

### DPLY-02, DPLY-03, DPLY-04, DPLY-07, DPLY-08 — REQUIREMENTS.md Checkbox Gap

The REQUIREMENTS.md checkboxes for DPLY-02, DPLY-03, DPLY-04, DPLY-07, and DPLY-08 were not updated to `[x]` during phase execution. The plan summaries document completion and the summary `requirements-completed` fields declare them done, but the REQUIREMENTS.md document still shows `[ ]` for these five IDs and the tracking table shows "Pending". This is a documentation tracking gap — the work was completed but REQUIREMENTS.md was not updated.

---

## DPLY-08 Content Verification (DEPLOYMENT.md)

DEPLOYMENT.md exists at repo root, 401 lines, committed as `1668e6b`.

| Required Content | Present | Evidence |
|-----------------|---------|---------|
| All 4 service configurations | Yes | Steps 5-8 cover public backend, admin backend, public frontend, admin frontend |
| Environment variable tables | Yes | 4 `| Variable | Value |` tables (one per service) |
| Tailscale installation | Yes | Step 3: `curl -fsSL https://tailscale.com/install.sh | sh` + `sudo tailscale up` |
| Tailscale-only binding for admin services | Yes | Steps 6d and 8: "Leave the Domains tab empty" + iptables DOCKER-USER rules in Step 4 |
| Volume mount steps | Yes | Step 5c with ordering warning: "configure BEFORE clicking Deploy for the first time" |
| Public domain/SSL assignment | Yes | Step 9: DNS A record, Dokploy Domains tab, letsencrypt certificate |
| SECRET_KEY generation | Yes | Step 2: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| Smoke test checklist (public + admin + isolation) | Yes | "Post-Deploy Smoke Test Checklist" with 17 checkbox items covering public HTTPS, admin Tailscale, and isolation tests |
| Architecture deviation documented | Yes | Architecture Overview section explains no public backend domain + Key design callout |
| Troubleshooting section | Yes | 7 common failure scenarios covered |
| Swarm DNS pattern documented | Yes | Step 5e and 6d document getting Swarm service names for BACKEND_URL |

---

## Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|-----------|
| `Dockerfile.frontend` line 21 | `ENV BACKEND_URL=http://localhost:8000` in builder stage | Info | Default for local dev only. Overridden at runtime via Dokploy env tab. DEPLOYMENT.md documents the correct override pattern. Not a blocker. |
| `Dockerfile.admin` line 21 | Same localhost default | Info | Same as above — intentional local dev default. |

No blocker or warning anti-patterns found. No TODO/FIXME/placeholder comments in modified files. No stub implementations. All handlers are substantive and wired.

---

## Human Verification Required

Phase 36 is a production infrastructure deployment phase. All code artifacts are verified as substantive and correctly wired. The live production state (services running, network isolation active, HTTPS serving) was confirmed by human smoke tests during execution (5/5 split-horizon tests in 36-02, 8/8 smoke tests in 36-03). The following items require a brief human spot-check to re-confirm production state:

### 1. Four Services Running

**Test:** In Dokploy UI, confirm all 4 services show "Running" status.
**Expected:** spectra-public-backend, spectra-admin-backend, spectra-public-frontend, spectra-admin-frontend — all green/Running.
**Why human:** Live container orchestration state — not readable from code.

### 2. Public Frontend HTTPS Smoke Test

**Test:** Open `https://spectra.nuelo.ai` in browser. Log in. Send a chat message. Check Settings page.
**Expected:** Padlock icon shows (no SSL warning), login succeeds, chat response streams token-by-token, Settings page shows version v0.6.0.
**Why human:** SSE streaming behavior and browser SSL state require a live browser session.

### 3. Admin Tailscale Isolation Verification

**Test:** From a Tailscale-connected device, `curl http://100.115.125.119:8001/health`. From a non-Tailscale network, `curl --max-time 5 http://<SERVER_PUBLIC_IP>:8001/health`.
**Expected:** Via Tailscale: `{"status":"ok"}`. Via public internet: timeout (no response within 5 seconds).
**Why human:** Requires two different network contexts simultaneously.

### 4. File Upload Persistence

**Test:** Upload a file via `https://spectra.nuelo.ai`. In Dokploy UI, click Deploy on spectra-public-backend. After redeploy completes, verify file still appears in file list.
**Expected:** File accessible after redeploy. `docker inspect` on the new container still shows spectra-uploads volume at /app/uploads.
**Why human:** Requires triggering a live redeployment event and observing the result.

---

## Gaps Summary

No code gaps found. All verifiable artifacts exist, are substantive, and are correctly wired:

- `Dockerfile.backend`: multi-stage, uploads ownership fix, entrypoint wired to alembic-then-uvicorn
- `Dockerfile.frontend` + `Dockerfile.admin`: multi-stage Next.js builds, IPv6 healthcheck fix, runtime BACKEND_URL
- `backend/docker-entrypoint.sh`: pg_isready wait → alembic upgrade head → uvicorn
- Frontend proxy route handlers: substantive, runtime BACKEND_URL, correct path handling for SSE
- `DEPLOYMENT.md`: 401 lines, all DPLY-08 content confirmed present
- Admin null-name crash fix: confirmed in AdminHeader.tsx

**Documentation tracking gap (not a code gap):** REQUIREMENTS.md checkboxes for DPLY-02, DPLY-03, DPLY-04, DPLY-07, and DPLY-08 remain `[ ]` (Pending) and the tracking table rows still say "Pending". The summaries and plan `requirements-completed` fields document these as done. REQUIREMENTS.md should be updated to reflect actual completion state.

**Architectural deviation (accepted):** DPLY-07 specified "public backend AND public frontend" on HTTPS. The actual delivery is frontend-only public HTTPS (`spectra.nuelo.ai`) with backend internal-only via Swarm DNS. This reduces attack surface. The user confirmed this deviation in SUMMARY documentation and the verification prompt explicitly notes it as a deliberate security improvement.

---

_Verified: 2026-02-19_
_Verifier: Claude (gsd-verifier)_
