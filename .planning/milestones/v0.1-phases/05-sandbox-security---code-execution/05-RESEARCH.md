# Phase 5: Sandbox Security & Code Execution - Research

**Researched:** 2026-02-03
**Domain:** E2B Cloud microVM sandboxing, Python code execution security
**Confidence:** HIGH

## Summary

E2B Cloud provides managed microVM sandboxes with Firecracker isolation for secure Python code execution. The platform offers a Python SDK (`e2b-code-interpreter` v2.4.1) that supports creating ephemeral sandboxes, executing code with resource limits, and retrieving structured results. The standard pattern is one sandbox per execution (create → execute → destroy) with automatic timeout-based cleanup.

The research confirms E2B as a production-ready solution for AI-generated code execution, with strong isolation guarantees from Firecracker microVMs (~150ms boot time), flexible resource limits (configurable timeout, memory, CPU), and a well-documented Python SDK. The abstraction layer should use Python's Protocol or ABC pattern to enable future runtime swapping (E2B to gVisor/Docker) without rewriting agent logic.

Security is multi-layered: Firecracker provides hardware-level isolation (separate kernel, memory space), E2B enforces resource limits (timeout, memory, CPU), and the sandbox prevents network access and file system writes outside workspace. Error handling follows structured patterns with separate stdout, stderr, and error objects for comprehensive diagnostics.

**Primary recommendation:** Use `e2b-code-interpreter` SDK with context manager pattern (`with Sandbox.create() as sandbox`) for automatic cleanup, implement SandboxRuntime Protocol for abstraction, and structure execution results with clear separation of data (stdout), errors (stderr + error object), and metadata (execution time, resource usage).

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| e2b-code-interpreter | 2.4.1+ | Managed microVM sandboxes with Python code execution | Official E2B SDK, battle-tested for AI code execution, handles lifecycle/cleanup automatically |
| e2b (base SDK) | 2.8.1+ | Core E2B functionality (filesystem, commands, process management) | Underlying SDK for code-interpreter, provides lower-level control |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing | stdlib | Protocol/ABC definitions for SandboxRuntime abstraction | Define runtime interface for swappable implementations |
| asyncio | stdlib | Async sandbox operations in FastAPI | Non-blocking execution in async API endpoints |
| contextlib | stdlib | Context manager patterns for cleanup | Ensure sandbox cleanup even on exceptions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| E2B Cloud | Docker + gVisor (self-hosted) | E2B: zero maintenance, fast boot, managed infrastructure. gVisor: full control, no vendor lock-in, higher ops burden |
| E2B Cloud | Firecracker (self-hosted) | E2B: managed, SDK included. Firecracker: lowest latency possible, complete control, requires infrastructure expertise |
| Code Interpreter SDK | Base E2B SDK | Code Interpreter: higher-level, built for pandas/matplotlib. Base SDK: more control, manual file operations |

**Installation:**
```bash
pip install e2b-code-interpreter
```

**Environment Setup:**
```bash
# Required: E2B API key from dashboard
export E2B_API_KEY=e2b_***
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── services/
│   └── sandbox/
│       ├── __init__.py
│       ├── runtime.py           # SandboxRuntime Protocol definition
│       ├── e2b_runtime.py       # E2BSandboxRuntime implementation
│       └── models.py            # ExecutionResult, ExecutionError models
├── agents/
│   └── coding_agent.py          # Uses SandboxRuntime abstraction
└── config/
    └── sandbox_config.py        # Timeout, memory, CPU limits
```

### Pattern 1: SandboxRuntime Abstraction (Protocol-Based)
**What:** Define runtime interface using Python Protocol for swappable implementations
**When to use:** When you need to support multiple sandbox backends (E2B now, gVisor later) without code changes
**Example:**
```python
# Source: Python typing docs + E2B SDK patterns
from typing import Protocol, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Structured execution result from sandbox"""
    stdout: list[str]           # Lines printed to stdout
    stderr: list[str]           # Lines printed to stderr
    results: list[dict]         # Cell results (last line value, plots, etc.)
    error: Optional[dict]       # {"name": "ValueError", "value": "...", "traceback": "..."}
    execution_time_ms: int      # Duration for monitoring

class SandboxRuntime(Protocol):
    """Abstract interface for code execution sandboxes"""

    def execute(
        self,
        code: str,
        timeout: float = 60.0,
        data_file: Optional[bytes] = None,
        data_filename: Optional[str] = None
    ) -> ExecutionResult:
        """Execute Python code in isolated sandbox with optional data file"""
        ...

    def cleanup(self) -> None:
        """Release sandbox resources"""
        ...
```

