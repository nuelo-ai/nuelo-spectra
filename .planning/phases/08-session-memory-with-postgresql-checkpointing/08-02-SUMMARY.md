---
phase: 08-session-memory-with-postgresql-checkpointing
plan: 02
subsystem: context-management
tags: [token-counting, tiktoken, context-trimming, frontend-ui, react-query, beforeunload]

# Dependency graph
requires:
  - phase: 08-session-memory-with-postgresql-checkpointing-01
    provides: AsyncPostgresSaver, checkpointer access from app.state, context_window_tokens config
provides:
  - Provider-agnostic token counting with tiktoken approximation and scaling factors
  - Message trimming utility with two-phase confirmation flow
  - GET /chat/{file_id}/context-usage endpoint (token count, percentage, warnings)
  - POST /chat/{file_id}/trim-context endpoint (prunes oldest messages to 90% of limit)
  - Frontend ContextUsage component displaying token usage with warning states
  - Browser tab close warning via useTabCloseWarning hook
  - Trim confirmation dialog integrated into ChatInterface
affects: [phase-09-query-suggestions, conversation-ux, memory-management]

# Tech tracking
tech-stack:
  added:
    - tiktoken (OpenAI tokenizer for universal approximation)
    - langchain_core.messages.trim_messages
    - beforeunload event listener (tab close warning)
  patterns:
    - Token counting factory pattern with provider-specific scaling factors
    - Two-phase trimming flow: check → user confirmation → trim → update state
    - React Query polling for context usage updates (messageCount as dependency)
    - Browser native beforeunload for tab close warning (no custom messages)

key-files:
  created:
    - backend/app/agents/memory/__init__.py
    - backend/app/agents/memory/token_counter.py
    - backend/app/agents/memory/trimmer.py
    - frontend/src/hooks/useTabCloseWarning.ts
    - frontend/src/components/chat/ContextUsage.tsx
  modified:
    - backend/app/routers/chat.py
    - frontend/src/components/chat/ChatInterface.tsx

key-decisions:
  - "Use tiktoken for all providers with scaling factors (1.0 OpenAI, 1.1 Anthropic, 1.05 Google) instead of provider-native APIs to avoid expensive network calls for frequent UI updates"
  - "Trim to 90% of context window on confirmation to leave headroom for new messages"
  - "Poll context usage every 60 seconds + on messageCount change for real-time updates"
  - "Show browser-native 'Leave site?' dialog (custom messages not supported by modern browsers)"
  - "Token counter uses tiktoken encoding with message overhead (4 tokens per message) per OpenAI spec"

patterns-established:
  - "TokenCounter Protocol for swappable implementations"
  - "Trim confirmation dialog appears when onLimitExceeded callback fires"
  - "Context usage displayed in header next to file name (non-intrusive)"
  - "Tab close warning only activates when hasContext (>2 messages)"

# Metrics
duration: 3min
completed: 2026-02-07
---

# Phase 8 Plan 2: Token Counting & Context Management Summary

**Tiktoken-based token counting with provider scaling, context usage display showing "X / 12,000 tokens" with trim confirmation, and browser tab close warning for conversation context**

## Performance

- **Duration:** 3 min 30 sec
- **Started:** 2026-02-07T20:32:46Z
- **Completed:** 2026-02-07T20:36:16Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Provider-agnostic token counting using tiktoken with scaling factors (avoids expensive API calls)
- Two-phase message trimming flow with user confirmation before pruning oldest messages
- Backend endpoints for context usage monitoring and trimming (GET /context-usage, POST /trim-context)
- Frontend context usage component showing "8,543 / 12,000 tokens" with orange warning at 85%, red at exceeded
- Browser tab close warning when conversation context exists (>2 messages)
- Trim confirmation dialog with "Trim older messages" and "Keep all messages" options
- All components integrate cleanly with existing ChatInterface and React Query patterns

## Task Commits

Each task was committed atomically:

1. **Task 1: Create token counting, trimming utilities, and context management endpoints** - `951b674` (feat)
   - Create backend/app/agents/memory/ module with __init__.py, token_counter.py, trimmer.py
   - Implement TiktokenCounter with provider-specific scaling (1.1x Anthropic, 1.05x Google)
   - Add get_token_counter factory function for provider-agnostic counting
   - Implement trim_if_needed with two-phase confirmation flow
   - Add GET /chat/{file_id}/context-usage endpoint (returns tokens, percentage, warnings)
   - Add POST /chat/{file_id}/trim-context endpoint (trims to 90% of limit)
   - Import get_or_create_graph in chat.py for checkpointer state access

2. **Task 2: Add frontend tab close warning, context usage display, and trim confirmation** - `3273ff6` (feat)
   - Create useTabCloseWarning hook with vanilla beforeunload listener
   - Create ContextUsage component with React Query polling (60s interval + messageCount trigger)
   - Integrate ContextUsage in ChatInterface header
   - Add trim confirmation dialog with orange warning banner
   - Wire handleTrimContext to POST /trim-context and refetch messages
   - TypeScript build passes with no errors

## Files Created/Modified

- `backend/app/agents/memory/__init__.py` - Memory module exports (get_token_counter, TokenCounter, trim_if_needed)
- `backend/app/agents/memory/token_counter.py` - TiktokenCounter implementation with provider scaling factors
- `backend/app/agents/memory/trimmer.py` - trim_if_needed with two-phase confirmation flow
- `backend/app/routers/chat.py` - Added /context-usage and /trim-context endpoints, import get_or_create_graph
- `frontend/src/hooks/useTabCloseWarning.ts` - Browser tab close warning hook (beforeunload event)
- `frontend/src/components/chat/ContextUsage.tsx` - Token usage display with warning states
- `frontend/src/components/chat/ChatInterface.tsx` - Integrated ContextUsage, tab close warning, trim dialog

## Decisions Made

**Token counting approach:**
- Decision: Use tiktoken as universal approximation with provider scaling factors instead of provider-native APIs
- Rationale: Provider-native counting (e.g., Anthropic's count_tokens()) requires network calls, too slow for frequent UI updates. Tiktoken with 1.1x scaling for Anthropic gives "close enough" counts (within 15%) for UI purposes.

**Trimming strategy:**
- Decision: Trim to 90% of context_window_tokens on user confirmation
- Rationale: Leaves 10% headroom for new messages before hitting limit again. Using langchain_core.messages.trim_messages with strategy="last" keeps most recent conversation.

**Warning thresholds:**
- Decision: Orange warning at 85%, red exceeded state triggers trim dialog
- Rationale: Matches context_warning_threshold from config (0.85). Gives users advance notice before hitting hard limit.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - token counter, trimmer, and endpoints implemented as specified. Frontend components integrated cleanly with existing React Query patterns.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Token counting and context management complete
- Context usage visible to users in real-time
- Ready for Phase 8 Plan 3 (conversation history UI) or Phase 9 (query suggestions with context awareness)
- All MEMORY requirements (MEMORY-03, MEMORY-06, MEMORY-07, MEMORY-08) satisfied across Plans 01 and 02

## Self-Check: PASSED

All files verified:
- FOUND: backend/app/agents/memory/__init__.py
- FOUND: backend/app/agents/memory/token_counter.py
- FOUND: backend/app/agents/memory/trimmer.py
- FOUND: frontend/src/hooks/useTabCloseWarning.ts
- FOUND: frontend/src/components/chat/ContextUsage.tsx

All commits verified:
- FOUND: 951b674 (Task 1)
- FOUND: 3273ff6 (Task 2)

---
*Phase: 08-session-memory-with-postgresql-checkpointing*
*Completed: 2026-02-07*
