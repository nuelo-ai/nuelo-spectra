"""Data Analysis Agent for interpreting code execution results."""

from langchain_core.messages import HumanMessage, SystemMessage
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

    # Return both analysis and final_response (same content for v1)
    return {
        "analysis": response.content,
        "final_response": response.content
    }
