# Technology Stack: v0.7 API Services & MCP

**Project:** Spectra — AI-powered data analytics platform
**Researched:** 2026-02-23
**Confidence:** HIGH (all libraries verified via PyPI, official docs, and FastMCP documentation site)

## Overview

v0.7 adds three new capabilities to the existing FastAPI backend: API key management, a versioned public REST API (v1), and an MCP server that wraps those API endpoints as tools for Claude/AI agents. The architecture extends the existing SPECTRA_MODE split-horizon pattern with a 5th mode (`api`).

**Key principle: minimal new dependencies, maximum reuse.** The existing stack handles almost everything. Only two new Python packages are genuinely required: `fastmcp` (MCP server framework) and `slowapi` (rate limiting for the public API). API key management uses Python stdlib (`secrets`, `hashlib`) plus the existing SQLAlchemy/Alembic/FastAPI stack.

---

## What Changes (and What Does Not)

### Does NOT Change

- FastAPI backend framework
- PostgreSQL + SQLAlchemy ORM + Alembic migrations
- JWT Bearer authentication (existing user-facing flow, unchanged)
- LangGraph agent orchestration
- E2B sandbox execution
- pydantic-settings + python-dotenv
- All frontend applications (no frontend changes in v0.7)
- Docker + Dokploy deployment infrastructure

### Changes Required

| Layer | What Changes | Why |
|-------|-------------|-----|
| Backend: New model | `api_keys` table | Store hashed keys with metadata |
| Backend: New routers | `routers/api_keys.py`, `routers/v1/` directory | API key CRUD and versioned public endpoints |
| Backend: Auth dependency | `get_current_user_or_api_key` dependency | Support both JWT and API key auth |
| Backend: Admin router | Extend admin with API key management | Admin can view/revoke all user API keys |
| Backend: MCP server | `mcp_server.py` + mount in `api` mode | MCP protocol endpoint |
| Backend: SPECTRA_MODE | Add `api` as valid 5th mode | Isolated API + MCP deployment |
| Backend: Rate limiting | Per-key request limiting | Protect public API from abuse |
| Config: Settings | New env vars for API mode | Rate limits, API key prefix |

---

## Recommended Stack Additions

### Backend: New Python Dependencies (2 packages)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `fastmcp` | `>=3.0.2` | MCP server framework | The de facto standard for Python MCP servers. v3.0.0 (released 2026-01-19) introduced the `FastMCP.from_fastapi()` method that generates MCP tools directly from a FastAPI app's OpenAPI spec — zero boilerplate. Powers ~70% of all MCP servers. Python >=3.10 required. |
| `slowapi` | `>=0.1.9` | Rate limiting for FastAPI/Starlette | Thin wrapper on `limits` library, integrates with FastAPI via dependency injection. Supports custom key functions (extract API key from header, not just IP). In-memory storage sufficient for single-instance `api` mode deployment. |

**Why `fastmcp` over the base `mcp` package (1.26.0):**
- The base `mcp` SDK requires manual tool registration, transport setup, and session management — 3–5x more boilerplate.
- `fastmcp` 3.0 provides `FastMCP.from_fastapi(app=app)` which auto-generates MCP tools from your FastAPI OpenAPI spec. The Spectra v1 API can become an MCP server in ~10 lines.
- FastMCP handles transport negotiation (Streamable HTTP default, SSE fallback), authentication (`BearerAuthProvider`, `DebugTokenVerifier`), and session lifecycle automatically.
- Both packages are Python >=3.10 compatible with the project's Python 3.12 requirement.

**Why `slowapi` over alternatives:**
- `limits` (the underlying library) supports in-memory, Redis, and Memcached backends. For a single-instance `api` mode deployment, in-memory is sufficient with no added infrastructure.
- Custom `key_func` extracts the API key from the `Authorization: Bearer` header — rate limiting is per-key, not per-IP.
- Integrates with FastAPI via a single middleware line and `@limiter.limit()` decorator. No separate process or config file needed.
- vs Redis-based rate limiting: overkill for single-instance. Add Redis only when horizontal scaling is needed.

