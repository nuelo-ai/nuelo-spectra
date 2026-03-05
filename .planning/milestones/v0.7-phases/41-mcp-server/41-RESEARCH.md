# Phase 41: MCP Server - Research

**Researched:** 2026-02-24
**Domain:** MCP (Model Context Protocol) server integration with existing FastAPI backend
**Confidence:** HIGH

## Summary

Phase 41 adds a production-ready MCP server to the existing Spectra FastAPI backend, exposing file management and AI analysis capabilities as curated MCP tools. The MCP server mounts as an ASGI sub-application at `/mcp/` on the existing backend, uses Streamable HTTP transport, and authenticates via the Phase 38 API key infrastructure (Bearer token in Authorization header). All tool calls route through the existing REST API v1 endpoints internally, ensuring credit deduction, usage logging, and auth remain consistent.

The implementation uses `fastmcp>=3.0.2` (the de facto Python MCP framework, released 2026-02-22). FastMCP provides the `@mcp.tool` decorator for curated tool definitions, middleware for per-request auth validation, `get_http_headers()` for extracting Bearer tokens inside tools, and `combine_lifespans` for merging the MCP server lifecycle with the existing FastAPI lifespan. The MCP server defines 6 tools with `spectra_` prefix, all calling the REST API v1 endpoints via httpx loopback to preserve the existing auth/credit/logging middleware chain.

