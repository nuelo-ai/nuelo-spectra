---
status: diagnosed
trigger: "Query follow-up suggestions do not display when Manager Agent routes via MEMORY_SUFFICIENT path"
created: 2026-02-09T00:00:00Z
updated: 2026-02-09T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED - Three independent defects across backend and frontend prevent follow-up suggestions from appearing on MEMORY_SUFFICIENT responses
test: Full end-to-end code path trace completed
expecting: N/A - root cause confirmed
next_action: Report diagnosis

## Symptoms

expected: After a MEMORY_SUFFICIENT response, follow-up suggestion chips should appear below the response
actual: Follow-up suggestions do not display for MEMORY_SUFFICIENT routed queries
errors: None reported (silent omission)
reproduction: Send a query that triggers MEMORY_SUFFICIENT route, observe no follow-up chips
started: Since Phase 10 added suggestions on top of Phase 9 routing

## Eliminated

- hypothesis: SSE streaming layer filters out follow_up_suggestions for MEMORY_SUFFICIENT
  evidence: agent_service.py line 404 includes "follow_up_suggestions" in the node_complete event whitelist for ALL nodes. The streaming layer is route-agnostic -- it passes through whatever the node returns. No filtering based on route.
  timestamp: 2026-02-09

- hypothesis: The graph wiring skips da_response_node for MEMORY_SUFFICIENT
  evidence: graph.py line 523-530 shows da_with_tools routes to da_response via tools_condition "__end__" path. MEMORY_SUFFICIENT goes manager -> da_with_tools -> (tools_condition evaluates to __end__ since no tools called) -> da_response. The da_response node IS reached for MEMORY_SUFFICIENT. Confirmed by ChatInterface.tsx line 370-371 which looks for node_complete with node="da_response" -- this event IS expected.
  timestamp: 2026-02-09

- hypothesis: metadata_json persistence layer drops follow_up_suggestions for MEMORY_SUFFICIENT
  evidence: agent_service.py line 444 unconditionally includes follow_up_suggestions in metadata_json for ALL routes. No route-based filtering in persistence.
  timestamp: 2026-02-09

## Evidence

- timestamp: 2026-02-09
  checked: backend/app/agents/data_analysis.py _build_memory_prompt() (lines 298-339)
  found: The MEMORY_SUFFICIENT prompt does NOT ask the LLM to return JSON with "analysis" and "follow_up_suggestions" keys. It asks for plain markdown text ("Be concise and direct", "Format for readability with markdown"). Compare with _build_analysis_prompt() which uses the YAML system_prompt that explicitly instructs JSON with both keys.
  implication: DEFECT 1 (BACKEND) - The LLM returns plain text, not JSON. When this plain text hits _parse_analysis_json() (line 210), json.loads() fails at line 290, the JSONDecodeError except clause at line 294 returns (raw, []) -- the empty list means NO follow_up_suggestions are ever produced for MEMORY_SUFFICIENT.

- timestamp: 2026-02-09
  checked: backend/app/agents/data_analysis.py da_with_tools_node() (lines 134-137)
  found: For MEMORY_SUFFICIENT, the HumanMessage sent to the LLM is "Please analyze these results." (line 136), same as the code analysis path. This is semantically wrong (there are no "results" to analyze) but not the root cause -- the prompt itself is the issue.
  implication: Minor inconsistency but not the primary defect.

- timestamp: 2026-02-09
  checked: frontend/src/components/chat/ChatInterface.tsx MEMORY_SUFFICIENT streaming branch (lines 359-396)
  found: The MEMORY_SUFFICIENT streaming branch (lines 369-394) renders a plain ChatMessage component, NOT a DataCard. The ChatMessage component does NOT render follow-up suggestion chips -- only DataCard does (DataCard.tsx lines 175-191). Even if the backend DID return follow_up_suggestions, the streaming UI would not display them because it uses ChatMessage instead of DataCard.
  implication: DEFECT 2 (FRONTEND/STREAMING) - During streaming, follow-up suggestions have no rendering path for MEMORY_SUFFICIENT responses. The code at lines 370-376 extracts analysisText from the da_response node_complete event but never extracts or passes follow_up_suggestions to anything.

- timestamp: 2026-02-09
  checked: frontend/src/components/chat/ChatMessage.tsx hasStructuredData check (lines 38-44)
  found: The hasStructuredData check requires metadata_json to contain generated_code OR execution_result. MEMORY_SUFFICIENT responses have NEITHER (no code generation, no execution). So hasStructuredData=false, and the message renders as a plain text bubble (lines 172-231) with no DataCard and no follow-up suggestions.
  implication: DEFECT 3 (FRONTEND/PERSISTED) - After stream completes and messages are refetched from the database, the persisted MEMORY_SUFFICIENT message also fails to show follow-ups. Even though follow_up_suggestions would be in metadata_json (IF the backend produced them), the guard at line 38-44 prevents DataCard from rendering. The plain ChatMessage template has no follow-up chip UI.

- timestamp: 2026-02-09
  checked: backend/app/services/agent_service.py run_chat_query() non-streaming path (lines 241-248)
  found: The non-streaming path does NOT include follow_up_suggestions in metadata_json at all (compare line 241-248 vs streaming path lines 439-452). The streaming path includes it at line 444, but the non-streaming path omits it entirely.
  implication: DEFECT 4 (BACKEND/NON-STREAMING) - If the non-streaming endpoint is used, follow_up_suggestions are never persisted to the database regardless of route. This affects all routes, not just MEMORY_SUFFICIENT.

## Resolution

root_cause: |
  Three compounding defects prevent follow-up suggestions from appearing on MEMORY_SUFFICIENT responses:

  **DEFECT 1 (Primary, Backend): _build_memory_prompt() does not request JSON output with follow_up_suggestions**
  File: backend/app/agents/data_analysis.py, lines 298-339
  The memory prompt asks for plain markdown text. When the LLM's plain-text response hits _parse_analysis_json() (line 210 -> line 268), json.loads() fails (line 290), and the except clause at line 294 returns an empty list for follow_ups. Result: follow_up_suggestions is always [] for MEMORY_SUFFICIENT.

  **DEFECT 2 (Frontend/Streaming): MEMORY_SUFFICIENT streaming branch renders ChatMessage, not DataCard**
  File: frontend/src/components/chat/ChatInterface.tsx, lines 369-394
  The isMemoryRoute branch creates a plain ChatMessage with no follow-up chip UI. Even if suggestions existed in the da_response node_complete event, they are never extracted or rendered. The code at line 370-376 only extracts analysisText, ignoring follow_up_suggestions entirely.

  **DEFECT 3 (Frontend/Persisted): hasStructuredData guard excludes MEMORY_SUFFICIENT messages from DataCard**
  File: frontend/src/components/chat/ChatMessage.tsx, lines 38-44
  The guard checks for generated_code OR execution_result in metadata_json. MEMORY_SUFFICIENT has neither, so it falls through to plain text rendering with no suggestion chips.

  **DEFECT 4 (Backend/Non-streaming, bonus): run_chat_query() omits follow_up_suggestions from metadata_json**
  File: backend/app/services/agent_service.py, lines 241-248
  The non-streaming path never persists follow_up_suggestions. Compare with streaming path at line 444 which does include it.

fix:
verification:
files_changed: []
