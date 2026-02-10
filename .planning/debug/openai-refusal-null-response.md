---
status: diagnosed
trigger: "Investigate why switching an agent to OpenAI provider (gpt-5-nano-2025-08-07) returns `ai: {\"refusal\":null}` instead of actual content."
created: 2026-02-09T00:00:00Z
updated: 2026-02-09T00:12:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: OpenAI's ChatOpenAI returns empty string for `.content` when using gpt-5-nano, and the user is seeing serialized additional_kwargs instead of actual content
test: Verify if response.content is empty and check where additional_kwargs might be shown to user
expecting: Find that response.content is empty, causing fallback to show wrong data
next_action: Confirm hypothesis by analyzing code path

## Symptoms

expected: Onboarding agent returns actual content when using OpenAI provider
actual: Agent returns `ai: {"refusal":null}` instead of content
errors: None - connection successful, just wrong content
reproduction: Change onboarding agent in prompts.yaml to openai provider with gpt-5-nano-2025-08-07
started: When user switched from Anthropic to OpenAI provider

## Eliminated

## Evidence

- timestamp: 2026-02-09T00:01:00Z
  checked: onboarding.py lines 189-209
  found: Response processing at line 193 uses `response.content` directly - assumes LangChain normalizes all providers to have `.content` attribute
  implication: If OpenAI returns different structure, the `.content` access might be returning wrong data

- timestamp: 2026-02-09T00:02:00Z
  checked: onboarding.py lines 193-209
  found: Code tries to parse `response.content` as JSON (line 203), with fallback to raw `response.content` (line 209)
  implication: If `response.content` contains `{"refusal":null}` literally, JSON parsing would succeed but extract wrong data

- timestamp: 2026-02-09T00:03:00Z
  checked: llm_factory.py lines 153-155
  found: OpenAI instantiation is straightforward: `ChatOpenAI(model=model, api_key=api_key, **kwargs)`
  implication: No special response handling - relies on LangChain's ChatOpenAI wrapper to normalize responses

- timestamp: 2026-02-09T00:04:00Z
  checked: OpenAI API documentation and LangChain ChatOpenAI behavior
  found: OpenAI's Structured Outputs API adds a `refusal` field to responses. LangChain copies this to `additional_kwargs={'refusal': None}`. When there's no refusal, the field is null.
  implication: The `{"refusal":null}` is from additional_kwargs, not the actual content

- timestamp: 2026-02-09T00:05:00Z
  checked: LangChain AIMessage structure
  found: AIMessage has `.content` for actual response text and `.additional_kwargs` for provider-specific metadata (like refusal field)
  implication: The issue is that `response.content` is being serialized incorrectly, or the entire response object is being serialized instead of just `.content`

- timestamp: 2026-02-09T00:06:00Z
  checked: agent_service.py line 75, onboarding.py line 239-240
  found: `file_record.data_summary = result.data_summary` where result comes from `agent.run()` which returns OnboardingResult.data_summary from line 240
  implication: The data_summary field is set correctly by the return value from generate_summary

- timestamp: 2026-02-09T00:07:00Z
  checked: onboarding.py lines 189-209 (generate_summary response processing)
  found: Line 193 accesses `response.content` directly. Line 203 tries to parse it as JSON. Line 204 extracts summary from parsed JSON or falls back to raw `response.content` on line 209.
  implication: If `response.content` literally contains the string `{"refusal":null}`, the JSON parse would succeed, and line 204 would do `parsed.get("summary", response.content)` which would return `response.content` again since there's no "summary" key

- timestamp: 2026-02-09T00:08:00Z
  checked: User report format and LangChain behavior patterns
  found: User saw `ai: {"refusal":null}`. OpenAI's API includes refusal field which LangChain copies to additional_kwargs. The "ai:" prefix suggests this might be from a debug/logging output or error message.
  implication: Either response.content is empty and something else is being displayed, OR the model is literally returning the string '{"refusal":null}' as content

- timestamp: 2026-02-09T00:09:00Z
  checked: Code path in onboarding.py
  found: Line 193 strips markdown fences, line 203 parses JSON. If response.content is EMPTY STRING, line 193 would make content = "", line 203 json.loads("") would raise JSONDecodeError, triggering except block at line 208 which returns (response.content, None) = ("", None)
  implication: If response.content is empty, data_summary would be empty string, not `{"refusal":null}`

- timestamp: 2026-02-09T00:10:00Z
  checked: Web search for gpt-5-nano empty content issues
  found: Known issue with gpt-5-nano: "With the Responses API, GPT-5-nano/mini may emit only a reasoning item and no message item, so output_text is empty even when the call succeeds." Also: "High reasoning effort on nano can consume hundreds of tokens before producing a message, sometimes exhausting the budget."
  implication: gpt-5-nano returns empty response.content due to token exhaustion or reasoning-only output

- timestamp: 2026-02-09T00:11:00Z
  checked: How empty content causes the refusal display
  found: When response.content is empty, onboarding.py line 208 fallback returns (response.content, None) which is ("", None). This gets stored as data_summary = "". But the user saw `ai: {"refusal":null}`, which suggests they're seeing a debug representation of the AIMessage object or additional_kwargs, not the actual data_summary.
  implication: The issue might be in how the response is displayed to the user, OR the model is literally returning the string '{"refusal":null}' as content in some edge case

## Resolution

root_cause: gpt-5-nano-2025-08-07 model returns empty response.content due to known OpenAI API behavior where GPT-5-nano/mini models may emit only reasoning items and no message item, leaving output_text empty even when the API call succeeds. High reasoning effort on nano can consume hundreds of tokens before producing a message, sometimes exhausting the token budget entirely. The onboarding agent's generate_summary() method (lines 189-209 in backend/app/agents/onboarding.py) invokes the LLM at line 189, then directly accesses response.content at line 193 without validating it's non-empty. When content is empty, the JSON parsing at line 203 fails with JSONDecodeError, triggering the except block at line 208 which returns (response.content, None) = ("", None). This empty string gets stored as data_summary in the database via agent_service.py line 75.

The user report of `ai: {"refusal":null}` indicates they saw either: (1) a debug/logging representation of the AIMessage's additional_kwargs field (where LangChain stores OpenAI's refusal field), (2) an error message showing the AIMessage object structure, or (3) frontend behavior when data_summary is unexpectedly empty.

fix: Multiple approaches needed:
1. **Immediate**: Add validation in onboarding.py generate_summary() to check if response.content is empty and raise a descriptive error explaining gpt-5-nano token exhaustion
2. **Configuration**: Increase max_tokens for onboarding agent when using OpenAI models (current default is 3000, may need higher for reasoning models)
3. **Reasoning models**: If using gpt-5-nano (a reasoning model), consider setting reasoning_effort parameter to "low" or "minimal" to prevent token exhaustion
4. **Model recommendation**: Warn users that gpt-5-nano may not be suitable for complex JSON-output tasks like onboarding summary generation; recommend gpt-4o or gpt-5-mini instead
5. **Robust parsing**: Add fallback handling when content is empty - could retry with higher token limit or return a user-friendly error

verification:
files_changed:
  - backend/app/agents/onboarding.py: Add empty content validation and descriptive error
  - backend/app/config/prompts.yaml: Document max_tokens requirements for OpenAI reasoning models
  - (optional) backend/app/agents/llm_factory.py: Add reasoning_effort parameter support for OpenAI models

root_cause:
fix:
verification:
files_changed: []