**Primary recommendation:** Use `fastmcp>=3.0.2` with manually curated tools (not `from_fastapi()` auto-generation), custom auth middleware extracting Bearer tokens via `get_http_headers()`, and `combine_lifespans` for lifecycle coordination. Mount at `/mcp/` in `api` and `dev` modes only.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- All tools use `spectra_` prefix for clear namespace identification across multi-server setups (e.g., `spectra_upload_file`, `spectra_run_analysis`)
- Rich descriptions for core tools (`spectra_upload_file`, `spectra_run_analysis`, `spectra_get_context`) where the LLM needs guidance on when/how to use them; concise one-liner descriptions for simple CRUD tools (`spectra_list_files`, `spectra_delete_file`, `spectra_download_file`)
- Minimal parameters only — expose essentials (file path, question text, file ID). No optional power-user params. Power users use the REST API directly. AI agents work best with simple tool signatures.
- Use typed MCP content blocks (text, image, resource) to preserve semantic distinction between output types — narrative analysis, generated code, chart specifications, and data tables must be distinguishable by the consuming AI agent
- Wait for completion on long-running operations (file upload + onboarding, complex analysis) — no polling pattern. Single tool call returns the full result. MCP hosts handle long-running tool calls natively.
- ASGI sub-mount on the existing FastAPI backend application
- Streamable HTTP transport only — no stdio. Both local dev (`http://localhost:3000/mcp/`) and production (`https://<domain>/mcp/`) use the same transport
- Mounted at `/mcp/` path — clearly separate from REST API at `/api/v1/`
- Always active in dev mode (SPECTRA_MODE=dev) alongside existing backend routes — no mode switching needed for local MCP testing with Claude Desktop
- Bearer token in Authorization header — reuses Phase 38 API key infrastructure directly
- Per-request validation (Stripe/industry standard pattern) — API key checked on every MCP request including tool discovery (`tools/list`). No separate connection-time validation step.
- Invalid/revoked keys receive auth errors on the next request — clean, stateless behavior
- MCP tool calls billed and logged identically to REST API calls — single source of truth, no separate MCP tracking
- Include prompt injection warnings for multi-server environments (following Stripe's guidance)
- Document recommendation for human confirmation of tool calls in MCP host settings
- Configuration for Claude Desktop should be as simple as: `{"url": "http://localhost:3000/mcp/", "headers": {"Authorization": "Bearer <key>"}}`

### Claude's Discretion
- Tool granularity decisions (one-per-operation vs grouped)
- Exact MCP content block structure per tool response
- Error message formatting and actionable suggestions
- MCP SDK/library choice for Python implementation

### Deferred Ideas (OUT OF SCOPE)
- OpenClaw `skills.md` — a human/agent-readable guide teaching OpenClaw how to invoke Spectra tools via skills. Create after MCP server is built and tested.
- OAuth support — Stripe recommends OAuth for production. Would matter for third-party apps connecting on behalf of users. Future phase.
- Restricted/scoped API keys — ability to create keys limited to read-only or specific resources. Future enhancement to Phase 38 key infrastructure.
- stdio transport — npm-distributable local MCP package (like `@stripe/mcp`). Not needed since Spectra is a hosted service and HTTP works for local dev.
- Sandbox/live mode separation — separate MCP access for test vs production environments. Spectra doesn't have a sandbox concept yet.
- `search_stripe_documentation`-style tool — let AI agents search Spectra docs. Interesting but out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MCP-01 | MCP server exposes a tool to upload a file and trigger onboarding | `spectra_upload_file` tool: base64 file content + filename -> httpx POST to `/v1/files/upload` -> returns data brief + suggestions. FastMCP `@mcp.tool` decorator with curated description. |
| MCP-02 | MCP server exposes a tool to query a file (ask a question, get analysis result) | `spectra_run_analysis` tool: file_id + question -> httpx POST to `/v1/chat/query` -> returns analysis with typed content blocks (TextContent for narrative, code blocks for generated code, structured data for chart specs). |
| MCP-03 | MCP server exposes tools to list, delete, and download files | `spectra_list_files`, `spectra_delete_file`, `spectra_download_file` tools: simple CRUD wrappers calling GET `/v1/files`, DELETE `/v1/files/{id}`, GET `/v1/files/{id}/download` via httpx. |
| MCP-04 | MCP server exposes a tool to get file context, data brief, and query suggestions | `spectra_get_context` tool: file_id -> httpx GET `/v1/files/{id}/context` -> returns data brief, summary, user context, and query suggestions as structured text. |
| MCP-05 | MCP server authenticates using a user's API key | Custom FastMCP middleware extracts Bearer token from Authorization header via `get_http_headers()`, passes it through to httpx calls to REST API. REST API validates the key via existing `get_authenticated_user()` dependency. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastmcp` | `>=3.0.2` | MCP server framework | De facto standard for Python MCP servers. v3.0.2 released 2026-02-22. Provides `@mcp.tool` decorator, middleware system, `get_http_headers()` dependency injection, `combine_lifespans`, Streamable HTTP transport. Compatible with Python 3.12. |
| `httpx` | `>=0.27.0` (existing) | Internal loopback HTTP calls from MCP tools to REST API | Already installed. MCP tools call REST API via httpx to preserve the complete auth/credit/logging middleware chain. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mcp` (transitive) | `>=1.26.0` | Official MCP Python SDK types (`TextContent`, `ImageContent`, `EmbeddedResource`, `ToolAnnotations`) | Pulled in by `fastmcp` as dependency. Import types for explicit content block construction in tool responses. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `fastmcp` (manual tools) | `FastMCP.from_fastapi()` auto-generation | Auto-generated tools have poor LLM descriptions per FastMCP's own docs. Manual tools with curated descriptions perform significantly better for AI agents. |
| `fastmcp` | Base `mcp` SDK (v1.26.0) | Base SDK requires manual tool registration, transport setup, session management — 3-5x more boilerplate. |
| `fastapi-mcp` (tadata-org) | — | Wrapper over FastMCP without enough added value; last release July 2025. |
| httpx loopback | Direct service function imports | httpx adds ~1ms but keeps auth consistent. Direct import bypasses auth entirely, creating a security discrepancy between REST API and MCP paths. |

**Installation:**
```bash
uv add fastmcp
```

Note: `fastmcp` pulls in `mcp>=1.26.0` transitively. Do NOT add `mcp` separately.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── mcp_server.py           # FastMCP instance + tool definitions + auth middleware
├── main.py                 # Modified: combine_lifespans, mount mcp_app at /mcp/
└── routers/api_v1/         # Existing REST API (unchanged, called by MCP tools via httpx)
```

### Pattern 1: MCP Server as ASGI Sub-Mount with Lifespan Coordination

**What:** Create a FastMCP instance in `mcp_server.py`, generate the ASGI app via `mcp.http_app(path="/")`, and mount it on the FastAPI app at `/mcp`. Use `combine_lifespans` to merge the existing FastAPI lifespan with the MCP app's lifespan.

**When to use:** Always — this is the only pattern that correctly initializes both the FastAPI checkpointer/scheduler and the MCP session manager.

**Example:**
```python
# backend/app/mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP(
    name="Spectra Data Analysis",
    stateless_http=True,  # No session affinity needed
)

def create_mcp_app():
    """Return the ASGI app for mounting on FastAPI."""
    return mcp.http_app(path="/")
```

```python
# backend/app/main.py (modified section)
from fastmcp.utilities.lifespan import combine_lifespans

# In the mode-gating section:
if mode in ("api", "dev"):
    from app.mcp_server import create_mcp_app

    mcp_app = create_mcp_app()

    # Replace the existing lifespan with combined lifespan
    # The FastAPI app must be created with the combined lifespan
    ...

    app.mount("/mcp", mcp_app)
```

**Critical detail on lifespan:** The existing FastAPI app already has a lifespan (checkpointer, scheduler, LLM validation). FastMCP's `http_app()` also has its own lifespan for session manager initialization. These MUST be merged using `combine_lifespans`:

```python
from fastmcp.utilities.lifespan import combine_lifespans

# The FastAPI app constructor needs the combined lifespan
app = FastAPI(
    ...
    lifespan=combine_lifespans(existing_lifespan, mcp_app.lifespan),
)
```

**Import path verified:** `from fastmcp.utilities.lifespan import combine_lifespans` — confirmed in FastMCP 3.0.2 docs and issue tracker. The STATE.md blocker about this import path is resolved.

### Pattern 2: Custom Auth Middleware for Per-Request API Key Validation

**What:** Use FastMCP's middleware system to extract the Bearer token from the Authorization header on every MCP request, validate it, and make it available to tools. Tools then pass the token through to httpx calls.

**When to use:** Every MCP request including `tools/list`.

**Example:**
```python
# backend/app/mcp_server.py
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError

class ApiKeyAuthMiddleware(Middleware):
    """Validate Spectra API key on every MCP request."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            raise ToolError("Missing or invalid Authorization header. Use: Bearer <your-api-key>")

        token = auth_header.removeprefix("Bearer ").strip()
        if not token.startswith("spe_"):
            raise ToolError("Invalid API key format. Spectra API keys start with 'spe_'.")

        # Store token in context for tools to use
        context.fastmcp_context.set_state("api_key", token)
        return await call_next(context)

mcp = FastMCP(name="Spectra Data Analysis", stateless_http=True)
mcp.add_middleware(ApiKeyAuthMiddleware())
```

### Pattern 3: MCP Tools Calling REST API via httpx Loopback

**What:** Each MCP tool extracts the API key from context, makes an httpx call to the REST API endpoint with the Bearer token, and returns the result as typed MCP content blocks.

**When to use:** All MCP tools. This preserves the complete auth/credit/logging chain.

**Example:**
```python
from fastmcp import Context
import httpx

BASE_URL = "http://localhost:8000"  # Configured per environment

@mcp.tool(
    description="Upload a CSV or Excel file to Spectra for AI analysis. "
    "Returns a data brief summarizing the file's contents and suggested questions to ask.",
    annotations={"destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def spectra_upload_file(
    filename: str,
    file_content_base64: str,
    ctx: Context,
) -> str:
    """Upload a file and trigger onboarding analysis."""
    api_key = ctx.get_state("api_key")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Decode base64, construct multipart upload
        import base64
        file_bytes = base64.b64decode(file_content_base64)
        response = await client.post(
            f"{BASE_URL}/v1/files/upload",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, file_bytes)},
        )

    if response.status_code != 201:
        error = response.json().get("error", {})
        raise ToolError(f"Upload failed: {error.get('message', 'Unknown error')}")

    data = response.json()["data"]
    return (
        f"File uploaded successfully.\n\n"
        f"**File ID:** {data['id']}\n"
        f"**Filename:** {data['filename']}\n\n"
        f"## Data Brief\n{data.get('data_brief', 'Processing...')}\n\n"
        f"## Suggested Questions\n"
        + "\n".join(f"- {q}" for q in (data.get('query_suggestions') or []))
    )
```

### Pattern 4: Typed Content Blocks for Multi-Type Responses

**What:** Use FastMCP's `ToolResult` with explicit `TextContent` blocks to return semantically distinct output types (narrative, code, chart specs) that AI agents can parse.

**When to use:** `spectra_run_analysis` tool response, which returns analysis text, generated code, and optional chart specifications.

**Example:**
```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

@mcp.tool(
    description="Ask a natural language question about an uploaded file. "
    "Returns the AI-generated analysis including narrative text, Python code, "
    "and chart specifications when applicable.",
)
async def spectra_run_analysis(
    file_id: str,
    question: str,
    ctx: Context,
) -> ToolResult:
    """Run analysis query against a file."""
    api_key = ctx.get_state("api_key")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/query",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": question, "file_ids": [file_id]},
        )

    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ToolError(f"Analysis failed: {error.get('message', 'Unknown error')}")

    result = response.json()
    data = result.get("data", {})

    content_blocks = []

    # Narrative analysis as text
    if data.get("analysis"):
        content_blocks.append(
            TextContent(type="text", text=f"## Analysis\n\n{data['analysis']}")
        )

    # Generated code as distinct text block
    if data.get("code"):
        content_blocks.append(
            TextContent(type="text", text=f"## Generated Code\n\n```python\n{data['code']}\n```")
        )

    # Chart spec as distinct text block
    if data.get("chart_spec"):
        import json
        content_blocks.append(
            TextContent(
                type="text",
                text=f"## Chart Specification\n\n```json\n{json.dumps(data['chart_spec'], indent=2)}\n```"
            )
        )

    credits_note = f"\n\n*Credits used: {result.get('credits_used', 'unknown')}*"
    content_blocks.append(TextContent(type="text", text=credits_note))

    return ToolResult(content=content_blocks)
```

### Pattern 5: Mode-Gated MCP Mounting

**What:** Only mount the MCP server when `SPECTRA_MODE` is `api` or `dev`, consistent with the existing REST API v1 mode-gating pattern in `main.py`.

**When to use:** Always — prevents MCP endpoint exposure in `public` or `admin` modes.

**Example (in main.py):**
```python
# API v1 routes + MCP server (api and dev modes)
if mode in ("api", "dev"):
    from app.routers.api_v1 import api_v1_router
    from app.middleware.api_usage import ApiUsageMiddleware
    from app.mcp_server import create_mcp_app

    app.include_router(api_v1_router)
    app.include_router(api_v1_router, prefix="/api")
    app.add_middleware(ApiUsageMiddleware)

    mcp_app = create_mcp_app()
    app.mount("/mcp", mcp_app)
```

### Anti-Patterns to Avoid
- **Using `from_fastapi()` auto-generation as the final implementation:** Auto-generated tool descriptions are poor for LLM consumption. FastMCP's own docs warn against this. Use manual curated tools.
- **Importing service functions directly in MCP tools:** Bypasses the auth/credit/logging middleware chain. Always call REST API via httpx.
- **Module-level mutable state in MCP tools:** Concurrent requests share module state. Pass all context through tool arguments and resolve per-call via API key.
- **Using `asyncio.run()` inside sync MCP tool functions:** Fails in ASGI context. Define all tools as `async def`.
- **Mounting MCP in all modes:** Only mount in `api` and `dev` modes. Public and admin modes should not expose MCP.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol handling | Custom JSON-RPC implementation | `fastmcp>=3.0.2` | MCP protocol is complex (sessions, content negotiation, transport). FastMCP handles all of this. |
| ASGI lifespan merging | Manual `asynccontextmanager` composition | `combine_lifespans` from `fastmcp.utilities.lifespan` | FastMCP's utility handles edge cases around nested lifespans that manual composition misses. |
| Content type conversion | Manual base64/MIME type handling | FastMCP's `Image`, `File`, `ToolResult` helpers | Automatic MIME detection, base64 encoding, correct MCP content block types. |
| Bearer token extraction | Custom ASGI middleware | FastMCP's `Middleware` class + `get_http_headers()` | Protocol-aware middleware that works correctly with MCP's message lifecycle. |

**Key insight:** The MCP protocol layer is non-trivial (JSON-RPC framing, session management, content negotiation). FastMCP abstracts this entirely. The implementation work is in the tool definitions and auth middleware, not the protocol.

## Common Pitfalls

### Pitfall 1: Forgetting to Merge Lifespans
**What goes wrong:** MCP server is mounted but FastAPI app keeps its original lifespan. The MCP session manager never initializes. Requests to `/mcp/` return "Task group is not initialized" errors.
**Why it happens:** `app.mount("/mcp", mcp_app)` does not automatically merge lifespans. FastAPI/Starlette does not support nested lifespan propagation.
**How to avoid:** Use `combine_lifespans(existing_lifespan, mcp_app.lifespan)` when constructing the FastAPI app. The existing `lifespan` function must be extracted and passed as the first argument.
**Warning signs:** "Task group is not initialized" or silent 500 errors on MCP endpoint access.

### Pitfall 2: httpx Calling Wrong Base URL
**What goes wrong:** MCP tools use hardcoded `http://localhost:8000` but the backend runs on a different port or behind a reverse proxy in production. Tool calls fail silently or hit wrong service.
**Why it happens:** The base URL for loopback calls depends on deployment topology (Docker, Dokploy, local dev).
**How to avoid:** Use a configurable base URL, ideally from an environment variable or settings. In dev mode, the backend serves everything on one port. In production, the API service has its own domain.
**Warning signs:** MCP tools return connection errors or unexpected responses in staging/production.

### Pitfall 3: MCP Tool Returning Raw Exception Traces
**What goes wrong:** An unhandled exception in a tool function returns a Python traceback to the LLM. The LLM gets confused by stack traces and cannot reason about the error.
**Why it happens:** Developer tests happy path only. Error handling is not added to tool functions.
**How to avoid:** Wrap all httpx calls in try/except. Use `ToolError` from FastMCP for controlled error messages. Use `mask_error_details=True` on the FastMCP instance as a safety net.
**Warning signs:** LLM responses include Python traceback text in conversations.

### Pitfall 4: Truncation of Large Analysis Results
**What goes wrong:** `spectra_run_analysis` returns the full execution result (potentially megabytes of DataFrame output). The LLM context window is exhausted, causing degraded performance or errors.
**Why it happens:** REST API returns full results. MCP tool passes them through without truncation.
**How to avoid:** Truncate or summarize large results in the MCP tool response. Set a reasonable max length for text content blocks. The REST API returns everything; the MCP layer should be smarter about what it passes to the LLM.
**Warning signs:** LLM responses become slow or reference truncated content.

### Pitfall 5: CORS Headers Missing for MCP-Specific Headers
**What goes wrong:** Browser-based MCP clients cannot access `mcp-session-id` response header. Session tracking breaks.
**Why it happens:** CORS middleware does not expose MCP-specific headers.
**How to avoid:** When configuring CORS for the MCP endpoint, include `mcp-protocol-version` and `mcp-session-id` in allowed/exposed headers. With `stateless_http=True`, session headers are less critical, but including them is defensive.
**Warning signs:** Browser console CORS errors when connecting to MCP endpoint.

### Pitfall 6: File Upload via MCP Using Base64 in Tool Parameters
**What goes wrong:** MCP protocol passes tool arguments as JSON. Binary files must be base64-encoded in the tool parameter, which increases payload size by ~33% and adds encoding/decoding overhead.
**Why it happens:** MCP tools receive structured JSON parameters, not multipart form data. There is no native binary upload in MCP tool calls.
**How to avoid:** Accept `file_content_base64: str` parameter in the upload tool. Decode in the tool function before sending to REST API as multipart upload. Document the base64 requirement in the tool description so the LLM encodes correctly. Set appropriate timeout (120s) for large files.
**Warning signs:** Upload tool fails with encoding errors or times out on large files.

## Code Examples

### Complete MCP Server Module
```python
# backend/app/mcp_server.py

from fastmcp import FastMCP, Context
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
import httpx
import base64
import json

from app.config import get_settings


class ApiKeyAuthMiddleware(Middleware):
    """Validate Spectra API key on every MCP request."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            raise ToolError(
                "Authentication required. Include your Spectra API key as: "
                "Authorization: Bearer spe_<your-key>"
            )

        token = auth_header.removeprefix("Bearer ").strip()
        if not token.startswith("spe_"):
            raise ToolError(
                "Invalid API key format. Spectra API keys start with 'spe_'. "
                "Create one at Settings > API Keys in the Spectra dashboard."
            )

        context.fastmcp_context.set_state("api_key", token)
        return await call_next(context)


def _get_base_url() -> str:
    """Get the base URL for internal REST API calls."""
    settings = get_settings()
    # In production, use the configured API URL
    # In dev, use localhost on the same port
    return getattr(settings, "mcp_api_base_url", "http://localhost:8000")


mcp = FastMCP(
    name="Spectra Data Analysis",
    stateless_http=True,
    mask_error_details=True,
)
mcp.add_middleware(ApiKeyAuthMiddleware())


@mcp.tool(
    description=(
        "Upload a CSV or Excel file to Spectra for AI-powered data analysis. "
        "The file is automatically analyzed to produce a data brief summarizing "
        "its structure, key statistics, and notable patterns. "
        "Returns the file ID (needed for subsequent queries), the data brief, "
        "and suggested questions you can ask about the data. "
        "Supports .csv, .xlsx, and .xls files up to 50MB."
    ),
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
)
async def spectra_upload_file(
    filename: str,
    file_content_base64: str,
    ctx: Context,
) -> str:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    try:
        file_bytes = base64.b64decode(file_content_base64)
    except Exception:
        raise ToolError("Invalid base64 encoding for file_content_base64.")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{base_url}/v1/files/upload",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, file_bytes)},
        )

    if response.status_code != 201:
        error = response.json().get("error", {})
        raise ToolError(f"Upload failed: {error.get('message', 'Unknown error')}")

    data = response.json()["data"]
    suggestions = "\n".join(f"- {q}" for q in (data.get("query_suggestions") or []))
    return (
        f"File uploaded successfully.\n\n"
        f"**File ID:** `{data['id']}`\n"
        f"**Filename:** {data['filename']}\n\n"
        f"## Data Brief\n{data.get('data_brief', 'Processing...')}\n\n"
        f"## Suggested Questions\n{suggestions}"
    )


@mcp.tool(description="List all files uploaded to your Spectra account.")
async def spectra_list_files(ctx: Context) -> str:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{base_url}/v1/files",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ToolError(f"Failed to list files: {error.get('message', 'Unknown error')}")

    files = response.json()["data"]
    if not files:
        return "No files found. Upload a file first using spectra_upload_file."

    lines = ["| File ID | Filename | Created |", "| --- | --- | --- |"]
    for f in files:
        lines.append(f"| `{f['id']}` | {f['filename']} | {f['created_at']} |")
    return "\n".join(lines)


@mcp.tool(description="Delete a file from your Spectra account by its file ID.")
async def spectra_delete_file(file_id: str, ctx: Context) -> str:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(
            f"{base_url}/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ToolError(f"Delete failed: {error.get('message', 'Unknown error')}")

    return f"File `{file_id}` deleted successfully."


@mcp.tool(description="Download a file's raw content by its file ID.")
async def spectra_download_file(file_id: str, ctx: Context) -> str:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{base_url}/v1/files/{file_id}/download",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    if response.status_code != 200:
        raise ToolError(f"Download failed (HTTP {response.status_code}).")

    # Return file content as text (CSV) or indicate binary
    content_type = response.headers.get("content-type", "")
    if "text" in content_type or "csv" in content_type:
        # Truncate large files for LLM context
        text = response.text
        if len(text) > 10000:
            return f"File content (first 10,000 characters):\n\n{text[:10000]}\n\n... (truncated)"
        return f"File content:\n\n{text}"
    else:
        return (
            f"File downloaded ({len(response.content)} bytes, type: {content_type}). "
            "Binary files cannot be displayed as text."
        )


@mcp.tool(
    description=(
        "Get detailed context about an uploaded file, including: "
        "the AI-generated data brief summarizing the file's structure and patterns, "
        "any user-provided context, and suggested questions to explore the data. "
        "Use this before running an analysis to understand what the file contains."
    ),
)
async def spectra_get_context(file_id: str, ctx: Context) -> str:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{base_url}/v1/files/{file_id}/context",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ToolError(f"Failed to get context: {error.get('message', 'Unknown error')}")

    data = response.json()["data"]
    suggestions = "\n".join(f"- {q}" for q in (data.get("query_suggestions") or []))
    user_ctx = data.get("user_context") or "None provided"

    return (
        f"## File: {data['filename']}\n\n"
        f"## Data Brief\n{data.get('data_brief', 'Not available')}\n\n"
        f"## User Context\n{user_ctx}\n\n"
        f"## Suggested Questions\n{suggestions}"
    )


@mcp.tool(
    description=(
        "Ask a natural language question about an uploaded file and receive "
        "AI-powered data analysis. Returns the analysis narrative, generated "
        "Python code used for the analysis, and chart specifications if applicable. "
        "Each query costs credits (same as using the Spectra web interface). "
        "Use spectra_get_context first to understand the file before querying."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
async def spectra_run_analysis(
    file_id: str,
    question: str,
    ctx: Context,
) -> ToolResult:
    api_key = ctx.get_state("api_key")
    base_url = _get_base_url()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{base_url}/v1/chat/query",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": question, "file_ids": [file_id]},
        )

    if response.status_code != 200:
        error = response.json().get("error", {})
        raise ToolError(f"Analysis failed: {error.get('message', 'Unknown error')}")

    result = response.json()
    data = result.get("data", {})
    content_blocks = []

    if data.get("analysis"):
        content_blocks.append(
            TextContent(type="text", text=f"## Analysis\n\n{data['analysis']}")
        )

    if data.get("code"):
        content_blocks.append(
            TextContent(
                type="text",
                text=f"## Generated Code\n\n```python\n{data['code']}\n```",
            )
        )

    if data.get("chart_spec"):
        content_blocks.append(
            TextContent(
                type="text",
                text=f"## Chart Specification\n\n```json\n{json.dumps(data['chart_spec'], indent=2)}\n```",
            )
        )

    credits_used = result.get("credits_used")
    if credits_used is not None:
        content_blocks.append(
            TextContent(type="text", text=f"\n*Credits used: {credits_used}*")
        )

    if not content_blocks:
        content_blocks.append(
            TextContent(type="text", text="Analysis completed but returned no content.")
        )

    return ToolResult(content=content_blocks)


def create_mcp_app():
    """Create and return the MCP ASGI application for mounting."""
    return mcp.http_app(path="/")
```

### Lifespan Coordination in main.py
```python
# In backend/app/main.py — modify the lifespan and app creation

from fastmcp.utilities.lifespan import combine_lifespans

# Extract existing lifespan function (already defined as async context manager)
# Then conditionally combine with MCP lifespan

if mode in ("api", "dev"):
    from app.mcp_server import create_mcp_app
    mcp_app = create_mcp_app()
    # Rebuild app with combined lifespan
    app = FastAPI(
        title="Spectra API",
        version="0.1.0",
        lifespan=combine_lifespans(lifespan, mcp_app.lifespan),
        redirect_slashes=False,
    )
    app.mount("/mcp", mcp_app)
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "spectra": {
      "url": "http://localhost:3000/mcp/",
      "headers": {
        "Authorization": "Bearer spe_your_api_key_here"
      }
    }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SSE transport for MCP | Streamable HTTP transport | MCP SDK 1.x (2025) | SSE is deprecated. Use Streamable HTTP as default. |
| `mcp.server.fastmcp.FastMCP` (from base SDK) | `fastmcp.FastMCP` (standalone package) | FastMCP 2.x (2025) | Import path changed when FastMCP became a separate package from the base MCP SDK. |
| `fastmcp.utilities.asgi.combine_lifespans` | `fastmcp.utilities.lifespan.combine_lifespans` | FastMCP 3.0 (2026-01-19) | Import path moved. This resolves the STATE.md blocker. |
| Stateful MCP sessions | `stateless_http=True` for scalable deployments | FastMCP 2.x+ | Stateless mode recommended for production HTTP deployments. Eliminates session affinity requirements. |
| OAuth for MCP auth | Bearer token / custom middleware | Current | OAuth is optional and recommended for third-party integrations. For first-party API key auth, custom middleware with `get_http_headers()` is simpler and sufficient. |

**Deprecated/outdated:**
- SSE transport (`/sse` endpoint): Deprecated in favor of Streamable HTTP. Do not use.
- `mcp.server.fastmcp` import: Old import path from when FastMCP was bundled in the base `mcp` SDK. Use `from fastmcp import FastMCP`.

## Open Questions

1. **httpx Base URL Configuration for Loopback**
   - What we know: MCP tools need to call REST API via httpx. In dev mode, both run on the same process. In production (Dokploy), the API service is at its own domain.
   - What's unclear: Should the loopback be `http://localhost:8000` (same process) or should it go through the public URL? Using localhost avoids network latency but may not work if the backend is behind a reverse proxy with path rewriting.
   - Recommendation: Add a `MCP_API_BASE_URL` env var (defaults to `http://localhost:8000`). In Dokploy production config, set it to the internal service URL. This is a simple configuration choice during implementation.

2. **Auth Middleware Scope: `on_call_tool` vs `on_list_tools`**
   - What we know: The CONTEXT.md states API key should be checked on every request including `tools/list`. FastMCP middleware has `on_call_tool` hook.
   - What's unclear: Whether FastMCP middleware also has an `on_list_tools` hook, or whether there is a different mechanism to intercept `tools/list` requests.
   - Recommendation: Verify at implementation time. If `on_list_tools` does not exist, the auth can be applied at the ASGI level (Starlette middleware on the mounted app) as a fallback. The tools themselves still validate auth via httpx calls, so even if `tools/list` is unauthenticated, no data is exposed — only tool names and descriptions.

3. **Trailing Slash Behavior on `/mcp/` Mount**
   - What we know: The existing FastAPI app has a `strip_trailing_slash` middleware. The MCP server is mounted at `/mcp`. Starlette's `mount()` behavior with trailing slashes can be inconsistent.
   - What's unclear: Whether MCP clients will send requests to `/mcp/` (with slash) or `/mcp` (without). The existing trailing slash middleware may interfere.
   - Recommendation: Test both paths during implementation. The `path="/"` in `mcp.http_app(path="/")` means the MCP endpoint is at the root of the mounted sub-app. Claude Desktop config should use `http://localhost:3000/mcp/` with trailing slash.

## Sources

### Primary (HIGH confidence)
- [FastMCP official docs — HTTP Deployment](https://gofastmcp.com/deployment/http) — ASGI mounting, lifespan, Streamable HTTP transport
- [FastMCP official docs — Tools](https://gofastmcp.com/servers/tools) — Tool decorator, ToolResult, content types, annotations, error handling
- [FastMCP official docs — Dependency Injection](https://gofastmcp.com/servers/dependency-injection) — `get_http_headers()`, `Context`, `Depends()`, `set_state()`/`get_state()`
- [FastMCP official docs — Authentication](https://gofastmcp.com/servers/auth/authentication) — Auth providers, middleware patterns
- [FastMCP PyPI](https://pypi.org/project/fastmcp/) — v3.0.2 released 2026-02-22, Python >=3.10
- [MCP Python SDK PyPI](https://pypi.org/project/mcp/) — v1.26.0, pulled transitively by fastmcp

### Secondary (MEDIUM confidence)
- [Implementing Authentication in a Remote MCP Server with FastMCP](https://gelembjuk.com/blog/post/authentication-remote-mcp-server-python/) — Custom middleware pattern with `get_http_headers()` and `set_state()`
- [GitHub Issue #1367: Mounting Streamable HTTP on FastAPI](https://github.com/modelcontextprotocol/python-sdk/issues/1367) — Lifespan and path issues when mounting
- [FastMCP `combine_lifespans` discussions](https://github.com/jlowin/fastmcp/discussions/559) — Lifespan merging patterns
- [Stripe MCP Documentation](https://docs.stripe.com/mcp) — Reference architecture for per-request Bearer auth

### Tertiary (LOW confidence)
- Prior project research (`.planning/research/ARCHITECTURE.md`, `STACK.md`, `PITFALLS-v0.7-api-mcp.md`) — Written 2026-02-23, some details (e.g., import paths) now updated based on current research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `fastmcp>=3.0.2` verified on PyPI (2026-02-22), official docs consulted for all patterns, import paths confirmed
- Architecture: HIGH — ASGI mounting, lifespan coordination, middleware auth, and httpx loopback patterns all verified in official FastMCP docs and community examples
- Pitfalls: HIGH — Cross-referenced with prior project pitfall research (PITFALLS-v0.7-api-mcp.md) and FastMCP GitHub issues

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (30 days — FastMCP is stable at v3.0.2)
