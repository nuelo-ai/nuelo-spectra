# Feature Research

**Domain:** API Key Management, Public REST API v1, and MCP Server — Spectra v0.7
**Researched:** 2026-02-23
**Confidence:** HIGH (API key UX and REST patterns verified against multiple sources and industry standards; MCP verified against official modelcontextprotocol.io docs and Python SDK)
**Supersedes:** Previous FEATURES.md (v0.6 Docker/Dokploy features, 2026-02-18)

---

## Context: Subsequent Milestone Scope

This research covers only the NEW features being added in v0.7. The following already exist and must NOT be re-planned:

- JWT authentication with refresh tokens
- File upload and management (Excel/CSV, up to 50MB)
- 6-agent LangGraph analysis system (sessions, multi-file, cross-file, streaming)
- Credit system with atomic deduction and tier-based allocations
- Admin portal with user management (SPECTRA_MODE split-horizon)
- Docker/Dokploy deployment infrastructure

v0.7 adds three surfaces on top of the existing backend:
1. **API key management** — new DB table + CRUD endpoints + user-facing UI screen + admin portal extension
2. **Public REST API v1** — programmatic access to file management and analysis capabilities
3. **MCP server** — wraps REST API as tools callable by Claude Desktop, Claude Code, or any MCP host

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that developers and API consumers assume exist. Missing any of these makes the product feel incomplete or untrustworthy to developers evaluating integration.

#### API Key Management — User Self-Service

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Create named API key | Every API portal lets users name keys descriptively. Name is the only identifier after creation since the full key is hashed. | LOW | Name is required; e.g., "CI pipeline prod" or "Claude Desktop". Enforce non-empty, max 100 chars. |
| Display full key exactly once on creation | Industry-standard security invariant — key is hashed at rest, never stored in plaintext, therefore never retrievable after creation | LOW | Show full key in a modal/dialog with an explicit "Copy now. You will not be able to view this key again." warning and a copy-to-clipboard button. Modal closes on user confirmation. |
| Show key prefix in list view | Users cannot identify keys without seeing something. Full hash is never stored, so a prefix (first 8-12 chars of raw key) is stored plaintext and displayed in the list. | LOW | Display format: `sk-spectra-abc12345...` — the prefix disambiguates keys without exposing anything useful to an attacker |
| Revoke (delete) a key | Users must be able to decommission compromised or stale keys. Revocation must be immediate. | LOW | Confirmation dialog required. Set `revoked_at` timestamp; do not hard-delete (audit trail). Key immediately fails auth after revocation. |
| List keys with metadata | Developers need to audit what keys exist and when they were last used to identify stale keys or suspicious access | LOW | Columns: Name, Prefix, Created, Last Used (or "Never"), Status (Active / Revoked) |
| Key status indicator | Instant visual feedback on usability. Active keys are the operational default; revoked keys are dead. | LOW | Active (green) / Revoked (red/muted). No other statuses at v1. |
| Cannot view key again after creation | Security invariant enforced in UI — no "reveal key" button anywhere. Only prefix is ever shown post-creation. | LOW | Any "view key" UI is an anti-pattern. The list shows prefix only; full key is permanently gone after the creation modal closes. |

#### API Key Management — Admin Portal Extension

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| View all users' API keys | Admins must audit key usage across the platform for security compliance and support | LOW | Read-only list view per user within existing admin user management screen. Same metadata columns as user view. |
| Revoke any user's key | Security incident response: admin must be able to kill any key without user cooperation | LOW | Add revoke action to admin key list. Extends existing admin user management patterns. |
| Last-used timestamp per key visible to admin | Identifies stale keys, dormant API integrations, or anomalous usage patterns | LOW | Populated on every successful API key auth request. Visible in admin view. |

