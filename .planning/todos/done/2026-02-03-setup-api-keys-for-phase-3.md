---
created: 2026-02-03T09:26
title: Setup API keys for Phase 3 execution
area: planning
files:
  - backend/app/config.py
  - .planning/phases/03-ai-agents---orchestration/03-01-PLAN.md
---

## Problem

Phase 3 (AI Agents & Orchestration) requires two external API keys before execution can begin:

1. **ANTHROPIC_API_KEY** - Required for Claude LLM powering all 4 agents (Onboarding, Coding, Code Checker, Data Analysis)
2. **LANGSMITH_API_KEY** - Optional but recommended for agent observability and tracing

Plan 03-01 has user_setup section documenting these requirements, but the keys need to be obtained and configured in the environment before running `/gsd:execute-phase 3`.

Without these keys:
- LangGraph workflows will fail on first LLM invocation
- Onboarding Agent cannot generate data summaries
- Chat queries will error immediately
- No agent observability/debugging capability

## Solution

Before executing Phase 3:

1. **Anthropic API Key:**
   - Visit Anthropic Console (https://console.anthropic.com)
   - Navigate to API Keys section
   - Create new key
   - Add to `.env` file: `ANTHROPIC_API_KEY=sk-ant-...`
   - Or export: `export ANTHROPIC_API_KEY=sk-ant-...`

2. **LangSmith API Key (optional but recommended):**
   - Visit LangSmith (https://smith.langchain.com)
   - Go to Settings → API Keys
   - Create new key
   - Add to `.env`: `LANGSMITH_API_KEY=...`
   - Add to `.env`: `LANGSMITH_TRACING=true`
   - Add to `.env`: `LANGSMITH_PROJECT=spectra-agents`

3. **Verify configuration:**
   - Keys loaded in `backend/app/config.py` Settings class
   - agent_service.py sets LangSmith env vars from settings at initialization
   - Test with: `python -c "from app.config import get_settings; s = get_settings(); print('Anthropic:', bool(s.anthropic_api_key))"`

Alternative: Set as environment variables before running backend server if not using `.env` file.
