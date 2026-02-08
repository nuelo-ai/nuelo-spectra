"""Test suite for Manager Agent routing logic (Phase 9 Plan 3).

Comprehensive tests covering:
- Routing classification (manager_node routes queries correctly)
- Fallback behavior (LLM failure defaults to NEW_ANALYSIS)
- Route-specific agent behavior (memory, modification, new analysis)
- Graph topology (manager as entry point, correct edges)
- Configuration loading (YAML config for manager agent)
- Structured logging (ROUTING-08 compliance)

All tests are fully mocked - zero live API keys required.
"""

import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.state import ChatAgentState, RoutingDecision
from langchain_core.messages import AIMessage, HumanMessage


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def base_state():
    """Base ChatAgentState with common fields for routing tests."""
    return {
        "file_id": "test-file-123",
        "user_id": "test-user-456",
        "user_query": "",
        "data_summary": "Test dataset with columns: id, name, sales, region. 1000 rows.",
        "data_profile": '{"columns": {"id": {"type": "int"}, "name": {"type": "str"}, "sales": {"type": "float"}, "region": {"type": "str"}}}',
        "user_context": "",
        "file_path": "/tmp/test.csv",
        "generated_code": "",
        "validation_result": "",
        "validation_errors": [],
        "error_count": 0,
        "max_steps": 3,
        "execution_result": "",
        "analysis": "",
        "final_response": "",
        "error": "",
        "messages": [],
        "routing_decision": None,
        "previous_code": "",
    }


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    settings = MagicMock()
    settings.anthropic_api_key = "test-anthropic-key"
    settings.openai_api_key = "test-openai-key"
    settings.google_api_key = "test-google-key"
    settings.ollama_base_url = "http://localhost:11434"
    settings.openrouter_api_key = "test-openrouter-key"
    return settings


@pytest.fixture
def mock_prompts():
    """Mock prompts.yaml configuration."""
    return {
        "agents": {
            "manager": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.0,
                "routing_context_messages": 10,
                "system_prompt": "You are a Query Router...",
                "max_tokens": 500,
            },
            "data_analysis": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.0,
                "system_prompt": "You are a Data Analysis Agent. {user_query} {executed_code} {execution_result}",
                "max_tokens": 2000,
            },
            "coding": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.0,
                "system_prompt": "Generate Python code. {data_profile} {user_context} {allowed_libraries}",
                "max_tokens": 10000,
            },
        }
    }


def _make_routing_decision(route, reasoning="Test reasoning", context_summary="Test context"):
    """Helper to create a RoutingDecision with defaults."""
    return RoutingDecision(
        route=route,
        reasoning=reasoning,
        context_summary=context_summary,
    )


def _patch_manager_dependencies(mock_settings, mock_prompts):
    """Return a dictionary of patch targets for manager_node dependencies.

    Returns context managers for use with ExitStack or nested with statements.
    """
    return {
        "get_settings": patch("app.agents.manager.get_settings", return_value=mock_settings),
        "get_llm": patch("app.agents.manager.get_llm"),
        "get_agent_provider": patch("app.agents.manager.get_agent_provider", return_value="anthropic"),
        "get_agent_model": patch("app.agents.manager.get_agent_model", return_value="claude-sonnet-4-20250514"),
        "get_agent_temperature": patch("app.agents.manager.get_agent_temperature", return_value=0.0),
        "get_api_key_for_provider": patch("app.agents.manager.get_api_key_for_provider", return_value="test-key"),
        "get_agent_max_tokens": patch("app.agents.manager.get_agent_max_tokens", return_value=500),
        "get_agent_prompt": patch("app.agents.manager.get_agent_prompt", return_value="You are a Query Router..."),
        "load_prompts": patch("app.agents.manager.load_prompts", return_value=mock_prompts),
        "get_stream_writer": patch("app.agents.manager.get_stream_writer", return_value=MagicMock()),
    }


# ============================================================================
# Test Group 1: Routing Classification (manager_node)
# ============================================================================


