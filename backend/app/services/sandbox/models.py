"""Sandbox execution result models."""
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of code execution in a sandbox.

    Captures all outputs, errors, and timing information from a single
    code execution attempt. This is a structured alternative to raising
    exceptions, allowing retry logic to inspect error details.

    Attributes:
        stdout: Lines printed to stdout during execution
        stderr: Lines printed to stderr during execution
        results: Cell results (last line values, plots, etc.)
        error: Structured error dict with name, value, traceback (or None)
        execution_time_ms: Duration of execution in milliseconds
    """
    stdout: list[str]
    stderr: list[str]
    results: list[dict]
    error: dict | None
    execution_time_ms: int

    @property
    def success(self) -> bool:
        """True if execution completed without error."""
        return self.error is None
