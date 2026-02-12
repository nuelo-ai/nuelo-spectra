---
status: diagnosed
trigger: "Investigate why the onboarding pipeline takes a very long time before it starts processing when uploading a file from the My Files screen"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - Multiple root causes identified
test: Code trace complete
expecting: N/A
next_action: Report findings

## Symptoms

expected: File upload triggers onboarding pipeline that begins processing promptly
actual: Long delay before onboarding processing begins after file upload
errors: None reported — just slow start
reproduction: Upload a file from the My Files screen
started: Unknown — possibly related to v0.3 session-based changes

## Eliminated

- hypothesis: Polling loop or redundant API calls causing delay
  evidence: Frontend polls every 3s via useFileSummary hook — this is appropriate and not the cause
  timestamp: 2026-02-12

- hypothesis: Retry loop in onboarding agent
  evidence: OnboardingAgent.run() is strictly sequential: profile_data -> generate_summary. No retry loops.
  timestamp: 2026-02-12

- hypothesis: v0.3 session-based changes added overhead to upload/onboarding flow
  evidence: The upload endpoint (files.py POST /upload) and run_onboarding() in agent_service.py are unchanged by session logic. Session logic only affects chat queries.
  timestamp: 2026-02-12

## Evidence

- timestamp: 2026-02-12
  checked: Upload endpoint flow (routers/files.py)
  found: Upload creates file record, then fires asyncio.create_task for background onboarding. Upload response returns immediately.
  implication: Upload itself is not blocking. Delay is in background onboarding task.

- timestamp: 2026-02-12
  checked: run_onboarding() in agent_service.py
  found: Calls OnboardingAgent().run() which calls profile_data() then generate_summary()
  implication: Delay must be in one of these two phases

- timestamp: 2026-02-12
  checked: OnboardingAgent.profile_data() (onboarding.py:69-134)
  found: READS ENTIRE FILE with pd.read_csv(file_path) — NO nrows limit. Computes nunique(), describe(), duplicated() on ALL rows/columns. For large files (10k+ rows, many columns), this is expensive.
  implication: PRIMARY CAUSE #1 — Full file read + per-column stats + duplicate detection on entire dataset

- timestamp: 2026-02-12
  checked: OnboardingAgent.generate_summary() (onboarding.py:144-221)
  found: Uses asyncio.to_thread(llm.invoke, messages) — synchronous blocking LLM call. Configured as anthropic/claude-sonnet-4 with max_tokens=3000. Profile JSON (full dataset stats) is serialized and sent as the user message.
  implication: PRIMARY CAUSE #2 — LLM call latency (network round-trip to Anthropic + token generation for 3000 max_tokens). Large profile JSON = more input tokens = longer processing.

- timestamp: 2026-02-12
  checked: Frontend polling mechanism (useFileManager.ts:96-117)
  found: useFileSummary polls GET /files/{id}/summary every 3 seconds. Only stops when data_summary is non-null.
  implication: Frontend polling is fine. The perceived "long time" is the actual backend processing time.

- timestamp: 2026-02-12
  checked: Additional profile_data calls in chat flow (agent_service.py:439-452, context_assembler.py:122-131)
  found: profile_data() is called AGAIN on every streaming chat query (run_chat_query_stream line 443) and on every ContextAssembler.assemble() call (line 128, per file). Both read the ENTIRE file each time.
  implication: SECONDARY ISSUE — Not the onboarding delay, but will cause delays on every chat query too. The comment on line 439 ("quick operation, only reads 5 rows") is factually wrong.

## Resolution

root_cause: |
  The onboarding pipeline delay has two compounding causes:

  1. **profile_data() reads entire file** (onboarding.py:73): pd.read_csv(file_path) loads the complete dataset into memory with no nrows limit. Then it computes nunique(), describe(), and duplicated() on every column of the full dataset. For a 50MB file with many columns, this can take 5-30+ seconds.

  2. **Synchronous blocking LLM call** (onboarding.py:189): asyncio.to_thread(llm.invoke, ...) makes a synchronous API call to Anthropic Claude Sonnet with the full profile JSON. The large profile payload (full column stats for every column) increases input tokens, adding 3-10+ seconds of API latency.

  Combined: profile_data (5-30s) + LLM call (3-10s) = 8-40s perceived delay before onboarding completes.

  BONUS: profile_data is also called redundantly on every chat query (agent_service.py:443) and per-file in ContextAssembler (context_assembler.py:128), creating ongoing per-query delays.

fix:
verification:
files_changed: []
