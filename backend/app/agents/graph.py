"""LangGraph workflow for chat analysis pipeline.

This module assembles the complete chat analysis pipeline:
Manager Agent -> (routes to) Coding Agent or Data Analysis Agent (with tools)

The Manager Agent classifies queries and routes via Command:
- MEMORY_SUFFICIENT -> da_with_tools (skip code generation, answer from history)
- CODE_MODIFICATION -> Coding Agent (modify existing code)
- NEW_ANALYSIS -> Coding Agent (fresh code generation)

The code generation pipeline:
Coding Agent -> Code Checker -> Execute -> da_with_tools

The data analysis pipeline (tool-calling loop):
da_with_tools <-> search_tools (loop via tools_condition)
da_with_tools -> da_response (when LLM has no more tool calls)

The workflow includes:
- Intelligent query routing via Manager Agent
- Conditional routing based on validation results
- Bounded retry loops with circuit breaker (max_steps=3)
- Tool-calling loop for web search (bind_tools + ToolNode)
- PostgreSQL checkpointing for thread isolation
"""

from typing import Literal
import asyncio
import os

from langgraph.graph import StateGraph
# from langgraph.checkpoint.postgres import PostgresSaver  # Temporarily disabled
from langgraph.types import Command
from langgraph.config import get_stream_writer
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.state import ChatAgentState
from app.agents.manager import manager_node
from app.agents.coding import coding_agent
from app.agents.code_checker import validate_code
from app.agents.data_analysis import da_with_tools_node, da_response_node
from app.agents.tools import search_web
from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm, validate_llm_response, EmptyLLMResponseError
from app.config import get_settings
from app.services.sandbox import E2BSandboxRuntime, ExecutionResult

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import logging

logger = logging.getLogger(__name__)


def _extract_used_dataframes(code: str, file_metadata: list[dict]) -> list[dict]:
    """Find which DataFrames from file_metadata are actually used in code.

    Checks for each file's var_name in the generated code string.
    Only files whose variable name appears in the code will be uploaded
    to the sandbox (selective loading for memory efficiency).

    Args:
        code: Generated Python code string.
        file_metadata: List of file metadata dicts, each containing
            'var_name', 'name', 'file_path', 'file_type'.

    Returns:
        List of file metadata dicts for files actually referenced in code.
    """
    used = []
    for fm in file_metadata:
        if fm["var_name"] in code:
            used.append(fm)
    return used


# Module-level cached graph instance and its checkpointer
_cached_graph = None
_cached_checkpointer = None


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
        "type": "validation_started",
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

    # Initialize LLM using per-agent config
    provider = get_agent_provider("code_checker")
    model = get_agent_model("code_checker")
    temperature = get_agent_temperature("code_checker")
    api_key = get_api_key_for_provider(provider, settings)
    max_tokens = get_agent_max_tokens("code_checker")

    # Build kwargs for provider-specific options
    kwargs = {"max_tokens": max_tokens, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    llm = get_llm(provider=provider, model=model, api_key=api_key, **kwargs)

    # Invoke LLM for logical validation
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please validate this code."),
    ]

    response = await llm.ainvoke(messages)

    # Validate non-empty response
    try:
        validation_response = validate_llm_response(response, provider, model, "code_checker")
        validation_response = validation_response.strip()
    except EmptyLLMResponseError:
        # Treat empty response as validation failure (route to retry)
        new_error_count = error_count + 1
        if new_error_count >= max_steps:
            return Command(
                goto="halt",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": ["Code checker LLM returned empty response"],
                    "error_count": new_error_count,
                },
            )
        else:
            writer({
                "type": "retry",
                "event": "retry",
                "message": "Code validation returned empty response. Retrying...",
                "attempt": new_error_count,
                "max_attempts": max_steps
            })
            return Command(
                goto="coding_agent",
                update={
                    "validation_result": "INVALID",
                    "validation_errors": ["Code checker LLM returned empty response"],
                    "error_count": new_error_count,
                },
            )

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


