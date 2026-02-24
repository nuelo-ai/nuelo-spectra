# Project Research Summary

**Project:** Spectra v0.7 — API Services and MCP Server
**Domain:** Programmatic API access layer and AI agent integration (MCP) for an existing AI-powered data analytics platform
**Researched:** 2026-02-23
**Confidence:** HIGH

## Executive Summary

Spectra v0.7 adds three tightly layered capabilities on top of an already-complete FastAPI monolith: API key management (new DB table, hashed storage, user self-service UI, admin visibility), a versioned public REST API (v1 endpoints for file listing, data context, and synchronous analysis), and an MCP server that wraps those REST endpoints as tools callable by Claude Desktop, Claude Code, or any MCP host. All three surfaces follow a strict dependency chain — keys must exist before the API can authenticate, the API must exist before the MCP server has anything to call. The recommended build order mirrors this: data model and service layer first, auth layer second, REST endpoints third, MCP last.

The stack change is deliberately minimal: only two new Python packages are needed — `fastmcp>=3.0.2` (the de facto Python MCP server framework, released 2026-01-19, with native FastAPI integration) and `slowapi>=0.1.9` (per-key rate limiting). Everything else — FastAPI, SQLAlchemy, Alembic, LangGraph, E2B, Pydantic settings — carries forward unchanged. API key generation and hashing use Python stdlib (`secrets`, `hashlib`, `hmac`). The MCP server mounts as an ASGI sub-application on a new `SPECTRA_MODE=api` deployment, keeping it isolated from the public web frontend without requiring any new infrastructure. No Redis, no Celery, no message broker, no frontend changes.

The primary risk area is MCP server quality, not correctness. FastMCP's `from_fastapi()` auto-generation is a tempting shortcut but produces tool descriptions that LLMs use poorly — FastMCP's own documentation warns about this explicitly. The recommendation is to bootstrap with auto-generation as scaffolding, then hand-curate each of the 3-5 tool descriptions for AI agent clarity. A secondary risk is the synchronous query endpoint timeout: LangGraph analysis runs take 10-45 seconds, so the `api` mode service needs an explicit 120-second uvicorn request timeout — the default 30 seconds will silently cut off legitimate queries. The v0.7 infrastructure also inherits the Docker/Dokploy deployment patterns from v0.6, so all volume, secret, and SPECTRA_MODE pitfalls documented in PITFALLS.md remain relevant for the new `spectra-api` Dokploy service.

---

## Key Findings

### Recommended Stack

The existing stack handles v0.7 completely with two additions. `fastmcp>=3.0.2` is the de facto Python MCP server framework — it provides `FastMCP.from_fastapi()` for OpenAPI-based auto-generation, `DebugTokenVerifier` for database-backed token validation, and native Streamable HTTP transport. `slowapi>=0.1.9` provides FastAPI-native rate limiting via a single middleware line and `@limiter.limit()` decorator, with a custom `key_func` that extracts the API key from the Authorization header rather than rate-limiting by IP.

API key hashing deliberately uses `hashlib.sha256()` rather than Argon2 — this is correct practice, not a shortcut. API keys are 32 bytes of cryptographic randomness, making brute force computationally infeasible regardless of hash speed. Argon2 would add ~250ms to every API request. SHA-256 is the industry standard for high-entropy random keys (GitHub, Stripe, Twilio all use this pattern). API keys use the prefix format `spe_<secrets.token_urlsafe(32)>`, stored as `sha256(full_key).hexdigest()` with only the first 8-12 characters stored as plaintext for display.

**Core technologies:**
- `fastmcp>=3.0.2`: MCP server framework — only Python library with native `from_fastapi()` auto-generation, built-in auth providers, and Streamable HTTP transport; v3.0 stable and widely adopted
- `slowapi>=0.1.9`: Per-key rate limiting — thin `limits` wrapper, FastAPI middleware integration, no Redis dependency for single-instance deployment
- `secrets` + `hashlib` + `hmac` (stdlib): API key generation and hashing — no additional packages; SHA-256 appropriate for high-entropy random keys
- `fastapi[standard]>=0.115` (existing): Extended with new v1 router prefix and `api` mode gate — zero changes to existing router registrations
- `sqlalchemy[asyncio]` + `alembic` (existing): New `api_keys` table follows identical ORM and migration patterns as all existing models

