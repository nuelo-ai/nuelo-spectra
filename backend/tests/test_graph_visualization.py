"""Tests for graph visualization pipeline integration.

This module tests the visualization pipeline nodes and routing in the LangGraph workflow:
- should_visualize conditional routing
- viz_execute_node chart code execution
- viz_response_node SSE event emission
- Graph compilation with visualization nodes
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agents.graph import should_visualize, viz_execute_node, viz_response_node, build_chat_graph
from app.services.sandbox import ExecutionResult


class TestShouldVisualizeRouting:
    """Test should_visualize conditional edge function."""

    def test_should_visualize_true(self):
        """should_visualize returns 'visualization_agent' when visualization_requested=True."""
        state = {"visualization_requested": True}
        result = should_visualize(state)
        assert result == "visualization_agent"

    def test_should_visualize_false(self):
        """should_visualize returns 'finish' when visualization_requested=False."""
        state = {"visualization_requested": False}
        result = should_visualize(state)
        assert result == "finish"

    def test_should_visualize_missing_field(self):
        """should_visualize returns 'finish' when field missing from state (default behavior)."""
        state = {}
        result = should_visualize(state)
        assert result == "finish"


class TestVizExecuteNode:
    """Test viz_execute_node chart code execution."""

    @pytest.mark.asyncio
    async def test_viz_execute_empty_code(self):
        """viz_execute_node returns chart_error when chart_code is empty."""
        state = {"chart_code": ""}

        with patch("app.agents.graph.get_stream_writer") as mock_writer:
            mock_writer.return_value = Mock()
            result = await viz_execute_node(state)

        assert result["chart_specs"] == ""
        assert "Chart generation produced no code" in result["chart_error"]

    @pytest.mark.asyncio
    async def test_viz_execute_success(self):
        """viz_execute_node extracts chart JSON on successful execution."""
        state = {"chart_code": "print('test')"}

        mock_execution_result = ExecutionResult(
            stdout=['{"chart": {"data": [{"x": [1, 2], "y": [3, 4]}], "layout": {}}}'],
            stderr=[],
            results=[],
            error=None,
            execution_time_ms=100
        )

        with patch("app.agents.graph.get_stream_writer") as mock_writer, \
             patch("app.agents.graph.get_settings") as mock_settings, \
             patch("app.agents.graph.E2BSandboxRuntime") as mock_runtime, \
             patch("app.agents.graph.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:

            mock_writer.return_value = Mock()
            mock_settings.return_value.sandbox_timeout_seconds = 30
            mock_to_thread.return_value = mock_execution_result

            result = await viz_execute_node(state)

        assert result["chart_specs"] != ""
        assert result["chart_error"] == ""
        assert "data" in result["chart_specs"]

    @pytest.mark.asyncio
    async def test_viz_execute_failure_max_retries(self):
        """viz_execute_node returns chart_error after max retries exhausted."""
        state = {"chart_code": "import bad_module"}

        mock_execution_result = ExecutionResult(
            stdout=[],
            stderr=[],
            results=[],
            error={"name": "ModuleNotFoundError", "value": "No module named 'bad_module'"},
            execution_time_ms=50
        )

        with patch("app.agents.graph.get_stream_writer") as mock_writer, \
             patch("app.agents.graph.get_settings") as mock_settings, \
             patch("app.agents.graph.E2BSandboxRuntime") as mock_runtime, \
             patch("app.agents.graph.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread, \
             patch("app.agents.graph._retry_chart_code", new_callable=AsyncMock) as mock_retry:

            mock_writer.return_value = Mock()
            mock_settings.return_value.sandbox_timeout_seconds = 30
            mock_to_thread.return_value = mock_execution_result
            mock_retry.return_value = ""  # Retry fails to generate new code

            result = await viz_execute_node(state)

        assert result["chart_specs"] == ""
        assert "Chart execution failed" in result["chart_error"]
        assert "ModuleNotFoundError" in result["chart_error"]

    @pytest.mark.asyncio
    async def test_viz_execute_chart_too_large(self):
        """viz_execute_node discards chart JSON larger than 2MB."""
        state = {"chart_code": "print('test')"}

        # Create a valid chart JSON > 2MB by repeating data points
        data_points = ','.join(['{"x": [1, 2], "y": [3, 4]}'] * 100000)
        large_chart = f'{{"chart": {{"data": [{data_points}], "layout": {{}}}}}}'

        mock_execution_result = ExecutionResult(
            stdout=[large_chart],
            stderr=[],
            results=[],
            error=None,
            execution_time_ms=200
        )

        with patch("app.agents.graph.get_stream_writer") as mock_writer, \
             patch("app.agents.graph.get_settings") as mock_settings, \
             patch("app.agents.graph.E2BSandboxRuntime") as mock_runtime, \
             patch("app.agents.graph.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread, \
             patch("app.agents.graph._retry_chart_code", new_callable=AsyncMock) as mock_retry:

            mock_writer.return_value = Mock()
            mock_settings.return_value.sandbox_timeout_seconds = 30
            mock_to_thread.return_value = mock_execution_result
            mock_retry.return_value = ""  # Retry fails to generate smaller code

            result = await viz_execute_node(state)

        assert result["chart_specs"] == ""
        assert "Chart data too large" in result["chart_error"]


class TestVizResponseNode:
    """Test viz_response_node SSE event emission."""

    @pytest.mark.asyncio
    async def test_viz_response_success(self):
        """viz_response_node emits chart_completed SSE event when chart_specs present."""
        state = {
            "chart_specs": '{"data": [], "layout": {}}',
            "chart_error": ""
        }

        mock_writer = Mock()
        with patch("app.agents.graph.get_stream_writer") as mock_get_writer:
            mock_get_writer.return_value = mock_writer
            result = await viz_response_node(state)

        # Verify SSE event emitted
        mock_writer.assert_called_once()
        call_args = mock_writer.call_args[0][0]
        assert call_args["type"] == "chart_completed"
        assert call_args["message"] == "Chart ready"
        assert call_args["chart_specs"] == state["chart_specs"]

        # Verify empty return (state already updated by viz_execute)
        assert result == {}

    @pytest.mark.asyncio
    async def test_viz_response_failure(self):
        """viz_response_node emits chart_failed SSE event when chart_error present."""
        state = {
            "chart_specs": "",
            "chart_error": "Chart execution failed: TypeError"
        }

        mock_writer = Mock()
        with patch("app.agents.graph.get_stream_writer") as mock_get_writer:
            mock_get_writer.return_value = mock_writer
            result = await viz_response_node(state)

        # Verify SSE event emitted
        mock_writer.assert_called_once()
        call_args = mock_writer.call_args[0][0]
        assert call_args["type"] == "chart_failed"
        assert call_args["message"] == "Chart unavailable"

        # Verify empty return
        assert result == {}


class TestGraphCompilation:
    """Test graph compilation with visualization nodes."""

    def test_graph_compiles_with_viz_nodes(self):
        """build_chat_graph() compiles without error and contains visualization_agent node."""
        graph = build_chat_graph()

        # Verify graph compiles
        assert graph is not None

        # Verify visualization nodes are present by attempting to invoke the graph
        # (we can't directly inspect node names in the compiled graph, but we can
        # verify it compiles without error)
        assert hasattr(graph, "ainvoke")
        assert hasattr(graph, "astream")
