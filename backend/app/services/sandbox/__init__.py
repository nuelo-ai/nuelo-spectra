"""Sandbox service for secure Python code execution.

This module provides a Protocol-based abstraction for swappable sandbox
backends (E2B Cloud, Docker+gVisor, etc.) and structured execution results.

Public API:
    SandboxRuntime: Protocol defining execute() and cleanup() interface
    E2BSandboxRuntime: E2B Cloud implementation using Firecracker microVMs
    ExecutionResult: Structured execution output with stdout/stderr/error/timing
"""
from .runtime import SandboxRuntime
from .e2b_runtime import E2BSandboxRuntime
from .models import ExecutionResult

__all__ = [
    "SandboxRuntime",
    "E2BSandboxRuntime",
    "ExecutionResult",
]
