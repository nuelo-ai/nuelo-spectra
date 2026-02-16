"""E2B sandbox Plotly availability verification tests.

These integration tests verify:
1. Plotly is installed and importable in E2B sandbox (INFRA-03)
2. fig.to_json() produces valid Plotly JSON schema
3. Dual-key output contract works: {"result": ..., "chart": ...}
4. Backward-compatible single-key output still works

Requires E2B API key (E2B_API_KEY env var).
"""

import json
import os

import pytest

from app.services.sandbox import E2BSandboxRuntime

# Mark all tests in this file as integration tests (require E2B API key)
pytestmark = pytest.mark.skipif(
    not os.getenv("E2B_API_KEY"),
    reason="E2B_API_KEY not set (integration test)",
)


class TestPlotlyAvailability:
    """Verify Plotly is available and functional in E2B sandbox."""

    def test_plotly_version(self):
        """Verify Plotly is importable and version is 5.x or 6.x in E2B sandbox.

        This is the primary INFRA-03 verification: confirms that Plotly is
        pre-installed in the E2B code interpreter sandbox and returns a
        supported version string.
        """
        runtime = E2BSandboxRuntime(timeout_seconds=15.0)
        result = runtime.execute(
            code="import plotly; print(plotly.__version__)",
            timeout=15.0,
        )

        assert result.success, f"Plotly import failed: {result.error}"
        assert result.stdout, "No version output received"

        version = result.stdout[0].strip()
        major = int(version.split(".")[0])
        assert major in (5, 6), f"Unexpected Plotly major version: {version} (expected 5.x or 6.x)"
        print(f"Plotly available in E2B sandbox: version {version}")

    def test_plotly_to_json_produces_valid_chart(self):
        """Verify fig.to_json() produces valid JSON with data and layout keys.

        Creates a simple bar chart in E2B sandbox, serializes via to_json(),
        and validates the output contract: {"result": ..., "chart": ...} with
        Plotly JSON schema structure (data array + layout object).
        """
        runtime = E2BSandboxRuntime(timeout_seconds=15.0)

        code = """\
import plotly.express as px
import plotly.io as pio
import json

# Create simple bar chart with synthetic data
fig = px.bar(x=['A', 'B', 'C'], y=[1, 3, 2], title='Test Chart')

# Serialize to JSON
chart_json = pio.to_json(fig)

# Output using dual-key contract
print(json.dumps({"result": {"test": "ok"}, "chart": json.loads(chart_json)}))
"""

        result = runtime.execute(code=code, timeout=15.0)

        assert result.success, f"Chart generation failed: {result.error}"
        assert result.stdout, "No output received"

        # Parse the last stdout line as JSON
        output_line = result.stdout[-1].strip()
        parsed = json.loads(output_line)

        # Verify dual-key contract
        assert "result" in parsed, "Missing 'result' key in output"
        assert "chart" in parsed, "Missing 'chart' key in output"

        # Verify chart JSON structure
        chart = parsed["chart"]
        assert "data" in chart, "Chart JSON missing 'data' field"
        assert "layout" in chart, "Chart JSON missing 'layout' field"
        assert isinstance(chart["data"], list), "Chart 'data' should be a list"
        assert len(chart["data"]) > 0, "Chart 'data' should have at least one trace"

        # Verify chart title was preserved
        assert chart["layout"]["title"]["text"] == "Test Chart", "Chart title mismatch"

        print(f"Chart JSON structure valid ({len(json.dumps(chart))} bytes)")

    def test_plotly_output_contract_backward_compatible(self):
        """Verify non-chart code producing only {"result": ...} still works.

        This confirms backward compatibility: code that outputs only the
        tabular result without a chart key continues to execute successfully
        in the E2B sandbox.
        """
        runtime = E2BSandboxRuntime(timeout_seconds=15.0)

        code = """\
import json

# Simulate existing non-chart code output
result_data = [{"col1": "A", "col2": 10}, {"col1": "B", "col2": 20}]
print(json.dumps({"result": result_data}))
"""

        result = runtime.execute(code=code, timeout=15.0)

        assert result.success, f"Execution failed: {result.error}"
        assert result.stdout, "No output received"

        # Parse output
        output_line = result.stdout[-1].strip()
        parsed = json.loads(output_line)

        # Verify single-key contract works
        assert "result" in parsed, "Missing 'result' key in output"
        assert "chart" not in parsed, "Unexpected 'chart' key in backward-compat output"

        # Verify result data integrity
        assert len(parsed["result"]) == 2, "Result should have 2 rows"
        assert parsed["result"][0]["col1"] == "A", "Result data mismatch"

        print("Backward-compatible single-key output contract works.")
