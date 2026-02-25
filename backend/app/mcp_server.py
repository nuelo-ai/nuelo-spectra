"""Spectra MCP Server — exposes data analysis capabilities as MCP tools.

Defines 6 tools with spectra_ prefix, auth middleware for API key validation,
and a factory function to create the ASGI application for mounting.

All tools call the REST API v1 via httpx loopback to preserve the auth,
credit deduction, and usage logging middleware chain. No direct service imports.

Claude Desktop configuration:
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

Security:
  - Enable "Ask before running tools" in your MCP host settings.
  - In multi-server environments, be aware of prompt injection risks --
    a malicious tool in another server could craft prompts that invoke
    Spectra tools without user awareness.
  - API keys grant full access to the authenticated user's data.
    Use scoped keys when available (future feature).
"""

from __future__ import annotations

import base64
import json
import logging
import struct
from typing import Any, Sequence

logger = logging.getLogger(__name__)

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from app.config import get_settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_base_url() -> str:
    """Get the base URL for internal REST API calls.

    Reads MCP_API_BASE_URL from settings. Defaults to http://localhost:8000.
    In production (Dokploy), set this to the internal service URL.
    """
    settings = get_settings()
    return settings.mcp_api_base_url


def _api_v1(path: str) -> str:
    """Build a full /api/v1/{path} URL.

    MCP only runs in SPECTRA_MODE=api and dev. In both modes the api_v1_router
    is mounted under /api (giving /api/v1/*). Bare /v1/* only exists in dev
    as a secondary mount — using /api/v1/ is correct in all MCP-enabled modes.
    """
    return f"{_get_base_url()}/api/v1/{path.lstrip('/')}"


async def _api_headers(ctx: Context) -> dict[str, str]:
    """Build Authorization header from the API key stored in tool context."""
    return {"Authorization": f"Bearer {await ctx.get_state('api_key')}"}


def _extract_error_message(response: httpx.Response) -> str:
    """Extract error message from API error envelope, with fallback."""
    try:
        body = response.json()
        return body.get("error", {}).get("message", f"HTTP {response.status_code}")
    except Exception:
        return f"HTTP {response.status_code}"


def _render_execution_result_table(raw) -> str | None:
    """Render execution_result as a markdown table (max 50 rows).

    Returns None if the data is absent or cannot be rendered as a table.
    """
    if not raw:
        return None

    data = raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

    if not isinstance(data, list) or not data:
        return None

    MAX_ROWS = 50
    total = len(data)
    rows = data[:MAX_ROWS]
    truncation_note = f"\n\n*Showing {MAX_ROWS} of {total} rows.*" if total > MAX_ROWS else ""

    # List of dicts → full table
    if isinstance(rows[0], dict):
        headers = list(rows[0].keys())
        header_row = "| " + " | ".join(str(h) for h in headers) + " |"
        sep_row = "| " + " | ".join("---" for _ in headers) + " |"
        data_rows = [
            "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
            for row in rows
        ]
        table = "\n".join([header_row, sep_row, *data_rows])
    else:
        # Scalars — single-column table
        table = "| Value |\n| --- |\n" + "\n".join(f"| {v} |" for v in rows)

    return f"## Data Table\n\n{table}{truncation_note}"


# Plotly dtype → (struct format char, byte size)
_PLOTLY_DTYPE_MAP: dict[str, tuple[str, int]] = {
    "f8": ("d", 8),  # float64
    "f4": ("f", 4),  # float32
    "i8": ("q", 8),  # int64
    "i4": ("i", 4),  # int32
    "u4": ("I", 4),  # uint32
}


