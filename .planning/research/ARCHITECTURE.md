# Architecture Research: API Services & MCP Server

**Domain:** API key management, public REST API v1, and MCP server layered onto existing FastAPI monolith
**Researched:** 2026-02-23
**Confidence:** HIGH (core FastAPI patterns from official docs + direct codebase analysis; MCP SDK mounting from official GitHub + FastMCP docs)

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        SPECTRA BACKEND (single FastAPI process)                  │
├────────────────┬──────────────────┬──────────────────┬──────────────────────────┤
│  SPECTRA_MODE  │      public       │      admin        │     api   (NEW v0.7)     │
│   Routes       │  /auth/*          │  /api/admin/*     │  /api/v1/*               │
│                │  /files/*         │                   │  /mcp  (SSE transport)   │
│                │  /chat/*          │                   │                          │
│                │  /sessions/*      │                   │                          │
├────────────────┴──────────────────┴──────────────────┴──────────────────────────┤
│                        Auth Middleware Layer                                      │
│  ┌──────────────────────┐   ┌──────────────────────────────────────────────┐    │
│  │  JWT (existing)       │   │  API Key  (NEW v0.7)                          │    │
│  │  OAuth2PasswordBearer │   │  APIKeyHeader("Authorization") + DB lookup    │    │
│  │  get_current_user()   │   │  get_current_user_from_api_key()              │    │
│  └──────────────────────┘   └──────────────────────────────────────────────┘    │
│                    ↓ unified: get_authenticated_user()                            │
├────────────────────────────────────────────────────────────────────────────────┤
│                        Service Layer (shared across modes)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐    │
│  │  files   │  │  chat    │  │ sessions │  │  credits │  │  api_keys     │    │
│  │ service  │  │ service  │  │ service  │  │  service │  │  service(NEW) │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └───────────────┘    │
├────────────────────────────────────────────────────────────────────────────────┤
│                        Database Layer (PostgreSQL)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐    │
│  │  users   │  │  files   │  │ sessions │  │  credits │  │   api_keys    │    │
│  │          │  │          │  │          │  │          │  │   (NEW table) │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └───────────────┘    │
└────────────────────────────────────────────────────────────────────────────────┘

External consumers:
  ┌──────────────────────────────────────────────────────────┐
  │  MCP Clients (Claude Desktop, Claude.ai, AI agents)      │
  │    ↓  MCP SSE or Streamable HTTP transport               │
  │  GET /mcp  (mounted on api-mode backend)                 │
  └──────────────────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────────────────┐
  │  REST API clients (scripts, integrations)                │
  │    ↓  HTTP + Authorization: Bearer <api_key>             │
  │  /api/v1/*                                               │
  └──────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `SPECTRA_MODE=api` gate | Registers `/api/v1/*` router and `/mcp` endpoint when env is `api` | NEW |
| `api_keys` table | Stores hashed API keys with metadata (prefix, hash, name, user_id, is_active, last_used_at) | NEW |
| `ApiKeyService` | Create, list, revoke, validate API keys | NEW |
| `get_authenticated_user()` dependency | Unified auth: accepts JWT Bearer OR API key Bearer, resolves to User | NEW |
| `routers/api/v1/` | Public REST endpoints under `/api/v1/` (files, context, query) | NEW |
| `routers/api/keys.py` | User-facing key management CRUD (under existing public routes) | NEW |
| `routers/admin/api_keys.py` | Admin-facing key management (list all, revoke any) | NEW |
| `mcp_server.py` | FastMCP instance with tools wrapping v1 endpoints via internal HTTP | NEW |
| Existing `routers/files.py` | Unchanged — v1 mirrors its logic, does not import it | UNCHANGED |
| Existing `dependencies.py` | `get_current_user` unchanged — new `get_authenticated_user` wraps it | MODIFIED (additive) |
| `config.py` / `Settings` | Add `spectra_mode` validation for `api` value | MODIFIED (additive) |
| `main.py` | Add `api` to mode routing block | MODIFIED (additive) |

---

## Recommended Project Structure

```
backend/app/
├── models/
│   ├── api_key.py              # NEW: ApiKey SQLAlchemy model
│   └── api_usage_log.py        # NEW: per-request API usage log (APISEC-04)
│
├── schemas/
│   ├── api_key.py              # NEW: ApiKeyCreate, ApiKeyResponse, ApiKeyListItem
│   └── api_v1.py               # NEW: request/response schemas for v1 endpoints
│
├── services/
│   └── api_keys.py             # NEW: create_key, list_keys, revoke_key, validate_key
│
├── routers/
│   ├── api_keys.py             # NEW: user-facing /api-keys CRUD (public/dev modes)
│   ├── admin/
│   │   └── api_keys.py         # NEW: admin-facing key management
│   └── api/
│       └── v1/
│           ├── __init__.py     # NEW: api_router combining all v1 sub-routers
│           ├── files.py        # NEW: /api/v1/files/* endpoints
│           ├── context.py      # NEW: /api/v1/files/{id}/context endpoints
│           └── query.py        # NEW: /api/v1/query endpoint (synchronous chat)
│
├── mcp_server.py               # NEW: FastMCP instance, tool definitions
│
├── dependencies.py             # MODIFIED: add get_authenticated_user()
├── config.py                   # MODIFIED: add 'api' to mode validator
└── main.py                     # MODIFIED: add api-mode router registration
```

### Structure Rationale

- **`routers/api/v1/`:** Versioned from day one. If v2 is needed, `routers/api/v2/` is a clean addition.
- **`services/api_keys.py`:** Key validation logic lives in a service (not a dependency) so the MCP server can reuse it for authenticating tool calls without importing router code.
- **`mcp_server.py` at app root:** Keeps MCP concerns separate from the router tree. The FastMCP instance is created here and mounted in `main.py` under the `api` mode block.
- **`models/api_usage_log.py`:** Separate model from `credit_transaction` — credit deductions happen in credits service; usage logging is orthogonal (captures endpoint, key ID, timestamp, credits used for APISEC-04).

---

## Architectural Patterns

### Pattern 1: Unified Auth Dependency with Fallback

The existing `get_current_user` only accepts JWT. The v1 API routes need to accept API keys. The correct FastAPI pattern is to create a new combined dependency that tries both schemes with `auto_error=False`, falling back gracefully.

**What:** Single `get_authenticated_user()` dependency that extracts a Bearer token, tries JWT first, falls back to API key lookup if JWT fails.

**When to use:** All `/api/v1/*` endpoints. Do NOT use on `/auth/*` or web frontend routes — keep JWT-only there.

**Trade-offs:** One dependency per call does a JWT decode attempt (fast, in-memory) plus possibly one DB lookup for API key validation. Negligible overhead. Keeps endpoint signatures clean.

**Example:**

```python
# backend/app/dependencies.py (additive changes)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security

http_bearer = HTTPBearer(auto_error=False)

async def get_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(http_bearer)],
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Accept JWT Bearer token OR API key Bearer token.

    Try JWT first (fast, in-memory). If JWT decode fails, attempt API key lookup.
    Returns User in both cases. Raises 401 if neither works.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials

    # Try JWT first (fast path — no DB hit)
    try:
        user_id_str = verify_token(token, "access", settings)
        user_id = UUID(user_id_str)
        user = await get_user_by_id(db, user_id)
        if user and user.is_active:
            return user
    except HTTPException:
        pass  # Fall through to API key check

    # Try API key (DB lookup path)
    from app.services.api_keys import validate_api_key
    user = await validate_api_key(db, token)
    if user:
        return user

    raise HTTPException(
        status_code=401,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# New typed alias for v1 routes
ApiUser = Annotated[User, Depends(get_authenticated_user)]
```

**Why `HTTPBearer` not `OAuth2PasswordBearer` for the combined dependency:** `OAuth2PasswordBearer` adds a Swagger UI "Authorize" button pointing to a tokenUrl, which is wrong for API key flows. `HTTPBearer` with `auto_error=False` extracts the token from `Authorization: Bearer <token>` without asserting what kind of token it is. Swagger UI shows a simpler "value" field for the bearer token, which works for both JWT and API keys during manual testing.

**APISEC-01 note:** The spec says API requests use `Authorization: Bearer <api_key>`. This means API keys and JWT tokens share the same header. The unified dependency handles both correctly — JWT decode is tried first, and if the token does not parse as a valid JWT (wrong structure, wrong issuer), the DB key lookup runs.

---

### Pattern 2: API Key Hashed Storage

**What:** Store a SHA-256 hash of the key, not the key itself. Return the full key exactly once on creation. Include a short prefix in the stored record for fast lookup without full-scan.

**When:** Always. Never store raw API keys in the database.

**Trade-offs:** SHA-256 is appropriate here (not bcrypt/argon2) because API keys are long random strings (32+ bytes), not user-chosen passwords. Brute-forcing SHA-256 against a 32-byte random key is computationally infeasible — the key space is the bottleneck, not the hash speed. Argon2 would add ~250ms per validation, making every API request slow.

**Example — key format:**

```
spc_live_<base64url_32bytes>
         ^^^^^^^^^^^^^^^^^
         secrets.token_urlsafe(32) = ~43 characters

Full key: spc_live_Wd3kJm8XqR1pN6vYtAhBcE0fG2iHjL4oM5nS7uO9wQ=
Prefix stored in DB: spc_live_ (for human identification in admin UI)
Hash stored in DB: sha256(full_key)
```

**Lookup pattern:** Incoming key → SHA-256 → WHERE key_hash = ? AND is_active = true. No prefix-based lookup needed for 1-to-1 hash matching. The `prefix` column is for display/audit only.

---

### Pattern 3: SPECTRA_MODE=api Route Gating

**What:** Add `api` as a fourth valid `spectra_mode` value. The `api` block in `main.py` registers the `/api/v1/` router and mounts the MCP server.

**When:** Any deployment that should expose the public REST API and MCP server. Separate Dokploy service from `public` mode.

**Trade-offs:** The `api` mode intentionally does NOT include the web auth routes (`/auth/signup`, `/auth/login`, etc.) or SSE streaming chat routes — API clients authenticate via API keys and get synchronous responses. This keeps the mode focused and the attack surface minimal.

**Example:**

```python
# backend/app/main.py (additions to existing mode block)

# Validate mode — extend existing check
if mode not in ("public", "admin", "dev", "api"):
    raise ValueError(f"Invalid SPECTRA_MODE: '{mode}'. Must be 'public', 'admin', 'dev', or 'api'")

# API routes (api and dev modes)
if mode in ("api", "dev"):
    from app.routers.api.v1 import api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")

    # User-facing key management (also available in public/dev for web UI)
    from app.routers import api_keys
    app.include_router(api_keys.router)

    # Mount MCP server
    from app.mcp_server import create_mcp_server
    mcp = create_mcp_server()
    mcp_asgi = mcp.http_app(path="/mcp")
    app.mount("/mcp", mcp_asgi)
```

**Why `api` separate from `public`:** The `public` mode serves the web frontend — it needs SSE streaming (`/chat/sessions/{id}/stream`), JWT refresh flows, and password reset emails. The `api` mode serves programmatic clients — synchronous responses, no streaming, no email. Mixing them in one mode forces both client types onto one service with no ability to scale or secure independently.

**`dev` mode includes `api`** so local development can test all routes from one process.

---

### Pattern 4: MCP Server as a FastMCP Instance Mounted on the ASGI App

**What:** Use `fastmcp` (part of the official MCP Python SDK since v1.x) to define tools as decorated functions, then mount the resulting ASGI app onto the FastAPI instance. The MCP tools call the REST API internally via httpx (not by importing router functions directly).

**When:** MCP server must be co-located with the backend in `api` mode.

**Trade-offs:**
- Calling via httpx (loopback) vs importing service functions directly: httpx adds ~1ms round-trip but keeps auth consistent (MCP tools prove they have a valid API key, just like external clients). Direct import would bypass auth entirely, creating a security discrepancy between "API call" and "MCP tool call" paths.
- `FastMCP.from_fastapi(app)` auto-generates tools from OpenAPI spec — convenient but produces many tools (all routes). For Spectra, explicit tool definitions give better tool descriptions and control over what's exposed to Claude.

**Example:**

```python
# backend/app/mcp_server.py

from mcp.server.fastmcp import FastMCP
import httpx

def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name="Spectra Data Analysis")

    @mcp.tool()
    async def upload_file(
        file_content: str,   # base64-encoded
        filename: str,
        context: str = "",
        api_key: str = "",   # injected via MCP client config
    ) -> dict:
        """Upload a CSV or Excel file and trigger AI onboarding analysis.
        Returns file_id, data_brief, and query suggestions."""
        async with httpx.AsyncClient() as client:
            # POST /api/v1/files with Authorization header
            ...

    @mcp.tool()
    async def query_file(
        file_id: str,
        question: str,
        api_key: str = "",
    ) -> dict:
        """Ask a natural language question about an uploaded file.
        Returns analysis text, generated code, and optional chart spec."""
        ...

    return mcp
```

**Lifespan coordination:** The FastMCP `http_app()` has its own lifespan. The existing FastAPI app already has a lifespan (`asynccontextmanager`). Use `combine_lifespans` from FastMCP to merge them:

```python
from fastmcp.utilities.asgi import combine_lifespans

mcp_app = mcp.http_app(path="/mcp")
app = FastAPI(lifespan=combine_lifespans(existing_lifespan, mcp_app.lifespan))
app.mount("/mcp", mcp_app)
```

This ensures the MCP server starts and stops cleanly alongside the FastAPI app without either lifespan cancelling the other.

---

### Pattern 5: Synchronous Query Endpoint (No SSE)

**What:** The `/api/v1/query` endpoint runs the LangGraph agent to completion and returns the full result in a single JSON response. No Server-Sent Events.

**When:** All API v1 chat/query calls. The requirements explicitly defer streaming API responses to v0.8+.

**Trade-offs:** A typical analysis run takes 10-45 seconds (LLM calls + E2B sandbox). Synchronous HTTP means the client must hold the connection open for this duration. This is acceptable for programmatic API clients (scripts, AI agents) but would be unusable in a browser.

**Implementation:** Use the existing LangGraph graph (same agents, same credit deduction) but collect the final state instead of streaming events. The existing `AgentState` already contains all output fields (`analysis_result`, `chart_spec`, `code`). The sync endpoint just runs `graph.ainvoke(...)` and reads the final state.

**Timeout consideration:** Set a 120-second uvicorn/gunicorn request timeout for the `api` mode service. The existing `stream_timeout_seconds: int = 180` in Settings controls SSE; a new `api_query_timeout_seconds: int = 120` config field is appropriate.

---

## Data Flow

### API Key Validation Flow (per request)

```
API Client
  |
  +-> POST /api/v1/files   (Authorization: Bearer spc_live_Wd3k...)
  |
  v
FastAPI dependency resolution
  get_authenticated_user()
    |
    +-> HTTPBearer extracts token from header
    +-> verify_token(token, "access", settings)
    |     -> jwt.decode() raises InvalidTokenError (not a JWT)
    |
    +-> validate_api_key(db, token)
          -> sha256(token) = key_hash
          -> SELECT * FROM api_keys WHERE key_hash=? AND is_active=true
          -> UPDATE api_keys SET last_used_at=now() WHERE id=?
          -> return User (via api_key.user_id FK)
  |
  v
Endpoint handler receives User
  -> credit deduction (existing credits service)
  -> API usage log insert (new api_usage_log table)
  -> business logic (file upload, query, etc.)
```

### MCP Tool Call Flow

```
Claude Desktop / AI Agent
  |
  +-> MCP SSE connection to  GET /mcp
  |     (Streamable HTTP handshake)
  |
  +-> tool call: query_file(file_id="...", question="...", api_key="spc_live_...")
  |
  v
FastMCP tool handler (mcp_server.py)
  |
  +-> httpx.AsyncClient().post(
  |     "http://localhost:8000/api/v1/query",
  |     headers={"Authorization": f"Bearer {api_key}"},
  |     json={"file_id": file_id, "question": question}
  |   )
  |
  v
/api/v1/query endpoint
  -> get_authenticated_user() validates api_key
  -> LangGraph ainvoke()
  -> returns JSON result
  |
  v
FastMCP returns tool result to MCP client
```

### Key Creation Flow

```
User (via web UI or direct API call)
  |
  +-> POST /api-keys  {name: "My Script Key"}
  |   (Authorization: Bearer <jwt_token>)
  |
  v
get_current_user() (JWT-only, existing dependency — key mgmt uses JWT auth)
  |
  v
ApiKeyService.create_key(user_id, name)
  -> raw_key = "spc_live_" + secrets.token_urlsafe(32)
  -> key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
  -> INSERT INTO api_keys (user_id, key_hash, prefix, name, is_active, created_at)
  -> return {id, name, key: raw_key, created_at}  <- raw_key returned ONCE
  |
  v
Client receives raw_key — must store it, never retrievable again
```

---

## New vs Modified Components

### New Files

| File | Purpose | Covers Requirements |
|------|---------|---------------------|
| `backend/app/models/api_key.py` | ApiKey ORM model | APIKEY-05 |
| `backend/app/models/api_usage_log.py` | Per-request log model | APISEC-04 |
| `backend/app/schemas/api_key.py` | Pydantic schemas for key CRUD | APIKEY-01..08 |
| `backend/app/schemas/api_v1.py` | v1 endpoint request/response schemas | APIF, APIC, APIQ |
| `backend/app/services/api_keys.py` | Create / validate / revoke logic | APIKEY-01..08, APISEC-01..02 |
| `backend/app/routers/api_keys.py` | User-facing key management endpoints | APIKEY-01..05 |
| `backend/app/routers/admin/api_keys.py` | Admin key management endpoints | APIKEY-06..08 |
| `backend/app/routers/api/__init__.py` | Package init | — |
| `backend/app/routers/api/v1/__init__.py` | Combines v1 sub-routers | APIINFRA-02 |
| `backend/app/routers/api/v1/files.py` | /api/v1/files endpoints | APIF-01..04 |
| `backend/app/routers/api/v1/context.py` | /api/v1/files/{id}/context endpoints | APIC-01..03 |
| `backend/app/routers/api/v1/query.py` | /api/v1/query synchronous query | APIQ-01 |
| `backend/app/mcp_server.py` | FastMCP server instance + tool definitions | MCP-01..05 |
| Alembic migration | api_keys + api_usage_log tables | APIKEY-05 |

### Modified Files

| File | Change | Risk |
|------|--------|------|
| `backend/app/dependencies.py` | Add `get_authenticated_user()` + `ApiUser` type alias | Low — additive only |
| `backend/app/config.py` | Add `api` to `spectra_mode` validator; add `api_query_timeout_seconds` field | Low — additive |
| `backend/app/main.py` | Add `api` to mode check; register v1 router + MCP mount in `api`/`dev` block | Medium — touches routing |
| `backend/app/routers/admin/__init__.py` | Include new admin api_keys router | Low — additive |
| `backend/pyproject.toml` | Add `mcp[cli]` dependency (FastMCP is included in `mcp` package) | Low |

### Unchanged Files

All existing routers (`auth.py`, `files.py`, `chat.py`, `chat_sessions.py`, `credits.py`) are unchanged. The v1 API routes duplicate the relevant service calls rather than importing from existing routers — this keeps the public API contract independent of internal route evolution.

---

## Data Model: api_keys Table

```python
# backend/app/models/api_key.py

class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    prefix: Mapped[str] = mapped_column(String(20))      # "spc_live_" — display only
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # SHA-256 hex
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")
```

**Why SHA-256 not Argon2:** API keys are 32 bytes of cryptographic randomness (`secrets.token_urlsafe(32)`). Their entropy (~256 bits) makes brute force infeasible regardless of hash speed. Argon2 adds ~250ms per validation, which would add 250ms to every API request. SHA-256 is ~microseconds and is the standard for this use case (used by GitHub, Stripe, Twilio). [MEDIUM confidence — consistent across multiple 2025 sources]

**Key format:** `spc_live_<secrets.token_urlsafe(32)>` — total length ~50 characters. The `spc_live_` prefix lets users and admins identify Spectra keys in logs. No separate lookup index on prefix needed — `key_hash` index handles all auth lookups.

---

## Data Model: api_usage_log Table

```python
# backend/app/models/api_usage_log.py

class ApiUsageLog(Base):
    __tablename__ = "api_usage_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    api_key_id: Mapped[UUID] = mapped_column(ForeignKey("api_keys.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String(100))    # e.g., "POST /api/v1/query"
    credits_used: Mapped[Decimal] = mapped_column(Numeric(10, 1), default=0)
    status_code: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
```

This is append-only. Admin can query per-user or per-key. Not exposed via a v0.7 endpoint (APISEC-04 is logging only; reporting UI is future work).

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (1-10 API users) | Single `api` mode Dokploy service; SHA-256 key lookup is O(1) via index |
| 100-1000 API users | Add Redis cache for validated API keys (TTL = 60s) to avoid DB hit per request; api_usage_log table will grow — add partition by month |
| 10k+ API users | Rate limiting layer (RATELIMIT-01..03 deferred to v0.8); consider separate read replica for key validation |

### Scaling Priorities

1. **First bottleneck:** `api_usage_log` table becomes large quickly at high request rates. Add `created_at` index and consider TimescaleDB extension or monthly partitioning before the table exceeds 10M rows.
2. **Second bottleneck:** API key DB lookup on every request. A 60-second in-memory or Redis TTL cache per key_hash cuts DB load by ~99% for burst traffic without stale revocation risk (60-second revocation window is acceptable for API keys).

---

## Anti-Patterns

### Anti-Pattern 1: API Keys as JWT Claims

**What people do:** Generate a "long-lived JWT" and call it an API key.
**Why it's wrong:** JWTs are self-contained — you cannot revoke them without a revocation list or waiting for expiry. API keys must be instantly revocable (APIKEY-03, APIKEY-04). A compromised key needs to stop working in seconds, not 30 minutes.
**Do this instead:** Random opaque token stored as SHA-256 hash in DB. Revocation is a single `UPDATE api_keys SET is_active=false WHERE id=?`.

### Anti-Pattern 2: Storing Raw API Keys in the Database

**What people do:** Store the full key in a `key` VARCHAR column "for display".
**Why it's wrong:** A database dump exposes all keys. The entire point of key management is that the secret is shown once and never stored.
**Do this instead:** Store only `key_hash` (SHA-256 hex) and `prefix` (display-only). The user must copy the key at creation time. Include a clear UI warning: "This key will not be shown again."

### Anti-Pattern 3: Importing Router Functions from Existing Routers into v1 Routers

**What people do:** `from app.routers.files import upload_file_handler` and call it from the v1 router.
**Why it's wrong:** Existing routers have FastAPI-specific parameter handling (Form fields, UploadFile, streaming responses) tied to the web frontend. Importing them couples the public API contract to internal router implementation details.
**Do this instead:** Both existing routers and v1 routers call the same **service layer** functions directly. The service functions (`files_service.create_file()`, etc.) are the shared boundary, not the router handlers.

### Anti-Pattern 4: Mounting MCP Server on All Modes

**What people do:** Mount the MCP server in `public` mode alongside the web frontend.
**Why it's wrong:** The MCP server exposes AI tool endpoints that should require API key auth. `public` mode also serves unauthenticated routes (`/auth/signup`). Mixing them adds complexity and a larger attack surface to the main public service.
**Do this instead:** Mount MCP only in `api` and `dev` modes. The API service is a separate Dokploy deployment.

### Anti-Pattern 5: MCP Tools Importing Service Functions Directly (Bypassing Auth)

**What people do:** In `mcp_server.py`, call `await files_service.create_file(user_id, ...)` directly after extracting `api_key` from the MCP context.
**Why it's wrong:** The credit deduction, usage logging, and user resolution logic lives in the HTTP dependency chain. Bypassing it means MCP tool calls don't deduct credits or log usage — inconsistent with APISEC-03 and APISEC-04.
**Do this instead:** MCP tool handlers make an internal httpx call to `http://localhost:8000/api/v1/...` with the `Authorization: Bearer <api_key>` header. This runs the full middleware stack including credit deduction and logging. The loopback overhead (~1ms) is negligible.

---

## Integration Points

### New External Dependencies

| Dependency | Integration | Notes |
|------------|------------|-------|
| `mcp[cli]` PyPI package | FastMCP server instance, `mcp.http_app()` ASGI mounting | Part of official Python MCP SDK; version 1.x stable. Includes `fastmcp` module. |
| `httpx` | Already in project via LangChain/httpx | MCP tool handlers use it for internal API calls |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| v1 routers ↔ service layer | Direct Python function calls | Same pattern as existing routers |
| MCP tool handlers ↔ v1 API | httpx over loopback | Preserves full auth/credit middleware chain |
| `get_authenticated_user` ↔ existing `get_current_user` | `get_authenticated_user` calls `verify_token` then falls back to `validate_api_key` | `get_current_user` unchanged |
| API key management routes ↔ `api_keys` service | Direct function calls | Same pattern as all other services |

### Deployment: 5th Dokploy Service

```
spectra-api  (NEW Dokploy Application service)
  Dockerfile: Dockerfile.backend (same image as public/admin)
  SPECTRA_MODE=api
  Domain: api.spectra.io (public HTTPS)
  Environment:
    DATABASE_URL=<shared postgres>
    SPECTRA_MODE=api
    SECRET_KEY=<same as public backend — needed for JWT validation>
    ANTHROPIC_API_KEY=<same as public>
    E2B_API_KEY=<same as public>
    CORS_ORIGINS=["*"]  (API clients, no browser restrictions needed)
    UPLOAD_DIR=/app/uploads
  Volume: spectra_uploads -> /app/uploads  (same named volume as public backend)
```

**Shared volume note:** If `spectra-api` and `spectra-public` run on the same Dokploy host, both can mount the `spectra_uploads` named volume. Files uploaded via API are immediately accessible to the public web frontend and vice versa. If they run on different hosts, a shared volume strategy (NFS or S3) is needed — but that is a v0.8+ concern given current single-host deployment.

---

## Build Order for Phases

Dependencies between components determine implementation order:

```
Phase 1: Data Model + API Key Service
  - api_keys table + ApiKey model
  - api_usage_log table
  - ApiKeyService (create, list, revoke, validate)
  - Alembic migration
  RATIONALE: Everything else depends on being able to validate an API key.

Phase 2: Auth Integration + Key Management Routes
  - get_authenticated_user() dependency in dependencies.py
  - /api-keys CRUD endpoints (user-facing, under public/dev modes)
  - Admin /api/admin/api-keys endpoints
  - config.py + main.py mode additions
  RATIONALE: Auth layer must be solid before any v1 endpoint is written.

Phase 3: REST API v1 Endpoints
  - /api/v1/files (upload, list, delete, download)
  - /api/v1/files/{id}/context (get, update, suggestions)
  - /api/v1/query (synchronous analysis)
  RATIONALE: Can develop and test each endpoint independently with valid API key.

Phase 4: MCP Server
  - mcp_server.py tool definitions
  - Lifespan coordination with FastAPI
  - Mount in main.py api/dev mode block
  RATIONALE: MCP tools are thin wrappers over Phase 3 endpoints. Build last when endpoints are stable.
```

---

## Sources

- MCP Python SDK (official): [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) — HIGH confidence
- FastMCP + FastAPI integration guide: [https://gofastmcp.com/integrations/fastapi](https://gofastmcp.com/integrations/fastapi) — HIGH confidence (official FastMCP docs)
- FastMCP running server / HTTP transport: [https://gofastmcp.com/deployment/running-server](https://gofastmcp.com/deployment/running-server) — HIGH confidence
- FastAPI-MCP (tadata library, alternative approach): [https://github.com/tadata-org/fastapi_mcp](https://github.com/tadata-org/fastapi_mcp) — MEDIUM confidence (third-party, v0.4.0, active)
- FastAPI combining OAuth2 + APIKeyHeader discussion: [https://github.com/fastapi/fastapi/discussions/9601](https://github.com/fastapi/fastapi/discussions/9601) — HIGH confidence (official FastAPI repo)
- FastAPI `HTTPBearer(auto_error=False)` pattern for optional auth: [https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — HIGH confidence (official FastAPI docs)
- API key best practices (SHA-256 storage, format, metadata): [https://oneuptime.com/blog/post/2026-02-20-api-key-management-best-practices/view](https://oneuptime.com/blog/post/2026-02-20-api-key-management-best-practices/view) — MEDIUM confidence (2026 article, consistent with GitHub/Stripe public documentation)
- Practical FastAPI security guide (JWT + API key combined): [https://blog.greeden.me/en/2025/12/30/practical-fastapi-security-guide-designing-modern-apis-protected-by-jwt-auth-oauth2-scopes-and-api-keys/](https://blog.greeden.me/en/2025/12/30/practical-fastapi-security-guide-designing-modern-apis-protected-by-jwt-auth-oauth2-scopes-and-api-keys/) — MEDIUM confidence (2025, community)
- MCP Streamable HTTP production transport recommendation: [https://medium.com/@nsaikiranvarma/building-production-ready-mcp-server-with-streamable-http-transport-in-15-minutes-ba15f350ac3c](https://medium.com/@nsaikiranvarma/building-production-ready-mcp-server-with-streamable-http-transport-in-15-minutes-ba15f350ac3c) — MEDIUM confidence (community, 2025)
- Direct codebase analysis: `backend/app/main.py`, `backend/app/config.py`, `backend/app/dependencies.py`, `backend/app/utils/security.py`, `backend/app/models/user.py` — HIGH confidence

---

*Architecture research for: API key authentication, public REST API v1, SPECTRA_MODE=api, MCP server integration*
*Researched: 2026-02-23*