**What NOT to add:** `fastapi-mcp` (tadata/last release July 2025), base `mcp` SDK directly, `bcrypt` for key hashing, Redis for rate limiting, `fastapi-versioning`, OAuth2, Celery.

### Expected Features

All v0.7 features are P1 (launch-blocking) except three P2 items deferred until the first user requests them. The feature dependency graph is strictly linear: API key infrastructure → auth middleware → REST v1 endpoints → MCP tools.

**Must have (table stakes):**
- `api_keys` table + CRUD endpoints — foundation; nothing else works without this
- User self-service key management UI — create (display-once modal with copy button), list (prefix + metadata), revoke (immediate, soft-delete for audit trail)
- REST API v1 auth middleware — validate Bearer key, lookup by SHA-256 hash, check revocation, update `last_used_at`
- `GET /api/v1/files` — list user's files; simplest endpoint; validates auth plumbing end-to-end
- `GET /api/v1/files/{id}/context` — AI-generated data profile; high value, zero new computation (pre-computed at upload)
- `POST /api/v1/analysis` — synchronous query; core product capability; credit deduction mandatory (same atomic `SELECT FOR UPDATE` as web UI)
- `GET /api/v1/me` — current user info + credits; developer validation endpoint
- Consistent JSON error envelope (`{"error": {"code": "...", "message": "...", "request_id": "..."}}`) across all v1 routes
- OpenAPI docs at `/api/v1/docs` — auto-generated by FastAPI; zero implementation cost; essential for developer adoption
- MCP server with 3 core tools: `spectra_list_files`, `spectra_get_file_context`, `spectra_run_analysis`
- Admin portal key view and revoke — security requirement; extends existing user management screen
- `SPECTRA_MODE=api` — 5th Dokploy service; clean API-only backend with its own domain

**Should have (add after first user request):**
- `X-Credits-Remaining` response header — track consumption per-request without polling `/api/v1/me`; one line of middleware
- API key scopes (`files:read`, `analysis:run`) — least-privilege access; accommodate `scopes TEXT[]` column in DB schema from day one even if unused at launch
- Key expiration / TTL (`expires_at TIMESTAMPTZ NULL` column) — short-lived keys for automation pipelines

**Defer (v1.x / v2+):**
- File upload via REST API — significantly expands scope; requires async profiling pipeline decisions
- Async analysis with job ID polling — only if 60-second synchronous timeout regularly triggers
- OAuth 2.0 — only justified when third-party delegated access is required
- SDK libraries (Python, JS) — auto-generate with Speakeasy or OpenAPI Generator after stable API surface
- SSE streaming on REST API — adds client SDK complexity with no benefit for the MCP use case

**Anti-features to explicitly avoid building:**
- SSE streaming on v1 API — AI agent tool calls need a single return value; synchronous JSON is correct
- GraphQL — REST with a consistent envelope covers all v0.7 use cases without schema definition overhead
- Per-key rate limiting as primary consumption gate — credits already serve this role; add hard abuse-prevention floor (e.g., 120 req/min) only as a secondary floor, not as the primary mechanism

### Architecture Approach

The v0.7 architecture extends the existing SPECTRA_MODE split-horizon pattern with a 5th mode (`api`) that mounts the v1 router and MCP server, while keeping all existing public/admin/dev modes unchanged. The unified auth dependency (`get_authenticated_user()`) tries JWT decode first (fast, in-memory, no DB hit), then falls back to SHA-256 key lookup if JWT decode fails — a single dependency serves all v1 routes without modifying the existing `get_current_user` JWT-only path. MCP tool handlers call v1 endpoints via httpx loopback rather than importing service functions directly — this preserves the full auth, credit deduction, and usage logging middleware chain and ensures MCP calls are indistinguishable from REST API calls in terms of billing and audit.

