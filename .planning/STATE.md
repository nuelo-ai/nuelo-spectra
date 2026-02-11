# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.3 Multi-file Conversation Support — roadmap created, ready for planning

## Current Position

Phase: 16 - Frontend Restructure (Session-Centric UX)
Plan: 02 of 03 (Dashboard Layout & Session Migration) — COMPLETE
Status: Executing Phase 16 — plan 02 complete, session routes and ChatInterface migrated
Branch: develop (fresh from master for v0.3)
Last activity: 2026-02-11 — Completed 16-02-PLAN.md

Progress: [██████████████████████░░░░░░░░░░░] 67% (2/3 plans complete in Phase 16)

## Performance Metrics

**Velocity (v0.1):**
- Total plans completed: 36
- Total execution time: ~5 days (Feb 1-6, 2026)
- Plans per day: ~7 plans/day

**Velocity (v0.2):**
- Total plans completed: 19
- Total execution time: ~4 days (Feb 7-10, 2026)
- Plans per day: ~5 plans/day
- Total commits: 110

**Velocity (v0.3):**
- Total plans completed: 8
- Phase 14 Plan 01: 3 min, 2 tasks, 7 files
- Phase 14 Plan 02: 4 min, 2 tasks, 3 files
- Phase 14 Plan 03: 3 min, 2 tasks, 5 files
- Phase 14 Plan 04: 4 min, 2 tasks, 3 files
- Phase 15 Plan 01: 3 min, 2 tasks, 2 files
- Phase 15 Plan 02: 2 min, 2 tasks, 2 files
- Phase 15 Plan 03: 3 min, 2 tasks, 6 files
- Phase 16 Plan 01: 4 min, 2 tasks, 13 files
- Phase 16 Plan 02: 4 min, 2 tasks, 10 files
- Total commits: 18

## Accumulated Context

### Decisions

**Phase 14-01 (ChatSession Model & Schemas):**
- ChatMessage.session_id is nullable for migration compatibility (will be made NOT NULL after data migration)
- session_files association table uses CASCADE deletes on both FKs (deleting session removes associations, not files)
- File-to-Session M2M has no cascade delete from File side (deleting file removes associations, not sessions)
- Association tables use SQLAlchemy Core Table, not ORM class
- TYPE_CHECKING imports avoid circular dependencies

**Phase 14-02 (Migration Scripts):**
- Use session_files table for checkpoint migration (covers files with no messages)
- Preserve orphaned checkpoints for deleted files (harmless, age out naturally)
- Make file_id nullable with SET NULL on delete (DATA-06 requirement)
- Checkpoint downgrade raises NotImplementedError (requires backup restoration)

**Phase 14-03 (Session Service & API):**
- ChatMessage.file_id made nullable to match migration (SET NULL on file delete)
- Service methods raise ValueError for business logic errors, router converts to HTTPException
- 10-file-per-session limit enforced at service layer
- Session-based messages use file_id=None (messages belong to sessions, not files)

**Phase 14-04 (Session-Based Agent Integration):**
- Session-based endpoints require at least one linked file (400 error if none)
- File-based endpoints preserved during transition (removed in later phase)
- Agent service file_id parameter made optional (UUID | None) for session-based flow
- Session-based flow uses first file's context (multi-file assembly is Phase 15 scope)
- Thread_id format: session_{session_id}_user_{user_id} for sessions, file_{file_id}_user_{user_id} for files

**Phase 15-01 (Context Assembler Service):**
- ContextAssembler loads settings.yaml independently (not via config.py Settings class), following agents/config.py pattern
- Effective token budget = token_budget * (1 - safety_margin) = 8000 * 0.8 = 6400 tokens
- OnboardingAgent imported inside assemble() method to avoid circular imports
- Variable name collision handling appends numeric suffixes (_2, _3) to df_ names
- Join hints sorted by column name for deterministic output
- Fail-whole-query: all files must exist and be onboarded, otherwise ValueError

**Phase 15-02 (Agent State & Prompts):**
- New state fields use default-compatible types (str='', list=[], None) so state.get() works without migration
- session_id added to TypedDict to make existing agent_service.py usage explicit
- Coding prompt uses {multi_file_context} placeholder that is empty string for single-file (no conditional logic needed)
- Join hint confirmation is mandatory before agent generates cross-file merge code

**Phase 15-03 (Agent Pipeline Integration):**
- ContextAssembler ValueError in streaming flow yields error event (not HTTPException) for consistent SSE handling
- Multi-file vs single-file branching in execute_in_sandbox uses file_metadata emptiness (not session_id)
- Selective loading uses var_name substring match in code -- sufficient because ContextAssembler generates unique df_ prefixed names
- E2B data_files parameter is additive alongside existing data_file/data_filename (both paths coexist)

**Phase 16-01 (Session State & Left Sidebar):**
- Sidebar uses shadcn default 16rem (256px) width, within user's 260-300px range
- Optimistic update for session rename with rollback on error
- Delete redirects to /dashboard when active session is deleted
- Session list staleTime 5 minutes to balance freshness with request volume
- UserSection replicates avatar gradient style from existing dashboard layout

**Phase 16-02 (Dashboard Layout & Session Migration):**
- ContextUsage and trim-context deferred to Phase 18 (file-based endpoints not yet session-aware)
- Legacy dashboard page converted to redirect stub instead of deletion (preserves bookmarks)
- Empty state simplified to generic message (WelcomeScreen replaces QuerySuggestions in Plan 03)

See also: PROJECT.md Key Decisions table for milestone-level decisions.

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment)
- [ ] Query safety filter in Manager Agent (security — block PII extraction, prompt injection, etc.)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (eliminate inconsistent JSON rendering across LLM providers)

### Blockers/Concerns

- E2B sandboxes created per-execution (no warm pools) — acceptable, optimization deferred to future milestone

## Session Continuity

Last session: 2026-02-11
Stopped at: Completed 16-02-PLAN.md (Dashboard Layout & Session Migration)
Resume with: Execute 16-03-PLAN.md (WelcomeScreen & Session Creation Flow)
Next decision: Session routes and ChatInterface migrated. Plan 03 adds WelcomeScreen to /sessions/new page.
UI directive: Use Frontend Design skill (/frontend-design) for UI work in Phases 16, 17, 18
