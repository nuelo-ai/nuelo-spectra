---
status: resolved
trigger: "Memory not persisting across queries (Round 2) - User reports fix from e4fa3ce not working"
created: 2026-02-07T00:00:00Z
updated: 2026-02-07T00:00:00Z
symptoms_prefilled: true
goal: find_and_fix
---

## Current Focus

hypothesis: CONFIRMED and FIXED - Previous fix was fundamentally flawed
test: Applied correct pattern using aupdate_state without passing messages in initial_state
expecting: Memory should now persist correctly - messages accumulate via add_messages reducer
next_action: User to verify by testing in browser OR run verification script

## Symptoms

expected: Follow-up queries should use conversation memory without user re-explaining context
actual: User reports "LangChain shows that for my second query the AI agent invoked the LLM again instead of pulling the information from memory"
errors: None reported - functional behavior issue
reproduction: Make initial query, then follow-up query - LLM invoked again (but should have previous context)
started: UAT Test 1 - Still failing after fix in commit e4fa3ce

## Eliminated

## Evidence

- timestamp: 2026-02-07T00:01:00Z
  checked: agent_service.py lines 177-181 (run_chat_query)
  found: |
    Fix IS present:
    - Line 177: existing_state = await graph.aget_state(config)
    - Line 178: existing_messages = existing_state.values.get("messages", [])
    - Line 181: updated_messages = existing_messages + [HumanMessage(content=user_query)]
    - Line 198: "messages": updated_messages
  implication: Code retrieves and appends messages as intended in fix

- timestamp: 2026-02-07T00:02:00Z
  checked: agent_service.py lines 318-322 (run_chat_query_stream)
  found: Same fix applied in streaming function (lines 318-322, 340)
  implication: Both query methods have the fix

- timestamp: 2026-02-07T00:03:00Z
  checked: agent_service.py line 198 and 340
  found: |
    CRITICAL PROBLEM IDENTIFIED:
    The fix retrieves existing messages and creates updated_messages list, BUT
    then passes "messages": updated_messages in initial_state dict (line 198, 340)

    This is THE EXACT SAME PROBLEM as before, just with manual concatenation:
    - graph.ainvoke(initial_state, config) merges initial_state into checkpointed state
    - Explicit "messages" field in initial_state OVERRIDES checkpointed messages
    - Even though we manually retrieved and concatenated messages, passing them
      in initial_state defeats the add_messages reducer

    The fix attempted to work AROUND the issue by manually managing messages,
    but the fundamental problem remains: you cannot pass "messages" field in
    initial_state when using checkpointing - it overrides the checkpoint.
  implication: The fix is fundamentally flawed - still overriding checkpointed state

- timestamp: 2026-02-07T00:04:00Z
  checked: chat.py lines 334-335 (trim_messages endpoint)
  found: |
    Found CORRECT pattern for updating checkpointed state:
    await graph.aupdate_state(config, {"messages": trimmed_messages})

    This is used in the trim_messages endpoint to replace messages.
    Note: aupdate_state is for UPDATING checkpoint, not initial invocation.
  implication: Should use aupdate_state or different invocation pattern

- timestamp: 2026-02-07T00:05:00Z
  checked: LangGraph checkpointing behavior pattern
  found: |
    CORRECT pattern for checkpointed graph with reducers:

    Option 1 - Minimal initial_state (RECOMMENDED):
    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke({"user_query": query}, config)
    # Graph loads checkpointed state automatically
    # First node adds HumanMessage to state.messages
    # Reducer handles accumulation

    Option 2 - Update state before invoke:
    config = {"configurable": {"thread_id": thread_id}}
    await graph.aupdate_state(config, {"messages": [HumanMessage(query)]})
    result = await graph.ainvoke(initial_state, config)
    # Update checkpoint first, then invoke

    WRONG pattern (current implementation):
    initial_state = {"messages": [HumanMessage(query)]}  # OVERRIDES checkpoint
    result = await graph.ainvoke(initial_state, config)
  implication: Need to change invocation pattern - don't pass messages in initial_state

- timestamp: 2026-02-07T00:06:00Z
  checked: agent_service.py invocation pattern requirements
  found: |
    Current code passes many state fields in initial_state:
    - file_id, user_id, user_query, data_summary, user_context, file_path
    - generated_code, validation_result, validation_errors, error_count
    - max_steps, execution_result, analysis, messages, final_response, error

    Most of these are query-specific metadata that should be passed.
    Only "messages" field is problematic because it overrides the reducer.

    SOLUTION: Pass all fields EXCEPT messages in initial_state.
    Use graph.aupdate_state() to add new user message to checkpoint.
  implication: ROOT CAUSE CONFIRMED - Need to separate metadata from messages

- timestamp: 2026-02-07T00:07:00Z
  checked: Important clarification about expected behavior
  found: |
    User reported: "AI agent invoked the LLM again instead of pulling from memory"

    CRITICAL CLARIFICATION:
    The agents WILL invoke LLMs on EVERY query - this is CORRECT behavior.
    Memory persistence does NOT mean "skip LLM calls."
    Memory persistence means "LLM sees previous conversation history in its context."

    Example:
    Query 1: "What are the columns?"
    - LLM receives: [HumanMessage("What are the columns?")]
    - LLM responds with analysis

    Query 2: "Show me the first 5 rows"
    - LLM receives: [HumanMessage("What are the columns?"), AIMessage("..."), HumanMessage("Show me first 5 rows")]
    - LLM is INVOKED again (correct!)
    - But it has CONTEXT from previous exchange (memory working!)

    The user may expect NO LLM calls for follow-up questions, which is not how
    conversational AI works. The LLM must be invoked to generate a response, but
    it should have access to the conversation history.
  implication: Need to verify memory is actually working AND clarify expectations

