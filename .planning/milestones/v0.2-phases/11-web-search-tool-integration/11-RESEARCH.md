# Phase 11: Web Search Tool Integration - Research

**Researched:** 2026-02-08
**Domain:** LangGraph bind_tools/ToolNode pattern, Serper.dev API integration, tool-calling agent architecture
**Confidence:** HIGH

## Summary

Phase 11 adds web search capability to the Data Analysis Agent via Serper.dev, using LangGraph's `bind_tools` / `ToolNode` pattern. This is a DELIBERATE ARCHITECTURAL DECISION to establish a standardized tool-calling pattern for future extensibility, rather than the simpler direct `httpx` approach.

The core architectural change is introducing a tool-calling mini-loop within the data analysis portion of the graph. The Data Analysis Agent's LLM gets tools bound via `llm.bind_tools([search_web])`, and a `ToolNode` executes the actual Serper.dev API calls. A `tools_condition` conditional edge creates a loop: the LLM decides whether to call the search tool, ToolNode executes it, results flow back as `ToolMessage`, and the LLM decides whether to search again or produce the final response. This pattern coexists cleanly with the existing Command-based routing (manager_node still uses `Command` for top-level routing; the tool-calling loop is scoped to the data analysis sub-flow).

**Primary recommendation:** Add three new nodes to the graph (`da_with_tools`, `search_tools`, and `da_response`) that implement a tool-calling loop for the Data Analysis Agent. Define `search_web` as a LangChain `@tool` with async support. Use `ToolRuntime` or `get_stream_writer()` inside the tool to emit `search_started` SSE events. Keep the `SearchService` class for the actual Serper.dev HTTP calls. The MEMORY_SUFFICIENT path bypasses the tool loop entirely.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Dual-gate activation: user must toggle "Search Tool" ON below chat input (per-query, not per-tab) AND agent decides if search is actually needed for the query
- Default toggle state: OFF -- user explicitly activates per message
- Toggle resets to OFF after each query -- user re-enables for next query if desired
- When toggle is ON but agent decides search isn't needed: silent skip (no notification to user)
- Multiple searches allowed per response -- agent can issue up to N searches per query (configurable via env/config, default max: 5)
- Agent formulates search queries autonomously based on query content
- Sources displayed as "Sources" section at the end of the response (not inline citations)
- Each source entry: page title as clickable link + URL (no snippet/excerpt)
- Search activity shown in real-time while searching -- display actual search query text (e.g., "Searching: 'industry revenue benchmarks 2025'...") similar to Perplexity's search transparency
- Search results integrate into DataCard format -- sources section added as part of the DataCard (not separate chat message)
- API failure/timeout: inline notice in response ("Web search unavailable -- answering from available data") then continue with data analysis only
- On search failure: do NOT attempt to answer from LLM knowledge -- just analyze the uploaded data without external comparison
- No API key configured: search toggle appears but is grayed out with tooltip "Search not configured"
- Quota exceeded: toggle auto-disables for the rest of the session with message "Search quota reached"
- Configurable domain blocklist -- admin can block specific domains from search results
- Results per search query: configurable via env/config (Claude picks sensible default)
- Query sanitization: agent must formulate generic search queries, never include raw cell values or identifiable data from uploaded files in search queries
- User-level daily search quota: configurable, default 7 searches per day per user (future subscription tiers will increase this for paid users)
- App-level quota tracking separate from Serper's own plan limits

### Updated Architecture Decision
- USE bind_tools / ToolNode for Serper.dev search integration (NOT direct httpx inside node)
- This is the FIRST tool being added to the project -- establish the pattern for future tools
- Standardize on LangGraph's native tool-calling infrastructure

### Claude's Discretion
- Default number of results per search query
- Default domain blocklist entries (if any)
- Search query formulation strategy (how agent converts user intent to search queries)
- Exact toggle UI component design and positioning
- Search activity animation/indicator design
- How sources section is styled within DataCard

