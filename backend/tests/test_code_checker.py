"""Tests for AST-based code validation (Code Checker Agent).

Tests follow RED-GREEN-REFACTOR TDD pattern.
Testing all validation scenarios before implementation.
"""

import pytest
from app.agents.code_checker import ValidationResult, validate_code


class TestSyntaxValidation:
    """Test syntax error detection."""

    def test_syntax_error_unclosed_parenthesis(self):
        """Should reject code with syntax errors."""
        code = "def foo("
        result = validate_code(code)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "syntax" in result.errors[0].lower() or "unexpected" in result.errors[0].lower()

    def test_syntax_error_invalid_indentation(self):
        """Should reject code with indentation errors."""
        code = "def foo():\nprint('test')"
        result = validate_code(code)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_valid_syntax(self):
        """Should accept syntactically valid code."""
        code = "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})"
        result = validate_code(code)
        # May fail for other reasons, but not syntax
        if not result.is_valid:
            assert not any("syntax" in err.lower() for err in result.errors)


class TestAllowedImports:
    """Test import allowlist validation."""

    def test_allowed_import_pandas(self):
        """Should accept pandas import (in allowlist)."""
        code = "import pandas"
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_allowed_import_pandas_as(self):
        """Should accept pandas with alias."""
        code = "import pandas as pd"
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_allowed_import_numpy(self):
        """Should accept numpy import."""
        code = "import numpy as np"
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_allowed_import_multiple(self):
        """Should accept multiple allowed imports."""
        code = "import pandas\nimport numpy\nimport datetime"
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_allowed_from_import(self):
        """Should accept from imports of allowed modules."""
        code = "from datetime import datetime"
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestDisallowedImports:
    """Test detection of disallowed imports."""

    def test_disallowed_import_os(self):
        """Should reject os module import."""
        code = "import os"
        result = validate_code(code)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("os" in err.lower() for err in result.errors)

    def test_disallowed_import_subprocess(self):
        """Should reject subprocess module import."""
        code = "import subprocess"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("subprocess" in err.lower() for err in result.errors)

    def test_disallowed_import_sys(self):
        """Should reject sys module import."""
        code = "import sys"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("sys" in err.lower() for err in result.errors)

    def test_disallowed_from_import_subprocess(self):
        """Should reject from subprocess import."""
        code = "from subprocess import run"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("subprocess" in err.lower() for err in result.errors)

    def test_mixed_allowed_and_disallowed(self):
        """Should reject code with mix of allowed and disallowed imports."""
        code = "import pandas\nimport os"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("os" in err.lower() for err in result.errors)

    def test_disallowed_pathlib(self):
        """Should reject pathlib import."""
        code = "from pathlib import Path"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("pathlib" in err.lower() for err in result.errors)

    def test_disallowed_pickle(self):
        """Should reject pickle import."""
        code = "import pickle"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("pickle" in err.lower() for err in result.errors)


class TestUnsafeBuiltins:
    """Test detection of unsafe builtin functions."""

    def test_unsafe_builtin_eval(self):
        """Should reject code using eval()."""
        code = "result = eval('1+1')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("eval" in err.lower() for err in result.errors)

    def test_unsafe_builtin_exec(self):
        """Should reject code using exec()."""
        code = "exec('print(1)')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("exec" in err.lower() for err in result.errors)

    def test_unsafe_builtin___import__(self):
        """Should reject code using __import__()."""
        code = "__import__('os')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("__import__" in err.lower() or "import" in err.lower() for err in result.errors)

    def test_unsafe_builtin_compile(self):
        """Should reject code using compile()."""
        code = "compile('pass', '', 'exec')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("compile" in err.lower() for err in result.errors)

    def test_unsafe_builtin_globals(self):
        """Should reject code using globals()."""
        code = "g = globals()"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("globals" in err.lower() for err in result.errors)

    def test_unsafe_builtin_locals(self):
        """Should reject code using locals()."""
        code = "l = locals()"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("locals" in err.lower() for err in result.errors)