#### Public REST API v1

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Bearer token auth via API key | Standard HTTP auth pattern for REST APIs. Developers expect `Authorization: Bearer {key}` | LOW | New auth dependency in FastAPI that validates API key, looks up user, checks revoked status, updates `last_used_at` |
| `/api/v1/` URL prefix | Signals versioning intent. Developers assume any production API is versioned. Absence feels like a red flag. | LOW | All API v1 routes under `/api/v1/`. Internal JWT routes remain at `/api/`. No naming conflict. |
| Consistent JSON response envelope | Predictable structure enables client code that doesn't inspect every endpoint's shape | LOW | Success: `{"data": {...}, "meta": {"request_id": "..."}}`. Error: `{"error": {"code": "...", "message": "..."}}` |
| Structured error responses | Machine-readable `code` + human-readable `message`. Required for client error handling and debugging. | LOW | Error codes should be screaming-snake: `FILE_NOT_FOUND`, `INSUFFICIENT_CREDITS`, `ANALYSIS_TIMEOUT`. Include `request_id` for support correlation. |
| `GET /api/v1/files` — list user files | Core discovery endpoint. Developers need to know what files are available before querying. | LOW | Reuse existing file listing service. New auth adapter. Returns: `id`, `name`, `size`, `upload_date`, `row_count` |
| `GET /api/v1/files/{id}/context` — get file profile | The AI-generated data profile is Spectra's highest-value zero-cost (pre-computed) response. Agents need this to form good queries. | LOW | Returns profiling summary, column names and types, row count, AI-generated natural language description. All computed at upload time. |
| `POST /api/v1/analysis` — submit query | The core product capability. Primary reason to use the API. | MEDIUM | Synchronous blocking; accepts `file_ids[]`, `query` string; invokes LangGraph pipeline; returns answer, optional table, optional chart spec. Credit deduction required. |
| Credit deduction on API queries | API access must respect the existing credit model. Developers should not be able to bypass billing by using the API instead of the web UI. | LOW | Reuse existing `SELECT FOR UPDATE` atomic deduction. Same credit cost as interactive queries. Return `INSUFFICIENT_CREDITS` error when balance is zero. |
| `GET /api/v1/me` — current user info | Developers need to verify auth is working and check their remaining credits | LOW | Returns: `user_id`, `email`, `tier`, `credits_remaining`. Simple read-only endpoint. |
| 429 Too Many Requests on credit exhaustion | Standard API error for resource exhaustion. Developers expect HTTP semantics. | LOW | Return 429 with `Retry-After` header when credits hit zero. Communicates "temporary" exhaustion vs. 403 "permanently forbidden". |
| OpenAPI docs at `/api/v1/docs` | Developers expect interactive documentation. FastAPI generates this automatically. | LOW | Zero marginal implementation cost. Set `docs_url="/api/v1/docs"` on the v1 APIRouter. Essential for developer adoption. |

#### MCP Server

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `tools/list` discovery | Core MCP protocol requirement. Any MCP host (Claude Desktop, Claude Code) issues `tools/list` on connect to enumerate capabilities. | LOW | Handled automatically by MCP SDK. Tool metadata is declared once in tool definitions. |
| `tools/call` execution | Core MCP execution primitive. How the LLM invokes a tool and receives results. | LOW | SDK handles JSON-RPC routing. Developer writes handler functions. |
| JSON Schema input definitions per tool | LLMs use the schema to generate valid tool arguments. Missing or vague schema causes bad argument generation. | LOW | Defined via Python type hints in `@mcp.tool()` decorators. SDK auto-generates JSON Schema from types. |
| Natural language tool descriptions | The LLM uses the `description` field to decide when and whether to call a tool. Vague descriptions cause wrong tool selection. | LOW | Critical quality gate: descriptions must be precise about what the tool does, when to use it, and what inputs mean. |
| Streamable HTTP transport | Required for remote MCP servers serving multiple clients. stdio transport is local-process only. | LOW | Official MCP Python SDK (`mcp` package, 1.8+) supports `streamable-http` transport natively. |
| API key auth passed from MCP client config | MCP server calls the REST API on behalf of a user. It needs the user's Spectra API key to authenticate. | LOW | User configures their API key in Claude Desktop's MCP server settings (env var or config param). MCP server reads it at startup and passes as `Authorization: Bearer` on all REST API calls. |