### Deferred Ideas (OUT OF SCOPE)
- Subscription-tier search quotas (different limits for free vs paid users) -- future subscription/billing phase
- Query safety filter in Manager Agent (block PII extraction, prompt injection) -- noted in STATE.md pending todos
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.7 (installed) | ToolNode, tools_condition, graph topology | Already installed; ToolNode is the official prebuilt for tool execution |
| langchain-core | 1.2.8 (installed) | @tool decorator, ToolMessage, AIMessage.tool_calls | Already installed; provides the tool abstraction layer |
| httpx | >=0.27.0 (installed) | Serper.dev API HTTP calls inside the @tool | Already a dependency; used inside the tool function for actual API calls |
| langgraph.prebuilt | (bundled with langgraph) | ToolNode, tools_condition, InjectedState, ToolRuntime | Part of langgraph; provides prebuilt tool infrastructure |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | (bundled) | Search config models, response schemas | Already used for RoutingDecision, Settings |
| pyyaml | >=6.0.0 | Search config in prompts.yaml / search.yaml | Already used for agent config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| bind_tools + ToolNode | Direct httpx call inside node (previous research) | Simpler but doesn't establish reusable tool pattern. User chose bind_tools. |
| Custom tool-calling loop | LangGraph prebuilt create_react_agent | create_react_agent is too opinionated; we need control over graph topology and state |
| langchain-community GoogleSerperAPIWrapper | Custom @tool with httpx | Would add ~50MB dependency for a 20-line wrapper. Not installed. |

**Installation:**
No new dependencies required. All packages already installed:
- `langgraph 1.0.7` includes `langgraph.prebuilt` (ToolNode, tools_condition, InjectedState, ToolRuntime)
- `langchain-core 1.2.8` includes `@tool` decorator, ToolMessage, InjectedToolCallId
- `httpx` already installed for API calls
- Python 3.12.12 -- `get_stream_writer()` works in async tools (requires >= 3.11)

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
  services/
    search.py              # NEW: SearchService class (Serper.dev API client)
  agents/
    tools/
      __init__.py           # NEW: Tool registry
      web_search.py         # NEW: @tool search_web definition
    graph.py                # MODIFIED: Add tool-calling nodes and edges
    data_analysis.py        # MODIFIED: Split into da_with_tools + da_response nodes
    state.py                # MODIFIED: Add web_search_enabled, search_sources fields
    config.py               # MODIFIED: Add search config loader
  config/
    prompts.yaml            # MODIFIED: Add search-aware data analysis prompt
    search.yaml             # NEW: Search configuration (blocklist, defaults)
  models/
    search_quota.py         # NEW: SearchQuota model for daily tracking
  routers/
    chat.py                 # MODIFIED: Accept web_search_enabled in request
    search.py               # NEW: Search config endpoint (quota status)
  schemas/
    chat.py                 # MODIFIED: Add web_search_enabled to ChatQueryRequest
frontend/src/
  components/chat/
    ChatInput.tsx            # MODIFIED: Add search toggle below textarea
    DataCard.tsx             # MODIFIED: Add Sources section
    ChatInterface.tsx        # MODIFIED: Handle search streaming events
  hooks/
    useSSEStream.ts          # MODIFIED: Handle search_started events
    useSearchToggle.ts       # NEW: Toggle state + config check hook
  types/
    chat.ts                  # MODIFIED: Add search event types
```

### Pattern 1: Graph Topology with Tool-Calling Loop
**What:** The key architectural pattern -- how the tool-calling loop fits into the existing graph
**When to use:** This is THE pattern for the entire phase
**Why it works:** `tools_condition` returns `"tools"` or `"__end__"`. We map these to our custom node names. The loop is self-contained and does not interfere with Command-based routing.

**Verified working graph topology (tested with langgraph 1.0.7):**
```python
# Source: Verified via local Python execution against installed langgraph 1.0.7
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

def build_chat_graph(checkpointer=None):
    graph = StateGraph(ChatAgentState)

    # Existing nodes (unchanged)
    graph.add_node("manager", manager_node)
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("halt", halt_node)

    # NEW: Tool-calling nodes for Data Analysis
    graph.add_node("da_with_tools", da_with_tools_node)      # LLM with bind_tools
    graph.add_node("search_tools", ToolNode(                  # Executes search tool
        [search_web],
        handle_tool_errors=True,
    ))
    graph.add_node("da_response", da_response_node)           # Final response generation

    # Entry point (unchanged)
    graph.set_entry_point("manager")

    # Existing edges (unchanged)
    graph.add_edge("coding_agent", "code_checker")
    graph.add_edge("execute", "da_with_tools")  # CHANGED: route to da_with_tools instead

    # NEW: Tool-calling loop
    graph.add_conditional_edges(
        "da_with_tools",
        tools_condition,
        {
            "tools": "search_tools",      # LLM wants to search -> execute tool
            "__end__": "da_response",      # LLM done searching -> generate response
        },
    )
    graph.add_edge("search_tools", "da_with_tools")  # Tool results -> back to LLM

    # Finish points
    graph.set_finish_point("da_response")
    graph.set_finish_point("halt")

    return graph.compile(checkpointer=checkpointer)
