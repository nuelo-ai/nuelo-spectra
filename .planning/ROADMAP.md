# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** — Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** — Phases 7-13 (shipped 2026-02-10)
- ✅ **v0.3 Multi-file Conversation Support** — Phases 14-19 (shipped 2026-02-12)
- ✅ **v0.4 Data Visualization** — Phases 20-25 (shipped 2026-02-15)
- ✅ **v0.5 Admin Portal** — Phases 26-32 (shipped 2026-02-18)
- 🚧 **v0.6 Docker and Dokploy Support** — Phases 33-36 (in progress)

## Phases

<details>
<summary>✅ v0.1 Beta MVP (Phases 1-6) — SHIPPED 2026-02-06</summary>

- [x] Phase 1: Foundation Setup (6/6 plans) — completed 2026-02-06
- [x] Phase 2: File Upload & AI Profiling (6/6 plans) — completed 2026-02-06
- [x] Phase 3: Multi-File Management (4/4 plans) — completed 2026-02-06
- [x] Phase 4: AI Agent System & Code Generation (8/8 plans) — completed 2026-02-06
- [x] Phase 5: Secure Code Execution & E2B (6/6 plans) — completed 2026-02-06
- [x] Phase 6: Interactive Data Cards & Frontend Polish (6/6 plans) — completed 2026-02-06

</details>

<details>
<summary>✅ v0.2 Intelligence & Integration (Phases 7-13) — SHIPPED 2026-02-10</summary>