async def execute_in_sandbox(
    state: ChatAgentState,
) -> dict | Command[Literal["coding_agent", "halt"]]:
    """Execute Python code in E2B Firecracker microVM sandbox.

    This replaces the development stub with real OS-level isolation via E2B.
    Uploads user data file to sandbox, executes code with timeout, and handles
    errors with intelligent retry routing.

    Args:
        state: Current chat workflow state with generated_code

    Returns:
        dict: State update with execution_result on success
        Command: Routing to coding_agent (retry) or halt (exhausted) on error

    Example:
        >>> state = {"generated_code": "result = 2 + 2", "file_path": "/data.csv"}
        >>> result = await execute_in_sandbox(state)
        >>> result["execution_result"]
        '4'
    """
    writer = get_stream_writer()
    settings = get_settings()

    # Emit code display event BEFORE execution (EXEC-05)
    writer({
        "type": "content",
        "event": "code_display",
        "message": "Code validated, preparing execution...",
        "generated_code": state.get("generated_code", ""),
        "step": 3,
        "total_steps": 4
    })

    generated_code = state.get("generated_code", "")
    file_metadata = state.get("file_metadata", [])

    # Multi-file mode: file_metadata is non-empty (session-based flow)
    if file_metadata:
        files_to_load = _extract_used_dataframes(generated_code, file_metadata)
        loading_lines = ["import pandas as pd"]
        data_files_to_upload: list[tuple[bytes, str]] = []

        for fm in files_to_load:
            file_path = fm["file_path"]
            filename = fm["name"]
            var_name = fm["var_name"]
            file_ext = os.path.splitext(filename)[1].lower()

            # Read file from disk -- fail entire query if any referenced file is unreadable
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                data_files_to_upload.append((file_bytes, filename))
            except (FileNotFoundError, IOError) as e:
                writer({"type": "error", "event": "error",
                        "message": f"Cannot read file: {filename}"})
                return Command(goto="halt", update={
                    "execution_result": f"Error: Cannot read file {filename}: {e}",
                    "error": "file_read_error",
                })

            if file_ext in ['.xlsx', '.xls']:
                loading_lines.append(f"{var_name} = pd.read_excel('/home/user/{filename}')")
            else:
                loading_lines.append(f"{var_name} = pd.read_csv('/home/user/{filename}')")

        file_loading_code = "\n".join(loading_lines) + "\n\n"
        full_code = file_loading_code + generated_code

        # Emit execution started status
        writer({
            "type": "execution_started",
            "message": "Executing...",
            "step": 3,
            "total_steps": 4
        })

        # Create E2B runtime and execute with multi-file upload
        runtime = E2BSandboxRuntime(timeout_seconds=settings.sandbox_timeout_seconds)

        result: ExecutionResult = await asyncio.to_thread(
            runtime.execute,
            code=full_code,
            timeout=float(settings.sandbox_timeout_seconds),
            data_files=data_files_to_upload,
        )

    else:
        # Single-file legacy mode: unchanged behavior
        file_path = state.get("file_path", "")
        data_file = None
        data_filename = None
        if file_path:
            data_filename = os.path.basename(file_path)
            try:
                with open(file_path, "rb") as f:
                    data_file = f.read()
            except FileNotFoundError:
                writer({
                    "type": "error",
                    "event": "error",
                    "message": "Data file not found. Please re-upload your file and try again."
                })
                return Command(
                    goto="halt",
                    update={
                        "execution_result": "Error: Data file not found on server",
                        "error": "file_not_found",
                    },
                )
            except (IOError, OSError) as e:
                writer({
                    "type": "error",
                    "event": "error",
                    "message": "Unable to read data file. Please re-upload your file and try again."
                })
                return Command(
                    goto="halt",
                    update={
                        "execution_result": f"Error: Unable to read data file: {e}",
                        "error": "file_read_error",
                    },
                )

        # Emit execution started status
        writer({
            "type": "execution_started",
            "message": "Executing...",
            "step": 3,
            "total_steps": 4
        })

        # Create E2B runtime and execute in thread pool (SDK is synchronous)
        runtime = E2BSandboxRuntime(timeout_seconds=settings.sandbox_timeout_seconds)

        # Prepend file loading code if data file exists
        if data_file and data_filename:
            # Inject pandas import and file loading before generated code
            # Detect file type by extension and use appropriate reader
            file_ext = os.path.splitext(data_filename)[1].lower()
            if file_ext in ['.xlsx', '.xls']:
                # Excel file - use read_excel
                file_loading_code = f"""import pandas as pd
df = pd.read_excel('/home/user/{data_filename}')

"""
            else:
                # CSV file - use read_csv with encoding fallback
                file_loading_code = f"""import pandas as pd
try:
    df = pd.read_csv('/home/user/{data_filename}', encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv('/home/user/{data_filename}', encoding='latin-1')
    except UnicodeDecodeError:
        df = pd.read_csv('/home/user/{data_filename}', encoding='cp1252')

"""
            full_code = file_loading_code + generated_code
        else:
            full_code = generated_code

        result: ExecutionResult = await asyncio.to_thread(
            runtime.execute,
            code=full_code,
            timeout=float(settings.sandbox_timeout_seconds),
            data_file=data_file,
            data_filename=data_filename,
        )

    # Handle execution result
    if result.success:
        # Success: parse JSON output from stdout
        import json
        execution_result = None

        if result.stdout:
            # Try to parse JSON from last line of stdout (where print(json.dumps()) outputs)
            stdout_text = "\n".join(result.stdout)
            try:
                # Look for JSON in stdout
                for line in reversed(result.stdout):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        parsed = json.loads(line.strip())
                        if "result" in parsed:
                            execution_result = json.dumps(parsed["result"])
                            break
                # If no JSON found, use raw stdout
                if execution_result is None:
                    execution_result = stdout_text
            except json.JSONDecodeError:
                # Fallback: use raw stdout if JSON parsing fails
                execution_result = stdout_text
        elif result.results:
            # Fallback: use results list if no stdout
            execution_result = str(result.results)
        else:
            execution_result = "Code executed successfully (no output)"

        return {"execution_result": execution_result}
    else:
        # Execution failed: check retry budget
        error_msg = f"{result.error['name']}: {result.error['value']}"
        new_error_count = state.get("error_count", 0) + 1

        if new_error_count < settings.sandbox_max_retries + 1:
            # Retries remaining: route to coding_agent with error context
            writer({
                "type": "retry",
                "event": "retry",
                "message": f"Execution failed: {error_msg}. Retrying with adjusted code...",
                "attempt": new_error_count,
                "max_attempts": state.get("max_steps", 3)
            })
            return Command(
                goto="coding_agent",
                update={
                    "execution_result": f"Execution error: {error_msg}",
                    "validation_errors": [f"Execution error: {error_msg}. Please fix the code."],
                    "error_count": new_error_count,
                },
            )
        else:
            # Retries exhausted: route to halt
            writer({
                "type": "error",
                "event": "error",
                "message": f"Execution failed after {new_error_count} attempts"
            })
            return Command(
                goto="halt",
                update={
                    "execution_result": f"Execution error: {error_msg}",
                    "error_count": new_error_count,
                    "error": "execution_failed",
                },
            )


