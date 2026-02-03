"""AST-based code validation for generated Python code.

This module provides safety validation for AI-generated code before execution.
Uses Python's ast module to analyze code structure and enforce security policies.
"""

import ast
from dataclasses import dataclass
from typing import Optional

from app.agents.config import (
    get_allowed_libraries,
    get_unsafe_builtins,
    get_unsafe_modules,
    get_unsafe_operations,
)


@dataclass
class ValidationResult:
    """Result of code validation.

    Attributes:
        is_valid: True if code passed all validation checks.
        errors: List of error messages describing validation failures.
    """

    is_valid: bool
    errors: list[str]


class CodeValidator(ast.NodeVisitor):
    """AST NodeVisitor that validates code against security policies.

    Checks for:
    - Disallowed module imports (e.g., os, subprocess, sys)
    - Unsafe builtin functions (e.g., eval, exec, __import__)
    - Unsafe operations (e.g., open, file I/O, input)
    """

    def __init__(
        self,
        allowed_modules: set[str],
        unsafe_builtins: set[str],
        unsafe_modules: set[str],
        unsafe_operations: set[str],
    ):
        """Initialize validator with security policies.

        Args:
            allowed_modules: Set of allowed module names (e.g., {'pandas', 'numpy'}).
            unsafe_builtins: Set of unsafe builtin function names (e.g., {'eval', 'exec'}).
            unsafe_modules: Set of unsafe module names (e.g., {'os', 'subprocess'}).
            unsafe_operations: Set of unsafe operation names (e.g., {'open', 'input'}).
        """
        self.allowed_modules = allowed_modules
        self.unsafe_builtins = unsafe_builtins
        self.unsafe_modules = unsafe_modules
        self.unsafe_operations = unsafe_operations
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements (e.g., 'import pandas').

        Args:
            node: AST Import node.
        """
        for alias in node.names:
            module_name = alias.name.split(".")[0]  # Get root module (os.path -> os)

            # Check if module is explicitly unsafe
            if module_name in self.unsafe_modules:
                self.errors.append(f"Disallowed module: {alias.name}")
            # Check if module is in allowlist
            elif module_name not in self.allowed_modules:
                self.errors.append(f"Module not in allowlist: {alias.name}")

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements (e.g., 'from pandas import DataFrame').

        Args:
            node: AST ImportFrom node.
        """
        if node.module:
            module_name = node.module.split(".")[0]  # Get root module

            # Check if module is explicitly unsafe
            if module_name in self.unsafe_modules:
                self.errors.append(f"Disallowed module: {node.module}")
            # Check if module is in allowlist
            elif module_name not in self.allowed_modules:
                self.errors.append(f"Module not in allowlist: {node.module}")

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call expressions.

        Checks for unsafe builtin functions and operations.

        Args:
            node: AST Call node.
        """
        # Check for unsafe builtins (eval, exec, __import__, compile, etc.)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.unsafe_builtins:
                self.errors.append(f"Unsafe builtin: {func_name}")
            elif func_name in self.unsafe_operations:
                self.errors.append(f"Unsafe operation: {func_name}")

        # Check for unsafe operations via attribute access (e.g., obj.open())
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in self.unsafe_operations:
                self.errors.append(f"Unsafe operation: {attr_name}")

        self.generic_visit(node)


def validate_code(
    code: str, allowlist: Optional[dict] = None
) -> ValidationResult:
    """Validate Python code against security policies.

    Checks:
    1. Syntax correctness (code must parse without SyntaxError)
    2. Import allowlist (only allowed libraries may be imported)
    3. Unsafe builtins (eval, exec, __import__, compile, globals, locals)
    4. Unsafe operations (open, input, file I/O)

    Args:
        code: Python code string to validate.
        allowlist: Optional custom allowlist dict. If None, loads from config.

    Returns:
        ValidationResult with is_valid flag and error messages.

    Examples:
        >>> result = validate_code("import pandas as pd")
        >>> result.is_valid
        True

        >>> result = validate_code("import os")
        >>> result.is_valid
        False
        >>> "os" in result.errors[0].lower()
        True

        >>> result = validate_code("eval('1+1')")
        >>> result.is_valid
        False
        >>> "eval" in result.errors[0].lower()
        True
    """
    # Load security policies
    if allowlist is None:
        allowed_modules = get_allowed_libraries()
        unsafe_builtins = get_unsafe_builtins()
        unsafe_modules = get_unsafe_modules()
        unsafe_operations = get_unsafe_operations()
    else:
        allowed_modules = set(allowlist.get("allowed_libraries", []))
        unsafe_builtins = set(allowlist.get("unsafe_builtins", []))
        unsafe_modules = set(allowlist.get("unsafe_modules", []))
        unsafe_operations = set(allowlist.get("unsafe_operations", []))

    # Check syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Syntax error: {e.msg} (line {e.lineno})"],
        )

    # Validate with AST visitor
    validator = CodeValidator(
        allowed_modules=allowed_modules,
        unsafe_builtins=unsafe_builtins,
        unsafe_modules=unsafe_modules,
        unsafe_operations=unsafe_operations,
    )
    validator.visit(tree)

    # Return result
    if validator.errors:
        return ValidationResult(is_valid=False, errors=validator.errors)
    else:
        return ValidationResult(is_valid=True, errors=[])