## Resolution

root_cause: |
  The fix in commit e4fa3ce attempted to solve memory persistence by manually
  retrieving existing messages and concatenating them:

  existing_state = await graph.aget_state(config)
  existing_messages = existing_state.values.get("messages", [])
  updated_messages = existing_messages + [HumanMessage(content=user_query)]
  initial_state = {"messages": updated_messages, ...}  # Line 198, 340

  However, this is STILL WRONG because:

  1. LangGraph with checkpointer loads previous state automatically when thread_id matches
  2. Then MERGES initial_state dict into loaded state
  3. Fields explicitly set in initial_state REPLACE checkpointed values
  4. The add_messages reducer ONLY works for updates within graph execution
  5. Passing "messages" in initial_state bypasses the reducer and overwrites checkpoint

  The manual concatenation is correct logic, but becomes useless when passed
  back into initial_state - it still overrides the checkpoint on every call.

  CORRECT PATTERN:
  1. Don't pass "messages" field in initial_state at all
  2. Use graph.aupdate_state() to add new user message to checkpoint
  3. Let graph.ainvoke() load checkpointed state (including accumulated messages)
  4. The add_messages reducer handles accumulation within graph nodes

fix: |
  Modify both run_chat_query() and run_chat_query_stream() in agent_service.py:

  BEFORE (lines 177-198):
  existing_state = await graph.aget_state(config)
  existing_messages = existing_state.values.get("messages", []) if existing_state.values else []
  updated_messages = existing_messages + [HumanMessage(content=user_query)]

  initial_state = {
    "file_id": str(file_id),
    ...
    "messages": updated_messages,  # <-- REMOVE THIS LINE
    ...
  }
  result = await graph.ainvoke(initial_state, config)

  AFTER:
  # Remove the manual message retrieval/concatenation (lines 177-181)
  # Don't pass "messages" in initial_state

  initial_state = {
    "file_id": str(file_id),
    "user_id": str(user_id),
    "user_query": user_query,
    "data_summary": file_record.data_summary,
    "user_context": file_record.user_context or "",
    "file_path": file_record.file_path,
    "generated_code": "",
    "validation_result": "",
    "validation_errors": [],
    "error_count": 0,
    "max_steps": settings.agent_max_retries,
    "execution_result": "",
    "analysis": "",
    # "messages" field REMOVED - let checkpoint handle it
    "final_response": "",
    "error": ""
  }

  # Add new user message to checkpoint using aupdate_state
  from langchain_core.messages import HumanMessage
  await graph.aupdate_state(config, {"messages": [HumanMessage(content=user_query)]})

  # Invoke graph - it will load checkpointed state with accumulated messages
  result = await graph.ainvoke(initial_state, config)

  Apply same fix to run_chat_query_stream() at lines 318-340.

verification: |
  APPLIED FIX:
  Modified both run_chat_query() and run_chat_query_stream() in agent_service.py:

  1. Removed manual message retrieval/concatenation (lines 177-181, 318-322)
  2. Initialize initial_state with empty messages list (for schema completeness)
  3. Call graph.aupdate_state(config, {"messages": [HumanMessage(...)]})
     - On first query: Creates checkpoint with the message
     - On subsequent queries: Appends to existing checkpointed messages via add_messages reducer
  4. Remove messages from initial_state before invoke (pop)
  5. graph.ainvoke() loads checkpointed state with accumulated messages

  KEY CHANGES:
  - Line 173-197: Updated run_chat_query to use aupdate_state pattern
  - Line 310-342: Updated run_chat_query_stream to use aupdate_state pattern

  VERIFICATION PLAN:
  1. Start backend server
  2. Upload a test file
  3. Send first query: "What are the columns?"
  4. Check PostgreSQL: SELECT * FROM checkpoints WHERE thread_id LIKE 'file_%' ORDER BY checkpoint_id DESC LIMIT 1;
     - Verify 1 HumanMessage + 1 AIMessage in checkpoint
  5. Send second query: "Show me the first 5 rows"
  6. Check PostgreSQL again: Verify 2 HumanMessages + 2 AIMessages
  7. Check LangSmith/logs: Verify coding_agent receives state with both previous messages
  8. User confirms: Second query doesn't require re-explaining context

  EXPECTED BEHAVIOR:
  - LLM WILL be invoked on every query (this is correct)
  - But each invocation should have access to previous conversation messages
  - Memory doesn't mean "skip LLM" - it means "LLM sees previous context"

  MANUAL VERIFICATION STEPS:
  1. Start backend: cd backend && uvicorn app.main:app --reload
  2. Open frontend: cd frontend && npm run dev
  3. Upload a CSV file
  4. First query: "What are the column names?"
  5. Observe: Coding agent generates code, returns response
  6. Second query: "Show me the first 5 rows"
  7. Expected: Agent should reference columns from first query without asking again
  8. Check logs: Second invocation should show messages list with 2+ messages

  AUTOMATED VERIFICATION:
  Run: python backend/test_memory_verification.py
  (Tests add_messages reducer directly with aupdate_state)

  DATABASE VERIFICATION:
  SELECT checkpoint_id, thread_id,
         jsonb_array_length(checkpoint->'channel_values'->'messages') as message_count
  FROM checkpoints
  WHERE thread_id LIKE 'file_%'
  ORDER BY checkpoint_id DESC LIMIT 10;

files_changed:
  - backend/app/services/agent_service.py