async def halt_node(state: ChatAgentState) -> dict:
    """Halt node for when max retries are exceeded or unrecoverable errors occur.

    Returns user-friendly error messages tailored to the type of failure:
    - execution_failed: code ran but failed in sandbox (timeout, runtime error)
    - file_not_found / file_read_error: data file unavailable
    - max_retries_exceeded: validation failures exhausted retry budget

    Args:
        state: Current chat workflow state

    Returns:
        dict: State update with final_response and error
    """
    writer = get_stream_writer()
    error_type = state.get("error", "")
    max_steps = state.get("max_steps", 3)

    if error_type == "execution_failed":
        writer({
            "type": "error",
            "event": "error",
            "message": "Unable to complete analysis after multiple attempts"
        })
        final_response = (
            "Unable to complete analysis. "
            "Try: filtering data first, breaking into simpler questions, or rephrasing your query."
        )
    elif error_type in ("file_not_found", "file_read_error"):
        writer({
            "type": "error",
            "event": "error",
            "message": "Data file unavailable"
        })
        final_response = (
            "Unable to access your data file. "
            "Please re-upload your file and try again."
        )
    else:
        writer({
            "type": "error",
            "event": "error",
            "message": f"Unable to generate valid code after {max_steps} attempts"
        })
        validation_errors = state.get("validation_errors", [])
        error_summary = ", ".join(validation_errors) if validation_errors else "Unknown issues"
        final_response = (
            f"I was unable to generate valid code after {max_steps} attempts. "
            f"Errors encountered: {error_summary}. "
            f"Please try rephrasing your question or providing more context."
        )

    return {
        "final_response": final_response,
        "error": error_type or "max_retries_exceeded",
        "messages": [AIMessage(content=final_response)],
    }


