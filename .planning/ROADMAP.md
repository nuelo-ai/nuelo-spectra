# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** — Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** — Phases 7-13 (shipped 2026-02-10)
- ✅ **v0.3 Multi-file Conversation Support** — Phases 14-19 (shipped 2026-02-12)
- ✅ **v0.4 Data Visualization** — Phases 20-25 (shipped 2026-02-15)
- ✅ **v0.5 Admin Portal** — Phases 26-32 (shipped 2026-02-18)
- ✅ **v0.6 Docker and Dokploy Support** — Phases 33-37 (shipped 2026-02-21)
- 🚧 **v0.7 API Services & MCP** — Phases 38-41 (in progress)

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

<details>
<summary>✅ v0.6 Docker and Dokploy Support (Phases 33-37) — SHIPPED 2026-02-21</summary>

- [x] Phase 33: Pre-Work and Version API (2/2 plans) — completed 2026-02-19
- [x] Phase 34: Dockerfiles and Entrypoint (3/3 plans) — completed 2026-02-19
- [x] Phase 35: Docker Compose and Local Validation (1/1 plan) — completed 2026-02-19
- [x] Phase 36: Dokploy Deployment and DEPLOYMENT.md (3/3 plans) — completed 2026-02-20
- [x] Phase 37: Admin Seed on Startup and Mandatory Credentials (1/1 plan) — completed 2026-02-21

</details>

### v0.7 API Services & MCP (In Progress)

**Milestone Goal:** Expose Spectra's data analysis capabilities as a public REST API and MCP server, enabling programmatic access and AI agent integrations.

- [x] **Phase 38: API Key Infrastructure** - Data model, ApiKeyService, Alembic migration, auth middleware, and frontend management UI — completed 2026-02-23
- [x] **Phase 39: API Key Management UI + Deployment Mode** - User Settings page, admin User Management extension, and SPECTRA_MODE=api as 5th Dokploy service (UAT gap closure in progress) (completed 2026-02-24)
- [x] **Phase 40: REST API v1 Endpoints** - File management, file context, and synchronous query endpoints with credit deduction and usage logging (completed 2026-02-24)
- [x] **Phase 41: MCP Server** - Manually curated MCP tools wrapping Phase 40 endpoints, ASGI mounting, and Streamable HTTP transport (completed 2026-02-24)

## Phase Details

### Phase 38: API Key Infrastructure
**Goal**: Users can create, view, and revoke API keys, and the backend can authenticate API requests using those keys
**Depends on**: Phase 37 (v0.6 complete)
**Requirements**: APIKEY-01, APIKEY-02, APIKEY-03, APIKEY-04, APIKEY-05, APISEC-01, APISEC-02, APIINFRA-01, APIINFRA-02, APIINFRA-05
**Success Criteria** (what must be TRUE):
  1. User can create an API key with a name; the full key is displayed once and cannot be retrieved again
  2. User can view their existing API keys showing name, prefix (first 8-12 chars), and creation date
  3. User can revoke an API key; revoked keys immediately return 401 on any API request
  4. An API request with a valid Bearer token is authenticated as the key's owner; an invalid or revoked token returns 401
  5. API routes are served under `/api/v1/` versioned prefix when `SPECTRA_MODE=api` is set
  6. In `SPECTRA_MODE=dev` (Docker Compose), all `/api/v1/` routes are active alongside existing backend routes — no separate service needed locally
**Plans**: 4 plans

Plans:
- [ ] 38-01-PLAN.md — ApiKey model, Alembic migration, User relationship, config.py api mode acceptance
- [ ] 38-02-PLAN.md — ApiKeyService TDD (generate, create, list, revoke, authenticate) + Pydantic schemas
- [ ] 38-03-PLAN.md — api_v1 router + CRUD endpoints + get_authenticated_user() + main.py mode gate
- [ ] 38-04-PLAN.md — Frontend hooks (useApiKeys) + ApiKeySection component + Settings page integration

