# Pitfalls Research: API Services & MCP (v0.7)

**Domain:** Adding API key auth, public REST API v1, and MCP server to an existing FastAPI app with JWT auth, credit deduction, and LangGraph AI agents
**Researched:** 2026-02-23
**Confidence:** HIGH for auth/security pitfalls (official docs + community evidence); MEDIUM for MCP-specific pitfalls (newer ecosystem, evolving SDK)

**Context:** Spectra v0.7 adds three interdependent features to an existing production codebase: (1) API key management for programmatic access, (2) a public REST API v1 exposing file management and synchronous AI analysis, and (3) an MCP server wrapping those endpoints as tools. The existing system uses Argon2-hashed passwords, JWT bearer tokens, an in-memory revocation set, SELECT FOR UPDATE credit deduction, SPECTRA_MODE routing, and LangGraph async agents invoked via `graph.ainvoke()` / `graph.astream()`.

---

## Critical Pitfalls

Mistakes at this level cause security breaches, broken credit accounting, or a rewrite of the auth layer.

### Pitfall 1: Storing the Full API Key in the Database

**What goes wrong:**
The raw API key (e.g., `sk_live_AbCdEfGhIj...`) is saved as plaintext or reversibly encrypted in the `api_keys` table. A database dump, a misconfigured S3 backup, or a SQL injection attack exposes all API keys immediately — every customer's programmatic access is compromised at once.

**Why it happens:**
Developers know they need to "store a key," copy the UUIDs-in-database pattern from session tokens, and miss that API keys need the same treatment as passwords: one-way hashing.

**How to avoid:**
At creation time, generate a high-entropy key, return it to the user **once**, and store only the SHA-256 hash plus a short prefix (first 8 characters) for lookup. Use `secrets.token_urlsafe(32)` for generation (256 bits of entropy — SHA-256 of a high-entropy source is computationally impossible to reverse). Store `key_hash = hashlib.sha256(raw_key.encode()).hexdigest()` and index on it. Never store the raw key again. If a user loses the key, revoke and regenerate.

```python
import hashlib, secrets

raw_key = f"sk_{secrets.token_urlsafe(32)}"
key_prefix = raw_key[:8]          # shown in UI for identification
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
# Store key_prefix + key_hash; return raw_key to user once
```

**Warning signs:**
- `api_key` column is `String(255)` without an adjacent `_hash` suffix in the model
- Unit tests assert `db_record.api_key == raw_key_from_response`

**Phase to address:** API key management schema and creation endpoint (Phase 1 of v0.7)

---

### Pitfall 2: Using Argon2/bcrypt to Hash API Keys (Wrong Hash for This Use Case)

**What goes wrong:**
The existing `security.py` uses `pwdlib`'s `PasswordHash.recommended()` (Argon2). A developer reaches for the same utility to hash API keys. Argon2 is intentionally slow (memory-hard) — API key verification happens on every request, so hashing at Argon2 cost adds 100–400ms per API call. Under load, this destroys throughput.

**Why it happens:**
Argon2 is correctly the right choice for passwords (human-memorized, low-entropy, brute-forceable). API keys have 256 bits of entropy — brute-forcing is computationally impossible regardless of hash speed. The threat model is a database breach, not brute-force, so a fast cryptographic hash (SHA-256) is the correct tool.

**How to avoid:**
Use `hashlib.sha256()` for API key hashing — no salt needed because the key already has sufficient entropy. Reserve Argon2 for the password column. Put a comment in `security.py` documenting the distinction so future developers do not "fix" it.

**Warning signs:**
- `hash_api_key()` calls `password_hash.hash()` from the existing pwdlib instance
- API key auth endpoints take 200ms+ in profiling

**Phase to address:** API key hashing utility (Phase 1 of v0.7, before first auth integration test)

---

### Pitfall 3: Breaking the Existing `get_current_user` Dependency for JWT Endpoints

**What goes wrong:**
The new API-key dependency is wired into existing JWT-protected endpoints by modifying `get_current_user` to accept either auth method. This works for the happy path but breaks existing JWT flows in subtle ways: the `OAuth2PasswordBearer` scheme still marks the Authorization header as required in OpenAPI, so new API key routes show the wrong security scheme in docs; or the combined dependency raises a 401 for requests that send only `X-API-Key` because `OAuth2PasswordBearer` throws before the key check runs.

