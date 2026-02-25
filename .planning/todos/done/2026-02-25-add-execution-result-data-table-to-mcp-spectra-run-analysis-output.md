---
created: 2026-02-25T19:51:19.933Z
title: Add execution result data table to MCP spectra_run_analysis output
area: api
files:
  - backend/app/mcp_server.py
---

## Problem

The `spectra_run_analysis` MCP tool omits `execution_result` from its output, even though the backend returns it. The data table (the actual computed rows) is critical for AI agents consuming MCP — without it, the agent only gets the narrative analysis but not the underlying data to reason over or verify.

Comparison:
- REST API response includes `execution_result` (JSON array of result rows)
- MCP tool output includes Analysis, Generated Code, Chart Spec — but NOT the data table

## Solution

In `spectra_run_analysis` in `backend/app/mcp_server.py`, add a content block for `execution_result`:

1. **Format**: Render as a markdown table (not raw JSON) — most readable for AI agents
2. **Placement**: Insert BEFORE the Analysis block (data first, then interpretation)
3. **Truncation**: Cap at 50 rows with a note if truncated (e.g. "Showing 50 of 120 rows")
4. **Also consider**: Adding `follow_up_suggestions` as a final block (low priority)

Output order after fix:
1. Data Table (execution_result → markdown table, max 50 rows)
2. Analysis narrative
3. Generated Code
4. Chart Specification
5. Credits used

The `execution_result` field is a JSON string — parse it with `json.loads()` before rendering.
Handle the case where result is not a list (e.g. scalar or dict output from agent).
