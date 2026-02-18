---
phase: 16-frontend-restructure
plan: 02
subsystem: ui
tags: [next.js, react, session-routing, sse-streaming, tanstack-query, shadcn-sidebar]

requires:
  - phase: 16-frontend-restructure
    plan: 01
    provides: "Zustand session store, TanStack Query hooks, ChatSidebar component tree"
  - phase: 14-session-data-layer
    provides: "Session API endpoints (GET /sessions/{id}/messages, POST /chat/sessions/{id}/stream)"
provides:
  - "Session-centric dashboard layout with SidebarProvider wrapping ChatSidebar + main content"
  - "Session routes: /sessions/new (placeholder) and /sessions/[sessionId] (chat interface)"
  - "ChatInterface migrated from file-based to session-based props and endpoints"
  - "useChatMessages fetching from /sessions/{id}/messages"
  - "useSSEStream streaming from /chat/sessions/{id}/stream"
  - "Root and auth redirects pointing to /sessions/new"
affects: [16-03-PLAN, 17-file-management, 18-cleanup]

tech-stack:
  added: []
  patterns: [session-centric routing, SidebarProvider layout wrapper, session-based SSE streaming]

key-files:
  created:
    - frontend/src/app/(dashboard)/sessions/new/page.tsx
    - frontend/src/app/(dashboard)/sessions/[sessionId]/page.tsx
  modified:
    - frontend/src/app/(dashboard)/layout.tsx
    - frontend/src/app/(dashboard)/dashboard/page.tsx
    - frontend/src/app/page.tsx
    - frontend/src/hooks/useAuth.tsx
    - frontend/src/components/chat/ChatInterface.tsx
    - frontend/src/hooks/useChatMessages.ts
    - frontend/src/hooks/useSSEStream.ts
    - frontend/src/types/chat.ts

key-decisions:
  - "ContextUsage and trim-context deferred to Phase 18 (file-based endpoints not yet session-aware)"
  - "Legacy dashboard page converted to redirect stub instead of deletion (preserves bookmarks)"
  - "Empty state simplified to generic message (WelcomeScreen replaces QuerySuggestions in Plan 03)"

patterns-established:
  - "Session page pattern: useParams -> useSessionDetail -> ChatInterface with sessionId prop"
  - "SidebarProvider wraps entire dashboard layout at top level"
  - "Streaming messages use file_id: null for session-based flow"

duration: 4min
completed: 2026-02-11
---

# Phase 16 Plan 02: Dashboard Layout & Session Migration Summary

**Session-centric dashboard layout with SidebarProvider, session routes (/sessions/new, /sessions/[id]), and full ChatInterface migration from file-based to session-based API endpoints**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T22:22:46Z
- **Completed:** 2026-02-11T22:27:08Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Dashboard layout restructured: ChatSidebar (left) + main content, no top nav header, wrapped in SidebarProvider
- Session routing operational: /sessions/new (placeholder for WelcomeScreen) and /sessions/[sessionId] (ChatInterface with session data)
- ChatInterface fully migrated from file-based (fileId/fileName) to session-based (sessionId/sessionTitle)
- All chat data flow migrated: messages fetch from /sessions/{id}/messages, SSE streams from /chat/sessions/{id}/stream
- File-tab navigation completely removed from active flow (layout, ChatInterface)
- Auth flow redirects to /sessions/new (CHAT-09)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite dashboard layout, create session routes, update redirects** - `507c353` (feat)
2. **Task 2: Migrate ChatInterface, useChatMessages, and useSSEStream to session-based** - `21e82d5` (feat)

## Files Created/Modified
- `frontend/src/app/(dashboard)/layout.tsx` - Rewritten: SidebarProvider + ChatSidebar layout (removed top nav, FileSidebar, tabStore)
- `frontend/src/app/(dashboard)/sessions/new/page.tsx` - New session placeholder page (WelcomeScreen in Plan 03)
- `frontend/src/app/(dashboard)/sessions/[sessionId]/page.tsx` - Session chat page with useSessionDetail and ChatInterface
- `frontend/src/app/page.tsx` - Root redirect changed from /dashboard to /sessions/new
- `frontend/src/hooks/useAuth.tsx` - Login/signup redirects changed to /sessions/new
- `frontend/src/components/chat/ChatInterface.tsx` - Migrated from fileId/fileName to sessionId/sessionTitle props
- `frontend/src/hooks/useChatMessages.ts` - Migrated from /chat/{fileId}/messages to /sessions/{sessionId}/messages
- `frontend/src/hooks/useSSEStream.ts` - Migrated from /chat/{fileId}/stream to /chat/sessions/{sessionId}/stream
- `frontend/src/types/chat.ts` - ChatMessageResponse.file_id made nullable, added optional session_id
- `frontend/src/app/(dashboard)/dashboard/page.tsx` - Converted to redirect stub for /sessions/new

## Decisions Made
- ContextUsage component removed from ChatInterface header (file-based endpoint not session-aware yet); deferred to Phase 18 for session-based migration
- trim-context endpoint stubbed out with console.warn (file-based endpoint); deferred to Phase 18
- QuerySuggestions and useFileSummary removed from ChatInterface empty state; simplified to generic "Ask a question" message since WelcomeScreen (Plan 03) handles the proper greeting flow
- Legacy dashboard page converted to redirect stub rather than deleted, preserving bookmarks and avoiding broken imports during transition

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated legacy dashboard page to redirect stub**
- **Found during:** Task 2 (ChatInterface migration)
- **Issue:** Old dashboard/page.tsx used ChatInterface with fileId/fileName props which no longer exist, causing TypeScript build failure
- **Fix:** Converted dashboard page to a simple redirect stub that sends users to /sessions/new, consistent with plan intent to keep file but not use old interface
- **Files modified:** frontend/src/app/(dashboard)/dashboard/page.tsx
- **Verification:** `npx tsc --noEmit` and `npm run build` both pass cleanly
- **Committed in:** 21e82d5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for build compatibility. Plan noted "do not delete" the dashboard page but changing props made it type-incompatible. Redirect stub preserves the route while allowing clean build.

## Issues Encountered
None - both tasks executed smoothly after the dashboard page compatibility fix.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Session routes and ChatInterface fully migrated, ready for WelcomeScreen integration (Plan 03)
- /sessions/new page is a placeholder awaiting WelcomeScreen component
- SidebarProvider is in place, sidebar fully wired
- ContextUsage and trim-context need Phase 18 session-based migration

## Self-Check: PASSED

All 10 files verified on disk. Both task commits (507c353, 21e82d5) verified in git log.

---
*Phase: 16-frontend-restructure*
*Completed: 2026-02-11*
