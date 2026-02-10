---
created: 2026-02-10T14:57:22.044Z
title: Use Pydantic structured output for agent JSON responses
area: api
files:
  - backend/app/agents/data_analysis.py:290 (_parse_analysis_json fallback)
  - backend/app/agents/data_analysis.py:298-339 (_build_memory_prompt)
  - backend/app/agents/onboarding_agent.py (summary + query_suggestions JSON)
  - backend/app/agents/manager_agent.py (already uses with_structured_output - reference pattern)
---

## Problem

Different LLM providers inconsistently return JSON when instructed via prompts. Some wrap responses in markdown fences, others add preamble text before/after the JSON. This causes `_parse_analysis_json()` to fall through to the `JSONDecodeError` fallback, silently dropping `follow_up_suggestions` and potentially corrupting `analysis` text. The issue manifests as frontend rendering problems (missing suggestions, malformed DataCard content) that vary by provider.

Currently affected agents:
- **Data Analysis Agent**: `_parse_analysis_json()` relies on `json.loads()` with silent fallback to `(raw_text, [])`
- **Onboarding Agent**: Returns JSON with `summary` + `query_suggestions` via prompt instruction
- **Memory prompt** (`_build_memory_prompt()`): Recently fixed in Phase 13 Plan 2, but still prompt-based

The Manager Agent already uses `with_structured_output(RoutingDecision)` successfully (Phase 9), proving the pattern works cross-provider.

## Solution

Replace prompt-based JSON instruction with Pydantic models and `with_structured_output()` for all agent response schemas:

1. Define Pydantic response models (e.g., `AnalysisResponse`, `OnboardingResponse`, `MemoryResponse`) with typed fields
2. Use `llm.with_structured_output(ResponseModel)` instead of raw `llm.invoke()` + `json.loads()`
3. Add fallback path for providers that don't support structured output (graceful degradation to current prompt-based approach with `try/except`)
4. Consider provider-specific mechanisms: native JSON mode (OpenAI/Anthropic), tool-calling (others), and Ollama model limitations
5. Remove `_parse_analysis_json()` fallback once structured output is in place

Reference implementation: `backend/app/agents/manager_agent.py` using `with_structured_output(RoutingDecision)`