**Why it happens:**
The impulse to "unify" auth into a single dependency function is natural, but FastAPI's `OAuth2PasswordBearer` scheme makes the Bearer header required at the scheme level. Trying to make it optional to support API keys breaks the scheme declaration.

**How to avoid:**
Keep two completely separate dependency functions — `get_current_user` (JWT only, unchanged) and `get_api_key_user` (API key only). Create a third optional combinator only for endpoints that must accept both, using `Optional` headers and explicit fallback logic. New `/api/v1/` routes use `get_api_key_user` exclusively. Existing routes keep `CurrentUser` (JWT). No modification of `dependencies.py` existing functions.

```python
# New file: app/dependencies_api.py
async def get_api_key_user(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: DbSession = ...,
) -> User:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    # lookup by sha256 hash
    ...
```

**Warning signs:**
- Modifying `get_current_user` signature to add an `Optional` API key parameter
- Existing `/chat/` or `/files/` tests start failing after API key code is merged

**Phase to address:** Dependency layer design at the start of the public REST API phase (before writing any v1 endpoint)

---

### Pitfall 4: API Key Auth Bypassing Credit Deduction

**What goes wrong:**
New `/api/v1/query` endpoints call `run_chat_query` but omit the `_deduct_credits_or_raise` step that the existing `/chat/sessions/{id}/query` endpoint calls. API key users can run unlimited queries without credit deduction.

**Why it happens:**
The credit deduction logic in `chat.py` is embedded inline in each router function rather than being a dependency. When a new router (`api_v1.py`) calls the same underlying service function (`agent_service.run_chat_query`), the developer focuses on the agent call and forgets to replicate the credit guard.

**How to avoid:**
Extract `_deduct_credits_or_raise` into `app/dependencies_api.py` as a proper FastAPI dependency so it is impossible to add a new query endpoint without explicitly handling credits. Alternatively, move credit deduction into `agent_service.run_chat_query` itself so it always fires — but this couples the service to the HTTP layer, which has tradeoffs.

```python
# Make it a reusable dependency, not a private helper
async def require_credits(
    current_user: User,
    db: AsyncSession,
) -> None:
    await _deduct_credits_or_raise(db, current_user.id)
```

**Warning signs:**
- `api_v1.py` query endpoint calls `agent_service.run_chat_query` without a credit check above it
- Integration test: create a free-tier user with 0 credits, call `/api/v1/query`, expect 402 — actually gets 200

**Phase to address:** Public REST API v1 query endpoint implementation

---

### Pitfall 5: Timing Attack Vulnerability in API Key Comparison

**What goes wrong:**
The database lookup returns the stored `key_hash`, and the comparison is `stored_hash == hashlib.sha256(provided_key).hexdigest()` using Python's `==` operator. Python's string `==` short-circuits on the first differing character, leaking timing information that an attacker with sufficient request volume can exploit to enumerate valid key hash prefixes.

**Why it happens:**
Developers know to hash the key but overlook the comparison step. SHA-256 hashes are 64 hex characters, and timing differences of nanoseconds are measurable with `time.perf_counter_ns()` across many samples.

**How to avoid:**
Use `hmac.compare_digest(stored_hash, computed_hash)` for all API key comparisons. This is constant-time regardless of where the strings differ.

```python
import hmac, hashlib

def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    computed = hashlib.sha256(raw_key.encode()).hexdigest()
    return hmac.compare_digest(computed, stored_hash)
```

**Warning signs:**
- Key verification code uses `==` or `!=` to compare hash strings
- No import of `hmac` in the auth/security module

**Phase to address:** API key verification utility, same commit as hashing utility

---

### Pitfall 6: Wrapping `graph.ainvoke()` with `asyncio.run()` Inside a Synchronous REST Endpoint

**What goes wrong:**
The MCP server or a synchronous REST endpoint tries to call the async LangGraph agent with `asyncio.run(agent_service.run_chat_query(...))`. This raises `RuntimeError: This event loop is already running` because FastAPI/uvicorn runs inside an existing asyncio event loop, and `asyncio.run()` cannot nest inside a running loop.