### Differentiators (Competitive Advantage)

Features beyond table stakes that create differentiated value for Spectra's AI-agent integration use case.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `spectra_list_files` MCP tool | Exposes file inventory to agents so they can discover what data is available before querying. Without this, agents must know file IDs out of band. | LOW | Maps directly to `GET /api/v1/files`. Returns rich metadata so the agent can select the right file. |
| `spectra_get_file_context` MCP tool | Exposes AI-generated data profile to agents. Agent reads column names, types, and data summary before forming queries — results in far more accurate analysis requests. | LOW | Maps to `GET /api/v1/files/{id}/context`. This is unique to Spectra: no other API would pre-compute and expose structured data profiles. |
| `spectra_run_analysis` MCP tool | Core capability: agent asks a natural language question about data and gets structured results back in the conversation. | MEDIUM | Maps to `POST /api/v1/analysis`. Returns answer text + table data + optional chart spec. The chart spec can be rendered by the agent or ignored. |
| `SPECTRA_MODE=api` deployment mode | Clean, dedicated API-serving backend with no web session overhead, no cookie routes, no WebSocket/SSE routes. Leaner process, easier to reason about. | LOW | Extends existing SPECTRA_MODE pattern (public / admin / dev). Disable interactive session endpoints. Enable API key auth as the only auth mechanism. |
| Key naming with descriptive labels | Developers give each key a name so they can tell keys apart ("Mobile app", "Zapier integration"). Without names, a list of prefixes is meaningless. | LOW | Already included in table stakes — called out here because the UX quality of the creation modal (descriptive placeholder text, validation) is where products differentiate. |
| `X-Credits-Remaining` response header | API consumers can track credit consumption per-request without polling `/api/v1/me`. Useful for automation pipelines that need to stay within budget. | LOW | Append remaining balance after deduction as a response header. One line of middleware. High UX value for zero implementation cost. |
| Scoped API keys (read vs. analysis) | Limits blast radius of a leaked key. Read-only keys can access files and context but cannot trigger analysis (credit consumption). Enterprise users expect least-privilege. | MEDIUM | v1: Start with no scopes (full access is the default). Add two scopes — `files:read` and `analysis:run` — in v1.x when first enterprise user requests it. Schema should accommodate `scopes` column from day one to avoid migration pain. |
| Key expiration / TTL | Enables short-lived keys for automation pipelines. Reduces stale key risk. Limits exposure window if a key is leaked. | LOW | Add `expires_at TIMESTAMPTZ NULL` column. NULL = no expiry. Check `expires_at < now()` in auth middleware. Expose in creation UI as optional field. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| SSE streaming on REST API | Developers used to interactive chat want streaming in the API too | Synchronous API design is far simpler to integrate, test, and document. SSE over HTTP adds client SDK complexity, server infrastructure complexity, and unclear benefit for the MCP use case where the tool call must complete before the LLM continues. | Synchronous blocking response. 30-60 second timeout is acceptable for data analysis. If individual queries regularly exceed 60s, the real fix is optimizing the pipeline, not adding streaming. |
| Per-key rate limiting independent of credits | "Proper API management" | Credits already serve as the consumption gate. Adding a separate rate limit layer doubles state to manage. At Spectra's current scale, credits are more meaningful than req/min limits. | Use credits as the primary consumption gate. Add a hard abuse-prevention limit (e.g., 120 req/min per key) only as an anti-abuse floor. |
| GraphQL API | Developers familiar with GraphQL ask for it | Spectra's operations (list files, run query, get context) are simple resource-oriented operations. GraphQL adds schema definition overhead, resolver complexity, and is harder for MCP to wrap than REST endpoints. | REST with a consistent JSON envelope covers all use cases at v1. |
| OAuth 2.0 for API access | "OAuth is the proper auth standard" | OAuth adds an authorization server, redirect flows, token exchange endpoints, scope consent screens, and refresh token management. API keys are sufficient and standard for programmatic/agent access. | API keys with optional scopes. Add OAuth when third-party app integrations (where delegated user consent is required) justify the infrastructure. |
| Webhook delivery | Useful for async notification patterns | Async delivery requires retry infrastructure, exponential backoff, signature verification (`X-Spectra-Signature`), dead-letter queues, and endpoint health monitoring. Not justified when a synchronous API covers the use case. | Synchronous API. If async becomes necessary, expose a job ID endpoint with polling — not webhooks. |
| File upload via API | Logical extension: if files can be listed, they should be uploadable | File upload adds multipart form handling, size limit enforcement, storage quota checks across API + web, onboarding agent async invocation, and response design (synchronous vs. async profiling). Significantly expands scope. v1 agents reference existing files by ID. | v1 API is read-only for files + analysis. Files uploaded via web UI. Agents are expected to work with pre-existing datasets. |
| SDK libraries (Python, JS, etc.) | Developers want convenience wrappers | SDKs require ongoing maintenance across API versions. The MCP server already provides the primary AI-agent integration point. OpenAPI spec enables auto-generation if needed. | Document curl examples and OpenAPI spec. Publish auto-generated SDKs (Speakeasy, OpenAPI Generator) only after stable API surface. |
| Multiple keys per key (key namespaces/groups) | Useful for org-level access management | Premature hierarchy. At current user scale, a flat list per user with descriptive names is sufficient. Namespaces add UI complexity for no user-visible benefit. | Flat list with descriptive names. Add grouping only when org-level billing and team access management are built. |