- [x] Phase 7: Multi-LLM Provider Infrastructure (5/5 plans) — completed 2026-02-09
- [x] Phase 8: Session Memory with PostgreSQL Checkpointing (2/2 plans) — completed 2026-02-08
- [x] Phase 9: Manager Agent with Intelligent Query Routing (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Smart Query Suggestions (2/2 plans) — completed 2026-02-08
- [x] Phase 11: Web Search Tool Integration (3/3 plans) — completed 2026-02-09
- [x] Phase 12: Production Email Infrastructure (2/2 plans) — completed 2026-02-09
- [x] Phase 13: Migrate Web Search (Tavily) (2/2 plans) — completed 2026-02-09

</details>

<details>
<summary>✅ v0.3 Multi-file Conversation Support (Phases 14-19) — SHIPPED 2026-02-12</summary>

- [x] Phase 14: Database Foundation & Migration (4/4 plans) — completed 2026-02-11
- [x] Phase 15: Agent System Enhancement (3/3 plans) — completed 2026-02-11
- [x] Phase 16: Frontend Restructure (3/3 plans) — completed 2026-02-11
- [x] Phase 17: File Management & Linking (3/3 plans) — completed 2026-02-11
- [x] Phase 18: Integration & Polish (3/3 plans) — completed 2026-02-11
- [x] Phase 19: v0.3 Gap Closure (7/7 plans) — completed 2026-02-12

</details>

<details>
<summary>✅ v0.4 Data Visualization (Phases 20-25) — SHIPPED 2026-02-15</summary>

- [x] Phase 20: Infrastructure & Pipeline (2/2 plans) — completed 2026-02-13
- [x] Phase 21: Visualization Agent (1/1 plan) — completed 2026-02-13
- [x] Phase 22: Graph Integration & Chart Intelligence (2/2 plans) — completed 2026-02-13
- [x] Phase 23: Frontend Chart Rendering (2/2 plans) — completed 2026-02-13
- [x] Phase 24: Chart Types & Export (3/3 plans) — completed 2026-02-13
- [x] Phase 25: Theme Integration (1/1 plan) — completed 2026-02-14

</details>

<details>
<summary>✅ v0.5 Admin Portal (Phases 26-32) — SHIPPED 2026-02-18</summary>

- [x] Phase 26: Foundation (3/3 plans) — completed 2026-02-16
- [x] Phase 27: Credit System (4/4 plans) — completed 2026-02-16
- [x] Phase 28: Platform Config (2/2 plans) — completed 2026-02-16
- [x] Phase 29: User Management (3/3 plans) — completed 2026-02-16
- [x] Phase 30: Invitation System (3/3 plans) — completed 2026-02-17
- [x] Phase 31: Dashboard & Admin Frontend (8/8 plans) — completed 2026-02-17
- [x] Phase 32: Production Readiness (1/1 plan) — completed 2026-02-18

</details>

### 🚧 v0.6 Docker and Dokploy Support (In Progress)

**Milestone Goal:** Package Spectra for production deployment — fix localhost hardcodes, add version API, write Dockerfiles for all 3 services, Docker Compose for local dev, and configure 3 separate Dokploy Application services with HTTPS domains and a DEPLOYMENT.md guide.

- [x] **Phase 33: Pre-Work and Version API** — Fix localhost hardcodes, enable standalone builds, add /api/health routes, and expose GET /version endpoint with display in both frontends (completed 2026-02-19)
- [x] **Phase 34: Dockerfiles and Entrypoint** — Write .dockerignore files (before any docker build), entrypoint script with pg_isready + Alembic, and all 3 production Dockerfiles (completed 2026-02-19)
- [x] **Phase 35: Docker Compose and Local Validation** — Write compose.yaml, bring up the full stack locally, and validate all services work together end-to-end (completed 2026-02-19)
- [x] **Phase 36: Dokploy Deployment and DEPLOYMENT.md** — Deploy 4 services to Dokploy (public backend + frontend via HTTPS, admin backend + frontend via Tailscale-only), configure volumes and env vars, and write DEPLOYMENT.md (completed 2026-02-20)

## Phase Details

### Phase 33: Pre-Work and Version API
**Goal**: The codebase is Docker-ready — no hardcoded localhost URLs exist, both Next.js apps build as standalone images, both frontends can proxy to a configurable backend URL, health routes exist for monitoring, and the version API is live with display in both frontends
**Depends on**: Phase 32 (v0.5 shipped)
**Requirements**: PRE-01, PRE-02, PRE-03, PRE-04, PRE-05, VER-01, VER-02, VER-03
**Success Criteria** (what must be TRUE):
  1. Developer inspects `useSSEStream.ts` and `register/page.tsx` and finds no `http://localhost:8000` strings — all API calls go through `/api/` proxy
  2. Both `next.config.ts` files have `output: 'standalone'` and rewrite destinations read `process.env.BACKEND_URL` (defaulting to `http://localhost:8000` locally)
  3. `GET /api/health` returns `{"status": "ok"}` on both the public frontend (port 3000) and admin frontend (port 3001) when running locally
  4. `GET /version` on the backend returns `{"version": "<APP_VERSION>", "environment": "<SPECTRA_MODE>"}` — version shows `"dev"` when `APP_VERSION` env var is unset
  5. User on the public settings page and admin on the admin settings page both see the app version fetched live from the backend — no page rebuild required to reflect a version change
**Plans**: 2 plans

Plans:
- [ ] 33-01-PLAN.md — Fix localhost hardcodes and enable standalone output (PRE-01, PRE-02, PRE-03)
- [ ] 33-02-PLAN.md — Add health routes, backend version endpoint, and version display in both frontends (PRE-04, PRE-05, VER-01, VER-02, VER-03)

### Phase 34: Dockerfiles and Entrypoint
**Goal**: Three production Docker images exist and each builds and runs correctly in isolation — the backend image waits for PostgreSQL, runs migrations, and starts uvicorn as PID 1; both frontend images serve the Next.js standalone app with `BACKEND_URL` controlling the proxy destination at runtime; no secrets are baked into any image layer
**Depends on**: Phase 33
**Requirements**: DOCK-01, DOCK-02, DOCK-03, DOCK-04, DOCK-05
**Success Criteria** (what must be TRUE):
  1. `.dockerignore` files exist for each service and exclude `.env`, `.venv`, `node_modules`, `.next`, `__pycache__`, and `uploads/` — verified by inspecting `docker history` output showing no API keys or secrets
  2. `backend/docker-entrypoint.sh` loops `pg_isready` until PostgreSQL accepts connections, then runs `alembic upgrade head`, then starts uvicorn via `exec` (PID 1 for graceful SIGTERM handling)
  3. Developer runs `docker build -f Dockerfile.backend .` and the resulting image starts against a local PostgreSQL, responds to `GET /health`, and runs as a non-root user
  4. Developer runs `docker build -f Dockerfile.frontend .` and the resulting image serves the public Next.js app on port 3000 with `BACKEND_URL` controlling the rewrite destination — responds to `GET /api/health`
  5. Developer runs `docker build -f Dockerfile.admin .` and the resulting image serves the admin Next.js app on port 3000 — same pattern as frontend, responds to `GET /api/health`
**Plans**: 3 plans

Plans:
- [ ] 34-01-PLAN.md — Write .dockerignore files and backend entrypoint script (DOCK-01, DOCK-02)
- [ ] 34-02-PLAN.md — Write Dockerfile.backend with uv multi-stage build (DOCK-03)
- [ ] 34-03-PLAN.md — Write Dockerfile.frontend and Dockerfile.admin with 3-stage standalone builds (DOCK-04, DOCK-05)

### Phase 35: Docker Compose and Local Validation
**Goal**: The full Spectra stack runs locally with a single `docker compose up` command — all three services start in the correct order, file uploads persist across `docker compose down && docker compose up`, inter-service networking works, and each service runs with the correct `SPECTRA_MODE`
**Depends on**: Phase 34
**Requirements**: COMP-01, COMP-02, COMP-03, COMP-04
**Success Criteria** (what must be TRUE):
  1. Developer runs `docker compose up` and all four containers (backend, public frontend, admin frontend, PostgreSQL) start successfully — backend on port 8000, public frontend on port 3000, admin frontend on port 3001
  2. A file uploaded via the local public frontend at `http://localhost:3000` survives `docker compose down && docker compose up` — the file still appears in the file list and is downloadable after restart
  3. Backend container starts only after the PostgreSQL healthcheck passes — `depends_on: condition: service_healthy` is verified by inspecting container startup logs showing pg_isready wait before uvicorn launch
  4. Developer can log into the admin frontend at `http://localhost:3001`, and the admin API routes respond correctly — `SPECTRA_MODE` is set correctly per service so public routes and admin routes are properly isolated
**Plans**: 1 plan

Plans:
- [ ] 35-01-PLAN.md — Create compose.yaml, .env.docker.example, and validate full stack end-to-end (COMP-01, COMP-02, COMP-03, COMP-04)

### Phase 36: Dokploy Deployment and DEPLOYMENT.md
**Goal**: Four Spectra services are running in production — public backend and public frontend accessible via public HTTPS, admin backend and admin frontend accessible only via Tailscale VPN; file uploads persist across redeployments; DEPLOYMENT.md gives a complete step-by-step guide for this split-horizon deployment
**Depends on**: Phase 35
**Requirements**: DPLY-01, DPLY-02, DPLY-03, DPLY-04, DPLY-05, DPLY-06, DPLY-07, DPLY-08
**Success Criteria** (what must be TRUE):
  1. Public backend Dokploy service is live — Alembic migration ran against Dokploy-managed PostgreSQL, `GET /health` returns 200, `SPECTRA_MODE=public` (only user-facing routes mounted)
  2. Public frontend is live at its HTTPS domain — login works, SSE chat streaming works end-to-end, version visible on settings page
  3. Admin backend Dokploy service is live at `admin-api.spectra.ts.net` via Tailscale only — `SPECTRA_MODE=admin`, admin routes respond, not reachable from public internet
  4. Admin frontend is live at `admin.spectra.ts.net` via Tailscale only — admin login works, user management and platform settings respond correctly, not reachable from public internet
  5. A file uploaded via the production public frontend survives a Dokploy redeploy — named volume at `/app/uploads` configured, file records in PostgreSQL match files on disk
  6. `DEPLOYMENT.md` covers all 4 service configs with env var tables, Tailscale installation and Tailscale-only binding for admin services, volume mount, public SSL, `SECRET_KEY` generation, and smoke test checklist for both public and VPN-only services
**Plans**: 3 plans

Plans:
- [x] 36-01-PLAN.md — Prerequisites + public backend deployment: Tailscale install, VPS firewall, DB setup, public backend with volume mount (DPLY-01, DPLY-05, DPLY-06)
- [ ] 36-02-PLAN.md — Admin backend + both frontends deployment, split-horizon routing verification (DPLY-02, DPLY-03, DPLY-04, DPLY-05)
- [ ] 36-03-PLAN.md — Public HTTPS domains/SSL, full smoke test, write DEPLOYMENT.md (DPLY-07, DPLY-08)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation Setup | v0.1 | 6/6 | Complete | 2026-02-06 |
| 2. File Upload & AI Profiling | v0.1 | 6/6 | Complete | 2026-02-06 |
| 3. Multi-File Management | v0.1 | 4/4 | Complete | 2026-02-06 |
| 4. AI Agent System & Code Generation | v0.1 | 8/8 | Complete | 2026-02-06 |
| 5. Secure Code Execution & E2B | v0.1 | 6/6 | Complete | 2026-02-06 |
| 6. Interactive Data Cards | v0.1 | 6/6 | Complete | 2026-02-06 |
| 7. Multi-LLM Infrastructure | v0.2 | 5/5 | Complete | 2026-02-09 |
| 8. Session Memory | v0.2 | 2/2 | Complete | 2026-02-08 |
| 9. Manager Agent Routing | v0.2 | 3/3 | Complete | 2026-02-08 |
| 10. Smart Query Suggestions | v0.2 | 2/2 | Complete | 2026-02-08 |
| 11. Web Search Integration | v0.2 | 3/3 | Complete | 2026-02-09 |
| 12. Production Email | v0.2 | 2/2 | Complete | 2026-02-09 |
| 13. Migrate Web Search (Tavily) | v0.2 | 2/2 | Complete | 2026-02-09 |
| 14. Database Foundation & Migration | v0.3 | 4/4 | Complete | 2026-02-11 |
| 15. Agent System Enhancement | v0.3 | 3/3 | Complete | 2026-02-11 |
| 16. Frontend Restructure | v0.3 | 3/3 | Complete | 2026-02-11 |
| 17. File Management & Linking | v0.3 | 3/3 | Complete | 2026-02-11 |
| 18. Integration & Polish | v0.3 | 3/3 | Complete | 2026-02-11 |
| 19. v0.3 Gap Closure | v0.3 | 7/7 | Complete | 2026-02-12 |
| 20. Infrastructure & Pipeline | v0.4 | 2/2 | Complete | 2026-02-13 |
| 21. Visualization Agent | v0.4 | 1/1 | Complete | 2026-02-13 |
| 22. Graph Integration & Chart Intelligence | v0.4 | 2/2 | Complete | 2026-02-13 |
| 23. Frontend Chart Rendering | v0.4 | 2/2 | Complete | 2026-02-13 |
| 24. Chart Types & Export | v0.4 | 3/3 | Complete | 2026-02-13 |
| 25. Theme Integration | v0.4 | 1/1 | Complete | 2026-02-14 |
| 26. Foundation | v0.5 | 3/3 | Complete | 2026-02-16 |
| 27. Credit System | v0.5 | 4/4 | Complete | 2026-02-16 |
| 28. Platform Config | v0.5 | 2/2 | Complete | 2026-02-16 |
| 29. User Management | v0.5 | 3/3 | Complete | 2026-02-16 |
| 30. Invitation System | v0.5 | 3/3 | Complete | 2026-02-17 |
| 31. Dashboard & Admin Frontend | v0.5 | 8/8 | Complete | 2026-02-17 |
| 32. Production Readiness | v0.5 | 1/1 | Complete | 2026-02-18 |
| 33. Pre-Work and Version API | v0.6 | 2/2 | Complete | 2026-02-19 |
| 34. Dockerfiles and Entrypoint | v0.6 | 3/3 | Complete | 2026-02-19 |
| 35. Docker Compose and Local Validation | v0.6 | 1/1 | Complete | 2026-02-19 |
| 36. Dokploy Deployment and DEPLOYMENT.md | 3/3 | Complete    | 2026-02-20 | - |