**Why it happens:**
The MCP server's tool functions may be defined as synchronous (def, not async def), because the developer follows an example that uses synchronous tool definitions. When the tool body tries to call an async function, `asyncio.run()` seems like the obvious bridge. It works in a script but fails in ASGI context.

**How to avoid:**
Define all MCP tool functions as `async def` — both the official MCP Python SDK and FastMCP support async tool handlers. Inside an async tool, `await agent_service.run_chat_query(...)` works directly without any bridge. If a synchronous context truly cannot be avoided (rare), use `asyncio.get_event_loop().run_until_complete()` with a thread pool, but this is fragile and should be avoided.

```python
# Correct: async MCP tool
@mcp.tool()
async def query_data(session_id: str, question: str) -> str:
    result = await agent_service.run_chat_query(...)
    return result["analysis"]

# Wrong: sync tool with asyncio.run()
@mcp.tool()
def query_data(session_id: str, question: str) -> str:
    result = asyncio.run(agent_service.run_chat_query(...))  # RuntimeError
    return result["analysis"]
```

**Warning signs:**
- MCP tool functions are defined as `def` (not `async def`) and call async services
- `import nest_asyncio` appears in MCP server code (a red flag — this is a patch, not a solution)
- `RuntimeError: This event loop is already running` in MCP server logs

**Phase to address:** MCP server tool definition (Phase: MCP server implementation)

---

### Pitfall 7: MCP Stdio Transport Polluting the Protocol with Log Output

**What goes wrong:**
When the MCP server runs in stdio transport mode (for Claude Desktop integration), any `print()`, `logging.StreamHandler` pointing to stdout, or stray debug output corrupts the JSON-RPC framing. MCP protocol messages are delimited by newlines on stdout; an extra line causes the client to try to parse a log message as JSON-RPC and fail with a protocol error, often silently disconnecting.

**Why it happens:**
The existing backend uses `logging` with a StreamHandler writing to stdout (standard uvicorn behavior). When MCP server code is imported or run as a subprocess, it inherits these log handlers. The developer sees it working in HTTP transport mode (where stdout is not the protocol channel) and misses the stdio failure mode.

**How to avoid:**
For stdio transport, reconfigure logging to write exclusively to stderr before starting the MCP server. The official Python SDK and FastMCP both document this requirement. If sharing code with the HTTP backend, gate the logging reconfiguration on a `SPECTRA_MODE=mcp` check.

```python
import logging, sys

if os.getenv("SPECTRA_MODE") == "mcp":
    # Redirect ALL log output to stderr — stdout is the protocol channel
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
```

**Warning signs:**
- Claude Desktop shows "server disconnected" or "protocol error" immediately on tool call
- MCP Inspector shows parse errors on messages that look like log lines
- The MCP server works in HTTP/SSE mode but not stdio mode

**Phase to address:** MCP server transport configuration (Phase: MCP server implementation)

---

### Pitfall 8: SSE Transport for MCP Instead of Streamable HTTP

**What goes wrong:**
The MCP server is deployed using SSE transport (`/sse` endpoint) because SSE is familiar from the existing streaming chat implementation. The MCP Python SDK marked SSE transport as deprecated in favor of Streamable HTTP. New MCP clients (Claude.ai, future versions of Claude Desktop) may drop SSE support, causing the integration to silently break after an SDK update.

**Why it happens:**
SSE is well-understood from v0.4 chat streaming. The name "SSE" appears in MCP documentation examples for historical reasons, and developers reaching for familiar patterns miss the deprecation notice.

**How to avoid:**
Use Streamable HTTP transport (the new default in MCP Python SDK 1.x). For FastMCP, the default `mcp.run()` uses Streamable HTTP. Only use stdio for local Claude Desktop development where HTTP is unavailable.

**Warning signs:**
- MCP server code mounts a `/sse` endpoint as the primary transport
- FastMCP or SDK version warnings about SSE deprecation in startup logs
- MCP Inspector shows SSE-specific warnings

**Phase to address:** MCP server transport configuration (Phase: MCP server implementation)

