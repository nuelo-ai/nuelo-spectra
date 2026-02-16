"""Unit tests for chart intelligence decision logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.data_analysis import _evaluate_visualization_need
from app.agents.state import RoutingDecision


# ============================================================================
# Tests for RoutingDecision chart_hint field
# ============================================================================


def test_routing_decision_chart_hint_default():
    """RoutingDecision with no chart_hint defaults to empty string."""
    decision = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="test reasoning",
        context_summary="test context"
    )
    assert decision.chart_hint == ""


def test_routing_decision_chart_hint_bar():
    """RoutingDecision with chart_hint='bar' preserves value."""
    decision = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="test reasoning",
        context_summary="test context",
        chart_hint="bar"
    )
    assert decision.chart_hint == "bar"


def test_routing_decision_chart_hint_empty():
    """RoutingDecision with chart_hint='' is valid."""
    decision = RoutingDecision(
        route="MEMORY_SUFFICIENT",
        reasoning="answer from history",
        context_summary="previous result available",
        chart_hint=""
    )
    assert decision.chart_hint == ""


# ============================================================================
# Tests for _evaluate_visualization_need
# ============================================================================


@pytest.mark.asyncio
async def test_viz_need_memory_sufficient_returns_false():
    """MEMORY_SUFFICIENT route skips visualization (no LLM call needed)."""
    routing = RoutingDecision(
        route="MEMORY_SUFFICIENT",
        reasoning="answer from history",
        context_summary="test"
    )
    state = {
        "routing_decision": routing,
        "execution_result": "some data",
        "user_query": "what was the total?",
        "chart_hint": "",
    }
    result = await _evaluate_visualization_need(state, "Analysis text")
    assert result is False


@pytest.mark.asyncio
async def test_viz_need_no_execution_result_returns_false():
    """Empty execution_result returns False."""
    routing = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="generate new code",
        context_summary=""
    )
    state = {
        "routing_decision": routing,
        "execution_result": "",
        "user_query": "show sales by region",
        "chart_hint": "bar",
    }
    result = await _evaluate_visualization_need(state, "Analysis text")
    assert result is False


@pytest.mark.asyncio
async def test_viz_need_error_result_returns_false():
    """execution_result starting with 'Error:' returns False."""
    routing = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="generate new code",
        context_summary=""
    )
    state = {
        "routing_decision": routing,
        "execution_result": "Error: Column not found",
        "user_query": "show sales trends",
        "chart_hint": "line",
    }
    result = await _evaluate_visualization_need(state, "Analysis text")
    assert result is False


@pytest.mark.asyncio
@patch("app.agents.data_analysis.get_llm")
@patch("app.agents.data_analysis.get_settings")
@patch("app.agents.data_analysis.get_agent_provider")
@patch("app.agents.data_analysis.get_agent_model")
@patch("app.agents.data_analysis.get_api_key_for_provider")
async def test_viz_need_llm_yes_returns_true(
    mock_api_key, mock_model, mock_provider, mock_settings, mock_get_llm
):
    """Mock LLM returning 'YES' produces True."""
    # Setup mocks
    mock_provider.return_value = "anthropic"
    mock_model.return_value = "claude-sonnet-4"
    mock_api_key.return_value = "test-key"
    mock_settings.return_value = MagicMock()

    # Mock LLM response
    mock_llm_instance = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "YES"
    mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
    mock_get_llm.return_value = mock_llm_instance

    routing = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="generate new code",
        context_summary=""
    )
    state = {
        "routing_decision": routing,
        "execution_result": '{"result": [{"category": "A", "value": 100}, {"category": "B", "value": 200}]}',
        "user_query": "compare sales by category",
        "chart_hint": "bar",
    }
    result = await _evaluate_visualization_need(state, "Sales analysis by category")
    assert result is True


@pytest.mark.asyncio
@patch("app.agents.data_analysis.get_llm")
@patch("app.agents.data_analysis.get_settings")
@patch("app.agents.data_analysis.get_agent_provider")
@patch("app.agents.data_analysis.get_agent_model")
@patch("app.agents.data_analysis.get_api_key_for_provider")
async def test_viz_need_llm_no_returns_false(
    mock_api_key, mock_model, mock_provider, mock_settings, mock_get_llm
):
    """Mock LLM returning 'NO' produces False."""
    # Setup mocks
    mock_provider.return_value = "anthropic"
    mock_model.return_value = "claude-sonnet-4"
    mock_api_key.return_value = "test-key"
    mock_settings.return_value = MagicMock()

    # Mock LLM response
    mock_llm_instance = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "NO"
    mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
    mock_get_llm.return_value = mock_llm_instance

    routing = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="generate new code",
        context_summary=""
    )
    state = {
        "routing_decision": routing,
        "execution_result": '{"result": 42}',
        "user_query": "what is the total?",
        "chart_hint": "",
    }
    result = await _evaluate_visualization_need(state, "The total is 42")
    assert result is False


@pytest.mark.asyncio
@patch("app.agents.data_analysis.get_llm")
@patch("app.agents.data_analysis.get_settings")
@patch("app.agents.data_analysis.get_agent_provider")
@patch("app.agents.data_analysis.get_agent_model")
@patch("app.agents.data_analysis.get_api_key_for_provider")
async def test_viz_need_llm_failure_returns_false(
    mock_api_key, mock_model, mock_provider, mock_settings, mock_get_llm
):
    """LLM exception falls back to False (non-fatal)."""
    # Setup mocks
    mock_provider.return_value = "anthropic"
    mock_model.return_value = "claude-sonnet-4"
    mock_api_key.return_value = "test-key"
    mock_settings.return_value = MagicMock()

    # Mock LLM to raise exception
    mock_llm_instance = AsyncMock()
    mock_llm_instance.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))
    mock_get_llm.return_value = mock_llm_instance

    routing = RoutingDecision(
        route="NEW_ANALYSIS",
        reasoning="generate new code",
        context_summary=""
    )
    state = {
        "routing_decision": routing,
        "execution_result": '{"result": [1, 2, 3]}',
        "user_query": "show distribution",
        "chart_hint": "histogram",
    }
    result = await _evaluate_visualization_need(state, "Distribution analysis")
    assert result is False