### Pattern 2: E2B Implementation with Context Manager
**What:** Implement E2BSandboxRuntime with automatic cleanup via context manager
**When to use:** Primary implementation for Phase 5, guarantees cleanup even on exceptions
**Example:**
```python
# Source: E2B SDK reference + context manager best practices
from e2b_code_interpreter import Sandbox
from contextlib import contextmanager

class E2BSandboxRuntime:
    """E2B Cloud implementation of SandboxRuntime"""

    def __init__(self, timeout_seconds: float = 60.0):
        self.timeout_seconds = timeout_seconds
        self._sandbox = None

    def execute(
        self,
        code: str,
        timeout: float = 60.0,
        data_file: Optional[bytes] = None,
        data_filename: Optional[str] = None
    ) -> ExecutionResult:
        """Execute code in fresh E2B sandbox"""
        import time
        start_time = time.time()

        with Sandbox.create(timeout=int(timeout)) as sandbox:
            # Upload data file if provided
            if data_file and data_filename:
                sandbox.filesystem.write(f"/home/user/{data_filename}", data_file)

            # Execute code
            execution = sandbox.run_code(code, timeout=timeout)

            # Convert E2B execution object to standard result
            return ExecutionResult(
                stdout=execution.logs.stdout if execution.logs else [],
                stderr=execution.logs.stderr if execution.logs else [],
                results=execution.results or [],
                error=execution.error,  # Already in {"name", "value", "traceback"} format
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
```

### Pattern 3: One Sandbox Per Execution Lifecycle
**What:** Create fresh sandbox, execute once, destroy immediately (no reuse)
**When to use:** Every code execution request (default pattern)
**Example:**
```python
# Source: E2B lifecycle best practices + CONTEXT.md decisions
async def execute_code_handler(code: str, file_id: str):
    """FastAPI endpoint pattern for sandbox execution"""

    # 1. Create fresh runtime (no reuse)
    runtime = E2BSandboxRuntime(timeout_seconds=60.0)

    try:
        # 2. Execute (sandbox created internally)
        result = runtime.execute(
            code=code,
            timeout=60.0,
            data_file=get_csv_bytes(file_id),
            data_filename="data.csv"
        )
        # 3. Sandbox destroyed automatically by context manager

        return result

    except Exception as e:
        # Sandbox cleanup happens via context manager even on error
        raise
```

### Pattern 4: Retry Logic with Error Context
**What:** Retry execution on failures, pass error context to agent for simpler code generation
**When to use:** When timeout, OOM, or execution errors occur (max 2 retries)
**Example:**
```python
# Source: Retry pattern best practices 2025 + CONTEXT.md decisions
from typing import Optional

async def execute_with_retry(
    runtime: SandboxRuntime,
    code: str,
    max_retries: int = 2,
    previous_error: Optional[str] = None
) -> ExecutionResult:
    """Execute with retry on failure, passing error context to agent"""

    for attempt in range(max_retries + 1):  # 0, 1, 2 = 3 total attempts
        try:
            result = runtime.execute(code, timeout=60.0)

            # Check for execution errors (Python exceptions)
            if result.error:
                if attempt < max_retries:
                    # Retry with error context for agent
                    error_msg = f"{result.error['name']}: {result.error['value']}"
                    # Agent will regenerate code with this context
                    continue
                else:
                    # Exhausted retries
                    return result

            # Success
            return result

        except TimeoutError as e:
            if attempt < max_retries:
                # Retry with simpler code (agent gets "timeout" signal)
                previous_error = "timeout"
                continue
            else:
                raise

        except MemoryError as e:
            if attempt < max_retries:
                # Retry with memory-efficient code
                previous_error = "memory_limit"
                continue
            else:
                raise
```

