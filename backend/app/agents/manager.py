"""Manager Agent for intelligent query routing.

This module implements the Manager Agent, which serves as the entry point of the
chat analysis graph. It classifies user queries into one of three routes:

- MEMORY_SUFFICIENT: Query can be answered from conversation history alone
- CODE_MODIFICATION: Query requires modifying existing code
- NEW_ANALYSIS: Query requires completely new code generation

The Manager Agent uses structured LLM output (RoutingDecision) for reliable
classification and Command-based routing to direct queries to the appropriate
downstream agent.
"""

import json
import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.types import Command

from app.agents.config import (
    get_agent_max_tokens,
    get_agent_model,
    get_agent_prompt,
    get_agent_provider,
    get_agent_temperature,
    get_api_key_for_provider,
    load_prompts,
)
from app.agents.llm_factory import get_llm
from app.agents.state import ChatAgentState, RoutingDecision
from app.config import get_settings

logger = logging.getLogger("spectra.routing")


async def manager_node(
    state: ChatAgentState,
) -> Command[Literal["data_analysis", "coding_agent"]]:
    """Manager Agent node that classifies queries and routes to appropriate agent.

    Analyzes the user's query and conversation context to determine the optimal
    processing route. Uses structured LLM output for reliable JSON parsing.

    Routes:
    - MEMORY_SUFFICIENT -> data_analysis (skip code generation entirely)
    - CODE_MODIFICATION -> coding_agent (with previous code for modification)
    - NEW_ANALYSIS -> coding_agent (fresh code generation)

    Falls back to NEW_ANALYSIS on any routing failure (ROUTING-04).

    Args:
        state: Current chat workflow state

    Returns:
        Command: Routing command to data_analysis or coding_agent with state updates
    """
    writer = get_stream_writer()
    writer({
        "type": "routing_started",
        "message": "Analyzing query...",
    })

    settings = get_settings()

    # Load LLM config for manager agent
    provider = get_agent_provider("manager")
    model = get_agent_model("manager")
    temperature = get_agent_temperature("manager")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("manager")

    # Build kwargs for provider-specific options
    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    # Instantiate LLM with structured output for reliable JSON parsing
    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)
    structured_llm = llm.with_structured_output(RoutingDecision)

    # Load system prompt from YAML
    system_prompt = get_agent_prompt("manager")

    # Get routing context messages limit from YAML config (default: 10)
    prompts = load_prompts()
    routing_context_messages = prompts["agents"]["manager"].get(
        "routing_context_messages", 10
    )

    # Read conversation messages and limit to last N
    messages = state.get("messages", [])
    recent_messages = messages[-routing_context_messages:]

    # Check for previous code
    previous_code = state.get("generated_code", "")
    has_previous_code = bool(previous_code)

    # Get data summary for context
    data_summary = state.get("data_summary", "")

    # Build routing prompt with context
    code_snippet = previous_code[:500] if previous_code else "None"
    routing_prompt = (
        f"**Current User Query:** {state.get('user_query', '')}\n\n"
        f"**Conversation Context:**\n"
        f"- Messages in history: {len(messages)}\n"
        f"- Has previous code: {has_previous_code}\n\n"
        f"**Data Summary:**\n{data_summary}\n\n"
        f"**Previous Code (truncated):**\n```python\n{code_snippet}\n```\n\n"
        f"Analyze the query and determine the optimal route."
    )

    try:
        # Send to structured LLM for reliable parsing
        decision: RoutingDecision = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=routing_prompt),
        ])
    except Exception as e:
        # Fallback to NEW_ANALYSIS on any failure (ROUTING-04)
        error_type = type(e).__name__
        logger.warning(
            f"Routing LLM failed ({error_type}): {e}. Falling back to NEW_ANALYSIS."
        )
        decision = RoutingDecision(
            route="NEW_ANALYSIS",
            reasoning=f"Fallback: routing failed ({error_type})",
            context_summary="",
        )

    # Log routing decision with reasoning (ROUTING-08)
    thread_id = state.get("file_id", "unknown")
    logger.info(json.dumps({
        "event": "routing_decision",
        "route": decision.route,
        "reasoning": decision.reasoning,
        "message_count": len(messages),
        "has_previous_code": has_previous_code,
        "thread_id": thread_id,
    }))

    # Emit routing decision event for frontend
    route_messages = {
        "MEMORY_SUFFICIENT": "Answering from conversation history...",
        "CODE_MODIFICATION": "Modifying existing code...",
        "NEW_ANALYSIS": "Generating new analysis...",
    }
    writer({
        "type": "routing_decided",
        "route": decision.route,
        "message": route_messages.get(decision.route, "Processing..."),
    })

    # Route via Command based on decision (single-route logic, ROUTING-10)
    if decision.route == "MEMORY_SUFFICIENT":
        return Command(
            goto="data_analysis",
            update={"routing_decision": decision},
        )
    elif decision.route == "CODE_MODIFICATION":
        return Command(
            goto="coding_agent",
            update={
                "routing_decision": decision,
                "previous_code": previous_code or "",
            },
        )
    else:
        # NEW_ANALYSIS (default)
        return Command(
            goto="coding_agent",
            update={
                "routing_decision": decision,
                "previous_code": "",
            },
        )