### Phase 39: API Key Management UI + Deployment Mode
**Goal**: API key management is accessible from the public frontend Settings page, admins can manage keys for any user, and the api mode backend is deployable as a standalone Dokploy service
**Depends on**: Phase 38
**Requirements**: APIKEY-06, APIKEY-07, APIKEY-08, APIINFRA-03
**Success Criteria** (what must be TRUE):
  1. User can manage API keys from a dedicated section on their Settings page (create, view prefix/name, revoke)
  2. Admin can view all API keys for any user from the User Management screen
  3. Admin can create and revoke API keys on behalf of any user
  4. A `SPECTRA_MODE=api` backend service is deployable as a 5th Dokploy Application with its own public HTTPS domain
**Plans**: 5 plans

Plans:
- [x] 39-01-PLAN.md — Backend: ApiKey model migration, admin service methods, admin API key router, /api/v1/health endpoint
- [x] 39-02-PLAN.md — Public frontend ApiKeySection enhancement (credit usage column) + DEPLOYMENT.md 5th service docs + API mode CORS
- [x] 39-03-PLAN.md — Admin frontend: UserApiKeysTab component + hooks + UserDetailTabs 5th tab integration
- [ ] 39-04-PLAN.md — Gap closure: Fix /api/v1 router prefix, admin revoke 204 handling, admin key list table layout
- [ ] 39-05-PLAN.md — Gap closure: Public frontend credit usage label, last used display, admin badge for admin-created keys

### Phase 40: REST API v1 Endpoints
**Goal**: External callers can programmatically manage files, retrieve file context, and run synchronous analysis queries — all authenticated by API key with credit deduction and usage logging
**Depends on**: Phase 39
**Requirements**: APIF-01, APIF-02, APIF-03, APIF-04, APIC-01, APIC-02, APIC-03, APIQ-01, APISEC-03, APISEC-04, APIINFRA-04
**Success Criteria** (what must be TRUE):
  1. API caller can upload a CSV/Excel file and receive the AI-generated data brief and query suggestions in the response
  2. API caller can list, download, and delete files belonging to their account
  3. API caller can retrieve a file's full context (data brief, summary, suggestions) and update the summary/context fields
  4. API caller can send a natural language query against a file and receive the complete analysis result (code, chart spec, explanation) synchronously
  5. Each analysis query deducts credits from the caller's balance; each API request is logged (endpoint, credits used, status code) and structured request/error logs are written
**Plans**: 4 plans

Plans:
- [ ] 40-01-PLAN.md — Foundation: API envelope schemas, ApiUsageLog model + migration, usage service, credit refund, auth api_key_id tracking
- [ ] 40-02-PLAN.md — File + context endpoints: upload, list, delete, download, get context, update context, get suggestions
- [ ] 40-03-PLAN.md — Query endpoint + usage logging: stateless analysis with credit deduction/refund, API usage middleware
- [ ] 40-04-PLAN.md — Gap closure: Fix context update persistence (flush->commit) and auth error ApiErrorResponse envelope

### Phase 41: MCP Server
**Goal**: Claude Desktop, Claude Code, or any MCP host can use Spectra's analysis capabilities as first-class tools via a production-ready MCP server
**Depends on**: Phase 40
**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04, MCP-05
**Success Criteria** (what must be TRUE):
  1. An MCP host can upload a file and receive the AI-generated data brief through a curated `spectra_upload_file` tool
  2. An MCP host can query a file with a natural language question and receive the full analysis result through `spectra_run_analysis`
  3. An MCP host can list, delete, and download files through dedicated tools
  4. An MCP host can retrieve file context and query suggestions through a dedicated tool
  5. All MCP tools authenticate using a Spectra API key; tool calls are billed and logged identically to direct REST API calls
**Plans**: TBD

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
| 36. Dokploy Deployment and DEPLOYMENT.md | v0.6 | 3/3 | Complete | 2026-02-20 |
| 37. Admin Seed on Startup | v0.6 | 1/1 | Complete | 2026-02-21 |
| 38. API Key Infrastructure (incl. dev mode) | v0.7 | Complete    | 2026-02-24 | 2026-02-23 |
| 39. API Key Management UI + Deployment Mode | 5/5 | Complete    | 2026-02-24 | - |
| 40. REST API v1 Endpoints | 4/4 | Complete   | 2026-02-24 | - |
| 41. MCP Server | v0.7 | 0/TBD | Not started | - |
