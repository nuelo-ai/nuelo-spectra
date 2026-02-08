"""Data Analysis Agent for interpreting code execution results.

Supports two modes:
- MEMORY_SUFFICIENT: Answer from conversation history without code generation
- Standard mode: Interpret code execution results (existing behavior)
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.config import get_stream_writer

from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm
from app.agents.state import ChatAgentState
from app.config import get_settings


async def data_analysis_agent(state: ChatAgentState) -> dict:
    """Interpret code execution results or answer from conversation history.

    This agent operates in two modes based on routing_decision:

    1. MEMORY_SUFFICIENT mode: Answers the user's question using only
       conversation history and data context (no code generation or execution).

    2. Standard mode (default): Takes executed code output and translates it
       into a clear, conversational explanation that directly answers the user's query.

    Args:
        state: Current chat workflow state containing:
            - user_query: Original natural language question
            - routing_decision: Manager Agent's routing decision (or None)
            - messages: Conversation history (used in memory mode)
            - generated_code: Python code that was executed (standard mode)
            - execution_result: Output from code execution (standard mode)

    Returns:
        dict: State update with analysis, final_response, and messages (AIMessage).
              In memory mode, generated_code and execution_result are NOT returned
              so that checkpoint values from previous queries are preserved.

    Examples:
        >>> state = {
        ...     "user_query": "What is the average sales?",
        ...     "generated_code": "result = df['sales'].mean()",
        ...     "execution_result": "1234.56"
        ... }
        >>> result = await data_analysis_agent(state)
        >>> "analysis" in result and "final_response" in result
        True
    """
    writer = get_stream_writer()

    # Check for MEMORY_SUFFICIENT route — answer from conversation history
    routing = state.get("routing_decision")
    if routing and routing.route == "MEMORY_SUFFICIENT":
        # MEMORY MODE: Answer from conversation history, no code/execution
        writer({
            "type": "analysis_started",
            "message": "Answering from conversation context...",
            "step": 1,
            "total_steps": 1,
        })

        # Build memory-mode prompt using conversation history
        messages_history = state.get("messages", [])
        context_summary = routing.context_summary

        # Format recent messages for the prompt (last 10)
        recent = messages_history[-10:] if len(messages_history) > 10 else messages_history
        formatted_messages = []
        for msg in recent:
            role = getattr(msg, "type", "unknown")
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            formatted_messages.append(f"[{role}]: {content}")
        conversation_text = "\n".join(formatted_messages)

        memory_prompt = f"""Answer the user's question using ONLY the conversation history and data context.

**User's Question:** {state["user_query"]}

**Relevant Context from Router:**
{context_summary}

**Data Summary:**
{state.get("data_summary", "No data summary available")}

**Recent Conversation:**
{conversation_text}

**Instructions:**
- Answer the user's question using information from the conversation history
- If the answer is in previous results, reference it clearly
- If asking about data structure, use the data summary
- DO NOT suggest generating new code
- Be concise and direct
- Format for readability with markdown"""

        # Use existing LLM config for data_analysis agent
        settings = get_settings()
        provider = get_agent_provider("data_analysis")
        model = get_agent_model("data_analysis")
        temperature = get_agent_temperature("data_analysis")
        api_key = get_api_key_for_provider(provider, settings)
        max_tokens = get_agent_max_tokens("data_analysis")

        kwargs = {"max_tokens": max_tokens, "temperature": temperature}
        if provider == "ollama":
            kwargs["base_url"] = settings.ollama_base_url

        llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

        messages = [
            SystemMessage(content="You are a Data Analyst answering questions using conversation context. Do not suggest generating code."),
            HumanMessage(content=memory_prompt),
        ]

        response = await llm.ainvoke(messages)

        # Do NOT return generated_code or execution_result here —
        # that would overwrite checkpoint values from previous queries,
        # causing the Manager Agent to lose track of previous code/results.
        return {
            "analysis": response.content,
            "final_response": response.content,
            "follow_up_suggestions": [],
            "messages": [AIMessage(content=response.content)],
        }

    # STANDARD MODE: Interpret code execution results (existing behavior)
    writer({
        "type": "analysis_started",
        "message": "Analyzing...",
        "step": 4,
        "total_steps": 4
    })

    settings = get_settings()

    # Load system prompt from YAML
    system_prompt_template = get_agent_prompt("data_analysis")

    # Format prompt with execution context
    system_prompt = system_prompt_template.format(
        user_query=state["user_query"],
        executed_code=state.get("generated_code", "No code available"),
        execution_result=state.get("execution_result", "No result available")
    )

    # Initialize LLM using per-agent config
    provider = get_agent_provider("data_analysis")
    model = get_agent_model("data_analysis")
    temperature = get_agent_temperature("data_analysis")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("data_analysis")

    # Build kwargs for provider-specific options
    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please analyze these results.")
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Parse JSON response with fallback for non-JSON responses
    try:
        parsed = json.loads(response.content)
        analysis = parsed.get("analysis", response.content)
        follow_ups = parsed.get("follow_up_suggestions", [])
    except json.JSONDecodeError:
        # Fallback: treat entire response as analysis, no follow-ups
        analysis = response.content
        follow_ups = []

    # Return analysis, final_response, follow_up_suggestions, and add AIMessage to conversation history
    return {
        "analysis": analysis,
        "final_response": analysis,
        "follow_up_suggestions": follow_ups,
        "messages": [AIMessage(content=analysis)],
    }