---

### Pitfall 9: MCP Global State Leaking Between Concurrent Users

**What goes wrong:**
MCP tool functions use module-level variables to track state between calls (e.g., `current_user_id = None` set at the start of each request). With concurrent AI agent clients, user A's request overwrites the global before user B's tool reads it, causing user B's tool to operate on user A's data.

**Why it happens:**
Single-threaded scripting habits — "just use a global" — do not translate to concurrent ASGI servers. The MCP server runs in the same async event loop as the FastAPI app, so concurrent requests share module state.

**How to avoid:**
Never use module-level mutable state in MCP tool functions. Pass all context through tool arguments (session IDs, API keys) and resolve them per-call via database lookup. The API key in the tool call header identifies the user — look it up fresh on each invocation.

**Warning signs:**
- `global current_user` or `global session_context` in MCP tool file
- Integration test: two concurrent tool calls return swapped results

**Phase to address:** MCP server tool implementation (Phase: MCP server)

---

### Pitfall 10: API Key Not Scoped to SPECTRA_MODE=api, Accepted by Public/Admin Modes

**What goes wrong:**
The API key auth dependency is added to the shared FastAPI app without mode-gating. The public frontend's backend (`SPECTRA_MODE=public`) starts accepting API key requests to endpoints that were never designed for programmatic access (e.g., SSE streaming chat, admin routes). API key holders can discover and call internal endpoints not intended for the public API.

**Why it happens:**
The same FastAPI app object handles all modes (public/admin/api/dev). Adding an API key dependency at the router level without mode-awareness means it is active in all modes.

**How to avoid:**
The `/api/v1/` router should only be included in the app when `SPECTRA_MODE=api`. The existing `main.py` already conditionally includes routers based on mode — apply the same pattern. The API key dependency itself can also check `SPECTRA_MODE` and reject requests in wrong modes.

```python
# main.py pattern (already exists for admin routes)
if settings.spectra_mode in ("api", "dev"):
    app.include_router(api_v1_router)
```

**Warning signs:**
- `app.include_router(api_v1_router)` is unconditional in `main.py`
- Smoke test: call `GET /api/v1/files` against the public-mode backend — should return 404, actually returns 200

**Phase to address:** SPECTRA_MODE=api deployment mode and router registration

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Storing API key prefix only for lookup (no hash) | Faster lookup, simpler code | Prefix collisions or enumeration attacks if prefix is too short | Never — always store hash |
| Using `asyncio.run()` with `nest_asyncio` for sync-to-async bridge | Avoids async def in MCP tools | Protocol-level failures in stdio, masks real concurrency bugs | Never in production ASGI |
| Embedding credit check inline in each endpoint | Copy-paste is fast | New endpoints silently skip credits | Only for the first endpoint; extract to dependency immediately |
| Using SSE transport for MCP instead of Streamable HTTP | Familiar from existing SSE code | Deprecated, will break with future SDK updates | Only for local Claude Desktop dev, never for deployed service |
| Sharing the LangGraph checkpointer between JWT sessions and API key sessions | No code change | API key users inherit session memory from web users if thread_id is reused | Never — use distinct thread_id namespaces |

---

## Integration Gotchas