---

## Feature Dependencies

```
[API Key DB Table + CRUD Endpoints]
    └──required by──> [User Self-Service Key Management UI]
    └──required by──> [Admin Portal Key View + Revoke]
    └──required by──> [REST API v1 Auth Middleware]
                          └──required by──> [All REST API v1 Endpoints]
                                                └──required by──> [MCP Server Tools]

[Existing Credit System]
    └──must integrate with──> [POST /api/v1/analysis (credit deduction)]

[Existing File Management Service]
    └──re-exposed by──> [GET /api/v1/files]
    └──re-exposed by──> [GET /api/v1/files/{id}/context]

[Existing LangGraph Analysis Pipeline]
    └──re-exposed by──> [POST /api/v1/analysis]
                            └──wrapped by──> [spectra_run_analysis MCP tool]

[SPECTRA_MODE pattern (existing)]
    └──extended by──> [SPECTRA_MODE=api]

[Admin Portal User Management (existing)]
    └──extended by──> [Admin API Key View + Revoke UI]
```

### Dependency Notes

- **API keys must be built before REST API v1.** The REST API has no authentication without API key infrastructure. Build `api_keys` table, key generation, hashing, and auth middleware first.
- **REST API v1 must be built before MCP server.** The MCP server is a thin client that calls the REST API. It cannot exist without the API.
- **Credit system integration is mandatory on the analysis endpoint.** The LangGraph pipeline is the most expensive operation. Do not ship `POST /api/v1/analysis` without credit deduction using the existing atomic `SELECT FOR UPDATE` pattern.
- **`SPECTRA_MODE=api` is a deployment optimization, not a blocker.** The MCP server can call the existing public-mode backend. Deploy `api` mode after the rest is working.
- **Admin key management is a UI extension, not new infrastructure.** Add to the existing user management screen. No new tables, no new backend patterns needed.

---

## MVP Definition (v0.7)

### Launch With