def _decode_plotly_binary(obj: Any) -> Any:
    """Recursively decode Plotly binary typed arrays to plain Python lists.

    Plotly serializes numpy numeric arrays as {"dtype": "f8", "bdata": "<base64>"}
    for space efficiency. Plotly.js decodes this natively, but the format is
    opaque to AI agents. This helper converts every such node to a plain list
    of numbers so the chart spec is fully readable in MCP output.

    Handles:
      - 1-D arrays  → flat list
      - 2-D arrays  → list of lists (uses "shape" field when present)
      - Unknown dtype → left as-is with a warning log
    """
    if isinstance(obj, dict):
        if "bdata" in obj and "dtype" in obj:
            dtype = obj["dtype"]
            if dtype not in _PLOTLY_DTYPE_MAP:
                logger.warning("_decode_plotly_binary: unknown Plotly dtype %r — leaving as-is", dtype)
                return obj
            fmt_char, item_size = _PLOTLY_DTYPE_MAP[dtype]
            raw = base64.b64decode(obj["bdata"])
            n = len(raw) // item_size
            values: list = list(struct.unpack(f"<{n}{fmt_char}", raw))
            if "shape" in obj:
                try:
                    dims = [int(s.strip()) for s in obj["shape"].split(",")]
                    if len(dims) == 2:
                        rows, cols = dims
                        return [values[i * cols: (i + 1) * cols] for i in range(rows)]
                except (ValueError, AttributeError):
                    pass
            return values
        return {k: _decode_plotly_binary(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_plotly_binary(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Auth Middleware
# ---------------------------------------------------------------------------

class ApiKeyAuthMiddleware(Middleware):
    """Validate Spectra API key on every MCP request.

    Extracts the Bearer token from the Authorization header, verifies
    the spe_ prefix, and stores the token in context state for tools.

    NOTE: on_list_tools is implemented to enforce auth on tools/list too.
    Even without it, tools/list only exposes tool names and descriptions
    (no user data), and each tool validates auth via httpx calls anyway.
    """

    async def _extract_and_validate_token(self) -> str:
        """Extract and validate the Bearer token from HTTP headers.

        Returns:
            The raw API key token.

        Raises:
            ToolError: If the Authorization header is missing/invalid or
                       the token does not have the spe_ prefix.
        """
        request = get_http_request()
        auth_header = request.headers.get("authorization", "")

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

        return token

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        token = await self._extract_and_validate_token()
        # serializable=False → request-scoped dict, no session store needed (stateless_http=True)
        await context.fastmcp_context.set_state("api_key", token, serializable=False)
        return await call_next(context)

    async def on_list_tools(self, context: MiddlewareContext, call_next) -> Sequence:
        # Validate auth even on tools/list per CONTEXT.md decision
        await self._extract_and_validate_token()
        return await call_next(context)


# ---------------------------------------------------------------------------
# FastMCP Instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Spectra Data Analysis",
    mask_error_details=True,
)
mcp.add_middleware(ApiKeyAuthMiddleware())


# ---------------------------------------------------------------------------
# Tool 1: Upload File
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Upload a CSV or Excel file to Spectra for AI-powered data analysis. "
        "The file is automatically analyzed to produce a data brief summarizing "
        "its structure, key statistics, and notable patterns. "
        "Returns the file ID (needed for subsequent queries), the data brief, "
        "and suggested questions you can ask about the data.\n\n"
        "Supported formats: .csv, .xlsx, .xls (up to 50 MB). "
        "The file_content_base64 parameter must be the file's raw bytes "
        "encoded as a base64 string."
    ),
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
)
async def spectra_upload_file(
    filename: str,
    file_content_base64: str,
    ctx: Context,
) -> str:
    """Upload a file and trigger AI onboarding analysis."""
    headers = await _api_headers(ctx)

    try:
        file_bytes = base64.b64decode(file_content_base64)
    except Exception:
        raise ToolError(
            "Invalid base64 encoding for file_content_base64. "
            "Ensure the file content is properly base64-encoded."
        )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                _api_v1("files/upload"),
                headers=headers,
                files={"file": (filename, file_bytes)},
            )
    except httpx.TimeoutException:
        raise ToolError(
            "Upload timed out. Large files may take longer to process. "
            "Try again or use a smaller file."
        )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error during upload: {e}")

    if response.status_code != 201:
        raise ToolError(f"Upload failed: {_extract_error_message(response)}")

    data = response.json()["data"]
    suggestions = "\n".join(
        f"- {q}" for q in (data.get("query_suggestions") or [])
    )
    return (
        f"File uploaded successfully.\n\n"
        f"**File ID:** `{data['id']}`\n"
        f"**Filename:** {data['filename']}\n\n"
        f"## Data Brief\n{data.get('data_brief', 'Processing...')}\n\n"
        f"## Suggested Questions\n{suggestions}"
    )


# ---------------------------------------------------------------------------
# Tool 2: Run Analysis
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Ask a natural language question about an uploaded file and receive "
        "AI-powered data analysis. Returns the analysis narrative, generated "
        "Python code used for the analysis, and chart specifications if applicable.\n\n"
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
    """Run an analysis query against an uploaded file."""
    headers = await _api_headers(ctx)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                _api_v1("chat/query"),
                headers={**headers, "Content-Type": "application/json"},
                json={"query": question, "file_ids": [file_id]},
            )
    except httpx.TimeoutException:
        raise ToolError(
            "Analysis timed out. Complex queries may take longer. Please try again."
        )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error during analysis: {e}")

    if response.status_code != 200:
        raise ToolError(f"Analysis failed: {_extract_error_message(response)}")

    result = response.json()
    data = result.get("data", {})
    content_blocks: list[TextContent] = []

    # Data table (execution_result) — first, so agents see raw data before interpretation
    table_md = _render_execution_result_table(data.get("execution_result"))
    if table_md:
        content_blocks.append(TextContent(type="text", text=table_md))

    # Narrative analysis
    if data.get("analysis"):
        content_blocks.append(
            TextContent(type="text", text=f"## Analysis\n\n{data['analysis']}")
        )

    # Generated Python code
    if data.get("generated_code"):
        content_blocks.append(
            TextContent(
                type="text",
                text=f"## Generated Code\n\n```python\n{data['generated_code']}\n```",
            )
        )

    # Chart specification — decode any Plotly binary typed arrays before returning
    chart_specs = data.get("chart_specs")
    if chart_specs:
        if isinstance(chart_specs, str):
            try:
                chart_specs = _decode_plotly_binary(json.loads(chart_specs))
            except (json.JSONDecodeError, ValueError):
                pass  # malformed JSON — surface as-is
        if isinstance(chart_specs, (dict, list)):
            chart_specs = _decode_plotly_binary(chart_specs)
        if isinstance(chart_specs, str):
            chart_text = chart_specs
        else:
            chart_text = json.dumps(chart_specs, indent=2)
        content_blocks.append(
            TextContent(
                type="text",
                text=f"## Chart Specification\n\n```json\n{chart_text}\n```",
            )
        )

    # Credits used note
    credits_used = result.get("credits_used")
    if credits_used is not None:
        content_blocks.append(
            TextContent(type="text", text=f"\n*Credits used: {credits_used}*")
        )

    # Fallback if no content
    if not content_blocks:
        content_blocks.append(
            TextContent(
                type="text",
                text="Analysis completed but returned no content.",
            )
        )

    return ToolResult(content=content_blocks)