### Pattern 5: File Upload and Result Retrieval
**What:** Upload CSV data to sandbox, execute pandas code, retrieve results as structured data
**When to use:** Every data analysis query (standard flow)
**Example:**
```python
# Source: E2B data analyst blog post + filesystem API
def execute_analysis(csv_bytes: bytes, analysis_code: str) -> ExecutionResult:
    """Upload data, analyze, retrieve results"""

    with Sandbox.create(timeout=60) as sandbox:
        # 1. Upload data file
        sandbox.filesystem.write("/home/user/data.csv", csv_bytes)

        # 2. Execute analysis (code references 'data.csv')
        code_with_output = f"""
import pandas as pd
import json

# User's analysis code
{analysis_code}

# Serialize result for retrieval
if 'result_df' in locals():
    print("__RESULT_JSON__")
    print(result_df.to_json(orient='records'))
"""

        execution = sandbox.run_code(code_with_output, timeout=60.0)

        # 3. Parse results from stdout
        stdout_text = "\n".join(execution.logs.stdout)
        if "__RESULT_JSON__" in stdout_text:
            json_start = stdout_text.index("__RESULT_JSON__") + len("__RESULT_JSON__\n")
            result_json = stdout_text[json_start:]
            parsed_result = json.loads(result_json)

        return ExecutionResult(
            stdout=execution.logs.stdout,
            stderr=execution.logs.stderr,
            results=[{"type": "dataframe", "data": parsed_result}],
            error=execution.error,
            execution_time_ms=0
        )
```

### Anti-Patterns to Avoid
- **Reusing sandboxes across executions:** Creates state leakage between queries, violates isolation guarantee. Always create fresh sandbox per execution.
- **Forgetting context manager:** Without `with` statement, sandboxes may not cleanup on exceptions, causing resource leaks and billing issues.
- **Blocking async FastAPI routes:** Using synchronous `Sandbox.create()` in async FastAPI endpoint blocks event loop. Use async wrapper or run in thread pool.
- **Not passing error context to agent:** Generic "execution failed" forces agent to guess. Pass specific error message so agent can fix the issue.
- **Setting timeout=0 for all executions:** Disables timeout protection, allows runaway processes. Only use timeout=0 for known long-running tasks.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MicroVM orchestration | Custom Firecracker manager with API server | E2B Cloud | Handles boot, networking, process isolation, cleanup, monitoring. Complex infrastructure with edge cases (orphaned VMs, network conflicts, kernel updates). |
| Execution result parsing | Custom stdout parser with regex | E2B Execution object | Structured `logs.stdout`, `logs.stderr`, `results`, `error` fields. Handles matplotlib plots, dataframe display, error tracebacks automatically. |
| Timeout enforcement | Python `signal.alarm()` or threading.Timer | E2B timeout parameter | Signal-based timeouts don't work in sandboxed environments. E2B enforces at VM level, guarantees termination. |
| Resource limits (memory, CPU) | Python `resource.setrlimit()` | E2B sandbox resource config | User-space limits can be bypassed. MicroVM limits are hardware-enforced at hypervisor level. |
| Sandbox cleanup | Manual `kill()` calls with try/finally | Context manager (`with Sandbox.create()`) | Exception during execution can skip cleanup. Context manager guarantees cleanup via `__exit__`. |
| File upload to sandbox | SCP, SFTP, or custom file API | `sandbox.filesystem.write()` | E2B provides in-memory file writes without network overhead. No SSH setup, no port management. |
| Error recovery retry logic | Custom retry with sleep() | Adaptive retry with error context | Blind retries waste time/money. Pass error to agent so it generates better code, not just retry same code. |

**Key insight:** Sandbox security is deceptively complex. Custom solutions miss critical edge cases (container escapes, race conditions in cleanup, process orphaning). E2B's managed microVMs provide defense-in-depth: Firecracker isolation + resource limits + automatic cleanup. Focus on application logic, not infrastructure.

## Common Pitfalls

### Pitfall 1: Sandbox Not Cleaned Up on Exception
**What goes wrong:** Exception during execution causes sandbox to stay alive, consuming resources and incurring costs
**Why it happens:** Manual cleanup code in `finally` block is error-prone, easy to forget, doesn't handle all exception types
**How to avoid:** Always use context manager pattern: `with Sandbox.create() as sandbox:`
**Warning signs:** E2B dashboard shows sandboxes running longer than expected, billing costs higher than usage

