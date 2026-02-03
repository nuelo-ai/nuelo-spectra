"""LangGraph workflow for chat analysis pipeline.

This module assembles the complete chat analysis pipeline:
Coding Agent -> Code Checker -> Execute -> Data Analysis Agent

The workflow includes:
- Conditional routing based on validation results
- Bounded retry loops with circuit breaker (max_steps=3)
- PostgreSQL checkpointing for thread isolation
"""

from typing import Literal
import pandas as pd
import numpy as np

from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from langgraph.config import get_stream_writer

from app.agents.state import ChatAgentState
from app.agents.coding import coding_agent
from app.agents.code_checker import validate_code
from app.agents.data_analysis import data_analysis_agent
from app.agents.config import get_agent_prompt, get_agent_max_tokens
from app.agents.llm_factory import get_llm
from app.config import get_settings

from langchain_core.messages import HumanMessage, SystemMessage


# Module-level cached graph instance
_cached_graph = None


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


async def code_checker_node(
    state: ChatAgentState,
) -> Command[Literal["execute", "coding_agent", "halt"]]:
    """Code checker node that validates code with AST + LLM logical check.

    This node performs two-stage validation:
    1. AST validation: Syntax, imports, unsafe operations
    2. LLM logical check: Does code answer user's query correctly?

    Routes to:
    - "execute": Code is valid, proceed to execution
    - "coding_agent": Validation failed, retry with feedback
    - "halt": Max retries exceeded, stop execution

    Args:
        state: Current chat workflow state

    Returns:
        Command: Routing command with state updates
    """
    writer = get_stream_writer()
    writer({
        "type": "status",
        "event": "validation_started",
        "message": "Validating...",
        "step": 2,
        "total_steps": 4
    })

    generated_code = state.get("generated_code", "")
    error_count = state.get("error_count", 0)
    max_steps = state.get("max_steps", 3)

    # Stage 1: AST validation
    ast_result = validate_code(generated_code)

    if not ast_result.is_valid:
        # AST validation failed - increment error count and route to retry or halt
        new_error_count = error_count + 1

        if new_error_count >= max_steps:
            # Circuit breaker: max retries exceeded
            return Command(
                goto="halt",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": ast_result.errors,
                    "error_count": new_error_count,
                },
            )
        else:
            # Retry: send back to coding agent with feedback
            writer({
                "type": "retry",
                "event": "retry",
                "message": f"Code validation failed: {'; '.join(ast_result.errors[:2])}",
                "attempt": new_error_count,
                "max_attempts": max_steps
            })
            return Command(
                goto="coding_agent",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": ast_result.errors,
                    "error_count": new_error_count,
                },
            )

    # Stage 2: LLM logical validation
    settings = get_settings()

    # Load system prompt from YAML
    system_prompt_template = get_agent_prompt("code_checker")
    system_prompt = system_prompt_template.format(
        user_query=state["user_query"], generated_code=generated_code
    )

    # Initialize LLM
    api_key = _get_api_key(settings)
    max_tokens = get_agent_max_tokens("code_checker")
    llm = get_llm(
        provider=settings.llm_provider,
        model=settings.agent_model,
        api_key=api_key,
        max_tokens=max_tokens,
    )

    # Invoke LLM for logical validation
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please validate this code."),
    ]

    response = await llm.ainvoke(messages)
    validation_response = response.content.strip()

    # Parse LLM response
    if validation_response.upper().startswith("VALID"):
        # Code is valid, proceed to execution
        return Command(
            goto="execute",
            update={
                "validation_result": "VALID",
                "validation_errors": [],
            },
        )
    else:
        # LLM found logical issues
        # Extract error messages (lines starting with '-' or after 'INVALID')
        lines = validation_response.split("\n")
        issues = []
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("Issue"):
                issues.append(line)
            elif line.startswith("Suggestion"):
                issues.append(line)

        if not issues:
            # Fallback: use entire response as error
            issues = [validation_response]

        new_error_count = error_count + 1

        if new_error_count >= max_steps:
            # Circuit breaker
            return Command(
                goto="halt",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": issues,
                    "error_count": new_error_count,
                },
            )
        else:
            # Retry with feedback
            writer({
                "type": "retry",
                "event": "retry",
                "message": f"Code validation failed: {'; '.join(issues[:2])}",
                "attempt": new_error_count,
                "max_attempts": max_steps
            })
            return Command(
                goto="coding_agent",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": issues,
                    "error_count": new_error_count,
                },
            )


