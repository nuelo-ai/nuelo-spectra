"""Data Analysis Agent with web search tool-calling capability.

Split into two exported functions for the LangGraph tool-calling loop:
- da_with_tools_node: LLM with optional tools bound (decides whether to search)
- da_response_node: Final response generation after tool loop completes

Supports three modes:
- MEMORY_SUFFICIENT: Answer from conversation history without code generation
- Standard mode with search: Interpret results + optionally search web for benchmarks
- Standard mode without search: Interpret results only (original behavior)
"""

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.config import get_stream_writer

from app.agents.config import (
    get_agent_prompt,
    get_agent_max_tokens,
    get_agent_provider,
    get_agent_model,
    get_agent_temperature,
    get_api_key_for_provider,
)
from app.agents.llm_factory import get_llm, validate_llm_response, EmptyLLMResponseError
from app.agents.state import ChatAgentState
from app.agents.tools import search_web
from app.config import get_settings

logger = logging.getLogger("spectra.data_analysis")


async def da_with_tools_node(state: ChatAgentState) -> dict:
    """Data Analysis Agent with tool-calling capability.

    The LLM decides whether to call search_web tool based on:
    1. Whether web_search_enabled is True (user toggled ON)
    2. Whether the query needs external data (agent's autonomous decision)

    If web_search_enabled is False, no tools are bound -- LLM cannot search.
    The LLM's response either contains tool_calls (routed to search_tools)
    or no tool_calls (routed to da_response via tools_condition).

    On subsequent calls in the tool-calling loop (after ToolNode returns),
    the state.messages contain the full tool-calling conversation, which
    the LLM uses to decide whether to search again or produce final response.

    Args:
        state: Current chat workflow state

    Returns:
        dict: State update with messages containing the LLM's response
    """
    writer = get_stream_writer()

    # Check if we are in the tool-calling loop (ToolMessages present)
    existing_messages = state.get("messages", [])
    has_tool_messages = any(
        isinstance(msg, ToolMessage) for msg in existing_messages
    )

    # Only emit analysis_started on first call (not on loop iterations)
    if not has_tool_messages:
        routing = state.get("routing_decision")
        if routing and routing.route == "MEMORY_SUFFICIENT":
            writer({
                "type": "analysis_started",
                "message": "Answering from conversation context...",
                "step": 1,
                "total_steps": 1,
            })
        else:
            writer({
                "type": "analysis_started",
                "message": "Analyzing...",
                "step": 4,
                "total_steps": 4,
            })

    # Build LLM with per-agent config
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

    # Conditionally bind tools -- ONLY if user enabled search
    web_search_enabled = state.get("web_search_enabled", False)
    if web_search_enabled:
        try:
            llm_with_tools = llm.bind_tools([search_web])
        except Exception as e:
            # Provider doesn't support tool calling -- fall back to bare LLM
            logger.warning(f"bind_tools failed ({type(e).__name__}): {e}. Falling back to no-tools mode.")
            llm_with_tools = llm
    else:
        llm_with_tools = llm  # No tools, LLM cannot request search

    # Build system prompt based on routing decision
    routing = state.get("routing_decision")
    if routing and routing.route == "MEMORY_SUFFICIENT":
        system_prompt = _build_memory_prompt(state)
    else:
        system_prompt = _build_analysis_prompt(state, web_search_enabled)

    # Build messages for the LLM
    if has_tool_messages:
        # In tool-calling loop: the SystemMessage (with JSON instructions) was
        # a local variable on the first call and is NOT in state.messages.
        # We must prepend it so the LLM still follows JSON output format.
        # Only include messages from the current tool conversation (after last
        # HumanMessage) to avoid flooding with old checkpoint history.
        last_human_idx = -1
        for i, msg in enumerate(existing_messages):
            if isinstance(msg, HumanMessage):
                last_human_idx = i
        if last_human_idx >= 0:
            tool_conversation = existing_messages[last_human_idx:]
        else:
            tool_conversation = existing_messages[-5:]
        messages = [SystemMessage(content=system_prompt)] + list(tool_conversation)
    else:
        # First call: construct fresh messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please analyze these results."),
        ]

    # Invoke LLM -- it will either return tool_calls or a final response
    response = await llm_with_tools.ainvoke(messages)

    # Validate non-empty response ONLY when LLM is NOT requesting tools.
    # In tool-calling mode, content may be empty while tool_calls is populated.
    has_tool_calls = bool(getattr(response, "tool_calls", None))
    if not has_tool_calls:
        try:
            validate_llm_response(response, provider, model, "data_analysis")
        except EmptyLLMResponseError:
            # Return a user-friendly error as AIMessage
            from langchain_core.messages import AIMessage as _AIMessage
            error_msg = (
                "The AI model returned an empty response. This may happen with certain "
                "reasoning models. Please try rephrasing your question or check the model "
                "configuration."
            )
            return {"messages": [_AIMessage(content=error_msg)]}

    # Return as message for the tool-calling loop
    return {"messages": [response]}