**Major components:**
1. `ApiKey` ORM model + `ApiKeyService` — create, validate (SHA-256 hash lookup), list, revoke; the shared service boundary used by auth dependency, user CRUD routes, and admin routes
2. `get_authenticated_user()` dependency — unified JWT-or-API-key auth; additive change to `dependencies.py`; used exclusively on v1 routes; existing `get_current_user` is unchanged
3. `routers/api/v1/` directory — files, context, query endpoints; calls service layer directly (not existing routers); independent public API contract versioned from day one
4. `mcp_server.py` — FastMCP instance with 3 manually curated tools; mounted on FastAPI app via ASGI in `api`/`dev` modes; uses `combine_lifespans` for clean lifecycle coordination
5. `SPECTRA_MODE=api` gate in `main.py` — registers v1 router and MCP mount; separate Dokploy service (`spectra-api`) at its own domain
6. `api_usage_log` table — append-only per-request log (key ID, endpoint, credits used, status code); admin visibility without v0.7 reporting UI

**Key patterns to enforce across all phases:**
- v1 routers call service layer functions, never import existing routers (avoids coupling public API contract to internal router implementation details)
- MCP tools call REST API via httpx loopback, never import service functions directly (preserves credit deduction and usage logging middleware chain)
- `api` mode intentionally excludes SSE streaming routes, password reset flows, and cookie-based session routes — minimal attack surface
- `scopes TEXT[]` and `expires_at TIMESTAMPTZ` columns in `api_keys` table from day one even if unused — avoids migration pain when P2 features ship

### Critical Pitfalls

The PITFALLS.md file covers v0.6 Docker/Dokploy deployment infrastructure. The pitfalls most relevant to v0.7 planning:

1. **MCP lifespan coordination** — FastMCP's `http_app()` carries its own ASGI lifespan. The existing FastAPI app also has a lifespan. Use `combine_lifespans(existing_lifespan, mcp_app.lifespan)` from `fastmcp.utilities.asgi` when constructing the FastAPI app in `api` mode. Failing to merge lifespans causes the MCP server to never initialize its connection pool or to abort silently during shutdown.

2. **Synchronous query timeout misconfiguration** — LangGraph analysis runs take 10-45 seconds. Default uvicorn timeout (30 seconds) will silently abort legitimate queries. Set `api_query_timeout_seconds: int = 120` in Settings and pass it as a uvicorn startup argument specifically for the `spectra-api` service. This is separate from the existing `stream_timeout_seconds` field which controls SSE.

3. **MCP tool descriptions: auto-generation is not enough** — `FastMCP.from_fastapi()` produces tool descriptions that LLMs use poorly. FastMCP's own documentation warns: "LLMs achieve significantly better performance with well-designed and curated MCP servers than with auto-converted OpenAPI servers." Use auto-generation as scaffolding only; manually curate all tool descriptions before shipping.

4. **API keys as long-lived JWTs (anti-pattern)** — JWTs are self-contained and cannot be instantly revoked. API keys must be instantly revocable (set `is_active=false` in one DB row). Never generate a "long-lived JWT" and call it an API key. Use opaque random tokens stored as SHA-256 hashes.

5. **Secrets baked into Docker image layers** (from PITFALLS.md) — directly relevant to the new `spectra-api` Dokploy service. `SECRET_KEY` (needed for JWT validation even in API mode), `ANTHROPIC_API_KEY`, and `E2B_API_KEY` must never appear in Dockerfile `ARG` or `ENV` instructions. Pass at runtime via Dokploy environment variables panel only.

6. **SPECTRA_MODE=api on the wrong service** (from PITFALLS.md pattern) — `api` mode must never be set on the public or admin backend services. The existing `logger.info(f"Starting Spectra in {mode.upper()} mode")` startup log is a useful smoke test signal; verify mode in post-deploy health check.

---

## Implications for Roadmap

The dependency chain dictates a strict 4-phase build order. No phase should begin before the prior phase is validated end-to-end with tests.