def build_chat_graph(checkpointer=None):
    """Build and compile the chat analysis LangGraph workflow.

    Creates a StateGraph with the following flow:
    1. manager: Classify query and route via Command
       - MEMORY_SUFFICIENT -> da_with_tools (answer from history, may skip tools)
       - CODE_MODIFICATION -> coding_agent (modify existing code)
       - NEW_ANALYSIS -> coding_agent (fresh code generation)
    2. coding_agent: Generate Python code from query
    3. code_checker: Validate with AST + LLM (routes to execute/retry/halt)
    4. execute: Run code in E2B sandbox
    5. da_with_tools: LLM with optional search tools bound (tool-calling loop)
    6. search_tools: ToolNode that executes search_web tool
    7. da_response: Final response generation after tool loop
    8. halt: Error handler for max retries exceeded

    Tool-calling loop: da_with_tools <-> search_tools (via tools_condition)
    When LLM has no more tool calls, routes to da_response.

    Args:
        checkpointer: Optional PostgreSQL checkpointer for session persistence

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> graph = build_chat_graph(checkpointer)
        >>> result = await graph.ainvoke(
        ...     {"user_query": "What is the average?", ...},
        ...     config={"configurable": {"thread_id": "user123_file456"}}
        ... )
    """
    # Create StateGraph
    graph = StateGraph(ChatAgentState)

    # Add nodes
    graph.add_node("manager", manager_node)
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("halt", halt_node)

    # Tool-calling nodes for Data Analysis Agent
    graph.add_node("da_with_tools", da_with_tools_node)
    graph.add_node("search_tools", ToolNode(
        [search_web],
        handle_tool_errors=True,
    ))
    graph.add_node("da_response", da_response_node)

    # Set entry point to Manager Agent (routes via Command, no explicit edges needed)
    graph.set_entry_point("manager")

    # Add edges for code generation pipeline
    graph.add_edge("coding_agent", "code_checker")
    # code_checker returns Command, so routing is automatic (no add_conditional_edges needed)
    graph.add_edge("execute", "da_with_tools")

    # Tool-calling loop: da_with_tools decides via tools_condition
    graph.add_conditional_edges(
        "da_with_tools",
        tools_condition,
        {
            "tools": "search_tools",       # LLM wants to search -> execute tool
            "__end__": "da_response",       # LLM done searching -> generate response
        },
    )
    graph.add_edge("search_tools", "da_with_tools")  # Tool results -> back to LLM

    # Finish points
    graph.set_finish_point("da_response")
    graph.set_finish_point("halt")

    # Compile with checkpointer
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled


def get_or_create_graph(checkpointer=None):
    """Get or create cached graph instance.

    Lazy initialization: builds graph on first call, returns cached instance thereafter.
    Rebuilds the graph if the checkpointer changes (e.g., first call was without
    checkpointer, then lifespan provides one).

    Thread ID formats (v0.3):
    - Session-based: "session_{session_id}_user_{user_id}" (multi-file conversations)
    - File-based: "file_{file_id}_user_{user_id}" (legacy, backward compat)

    Args:
        checkpointer: Optional PostgreSQL checkpointer for session persistence

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> graph = get_or_create_graph(checkpointer)
        >>> # Session-based conversation
        >>> config = {"configurable": {"thread_id": "session_abc123_user_xyz789"}}
        >>> result = await graph.ainvoke({...}, config=config)
    """
    global _cached_graph, _cached_checkpointer

    if _cached_graph is None or checkpointer is not _cached_checkpointer:
        _cached_graph = build_chat_graph(checkpointer)
        _cached_checkpointer = checkpointer

    return _cached_graph
