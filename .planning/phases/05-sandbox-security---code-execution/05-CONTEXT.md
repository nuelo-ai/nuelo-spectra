# Phase 5: Sandbox Security & Code Execution - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Secure Python code execution with multi-layer isolation protecting user data. AI-generated code must execute safely in an isolated environment that prevents malicious operations while allowing legitimate data analysis. The sandbox prevents file system access, network calls, and resource abuse while maintaining fast execution for pandas/numpy operations.

</domain>

<decisions>
## Implementation Decisions

### Sandbox Runtime Choice
- **E2B Cloud for MVP** — Managed microVMs with Firecracker isolation, ~150ms boot time, zero maintenance
- **Fallback plan**: Can migrate to self-hosted Docker + gVisor later if needed
- **Abstraction layer**: SandboxRuntime interface pattern with `execute()` method
  - E2BSandbox implementation (Phase 5)
  - GVisorSandbox implementation (future)
  - Swap via config without code changes
- **Failure handling**: If E2B is down, fail gracefully with "Service temporarily unavailable" error
  - No automatic fallback to Docker (security first)
  - Save query for potential retry
  - Clean failure state

### Sandbox Lifecycle
- **One sandbox per execution** (create → execute → destroy)
- Fresh sandbox created for each code execution
- Destroyed immediately after returning results
- No idle sandboxes (cost-efficient, no resource waste)
- No state persistence between queries (cleanest isolation)

### Execution UX Flow
- **Auto-execute**: Code runs immediately after Code Checker validates (no user approval required)
- **Code display timing**: Show code after validation, before execution
  - Stream flow: Thinking → Generating code → Validating → [Code block appears] → Executing → Results
  - User sees what will run but doesn't have to click "Run"
- **Results display**: Data table streams first, then explanation
  - Pandas DataFrame results appear immediately
  - Data Analysis Agent explanation follows after
  - User sees numbers fast
- **Execution progress**: Simple progress indicator ("Executing code..." + spinner)
  - No real-time logs (keeps UX clean)
  - No time estimates (avoid complexity)

### Resource Limits & Timeouts
- **Timeout**: 60 seconds per query
  - Balances complex analysis with reasonable wait time
  - Handles most pandas operations on medium datasets
- **Memory limit**: 1GB per sandbox
  - Aligns with 50MB file upload limit
  - Supports datasets with 10K-100K rows comfortably
- **CPU limit**: Single CPU core
  - Prevents expensive multi-threaded operations
  - Predictable costs, simpler code generation (no parallelism)
- **When limits hit**: Auto-retry with simpler code
  - Coding Agent regenerates with constraint info ("avoid sorting entire dataset")
  - One retry attempt for resource limits, then fail
  - Clear error message if still fails after retry

### Retry & Error Handling
- **Max retries**: 2 retries (3 total attempts)
  - Maintains Phase 3 default (`max_steps=3`)
  - Balances success rate with user patience
- **Retry triggers**: Retry on all errors
  - Code validation failures → retry
  - Execution errors (syntax, runtime) → retry
  - Resource limits (timeout, OOM) → retry with simpler code
  - Even E2B failures → retry (maximizes success rate)
- **User communication**: Show retry events during streaming
  - "Code validation failed, regenerating..."
  - "Timeout, trying simpler approach..."
  - User understands what's happening (transparency over silence)
- **Exhausted retries**: Show final error with helpful suggestions
  - "Unable to complete analysis. Try: filtering data first, breaking into simpler questions, or rephrasing query."
  - Actionable guidance for non-technical users
  - No code display to avoid confusion

### Claude's Discretion
- Exact error messages for different failure types
- E2B API configuration details (SDK setup, authentication)
- Sandbox environment variables and file mounting specifics
- Logging and monitoring instrumentation for sandbox events

</decisions>

<specifics>
## Specific Ideas

- Architecture must support runtime swapping: SandboxRuntime interface allows switching from E2B to Docker + gVisor without rewriting agent logic
- Cost efficiency is key: No idle sandboxes, single CPU core, 1GB memory aligns with MVP budget constraints
- UX should feel like ChatGPT Code Interpreter: Auto-execute, clean progress indicators, no technical clutter
- Security is non-negotiable: E2B microVM isolation prevents container escapes, multi-layer defense from Phase 3 AST validation remains

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

E2B cost monitoring and usage quotas mentioned but will be addressed during implementation (not a UX decision).

</deferred>

---

*Phase: 05-sandbox-security---code-execution*
*Context gathered: 2026-02-03*
