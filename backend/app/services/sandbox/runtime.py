"""SandboxRuntime Protocol for swappable sandbox backends.

This Protocol defines the interface for secure code execution environments.
Implementations can use E2B Cloud, Docker+gVisor, or other sandbox solutions
without requiring changes to agent code.

Protocol pattern (vs ABC) enables duck typing and lighter-weight contracts.
"""
from typing import Protocol
from .models import ExecutionResult


class SandboxRuntime(Protocol):
    """Protocol for secure code execution environments.

    Implementations must provide two methods:
    - execute(): Run Python code and return structured results
    - cleanup(): Release any resources held by the runtime

    Usage:
        runtime: SandboxRuntime = E2BSandboxRuntime(timeout_seconds=60)
        result = runtime.execute(code="print(1+1)", timeout=30.0)
        if result.success:
            print(result.stdout)
        runtime.cleanup()
    """

    def execute(
        self,
        code: str,
        timeout: float = 60.0,
        data_file: bytes | None = None,
        data_filename: str | None = None,
    ) -> ExecutionResult:
        """Execute Python code in the sandbox.

        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            data_file: Optional file data to upload to sandbox
            data_filename: Filename for uploaded data (required if data_file provided)

        Returns:
            ExecutionResult with stdout, stderr, results, error, timing

        Note:
            This method should NEVER raise exceptions. All errors must be
            captured and returned as ExecutionResult with error dict populated.
            This enables retry logic in the calling agent to inspect failures.
        """
        ...

    def cleanup(self) -> None:
        """Release resources held by the runtime.

        Called after execution completes or times out. Implementations using
        context managers may leave this as a no-op.
        """
        ...
