# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.3 Multi-file Conversation Support — roadmap created, ready for planning

## Current Position

Phase: 17 - File Management & Linking
Plan: 01 of 03 (File Download Endpoint & Frontend Hooks) — COMPLETE
Status: Plan 17-01 complete — download endpoint and hooks built. Continuing to Plan 02.
Branch: develop (fresh from master for v0.3)
Last activity: 2026-02-11 — Completed Plan 17-01

Progress: [██████████░░░░░░░░░░░░░░░░░░░░░░] 33% (1/3 plans complete in Phase 17)

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
- Total plans completed: 11
- Phase 14 Plan 01: 3 min, 2 tasks, 7 files
- Phase 14 Plan 02: 4 min, 2 tasks, 3 files
- Phase 14 Plan 03: 3 min, 2 tasks, 5 files
- Phase 14 Plan 04: 4 min, 2 tasks, 3 files
- Phase 15 Plan 01: 3 min, 2 tasks, 2 files
- Phase 15 Plan 02: 2 min, 2 tasks, 2 files
- Phase 15 Plan 03: 3 min, 2 tasks, 6 files
- Phase 16 Plan 01: 4 min, 2 tasks, 13 files
- Phase 16 Plan 02: 4 min, 2 tasks, 10 files
- Phase 16 Plan 03: 3 min, 2 tasks, 7 files
- Phase 17 Plan 01: 2 min, 2 tasks, 3 files
- Total commits: 22

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

**Phase 16-03 (WelcomeScreen & LinkedFilesPanel):**
- New session page auto-creates session on mount and redirects to /sessions/[id] for consistent sessionId availability
- Session page shows WelcomeScreen when zero messages, transitions to ChatInterface when messages exist
- Right panel toggle in ChatInterface header shows file count badge from session detail
- FileCard action buttons (info, remove) appear on hover for cleaner visual

**Phase 17-01 (File Download Endpoint & Frontend Hooks):**
- Download endpoint uses FileResponse with application/octet-stream for universal download behavior
- useRecentFiles derives from existing useFiles cache (no separate API endpoint)
- useBulkDeleteFiles invalidates both "files" and "sessions" query keys (CASCADE on session_files)
- Download endpoint checks both DB record and disk file existence (separate 404 messages)

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
Stopped at: Completed 17-01-PLAN.md
Resume with: Execute Plan 17-02 (My Files Screen)
Next decision: Plan 17-01 complete — download endpoint and frontend hooks ready. Plan 02 builds the My Files screen UI consuming these hooks.
UI directive: Use Frontend Design skill (/frontend-design) for UI work in Phases 16, 17, 18
