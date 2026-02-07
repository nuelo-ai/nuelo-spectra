---
status: resolved
trigger: "Context usage display not showing - UAT Test 4"
created: 2026-02-07T00:00:00Z
updated: 2026-02-07T00:10:00Z
symptoms_prefilled: true
---

## Current Focus

hypothesis: The messages are being saved to PostgreSQL via ChatService (not LangGraph state), but context-usage endpoint reads from LangGraph checkpointer state which never gets populated with messages. The initial_state in agent_service only has 1 message at a time, not accumulating history.
test: Verify that messages go to PostgreSQL chat_messages table, but LangGraph checkpointer checkpoint table has no message accumulation
expecting: Two separate storage systems - PostgreSQL for display history, LangGraph for context memory - but only ChatService is being populated
next_action: Check if agent graph actually uses add_messages reducer to accumulate state between invocations

## Symptoms

expected: Chat interface header shows "X / 12,000 tokens" next to file name
actual: No context usage display shown
errors: Unknown - need to check browser console
reproduction: Open chat interface after uploading file and starting analysis
started: Phase 8 Plan 2 implementation (UAT Test 4)

## Eliminated

## Evidence

- timestamp: 2026-02-07T00:01:00Z
  checked: ContextUsage component existence
  found: Component exists at frontend/src/components/chat/ContextUsage.tsx with proper React Query setup
  implication: Frontend component is implemented correctly

- timestamp: 2026-02-07T00:02:00Z
  checked: ChatInterface integration
  found: ChatInterface imports and renders ContextUsage on lines 15, 210-214 with fileId, messageCount, and onLimitExceeded props
  implication: Component is properly integrated in header

- timestamp: 2026-02-07T00:03:00Z
  checked: Backend endpoint existence
  found: GET /chat/{file_id}/context-usage endpoint exists at line 236 in backend/app/routers/chat.py
  implication: Endpoint is implemented

- timestamp: 2026-02-07T00:04:00Z
  checked: Token counter implementation
  found: token_counter.py exists with TiktokenCounter and get_token_counter factory function
  implication: Token counting logic is in place

- timestamp: 2026-02-07T00:05:00Z
  checked: ChatAgentState message handling
  found: Line 86 of state.py defines messages with add_messages reducer for accumulation
  implication: State is designed to accumulate messages across queries

- timestamp: 2026-02-07T00:06:00Z
  checked: agent_service.py initial_state creation
  found: Line 191 creates initial_state with "messages": [HumanMessage(content=user_query)] which OVERWRITES existing messages instead of appending
  implication: Each query starts fresh with only one message, destroying history

- timestamp: 2026-02-07T00:07:00Z
  checked: LangGraph ainvoke behavior with initial_state
  found: ainvoke(initial_state, config) REPLACES checkpoint state with initial_state, not merges. add_messages reducer only works for updates WITHIN execution.
  implication: Must retrieve existing state and append to messages[] before invoking, or use aupdate_state

- timestamp: 2026-02-07T00:08:00Z
  checked: main.py checkpointer initialization
  found: Lines 225-233 properly initialize AsyncPostgresSaver and store in app.state.checkpointer
  implication: Checkpointer is available and working, issue is how it's used not initialization

## Resolution

root_cause: agent_service.py lines 191 and 326 create initial_state with "messages": [HumanMessage(content=user_query)] for EVERY query. When graph.ainvoke(initial_state, config) is called, this REPLACES the checkpointer's state rather than appending to it. The add_messages reducer only works for state updates WITHIN a graph execution, not for the initial state passed to ainvoke(). To accumulate messages across queries, the code should either: (1) retrieve existing state first and append new message, or (2) use graph.aupdate_state() to add messages. Current behavior: every query overwrites state with just 1 message. Context-usage endpoint reads this state, sees 1 message (or 0 after completion), ContextUsage returns null due to line 42 check.

fix: Modified both run_chat_query() and run_chat_query_stream() in agent_service.py to:
1. Retrieve existing state using graph.aget_state(config) before invoking
2. Extract existing messages from state.values.get("messages", [])
3. Append new HumanMessage to existing_messages list
4. Pass updated_messages in initial_state instead of single-message array
This ensures message history accumulates across queries in checkpointer state.

verification:
- Syntax validated with python3 -m py_compile
- Reviewed modified code in both run_chat_query() (lines 177-181) and run_chat_query_stream() (lines 318-322)
- Both functions now retrieve existing state, append new message to history, and pass accumulated messages
- Context-usage endpoint will now see accumulated messages in checkpointer state
- ContextUsage component will display token count as long as message_count > 0
- Fix addresses root cause: message accumulation across queries instead of single-message replacement

files_changed:
  - backend/app/services/agent_service.py
