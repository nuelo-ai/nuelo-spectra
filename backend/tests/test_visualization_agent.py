"""Tests for Visualization Agent (Phase 21 Plan 1).

Tests cover:
- build_data_shape_hints: pure unit tests for data shape analysis
- visualization_agent_node: async tests with full mocking (no live API keys)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.visualization import (
    visualization_agent_node,
    build_data_shape_hints,
    _MAX_DATA_CHARS,
)
from app.agents.llm_factory import EmptyLLMResponseError


# ============================================================================
# Test Group 1: build_data_shape_hints (pure unit tests)
# ============================================================================


class TestBuildDataShapeHints:
    """Tests for build_data_shape_hints helper function."""

    def test_parses_list_of_dicts(self):
        """Should report row count, column count, and per-column info for list of dicts."""
        data = '[{"region": "East", "sales": 50000}, {"region": "West", "sales": 35000}]'
        result = build_data_shape_hints(data)
        assert "2 rows" in result
        assert "2 columns" in result
        assert "region" in result
        assert "sales" in result
        assert "categorical" in result
        assert "numeric" in result

    def test_parses_single_dict(self):
        """Should report key count and key names for a single dict."""
        data = '{"total": 85000, "count": 2}'
        result = build_data_shape_hints(data)
        assert "single dict" in result
        assert "2 keys" in result

    def test_handles_invalid_json(self):
        """Should return 'unable to parse' for invalid JSON."""
        result = build_data_shape_hints("not json at all")
        assert "unable to parse" in result

    def test_handles_empty_string(self):
        """Should return 'unable to parse' for empty string."""
        result = build_data_shape_hints("")
        assert "unable to parse" in result

    def test_detects_numeric_columns(self):
        """Should detect numeric type for columns with all numeric values."""
        data = '[{"value": 100}, {"value": 200}, {"value": 300}]'
        result = build_data_shape_hints(data)
        assert "numeric" in result

    def test_detects_categorical_columns(self):
        """Should detect categorical type for columns with string values."""
        data = '[{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]'
        result = build_data_shape_hints(data)
        assert "categorical" in result

    def test_reports_unique_value_count(self):
        """Should report correct unique value count for columns."""
        data = '[{"color": "red", "qty": 1}, {"color": "blue", "qty": 2}, {"color": "red", "qty": 3}, {"color": "green", "qty": 4}, {"color": "blue", "qty": 5}]'
        result = build_data_shape_hints(data)
        # color has 3 unique values: red, blue, green
        assert "3 unique" in result


# ============================================================================
# Test Group 2: visualization_agent_node (async tests with mocking)
# ============================================================================


@pytest.fixture
def sample_state():
    """Sample ChatAgentState for visualization agent tests."""
    return {
        "execution_result": '[{"region": "East", "sales": 50000}, {"region": "West", "sales": 35000}]',
        "analysis": "Sales are highest in the East region at $50K.",
        "user_query": "Show me a bar chart of sales by region",
        "chart_hint": "bar",
        "visualization_requested": True,
    }


def _get_viz_patches():
    """Return dict of patch context managers for visualization_agent_node dependencies."""
    return {
        "get_stream_writer": patch(
            "app.agents.visualization.get_stream_writer",
            return_value=MagicMock(),
        ),
        "get_settings": patch("app.agents.visualization.get_settings"),
        "get_agent_provider": patch(
            "app.agents.visualization.get_agent_provider",
            return_value="anthropic",
        ),
        "get_agent_model": patch(
            "app.agents.visualization.get_agent_model",
            return_value="claude-sonnet-4-20250514",
        ),
        "get_agent_temperature": patch(
            "app.agents.visualization.get_agent_temperature",
            return_value=0.0,
        ),
        "get_api_key_for_provider": patch(
            "app.agents.visualization.get_api_key_for_provider",
            return_value="test-key",
        ),
        "get_agent_max_tokens": patch(
            "app.agents.visualization.get_agent_max_tokens",
            return_value=4000,
        ),
        "get_agent_prompt": patch(
            "app.agents.visualization.get_agent_prompt",
            return_value="Test prompt {execution_result} {user_query} {chart_hint} {analysis} {data_shape_hints}",
        ),
        "get_llm": patch("app.agents.visualization.get_llm"),
        "validate_llm_response": patch(
            "app.agents.visualization.validate_llm_response",
            return_value="```python\nimport plotly.express as px\nfig = px.bar(data, x='region', y='sales')\n```",
        ),
    }


class TestVisualizationAgentNode:
    """Tests for visualization_agent_node async function."""

    @pytest.mark.asyncio
    async def test_returns_chart_code_key(self, sample_state):
        """Agent should return dict with chart_code key as a string."""
        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patches["validate_llm_response"]:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="```python\nfig = px.bar()\n```")
            mock_get_llm.return_value = mock_llm

            result = await visualization_agent_node(sample_state)

            assert "chart_code" in result
            assert isinstance(result["chart_code"], str)

    @pytest.mark.asyncio
    async def test_calls_llm_with_messages(self, sample_state):
        """Agent should invoke LLM with SystemMessage and HumanMessage."""
        from langchain_core.messages import SystemMessage, HumanMessage

        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patches["validate_llm_response"]:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="code")
            mock_get_llm.return_value = mock_llm

            await visualization_agent_node(sample_state)

            assert mock_llm.ainvoke.called
            call_args = mock_llm.ainvoke.call_args[0][0]
            assert len(call_args) == 2
            assert isinstance(call_args[0], SystemMessage)
            assert isinstance(call_args[1], HumanMessage)

    @pytest.mark.asyncio
    async def test_extracts_code_from_response(self, sample_state):
        """Agent should extract Python code from markdown-formatted LLM response."""
        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patch(
                 "app.agents.visualization.validate_llm_response",
                 return_value="```python\nimport plotly.express as px\nfig = px.bar(data, x='a', y='b')\n```",
             ):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="code")
            mock_get_llm.return_value = mock_llm

            result = await visualization_agent_node(sample_state)

            assert "import plotly.express" in result["chart_code"]

    @pytest.mark.asyncio
    async def test_handles_empty_llm_response(self, sample_state):
        """Agent should return chart_error when LLM returns empty response."""
        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patch(
                 "app.agents.visualization.validate_llm_response",
                 side_effect=EmptyLLMResponseError("anthropic", "claude-sonnet-4-20250514", "visualization"),
             ):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="")
            mock_get_llm.return_value = mock_llm

            result = await visualization_agent_node(sample_state)

            assert result["chart_code"] == ""
            assert result["chart_error"] != ""
            assert "empty LLM response" in result["chart_error"]

    @pytest.mark.asyncio
    async def test_truncates_large_execution_result(self, sample_state):
        """Agent should not crash with oversized execution_result and should truncate it."""
        sample_state["execution_result"] = "x" * (_MAX_DATA_CHARS + 5000)

        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patches["validate_llm_response"]:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="code")
            mock_get_llm.return_value = mock_llm

            result = await visualization_agent_node(sample_state)

            # Should not crash
            assert "chart_code" in result
            # LLM should have been invoked (truncation didn't break the flow)
            assert mock_llm.ainvoke.called

    @pytest.mark.asyncio
    async def test_sends_sse_event(self, sample_state):
        """Agent should emit visualization_started SSE event."""
        patches = _get_viz_patches()
        with patch("app.agents.visualization.get_stream_writer") as mock_get_writer, \
             patches["get_settings"], \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["get_llm"] as mock_get_llm, \
             patches["validate_llm_response"]:
            mock_writer = MagicMock()
            mock_get_writer.return_value = mock_writer

            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="code")
            mock_get_llm.return_value = mock_llm

            await visualization_agent_node(sample_state)

            # Verify writer was called with visualization_started event
            mock_writer.assert_called()
            event = mock_writer.call_args_list[0][0][0]
            assert event["type"] == "visualization_started"

    @pytest.mark.asyncio
    async def test_uses_visualization_agent_name_for_config(self, sample_state):
        """Agent should use 'visualization' as agent name for all config lookups."""
        patches = _get_viz_patches()
        with patches["get_stream_writer"], patches["get_settings"], \
             patches["get_agent_provider"] as mock_provider, \
             patches["get_agent_model"] as mock_model, \
             patches["get_agent_temperature"] as mock_temp, \
             patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"] as mock_max_tokens, \
             patches["get_agent_prompt"] as mock_prompt, \
             patches["get_llm"] as mock_get_llm, \
             patches["validate_llm_response"]:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="code")
            mock_get_llm.return_value = mock_llm

            await visualization_agent_node(sample_state)

            mock_provider.assert_called_with("visualization")
            mock_model.assert_called_with("visualization")
            mock_temp.assert_called_with("visualization")
            mock_max_tokens.assert_called_with("visualization")
            mock_prompt.assert_called_with("visualization")