- [ ] **`api_keys` table migration + CRUD endpoints** — Foundation for everything else; without this nothing works
- [ ] **User self-service key management UI screen** — Create (display-once modal), list (prefix + metadata), revoke
- [ ] **REST API v1 auth middleware** — Validate Bearer key, look up user, check revocation, update `last_used_at`
- [ ] **`GET /api/v1/files`** — List user's files; simplest endpoint; validates auth plumbing end-to-end
- [ ] **`GET /api/v1/files/{id}/context`** — Returns AI-generated profile; high value, zero new computation
- [ ] **`POST /api/v1/analysis`** — Synchronous query; core capability; must include credit deduction
- [ ] **`GET /api/v1/me`** — Current user info + credits; developer validation endpoint
- [ ] **Consistent JSON error format across all v1 routes** — Developers cannot use the API without predictable error responses
- [ ] **OpenAPI docs at `/api/v1/docs`** — Auto-generated by FastAPI; zero marginal cost; essential for developer adoption
- [ ] **MCP server with 3 core tools**: `spectra_list_files`, `spectra_get_file_context`, `spectra_run_analysis`
- [ ] **Admin portal key view + revoke** — Security requirement; extends existing user management screen
- [ ] **`SPECTRA_MODE=api` deployment mode** — 5th Dokploy service; clean API-only backend

### Add After Validation (v1.x)

- [ ] **API key scopes** (`files:read` and `analysis:run`) — Add when an enterprise user or paying customer requests least-privilege. Accommodate `scopes` column in DB schema from day one.
- [ ] **Key expiration / TTL** — Add when automation pipeline users request short-lived keys
- [ ] **`X-Credits-Remaining` response header** — Add when API users report difficulty tracking consumption. One line of middleware.
- [ ] **Per-key usage statistics** — Add when admin needs detailed API consumption analytics by user
- [ ] **MCP Resources primitive** — Expose uploaded files as MCP resources (not just tools) for richer agent context passing

### Future Consideration (v2+)

- [ ] **File upload via API** — Significantly expands scope; build when fully headless workflow demand is validated
- [ ] **Async analysis with job ID + polling** — Build when 30-60s synchronous timeout regularly hits users; requires a job queue
- [ ] **OAuth 2.0** — Build when third-party apps require user-consented delegated access
- [ ] **SDK libraries** — Auto-generate (Speakeasy, OpenAPI Generator) after stable API surface; maintain only if adoption justifies it
- [ ] **Webhooks** — Build when async event notification patterns are validated over polling

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `api_keys` table + CRUD endpoints | HIGH | LOW | P1 |
| User self-service key management UI | HIGH | LOW | P1 |
| REST API v1 auth middleware | HIGH | LOW | P1 |
| `GET /api/v1/files` | HIGH | LOW | P1 |
| `GET /api/v1/files/{id}/context` | HIGH | LOW | P1 |
| `POST /api/v1/analysis` + credit integration | HIGH | MEDIUM | P1 |
| `GET /api/v1/me` | MEDIUM | LOW | P1 |
| Consistent error format for v1 | HIGH | LOW | P1 |
| OpenAPI docs at `/api/v1/docs` | HIGH | LOW | P1 — auto-generated |
| MCP server: 3 core tools | HIGH | LOW | P1 |
| Admin key view + revoke | MEDIUM | LOW | P1 |
| `SPECTRA_MODE=api` | MEDIUM | LOW | P1 |
| `X-Credits-Remaining` header | MEDIUM | LOW | P2 |
| API key scopes | MEDIUM | MEDIUM | P2 |
| Key expiration / TTL | LOW | LOW | P2 |
| Per-key usage stats | LOW | MEDIUM | P3 |
| File upload via API | MEDIUM | HIGH | P3 |
| OAuth 2.0 | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for v0.7 launch
- P2: Add after v0.7 ships, when first user requests it
- P3: Future milestone, defer until demand is validated

---

## Implementation Notes by Feature

### API Key Security Model

**Key generation and storage pattern** (HIGH confidence — verified against freeCodeCamp best practices, AppMaster UX guide, and multiple authoritative sources):

- **Format:** `sk-spectra-{url_safe_base64_random_32_bytes}` — recognizable namespace prefix, hard to guess
- **Storage:** Store only `prefix` (first 16 chars, plaintext for display) + `key_hash` (SHA-256 of full key, hex). Never store the raw key.
- **Auth lookup:** Hash incoming Bearer token, query `WHERE key_hash = $1 AND revoked_at IS NULL`. O(1), index on `key_hash`.
- **Display:** Return full key in API creation response only. Never again. Frontend shows modal with copy button.