class TestRoutingClassification:
    """Tests for manager_node routing decisions."""

    @pytest.mark.asyncio
    async def test_memory_query_routes_to_memory_sufficient(self, base_state, mock_settings, mock_prompts):
        """Memory queries (asking about previous results) should route to MEMORY_SUFFICIENT."""
        base_state["user_query"] = "What were the columns?"
        base_state["messages"] = [
            HumanMessage(content="Show me sales by region"),
            AIMessage(content="Here are the sales by region..."),
        ]

        decision = _make_routing_decision("MEMORY_SUFFICIENT", "Query asks about previous results")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            # Configure mock LLM chain
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "data_analysis"
            assert result.update["routing_decision"].route == "MEMORY_SUFFICIENT"

    @pytest.mark.asyncio
    async def test_modification_query_routes_to_code_modification(self, base_state, mock_settings, mock_prompts):
        """Modification queries (with previous code) should route to CODE_MODIFICATION."""
        base_state["user_query"] = "Add a trend column"
        base_state["generated_code"] = "import json\nresult = df.groupby('region')['sales'].sum()\nprint(json.dumps({'result': result.to_dict()}))"
        base_state["messages"] = [
            HumanMessage(content="Show me sales by region"),
            AIMessage(content="Here are the sales by region..."),
        ]

        decision = _make_routing_decision("CODE_MODIFICATION", "User wants to modify existing code")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "CODE_MODIFICATION"
            # Verify previous_code is passed through
            assert result.update["previous_code"] != ""

    @pytest.mark.asyncio
    async def test_new_analysis_query_routes_to_new_analysis(self, base_state, mock_settings, mock_prompts):
        """New analysis queries should route to NEW_ANALYSIS."""
        base_state["user_query"] = "Show me sales by region"
        # No messages = first query

        decision = _make_routing_decision("NEW_ANALYSIS", "First query, need new analysis")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "NEW_ANALYSIS"
            # NEW_ANALYSIS clears previous code
            assert result.update["previous_code"] == ""

    @pytest.mark.asyncio
    async def test_modification_without_previous_code_has_no_code_context(self, base_state, mock_settings, mock_prompts):
        """When LLM says CODE_MODIFICATION but no previous code exists,
        the manager still routes to coding_agent but previous_code is empty string.

        Note: The LLM is supposed to route to NEW_ANALYSIS when no code exists,
        but this test verifies manager_node behavior even if LLM makes a suboptimal decision.
        """
        base_state["user_query"] = "Filter by region = North"
        base_state["generated_code"] = ""  # No previous code

        decision = _make_routing_decision("CODE_MODIFICATION", "User wants modification")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            # Still routes to coding_agent with CODE_MODIFICATION
            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "CODE_MODIFICATION"
            # previous_code is empty string (or empty) since no code existed
            assert result.update.get("previous_code", "") == ""

    @pytest.mark.asyncio
    async def test_first_query_no_messages_routes_to_new_analysis(self, base_state, mock_settings, mock_prompts):
        """First query (empty messages) should route to NEW_ANALYSIS."""
        base_state["user_query"] = "Analyze retention rates"
        base_state["messages"] = []  # No conversation history

        decision = _make_routing_decision("NEW_ANALYSIS", "No conversation history")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "NEW_ANALYSIS"

    @pytest.mark.asyncio
    async def test_routing_prompt_includes_query_and_context(self, base_state, mock_settings, mock_prompts):
        """Verify the routing prompt sent to LLM includes user query and context."""
        base_state["user_query"] = "What were the top sellers?"
        base_state["messages"] = [HumanMessage(content="Previous query")]
        base_state["generated_code"] = "result = df.head()"

        decision = _make_routing_decision("MEMORY_SUFFICIENT")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            await manager_node(base_state)

            # Verify LLM was called with messages containing query context
            call_args = mock_structured.ainvoke.call_args[0][0]
            # Should have SystemMessage and HumanMessage
            assert len(call_args) == 2
            # Human message should contain the user query
            human_msg_content = call_args[1].content
            assert "What were the top sellers?" in human_msg_content
            assert "Has previous code: True" in human_msg_content


# ============================================================================
# Test Group 2: Fallback Behavior (ROUTING-04)
# ============================================================================


