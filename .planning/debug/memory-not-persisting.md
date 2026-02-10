---
status: diagnosed
trigger: "Memory not persisting across queries - Coding Agent called on every query"
created: 2026-02-07T00:00:00Z
updated: 2026-02-07T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - Initial state overrides checkpointed messages on every invocation
test: Examined agent_service.run_chat_query() state initialization
expecting: Found root cause - messages field initialized with fresh list on every call
next_action: Document root cause and return diagnosis

## Symptoms

expected: Follow-up queries should use conversation memory without re-calling Coding Agent
actual: Coding Agent is being called again on every query, unclear if memory is being used
errors: None reported
reproduction: Make initial query, then follow-up query - Coding Agent called both times
started: UAT Test 1 - Phase 8 implementation

## Eliminated

## Evidence

- timestamp: 2026-02-07T00:01:00Z
  checked: chat.py endpoint and agent_service.py
  found: Checkpointer is passed from request.app.state.checkpointer to agent_service.run_chat_query()
  implication: Checkpointer is being passed correctly through the call chain

- timestamp: 2026-02-07T00:02:00Z
  checked: agent_service.py lines 167-197
  found: |
    Graph invocation initializes fresh state on EVERY call:
    - initial_state dict created with HumanMessage(content=user_query)
    - No loading of previous state from checkpointer
    - Thread_id IS being passed in config
    - But initial_state always starts with fresh messages list
  implication: Every query starts with blank slate, previous messages not loaded

- timestamp: 2026-02-07T00:03:00Z
  checked: graph.py lines 445-514
  found: |
    - Graph compiled with checkpointer (line 487)
    - get_or_create_graph caches graph instance (singleton pattern)
    - BUT: Cached graph may be compiled WITHOUT checkpointer on first call
  implication: If graph created before checkpointer initialized, it won't have persistence

- timestamp: 2026-02-07T00:04:00Z
  checked: state.py lines 86-87
  found: |
    messages field defined with add_messages reducer:
    messages: Annotated[list[AnyMessage], add_messages]
  implication: Messages SHOULD accumulate automatically with reducer

- timestamp: 2026-02-07T00:05:00Z
  checked: agent_service.py lines 176-191
  found: |
    CRITICAL ISSUE FOUND:
    initial_state = {
      ...
      "messages": [HumanMessage(content=user_query)],  # <-- Line 191
      ...
    }

    result = await graph.ainvoke(initial_state, config)  # <-- Line 197

    The initial_state dict is passed on EVERY invocation with a fresh messages list.
    Even though add_messages reducer is defined, ainvoke() merges initial_state
    into checkpointed state, and explicit field values OVERRIDE reducer behavior.
  implication: ROOT CAUSE IDENTIFIED - Initial state overrides checkpointed messages

- timestamp: 2026-02-07T00:06:00Z
  checked: LangGraph behavior documentation
  found: |
    When using graph.ainvoke(state, config):
    - If checkpointer exists and thread_id matches existing checkpoint
    - Graph loads previous state from checkpoint
    - Then MERGES input state dict into loaded state
    - Fields explicitly set in input state REPLACE checkpointed values
    - Reducers only apply to updates within the graph execution, not to initial merge
  implication: Passing messages=[...] in initial_state defeats checkpointing

## Resolution

root_cause: |
  Memory is not persisting because agent_service.run_chat_query() passes a fresh
  messages list in initial_state on every invocation (line 191):

  initial_state = {
    "messages": [HumanMessage(content=user_query)],  # Overrides checkpoint
    ...
  }

  Even though ChatAgentState.messages uses add_messages reducer, the explicit
  messages field in initial_state passed to graph.ainvoke() OVERRIDES the
  checkpointed messages from previous queries.

  LangGraph behavior:
  1. Load checkpointed state (includes previous messages)
  2. Merge initial_state into loaded state
  3. Explicit fields in initial_state REPLACE checkpointed values
  4. Reducers only apply during graph execution, not to initial merge

  Result: Every query starts with only [HumanMessage(current_query)], losing
  all previous conversation history. This causes Coding Agent to be called
  on every query because the graph has no memory of previous responses.

  Same issue exists in run_chat_query_stream() at line 326:
  "messages": [HumanMessage(content=user_query)]
fix: |
  SUGGESTED FIX DIRECTION:

  Remove "messages" field from initial_state in both functions.
  Let the add_messages reducer handle message accumulation.

  BEFORE (agent_service.py lines 177-194):
  initial_state = {
    "file_id": str(file_id),
    ...
    "messages": [HumanMessage(content=user_query)],  # <-- REMOVE THIS
    ...
  }

  AFTER:
  initial_state = {
    "file_id": str(file_id),
    ...
    # messages field omitted - let reducer handle it
    ...
  }

  Then ADD the user message to state via graph update:

  Option 1: Use graph.update_state() before ainvoke:
  from langchain_core.messages import HumanMessage
  await graph.aupdate_state(
    config,
    {"messages": [HumanMessage(content=user_query)]}
  )
  result = await graph.ainvoke(initial_state, config)

  Option 2: Add messages in first node (coding_agent):
  Let coding_agent append user message to state.messages at start

  Apply same fix to run_chat_query_stream() at line 326.

verification:
files_changed: []