class TestUnsafeOperations:
    """Test detection of unsafe operations."""

    def test_unsafe_operation_open(self):
        """Should reject code using open()."""
        code = "f = open('file.txt')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("open" in err.lower() for err in result.errors)

    def test_unsafe_operation_open_with_mode(self):
        """Should reject open() with write mode."""
        code = "with open('test.txt', 'w') as f:\n    f.write('test')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("open" in err.lower() for err in result.errors)

    def test_unsafe_operation_input(self):
        """Should reject code using input()."""
        code = "user_input = input('Enter: ')"
        result = validate_code(code)
        assert result.is_valid is False
        assert any("input" in err.lower() for err in result.errors)


class TestValidComplexCode:
    """Test that valid code using allowed libraries passes validation."""

    def test_valid_pandas_dataframe(self):
        """Should accept valid pandas DataFrame code."""
        code = """import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
result = df.describe()"""
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_numpy_operations(self):
        """Should accept valid numpy operations."""
        code = """import numpy as np
arr = np.array([1, 2, 3, 4, 5])
mean = np.mean(arr)
std = np.std(arr)"""
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_datetime_operations(self):
        """Should accept valid datetime operations."""
        code = """from datetime import datetime
now = datetime.now()
formatted = now.strftime('%Y-%m-%d')"""
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_pandas_with_math(self):
        """Should accept pandas with math operations."""
        code = """import pandas as pd
import math
df = pd.DataFrame({'values': [1, 4, 9, 16]})
df['sqrt'] = df['values'].apply(math.sqrt)"""
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_multiple_operations(self):
        """Should accept complex valid code with multiple operations."""
        code = """import pandas as pd
import numpy as np
from datetime import datetime

data = {'date': [datetime(2024, 1, i) for i in range(1, 6)],
        'values': [10, 20, 30, 40, 50]}
df = pd.DataFrame(data)
df['rolling_mean'] = df['values'].rolling(window=2).mean()
summary = df.describe()"""
        result = validate_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidationResult:
    """Test ValidationResult dataclass structure."""

    def test_validation_result_has_is_valid(self):
        """ValidationResult should have is_valid attribute."""
        code = "import pandas"
        result = validate_code(code)
        assert hasattr(result, 'is_valid')
        assert isinstance(result.is_valid, bool)

    def test_validation_result_has_errors(self):
        """ValidationResult should have errors attribute."""
        code = "import pandas"
        result = validate_code(code)
        assert hasattr(result, 'errors')
        assert isinstance(result.errors, list)

    def test_validation_result_errors_are_strings(self):
        """ValidationResult errors should be list of strings."""
        code = "import os"
        result = validate_code(code)
        assert isinstance(result.errors, list)
        for error in result.errors:
            assert isinstance(error, str)


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_empty_code(self):
        """Should handle empty code string."""
        code = ""
        result = validate_code(code)
        # Empty code is technically valid (no violations)
        assert result.is_valid is True

    def test_whitespace_only(self):
        """Should handle whitespace-only code."""
        code = "   \n   \n   "
        result = validate_code(code)
        assert result.is_valid is True

    def test_comments_only(self):
        """Should accept code with only comments."""
        code = "# This is a comment\n# Another comment"
        result = validate_code(code)
        assert result.is_valid is True

    def test_allowed_import_with_comments(self):
        """Should accept allowed imports with comments."""
        code = """# Import pandas
import pandas as pd
# Create dataframe
df = pd.DataFrame()"""
        result = validate_code(code)
        assert result.is_valid is True

    def test_nested_function_calls(self):
        """Should handle nested function calls correctly."""
        code = """import pandas as pd
import numpy as np
df = pd.DataFrame({'values': np.random.randn(10)})"""
        result = validate_code(code)
        assert result.is_valid is True