### Phase 1: API Key Infrastructure
**Rationale:** Everything in v0.7 depends on the ability to create, store, and validate API keys. This phase has zero dependencies on anything new — it follows identical patterns to existing models (`CreditService`, `FileService`, existing Alembic migrations). Build first, validate independently before writing any other v0.7 code.
**Delivers:** `api_keys` table migration, `ApiKey` ORM model, `api_usage_log` table migration, `ApiKeyService` (create/validate/list/revoke), Alembic migration, user-facing CRUD endpoints at `/api/keys`, admin key management extension in the admin portal, user self-service UI screen in the public frontend
**Addresses:** All APIKEY-* and APIKEY-ADMIN-* features; `scopes TEXT[]` and `expires_at TIMESTAMPTZ NULL` columns included in schema even if unused at launch
**Avoids:** Argon2 for key hashing (use SHA-256); hard-deleting revoked keys (use `revoked_at` soft-delete for audit trail); calling this a "long-lived JWT"
**Research flag:** No additional research needed — follows exact existing patterns

### Phase 2: Unified Auth Layer and SPECTRA_MODE Extension
**Rationale:** The auth dependency must be solid and independently testable before any v1 endpoint is written. A broken auth layer makes every endpoint test ambiguous — is the bug in the endpoint or the auth? Resolving auth first makes Phase 3 deterministic.
**Delivers:** `get_authenticated_user()` dependency in `dependencies.py`, `ApiUser` type alias, `config.py` extended with `api` mode and rate limit settings, `main.py` updated with `api`/`dev` mode routing block, `slowapi` middleware registered with per-key `key_func`
**Uses:** `fastapi[standard]` (existing), `slowapi>=0.1.9` (new), `HTTPBearer(auto_error=False)` pattern from FastAPI official docs
**Implements:** Unified auth dependency (JWT fast path, API key fallback); SPECTRA_MODE=api gate
**Avoids:** Using `OAuth2PasswordBearer` for the combined dependency (generates wrong Swagger UI behavior for API key flows); mounting MCP or v1 routes in `public` mode
**Research flag:** Verify `slowapi>=0.1.9` compatibility with FastAPI 0.115+ and custom `key_func` behavior before writing middleware (rated MEDIUM confidence in STACK.md)

### Phase 3: REST API v1 Endpoints
**Rationale:** v1 endpoints are the substantive implementation. Each endpoint is independently testable with a valid API key from Phase 1. Build the three endpoints in increasing complexity: file listing (read-only, no credits), file context (read-only, no credits), analysis query (LangGraph invocation, credit deduction, synchronous await with 120s timeout).
**Delivers:** `GET /api/v1/me`, `GET /api/v1/files`, `GET /api/v1/files/{id}/context`, `POST /api/v1/analysis` (synchronous, 120s timeout), consistent JSON error envelope, OpenAPI docs at `/api/v1/docs`, `api_usage_log` inserts on every request
**Uses:** Existing `FileService`, `CreditService`, LangGraph graph (`await graph.ainvoke()`); `fastapi[standard]` (existing)
**Implements:** `routers/api/v1/` directory; `schemas/api_v1.py`; synchronous LangGraph wrapper
**Avoids:** Missing credit deduction on analysis endpoint; importing existing routers into v1 routers; SSE streaming on v1 endpoints; timeout shorter than 120 seconds
**Research flag:** No additional research needed — synchronous `await graph.ainvoke()` is existing LangGraph usage; REST patterns are standard FastAPI

