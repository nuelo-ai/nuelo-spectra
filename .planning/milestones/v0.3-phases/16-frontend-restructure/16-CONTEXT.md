# Phase 16: Frontend Restructure (Session-Centric UX) - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace file-tab navigation with a session-centric layout. Users navigate via chat sessions in a left sidebar, conversations display in the main area, and linked files show in a collapsible right panel. File management (My Files screen, upload, delete) and integration polish are separate phases (17, 18).

</domain>

<decisions>
## Implementation Decisions

### Left Sidebar Design
- Collapsible sidebar with toggle button — when collapsed, shows icons only (New Chat, recent chat icons, My Files)
- Fixed width when expanded (~260-300px, Claude's discretion on exact value)
- Top section: "New Chat" button and "My Files" button grouped together
- Middle section: Flat chronological chat list, most recent first — NO time grouping (Today/Week/Month removed from requirements)
- Bottom section: User profile/avatar with dropdown for Settings, Logout
- Each chat item shows title only (no timestamp, no file count, no preview)
- Active session indicated by highlighted background color
- Hover on chat item reveals three-dot menu with Rename and Delete options
- Delete requires confirmation dialog; Rename is inline edit
- No search/filter for chat history in this phase

### Welcome Screen
- Friendly, warm greeting: "Hi [name]! What would you like to analyze today?" style
- Text-only greeting — no logo, no action cards, no quick-start tiles
- Chat input is always active (not disabled) — if user sends a message without a linked file, show a prompt asking them to "Add a file first"
- Query suggestions appear below greeting once first file is linked
- Suggestions refresh when additional files are linked (reflect all currently linked files)
- Initial suggestions disappear after first user message; follow-up suggestions continue to appear on Data Cards as in current flow

### Chat List Display
- Flat chronological list, most recent first
- Title-only display per session — compact and clean
- Active session: highlighted background
- Chat list loading strategy: Claude's discretion (load all vs lazy-load based on expected volume)

### Linked Files Right Panel
- Collapsible right sidebar panel (not top bar, not header strip)
- Toggle button in the chat header area to show/hide
- Default state: closed (maximizes chat area)
- Each file shows: file name + row/column count + file type icon + (i) info button + remove button
- Clicking (i) opens file context modal (same as current version)
- Remove button unlinks file from chat session with confirmation dialog ("Remove [filename] from this chat?")
- File removal unlinks only — does not delete the file itself

### Claude's Discretion
- Exact sidebar width when expanded
- Chat list loading strategy (all-at-once vs lazy-load)
- Collapsed sidebar icon design
- Transition animations between states
- Exact spacing, typography, and color values
- Mobile/responsive breakpoint behavior

</decisions>

<specifics>
## Specific Ideas

- The overall feel should be similar to ChatGPT's session-centric navigation — sidebar with chat history, main chat area, sessions as the primary navigation unit
- Current query suggestion system preserved: initial suggestions below greeting (from linked file context), follow-up suggestions on Data Cards after analysis
- The chat input should feel always-ready — not disabled or hidden when no file is linked, but gracefully redirect user to add a file when they try to send

</specifics>

<deferred>
## Deferred Ideas

- Chat history search/filter — future enhancement when chat volume warrants it
- Time-based grouping of chat history (Today, This Week, etc.) — removed from Phase 16, can be reconsidered later

</deferred>

---

*Phase: 16-frontend-restructure*
*Context gathered: 2026-02-11*