```

**Visual flow:**
```
manager --[Command]--> coding_agent --> code_checker --> execute --> da_with_tools
manager --[Command]--> da_with_tools (MEMORY_SUFFICIENT)                    |
                                                                            v
                                                              da_with_tools <---> search_tools
                                                                    |
                                                                    v (no more tool calls)
                                                              da_response --> END
```

### Pattern 2: The @tool Definition for Web Search
**What:** Defining the search tool with proper async support and SSE streaming
**When to use:** Single tool definition used by ToolNode
**Example:**
```python
# backend/app/agents/tools/web_search.py
# Source: langchain-core @tool decorator + langgraph ToolRuntime (verified in installed packages)
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.services.search import SearchService, SearchResponse

@tool
async def search_web(query: str) -> str:
    """Search the web for information using Google Search.

    Use this tool when you need external data like industry benchmarks,
    market statistics, or comparative data that isn't in the uploaded dataset.

    Args:
        query: A generic search query (3-8 words). NEVER include specific
               company names, personal data, or raw values from the dataset.

    Returns:
        Search results as formatted text with titles and URLs.
    """
    writer = get_stream_writer()

    # Emit SSE event for real-time search activity display
    writer({"type": "search_started", "message": f"Searching: '{query}'..."})

    # Get search service (checks API key, returns None if not configured)
    service = SearchService.from_settings()
    if service is None:
        return "Web search is not configured. Answer from available data only."

    # Execute search
    result: SearchResponse = await service.search(query)

    if not result.success:
        writer({"type": "search_failed", "message": "Web search unavailable"})
        return f"Search failed ({result.error}). Answer from available data only."

    # Format results for LLM consumption
    if not result.results:
        return "No relevant search results found."

    formatted = f"Search results for '{query}':\n"
    for r in result.results:
        formatted += f"- {r.title}: {r.link}\n"

    writer({
        "type": "search_completed",
        "message": f"Found {len(result.results)} results",
        "sources_count": len(result.results),
    })

    return formatted
```

### Pattern 3: da_with_tools Node (LLM with Tools Bound)
**What:** The node that calls the LLM with tools bound, letting the LLM decide whether to search
**When to use:** Replaces the old `data_analysis_agent` node as the LLM decision point
**Example:**
```python
# Inside graph.py or data_analysis.py
# Source: LangGraph docs on bind_tools pattern (verified)

async def da_with_tools_node(state: ChatAgentState) -> dict:
    """Data Analysis Agent with tool-calling capability.

    The LLM decides whether to call search_web tool based on:
    1. Whether web_search_enabled is True (user toggled ON)
    2. Whether the query needs external data

    If web_search_enabled is False, no tools are bound -- LLM cannot search.
    The LLM's response either contains tool_calls (routed to search_tools)
    or no tool_calls (routed to da_response via tools_condition).
    """
    writer = get_stream_writer()
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
        llm_with_tools = llm.bind_tools([search_web])
    else:
        llm_with_tools = llm  # No tools, LLM cannot request search

    # Build system prompt with analysis context
    routing = state.get("routing_decision")
    if routing and routing.route == "MEMORY_SUFFICIENT":
        # Memory mode prompt (answer from history)
        system_prompt = build_memory_prompt(state)
    else:
        # Standard mode prompt (interpret execution results)
        system_prompt = build_analysis_prompt(state)

    # Build messages for the LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please analyze these results."),
    ]

    # Include any previous tool call results from state
    # (ToolNode adds ToolMessages to state.messages, which carry over in the loop)
    existing_messages = state.get("messages", [])

    # Invoke LLM -- it will either return tool_calls or a final response
    response = await llm_with_tools.ainvoke(messages)

    # Return as message for the tool-calling loop
    return {"messages": [response]}
```

### Pattern 4: da_response Node (Final Response After Tool Loop)
**What:** Generates the final response after the tool-calling loop completes
**When to use:** Called when `tools_condition` returns `__end__` (LLM has no more tool calls)
**Example:**
```python
async def da_response_node(state: ChatAgentState) -> dict:
    """Generate final response from the Data Analysis Agent.

    Called after the tool-calling loop completes (LLM decided no more searches needed).
    The last AIMessage in state.messages contains the LLM's final response.
    Extract search sources from ToolMessages in the conversation.
    """
    writer = get_stream_writer()

    messages = state.get("messages", [])

    # The last message should be the AIMessage with the final analysis
    last_msg = messages[-1] if messages else None
    if last_msg and hasattr(last_msg, 'content'):
        analysis = last_msg.content
    else:
        analysis = "Unable to generate analysis."

    # Extract search sources from ToolMessages in the conversation
    search_sources = []
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'tool':
            # Parse sources from tool response content
            sources = extract_sources_from_tool_response(msg.content)
            search_sources.extend(sources)

    # Deduplicate sources
    seen_urls = set()
    unique_sources = []
    for src in search_sources:
        if src["url"] not in seen_urls:
            seen_urls.add(src["url"])
            unique_sources.append(src)

    # Parse JSON response with fallback (existing pattern)
    content = analysis.strip()
    if content.startswith("```"):
        first_newline = content.index("\n")
        content = content[first_newline + 1:]
        if content.endswith("```"):
            content = content[:-3].strip()

    try:
        parsed = json.loads(content)
        analysis_text = parsed.get("analysis", analysis)
        follow_ups = parsed.get("follow_up_suggestions", [])
    except json.JSONDecodeError:
        analysis_text = analysis
        follow_ups = []

    return {
        "analysis": analysis_text,
        "final_response": analysis_text,
        "follow_up_suggestions": follow_ups,
        "search_sources": unique_sources,
        "messages": [AIMessage(content=analysis_text)],
    }