---

### Backend: Python Standard Library (No New Dependencies)

API key generation and storage use stdlib — no additional packages:

| Capability | Module | Usage |
|------------|--------|-------|
| Key generation | `secrets.token_urlsafe(32)` | 256-bit cryptographically secure random key |
| Key hashing (storage) | `hashlib.sha256()` | Hash full key for DB storage |
| Timing-safe comparison | `hmac.compare_digest()` | Prevent timing attacks during key lookup |
| Key prefix | string formatting | `spe_` prefix for visual identification |

**API Key format:** `spe_{secrets.token_urlsafe(32)}`
- `spe_` prefix makes Spectra keys visually identifiable (like GitHub `ghp_`, Stripe `sk_`)
- `token_urlsafe(32)` = 256 bits of entropy, URL-safe, no padding chars
- Store: `sha256(full_key_string).hexdigest()` — no bcrypt needed (keys are random, not user-chosen passwords; SHA-256 is computationally fast which is acceptable here since the key has enough entropy to resist brute force)
- Show the full key ONCE at creation time only (standard API key UX)

---

### Backend: Existing Dependencies (Already Installed, Zero Changes)

| Existing Dependency | v0.7 Usage | Notes |
|---------------------|-----------|-------|
| `fastapi[standard]>=0.115` | New v1 routers, API key endpoints, MCP mount | Prefix `/api/v1/` |
| `sqlalchemy[asyncio]` + `asyncpg` | `api_keys` table, key lookup queries | Same ORM patterns |
| `alembic` | Migration for `api_keys` table | Same migration chain |
| `pyjwt` | JWT auth path unchanged | API endpoints accept BOTH JWT and API keys |
| `pydantic-settings` | New settings: rate limits, API mode CORS | Extend existing `Settings` |
| `pwdlib[argon2]` | Unchanged (user password hashing) | API key hashing uses `hashlib`, not `pwdlib` |
| `httpx` | MCP server makes internal ASGI calls to FastAPI app | `FastMCP.from_fastapi()` uses httpx internally |
| `sse-starlette` | SSE transport for MCP (if needed) | FastMCP uses this for SSE transport fallback |

---

## MCP Server Architecture Decision: `from_fastapi()` vs Manual Tools

Two approaches exist for building the MCP server:

**Option A: `FastMCP.from_fastapi(app=app)` — Auto-generate from OpenAPI spec**
- Single call generates all v1 endpoint tools automatically
- Tool names from FastAPI `operation_id` parameters (requires explicit IDs on v1 routes)
- Authentication forwarded via `httpx_client_kwargs`
- FastMCP documentation explicitly warns: "LLMs achieve significantly better performance with well-designed and curated MCP servers than with auto-converted OpenAPI servers"

**Option B: Manual FastMCP tool definitions wrapping v1 endpoints**
- Define each tool explicitly with curated names, descriptions, and parameter docs
- Better LLM performance — descriptions optimized for AI agent consumption
- More code, but each tool is intentional and tested independently

**Recommendation: Option B (manual tools) with Option A as scaffold.**
Use `FastMCP.from_fastapi()` to auto-generate the initial tool definitions, then curate and override each tool's description for AI agent clarity. This gives the best of both: speed to bootstrap, quality in production. The Spectra v0.7 API surface is small (file upload, file context, synchronous query) — manual curation of 5–8 tools is feasible.

---

## Synchronous Chat Endpoint Design

The existing `/chat` SSE endpoint is not suitable for MCP tool calls (AI agents need a single response, not a streaming event stream). The v1 API needs a **synchronous (non-SSE) query endpoint**:

```
POST /api/v1/query
Body: { session_id, message, file_ids[] }
Returns: { result, chart_spec, code, explanation } — JSON, not SSE
```

The existing LangGraph agent runs asynchronously internally — the sync endpoint awaits the full graph execution and returns the complete result. This removes the streaming UX but is appropriate for programmatic/agent use. Credit deduction, sandbox execution, and agent routing all work unchanged.

---

## API Mode Routing in SPECTRA_MODE

