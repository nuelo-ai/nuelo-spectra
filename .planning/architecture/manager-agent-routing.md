# Solution Architecture: Manager Agent with Intelligent Routing

**Status:** Proposed - Awaiting approval
**Date:** 2026-02-07
**Context:** Replace fixed agent pipeline with intelligent routing to avoid unnecessary code generation

---

## Problem Statement

### Current Architecture (Phase 8)

```
User Query
    ↓
Coding Agent (ALWAYS called)
    ↓
Code Checker (ALWAYS called)
    ↓
Code Execution (ALWAYS called)
    ↓
Data Analysis Agent (ALWAYS called)
    ↓
Response to User
```

**Issues:**
1. **Wasteful execution:** Simple questions like "What was the result?" trigger full code generation pipeline
2. **Slow responses:** Even context-only queries take 10-20 seconds (full pipeline)
3. **High cost:** 4 LLM calls per query regardless of complexity
4. **Memory underutilized:** Conversation history exists but agents always regenerate code
5. **Poor UX:** Users expect instant answers for simple follow-ups

### Example Scenarios (Current Behavior)

| User Query | Current Behavior | Ideal Behavior |
|------------|------------------|----------------|
| "Show me sales by region" | Coding → Checker → Execute → Analyst ✓ | Same ✓ |
| "What were the columns again?" | Coding → Checker → Execute → Analyst ✗ | Analyst reads from memory |
| "Can you explain that result?" | Coding → Checker → Execute → Analyst ✗ | Analyst uses previous result |
| "Add a trend column" | Coding → Checker → Execute → Analyst ✓ | Same ✓ (needs new code) |

---

## Proposed Architecture

### High-Level Flow

```
User Query
    ↓
Manager Agent (NEW - routing decision)
    ↓
    ├─ Route A: MEMORY_SUFFICIENT
    │      ↓
    │  Data Analysis Agent (answers from conversation history)
    │      ↓
    │  Response to User
    │
    ├─ Route B: CODE_MODIFICATION
    │      ↓
    │  Coding Agent (modifies existing code)
    │      ↓
    │  Code Checker
    │      ↓
    │  Code Execution
    │      ↓
    │  Data Analysis Agent
    │      ↓
    │  Response to User
    │
    └─ Route C: NEW_ANALYSIS
           ↓
       Coding Agent (fresh code)
           ↓
       Code Checker
           ↓
       Code Execution
           ↓
       Data Analysis Agent
           ↓
       Response to User
```

---

## Manager Agent Specification

### Role
**Decision-maker** that analyzes user queries and conversation context to determine optimal routing.

### Inputs
1. **Current user query** (string)
2. **Conversation history** (list of previous messages from checkpointer)
3. **File metadata** (data_summary, column names, user_context)
4. **Previous execution results** (if any exist in conversation)

### Outputs
```python
@dataclass
class RoutingDecision:
    route: Literal["MEMORY_SUFFICIENT", "CODE_MODIFICATION", "NEW_ANALYSIS"]
    reasoning: str  # Why this route was chosen
    context_summary: str  # Relevant info from conversation history
```

### Decision Logic

#### Route: MEMORY_SUFFICIENT
**When to use:** Query can be answered entirely from existing conversation context.

**Criteria:**
- Query is asking for clarification ("What did you mean?", "Can you explain?")
- Query references previous results ("What was the trend?", "Show me that again")
- Query asks about data structure already discussed ("What are the columns?")
- No new data transformation or code generation needed

**Examples:**
- "What were the column names again?"
- "Can you explain the previous result?"
- "What was the average we calculated?"
- "Show me the result again"

**Action:** Route directly to Data Analysis Agent with conversation history

---

#### Route: CODE_MODIFICATION
**When to use:** Query requires small changes to existing code.

**Criteria:**
- Previous code exists in conversation history
- Query asks to modify/extend previous analysis ("add a column", "filter by X", "sort by Y")
- Base logic remains the same, only parameters/transformations change
- User references "previous" or "last" result

**Examples:**
- "Add a trend column to that"
- "Now filter by region = 'North'"
- "Sort by date descending"
- "Show top 10 instead of 5"

