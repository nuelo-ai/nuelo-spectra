---
phase: 15-agent-system-enhancement
plan: 01
subsystem: services
tags: [context-assembler, tiktoken, token-budget, join-hints, multi-file, yaml-config]

# Dependency graph
requires:
  - phase: 14-database-foundation-migration
    provides: "Session model with files M2M, FileService.get_user_file(), OnboardingAgent.profile_data()"
provides:
  - "ContextAssembler service with progressive reduction and join hint detection"
  - "settings.yaml with configurable file limits and token budget"
  - "load_session_settings() cached YAML loader"
affects: [15-02, 15-03, agent-service, coding-agent, manager-agent]

# Tech tracking
tech-stack:
  added: [settings.yaml config file]
  patterns: [progressive-token-reduction, join-hint-detection, var-name-sanitization, module-level-yaml-config]

key-files:
  created:
    - backend/app/config/settings.yaml
    - backend/app/services/context_assembler.py
  modified: []

key-decisions:
  - "ContextAssembler loads settings.yaml independently (not via config.py Settings class)"
  - "Effective budget = token_budget * (1 - safety_margin) = 6400 tokens default"
  - "OnboardingAgent imported inside assemble() method to avoid circular imports"
  - "Collision handling appends _2, _3 etc. to df_ variable names"
  - "Join hints sorted by column name for deterministic output"

patterns-established:
  - "Progressive reduction: full -> no_samples -> no_stats -> minimal"
  - "YAML config loading with @lru_cache following agents/config.py pattern"
  - "Fail-whole-query validation: all files must exist and be onboarded before assembly"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 15 Plan 01: Context Assembler Summary

**ContextAssembler service with progressive token budget reduction, join hint detection with type mismatch warnings, and configurable file limits via settings.yaml**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T20:44:24Z
- **Completed:** 2026-02-11T20:47:35Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- ContextAssembler service profiles files via OnboardingAgent.profile_data() and assembles multi-file context within configurable token budget
- Progressive reduction across 4 levels (full, no_samples, no_stats, minimal) keeps context within effective budget of 6400 tokens
- Join hint detection finds shared column names across file pairs with dtype mismatch warnings
- DataFrame variable name sanitization handles special chars, leading digits, and collisions (df_sales, df_sales_2)
- settings.yaml provides configurable file limits (max_files_per_session: 5, ceiling: 10, max size: 50MB) and token budget (8000 with 20% safety margin)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create settings.yaml with file limits and token budget configuration** - `25cf766` (feat)
2. **Task 2: Create ContextAssembler service with progressive reduction and join hints** - `77ed1e7` (feat)

## Files Created/Modified
- `backend/app/config/settings.yaml` - Multi-file session limits and context assembly token budget configuration
- `backend/app/services/context_assembler.py` - Standalone service: ContextAssembler class with assemble(), _sanitize_var_name(), _detect_join_hints(), _build_context_string(), _count_tokens(), and load_session_settings()

## Decisions Made
- ContextAssembler loads settings.yaml via its own load_session_settings() function (not config.py Settings class) following the pattern of agents/config.py load_prompts()
- OnboardingAgent is imported inside the assemble() method to avoid circular imports (same pattern as agent_service.py line 398)
- Effective token budget is token_budget * (1 - safety_margin) = 8000 * 0.8 = 6400 tokens
- Variable name collision handling appends numeric suffixes (_2, _3) rather than using UUID or hash
- Join hint column iteration is sorted() for deterministic output order
- If even minimal reduction exceeds budget, returns minimal context with "minimal_exceeded" reduction_level (graceful degradation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ContextAssembler ready for integration into agent_service.py (Plan 03)
- Plan 02 will update Coding Agent prompts and Manager Agent routing for multi-file context
- settings.yaml file limits ready to be enforced in ChatSessionService (Plan 03)

## Self-Check: PASSED

- FOUND: backend/app/config/settings.yaml
- FOUND: backend/app/services/context_assembler.py
- FOUND: .planning/phases/15-agent-system-enhancement/15-01-SUMMARY.md
- FOUND: commit 25cf766 (Task 1)
- FOUND: commit 77ed1e7 (Task 2)

---
*Phase: 15-agent-system-enhancement*
*Completed: 2026-02-11*