Add `api` as a 5th valid value for `SPECTRA_MODE`. The `api` mode mounts:
1. Public v1 API endpoints (`/api/v1/files`, `/api/v1/sessions`, `/api/v1/query`)
2. API key management endpoints (`/api/keys`)
3. MCP server endpoint (`/mcp`)
4. Health + version endpoints (always)

The `api` mode does NOT mount: admin routes, browser-oriented auth (cookie session), or credit display endpoints. User authentication for the API mode uses API keys only (no JWT Bearer for the API surface — cleaner separation).

---

## API Key Auth Dependency Pattern

The existing `CurrentUser` dependency uses `OAuth2PasswordBearer` (JWT only). The v1 API needs a new dependency that accepts either JWT or an API key:

```python
# New: API key header scheme
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_user_from_api_key(
    api_key: str | None = Security(api_key_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    # Hash the provided key, look up in api_keys table
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_record = await ApiKeyService.get_by_hash(db, key_hash)
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return api_key_record.user
```

The v1 routers use `ApiKeyUser` (API key auth only). The MCP server passes the API key to FastAPI via `httpx_client_kwargs={"headers": {"X-API-Key": token}}`.

---

## MCP Server Authentication

FastMCP supports `DebugTokenVerifier` with a custom callable for database-backed token validation:

```python
from fastmcp.server.auth.providers.debug import DebugTokenVerifier

async def validate_api_key_token(token: str) -> bool:
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    record = await db_lookup(key_hash)
    return record is not None and record.is_active

auth = DebugTokenVerifier(validate=validate_api_key_token)
mcp = FastMCP.from_fastapi(app=v1_app, auth=auth)
```

This allows the MCP server to accept the same `spe_*` API keys as the REST API.

---

## Recommended Stack Summary

| Technology | Version | New? | Purpose |
|------------|---------|------|---------|
| `fastmcp` | `>=3.0.2` | YES | MCP server framework |
| `slowapi` | `>=0.1.9` | YES | Per-key rate limiting |
| `secrets` (stdlib) | — | No | API key generation |
| `hashlib` (stdlib) | — | No | SHA-256 key hashing |
| `hmac` (stdlib) | — | No | Timing-safe key comparison |
| `fastapi[standard]` | `>=0.115` | No (existing) | v1 routers, API mode |
| `sqlalchemy[asyncio]` | `>=2.0` | No (existing) | `api_keys` model |
| `alembic` | `>=1.13` | No (existing) | DB migration |

---

## Supporting Libraries: What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `fastapi-mcp` (tadata-org) | Last release v0.4.0, July 2025. Separate library that wraps FastMCP — adds an abstraction layer over FastMCP without enough benefit. FastMCP 3.0 already has `from_fastapi()` natively. | `fastmcp` directly |
| `mcp` (base SDK) | Manual transport, session, tool registration boilerplate. FastMCP wraps this with a much better DX. | `fastmcp` |
| `bcrypt` for key hashing | Bcrypt is for user-chosen passwords (brute-force resistant slow hashing). API keys are 256-bit random — SHA-256 is appropriate (not brute-forceable). Bcrypt adds unnecessary latency on every API request. | `hashlib.sha256()` |
| `redis` for rate limiting | `slowapi` in-memory storage is sufficient for single-instance `api` mode. Redis needed only for horizontal scaling. | `slowapi` with in-memory |
| `fastapi-versioning` / `fastapi-versionizer` | Small libraries that add routing complexity. Manual prefix pattern (`/api/v1/`) in `main.py` is simpler and already follows the project's router pattern. | Manual `prefix="/api/v1"` |
| OAuth2 / JWT for API consumers | Programmatic API consumers (scripts, agents) don't benefit from user-facing OAuth flows. API keys are simpler to generate, rotate, and revoke. | `spe_*` API keys |
| `celery` / background tasks for query | The existing LangGraph graph is async — it can be awaited synchronously in the v1 query endpoint. No background task queue needed for synchronous API responses. | `await graph.ainvoke()` |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| MCP framework | `fastmcp>=3.0.2` | `mcp>=1.26.0` (base SDK) | Base SDK requires manual tool registration, transport setup, session management. FastMCP provides `from_fastapi()` auto-generation and `DebugTokenVerifier` for custom auth. |
| MCP framework | `fastmcp` (manual tools) | `FastMCP.from_fastapi()` only | Auto-generated tools have poor LLM descriptions. Curated manual tools perform better for AI agents. Use `from_fastapi()` as scaffold only. |
| Key hashing | `hashlib.sha256` | `bcrypt` | Bcrypt is for user passwords. API keys have 256-bit entropy — SHA-256 lookup is appropriate and fast. |
| Rate limiting | `slowapi` | Redis + custom middleware | Redis adds infrastructure dependency. Single-instance `api` mode doesn't need distributed rate limiting. |
| API versioning | Manual `prefix="/api/v1"` | `fastapi-versioning` library | The project has 1 API version. Library overhead not justified. Router prefix is the FastAPI-idiomatic approach. |
| Chat endpoint | Synchronous JSON response | SSE streaming | AI agent tool calls need a single return value. SSE streaming is a browser UX pattern. v1 API wraps the async agent with `await graph.ainvoke()`. |