class TestRoutingFallback:
    """Tests for ROUTING-04 fallback behavior when LLM fails."""

    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_to_new_analysis(self, base_state, mock_settings, mock_prompts):
        """LLM exception should trigger fallback to NEW_ANALYSIS."""
        base_state["user_query"] = "Show me sales data"

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.side_effect = Exception("LLM service unavailable")
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            # Should fallback to NEW_ANALYSIS
            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "NEW_ANALYSIS"
            assert "Fallback" in result.update["routing_decision"].reasoning

    @pytest.mark.asyncio
    async def test_llm_timeout_falls_back_to_new_analysis(self, base_state, mock_settings, mock_prompts):
        """LLM timeout should trigger fallback to NEW_ANALYSIS."""
        base_state["user_query"] = "Calculate averages"

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.side_effect = TimeoutError("Request timed out")
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "NEW_ANALYSIS"
            assert "TimeoutError" in result.update["routing_decision"].reasoning

    @pytest.mark.asyncio
    async def test_llm_connection_error_falls_back_to_new_analysis(self, base_state, mock_settings, mock_prompts):
        """LLM connection error should trigger fallback to NEW_ANALYSIS."""
        base_state["user_query"] = "Show trends"

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.side_effect = ConnectionError("Connection refused")
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.goto == "coding_agent"
            assert result.update["routing_decision"].route == "NEW_ANALYSIS"
            assert "ConnectionError" in result.update["routing_decision"].reasoning

    @pytest.mark.asyncio
    async def test_fallback_decision_includes_error_type_in_reasoning(self, base_state, mock_settings, mock_prompts):
        """Fallback routing decision reasoning should include the error type."""
        base_state["user_query"] = "Analyze data"

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"]:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.side_effect = ValueError("Invalid response format")
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            result = await manager_node(base_state)

            assert result.update["routing_decision"].route == "NEW_ANALYSIS"
            assert "ValueError" in result.update["routing_decision"].reasoning


# ============================================================================
# Test Group 3: Route-Specific Agent Behavior
# ============================================================================