**Minimum DB schema:**
```sql
CREATE TABLE api_keys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,              -- "CI pipeline prod"
    prefix      TEXT NOT NULL,              -- "sk-spectra-abc12" (16 chars)
    key_hash    TEXT NOT NULL UNIQUE,       -- SHA-256 hex of full key
    scopes      TEXT[] DEFAULT '{}',        -- empty = full access; future: ["files:read", "analysis:run"]
    expires_at  TIMESTAMPTZ,               -- NULL = no expiry
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at TIMESTAMPTZ,              -- updated on every successful auth
    revoked_at  TIMESTAMPTZ                -- NULL = active; set = revoked (soft delete for audit)
);
CREATE INDEX ON api_keys (key_hash);
CREATE INDEX ON api_keys (user_id);
```

### REST API v1 Endpoint Design

**URL conventions:**
```
GET  /api/v1/me                          — current user + credits
GET  /api/v1/files                       — list files (paginated)
GET  /api/v1/files/{file_id}             — file metadata
GET  /api/v1/files/{file_id}/context     — AI-generated data profile
POST /api/v1/analysis                    — submit synchronous query
```

**Auth header:** `Authorization: Bearer sk-spectra-{key}`

**Error envelope (machine-readable):**
```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "No file found with ID abc123 for this user",
    "request_id": "req_01HABCXYZ"
  }
}
```

**Success envelope:**
```json
{
  "data": { ... },
  "meta": { "request_id": "req_01HABCXYZ" }
}
```

**Analysis request:**
```json
{
  "file_ids": ["uuid-1", "uuid-2"],
  "query": "What is the average revenue by region?"
}
```

**Analysis response** (synchronous blocking; 60s timeout):
```json
{
  "data": {
    "answer": "Average revenue by region: North $1.2M, South $890K...",
    "table": {
      "columns": ["region", "avg_revenue"],
      "rows": [["North", 1200000], ["South", 890000]]
    },
    "chart": {
      "type": "bar",
      "plotly_spec": { "data": [...], "layout": {...} }
    },
    "code": "import pandas as pd\n..."
  },
  "meta": { "request_id": "req_01HABCXYZ", "credits_used": 1.0 }
}
```

### MCP Server Tool Definitions

**Transport:** Streamable HTTP (not stdio) — required for multi-user remote deployment

**Authentication:** User configures their Spectra API key as an environment variable in Claude Desktop's MCP server configuration. MCP server reads it at startup and passes as `Authorization: Bearer {key}` on all outbound calls to the REST API.

**Implementation approach:** Use the official `mcp` Python SDK (`pip install mcp`) with `@mcp.tool()` decorators wrapping `httpx.AsyncClient` calls to the REST API. The `fastapi-mcp` library is an alternative that auto-converts FastAPI OpenAPI routes to tools via ASGI, but the explicit `httpx` approach is preferred for `SPECTRA_MODE=api` where MCP server is a separate process.

**Three tools for v0.7:**

```python
@mcp.tool()
async def spectra_list_files() -> list[dict]:
    """
    List all data files the user has uploaded to Spectra.
    Returns file IDs, names, sizes, upload dates, and row counts.
    Use this first to discover what data is available before running analysis.
    If you already know the file ID, you can skip this step.
    """
    # calls GET /api/v1/files

@mcp.tool()
async def spectra_get_file_context(file_id: str) -> dict:
    """
    Get the AI-generated data profile for a specific Spectra file.
    Returns column names, data types, row count, and a natural language
    summary of the dataset's structure and content.
    Use this before running analysis to understand what questions are
    answerable and how to phrase them accurately.
    """
    # calls GET /api/v1/files/{file_id}/context

@mcp.tool()
async def spectra_run_analysis(
    file_ids: list[str],
    query: str
) -> dict:
    """
    Run a natural language data analysis query against one or more Spectra files.
    Returns a text answer, optional structured data table, and optional Plotly
    chart specification. Deducts credits per query.

    file_ids: One or more file IDs from spectra_list_files to analyze.
    query: A natural language question about the data (e.g., "What is the
           average revenue by region?" or "Show me the top 10 customers by spend").
    """
    # calls POST /api/v1/analysis
```

