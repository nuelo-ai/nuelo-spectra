---
status: diagnosed
phase: 13-migrate-web-search-from-serper-dev-to-tavily
source: 13-01-SUMMARY.md
started: 2026-02-09T23:10:00Z
updated: 2026-02-09T23:18:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Web Search Returns Tavily Answer
expected: Enable web search toggle, ask a benchmarking/external-data question. The AI response includes substantive analysis grounded in web search content (Tavily synthesized answer), not just URL links. Search activity indicator appears during search.
result: pass

### 2. Source Citations Display Correctly
expected: After a web search query, the DataCard Sources section shows clickable source links with page titles. Links open in new tabs. Format should be clean title + URL pairs.
result: pass

### 3. Search Config Endpoint Reports Tavily Status
expected: With TAVILY_API_KEY configured in .env, the search toggle in the UI is available and functional. Without the key, search should be disabled/unavailable.
result: pass

### 4. Search Works End-to-End Without Errors
expected: Complete a web search query without any errors in the chat. The response should stream normally, showing search activity, then the AI analysis with sources. No error messages or fallback behavior.
result: issue
reported: "Overall is good. However, when the result was generated from Memory (MEMORY_SUFFICIENT), the Query Suggestions did not show"
severity: major

### 5. Non-Search Queries Unaffected
expected: With search toggle OFF (or for a non-benchmarking question), queries work exactly as before -- code generation, data analysis, memory recall all function normally without any search-related behavior.
result: pass

## Summary

total: 5
passed: 4
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Query follow-up suggestions display after MEMORY_SUFFICIENT route responses"
  status: failed
  reason: "User reported: Overall is good. However, when the result was generated from Memory (MEMORY_SUFFICIENT), the Query Suggestions did not show"
  severity: major
  test: 4
  root_cause: "4 compounding defects: (1) _build_memory_prompt() returns plain text, not JSON with follow_up_suggestions; (2) ChatInterface memory streaming branch ignores follow_up_suggestions; (3) ChatMessage hasStructuredData guard excludes MEMORY_SUFFICIENT from DataCard; (4) non-streaming path omits follow_up_suggestions from metadata_json"
  artifacts:
    - path: "backend/app/agents/data_analysis.py"
      issue: "_build_memory_prompt() (lines 298-339) does not instruct JSON output with follow_up_suggestions"
    - path: "frontend/src/components/chat/ChatInterface.tsx"
      issue: "Memory route streaming branch (lines 369-394) uses ChatMessage without suggestion chips"
    - path: "frontend/src/components/chat/ChatMessage.tsx"
      issue: "hasStructuredData guard (lines 38-44) requires generated_code/execution_result, excludes memory responses"
    - path: "backend/app/services/agent_service.py"
      issue: "Non-streaming run_chat_query() (lines 241-248) omits follow_up_suggestions from metadata_json"
  missing:
    - "Update _build_memory_prompt() to require JSON output with analysis + follow_up_suggestions keys"
    - "Extract follow_up_suggestions in ChatInterface memory streaming branch and render chips"
    - "Add follow-up chip rendering path for non-DataCard assistant messages"
    - "Add follow_up_suggestions to non-streaming metadata_json"
  debug_session: ".planning/debug/memory-suggestions-missing.md"