**Action:**
1. Pass previous code + query to Coding Agent with instruction to modify
2. Run through full validation pipeline (Checker → Execute → Analyst)

---

#### Route: NEW_ANALYSIS
**When to use:** Query requires completely new analysis or first query in conversation.

**Criteria:**
- No previous code exists (first query in chat)
- Query requests entirely different analysis from previous
- User explicitly says "new analysis" or "start over"
- Query involves different data columns or aggregations

**Examples:**
- First query: "Show me sales by region"
- "Now analyze customer retention instead" (after sales analysis)
- "Calculate correlation between price and quantity"
- "Start fresh - show me monthly trends"

**Action:** Run full pipeline from scratch (Coding → Checker → Execute → Analyst)

---

## Implementation Details

### LangGraph State Schema

```python
from typing import Literal, Annotated
from langchain_core.messages import AnyMessage, add_messages

class ChatAgentState(TypedDict):
    # Existing fields
    file_id: str
    user_id: str
    user_query: str
    data_summary: str
    user_context: str
    file_path: str

    # NEW: Routing decision
    routing_decision: RoutingDecision

    # Existing execution fields
    generated_code: str
    validation_result: str
    execution_result: str
    analysis: str

    # Memory
    messages: Annotated[list[AnyMessage], add_messages]

    # Error tracking
    error: str
    error_count: int
    max_steps: int
```

### LangGraph Flow Structure

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(ChatAgentState)

# Nodes
workflow.add_node("manager", manager_node)  # NEW
workflow.add_node("coding_agent", coding_node)
workflow.add_node("code_checker", checker_node)
workflow.add_node("execute_code", execution_node)
workflow.add_node("data_analyst", analyst_node)

# Entry point
workflow.set_entry_point("manager")

# Conditional routing from manager
workflow.add_conditional_edges(
    "manager",
    route_based_on_decision,  # Function that reads routing_decision
    {
        "MEMORY_SUFFICIENT": "data_analyst",
        "CODE_MODIFICATION": "coding_agent",
        "NEW_ANALYSIS": "coding_agent"
    }
)

# Existing pipeline edges
workflow.add_edge("coding_agent", "code_checker")
workflow.add_edge("code_checker", "execute_code")
workflow.add_edge("execute_code", "data_analyst")
workflow.add_edge("data_analyst", END)
```

### Manager Agent Implementation

```python
async def manager_node(state: ChatAgentState) -> dict:
    """
    Manager agent analyzes query and conversation to determine routing.
    """
    # Extract context
    user_query = state["user_query"]
    messages = state["messages"]
    data_summary = state["data_summary"]

    # Check if previous code exists
    previous_code = extract_last_code_from_messages(messages)
    previous_result = extract_last_result_from_messages(messages)

    # Build manager prompt
    manager_prompt = f"""
You are a Query Router for a data analysis system. Analyze the user's query and conversation history to determine the optimal route.

**Current Query:** {user_query}

**Conversation Summary:**
- Messages in history: {len(messages)}
- Previous code exists: {previous_code is not None}
- Previous result exists: {previous_result is not None}

**Data Context:**
{data_summary}

**Routing Options:**

1. **MEMORY_SUFFICIENT** - Query can be answered from conversation history alone
   - No new code generation needed
   - User asking for clarification, explanation, or recalling previous results
   - Examples: "What were the columns?", "Explain that result", "Show me again"

2. **CODE_MODIFICATION** - Query requires modifying existing code
   - Previous code exists and user wants to extend/modify it
   - Base logic stays same, only parameters change
   - Examples: "Add a column", "Filter by X", "Sort differently"

3. **NEW_ANALYSIS** - Query requires completely new analysis
   - First query in conversation OR completely different analysis
   - No previous code to build upon
   - Examples: First query, "Analyze X instead", "Start fresh"

**Previous Code (if exists):**
```python
{previous_code or "None"}
```

**Previous Result (if exists):**
{previous_result or "None"}

**Instructions:**
Analyze the query and return your routing decision in JSON format:
{{
  "route": "MEMORY_SUFFICIENT" | "CODE_MODIFICATION" | "NEW_ANALYSIS",
  "reasoning": "Brief explanation of why this route",
  "context_summary": "Relevant info from conversation that will help downstream agents"
}}
"""

    # Invoke manager LLM
    llm = get_llm("manager", temperature=0.0)  # Use separate manager config
    response = await llm.ainvoke(manager_prompt)

    # Parse JSON response
    decision = json.loads(response.content)

    return {
        "routing_decision": RoutingDecision(**decision)
    }