Common mistakes when connecting these new features to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| API key → existing credit system | Calling `agent_service.run_chat_query` without credit deduction | Add credit check as a FastAPI dependency on all v1 query endpoints |
| API key → existing auth dependency | Modifying `get_current_user` to accept API keys | Create separate `get_api_key_user` dependency; do not touch existing JWT dependency |
| MCP tools → LangGraph agents | Using `asyncio.run()` inside sync tool functions | Define MCP tools as `async def`; use `await` directly |
| LangGraph checkpointer → API sessions | Reusing `session_{id}_user_{id}` thread_id format | Use a distinct namespace: `api_{api_key_id}_session_{session_id}` |
| MCP server → SPECTRA_MODE routing | Mounting MCP on main app unconditionally | Only include MCP routes when `SPECTRA_MODE=api` or `dev` |
| API key → deactivated user check | Only checking DB `is_active` on key lookup | Also check `is_user_deactivated()` in-memory revocation set (same as JWT path) |
| API v1 → existing file endpoints | Reusing existing `/files/` routes that return SSE-streaming responses | Build sync non-streaming variants for API v1; SSE is incompatible with MCP tool calls |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| SHA-256 lookup without DB index on `key_hash` | API auth adds 50–500ms at load | Index `api_keys.key_hash` at migration time | At ~100 req/s |
| No rate limiting on API key endpoints | Single key exhausts E2B sandbox quota | Add per-key rate limiting (e.g., 10 req/min) at FastAPI middleware level | At first abuse attempt |
| LangGraph `run_chat_query` called synchronously from MCP tool without timeout | Tool call hangs indefinitely waiting for agent | Wrap `ainvoke` with `asyncio.wait_for(..., timeout=120)` | First complex query with agent retry |
| Creating new `async_session_maker()` for every API key lookup | DB connection pool exhaustion | Reuse the existing `get_db()` dependency; create new sessions only where the existing stream pattern already does | At ~50 concurrent API requests |
| MCP tool returning full `execution_result` (potentially MB of data) | LLM context window exhausted, slow tool responses | Truncate or summarize execution results in MCP tool response | First large DataFrame analysis |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Returning the full API key in list/detail responses | Key exposure in logs, browser history, monitoring tools | Never return the full key after creation; return only prefix + metadata |
| API key with no expiry and no revocation UI | Compromised key is permanent | Implement `expires_at` (nullable) + soft-delete revocation from day one |
| Accepting API key in query string (`?api_key=...`) | Key appears in server access logs, nginx logs, browser history | Accept only via `X-API-Key` header or `Authorization: Bearer` — never query string |
| No `is_active` gate on API key lookup | Deactivated users retain API access | The API key lookup must check both `api_key.is_active` AND `user.is_active` |
| Admin can see other users' API keys (even hashed) | Information disclosure, enumeration | Admin API should list keys by user but never show hash; only show prefix + metadata |
| MCP tool does not validate session ownership | API key holder accesses another user's session | Every tool call resolves the user from the API key and asserts session.user_id matches |

---

## UX Pitfalls