async def da_response_node(state: ChatAgentState) -> dict:
    """Generate final response from the Data Analysis Agent.

    Called after the tool-calling loop completes (LLM decided no more searches).

    Two paths:
    - No search used: Extract analysis from last AIMessage (reliable JSON from
      a clean LLM call without tools bound).
    - Search used: Make a FRESH LLM call (no tools bound) with search results
      included in the prompt. This guarantees reliable JSON output because
      bind_tools mode causes the LLM to unreliably follow text-based JSON
      format instructions.

    Args:
        state: Current chat workflow state with completed tool-calling conversation

    Returns:
        dict: State update with analysis, final_response, follow_up_suggestions,
              search_sources, and clean AIMessage for checkpoint.
    """
    messages = state.get("messages", [])

    # Extract current query messages (after last HumanMessage)
    last_human_idx = -1
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            last_human_idx = i
    current_query_messages = messages[last_human_idx + 1:] if last_human_idx >= 0 else messages

    # Check if search tools were used in this query
    has_current_tool_messages = any(
        isinstance(msg, ToolMessage) for msg in current_query_messages
    )

    # Extract search sources from ToolMessages
    search_sources = []
    search_results_text = ""
    for msg in current_query_messages:
        if isinstance(msg, ToolMessage):
            sources = _extract_sources_from_tool_response(msg.content)
            search_sources.extend(sources)
            search_results_text += msg.content + "\n"

    # Deduplicate sources by URL
    seen_urls = set()
    unique_sources = []
    for src in search_sources:
        if src["url"] not in seen_urls:
            seen_urls.add(src["url"])
            unique_sources.append(src)

    if has_current_tool_messages:
        # Search was used: make a fresh LLM call (no tools) for reliable JSON.
        # The tool-calling LLM's response is unreliable for JSON format.
        analysis_text, follow_ups = await _generate_analysis_with_search(
            state, search_results_text
        )
    else:
        # No search: extract from last AIMessage (reliable JSON)
        last_msg = messages[-1] if messages else None
        if last_msg and hasattr(last_msg, "content"):
            raw = last_msg.content
        else:
            raw = "Unable to generate analysis."
        analysis_text, follow_ups = _parse_analysis_json(raw)

    # Return structured response with clean AIMessage for checkpoint
    # The clean AIMessage ensures the Manager Agent sees a readable message
    # on subsequent queries, not a tool-calling message
    return {
        "analysis": analysis_text,
        "final_response": analysis_text,
        "follow_up_suggestions": follow_ups,
        "search_sources": unique_sources,
        "messages": [AIMessage(content=analysis_text)],
    }


async def _generate_analysis_with_search(
    state: ChatAgentState, search_results_text: str
) -> tuple[str, list[str]]:
    """Generate analysis with a fresh LLM call when search results are available.

    Makes a clean LLM call (no tools bound) to guarantee reliable JSON output.
    The tool-calling LLM doesn't reliably follow JSON format instructions because
    bind_tools puts it in function-calling mode.

    Args:
        state: Current chat workflow state with execution context
        search_results_text: Concatenated text of search tool results

    Returns:
        tuple: (analysis_text, follow_up_suggestions)
    """
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

    # Build prompt with search results included as context
    system_prompt = _build_analysis_prompt(state, web_search_enabled=False)
    system_prompt += f"""

**Web Search Results (incorporate relevant findings and cite sources):**
{search_results_text}"""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please analyze these results."),
    ])

    # Validate non-empty response
    try:
        content = validate_llm_response(response, provider, model, "data_analysis")
    except EmptyLLMResponseError:
        return (
            "Unable to generate analysis. The AI model returned an empty response. "
            "Please try rephrasing your question or check the model configuration.",
            [],
        )

    return _parse_analysis_json(content)


