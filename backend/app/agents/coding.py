"""Coding Agent for generating Python code from natural language queries.

Supports two modes:
- CODE_MODIFICATION: Modify existing code based on previous analysis
- Standard mode (NEW_ANALYSIS / retries): Generate fresh code from scratch
"""

import re
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer

from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_allowed_libraries,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm
from app.agents.state import ChatAgentState
from app.config import get_settings


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
    """Generate or modify Python code from natural language query.

    This agent operates in two modes based on routing_decision:

    1. CODE_MODIFICATION mode: Modifies existing code (previous_code) based on
       the user's request. Keeps base logic intact, only changes what's needed.

    2. Standard mode (NEW_ANALYSIS / retries): Generates fresh code from scratch.
       If validation errors exist (retry scenario), they are appended to the prompt.

    Args:
        state: Current chat workflow state containing:
            - user_query: Natural language question
            - routing_decision: Manager Agent's routing decision (or None)
            - previous_code: Previously generated code (for modification mode)
            - data_profile: Structured JSON with column names, types, and samples
            - user_context: Accumulated user context
            - validation_errors: Optional list of errors from previous attempts

    Returns:
        dict: State update with generated_code key

    Examples:
        >>> state = {
        ...     "user_query": "What is the average sales by region?",
        ...     "data_profile": '{"columns": {"region": {...}, "sales_amount": {...}}}',
        ...     "user_context": "Q4 2025 sales data",
        ...     "validation_errors": []
        ... }
        >>> result = await coding_agent(state)
        >>> "generated_code" in result
        True
    """
    writer = get_stream_writer()

    # Check for CODE_MODIFICATION route
    routing = state.get("routing_decision")
    is_modification = routing and routing.route == "CODE_MODIFICATION"
    previous_code = state.get("previous_code", "")

    # Determine prompt and status message based on mode
    error_count = state.get("error_count", 0)

    if is_modification and previous_code:
        # CODE_MODIFICATION MODE: Modify existing code
        writer({
            "type": "coding_started",
            "message": "Modifying previous code...",
            "step": 1,
            "total_steps": 4,
        })

        context_summary = routing.context_summary if routing else ""
        user_message = f"""{state["user_query"]}

**Context:** {context_summary}

**Previous Code (MODIFY this, do not rewrite from scratch):**
```python
{previous_code}
```

**Instructions:**
- MODIFY the existing code above to fulfill the user's new request
- Keep the base logic intact, only change what's needed
- Maintain the same output format (print(json.dumps({{"result": result}})))
- Add comments explaining what was changed"""

    else:
        # STANDARD MODE: Generate fresh code (NEW_ANALYSIS or retry)
        if error_count > 0:
            writer({
                "type": "coding_started",
                "message": f"Regenerating code (attempt {error_count + 1}/{state.get('max_steps', 3)})...",
                "step": 1,
                "total_steps": 4,
            })
        else:
            writer({
                "type": "coding_started",
                "message": "Generating code...",
                "step": 1,
                "total_steps": 4,
            })

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

    settings = get_settings()

    # Load system prompt from YAML
    system_prompt_template = get_agent_prompt("coding")

    # Format prompt with data context
    allowed_libs = get_allowed_libraries()
    allowed_libs_str = ", ".join(sorted(allowed_libs))

    system_prompt = system_prompt_template.format(
        data_profile=state.get("data_profile", "{}"),
        user_context=state.get("user_context", "No additional context provided"),
        allowed_libraries=allowed_libs_str
    )

    # Initialize LLM using per-agent config
    provider = get_agent_provider("coding")
    model = get_agent_model("coding")
    temperature = get_agent_temperature("coding")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("coding")

    # Build kwargs for provider-specific options
    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Build messages (shared path for both modes)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # Invoke LLM
    response = await llm.ainvoke(messages)

    # Extract code from response
    generated_code = extract_code_block(response.content)

    return {"generated_code": generated_code}