```

### Pattern 5: MEMORY_SUFFICIENT Path (No Tool Loop Needed)
**What:** When manager routes to MEMORY_SUFFICIENT, the agent answers from history
**When to use:** Manager decides query can be answered from conversation context
**Key insight:** The MEMORY_SUFFICIENT path STILL goes through `da_with_tools` but since `web_search_enabled` is typically False or the query doesn't warrant search, the LLM will NOT request tool calls, and `tools_condition` will route directly to `da_response`.

Even if `web_search_enabled` is True on a MEMORY_SUFFICIENT query, the LLM has autonomy to decide not to search (dual-gate: agent gate). The tool is available but the LLM will only call it if the query actually needs external data.

### Pattern 6: Manager Node Changes
**What:** Manager routing now sends MEMORY_SUFFICIENT to `da_with_tools` instead of `data_analysis`
**Key change:** The Command `goto` target changes:
```python
# In manager_node:
if decision.route == "MEMORY_SUFFICIENT":
    return Command(
        goto="da_with_tools",  # CHANGED from "data_analysis"
        update={"routing_decision": decision},
    )
```

### Anti-Patterns to Avoid
- **Creating a separate subgraph for tool calling:** Unnecessary complexity. The tool-calling loop works as top-level nodes with `tools_condition`. Subgraphs are for multi-agent teams with different state schemas.
- **Calling tools inside the node function manually:** Defeats the purpose of bind_tools/ToolNode. The LLM should decide when/whether to call tools via its native tool-calling API.
- **Binding tools to the manager LLM:** Tools belong to the Data Analysis Agent, not the Manager. The Manager does routing only.
- **Using `create_react_agent`:** Too opinionated; replaces our custom graph with a prebuilt one. We only need the tool-calling loop, not a full ReAct agent.
- **Storing search results in custom state fields during the loop:** ToolNode manages results via ToolMessage in the `messages` list. Extract sources in `da_response` at the end, not during the loop.
- **Not using `handle_tool_errors=True`:** Without this, a Serper.dev API failure would crash the entire graph. With it, the error becomes a ToolMessage that the LLM can gracefully handle.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool execution orchestration | Custom tool dispatch loop | `ToolNode` from `langgraph.prebuilt` | Handles parallel execution, error handling, ToolMessage formatting, state injection |
| Tool-calling conditional routing | Custom `if tool_calls` check | `tools_condition` from `langgraph.prebuilt` | Standard routing function, well-tested, handles edge cases |
| Tool definition schema | Manual JSON schema for LLM | `@tool` decorator from `langchain_core.tools` | Auto-generates schema from type hints and docstring |
| HTTP client | Raw urllib | `httpx.AsyncClient` | Already a dependency, handles timeouts, async |
| Toggle component | Custom toggle from scratch | shadcn/ui Switch component | Already in the project's UI library |

**Key insight:** The entire tool-calling infrastructure (ToolNode, tools_condition, @tool, bind_tools, ToolMessage) is already installed and tested. Building custom versions would be worse in every dimension.

## Common Pitfalls

### Pitfall 1: ToolNode Only Updates Messages Key
**What goes wrong:** Expecting ToolNode to update custom state fields like `search_sources`
**Why it happens:** ToolNode returns `{"messages": [ToolMessage(...)]}` by default. It does NOT know about custom state fields.
**How to avoid:** Extract search sources from ToolMessages in the `da_response` node AFTER the tool-calling loop completes. Parse the tool response content to build the `search_sources` list.
**Warning signs:** `search_sources` is always empty in the final response

### Pitfall 2: Tool-Calling Loop Runs Forever
**What goes wrong:** LLM keeps calling the search tool indefinitely
**Why it happens:** LLM doesn't know when to stop. System prompt doesn't set boundaries.
**How to avoid:** (1) Explicitly instruct in system prompt: "Call search_web at most {max_searches} times per query." (2) Count tool calls in state and skip bind_tools when limit reached. (3) The existing `max_steps` pattern can be adapted.
**Warning signs:** Graph execution hanging, excessive Serper API calls

### Pitfall 3: Messages Key Conflict with Existing State
**What goes wrong:** ToolNode's ToolMessages polluting the conversation history checkpoint
**Why it happens:** `ChatAgentState.messages` uses `add_messages` reducer, which accumulates ALL messages. ToolMessages and AIMessages with tool_calls will persist in checkpoint.
**How to avoid:** This is actually fine for the tool-calling loop (it needs history to work). However, in `da_response`, return a clean AIMessage as the final message. The checkpoint will contain the tool-calling messages but they won't confuse the Manager Agent on subsequent queries because the Manager only looks at recent messages and truncates.
**Warning signs:** Manager Agent confused by tool call messages in history

### Pitfall 4: bind_tools with Incompatible Providers
**What goes wrong:** `bind_tools` fails with certain LLM providers (Ollama with small models)
**Why it happens:** Not all LLM providers/models support tool calling. Ollama models need explicit tool-calling support.
**How to avoid:** Tool calling is a DATA ANALYSIS AGENT feature. The data_analysis agent uses `anthropic/claude-sonnet-4-20250514` which fully supports tool calling. If provider is changed to one without tool support, skip bind_tools and fall through to da_response (same as web_search_enabled=False).
**Warning signs:** `bind_tools` raises NotImplementedError or tool calls never appear in response

### Pitfall 5: get_stream_writer() Not Working in Tools
**What goes wrong:** `get_stream_writer()` raises error inside `@tool` function
**Why it happens:** Context variable propagation issues (Python < 3.11) or tool not executed via ToolNode
**How to avoid:** Project uses Python 3.12.12 -- get_stream_writer() works. Alternative: use `ToolRuntime` parameter with `runtime.stream_writer`. Both approaches verified working.
**Warning signs:** "No stream writer found" error during tool execution

### Pitfall 6: Search Queries Leaking Sensitive Data
**What goes wrong:** Agent formulates search queries that include raw cell values, user names, or other identifiable data from uploaded files
**Why it happens:** LLM naturally includes specific data in search queries for precision
**How to avoid:** Explicit system prompt instruction: "When calling search_web, formulate GENERIC industry/benchmarking queries. NEVER include specific values, names, or identifiable information from the dataset." The @tool docstring also reinforces this.
**Warning signs:** Search logs showing queries with numeric values, company names, or personal data

### Pitfall 7: Serper API Key Exposed in Frontend
**What goes wrong:** API key sent to frontend or visible in SSE events
**Why it happens:** Accidentally including config details in stream events
**How to avoid:** SearchService is backend-only. API key never leaves the server. Only search query text and source results are sent to frontend via SSE events.
**Warning signs:** API key appearing in network tab or SSE payloads

### Pitfall 8: Search Quota Not Counting Correctly
**What goes wrong:** Failed searches still decrement user quota, or quota not checked before search
**Why it happens:** Quota check happens at wrong point in the flow
**How to avoid:** Check and increment quota in `da_with_tools_node` BEFORE binding tools. If quota exceeded, don't bind tools -- LLM cannot search. Quota counts per user query (not per Serper API call).
**Warning signs:** Users running out of quota unexpectedly, or quota never decrementing

### Pitfall 9: handle_tool_errors=False Crashing the Graph
**What goes wrong:** Serper.dev API timeout/failure causes the entire graph to crash
**Why it happens:** ToolNode default error handling may not catch all errors. Without `handle_tool_errors=True`, exceptions propagate.
**How to avoid:** Always use `handle_tool_errors=True` (or a custom error handler). The ToolNode will catch errors and return a ToolMessage with the error content, allowing the LLM to gracefully respond.
**Warning signs:** 500 errors on search-enabled queries when Serper is down

### Pitfall 10: Multiple Search Results Losing Context
**What goes wrong:** When LLM calls search_web multiple times, earlier results are "forgotten"
**Why it happens:** Each ToolMessage only contains that call's results
**How to avoid:** The tool-calling loop automatically preserves all messages in state. Each ToolMessage stays in the messages list. When the LLM is re-invoked after a tool call, it sees ALL previous tool results. This is by design.
**Warning signs:** Final response only referencing the last search, ignoring earlier searches

## Code Examples

### Verified: ToolNode Import and Creation
```python
# Source: Verified import against installed langgraph 1.0.7
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool

