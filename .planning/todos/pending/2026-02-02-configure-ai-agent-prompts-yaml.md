---
created: 2026-02-02T13:22
title: Configure AI agent prompts in separate YAML file
area: agents
files: []
---

## Problem

When designing the AI Agent system using LangChain (Onboarding Agent, Coding Agent, Code Checker Agent, Data Analysis Agent), system prompts should be externalized to separate YAML configuration files. This allows prompt customization and tuning without requiring code recompilation or deployment.

Currently, there's a risk of hardcoding prompts directly in Python code, which makes iteration slow and requires developer involvement for prompt adjustments.

## Solution

Design the LangChain agent architecture to load system prompts from YAML configuration files:
- Create a prompts configuration directory (e.g., `config/prompts/`)
- One YAML file per agent type (onboarding.yaml, coding.yaml, code_checker.yaml, data_analysis.yaml)
- Load prompts at runtime using LangChain's prompt template system
- Consider environment-specific overrides (dev/staging/prod)

This enables non-developer prompt engineering and faster iteration during AI tuning phase.