### Pitfall 2: Blocking Async FastAPI Route with Synchronous E2B Call
**What goes wrong:** `Sandbox.create()` is synchronous, blocks FastAPI event loop, causes entire API to freeze during sandbox boot
**Why it happens:** E2B Python SDK doesn't expose async methods, must integrate with asyncio manually
**How to avoid:** Wrap synchronous sandbox operations in `asyncio.to_thread()` or use thread pool executor
**Warning signs:** FastAPI endpoint responds slowly, other endpoints timeout during sandbox execution, event loop warnings in logs
```python
# WRONG - blocks event loop
@app.post("/execute")
async def execute_code(code: str):
    with Sandbox.create() as sandbox:  # BLOCKS
        result = sandbox.run_code(code)
    return result

# RIGHT - runs in thread pool
@app.post("/execute")
async def execute_code(code: str):
    def _execute():
        with Sandbox.create() as sandbox:
            return sandbox.run_code(code)

    result = await asyncio.to_thread(_execute)
    return result
```

### Pitfall 3: Not Handling E2B Service Downtime
**What goes wrong:** E2B API unavailable, all code executions fail, user sees generic 500 error
**Why it happens:** No fallback or degradation strategy, assumes E2B always available
**How to avoid:** Catch E2B connection errors, return user-friendly "Service temporarily unavailable" message, log for retry
**Warning signs:** Sudden spike in 500 errors, E2B connection timeouts in logs, no execution attempts succeeding
```python
from e2b.exceptions import E2BException

try:
    with Sandbox.create() as sandbox:
        result = sandbox.run_code(code)
except E2BException as e:
    # E2B service unavailable
    return {
        "error": "Code execution service temporarily unavailable. Please try again.",
        "retry": True
    }
```

### Pitfall 4: Forgetting to Upload Data File Before Execution
**What goes wrong:** Code references `data.csv` but file doesn't exist in sandbox, execution fails with FileNotFoundError
**Why it happens:** Sandbox has isolated filesystem, doesn't have access to host files or database
**How to avoid:** Always upload data files before executing code that references them, verify upload succeeded
**Warning signs:** Execution errors like "FileNotFoundError: data.csv", code works locally but fails in sandbox
```python
# Upload CSV data before execution
csv_bytes = get_csv_from_db(file_id)
sandbox.filesystem.write("/home/user/data.csv", csv_bytes)

# Verify file exists
files = sandbox.filesystem.list("/home/user")
assert "data.csv" in [f.name for f in files]

# Now execute code that uses data.csv
execution = sandbox.run_code("import pandas as pd; df = pd.read_csv('data.csv')")
```

### Pitfall 5: Using Timeout But Not Handling TimeoutError
**What goes wrong:** Code execution times out (60s limit), exception propagates to user as 500 error
**Why it happens:** Timeout parameter raises exception, not captured in execution.error object
**How to avoid:** Wrap execution in try/except for timeout exceptions, treat as retryable error with simpler code
**Warning signs:** Users report "Request failed" after exactly 60 seconds, no error details provided
```python
import time

try:
    start = time.time()
    execution = sandbox.run_code(code, timeout=60.0)
    duration = time.time() - start

except TimeoutError:
    # Timeout is retryable - regenerate with simpler code
    return ExecutionResult(
        stdout=[],
        stderr=["Execution timed out after 60 seconds"],
        results=[],
        error={
            "name": "TimeoutError",
            "value": "Code execution exceeded 60 second limit. Try simpler operations or filter data first.",
            "traceback": ""
        },
        execution_time_ms=60000
    )
```

### Pitfall 6: Not Parsing Execution Results Correctly
**What goes wrong:** Execution succeeds but results not extracted, user sees "Analysis complete" with no data
**Why it happens:** `execution.results` contains matplotlib plots, not dataframe data. Need to serialize dataframe in code.
**How to avoid:** Modify generated code to explicitly serialize results (df.to_json(), df.to_dict()), parse from stdout
**Warning signs:** Users report "no results shown" but execution succeeds, stdout contains data but not displayed