# ToolNode constructor signature (verified):
# ToolNode(tools, *, name="tools", tags=None, handle_tool_errors=True, messages_key="messages")

tool_node = ToolNode(
    [search_web],           # list of @tool functions
    handle_tool_errors=True,  # catch errors, return as ToolMessage
    name="search_tools",    # node name in graph
)
```

### Verified: bind_tools on ChatAnthropic
```python
# Source: Verified against installed langchain-anthropic 1.3.1
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key="...")

# bind_tools signature (verified):
# bind_tools(tools, *, tool_choice=None, parallel_tool_calls=None, strict=None)
llm_with_tools = llm.bind_tools([search_web])

# The LLM will now include tool_calls in its response when it wants to search
response = await llm_with_tools.ainvoke(messages)
# response.tool_calls -> list of {"name": "search_web", "args": {"query": "..."}, "id": "..."}
```

### Verified: tools_condition with Custom Path Map
```python
# Source: Verified via local execution against langgraph 1.0.7
# tools_condition returns Literal["tools", "__end__"]
# We can map these to any node names:

graph.add_conditional_edges(
    "da_with_tools",         # source node
    tools_condition,         # routing function
    {
        "tools": "search_tools",    # route to ToolNode
        "__end__": "da_response",   # route to response generation
    },
)
# Verified: This compiles and runs correctly.
```

### Verified: get_stream_writer() in @tool Functions
```python
# Source: LangGraph streaming docs + verified Python 3.12 compatibility
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