```

### Routing Function

```python
def route_based_on_decision(state: ChatAgentState) -> str:
    """
    Simple routing function that reads the manager's decision.
    """
    decision = state["routing_decision"]
    return decision.route
```

---

## Agent Modifications

### 1. Data Analysis Agent (Memory Route)

**When called via MEMORY_SUFFICIENT route:**

```python
async def analyst_node_memory_mode(state: ChatAgentState) -> dict:
    """
    Data Analysis Agent in MEMORY mode - answers from conversation history.
    """
    user_query = state["user_query"]
    messages = state["messages"]
    context_summary = state["routing_decision"].context_summary

    analyst_prompt = f"""
You are a Data Analyst answering a user's question using ONLY the conversation history.

**User's Question:** {user_query}

**Relevant Context from Conversation:**
{context_summary}

**Full Conversation History:**
{format_messages_for_prompt(messages)}

**Instructions:**
- Answer the user's question using information from the conversation history
- If the answer is in previous results, reference it
- If asking about data structure, use the data summary
- DO NOT suggest generating new code
- Be concise and direct

Provide your answer:
"""

    llm = get_llm("data_analyst", temperature=0.0)
    response = await llm.ainvoke(analyst_prompt)

    return {
        "analysis": response.content,
        "generated_code": "",  # No code generated
        "execution_result": ""  # No execution
    }
```

### 2. Coding Agent (Modification Mode)

**When called via CODE_MODIFICATION route:**

```python
async def coding_node_modification_mode(state: ChatAgentState) -> dict:
    """
    Coding Agent in MODIFICATION mode - extends existing code.
    """
    user_query = state["user_query"]
    messages = state["messages"]
    previous_code = extract_last_code_from_messages(messages)
    context_summary = state["routing_decision"].context_summary

    coding_prompt = f"""
You are a Python Coding Agent modifying existing data analysis code.

**User's Request:** {user_query}

**Context:** {context_summary}

**Existing Code:**
```python
{previous_code}
```

**Instructions:**
- MODIFY the existing code to fulfill the user's new request
- Keep the base logic intact, only change what's needed
- Maintain the same output format (DataFrame)
- Add comments explaining changes

Generate the MODIFIED code:
"""

    llm = get_llm("coding_agent", temperature=0.0)
    response = await llm.ainvoke(coding_prompt)

    # Extract code from response
    code = extract_code_from_response(response.content)

    return {
        "generated_code": code
    }
```

---

## Performance Impact

### Expected Improvements

| Metric | Current (Phase 8) | With Manager Agent | Improvement |
|--------|-------------------|-------------------|-------------|
| **Response time (memory queries)** | ~15 seconds | ~2 seconds | **87% faster** |
| **LLM calls per query (memory)** | 4 agents | 2 agents (Manager + Analyst) | **50% reduction** |
| **LLM calls per query (modification)** | 4 agents | 5 agents (Manager + pipeline) | +25% (acceptable) |
| **LLM calls per query (new)** | 4 agents | 5 agents | +25% (acceptable) |
| **Cost per 100 queries** | $X | ~$0.6X (assuming 40% memory queries) | **40% reduction** |
| **User satisfaction** | Medium | High (instant responses) | **Significant** |

### Query Distribution (Estimated)

Based on typical data analysis conversations:
- **40% MEMORY_SUFFICIENT** - Clarifications, explanations, recalls
- **30% CODE_MODIFICATION** - Incremental changes, filters, sorts
- **30% NEW_ANALYSIS** - Fresh analyses, different data views

**Net Impact:** ~35-40% reduction in execution time and cost.

---

## Configuration

### Agent YAML Config

```yaml
# backend/app/agents/prompts/manager_agent.yaml
agent_name: "Manager Agent"
role: "Query Router"
provider: "anthropic"  # or from config
model: "claude-sonnet-4-5"  # Fast routing decisions
temperature: 0.0  # Deterministic routing