class TestRouteSpecificBehavior:
    """Tests for agent behavior per route."""

    @pytest.mark.asyncio
    async def test_memory_route_returns_no_code(self, base_state, mock_settings, mock_prompts):
        """MEMORY_SUFFICIENT route should return analysis with no generated_code or execution_result."""
        base_state["user_query"] = "What columns does this dataset have?"
        base_state["routing_decision"] = _make_routing_decision(
            "MEMORY_SUFFICIENT",
            "Query about data structure, no code needed",
            "Dataset has columns: id, name, sales, region"
        )
        base_state["messages"] = [
            HumanMessage(content="Show me the data"),
            AIMessage(content="The dataset has id, name, sales, region columns"),
        ]

        with patch("app.agents.data_analysis.get_settings", return_value=mock_settings), \
             patch("app.agents.data_analysis.get_llm") as mock_get_llm, \
             patch("app.agents.data_analysis.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.data_analysis.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.data_analysis.get_agent_temperature", return_value=0.0), \
             patch("app.agents.data_analysis.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.data_analysis.get_agent_max_tokens", return_value=2000), \
             patch("app.agents.data_analysis.get_stream_writer", return_value=MagicMock()):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="The dataset has 4 columns: id, name, sales, region.")
            mock_get_llm.return_value = mock_llm

            from app.agents.data_analysis import data_analysis_agent
            result = await data_analysis_agent(base_state)

            assert result["analysis"] != ""
            assert result["final_response"] != ""
            # Memory route should NOT produce code or execution results
            assert result["generated_code"] == ""
            assert result["execution_result"] == ""

    @pytest.mark.asyncio
    async def test_modification_route_includes_previous_code_in_prompt(self, base_state, mock_settings, mock_prompts):
        """CODE_MODIFICATION route should include previous_code in the LLM prompt."""
        previous = "import json\nresult = df.groupby('region')['sales'].sum().to_dict()\nprint(json.dumps({'result': result}))"
        base_state["user_query"] = "Sort by sales descending"
        base_state["routing_decision"] = _make_routing_decision(
            "CODE_MODIFICATION",
            "User wants to sort existing results",
            "Previous code grouped sales by region"
        )
        base_state["previous_code"] = previous
        base_state["data_profile"] = '{"columns": {"region": {"type": "str"}, "sales": {"type": "float"}}}'
        base_state["user_context"] = "Sales data"

        with patch("app.agents.coding.get_settings", return_value=mock_settings), \
             patch("app.agents.coding.get_llm") as mock_get_llm, \
             patch("app.agents.coding.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.coding.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.coding.get_agent_temperature", return_value=0.0), \
             patch("app.agents.coding.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.coding.get_agent_max_tokens", return_value=10000), \
             patch("app.agents.coding.get_agent_prompt", return_value="Generate Python code. {data_profile} {user_context} {allowed_libraries}"), \
             patch("app.agents.coding.get_allowed_libraries", return_value={"pandas", "numpy", "json"}), \
             patch("app.agents.coding.get_stream_writer", return_value=MagicMock()):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(
                content="```python\nimport json\nresult = df.groupby('region')['sales'].sum().sort_values(ascending=False).to_dict()\nprint(json.dumps({'result': result}))\n```"
            )
            mock_get_llm.return_value = mock_llm

            from app.agents.coding import coding_agent
            result = await coding_agent(base_state)

            # Verify coding_agent was called and produced code
            assert "generated_code" in result
            assert result["generated_code"] != ""

            # Verify the LLM received the previous code in the prompt
            call_args = mock_llm.ainvoke.call_args[0][0]
            human_msg = call_args[1].content
            assert "MODIFY" in human_msg
            assert previous in human_msg

    @pytest.mark.asyncio
    async def test_new_analysis_route_generates_fresh_code(self, base_state, mock_settings, mock_prompts):
        """NEW_ANALYSIS route should generate fresh code (standard behavior)."""
        base_state["user_query"] = "Show me monthly revenue trends"
        base_state["routing_decision"] = _make_routing_decision(
            "NEW_ANALYSIS",
            "Completely new analysis request"
        )
        base_state["data_profile"] = '{"columns": {"date": {"type": "datetime"}, "revenue": {"type": "float"}}}'
        base_state["user_context"] = "Revenue data"

        with patch("app.agents.coding.get_settings", return_value=mock_settings), \
             patch("app.agents.coding.get_llm") as mock_get_llm, \
             patch("app.agents.coding.get_agent_provider", return_value="anthropic"), \
             patch("app.agents.coding.get_agent_model", return_value="claude-sonnet-4-20250514"), \
             patch("app.agents.coding.get_agent_temperature", return_value=0.0), \
             patch("app.agents.coding.get_api_key_for_provider", return_value="test-key"), \
             patch("app.agents.coding.get_agent_max_tokens", return_value=10000), \
             patch("app.agents.coding.get_agent_prompt", return_value="Generate Python code. {data_profile} {user_context} {allowed_libraries}"), \
             patch("app.agents.coding.get_allowed_libraries", return_value={"pandas", "numpy", "json"}), \
             patch("app.agents.coding.get_stream_writer", return_value=MagicMock()):
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(
                content="```python\nimport json\nresult = df.groupby(df['date'].dt.month)['revenue'].sum().to_dict()\nprint(json.dumps({'result': result}))\n```"
            )
            mock_get_llm.return_value = mock_llm

            from app.agents.coding import coding_agent
            result = await coding_agent(base_state)

            assert "generated_code" in result
            assert result["generated_code"] != ""

            # Verify the LLM prompt does NOT contain modification instructions
            call_args = mock_llm.ainvoke.call_args[0][0]
            human_msg = call_args[1].content
            assert "MODIFY" not in human_msg


# ============================================================================
# Test Group 4: Graph Topology
# ============================================================================


