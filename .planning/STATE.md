# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.3 Gap Closure — Phase 19 UAT retest gap fixes

## Current Position

Phase: 19 - v0.3 Gap Closure
Plan: 05 of 05 (Branding Placement) — COMPLETE
Status: Phase 19 complete. All 5 plans executed.
Branch: develop (fresh from master for v0.3)
Last activity: 2026-02-12 — Completed Plan 19-05

Progress: [████████████████████████████████] 100% (5/5 plans complete in Phase 19)

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
- Total plans completed: 14
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
- Phase 17 Plan 02: 3 min, 2 tasks, 5 files
- Phase 17 Plan 03: 3 min, 2 tasks, 6 files
- Phase 18 Plan 01: 2 min, 2 tasks, 4 files
- Phase 18 Plan 02: 2 min, 2 tasks, 2 files
- Phase 18 Plan 03: 4 min, 2 tasks, 9 files
- Total commits: 32
- Phase 19 Plan 01: 2 min, 2 tasks, 3 files
- Phase 19 Plan 02: 2 min, 2 tasks, 4 files
- Phase 19 Plan 03: 4 min, 2 tasks, 5 files
- Phase 19 Plan 04: 2 min, 2 tasks, 2 files
- Phase 19 Plan 05: 2 min, 2 tasks, 4 files

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

**Phase 17-02 (My Files Screen):**
- Page-level drop zone opens upload dialog (FileUploadZone handles actual upload inside dialog)
- FileContextModal uses controlled open={!!fileId} pattern for reuse from multiple contexts
- Sidebar My Files link updated from /files to /my-files to match route convention
- TanStack Table getRowId uses file.id for stable selection across re-renders

**Phase 17-03 (In-Chat File Linking):**
- Upload from chat uses prevFileIdsRef snapshot pattern to detect and auto-link newly uploaded files
- Paperclip button placed in toolbar row below textarea (alongside search toggle) via leftSlot prop
- FileCard switched from FileInfoModal to FileContextModal for consistent file info display
- Drag-and-drop overlay has its own upload dialog separate from FileLinkingDropdown (acceptable duplication)
- File limit errors surface via component-level onError callbacks with toast.error

**Phase 18-01 (File Requirement & Last-File Protection):**
- Input textarea stays enabled at all times (user can type freely), only send is blocked when no files linked
- Dual feedback on send attempt: toast.error (transient) + inline warning below toolbar (persistent until files linked)
- Auto-clear inline warning via useEffect when linkedFileIds.length > 0
- Defense-in-depth for last file: disabled button prevents dialog + handleUnlink guard with toast.warning

**Phase 18-02 (Light/Dark Theme Toggle):**
- ThemeProvider wraps Providers component in layout.tsx (Server Component) for SSR theme injection
- No explicit System theme option in toggle -- system preference only for initial default, then Light/Dark binary toggle
- mounted state check on theme toggle prevents hydration mismatch (theme-dependent icons differ between SSR and client)
- class-based dark mode via ThemeProvider attribute="class" activates existing .dark CSS variables in globals.css

**Phase 18-03 (LLM Session Title Auto-Generation):**
- POST /sessions/{id}/generate-title accepts no request body (security: prevents LLM proxy abuse)
- Service reads first user message from DB (not from client input) and truncates to 500 chars (defense in depth)
- user_modified=True set on manual rename, auto-generation skips if user_modified is true
- Title generation fails silently (session keeps "New Chat" title, error logged but not shown to user)
- Frontend ref guard (titleGenerated.current) prevents duplicate generation calls during re-renders
- Title generation triggers when messages >= 2, title is "New Chat", and user_modified is false

**Phase 19-01 (Sidebar Double-Click Rename & Cosmetics):**
- 250ms click-delay guard disambiguates single-click (navigate) vs double-click (rename) on sidebar items
- Spectra logo uses existing gradient-primary class from globals.css for consistent branding
- clickTimerRef cleanup on unmount prevents timer memory leaks (auto-fixed deviation)

**Phase 19-02 (FileCard File Size, Tooltip & Bulk Delete Fixes):**
- Conditional isLastFile branching in FileCard: Tooltip when true, AlertDialog when false (avoids disabled-button-inside-trigger pointer-events issue)
- Bulk delete uses rowSelection keys directly as UUIDs since getRowId returns row.id
- Disabled button tooltip pattern: wrap disabled button in <span> inside TooltipTrigger to intercept hover through pointer-events-none

**Phase 19-03 (Drag-Drop File Upload & Sidebar Auto-Open):**
- initialFiles prop with useRef guard prevents double-processing in React Strict Mode
- WelcomeScreen uses separate dragUploadDialogOpen state to avoid conflicts with paperclip upload dialog
- setRightPanelOpen(true) NOT added to WelcomeScreen since it has no right panel (pre-message state)

**Phase 19-04 (Drag-Drop Analyzing Hang & Sidebar Auto-Open):**
- setTimeout(0) is minimal fix for Strict Mode MutationObserver disconnection (matches ChatInterface.tsx pattern)
- setRightPanelOpen(true) called before router.replace in handleSend so Zustand state persists across navigation
- Phase 19-03 decision that WelcomeScreen has no right panel was incorrect -- WelcomeScreen links files to existing sessions too

**Phase 19-05 (Branding Placement):**
- Branding moved from sidebar to main content header for always-visible placement (ChatGPT-style)
- Pipe separator (|) between branding and page title on ChatInterface and My Files; omitted on WelcomeScreen (no title context)
- Consistent pattern across all views: SidebarTrigger + gradient S logo + Spectra text + optional pipe + title

See also: PROJECT.md Key Decisions table for milestone-level decisions.

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment)
- [ ] Query safety filter in Manager Agent (security — block PII extraction, prompt injection, etc.)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (eliminate inconsistent JSON rendering across LLM providers)

### Blockers/Concerns

- E2B sandboxes created per-execution (no warm pools) — acceptable, optimization deferred to future milestone

## Session Continuity

Last session: 2026-02-12
Stopped at: Completed 19-05-PLAN.md (Phase 19 complete)
Resume with: Full v0.3 UAT retest — all 5 gap closure plans executed
Next decision: Run UAT retest to verify all v0.3 gaps are closed
UI directive: Use Frontend Design skill (/frontend-design) for UI work in Phases 16, 17, 18, 19