### Pitfall 7: Memory Limit Too Low for Dataset Size
**What goes wrong:** Pandas loads 50MB CSV, operations cause OOM (1GB limit), sandbox killed
**Why it happens:** Pandas expands data in memory (CSV 50MB → DataFrame 200MB with dtypes), operations create copies
**How to avoid:** Document dataset size limits (10K-100K rows), guide users to filter data first, retry with chunking
**Warning signs:** Execution fails on medium datasets, error is silent (no traceback), sandbox terminates abruptly

### Pitfall 8: Exposing E2B API Key in Logs
**What goes wrong:** API key logged with sandbox creation, exposed in CloudWatch/monitoring, security risk
**Why it happens:** Default logging includes environment variables, E2B_API_KEY gets logged
**How to avoid:** Configure logging to redact E2B_API_KEY, use secrets manager, never log sandbox creation parameters
**Warning signs:** API key visible in application logs, environment variables logged on startup

## Code Examples

Verified patterns from official sources:

### Basic Sandbox Creation and Execution
```python
# Source: E2B PyPI documentation
from e2b_code_interpreter import Sandbox

with Sandbox.create() as sandbox:
    sandbox.run_code("x = 1")
    execution = sandbox.run_code("x += 1; x")
    print(execution.text)  # outputs 2
```

### Complete FastAPI Integration with Error Handling
```python
# Source: E2B FastAPI patterns + async best practices 2025
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

app = FastAPI()

class ExecuteRequest(BaseModel):
    code: str
    file_id: str

@app.post("/execute")
async def execute_code(req: ExecuteRequest):
    """Execute Python code in E2B sandbox (non-blocking)"""

    def _execute_sync():
        try:
            with Sandbox.create(timeout=60) as sandbox:
                # Upload data file
                csv_bytes = get_csv_from_db(req.file_id)
                sandbox.filesystem.write("/home/user/data.csv", csv_bytes)

                # Execute code
                execution = sandbox.run_code(req.code, timeout=60.0)

                # Handle execution errors (Python exceptions)
                if execution.error:
                    return {
                        "success": False,
                        "error": execution.error,
                        "stdout": execution.logs.stdout,
                        "stderr": execution.logs.stderr
                    }

                # Success
                return {
                    "success": True,
                    "results": execution.results,
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr
                }

        except TimeoutError:
            return {
                "success": False,
                "error": {"name": "TimeoutError", "value": "Execution exceeded 60s"},
                "retry_with_simpler_code": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": {"name": type(e).__name__, "value": str(e)}
            }

    # Run in thread pool to avoid blocking event loop
    result = await asyncio.to_thread(_execute_sync)
    return result
```

### Sandbox Timeout Configuration
```python
# Source: E2B sandbox lifecycle docs
from e2b_code_interpreter import Sandbox

# Create sandbox with 5 minute timeout (auto-destroy after 5 min)
with Sandbox.create(timeout=300) as sandbox:

    # Execute code with 60s timeout (raises TimeoutError if exceeded)
    execution = sandbox.run_code(code, timeout=60.0)

    # For long-running operations, disable execution timeout
    execution = sandbox.run_code(long_code, timeout=0)  # No timeout
```

### Error Object Structure
```python
# Source: E2B code interpreter execution docs
execution = sandbox.run_code("x = undefined_variable")

if execution.error:
    # Error structure:
    # {
    #   "name": "NameError",
    #   "value": "name 'undefined_variable' is not defined",
    #   "traceback": "Traceback (most recent call last):\n  File ..."
    # }

    error_name = execution.error["name"]      # "NameError"
    error_msg = execution.error["value"]      # "name 'undefined_variable' is not defined"
    traceback = execution.error["traceback"]  # Full traceback string
```

### File Upload and Download
```python
# Source: E2B filesystem API docs + data analyst blog
from e2b_code_interpreter import Sandbox

with Sandbox.create() as sandbox:
    # Upload file (bytes or string)
    csv_data = open("local_data.csv", "rb").read()
    sandbox.filesystem.write("/home/user/data.csv", csv_data)

    # Verify upload
    files = sandbox.filesystem.list("/home/user")
    print([f.name for f in files])  # ['data.csv']

    # Execute code that uses file
    execution = sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/home/user/data.csv')
df.head()
""")

    # Download result file (if code generates output)
    result_bytes = sandbox.filesystem.read("/home/user/output.csv")
```

