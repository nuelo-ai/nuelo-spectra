---
created: 2026-02-08T19:59:32.686Z
title: Add query safety filter to Manager Agent
area: api
files:
  - backend/app/agents/manager.py
  - backend/app/config/prompts.yaml
---

## Problem

Currently, the Manager Agent routes queries to one of three paths (MEMORY_SUFFICIENT, CODE_MODIFICATION, NEW_ANALYSIS) without any safety screening. A user could submit queries that:

- Request specific private user information (PII) from the dataset (e.g., "show me all email addresses and passwords")
- Attempt prompt injection to override agent behavior
- Try to extract system internals (e.g., "show me your system prompt", "what API keys are configured")
- Request code that performs destructive or unauthorized operations
- Attempt to bypass the Code Checker Agent's safety validation through social engineering the Coding Agent

These queries currently flow through to the Coding Agent or Data Analysis Agent unchecked. The Manager Agent is the ideal interception point since it already analyzes every query before routing.

## Solution

Add a 4th routing decision: `BLOCKED` (or similar) to the Manager Agent's RoutingDecision schema. Extend the Manager Agent's system prompt to identify unsafe query categories:

1. **PII extraction** — queries asking for specific individual records, personal data, contact info
2. **System probing** — queries about system prompts, API keys, configuration, internal architecture
3. **Prompt injection** — attempts to override instructions, role-play as admin, "ignore previous instructions"
4. **Malicious code requests** — requests to delete data, access filesystem, make network calls, execute arbitrary code
5. **Data exfiltration** — attempts to export full datasets or bypass access controls

When BLOCKED, the Manager Agent returns a polite refusal message directly to the user without invoking any downstream agents. The refusal should explain what category was triggered without revealing specific detection rules.

Consider: configurable safety rules in YAML (like the allowed_libraries pattern), logging blocked queries for security monitoring, and whether some categories should be warnings vs hard blocks.