### Phase 4: MCP Server and api Mode Deployment
**Rationale:** MCP tools are thin wrappers over Phase 3 endpoints. Building last, when endpoints are stable, means tool descriptions can be accurate and integration tests can run end-to-end through the full stack. Building earlier couples MCP development to unstable endpoint contracts.
**Delivers:** `mcp_server.py` with 3 manually curated tools (`spectra_list_files`, `spectra_get_file_context`, `spectra_run_analysis`), lifespan coordination via `combine_lifespans`, MCP mount in `main.py` `api`/`dev` block, 5th Dokploy `spectra-api` service configuration with its own domain (`api.spectra.io`), 120-second uvicorn timeout for the api-mode service
**Uses:** `fastmcp>=3.0.2` (new); `httpx` (existing, already installed); Streamable HTTP transport
**Implements:** FastMCP instance mounted as ASGI sub-application; tools call REST API via httpx loopback; `SPECTRA_MODE=api` Dokploy service
**Avoids:** Auto-generated tool descriptions only — manually curate all tool descriptions; MCP tools importing service functions directly (bypasses credits and logging); mounting MCP in `public` mode; sharing the `spectra_uploads` volume without confirming Dokploy host topology
**Research flag:** Verify `combine_lifespans` import path and behavior in FastMCP 3.x at implementation time — the library moved quickly around the v3.0 release and the API may have changed from earlier community examples

### Phase Ordering Rationale

- **Infrastructure before API surface:** API key infrastructure (Phase 1) and auth layer (Phase 2) produce no user-visible output on their own but gate everything else. Completing them first means Phases 3 and 4 can move fast with high confidence.
- **REST before MCP:** The MCP server is architecturally a client of the REST API. Until `/api/v1/analysis` returns stable JSON, tool descriptions cannot be accurate and integration tests cannot be trusted end-to-end.
- **Services over routers as the shared boundary:** Both v1 routers and MCP tool handlers use service layer functions — not each other's router handlers. This is the single most important architectural discipline to enforce across all four phases.
- **Schema accommodates future from day one:** `scopes TEXT[]` and `expires_at TIMESTAMPTZ NULL` go into the `api_keys` table in Phase 1 even though the P2 features using them are deferred. Adding them later requires a migration and potential downtime.
- **Docker pitfalls are live for the new service:** The `spectra-api` service introduced in Phase 4 is a new Dokploy Application. All v0.6 deployment disciplines apply: correct context path, no secrets in image layers, explicit `SPECTRA_MODE=api` verification, and a plan for the `spectra_uploads` volume sharing strategy before deploying to production.

### Research Flags

Phases needing verification or attention during implementation:
- **Phase 2:** Verify `slowapi>=0.1.9` compatibility with FastAPI 0.115+ and test that the custom `key_func` correctly extracts API keys from `Authorization: Bearer <key>` headers in the project's specific Depends() chain before writing the rate limiting middleware.
- **Phase 4:** Verify the `combine_lifespans` import path (`fastmcp.utilities.asgi`) and API behavior in FastMCP 3.x at implementation time. If the API has changed, use a manual lifespan merge pattern as the fallback.
- **Phase 4:** Confirm `spectra-api` and `spectra-public` Dokploy host topology before deploying. If both run on the same host, the `spectra_uploads` named volume is shared automatically. If they run on different hosts, a shared storage strategy (S3 or NFS) is required before the `api` mode service can access files uploaded via the web UI.

Phases with well-documented patterns (no additional research needed):
- **Phase 1:** Exact same ORM + Alembic + service patterns as existing `CreditService`, `FileService`. SHA-256 key hashing is thoroughly documented. HIGH confidence.
- **Phase 3:** Standard FastAPI router patterns. `await graph.ainvoke()` is existing LangGraph usage. Credit deduction is existing `CreditService`. No novel patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | `fastmcp>=3.0.2` verified on PyPI (released 2026-02-22), official FastMCP docs consulted for all key patterns; `slowapi` rated MEDIUM (community consensus, multiple sources, not Context7-verified) |
| Features | HIGH | Industry patterns verified against Stripe, OpenAI, and official MCP documentation; feature dependency graph is unambiguous and directly derived from the codebase |
| Architecture | HIGH | Core FastAPI patterns from official docs and official FastAPI repo discussions; MCP mounting pattern from official FastMCP docs; direct codebase analysis of existing `main.py`, `dependencies.py`, `config.py` |
| Pitfalls | HIGH (v0.6 Docker) / MEDIUM (v0.7-specific) | v0.6 Docker/Dokploy pitfalls from official docs and verified GitHub issues; v0.7-specific pitfalls (MCP lifespan, query timeout) derived from architecture research and FastMCP documentation |