### Structured Result Extraction
```python
# Source: E2B execution object structure
execution = sandbox.run_code("""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df.sum())  # Prints to stdout

plt.plot([1, 2, 3])
plt.savefig('plot.png')
plt.show()  # Creates artifact

df  # Last line value becomes result
""")

# Stdout: printed output
stdout_lines = execution.logs.stdout  # ["a    6", "b    15", ...]

# Stderr: warnings/errors
stderr_lines = execution.logs.stderr  # []

# Results: last line value + artifacts (plots)
results = execution.results  # [
    # {"type": "dataframe", "data": ...},
    # {"type": "image", "format": "png", "data": "..."}
# ]

# Error: Python exception if any
error = execution.error  # None if success
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Docker containers with seccomp | Firecracker microVMs | 2018-2020 | Stronger isolation (separate kernel vs shared kernel), faster boot (~150ms vs ~2s), eliminates container escape vulnerabilities |
| Manual sandbox lifecycle | Context managers (`with` statement) | Python 2.6+ (2008), widely adopted 2020+ | Guarantees cleanup, reduces resource leaks, simpler error handling |
| Synchronous-only execution | AsyncSandbox (async/await) | E2B v2.x (2024+) | Non-blocking FastAPI integration, better concurrency, no event loop blocking |
| Fixed resource limits | Configurable CPU/memory per sandbox | E2B 2025+ | Right-size resources for workload (1GB for MVP, 2GB+ for large datasets), cost optimization |
| Generic retry logic | Error context passing to agent | AI agent era (2024+) | Intelligent retries (agent fixes code, not blind retry), higher success rate, better UX |

**Deprecated/outdated:**
- **Docker-only sandboxing:** Container escapes still occur (e.g., CVE-2019-5736). MicroVMs eliminate shared kernel vulnerabilities.
- **Thread-based timeouts:** `threading.Timer()` doesn't work across process boundaries. VM-level timeouts guarantee termination.
- **SSH-based file upload:** Adds network overhead and attack surface. In-memory filesystem writes are faster and more secure.
- **E2B v1.x SDK:** Legacy API (pre-2024). Use v2.x+ for context managers, better error handling, filesystem API.

## Open Questions

Things that couldn't be fully resolved:

1. **E2B AsyncSandbox availability and maturity**
   - What we know: E2B v2.x SDK references exist, but async methods not fully documented in official docs
   - What's unclear: Is `AsyncSandbox.create()` stable for production? Any gotchas with asyncio integration?
   - Recommendation: Start with synchronous `Sandbox.create()` wrapped in `asyncio.to_thread()` for Phase 5. Migrate to `AsyncSandbox` if/when docs confirm production-ready status.

2. **Exact E2B resource limit enforcement mechanism**
   - What we know: E2B provides timeout, CPU, memory limits via Firecracker
   - What's unclear: How does memory limit behave when exceeded? Hard kill or graceful OOM error? Is OOM error catchable?
   - Recommendation: Test memory limit behavior in dev environment (load 2GB data in 1GB sandbox). Document observed behavior for retry logic.

3. **E2B pricing for 60s timeout pattern**
   - What we know: E2B charges per second (~$0.000014/sec for 1 vCPU). 60s execution = ~$0.00084.
   - What's unclear: Billing for short-lived sandboxes (<1s)? Minimum charge per sandbox? Batch pricing?
   - Recommendation: Monitor E2B costs in production. Document cost per query for budgeting. Consider shorter timeout (30s) if costs exceed budget.

4. **SandboxRuntime abstraction: Protocol vs ABC?**
   - What we know: Protocol = structural typing (duck typing), ABC = nominal typing (explicit inheritance). Protocol is lighter weight.
   - What's unclear: Does Protocol support shared implementation logic? Or do we need ABC for common retry/error handling?
   - Recommendation: Start with Protocol for interface definition (Phase 5). If shared logic needed for future gVisor implementation, migrate to ABC with Protocol as public interface.

5. **E2B network isolation details**
   - What we know: E2B sandboxes are isolated, prevent network access (referenced in security docs)
   - What's unclear: Does E2B block all outbound connections? Can sandboxes reach public internet (e.g., pip install)? What about localhost?
   - Recommendation: Verify network isolation in testing. Document allowed/blocked destinations. If pip install needed, use E2B templates with pre-installed packages.

## Sources

### Primary (HIGH confidence)
- [E2B Official Documentation](https://e2b.dev/docs) - Getting started, SDK reference, concepts
- [E2B Code Interpreter PyPI](https://pypi.org/project/e2b-code-interpreter/) - Version 2.4.1 (Nov 26, 2025), installation, requirements
- [E2B GitHub - Code Interpreter SDK](https://github.com/e2b-dev/code-interpreter) - Official repository, usage examples
- [E2B SDK Reference - Python](https://e2b.dev/docs/sdk-reference/code-interpreter-python-sdk/v1.0.5/sandbox) - API methods, parameters
- [E2B Sandbox Lifecycle Documentation](https://e2b.dev/docs/sandbox) - Timeout, cleanup, resource management
- [E2B Execution Object Structure](https://e2b.dev/docs/legacy/code-interpreter/execution) - stdout, stderr, error, results fields
- [Python typing - ABC and Protocol](https://docs.python.org/3/library/abc.html) - Abstract base classes, Protocol definitions
- [Python Context Managers](https://docs.python.org/3/library/contextlib.html) - with statement, cleanup patterns

### Secondary (MEDIUM confidence)
- [E2B Blog - AI Data Analyst with LangChain](https://e2b.dev/blog/build-ai-data-analyst-with-langchain-and-e2b) - File upload/download patterns, error handling
- [E2B Blog - Python Guide for Claude Code](https://e2b.dev/blog/python-guide-run-claude-code-in-an-e2b-sandbox) - Sandbox.create() usage, timeout configuration
- [E2B Pricing Page](https://e2b.dev/pricing) - Cost model ($0.05/hour for 1 vCPU), per-second billing
- [NVIDIA Blog - Sandbox Security for Agentic Workflows](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk) - Security best practices, microVM benefits
- [Koyeb Blog - Top Sandbox Platforms 2026](https://www.koyeb.com/blog/top-sandbox-code-execution-platforms-for-ai-code-execution-2026) - E2B comparison, isolation mechanisms
- [FastAPI Async Programming](https://fastapi.tiangolo.com/async/) - Async/await patterns, event loop best practices
- [Code Sandboxes for LLMs - Amir's Blog](https://amirmalik.net/2025/03/07/code-sandboxes-for-llm-ai-agents) - FastAPI + AsyncKernelManager patterns, gVisor integration

### Tertiary (LOW confidence - requires validation)
- [Better Stack - Best Sandbox Runners 2026](https://betterstack.com/community/comparisons/best-sandbox-runners/) - E2B alternatives comparison
- [Codex Agentic Patterns - Sandbox Escalation](https://artvandelay.github.io/codex-agentic-patterns/learning-material/16-sandbox-escalation/) - Retry patterns for sandbox failures
- [Mastering Retry Logic Agents 2025](https://sparkco.ai/blog/mastering-retry-logic-agents-a-deep-dive-into-2025-best-practices) - Adaptive retry with error context
- [Kubernetes Agent Sandbox](https://opensource.googleblog.com/2025/11/unleashing-autonomous-ai-agents-why-kubernetes-needs-a-new-standard-for-agent-execution.html) - Multi-backend abstraction patterns (gVisor, Kata)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - E2B SDK verified via PyPI, official docs, active GitHub repo with recent releases
- Architecture patterns: HIGH - Protocol/ABC patterns from Python stdlib docs, context manager is Python standard, E2B lifecycle verified
- Pitfalls: MEDIUM - Common issues inferred from E2B GitHub issues, FastAPI async patterns, general sandbox gotchas (not all E2B-specific)

**Research date:** 2026-02-03
**Valid until:** ~30 days (March 2026) - E2B is stable, Python patterns are evergreen, but pricing/features may change quarterly
