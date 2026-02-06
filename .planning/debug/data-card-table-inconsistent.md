---
status: diagnosed
trigger: "Investigate why Data Card table rendering is inconsistent."
created: 2026-02-05T00:00:00Z
updated: 2026-02-05T00:35:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: DataCard has conditional rendering logic that switches between interactive TanStack table and static markdown based on data properties
test: examining DataCard component code and ChatMessage execution_result parsing
expecting: find conditional check that determines rendering mode
next_action: read DataCard and ChatMessage components

## Symptoms

expected: Data Card always displays interactive sortable/filterable table with download capability
actual: Sometimes shows interactive table with scrollable view and download button, sometimes shows simple static markdown table
errors: None reported
reproduction: Execute queries that should return data tables
started: Discovered during UAT Test 10

## Eliminated

## Evidence

- timestamp: 2026-02-05T00:05:00Z
  checked: DataCard.tsx parseTableData function (lines 52-73)
  found: Function only parses tableData prop, but never actually uses it - returns null always because line 75 has bug: `tableData || parseTableData(tableData)` which just returns tableData as-is if truthy
  implication: parseTableData is never actually called with execution_result

- timestamp: 2026-02-05T00:06:00Z
  checked: ChatMessage.tsx parseExecutionResult function (lines 45-91) and DataCard rendering (lines 94-109)
  found: ChatMessage correctly parses execution_result from metadata_json and passes as tableData prop to DataCard. Parser handles both array format and {columns, rows} format
  implication: Parsing logic exists in ChatMessage and works correctly

- timestamp: 2026-02-05T00:07:00Z
  checked: Backend graph.py execute_in_sandbox node (lines 331-360)
  found: execution_result is always a JSON string - either json.dumps(parsed["result"]) or raw stdout text or str(result.results)
  implication: execution_result from backend is always a string, needs parsing on frontend

- timestamp: 2026-02-05T00:08:00Z
  checked: Backend prompts.yaml coding agent instructions (lines 18-43)
  found: Coding agent instructed to output print(json.dumps({"result": result})) - but result can be anything (int, float, dict, list, DataFrame converted to dict/list)
  implication: Result format varies - sometimes it's a scalar, sometimes it's tabular data with columns/rows

- timestamp: 2026-02-05T00:10:00Z
  checked: ChatMessage.tsx parseExecutionResult logic flow
  found: Parser expects either array of objects [{col1: val1}, {col2: val2}] OR {columns: [...], rows: [...]} structure. If execution_result is just a scalar (number/string), parser returns null and no table renders
  implication: Interactive table only shows when execution_result contains array or columns/rows structure - scalars render as markdown in explanation instead

- timestamp: 2026-02-05T00:12:00Z
  checked: Backend coding agent prompt (prompts.yaml lines 18-43)
  found: Prompt says "End with: print(json.dumps({'result': result}))" and "Convert results to Python types: int(), float(), str()". Also says "If result is a DataFrame/Series, is it converted to dict/list before json.dumps?"
  implication: Backend can return either scalars wrapped in {"result": value} or structured data wrapped in {"result": [{}, {}]} or {"result": {"columns": [], "rows": []}}

- timestamp: 2026-02-05T00:15:00Z
  checked: 06-05-SUMMARY.md design decision (line 51-52)
  found: "Parse execution_result as JSON for table data" - design expects backend to return JSON strings with table data that frontend parses
  implication: By design, only queries that return tabular data should show interactive tables; scalar queries should show just the explanation

- timestamp: 2026-02-05T00:17:00Z
  checked: UAT Test 10 issue description again
  found: Issue says "Sometimes shows interactive table with scrollable view and download button, sometimes shows simple static markdown table"
  implication: Key word is "sometimes shows simple static markdown table" - this might mean the explanation text contains markdown tables, OR it might mean no table at all

- timestamp: 2026-02-05T00:20:00Z
  checked: DataCard.tsx line 75 logic bug
  found: `displayTableData = tableData || parseTableData(tableData)` - if tableData is truthy, returns it; if falsy, tries to parse null which returns null. The parseTableData function in DataCard is never effectively used because ChatMessage already parses execution_result
  implication: DataCard's parseTableData is dead code, but this doesn't cause the inconsistency - ChatMessage's parsing should work

- timestamp: 2026-02-05T00:22:00Z
  checked: Data analysis agent prompt line 94
  found: "Format for readability with markdown" - analysis agent can include markdown tables in explanation text
  implication: When execution_result contains tabular data, the analysis agent might format it as markdown table in explanation, creating "simple static markdown table" in explanation section

- timestamp: 2026-02-05T00:25:00Z
  hypothesis: Inconsistency occurs when execution_result contains tabular data but ChatMessage parseExecutionResult fails to parse it correctly, resulting in NO interactive table but analysis agent includes markdown table in explanation
  test: Check what format execution_result has when it contains tabular data - does backend always unwrap {"result": data} or does it sometimes send the full wrapper?
  expecting: Backend inconsistently formats execution_result - sometimes as unwrapped array string '[{...}]', sometimes keeping wrapper '{"result": [...]}'

- timestamp: 2026-02-05T00:30:00Z
  hypothesis_refined: ChatMessage parseExecutionResult expects {columns: [], rows: []} or array of objects, but if LLM generates code using df.to_dict('split') it returns {columns: [], data: []} with "data" key instead of "rows" key
  test: Check ChatMessage parseExecutionResult line 65 - does it handle "data" key?
  found: Line 65 says "rows: parsed.rows || parsed.data || []" - it DOES handle "data" key as fallback!
  implication: This is not the issue

- timestamp: 2026-02-05T00:33:00Z
  checked: ChatMessage line 53-60 array handling
  found: Checks "if (Array.isArray(parsed))" then "if (parsed.length > 0 && typeof parsed[0] === 'object')" - so it requires non-empty array with object as first element
  implication: If LLM generates code that returns empty array [], or array of scalars [1, 2, 3], parseExecutionResult returns null

## Resolution

root_cause: ChatMessage parseExecutionResult only recognizes two table formats - (1) arrays of objects with length > 0 and first element typeof 'object', (2) objects with 'columns' array property - but fails when LLM generates code using df.to_dict() default format which returns {column: {index: value}} structure without 'columns' key, or when result is empty array, causing inconsistent rendering where some tabular queries show no interactive table (only markdown table in explanation)

artifacts:
  - frontend/src/components/chat/ChatMessage.tsx:45-91 (parseExecutionResult function) - missing df.to_dict() default format handler
  - frontend/src/components/chat/ChatMessage.tsx:53-60 - requires non-empty array with object first element, rejects empty arrays
  - frontend/src/components/chat/DataCard.tsx:52-75 (parseTableData function) - dead code never called due to line 75 logic bug

missing:
  - Add handler for df.to_dict() default format {col: {idx: val}} → convert to array of objects
  - Add handler for empty arrays [] → show empty table instead of null
  - Fix DataCard line 75 to remove redundant parseTableData call
  - Consider updating backend coding prompt to specify df.to_dict('records') explicitly