---

## Installation

```bash
cd backend

# Add to pyproject.toml dependencies:
# "fastmcp>=3.0.2",
# "slowapi>=0.1.9",

uv add fastmcp
uv add slowapi
```

No frontend changes. No new npm packages. No new infrastructure (no Redis, no message broker).

---

## New Environment Variables

```bash
# v0.7 additions to .env

# API mode (5th valid value for SPECTRA_MODE)
SPECTRA_MODE=api

# Rate limiting (applied per API key)
API_RATE_LIMIT=60/minute         # Default: 60 requests per minute per key
API_RATE_LIMIT_BURST=10/second   # Burst limit

# API key settings
API_KEY_PREFIX=spe_              # Visual prefix for Spectra keys

# MCP endpoint (mounted at /mcp in api mode)
MCP_SERVER_NAME=spectra-analytics
```

---

## Integration Points with Existing Stack

### 1. SPECTRA_MODE Extended

```python
# In config.py: no change needed (string field, validated in main.py)
# In main.py: add "api" to valid modes

if mode not in ("public", "admin", "dev", "api"):
    raise ValueError(f"Invalid SPECTRA_MODE: '{mode}'")

if mode in ("public", "dev", "api"):
    app.include_router(auth.router)      # Still needed for API key management UI
    app.include_router(files.router)
    # ... existing routers

if mode in ("api", "dev"):
    from app.routers import api_keys
    app.include_router(api_keys.router)  # /api/keys
    from app.routers.v1 import v1_router
    app.include_router(v1_router, prefix="/api/v1")  # /api/v1/*

if mode == "api":
    from app.mcp_server import create_mcp_server
    mcp = create_mcp_server(app)
    mcp_app = mcp.http_app(path="/")
    app.mount("/mcp", mcp_app)           # /mcp (Streamable HTTP transport)
```

### 2. New Database Table: `api_keys`

```python
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: UUID
    user_id: UUID (FK -> users.id)
    name: str                          # User-provided label
    key_hash: str (unique, indexed)    # sha256(full_key)
    key_prefix: str                    # First 8 chars of key (for display)
    is_active: bool = True
    last_used_at: datetime (nullable)
    created_at: datetime
    expires_at: datetime (nullable)    # Optional expiry
```

Migration: single Alembic migration, no backfill needed (new table).

### 3. Credit Deduction (API Path)

The v1 `/query` endpoint uses the same `CreditService.deduct_credit()` call as the existing chat router. API key auth resolves to a `User` object — the credit deduction path is identical. No changes to `CreditService`.

### 4. MCP Server Mounting (lifespan)

```python
# FastMCP requires its lifespan to be passed to the parent FastAPI app:
mcp_app = mcp.http_app(path="/")
app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
```

This means the `api` mode FastAPI app must be constructed differently from other modes (lifespan from MCP app). In practice: only instantiate the MCP app in `api` mode; other modes use the existing lifespan.