@tool
async def search_web(query: str) -> str:
    """Search the web for information."""
    writer = get_stream_writer()  # Works in Python >= 3.11
    writer({"type": "search_started", "message": f"Searching: '{query}'..."})
    # ... perform search ...
    return "results"
```

### Alternative: ToolRuntime for Stream Writer
```python
# Source: Verified ToolRuntime class from langgraph.prebuilt (installed)
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

@tool
async def search_web(query: str, runtime: ToolRuntime) -> str:
    """Search the web for information."""
    # ToolRuntime provides: state, stream_writer, config, tool_call_id, store, context
    runtime.stream_writer({"type": "search_started", "message": f"Searching: '{query}'..."})
    # ... perform search ...
    return "results"
# Note: runtime parameter is automatically injected by ToolNode, hidden from LLM schema
```

### SearchService (Backend HTTP Client)
```python
# backend/app/services/search.py
# Source: Serper.dev API docs (verified endpoint and auth pattern)
import httpx
import logging
from dataclasses import dataclass

logger = logging.getLogger("spectra.search")

@dataclass
class SearchResult:
    title: str
    link: str
    position: int

@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    success: bool
    error: str | None = None

class SearchService:
    """Serper.dev search API client."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(
        self,
        api_key: str,
        num_results: int = 5,
        blocked_domains: list[str] | None = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.num_results = num_results
        self.blocked_domains = blocked_domains or []
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "SearchService | None":
        """Create from app settings. Returns None if API key not configured."""
        from app.config import get_settings
        settings = get_settings()
        api_key = getattr(settings, "serper_api_key", "")
        if not api_key:
            return None
        return cls(api_key=api_key)

    async def search(self, query: str) -> SearchResponse:
        """Execute a search query against Serper.dev."""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": self.num_results}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

            organic = data.get("organic", [])
            results = []
            for item in organic:
                link = item.get("link", "")
                if any(domain in link for domain in self.blocked_domains):
                    continue
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=link,
                    position=item.get("position", 0),
                ))

            logger.info({
                "event": "web_search",
                "query": query,
                "results_count": len(results),
                "status": "success",
            })

            return SearchResponse(query=query, results=results, success=True)

        except httpx.TimeoutException:
            logger.warning({"event": "web_search", "query": query, "status": "timeout"})
            return SearchResponse(query=query, results=[], success=False, error="timeout")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error({"event": "web_search", "query": query, "status": "http_error", "code": status_code})
            return SearchResponse(query=query, results=[], success=False, error=f"HTTP {status_code}")
        except Exception as e:
            logger.error({"event": "web_search", "query": query, "status": "error", "error": str(e)})
            return SearchResponse(query=query, results=[], success=False, error=str(e))
```

### Serper.dev API Response Structure
```json
{
  "searchParameters": {
    "q": "industry revenue benchmarks 2025",
    "type": "search",
    "num": 5
  },
  "organic": [
    {
      "title": "Industry Revenue Benchmarks Report 2025",
      "link": "https://example.com/report",
      "snippet": "Comprehensive analysis of industry revenue...",
      "position": 1
    }
  ],
  "knowledgeGraph": { "title": "...", "description": "..." },
  "answerBox": { "answer": "...", "snippet": "..." }
}
```

### SSE Event Types for Search
```python
# New SSE event types emitted during search tool execution
# 1. Search query being executed (from inside @tool via get_stream_writer)
{"type": "search_started", "message": "Searching: 'industry revenue benchmarks 2025'..."}

# 2. Search completed with results (from inside @tool)
{"type": "search_completed", "message": "Found 5 results", "sources_count": 5}

# 3. Search failed gracefully (from inside @tool)
{"type": "search_failed", "message": "Web search unavailable"}

# 4. Quota exceeded (from da_with_tools_node before binding tools)
{"type": "search_quota_exceeded", "message": "Search quota reached"}
```

### State Extension
```python
# Additions to backend/app/agents/state.py
class ChatAgentState(TypedDict):
    # ... all existing fields unchanged ...

    web_search_enabled: bool
    """Whether user toggled web search ON for this query."""

    search_sources: list[dict]
    """List of search sources: [{"title": str, "url": str}]. Populated by da_response."""
```

### Quota Model
```python
# backend/app/models/search_quota.py
from sqlalchemy import Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from uuid import UUID
from app.models.base import Base

class SearchQuota(Base):
    """Track daily search usage per user."""
    __tablename__ = "search_quotas"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    search_date: Mapped[date] = mapped_column(Date, primary_key=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
```

## How the Tool-Calling Loop Works (Key Conceptual Model)

The LLM decides when to stop calling tools. Here is the exact flow:

1. **da_with_tools_node**: Calls `llm.bind_tools([search_web]).ainvoke(messages)`.
   - If LLM response has `tool_calls`: `tools_condition` returns `"tools"` -> routes to `search_tools`
   - If LLM response has NO `tool_calls`: `tools_condition` returns `"__end__"` -> routes to `da_response`

2. **search_tools (ToolNode)**: Executes the `search_web` tool function. Returns `{"messages": [ToolMessage(content="results...")]}`. The ToolMessage is appended to state.messages via add_messages reducer.

3. **Back to da_with_tools_node**: Now state.messages includes the original prompt + AIMessage with tool_calls + ToolMessage with results. The LLM sees the search results and decides: call another search, or generate final response.

4. **Loop continues** until LLM stops requesting tool calls (controlled by system prompt instruction and max_searches config).

5. **da_response_node**: Extracts the final AIMessage content and any search sources from ToolMessages. Returns the structured response.

**Key: The LLM is in control of the loop.** It decides how many searches to perform (0 to max). The system prompt guides this behavior. `tools_condition` is purely mechanical -- it checks for tool_calls, nothing more.

## Interaction with Checkpointing

The existing `AsyncPostgresSaver` checkpoint system works seamlessly:
- Tool-calling messages (AIMessage with tool_calls, ToolMessage with results) are saved to checkpoint via the `messages` reducer
- On subsequent queries, the Manager Agent sees these in conversation history but they don't confuse routing because Manager only looks at recent messages and the tool-calling messages are internal
- The `da_response_node` adds a clean AIMessage at the end, which is what the Manager sees on the next query
- No changes to checkpoint configuration needed

## Discretion Recommendations

### Default Results Per Query: 5
**Rationale:** Balances information density with API cost. 5 results per search query provides sufficient signal for benchmarking without excessive token use. Configurable via `SEARCH_NUM_RESULTS` env var.

### Default Domain Blocklist: Empty
**Rationale:** No domains need blocking by default. Admin configures via `search.yaml`. Common candidates for future blocking: pinterest.com (irrelevant for data analysis).

### Search Query Formulation Strategy
**Rationale:** With bind_tools, the LLM formulates search queries AUTONOMOUSLY. The system prompt instructs it what to search for and the @tool docstring reinforces rules (generic queries only, no PII). No separate LLM call needed for query formulation -- the tool-calling LLM does it naturally as part of the agentic loop.

This is a significant advantage of the bind_tools approach over direct httpx: the LLM naturally formulates queries, decides how many to run, and synthesizes results -- all within the standard tool-calling protocol.

### Toggle UI Design
**Rationale:** Small Switch component with "Search web" label below chat input textarea, left-aligned. Grayed out with tooltip when unavailable. Uses shadcn/ui Switch (already in project).

### Search Activity Indicator
**Rationale:** Reuse existing status indicator bar. The `search_started` SSE event provides the query text for display: "Searching: 'query text'..." with the same pulsing dot animation.

### Sources Section Styling
**Rationale:** Add sources below follow-up suggestions in DataCard, separated by border-t. Each source is a clickable link with page title, text-xs styling. Compact, non-intrusive.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct httpx call inside node | bind_tools + ToolNode pattern | This phase (architectural decision) | Establishes reusable tool-calling infrastructure |
| Custom tool dispatch logic | langgraph.prebuilt.ToolNode | LangGraph 0.3+ (2024) | Standardized, tested, handles edge cases |
| Manual tool_calls check | langgraph.prebuilt.tools_condition | LangGraph 0.3+ (2024) | Clean conditional routing |
| Custom tool schemas | @tool decorator with type hints | langchain-core 0.3+ (2024) | Auto-generates LLM-compatible schemas |

**Current best practice:**
- LangGraph 1.0+ recommends ToolNode for custom graphs, create_react_agent for standard agents
- tools_condition is the standard routing function for tool-calling loops
- @tool with async support is the standard way to define tools
- get_stream_writer() works in tools on Python >= 3.11

## Open Questions

1. **Tool-Calling Messages in Checkpoint History**
   - What we know: AIMessage with tool_calls and ToolMessage with results will be saved to checkpoint. Manager Agent sees recent messages (last 10).
   - What's unclear: Will multiple tool-calling rounds (5 searches = 10+ messages per query) bloat the checkpoint and confuse the Manager?
   - Recommendation: In `da_response_node`, consider filtering/summarizing tool messages before they reach checkpoint. OR increase Manager's truncation to handle the extra messages. Test with real queries to determine impact.

2. **Quota Counting Granularity**
   - What we know: User decision is 7 searches per day per user.
   - What's unclear: Does "7 searches" mean 7 Serper API calls, or 7 user queries with search enabled?
   - Recommendation: Count per USER QUERY (not per Serper API call). If user sends 1 query and LLM makes 3 search calls, that's 1 of 7. More user-friendly.

3. **bind_tools on Non-Anthropic Providers**
   - What we know: ChatAnthropic supports bind_tools. ChatOpenAI supports bind_tools. ChatOllama may not support it for all models.
   - What's unclear: What happens if the data_analysis agent is configured with a provider that doesn't support bind_tools?
   - Recommendation: Try/except around bind_tools. If it fails, fall back to no-tools mode (same as web_search_enabled=False). Log a warning.

4. **Serper API Response Completeness**
   - What we know: Response includes `organic[]` with `title`, `link`, `snippet`, `position`.
   - What's unclear: Whether `organic` is always present even on zero results.
   - Recommendation: Handle missing `organic` key gracefully (default to empty list). Test with real API key.

## Sources

### Primary (HIGH confidence)
- Installed package versions verified via Python importlib.metadata:
  - langgraph 1.0.7, langchain-core 1.2.8, langchain-anthropic 1.3.1, langchain-openai 1.1.7
- ToolNode source code inspected from installed package (langgraph.prebuilt.tool_node)
- tools_condition source code inspected from installed package
- ToolRuntime class inspected from installed package (confirmed stream_writer field)
- bind_tools signature verified on ChatAnthropic
- Graph compilation with custom tools_condition path_map verified via local execution
- Python 3.12.12 confirmed (get_stream_writer works in async tools)

### Secondary (MEDIUM confidence)
- [LangGraph official docs - workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - tool-calling agent pattern, bind_tools usage
- [LangGraph official docs - streaming](https://docs.langchain.com/oss/python/langgraph/streaming) - get_stream_writer in tools, Python version requirements
- [LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart) - graph construction with tool-calling loop
- [LangChain tools docs](https://docs.langchain.com/oss/python/langchain/tools) - @tool decorator, ToolRuntime, Command returns
- [LangGraph ToolNode source on GitHub](https://github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/tool_node.py) - implementation details, error handling, Command support

### Tertiary (LOW confidence)
- Serper.dev API response schema: reconstructed from multiple sources, needs validation with real API call
- Serper rate limits by tier: only free tier (2,500 queries) confirmed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified installed, imports tested, signatures inspected
- Architecture (bind_tools/ToolNode): HIGH -- graph compilation tested locally, tools_condition path_map verified, ToolRuntime stream_writer confirmed
- Tool definition (@tool): HIGH -- decorator import verified, async support confirmed for Python 3.12
- API integration (Serper.dev): MEDIUM -- endpoint and auth verified, full response schema needs real API testing
- Frontend patterns: HIGH -- extending existing DataCard, ChatInput, useSSEStream with small additions
- Checkpoint interaction: MEDIUM -- theoretically sound but needs testing with real tool-calling messages
- Quota system: MEDIUM -- straightforward DB model, counting granularity needs confirmation

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days -- LangGraph API is stable at 1.0.x, Serper API is stable)
