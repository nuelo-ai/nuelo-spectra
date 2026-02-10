---
status: diagnosed
phase: 07-multi-llm-provider-infrastructure
source: [07-01-SUMMARY.md, 07-02-SUMMARY.md, 07-03-SUMMARY.md, 07-04-SUMMARY.md]
started: 2026-02-09T12:00:00Z
updated: 2026-02-09T12:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Default Provider Behavior Unchanged
expected: Start the backend with only ANTHROPIC_API_KEY set. System boots, all agents use Anthropic/Claude Sonnet 4.0 by default. Uploading a file and chatting works exactly as before.
result: pass

### 2. Per-Agent LLM Configuration via YAML
expected: Edit backend/app/config/prompts.yaml to change one agent's provider/model (e.g., set data_analysis to openai/gpt-4o). Restart backend. That agent uses the new provider while others remain on Anthropic.
result: issue
reported: "Changed Onboarding Agent to openai/gpt-5-nano-2025-08-07, received ai: {\"refusal\":null} — no actual content returned"
severity: major

### 3. Fail-Fast on Invalid Provider Config
expected: Set ANTHROPIC_API_KEY to an invalid value (e.g., "invalid-key-xxx"). Start the backend. It should refuse to start with a clear error message identifying which provider failed and what went wrong.
result: pass

### 4. LLM Health Endpoint
expected: With the backend running, call GET /health/llm. Response returns JSON showing status of each configured provider (healthy/unhealthy) with provider name, model, and latency.
result: pass

### 5. Provider Registry Configuration
expected: Open backend/app/config/llm_providers.yaml. File lists 5 providers (anthropic, openai, google, ollama, openrouter) with anthropic marked as default. Each has type, display_name, and metadata.
result: pass

### 6. Test Suite Passes
expected: Run `uv run pytest backend/tests/test_llm_providers.py -v` from project root. All 34 tests pass with no failures. Tests run without any live API keys (fully mocked).
result: pass

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Per-agent LLM config switch works correctly — alternative provider returns proper content"
  status: failed
  reason: "User reported: Changed Onboarding Agent to openai/gpt-5-nano-2025-08-07, received ai: {\"refusal\":null} — no actual content returned"
  severity: major
  test: 2
  root_cause: "gpt-5-nano reasoning models exhaust token budget on reasoning before producing content, leaving response.content empty. onboarding.py generate_summary() (line 193) doesn't validate empty content — silently stores empty string. LangChain stores OpenAI's refusal field in additional_kwargs, which surfaces as {refusal:null}."
  artifacts:
    - path: "backend/app/agents/onboarding.py"
      issue: "generate_summary() lines 189-209 — no validation for empty response.content"
    - path: "backend/app/agents/llm_factory.py"
      issue: "OpenAI instantiation lacks reasoning model config (reasoning_effort param)"
  missing:
    - "Add empty content validation after LLM invocation in all agents"
    - "Set reasoning_effort=minimal for OpenAI reasoning models (nano/mini) in llm_factory"
    - "Return user-friendly error instead of silently storing empty string"
  debug_session: ".planning/debug/openai-refusal-null-response.md"