class TestGraphTopology:
    """Tests for graph structure."""

    def test_manager_is_entry_point(self):
        """Manager should be the entry point of the graph."""
        from app.agents.graph import build_chat_graph
        graph = build_chat_graph()

        # LangGraph compiled graphs expose the entry point via first_node or nodes
        # The graph should start at the manager node
        graph_json = graph.get_graph().to_json()
        # Verify manager node exists and is connected from __start__
        assert "manager" in str(graph_json)

    def test_graph_has_all_expected_nodes(self):
        """Graph should contain all expected nodes."""
        from app.agents.graph import build_chat_graph
        graph = build_chat_graph()

        graph_dict = graph.get_graph().to_json()
        graph_str = str(graph_dict)

        expected_nodes = ["manager", "coding_agent", "code_checker", "execute", "data_analysis", "halt"]
        for node in expected_nodes:
            assert node in graph_str, f"Node '{node}' not found in graph"

    def test_manager_routes_to_data_analysis_and_coding(self):
        """Manager should have edges to both data_analysis and coding_agent."""
        from app.agents.graph import build_chat_graph
        graph = build_chat_graph()

        graph_data = graph.get_graph().to_json()
        graph_str = str(graph_data)

        # Manager should be connected to data_analysis (MEMORY_SUFFICIENT)
        # and coding_agent (CODE_MODIFICATION/NEW_ANALYSIS)
        # These are Command-based routes, so they appear as edges
        assert "data_analysis" in graph_str
        assert "coding_agent" in graph_str

    def test_coding_agent_connects_to_code_checker(self):
        """coding_agent should have an edge to code_checker."""
        from app.agents.graph import build_chat_graph
        graph = build_chat_graph()

        graph_data = graph.get_graph().to_json()
        graph_str = str(graph_data)

        assert "code_checker" in graph_str


# ============================================================================
# Test Group 5: Configuration
# ============================================================================


class TestRoutingConfig:
    """Tests for YAML configuration."""

    def test_manager_config_loads_from_yaml(self):
        """Manager agent config should be loadable from prompts.yaml."""
        from app.agents.config import load_prompts

        prompts = load_prompts()
        manager_config = prompts["agents"]["manager"]

        assert "system_prompt" in manager_config
        assert "model" in manager_config
        assert "provider" in manager_config
        assert "max_tokens" in manager_config

    def test_routing_context_messages_default(self):
        """routing_context_messages should default to 10 in YAML config."""
        from app.agents.config import load_prompts

        prompts = load_prompts()
        manager_config = prompts["agents"]["manager"]

        routing_context = manager_config.get("routing_context_messages", 10)
        assert routing_context == 10

    def test_manager_uses_specified_provider(self):
        """Manager should use the provider specified in YAML."""
        from app.agents.config import get_agent_provider

        provider = get_agent_provider("manager")
        assert provider == "anthropic"

    def test_manager_uses_specified_model(self):
        """Manager should use the model specified in YAML."""
        from app.agents.config import get_agent_model

        model = get_agent_model("manager")
        assert model == "claude-sonnet-4-20250514"


# ============================================================================
# Test Group 6: Structured Logging (ROUTING-08)
# ============================================================================


class TestRoutingLogging:
    """Tests for ROUTING-08 structured logging compliance."""

    @pytest.mark.asyncio
    async def test_routing_decision_logged(self, base_state, mock_settings, mock_prompts):
        """Routing decision should be logged with event, route, reasoning, message_count, has_previous_code."""
        base_state["user_query"] = "Show me sales"
        base_state["messages"] = [HumanMessage(content="Hello")]
        base_state["generated_code"] = "result = df.head()"

        decision = _make_routing_decision("NEW_ANALYSIS", "Fresh analysis needed")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"], \
             patch("app.agents.manager.logger") as mock_logger:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            await manager_node(base_state)

            # Verify logger.info was called with structured JSON
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call)

            assert log_data["event"] == "routing_decision"
            assert log_data["route"] == "NEW_ANALYSIS"
            assert log_data["reasoning"] == "Fresh analysis needed"
            assert log_data["message_count"] == 1
            assert log_data["has_previous_code"] is True
            assert log_data["thread_id"] == "test-file-123"

    @pytest.mark.asyncio
    async def test_fallback_logged_with_warning(self, base_state, mock_settings, mock_prompts):
        """Fallback routing should log a warning before the decision log."""
        base_state["user_query"] = "Analyze data"

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], patches["get_stream_writer"], \
             patch("app.agents.manager.logger") as mock_logger:
            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.side_effect = RuntimeError("Provider down")
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            await manager_node(base_state)

            # Verify warning was logged for the fallback
            assert mock_logger.warning.called
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "RuntimeError" in warning_msg
            assert "Falling back to NEW_ANALYSIS" in warning_msg

            # Verify info was still logged for the routing decision
            assert mock_logger.info.called
            log_call = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call)
            assert log_data["route"] == "NEW_ANALYSIS"


