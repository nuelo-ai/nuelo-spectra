---
status: diagnosed
phase: 08-session-memory-with-postgresql-checkpointing
source: [08-01-SUMMARY.md, 08-02-SUMMARY.md]
started: 2026-02-07T21:00:00Z
updated: 2026-02-07T22:00:00Z
round: 2
---

## Current Test

[testing complete]

## Tests

### 1. Multi-turn conversation with context persistence
expected: After asking a data question, follow-up queries work without re-explaining context (e.g., "add a column" after initial analysis)
result: issue
reported: "I can see that the memory was not invoked. LangChain shows that for my second query the AI agent invoked the LLM again instead of pulling the information from memory"
severity: major

### 2. Context persists after browser refresh
expected: After refreshing the browser while keeping the chat tab open, conversation context remains and follow-up questions still work
result: skipped
reason: can't be tested

### 3. Tab close warning appears
expected: When attempting to close a chat tab with active conversation (>2 messages), browser shows "Leave site?" warning dialog
result: issue
reported: "no warning shown"
severity: major

### 4. Context usage display shows token count
expected: Chat interface header shows current context usage as "X / 12,000 tokens" next to the file name
result: pass
note: "Display working - shows 26/12000. User raised concern about token counting accuracy (whether both input and output tokens are counted)"

### 5. Warning at 85% context usage
expected: When context reaches 85% of 12,000 tokens (10,200+ tokens), the token display turns orange as a warning
result: skipped
reason: impractical to test with 12,000 token limit - would need to lower default for testing

### 6. Trim confirmation dialog appears at limit
expected: When context exceeds 12,000 tokens, a dialog appears offering "Trim older messages" or "Keep all messages" options
result: skipped
reason: impractical to test with 12,000 token limit

### 7. Trimming reduces context to 90%
expected: After confirming "Trim older messages", context reduces to ~10,800 tokens (90% of 12,000), keeping most recent conversation
result: skipped
reason: depends on test 6

### 8. Independent chat state per file tab
expected: Opening multiple files in different tabs maintains separate conversation contexts - follow-ups in one tab don't affect other tabs
result: skipped
reason: memory not working properly

## Summary

total: 8
passed: 1
issues: 2
pending: 0
skipped: 5

## Gaps

- truth: "Follow-up queries should use conversation memory to understand context without needing user to re-explain"
  status: fixed
  reason: "User reported: I can see that the memory was not invoked. LangChain shows that for my second query the AI agent invoked the LLM again instead of pulling the information from memory"
  severity: major
  test: 1
  root_cause: "Previous fix (e4fa3ce) was flawed - passing messages in initial_state overrides checkpoint even after manual concatenation. LangGraph reducers only work for updates WITHIN graph execution, not for initial_state merge. Solution: Use aupdate_state() to append messages (uses reducer), then remove messages from initial_state before ainvoke() so checkpoint takes precedence."
  artifacts:
    - path: "backend/app/services/agent_service.py"
      issue: "Lines 177-181 and 318-322 - incorrect use of initial_state to pass messages"
      fix: "Use graph.aupdate_state(config, messages) to append via reducer, then pop messages from initial_state before ainvoke"
  missing: []
  debug_session: ".planning/debug/resolved/memory-not-persisting-round-2.md"
  fix_commit: "f5b3975"
  note: "LLM WILL be invoked on every query (correct behavior). Memory means LLM receives previous conversation in context, not that LLM calls are skipped."

- truth: "Browser shows 'Leave site?' warning dialog when closing chat tab with active conversation (>2 messages)"
  status: fixed
  reason: "User reported: no warning shown"
  severity: major
  test: 3
  root_cause: "event.returnValue was set to boolean true (in e4fa3ce fix), but W3C spec requires NON-EMPTY STRING. Modern browsers trigger dialog via preventDefault() OR non-empty string returnValue. Previous fix used boolean instead of string."
  artifacts:
    - path: "frontend/src/hooks/useTabCloseWarning.ts"
      issue: "Line 22 - event.returnValue = true as any (boolean, not string)"
      fix: "Changed to event.returnValue = 'true' (non-empty string)"
  missing: []
  debug_session: ".planning/debug/resolved/tab-close-warning-round-2.md"
  fix_commit: "3f8f2fb"
  note: "Requires user interaction (typing/clicking) before warning appears (browser security feature)"

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