**Overall confidence:** HIGH

### Gaps to Address

- **`slowapi` version pinning:** Rated MEDIUM confidence in STACK.md. Before writing rate limiting middleware in Phase 2, confirm `slowapi>=0.1.9` works with FastAPI 0.115+ and that the `key_func` correctly extracts API keys from `Authorization: Bearer` headers in the project's specific dependency injection pattern.

- **`combine_lifespans` API stability:** FastMCP's `combine_lifespans` utility for merging ASGI lifespans is referenced in ARCHITECTURE.md but its exact import path and behavior in FastMCP 3.x should be verified before Phase 4 begins. The library released v3.0 on 2026-01-19 and may have reorganized internal utilities. Fallback: manual lifespan merge using `asynccontextmanager` composition.

- **Shared volume strategy for `spectra-api`:** ARCHITECTURE.md notes that file volume sharing between `spectra-public` and `spectra-api` is only automatic on a single Dokploy host. If the `api` service runs on a different host, an S3 or NFS strategy is needed — and the existing file storage pattern (local disk) would need to change. Clarify deployment topology before configuring the Phase 4 Dokploy service.

- **User key management UI placement:** FEATURES.md implies the user self-service key management screen lives in the existing public frontend (served by `spectra-public`). ARCHITECTURE.md shows the `/api-keys` CRUD endpoints registered in `public`/`dev` modes. The frontend routing for this new screen should be confirmed before Phase 1 backend CRUD endpoints are finalized, to ensure the API shape matches what the UI will need.

---

## Sources

### Primary (HIGH confidence)
- FastMCP official docs (gofastmcp.com) — `from_fastapi()`, HTTP transport, lifespan coordination (`combine_lifespans`), auth providers, `DebugTokenVerifier`, tool description quality warning
- FastMCP PyPI — version 3.0.2, release date 2026-02-22, Python >=3.10 requirement verified
- MCP Python SDK (github.com/modelcontextprotocol/python-sdk) — protocol transport, `tools/list`, `tools/call` primitives
- modelcontextprotocol.io official docs — MCP architecture, JSON Schema tool definitions, Streamable HTTP transport recommendation
- FastAPI official docs — `HTTPBearer(auto_error=False)`, `APIKeyHeader`, router prefix, combined auth dependencies
- FastAPI official repo (GitHub Discussion #9601) — JWT + API key combined dependency patterns
- Python stdlib docs — `secrets.token_urlsafe()`, `hashlib.sha256()`, `hmac.compare_digest()` usage
- Next.js official docs — `NEXT_PUBLIC_*` build-time variable behavior (relevant for v0.6 infrastructure carrying into v0.7)
- Docker official docs — layer secrets, `.dockerignore`, health check patterns
- Direct codebase analysis — `backend/app/main.py`, `backend/app/config.py`, `backend/app/dependencies.py`, `backend/app/utils/security.py`, `backend/app/models/user.py`

### Secondary (MEDIUM confidence)
- freeCodeCamp — API key best practices (prefix format, SHA-256 hashing, display-once UX)
- Stripe, OpenAI, Perplexity API documentation — competitor key management UX feature comparison
- AppMaster blog — API key rotation, scoping, UX patterns
- oneuptime.com (2026-02-20) — API key management best practices; SHA-256 vs Argon2 for random keys
- slowapi GitHub (laurentS/slowapi) — FastAPI rate limiting, custom `key_func` documentation
- Medium (MCP Streamable HTTP production transport) — production deployment patterns, 2025
- greeden.me (2025-12-30) — practical FastAPI JWT + API key combined security guide
- Dokploy official docs — build types, env vars, volumes, Application model (carried from v0.6 research)
- Docker community forums and HackerNoon — volume persistence and startup race condition patterns

---

*Research completed: 2026-02-23*
*Ready for roadmap: yes*
