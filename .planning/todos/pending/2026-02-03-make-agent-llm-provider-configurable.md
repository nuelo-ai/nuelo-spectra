---
created: 2026-02-03T09:29
title: Make agent LLM provider configurable (model-agnostic)
area: agents
files:
  - backend/app/agents/onboarding.py
  - backend/app/agents/coding.py
  - backend/app/agents/data_analysis.py
  - backend/app/agents/graph.py
  - backend/app/config.py
  - .planning/phases/03-ai-agents---orchestration/03-01-PLAN.md
---

## Problem

Current Phase 3 architecture hardcodes Anthropic (Claude) as the LLM provider for all 4 agents:
- Onboarding Agent uses `ChatAnthropic` directly
- Coding Agent uses `ChatAnthropic` directly
- Code Checker logical validation uses `ChatAnthropic` directly
- Data Analysis Agent uses `ChatAnthropic` directly

This creates vendor lock-in and prevents:
- Using OpenAI GPT models (gpt-4, gpt-4-turbo)
- Using Google Gemini models
- Using other LangChain-compatible providers (Cohere, Mistral, local models via Ollama)
- A/B testing different models for cost/quality optimization
- Per-agent model selection (e.g., cheaper model for Code Checker, premium model for Coding Agent)

The application should be designed with a model-agnostic mechanism from the start to avoid costly refactoring later.

## Solution

Refactor Phase 3 plans to use abstraction pattern:

1. **Config-driven provider selection:**
   - Add to `backend/app/config.py` Settings:
     - `llm_provider: str = "anthropic"` (choices: anthropic, openai, google, etc.)
     - `agent_model: str` (already exists - make it provider-aware)
     - Optional: `onboarding_model`, `coding_model`, `checker_model`, `analysis_model` for per-agent override

2. **LLM factory pattern:**
   - Create `backend/app/agents/llm_factory.py`:
     ```python
     def get_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
         if provider == "anthropic":
             from langchain_anthropic import ChatAnthropic
             return ChatAnthropic(model=model, **kwargs)
         elif provider == "openai":
             from langchain_openai import ChatOpenAI
             return ChatOpenAI(model=model, **kwargs)
         elif provider == "google":
             from langchain_google_genai import ChatGoogleGenerativeAI
             return ChatGoogleGenerativeAI(model=model, **kwargs)
         else:
             raise ValueError(f"Unsupported provider: {provider}")
     ```

3. **Update all agent nodes to use factory:**
   - Replace `ChatAnthropic(...)` with `get_llm(settings.llm_provider, settings.agent_model, ...)`
   - Update Plan 03-01 (dependency installation) to include optional providers:
     - `langchain-openai` (optional)
     - `langchain-google-genai` (optional)
   - Update Plan 03-02, 03-04 (agent implementation) to use factory pattern

4. **Environment variable support:**
   - `LLM_PROVIDER=anthropic|openai|google`
   - `OPENAI_API_KEY` (if provider=openai)
   - `GOOGLE_API_KEY` (if provider=google)
   - `ANTHROPIC_API_KEY` (if provider=anthropic)

5. **Documentation:**
   - Update user_setup in plans to document multiple provider options
   - Add provider selection guide to README or docs

**Alternative (lighter-weight for v1):**
- Keep Anthropic as default
- Design agent functions to accept `llm: BaseChatModel` parameter instead of creating internally
- This makes them testable and swappable without full factory pattern
- Factory can be added later when multi-provider becomes a requirement

**When to implement:**
- Before executing Phase 3 plans (update plans now)
- OR: Accept as technical debt, ship v1 with Anthropic only, refactor in v2 when multi-provider demand is validated
