# Phase 17: File Management & Linking - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can manage files independently and link them to chat sessions. This phase delivers the My Files screen (standalone file management page) and the file linking flow within chat sessions (add file button, selection modal, drag-and-drop). Dependencies: Phase 14 (session model), Phase 16 (My Files route in sidebar).

</domain>

<decisions>
## Implementation Decisions

### My Files Screen
- Follow Julius.ai structure as reference
- Table/list view layout (rows with columns, not card grid)
- Columns: file name (with type icon), size, upload date — essential metadata only
- Drag-and-drop zone at top of page (dashed border, upload icon, "Drag files to upload")
- "Upload file" button below the drag zone
- Search bar for filtering files by name
- Bulk action: Delete only (Download and Chat with files removed from bulk actions)
- Checkboxes for multi-select (select-all in header, per-row checkboxes)
- Per-row inline icon: chat icon (start new chat with this file)
- Per-row three-dot menu: View context, Download, Delete

### File Selection Modal
- Single file selection per modal interaction (not multi-select)
- Shows file name with type icon, size, and upload date (consistent with My Files table)
- Search field at top for filtering files by name
- Already-linked files shown but disabled with a "linked" badge (not hidden)

### In-Chat File Adding
- Paperclip icon below chat input (like Julius.ai)
- Dropdown on click with three sections:
  - "Upload File" — triggers upload with modal overlay for onboarding
  - "Link Existing File" — opens file selection modal
  - "Recent" section — lists recent files for quick one-click linking
- Clicking a recent file links it immediately (no confirmation step)
- Drag-and-drop works on full chat area — drop zone overlay appears on drag
- Upload from chat uses modal overlay for onboarding (same flow as My Files), file auto-links to session on completion

### File Context Details
- "View context" opens a modal/dialog showing file profiling details (data summary, columns, row count)
- Same modal used from both My Files three-dot menu and right sidebar info icon — consistent experience

### File Deletion
- Simple confirmation dialog: "Delete file? This cannot be undone."
- No impact details shown (messages preserved, file context removed — handled silently)

### File Limit Enforcement
- When user tries to add a file beyond the configured maximum (from config settings), show an error message indicating the limit has been reached
- Limit is config-driven, not hardcoded

### Claude's Discretion
- Empty state design for My Files when no files exist
- Exact styling of drag-and-drop overlay on chat area
- "Recent" section: how many recent files to show, how "recent" is defined
- Loading states and skeleton patterns
- Error handling for failed uploads and failed file linking

</decisions>

<specifics>
## Specific Ideas

- Julius.ai My Files page used as reference for layout structure (drag zone at top, upload button, search + bulk actions bar, table below)
- Julius.ai paperclip dropdown used as reference for in-chat file adding (simplified for Spectra — no connectors like Google Drive, OneDrive, SharePoint)
- File context modal reused across both My Files and right sidebar — single component, two entry points

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-file-management-linking*
*Context gathered: 2026-02-11*