**Tool naming rationale:** `spectra_{resource}_{action}` matches MCP best-practice `namespace_verb` convention. Avoids generic names like `query` or `search` that conflict with other MCP tools in the same client.

---

## Competitor Feature Analysis

| Feature | Stripe API | OpenAI API | Perplexity API | Spectra v0.7 Approach |
|---------|------------|------------|----------------|------------------------|
| Key creation UX | Name + type (test/live), display once, copy button | Name only, display once, copy button | Simple create, display once | Name required, display once, copy button with warning, prefix shown in list |
| Key list metadata | Name, type, created, last used, prefix | Name, created, last used | Name, created | Name, prefix, created, last used, status |
| Key revocation | Immediate, confirmation required | Immediate | Immediate | Immediate, soft delete (revoked_at timestamp) for audit |
| Key scopes | Restricted keys with fine-grained resource permissions | Full access only at key level | Full access | v1: full access; v1.x: `files:read` + `analysis:run` scopes |
| Admin key visibility | Yes, organization dashboard | Yes, organization settings | N/A | Yes, in existing admin portal user detail view |
| API versioning | Header (`Stripe-Version`) | URL (`/v1/`) | URL (`/v1/`) | URL (`/api/v1/`) — FastAPI router prefix |
| Error format | `{"error": {"type": ..., "code": ..., "message": ...}}` | `{"error": {"message": ..., "type": ..., "code": ...}}` | `{"detail": ...}` | `{"error": {"code": ..., "message": ..., "request_id": ...}}` |
| Interactive API docs | No (handwritten) | No (handwritten) | No | Yes — FastAPI Swagger UI auto-generated at `/api/v1/docs` |
| MCP server | Yes (Stripe MCP, official) | Yes (OpenAI tools for agents) | No | Yes — 3 core tools wrapping REST API |

---

## Sources

- [MCP Architecture Overview — modelcontextprotocol.io](https://modelcontextprotocol.io/docs/learn/architecture) — HIGH confidence; official Anthropic documentation, verified June 2025 spec
- [API Key Rotation UX: Scopes, Self-Serve Keys, and Logs — AppMaster](https://appmaster.io/blog/api-key-rotation-scoping-ux) — MEDIUM confidence; aligns with industry patterns observed across Stripe, OpenAI, and other major APIs
- [Best Practices for Building Secure API Keys — freeCodeCamp](https://www.freecodecamp.org/news/best-practices-for-building-api-keys-97c26eabfea9/) — HIGH confidence; widely cited, consistent with multiple authoritative sources
- [API Keys: The Complete 2025 Guide — DEV Community](https://dev.to/hamd_writer_8c77d9c88c188/api-keys-the-complete-2025-guide-to-security-management-and-best-practices-3980) — MEDIUM confidence
- [REST API Best Practices — Postman Blog](https://blog.postman.com/rest-api-best-practices/) — HIGH confidence; authoritative source, current
- [Rate Limiting Best Practices in REST API Design — Speakeasy](https://www.speakeasy.com/api-design/rate-limiting) — MEDIUM confidence
- [fastapi-mcp — GitHub (tadata-org)](https://github.com/tadata-org/fastapi_mcp) — HIGH confidence; active maintained library
- [fastmcp / MCP Python SDK — PyPI](https://pypi.org/project/fastmcp/2.2.6/) — HIGH confidence; official SDK
- [RESTful API Best Practices 2025 — Hevo](https://hevodata.com/learn/rest-api-best-practices/) — MEDIUM confidence

---

*Feature research for: Spectra v0.7 API Services and MCP*
*Researched: 2026-02-23*
