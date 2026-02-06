"""Data Analysis Agent for interpreting code execution results."""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer

from app.agents.config import get_agent_prompt, get_agent_max_tokens
from app.agents.llm_factory import get_llm
from app.agents.state import ChatAgentState
from app.config import get_settings


def _get_api_key(settings) -> str:
    """Get API key based on configured LLM provider.

    Args:
        settings: Application settings instance

    Returns:
        str: API key for the configured provider

    Raises:
        ValueError: If provider is unknown
    """
    if settings.llm_provider == "anthropic":
        return settings.anthropic_api_key
    elif settings.llm_provider == "openai":
        return settings.openai_api_key
    elif settings.llm_provider == "google":
        return settings.google_api_key
    else:
        raise ValueError(f"Unknown provider: {settings.llm_provider}")


async def data_analysis_agent(state: ChatAgentState) -> dict:
    """Interpret code execution results and generate natural language explanation.

    This agent takes the executed code's output and translates it into a clear,
    conversational explanation that directly answers the user's query.

    Args:
        state: Current chat workflow state containing:
            - user_query: Original natural language question
            - generated_code: Python code that was executed
            - execution_result: Output from code execution

    Returns:
        dict: State update with analysis and final_response keys

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

    # Initialize LLM using factory
    api_key = _get_api_key(settings)
    max_tokens = get_agent_max_tokens("data_analysis")
    llm = get_llm(
        provider=settings.llm_provider,
        model=settings.agent_model,
        api_key=api_key,
        max_tokens=max_tokens
    )

    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please analyze these results.")
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Return both analysis and final_response (same content for v1)
    return {
        "analysis": response.content,
        "final_response": response.content
    }