# ---------------------------------------------------------------------------
# Tool 3: List Files
# ---------------------------------------------------------------------------

@mcp.tool(description="List all files uploaded to your Spectra account.")
async def spectra_list_files(ctx: Context) -> str:
    """List all files for the authenticated user."""
    headers = await _api_headers(ctx)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                _api_v1("files"),
                headers=headers,
            )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error: {e}")

    if response.status_code != 200:
        raise ToolError(f"Failed to list files: {_extract_error_message(response)}")

    files = response.json()["data"]
    if not files:
        return "No files found. Upload a file first using spectra_upload_file."

    lines = ["| File ID | Filename | Created |", "| --- | --- | --- |"]
    for f in files:
        lines.append(f"| `{f['id']}` | {f['filename']} | {f['created_at']} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: Delete File
# ---------------------------------------------------------------------------

@mcp.tool(description="Delete a file from your Spectra account by its file ID.")
async def spectra_delete_file(file_id: str, ctx: Context) -> str:
    """Delete a file by its ID."""
    headers = await _api_headers(ctx)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                _api_v1(f"files/{file_id}"),
                headers=headers,
            )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error: {e}")

    if response.status_code != 200:
        raise ToolError(f"Delete failed: {_extract_error_message(response)}")

    return f"File `{file_id}` deleted successfully."


# ---------------------------------------------------------------------------
# Tool 5: Download File
# ---------------------------------------------------------------------------

@mcp.tool(description="Download a file's raw content by its file ID.")
async def spectra_download_file(file_id: str, ctx: Context) -> str:
    """Download file content. Text/CSV is returned directly; binary files show metadata."""
    headers = await _api_headers(ctx)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                _api_v1(f"files/{file_id}/download"),
                headers=headers,
            )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error: {e}")

    if response.status_code != 200:
        raise ToolError(f"Download failed: {_extract_error_message(response)}")

    content_type = response.headers.get("content-type", "")
    if "text" in content_type or "csv" in content_type:
        text = response.text
        if len(text) > 10_000:
            return (
                f"File content (first 10,000 characters):\n\n"
                f"{text[:10_000]}\n\n"
                f"... (truncated, total {len(text)} characters)"
            )
        return f"File content:\n\n{text}"
    else:
        return (
            f"File downloaded ({len(response.content):,} bytes, "
            f"type: {content_type}). "
            "Binary files cannot be displayed as text."
        )


# ---------------------------------------------------------------------------
# Tool 6: Get Context
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Get detailed context about an uploaded file, including: "
        "the AI-generated data brief summarizing the file's structure and patterns, "
        "any user-provided context, and suggested questions to explore the data.\n\n"
        "Use this before running an analysis to understand what the file contains "
        "and what questions are most relevant."
    ),
)
async def spectra_get_context(file_id: str, ctx: Context) -> str:
    """Get file context: data brief, user context, and suggested questions."""
    headers = await _api_headers(ctx)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                _api_v1(f"files/{file_id}/context"),
                headers=headers,
            )
    except httpx.HTTPError as e:
        raise ToolError(f"Connection error: {e}")

    if response.status_code != 200:
        raise ToolError(
            f"Failed to get context: {_extract_error_message(response)}"
        )

    data = response.json()["data"]
    suggestions = "\n".join(
        f"- {q}" for q in (data.get("query_suggestions") or [])
    )
    user_ctx = data.get("user_context") or "None provided"

    return (
        f"## File: {data['filename']}\n\n"
        f"## Data Brief\n{data.get('data_brief', 'Not available')}\n\n"
        f"## User Context\n{user_ctx}\n\n"
        f"## Suggested Questions\n{suggestions}"
    )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_mcp_app():
    """Create and return the MCP ASGI application for mounting."""
    return mcp.http_app(path="/", stateless_http=True)