API developer experience mistakes that frustrate integrators.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No key prefix visible in UI after creation | User cannot identify which key to revoke | Store and display 8-char prefix (e.g., `sk_AbCdEfGh...`) always visible in key list |
| Synchronous query endpoint returns immediately with partial result | API consumers build retry logic, polling | Return complete result synchronously; if agent takes >30s, return 504 with Retry-After |
| MCP tool error messages contain raw Python exceptions | LLM gets confused by stack traces | Catch all exceptions in tool functions; return structured error strings the LLM can reason about |
| API v1 uses different field names than the existing internal API | Consumers cannot reuse client code | Keep field names consistent (e.g., `session_id`, `file_id`, `analysis`) |
| No `request_id` in API responses | Debugging customer issues requires log diving | Include `X-Request-ID` header in all API v1 responses |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **API key creation:** Returns the raw key to the user — verify it is shown exactly once, then never again (not stored, not in list endpoint)
- [ ] **API key auth:** Verify the in-memory revocation set (`is_user_deactivated()`) is also checked, not just DB `is_active`
- [ ] **Credit deduction:** Confirm a free-tier user with 0 credits calling `/api/v1/query` gets HTTP 402 — not 200
- [ ] **Mode gating:** Confirm `/api/v1/` routes return 404 when the backend runs as `SPECTRA_MODE=public` or `SPECTRA_MODE=admin`
- [ ] **MCP stdio transport:** Confirm no stdout log output — only stderr — by running `SPECTRA_MODE=mcp python -m app.mcp_server` and checking stdout contains only valid JSON-RPC
- [ ] **MCP tool auth:** Confirm MCP tool call with invalid/expired API key returns a clear error, not a 500 traceback
- [ ] **Timing safety:** Confirm API key comparison uses `hmac.compare_digest`, not `==`
- [ ] **Thread ID namespace:** Confirm API key sessions use a different thread_id prefix than web JWT sessions (no cross-contamination of LangGraph checkpoints)

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Raw API keys stored in DB (discovered post-ship) | HIGH | Force-rotate all keys (delete + regenerate); notify all affected users; implement hashing before re-issue |
| Argon2 used for API key hashing (performance issue) | MEDIUM | Add `key_hash_sha256` column; backfill by... wait, you can't — raw keys are not stored. Force-rotate all keys with new SHA-256 hash |
| Credit deduction missing on v1 query endpoint | MEDIUM | Add missing credit check; audit logs to identify free-ride queries; optionally deduct retroactively from transaction log |
| MCP stdio broken by log output | LOW | Reconfigure logging to stderr in `SPECTRA_MODE=mcp` entrypoint; no data migration needed |
| Thread ID collision between JWT and API sessions | MEDIUM | Update thread_id generation to use distinct prefix; existing checkpoints remain but are namespaced differently going forward |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Raw API key stored in DB | Phase: API key management (schema + creation endpoint) | Test: `db.query(ApiKey).first().key_hash` is a 64-char hex string; no `raw_key` column exists |
| Argon2 used for API key hashing | Phase: API key hashing utility | Test: benchmark `verify_api_key()` — should complete in <1ms |
| Breaking existing `get_current_user` | Phase: dependency layer design | Test: all existing JWT-protected endpoint tests still pass after API key dependency is added |
| Credit deduction bypass | Phase: public REST API v1 query endpoint | Test: free-tier user with 0 credits, call `/api/v1/query`, expect HTTP 402 |
| Timing attack on key comparison | Phase: API key verification utility | Code review: `hmac.compare_digest` used, not `==` |
| `asyncio.run()` in MCP tools | Phase: MCP server tool implementation | Test: call MCP tool from running uvicorn process — no RuntimeError |
| MCP stdout log pollution (stdio) | Phase: MCP server transport config | Test: `SPECTRA_MODE=mcp` startup, parse all stdout lines as JSON-RPC — 0 parse errors |
| SSE transport (deprecated) | Phase: MCP server transport config | Code review: no `/sse` endpoint; Streamable HTTP used |
| MCP global state leakage | Phase: MCP server tool implementation | Test: two concurrent MCP tool calls with different API keys return correct per-user data |
| Mode gating for API routes | Phase: SPECTRA_MODE=api deployment | Test: `/api/v1/files` against `SPECTRA_MODE=public` returns 404 |

---

## Sources

- [Best practices for building API keys — freeCodeCamp](https://www.freecodecamp.org/news/best-practices-for-building-api-keys-97c26eabfea9/)
- [API Key Management Best Practices 2026 — OneUptime](https://oneuptime.com/blog/post/2026-02-20-api-key-management-best-practices/view)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [bcrypt Performance Issues vs SHA-256 for API keys — CyberSierra](https://cybersierra.co/blog/bcrypt-performance-issues-api/)
- [Implementing MCP: Tips, Tricks and Pitfalls — Nearform](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [MCP Server Transports: STDIO, Streamable HTTP & SSE — Roo Code](https://docs.roocode.com/features/mcp/server-transports)
- [FastMCP Running Your Server — gofastmcp.com](https://gofastmcp.com/deployment/running-server)
- [LangGraph .ainvoke() breaks ASGI async context — LangChain Forum](https://forum.langchain.com/t/langgraph-ainvoke-breaks-asgi-async-context/99)
- [Timing Attacks in Python — securitypitfalls.wordpress.com](https://securitypitfalls.wordpress.com/2018/08/03/constant-time-compare-in-python/)
- [FastAPI auth with dependency injection — PropelAuth](https://www.propelauth.com/post/fastapi-auth-with-dependency-injection)
- [FastAPI-MCP: Expose FastAPI endpoints as MCP tools — GitHub tadata-org](https://github.com/tadata-org/fastapi_mcp)
- [MCP Python SDK official — GitHub modelcontextprotocol](https://github.com/modelcontextprotocol/python-sdk)
- Spectra codebase: `backend/app/dependencies.py`, `backend/app/utils/security.py`, `backend/app/services/agent_service.py`, `backend/app/services/credit.py`, `backend/app/routers/chat.py`

---
*Pitfalls research for: Spectra v0.7 — API key management, public REST API v1, MCP server*
*Researched: 2026-02-23*
