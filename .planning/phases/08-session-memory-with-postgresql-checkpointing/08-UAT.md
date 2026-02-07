---
status: diagnosed
phase: 08-session-memory-with-postgresql-checkpointing
source: [08-01-SUMMARY.md, 08-02-SUMMARY.md]
started: 2026-02-07T21:00:00Z
updated: 2026-02-07T21:20:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Multi-turn conversation with context persistence
expected: After asking a data question, follow-up queries work without re-explaining context (e.g., "add a column" after initial analysis)
result: issue
reported: "I can't tell if the answer came from memory because the agent coder was called again. This needs to be further investigated and might need some changes on how the AI agents were called."
severity: major

### 2. Context persists after browser refresh
expected: After refreshing the browser while keeping the chat tab open, conversation context remains and follow-up questions still work
result: skipped
reason: not sure if memory was stored

### 3. Tab close warning appears
expected: When attempting to close a chat tab with active conversation (>2 messages), browser shows "Leave site?" warning dialog
result: issue
reported: "fail - no warning was shown"
severity: major

### 4. Context usage display shows token count
expected: Chat interface header shows current context usage as "X / 12,000 tokens" next to the file name
result: issue
reported: "fail - no context was shown"
severity: major

### 5. Warning at 85% context usage
expected: When context reaches 85% of 12,000 tokens (10,200+ tokens), the token display turns orange as a warning
result: skipped
reason: can't test without display

### 6. Trim confirmation dialog appears at limit
expected: When context exceeds 12,000 tokens, a dialog appears offering "Trim older messages" or "Keep all messages" options
result: skipped
reason: can't test limit without display

### 7. Trimming reduces context to 90%
expected: After confirming "Trim older messages", context reduces to ~10,800 tokens (90% of 12,000), keeping most recent conversation
result: skipped
reason: can't test trimming without display

### 8. Independent chat state per file tab
expected: Opening multiple files in different tabs maintains separate conversation contexts - follow-ups in one tab don't affect other tabs
result: skipped
reason: memory not working properly

## Summary

total: 8
passed: 0
issues: 3
pending: 0
skipped: 5

## Gaps

- truth: "Follow-up queries should use conversation memory without re-calling Coding Agent for context that already exists"
  status: fixed
  reason: "User reported: I can't tell if the answer came from memory because the agent coder was called again. This needs to be further investigated and might need some changes on how the AI agents were called."
  severity: major
  test: 1
  root_cause: "Initial state with messages: [HumanMessage(...)] overrides checkpointed state. LangGraph reducers only apply during graph execution, not when merging initial state passed to ainvoke(). Every query starts with single message, losing conversation history."
  artifacts:
    - path: "backend/app/services/agent_service.py"
      issue: "Lines 177-181 and 318-322 - retrieve existing state, append new message, pass accumulated messages"
      fix: "Retrieve existing state using graph.aget_state(config), append new HumanMessage to existing messages, pass updated_messages in initial_state"
  missing: []
  debug_session: ".planning/debug/memory-not-persisting.md"
  fix_commit: "e4fa3ce"

- truth: "Browser shows 'Leave site?' warning dialog when closing chat tab with active conversation (>2 messages)"
  status: fixed
  reason: "User reported: fail - no warning was shown"
  severity: major
  test: 3
  root_cause: "event.returnValue set to empty string ('') which is falsy. Modern browsers require truthy returnValue to trigger beforeunload confirmation dialog."
  artifacts:
    - path: "frontend/src/hooks/useTabCloseWarning.ts"
      issue: "Line 19 - event.returnValue = '' (falsy value)"
      fix: "Changed to event.returnValue = true as any"
  missing: []
  debug_session: ".planning/debug/resolved/tab-close-warning-not-showing.md"
  fix_commit: "e4fa3ce"

- truth: "Chat interface header displays current context usage as 'X / 12,000 tokens' next to file name"
  status: fixed
  reason: "User reported: fail - no context was shown"
  severity: major
  test: 4
  root_cause: "Same as Gap 1 - messages being replaced instead of accumulated causes context-usage endpoint to read empty state from checkpointer, returning message_count = 0 which causes ContextUsage component to return null."
  artifacts:
    - path: "backend/app/services/agent_service.py"
      issue: "Lines 177-181 and 318-322 - initial_state replaces checkpointed messages"
      fix: "Retrieve existing state, append new message, pass accumulated messages"
  missing: []
  debug_session: ".planning/debug/resolved/context-usage-display-not-showing.md"
  fix_commit: "e4fa3ce"