system_prompt: |
  You are a Query Router for a data analysis AI system.

  Your job is to analyze user queries and conversation history to determine
  the most efficient route for handling the query:

  - MEMORY_SUFFICIENT: Answer from conversation history (fastest)
  - CODE_MODIFICATION: Modify existing code (medium)
  - NEW_ANALYSIS: Generate new code from scratch (slowest)

  Always choose the most efficient route that will correctly answer the user's query.
  When in doubt between MEMORY and CODE, prefer MEMORY (faster, cheaper).
```

---

## Migration Path

### Phase 1: Implement Manager Agent (New Phase in Roadmap)
- Add manager_agent.yaml prompt
- Implement manager_node in graph.py
- Add routing_decision to state schema
- Update graph to use conditional routing
- Add route_based_on_decision function

### Phase 2: Update Existing Agents
- Modify Data Analysis Agent to handle MEMORY_SUFFICIENT mode
- Modify Coding Agent to handle CODE_MODIFICATION mode
- Keep NEW_ANALYSIS mode as current behavior

### Phase 3: Testing & Optimization
- Unit tests for routing logic
- Integration tests for all 3 routes
- Performance benchmarking
- User acceptance testing (UAT)

### Phase 4: Monitoring
- Log routing decisions for analysis
- Track route distribution (memory vs code vs new)
- Monitor response times per route
- Adjust routing logic based on data

---

## Trade-offs & Considerations

### Pros
✅ **Dramatic performance improvement** for memory queries (87% faster)
✅ **Cost reduction** (~40% fewer LLM calls overall)
✅ **Better UX** (instant answers for simple questions)
✅ **Smarter system** (context-aware routing)
✅ **Scalability** (can add more routes in future)

### Cons
⚠️ **Additional complexity** (1 more agent, conditional routing)
⚠️ **One extra LLM call** per query (+manager overhead)
⚠️ **Routing mistakes** possible (manager chooses wrong route)
⚠️ **More testing needed** (3 routes to validate)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Manager chooses wrong route | User gets wrong answer or slow response | Extensive prompt engineering, fallback logic, monitoring |
| Memory route misses context | Incomplete answer | Include context_summary, allow analyst to request code generation |
| Code modification breaks logic | Execution errors | Code Checker validates all code regardless of route |
| Increased latency from manager call | Slower overall | Use fast model (Sonnet) for manager, cache decisions |

---

## Success Metrics

### Phase Success Criteria

1. **Performance:**
   - Memory queries respond in <3 seconds (vs 15 seconds current)
   - Code modification queries <20 seconds
   - New analysis queries <25 seconds (similar to current)

2. **Accuracy:**
   - Manager routing accuracy >90% (validated through UAT)
   - Memory route answers user questions correctly >95%
   - Code modification success rate >85%

3. **Cost:**
   - Overall LLM token usage reduced by >30%
   - Average LLM calls per query: <3.5 (vs 4.0 current)

4. **User Satisfaction:**
   - Users report faster responses for follow-up questions
   - Fewer complaints about "slow" system
   - Higher engagement (more multi-turn conversations)

---

## Open Questions for Review

1. **Manager Model Choice:** Should Manager use Sonnet (fast, cheap) or Opus (more accurate)?
2. **Fallback Strategy:** If Manager fails or is uncertain, default to NEW_ANALYSIS or ask user?
3. **Route Override:** Should we allow users to force a specific route? ("Generate new code" command)
4. **Context Window:** How much conversation history should Manager analyze? (last 5 messages? all?)
5. **Hybrid Routes:** Should we support combinations? (e.g., "answer from memory AND generate supplemental code")

---

## Next Steps (Pending Approval)

1. ✅ **Review this architecture** - User approval required
2. ⏸️ **Create new phase in ROADMAP.md** - After approval
3. ⏸️ **Add to MILESTONES.md** - Decide if v0.2 or v0.3
4. ⏸️ **Create detailed PLAN.md** - Break into executable tasks
5. ⏸️ **Implement & test** - Execute phase plans

---

**Status:** Awaiting user review and approval before proceeding.