def _parse_analysis_json(raw: str) -> tuple[str, list[str]]:
    """Parse LLM response as JSON, extracting analysis and follow-up suggestions.

    Handles markdown code fences and falls back to plain text on parse failure.

    Args:
        raw: Raw LLM response content

    Returns:
        tuple: (analysis_text, follow_up_suggestions)
    """
    content = raw.strip()
    if content.startswith("```"):
        try:
            first_newline = content.index("\n")
            content = content[first_newline + 1:]
            if content.endswith("```"):
                content = content[:-3].strip()
        except ValueError:
            pass

    try:
        parsed = json.loads(content)
        analysis_text = parsed.get("analysis", raw)
        follow_ups = parsed.get("follow_up_suggestions", [])
        return analysis_text, follow_ups
    except json.JSONDecodeError:
        return raw, []


def _build_memory_prompt(state: ChatAgentState) -> str:
    """Build prompt for MEMORY_SUFFICIENT mode (answer from history).

    Args:
        state: Current chat workflow state with conversation history

    Returns:
        str: System prompt for memory-mode response
    """
    routing = state.get("routing_decision")
    context_summary = routing.context_summary if routing else ""

    # Format recent messages for the prompt (last 10)
    messages_history = state.get("messages", [])
    recent = messages_history[-10:] if len(messages_history) > 10 else messages_history
    formatted_messages = []
    for msg in recent:
        role = getattr(msg, "type", "unknown")
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        formatted_messages.append(f"[{role}]: {content}")
    conversation_text = "\n".join(formatted_messages)

    return f"""Answer the user's question using ONLY the conversation history and data context.

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
- Format the analysis text with markdown for readability

Return ONLY valid JSON with two keys: "analysis" and "follow_up_suggestions".

**JSON Schema:**
```json
{{
  "analysis": "Your response text here...",
  "follow_up_suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3"
  ]
}}
```

- "analysis": Your direct answer formatted with markdown
- "follow_up_suggestions": 2-3 natural follow-up questions the user might ask next, based on the conversation context and data. Use real column names from the data summary.

Return ONLY the JSON object. No text before or after."""


def _build_analysis_prompt(state: ChatAgentState, web_search_enabled: bool) -> str:
    """Build prompt for standard analysis mode (interpret execution results).

    Args:
        state: Current chat workflow state with execution context
        web_search_enabled: Whether web search is available for this query

    Returns:
        str: System prompt for analysis-mode response
    """
    # Load base system prompt from YAML
    system_prompt_template = get_agent_prompt("data_analysis")

    # Format prompt with execution context
    system_prompt = system_prompt_template.format(
        user_query=state["user_query"],
        executed_code=state.get("generated_code", "No code available"),
        execution_result=state.get("execution_result", "No result available"),
    )

    # Add search-aware instructions if web search is enabled
    if web_search_enabled:
        settings = get_settings()
        max_searches = settings.search_max_per_query
        search_instructions = f"""

**Web Search Instructions:**
You have access to the search_web tool. When the user's query could benefit from external benchmarks, industry data, market statistics, or comparative data:
- Call search_web with GENERIC industry/benchmarking queries (3-8 words)
- NEVER include specific values, company names, personal data, or identifiable information from the dataset in search queries
- Limit tool calls to at most {max_searches} per query
- When search results are available, incorporate external benchmarks/data into your analysis and cite sources
- When search results are not helpful, proceed with available data only

If the query does NOT need external data, do NOT call search_web -- just analyze the execution results directly.

IMPORTANT: Your final response MUST still be valid JSON with "analysis" and "follow_up_suggestions" keys, exactly as specified above. Always include 2-3 follow-up suggestions even when search results are incorporated."""
        system_prompt += search_instructions

    return system_prompt


def _extract_sources_from_tool_response(content: str) -> list[dict]:
    """Extract search sources from a ToolMessage content string.

    Parses lines matching the format "- {title}: {url}" produced by
    the search_web tool.

    Args:
        content: ToolMessage content string from search_web tool

    Returns:
        list[dict]: List of {"title": str, "url": str} dicts
    """
    sources = []
    # Match lines like: "- Title Text: https://example.com/path"
    pattern = re.compile(r"^- (.+?):\s+(https?://\S+)$", re.MULTILINE)
    for match in pattern.finditer(content):
        title = match.group(1).strip()
        url = match.group(2).strip()
        sources.append({"title": title, "url": url})
    return sources