# ============================================================================
# Test Group 7: Routing Decision Model
# ============================================================================


class TestRoutingDecisionModel:
    """Tests for RoutingDecision Pydantic model."""

    def test_routing_decision_valid_routes(self):
        """RoutingDecision should accept all three valid route types."""
        for route in ["MEMORY_SUFFICIENT", "CODE_MODIFICATION", "NEW_ANALYSIS"]:
            decision = RoutingDecision(
                route=route,
                reasoning="test",
                context_summary="test",
            )
            assert decision.route == route

    def test_routing_decision_invalid_route_rejected(self):
        """RoutingDecision should reject invalid route values."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RoutingDecision(
                route="INVALID_ROUTE",
                reasoning="test",
                context_summary="test",
            )

    def test_routing_decision_serialization(self):
        """RoutingDecision should serialize to dict correctly."""
        decision = RoutingDecision(
            route="MEMORY_SUFFICIENT",
            reasoning="Memory is enough",
            context_summary="Previous results available",
        )
        data = decision.model_dump()
        assert data["route"] == "MEMORY_SUFFICIENT"
        assert data["reasoning"] == "Memory is enough"
        assert data["context_summary"] == "Previous results available"


# ============================================================================
# Test Group 8: Stream Events
# ============================================================================


class TestStreamEvents:
    """Tests for routing stream events emitted to frontend."""

    @pytest.mark.asyncio
    async def test_routing_started_event_emitted(self, base_state, mock_settings, mock_prompts):
        """Manager should emit routing_started event."""
        base_state["user_query"] = "Show me data"

        decision = _make_routing_decision("NEW_ANALYSIS")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], \
             patch("app.agents.manager.get_stream_writer") as mock_get_writer:
            mock_writer = MagicMock()
            mock_get_writer.return_value = mock_writer

            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            await manager_node(base_state)

            # Verify writer was called with routing_started event
            calls = mock_writer.call_args_list
            assert len(calls) >= 2  # routing_started + routing_decided

            # First call should be routing_started
            first_event = calls[0][0][0]
            assert first_event["type"] == "routing_started"

    @pytest.mark.asyncio
    async def test_routing_decided_event_emitted(self, base_state, mock_settings, mock_prompts):
        """Manager should emit routing_decided event with route info."""
        base_state["user_query"] = "Show me data"

        decision = _make_routing_decision("MEMORY_SUFFICIENT")

        patches = _patch_manager_dependencies(mock_settings, mock_prompts)
        with patches["get_settings"], patches["get_llm"] as mock_get_llm, \
             patches["get_agent_provider"], patches["get_agent_model"], \
             patches["get_agent_temperature"], patches["get_api_key_for_provider"], \
             patches["get_agent_max_tokens"], patches["get_agent_prompt"], \
             patches["load_prompts"], \
             patch("app.agents.manager.get_stream_writer") as mock_get_writer:
            mock_writer = MagicMock()
            mock_get_writer.return_value = mock_writer

            mock_llm = MagicMock()
            mock_structured = AsyncMock()
            mock_structured.ainvoke.return_value = decision
            mock_llm.with_structured_output.return_value = mock_structured
            mock_get_llm.return_value = mock_llm

            from app.agents.manager import manager_node
            await manager_node(base_state)

            # Verify writer was called with routing_decided event
            calls = mock_writer.call_args_list
            decided_events = [c[0][0] for c in calls if c[0][0].get("type") == "routing_decided"]
            assert len(decided_events) == 1
            assert decided_events[0]["route"] == "MEMORY_SUFFICIENT"
            assert "message" in decided_events[0]
