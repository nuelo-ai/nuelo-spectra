"""Coding Agent for generating Python code from natural language queries."""

import re
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer

from app.agents.config import get_agent_prompt, get_agent_max_tokens, get_allowed_libraries
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


def extract_code_block(text: str) -> str:
    """Extract Python code from markdown-formatted text.

    Attempts to extract code between ```python and ``` markers.
    Falls back to returning text stripped of markdown if no markers found.

    Args:
        text: Text containing code (possibly in markdown format)

    Returns:
        str: Extracted Python code

    Examples:
        >>> extract_code_block('```python\\nimport pandas\\n```')
        'import pandas'
        >>> extract_code_block('import pandas')
        'import pandas'
    """
    # Try to find code block with python marker
    pattern = r"```python\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    # Try generic code block markers
    pattern = r"```\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    # No markers found, return text as-is (stripped)
    return text.strip()


async def coding_agent(state: ChatAgentState) -> dict:
    """Generate Python code from natural language query.

    This agent uses the LLM to translate user queries into executable Python code.
    It incorporates data context from the Onboarding Agent and user context.
    If validation errors exist (retry scenario), they are appended to the prompt.

    Args:
        state: Current chat workflow state containing:
            - user_query: Natural language question
            - data_summary: Dataset summary from Onboarding Agent
            - user_context: Accumulated user context
            - validation_errors: Optional list of errors from previous attempts

    Returns:
        dict: State update with generated_code key

    Examples:
        >>> state = {
        ...     "user_query": "What is the average sales by region?",
        ...     "data_summary": "Dataset with columns: region, sales_amount",
        ...     "user_context": "Q4 2025 sales data",
        ...     "validation_errors": []
        ... }
        >>> result = await coding_agent(state)
        >>> "generated_code" in result
        True
    """
    writer = get_stream_writer()

    # Check if this is a retry
    error_count = state.get("error_count", 0)
    if error_count > 0:
        writer({
            "type": "status",
            "event": "coding_started",
            "message": f"Regenerating code (attempt {error_count + 1}/{state.get('max_steps', 3)})...",
            "step": 1,
            "total_steps": 4
        })
    else:
        writer({
            "type": "status",
            "event": "coding_started",
            "message": "Generating code...",
            "step": 1,
            "total_steps": 4
        })

    settings = get_settings()

    # Load system prompt from YAML
    system_prompt_template = get_agent_prompt("coding")

    # Format prompt with data context
    allowed_libs = get_allowed_libraries()
    allowed_libs_str = ", ".join(sorted(allowed_libs))

    system_prompt = system_prompt_template.format(
        data_summary=state.get("data_summary", "No data summary available"),
        user_context=state.get("user_context", "No additional context provided"),
        allowed_libraries=allowed_libs_str
    )

    # Build user message
    user_message = state["user_query"]

    # If validation errors exist (retry scenario), append feedback
    validation_errors = state.get("validation_errors", [])
    if validation_errors:
        error_feedback = "\n".join(validation_errors)
        # Check if this is an execution error (vs validation error)
        execution_result = state.get("execution_result", "")
        if execution_result.startswith("Execution error:"):
            user_message += f"\n\nThe previous code failed during execution:\n{error_feedback}\nPlease regenerate the code fixing the execution error. Consider using simpler operations if the error was a timeout or memory issue."
        else:
            user_message += f"\n\nPrevious code had validation issues:\n{error_feedback}\nPlease regenerate the code fixing these issues."

    # Initialize LLM using factory
    api_key = _get_api_key(settings)
    max_tokens = get_agent_max_tokens("coding")
    llm = get_llm(
        provider=settings.llm_provider,
        model=settings.agent_model,
        api_key=api_key,
        max_tokens=max_tokens
    )

    # Build messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Extract code from response
    generated_code = extract_code_block(response.content)

    return {"generated_code": generated_code}