---

## Version Compatibility Matrix

| Package | Version | Python | Compatibility Notes |
|---------|---------|--------|---------------------|
| `fastmcp` | >=3.0.2 | Python >=3.10 | Released 2026-02-22. Compatible with Python 3.12. Requires `httpx` (already installed). |
| `slowapi` | >=0.1.9 | Python >=3.8 | Compatible with FastAPI 0.115+. Uses `limits` library internally. |
| `fastapi[standard]` | >=0.115 | Python >=3.8 | Unchanged. `fastmcp.from_fastapi()` requires FastAPI's OpenAPI spec generation (v3.0.0+). |
| `mcp` (transitive) | >=1.26.0 | Python >=3.10 | Pulled in by `fastmcp` as a dependency — do not add separately. |

---

## Project Structure After v0.7

```
spectra-dev/
  backend/
    app/
      config.py                    # + api rate limit settings
      main.py                      # + "api" mode, v1 router, MCP mount
      mcp_server.py                # NEW: FastMCP server definition + manual tool curation
      models/
        api_key.py                 # NEW: ApiKey model
      routers/
        api_keys.py                # NEW: /api/keys CRUD (user self-service)
        v1/
          __init__.py              # NEW: v1_router
          files.py                 # NEW: /api/v1/files (upload, list, get, delete)
          sessions.py              # NEW: /api/v1/sessions (create, list, get)
          query.py                 # NEW: /api/v1/query (synchronous chat)
        admin/
          api_keys.py              # NEW: Admin view/revoke all keys
      services/
        api_key_service.py         # NEW: key generation, hash lookup, CRUD
      dependencies.py              # + get_user_from_api_key dependency
    alembic/
      versions/
        xxx_add_api_keys.py        # NEW migration
  frontend/                        # UNCHANGED
  admin-frontend/                  # UNCHANGED (admin router addition is backend-only)
```

---

## Sources

**FastMCP:**
- [fastmcp PyPI](https://pypi.org/project/fastmcp/) — v3.0.2 current (2026-02-22), Python >=3.10 — HIGH confidence
- [FastMCP official docs](https://gofastmcp.com/deployment/http) — HTTP deployment, Streamable HTTP transport, ASGI mounting — HIGH confidence
- [FastMCP FastAPI integration docs](https://gofastmcp.com/integrations/fastapi) — `from_fastapi()`, mounting pattern, lifespan requirement — HIGH confidence
- [FastMCP authentication docs](https://gofastmcp.com/servers/auth/authentication) — `DebugTokenVerifier`, `BearerAuthProvider` — HIGH confidence
- [FastMCP token verification docs](https://gofastmcp.com/servers/auth/token-verification) — Custom callable validation pattern — HIGH confidence

**MCP base SDK:**
- [mcp PyPI](https://pypi.org/project/mcp/) — v1.26.0 (2026-01-24), pulled as fastmcp dependency — HIGH confidence

**slowapi:**
- [slowapi GitHub](https://github.com/laurentS/slowapi) — Rate limiting for Starlette/FastAPI — MEDIUM confidence (not verified with Context7, but multiple sources confirm compatibility)

**API Key Design:**
- [API key best practices (Mergify)](https://articles.mergify.com/api-keys-best-practice/) — Prefix format, SHA-256 hashing, key rotation — MEDIUM confidence
- [Python secrets module](https://docs.python.org/3/library/secrets.html) — `token_urlsafe()` for generation — HIGH confidence

**FastAPI Versioning:**
- [FastAPI APIRouter docs](https://fastapi.tiangolo.com/reference/apirouter/) — `prefix` parameter for `/api/v1` — HIGH confidence

---

*Stack research for: Spectra v0.7 API Services & MCP*
*Researched: 2026-02-23*
*Confidence: HIGH — Two new backend dependencies (fastmcp v3.0.2, slowapi). API key management uses Python stdlib. No frontend changes. No new infrastructure. MCP server mounts inside existing FastAPI app via ASGI. Split-horizon extension follows established SPECTRA_MODE pattern.*
