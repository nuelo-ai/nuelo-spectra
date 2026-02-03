---
created: 2026-02-03T10:45
title: Add OpenRouter and Ollama LLM provider support
area: api
files:
  - backend/app/agents/llm_factory.py
  - backend/app/config.py
  - .planning/phases/03-ai-agents---orchestration/03-01-PLAN.md
---

## Problem

Phase 3 currently supports 3 LLM providers (Anthropic, OpenAI, Google) via the LLM factory pattern in `backend/app/agents/llm_factory.py`. User needs two additional providers:

1. **OpenRouter API** - Unified API gateway providing access to multiple LLM models (Claude, GPT, Llama, Mixtral, etc.) through a single endpoint
   - Benefit: Single API key for multiple models, competitive pricing, model diversity
   - Use case: Flexibility to switch between different models without managing multiple API keys

2. **Local LLM via Ollama** - Run models locally without API costs
   - Benefit: Privacy, no API costs, offline capability, full control
   - Use case: Development, testing, cost-sensitive workloads, data privacy requirements

Current Phase 3 plans (03-01 through 03-05) hardcode support for only Anthropic/OpenAI/Google providers. The LLM factory needs extension to support these additional providers.

## Solution

Extend `backend/app/agents/llm_factory.py` to support OpenRouter and Ollama:

**1. OpenRouter Integration:**
- Add dependency: `langchain-openai` (OpenRouter uses OpenAI-compatible API)
- Add config fields to `backend/app/config.py`:
  - `openrouter_api_key: str = ""`
  - `openrouter_base_url: str = "https://openrouter.ai/api/v1"`
- Extend `get_llm()` factory:
  ```python
  elif provider == "openrouter":
      from langchain_openai import ChatOpenAI
      return ChatOpenAI(
          model=model,  # e.g., "anthropic/claude-sonnet-4"
          api_key=api_key,
          base_url=settings.openrouter_base_url,
          **kwargs
      )
  ```
- Models available via OpenRouter: `anthropic/claude-sonnet-4`, `openai/gpt-4`, `meta-llama/llama-3.1-70b`, etc.

**2. Ollama Integration:**
- Add dependency: `langchain-ollama` or use `langchain-community` ChatOllama
- Add config fields to `backend/app/config.py`:
  - `ollama_base_url: str = "http://localhost:11434"` (default Ollama endpoint)
- Extend `get_llm()` factory:
  ```python
  elif provider == "ollama":
      from langchain_ollama import ChatOllama
      return ChatOllama(
          model=model,  # e.g., "llama3.1", "mistral"
          base_url=api_key or settings.ollama_base_url,  # api_key param can pass custom URL
          **kwargs
      )
  ```
- Note: Ollama runs locally, no API key needed, but requires `ollama serve` running

**3. Update LLM provider choices:**
- Update `llm_provider` field in `backend/app/config.py`:
  ```python
  llm_provider: str = "anthropic"  # choices: anthropic, openai, google, openrouter, ollama
  ```
- Update validation in `get_llm()` to list all 5 supported providers in error message

**4. Documentation:**
- Update Phase 3 PLAN.md files to mention OpenRouter and Ollama as options
- Add setup instructions for Ollama (install, model pull, serve)
- Update environment variable examples in user_setup sections

**Implementation timing:** Can be done during or after Phase 3 execution. Non-blocking for initial Phase 3 work since default Anthropic provider works.