async def execute_code_stub(state: ChatAgentState) -> dict:
    """Execute Python code in restricted namespace (development stub).

    This is a STUB for Phase 3. Real sandbox execution comes in Phase 5.
    The AST validation from Code Checker provides the safety layer.
    Phase 5 will add OS-level isolation with E2B or gVisor.

    Args:
        state: Current chat workflow state with generated_code

    Returns:
        dict: State update with execution_result (or error)

    Example:
        >>> state = {"generated_code": "result = 2 + 2"}
        >>> result = await execute_code_stub(state)
        >>> result["execution_result"]
        '4'
    """
    writer = get_stream_writer()
    writer({
        "type": "status",
        "event": "execution_started",
        "message": "Executing...",
        "step": 3,
        "total_steps": 4
    })

    # TODO Phase 5: Replace with E2B sandbox execution
    generated_code = state.get("generated_code", "")

    try:
        # Create restricted namespace with pandas and numpy
        namespace = {"pd": pd, "np": np, "result": None}

        # Execute code in restricted environment
        # NOTE: Using empty __builtins__ to restrict access, but this is NOT
        # sufficient for production. Phase 5 adds proper OS-level isolation.
        exec(generated_code, {"__builtins__": {}, "pd": pd, "np": np}, namespace)

        # Get result
        result_value = namespace.get("result", None)

        if result_value is None:
            return {"execution_result": "Error: No 'result' variable found in code"}

        # Convert result to string for display
        # Handle pandas DataFrames, Series, and basic types
        if isinstance(result_value, pd.DataFrame):
            result_str = result_value.to_string()
        elif isinstance(result_value, pd.Series):
            result_str = result_value.to_string()
        else:
            result_str = str(result_value)

        return {"execution_result": result_str}

    except Exception as e:
        # Execution error - return error message
        return {
            "execution_result": f"Execution error: {str(e)}",
            "error": str(e),
        }


async def halt_node(state: ChatAgentState) -> dict:
    """Halt node for when max retries are exceeded.

    Returns a user-friendly error message indicating that valid code
    could not be generated after multiple attempts.

    Args:
        state: Current chat workflow state

    Returns:
        dict: State update with final_response and error
    """
    writer = get_stream_writer()
    writer({
        "type": "error",
        "event": "error",
        "message": f"Unable to generate valid code after {state.get('max_steps', 3)} attempts"
    })

    max_steps = state.get("max_steps", 3)
    validation_errors = state.get("validation_errors", [])

    error_summary = ", ".join(validation_errors) if validation_errors else "Unknown issues"

    final_response = (
        f"I was unable to generate valid code after {max_steps} attempts. "
        f"Errors encountered: {error_summary}. "
        f"Please try rephrasing your question or providing more context."
    )

    return {
        "final_response": final_response,
        "error": "max_retries_exceeded",
    }


def build_chat_graph(postgres_url: str):
    """Build and compile the chat analysis LangGraph workflow.

    Creates a StateGraph with the following flow:
    1. coding_agent: Generate Python code from query
    2. code_checker: Validate with AST + LLM (routes to execute/retry/halt)
    3. execute: Run code in restricted namespace (stub)
    4. data_analysis: Interpret results and generate explanation
    5. halt: Error handler for max retries exceeded

    Args:
        postgres_url: PostgreSQL connection URL for checkpointing

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> graph = build_chat_graph("postgresql://...")
        >>> result = await graph.ainvoke(
        ...     {"user_query": "What is the average?", ...},
        ...     config={"configurable": {"thread_id": "user123_file456"}}
        ... )
    """
    # Initialize PostgreSQL checkpointer
    checkpointer = PostgresSaver.from_conn_string(postgres_url)
    checkpointer.setup()

    # Create StateGraph
    graph = StateGraph(ChatAgentState)

    # Add nodes
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_code_stub)
    graph.add_node("data_analysis", data_analysis_agent)
    graph.add_node("halt", halt_node)

    # Add edges
    graph.set_entry_point("coding_agent")
    graph.add_edge("coding_agent", "code_checker")
    # code_checker returns Command, so routing is automatic (no add_conditional_edges needed)
    graph.add_edge("execute", "data_analysis")
    graph.set_finish_point("data_analysis")
    graph.set_finish_point("halt")

    # Compile with checkpointer
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled


def get_or_create_graph():
    """Get or create cached graph instance.

    Lazy initialization: builds graph on first call, returns cached instance thereafter.
    This avoids rebuilding the graph on every request.

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> graph = get_or_create_graph()
        >>> result = await graph.ainvoke({...}, config={...})
    """
    global _cached_graph

    if _cached_graph is None:
        settings = get_settings()
        _cached_graph = build_chat_graph(settings.database_url)

    return _cached_graph
