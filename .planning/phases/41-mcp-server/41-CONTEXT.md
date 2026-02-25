# Phase 41: MCP Server - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose Spectra's analysis capabilities as first-class MCP tools via a production-ready MCP server. Claude Desktop, Claude Code, OpenClaw, or any MCP-compliant host can upload files, run analyses, and manage files through curated tools. The MCP server wraps Phase 40's REST API endpoints, is ASGI-mounted on the existing FastAPI backend, and uses Streamable HTTP transport.

</domain>

<decisions>
## Implementation Decisions

### Tool Design
- All tools use `spectra_` prefix for clear namespace identification across multi-server setups (e.g., `spectra_upload_file`, `spectra_run_analysis`)
- Tool granularity: Claude's discretion — decide per-tool whether to split or group based on MCP best practices and LLM tool-selection behavior
- Rich descriptions for core tools (`spectra_upload_file`, `spectra_run_analysis`, `spectra_get_context`) where the LLM needs guidance on when/how to use them; concise one-liner descriptions for simple CRUD tools (`spectra_list_files`, `spectra_delete_file`, `spectra_download_file`)
- Minimal parameters only — expose essentials (file path, question text, file ID). No optional power-user params. Power users use the REST API directly. AI agents work best with simple tool signatures.

### Response Formatting
- Use typed MCP content blocks (text, image, resource) to preserve semantic distinction between output types — narrative analysis, generated code, chart specifications, and data tables must be distinguishable by the consuming AI agent
- Wait for completion on long-running operations (file upload + onboarding, complex analysis) — no polling pattern. Single tool call returns the full result. MCP hosts handle long-running tool calls natively.
- Error handling: Claude's discretion — use MCP's built-in error mechanisms with clear, actionable messages

### Transport & Mounting
- ASGI sub-mount on the existing FastAPI backend application
- Streamable HTTP transport only — no stdio. Both local dev (`http://localhost:3000/mcp/`) and production (`https://<domain>/mcp/`) use the same transport
- Mounted at `/mcp/` path — clearly separate from REST API at `/api/v1/`
- Always active in dev mode (SPECTRA_MODE=dev) alongside existing backend routes — no mode switching needed for local MCP testing with Claude Desktop

### Authentication
- Bearer token in Authorization header — reuses Phase 38 API key infrastructure directly
- Per-request validation (Stripe/industry standard pattern) — API key checked on every MCP request including tool discovery (`tools/list`). No separate connection-time validation step.
- Invalid/revoked keys receive auth errors on the next request — clean, stateless behavior
- MCP tool calls billed and logged identically to REST API calls — single source of truth, no separate MCP tracking

### Security Documentation
- Include prompt injection warnings for multi-server environments (following Stripe's guidance)
- Document recommendation for human confirmation of tool calls in MCP host settings
- Security considerations section in MCP documentation

### Claude's Discretion
- Tool granularity decisions (one-per-operation vs grouped)
- Exact MCP content block structure per tool response
- Error message formatting and actionable suggestions
- MCP SDK/library choice for Python implementation

</decisions>

<specifics>
## Specific Ideas

- Stripe's MCP implementation at `https://mcp.stripe.com` as reference architecture — per-request auth, Bearer token in headers, tools organized by resource
- OpenClaw compatibility is important — the MCP server should work with any MCP-compliant host, not just Claude products
- Response formatting must distinguish output types (code vs chart vs narrative) at the protocol level using typed content blocks, not just markdown formatting — this is critical for AI agents to handle Spectra's multi-type query responses correctly
- Configuration for Claude Desktop should be as simple as: `{"url": "http://localhost:3000/mcp/", "headers": {"Authorization": "Bearer <key>"}}`

</specifics>

<deferred>
## Deferred Ideas

- OpenClaw `skills.md` — a human/agent-readable guide teaching OpenClaw how to invoke Spectra tools via skills. Create after MCP server is built and tested.
- OAuth support — Stripe recommends OAuth for production. Would matter for third-party apps connecting on behalf of users. Future phase.
- Restricted/scoped API keys — ability to create keys limited to read-only or specific resources. Future enhancement to Phase 38 key infrastructure.
- stdio transport — npm-distributable local MCP package (like `@stripe/mcp`). Not needed since Spectra is a hosted service and HTTP works for local dev.
- Sandbox/live mode separation — separate MCP access for test vs production environments. Spectra doesn't have a sandbox concept yet.
- `search_stripe_documentation`-style tool — let AI agents search Spectra docs. Interesting but out of scope.

</deferred>

---

*Phase: 41-mcp-server*
*Context gathered: 2026-02-24*
