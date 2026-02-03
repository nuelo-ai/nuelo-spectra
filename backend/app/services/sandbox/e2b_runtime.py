"""E2B Cloud implementation of SandboxRuntime.

Uses E2B's Firecracker microVM-based code interpreter for secure Python
execution. Each sandbox is created fresh per execution with guaranteed
cleanup via context manager.
"""
import time
from e2b_code_interpreter import Sandbox
from .models import ExecutionResult


class E2BSandboxRuntime:
    """E2B Cloud implementation of SandboxRuntime Protocol.

    Creates fresh Firecracker microVMs for each execution. Supports file
    upload for data analysis workflows. Wraps all E2B errors into structured
    ExecutionResult (never propagates exceptions).

    Usage:
        runtime = E2BSandboxRuntime(timeout_seconds=60)
        result = runtime.execute(code="print(1+1)", timeout=30.0)
        assert result.success
        assert "2" in result.stdout[0]
    """

    def __init__(self, timeout_seconds: float = 60.0):
        """Initialize E2B runtime with default timeout.

        Args:
            timeout_seconds: Default timeout for sandbox operations
        """
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        code: str,
        timeout: float = 60.0,
        data_file: bytes | None = None,
        data_filename: str | None = None,
    ) -> ExecutionResult:
        """Execute Python code in an E2B sandbox.

        Creates a fresh Firecracker microVM, optionally uploads data file,
        executes code, and returns structured results. All errors are caught
        and returned as ExecutionResult (never raised).

        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            data_file: Optional file data to upload to sandbox
            data_filename: Filename for uploaded data (required if data_file provided)

        Returns:
            ExecutionResult with stdout, stderr, results, error, timing
        """
        start_time = time.time()

        try:
            # Create fresh sandbox with timeout
            with Sandbox.create(timeout=int(timeout)) as sandbox:
                # Upload data file if provided
                if data_file and data_filename:
                    sandbox.filesystem.write(
                        f"/home/user/{data_filename}",
                        data_file
                    )

                # Execute code
                execution = sandbox.run_code(code, timeout=timeout)

                # Convert E2B execution object to ExecutionResult
                stdout = execution.logs.stdout if execution.logs else []
                stderr = execution.logs.stderr if execution.logs else []

                # Convert results to dicts (handle both dict and object results)
                results = []
                if execution.results:
                    for r in execution.results:
                        if hasattr(r, '__dict__'):
                            results.append(r.__dict__)
                        else:
                            results.append(r)

                # Convert error to dict if present
                error = None
                if execution.error:
                    error = {
                        "name": execution.error.name,
                        "value": execution.error.value,
                        "traceback": execution.error.traceback
                    }

                execution_time_ms = int((time.time() - start_time) * 1000)

                return ExecutionResult(
                    stdout=stdout,
                    stderr=stderr,
                    results=results,
                    error=error,
                    execution_time_ms=execution_time_ms
                )

        except TimeoutError as e:
            # Timeout from E2B SDK
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                stdout=[],
                stderr=[],
                results=[],
                error={
                    "name": "TimeoutError",
                    "value": f"Execution exceeded {timeout}s limit",
                    "traceback": ""
                },
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            # Generic exception from E2B SDK or network issues
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_name = type(e).__name__
            error_value = str(e)

            return ExecutionResult(
                stdout=[],
                stderr=[],
                results=[],
                error={
                    "name": error_name,
                    "value": error_value,
                    "traceback": ""
                },
                execution_time_ms=execution_time_ms
            )

    def cleanup(self) -> None:
        """Release resources held by the runtime.

        No-op for E2B implementation since Sandbox.create() context manager
        handles cleanup automatically.
        """
        pass
