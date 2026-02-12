---
status: testing
phase: v0.3-multi-file-conversation-support
source: 14-01-SUMMARY.md, 14-02-SUMMARY.md, 14-03-SUMMARY.md, 14-04-SUMMARY.md, 15-01-SUMMARY.md, 15-02-SUMMARY.md, 15-03-SUMMARY.md, 16-01-SUMMARY.md, 16-02-SUMMARY.md, 16-03-SUMMARY.md, 17-01-SUMMARY.md, 17-02-SUMMARY.md, 17-03-SUMMARY.md, 18-01-SUMMARY.md, 18-02-SUMMARY.md, 18-03-SUMMARY.md
started: 2026-02-11T22:00:00Z
updated: 2026-02-12T15:00:00Z
---

## Current Test

number: 1
name: Left sidebar shows session list with New Chat button
expected: |
  After logging in, you see a collapsible left sidebar with a "New Chat" button,
  chronological session list (grouped by time), "My Files" link, and user profile
  section at the bottom. No file tabs visible.
awaiting: user response

## Tests

### 1. Left sidebar shows session list with New Chat button
expected: After logging in, you see a collapsible left sidebar with a "New Chat" button, chronological session list (grouped by time), "My Files" link, and user profile section at the bottom. No file tabs visible.
result: issue
reported: "Sidebar layout mostly correct (collapsible, New Chat button, My Files, user profile, no file tabs). BUT: every page load auto-creates a new empty session, causing 'New Chat' entries to pile up in sidebar. Sessions should only be created when user sends first message, not on load."
severity: major

### 2. Create new chat session and see welcome screen
expected: Click "New Chat" in sidebar. A new session appears in sidebar as "New Chat". Main area shows a personalized welcome screen with "Hi {your name}!" greeting. Chat input is active and ready to type.
result: [pending]

### 3. File requirement enforcement — can't send without files
expected: In the new session (no files linked), type a message and press Enter or click Send. You should see a toast error "Link at least one file before sending a message" AND a persistent inline warning with an alert icon below the input saying "Link at least one file to start chatting". The message is NOT sent. You can still type freely.
result: [pending]

### 4. Link a file to chat via paperclip button
expected: Click the paperclip icon in the chat toolbar (below the input area). A dropdown appears with options to upload a new file or link an existing file. Select an existing file — it links to the session. The inline "link a file" warning disappears automatically. The right sidebar panel shows the linked file.
result: [pending]

### 5. Send a message and receive AI response
expected: With a file linked, type a data analysis question (e.g. "What are the columns in this dataset?") and send. The message appears in the chat. An AI response streams back with analysis or code output. The chat works normally.
result: [pending]

### 6. Session title auto-generates after first exchange
expected: After the first AI response completes, the sidebar updates the session title from "New Chat" to an LLM-generated descriptive title (e.g. "Dataset Column Analysis"). This happens automatically within a few seconds.
result: [pending]

### 7. Rename session via sidebar (locks title)
expected: Double-click or click the edit control on a session in the sidebar. Type a custom name and press Enter. The session renames. After renaming, the title should NOT be auto-generated again (it's locked).
result: [pending]

### 8. Right sidebar panel shows linked files
expected: Click the file count badge/toggle in the chat header area. A right sidebar panel opens showing the files linked to this session. Each file shows its name, size, and action buttons (info, remove) on hover.
result: [pending]

### 9. View file context details from right panel
expected: In the right sidebar panel, click the info icon on a linked file. A modal opens showing file profiling details: data summary, column information, row count, and any context/feedback from AI onboarding.
result: [pending]

### 10. Last file protection — can't remove only file
expected: With only 1 file linked to the session, hover over the file in the right panel and try to click the remove button. It should be disabled with a tooltip explaining "Cannot remove last file — at least one file must be linked". No confirmation dialog opens.
result: [pending]

### 11. Link a second file and verify multi-file display
expected: Use the paperclip button to link a second file to the session. Both files now appear in the right sidebar panel. The file count badge in the header updates to show "2".
result: [pending]

### 12. Multi-file analysis — cross-file question
expected: With 2+ files linked, ask a cross-file question (e.g. "Compare the data from both files" or "What columns do these files share?"). The AI generates Python code that references multiple DataFrames with proper names (e.g. df_sales, df_customers — not generic "df"). Code executes and returns results.
result: [pending]

### 13. Remove a file from session (not the last one)
expected: With 2+ files linked, click the remove button on one file in the right panel. A confirmation dialog appears. Confirm removal. The file is unlinked from the session (removed from right panel) but the file itself still exists in My Files. Previous messages in the chat are preserved.
result: [pending]

### 14. Navigate to My Files screen
expected: Click "My Files" in the left sidebar. A new screen loads showing all your uploaded files in a table with columns for name, size, type, and upload date. The table supports sorting and searching.
result: [pending]

### 15. Upload a file from My Files screen
expected: On the My Files screen, drag-and-drop a file onto the page or use the upload button. An upload dialog opens, the file uploads, and after AI profiling completes, it appears in the file list.
result: [pending]

### 16. File actions from My Files — download and context
expected: In the My Files table, click a file's download action — the file downloads to your computer with its original filename. Click the context/info action — a modal shows the AI-generated data summary, columns, and row count.
result: [pending]

### 17. Start new chat from My Files
expected: In the My Files table, click the "Start Chat" action on a file. A new chat session is created with that file already linked. You're navigated to the new session with the welcome screen.
result: [pending]

### 18. Bulk delete files from My Files
expected: In the My Files table, select multiple files using checkboxes. A bulk delete option appears. Click it, confirm the dialog. Selected files are deleted. They are removed from any linked sessions (but session messages are preserved).
result: [pending]

### 19. Drag-and-drop file onto chat area
expected: Drag a file from your desktop/finder onto the chat area. A visual drop overlay appears. Drop the file — an upload dialog opens. After upload completes, the file is automatically linked to the current session and appears in the right panel.
result: [pending]

### 20. Delete a session from sidebar
expected: Right-click or use the delete option on a session in the sidebar. A confirmation dialog appears. Confirm deletion. The session disappears from the sidebar. If it was the active session, you're redirected to the dashboard/home.
result: [pending]

### 21. Dark/light theme toggle
expected: Click your user profile in the sidebar bottom. A dropdown appears with a theme toggle item showing a Moon/Sun icon. Click it — the entire UI switches between dark and light mode. All components adapt (sidebar, chat, modals, inputs, toasts).
result: [pending]

### 22. Theme persists after refresh
expected: After toggling to a specific theme (e.g. dark mode), refresh the page (Cmd+R). The theme stays on dark mode — no flash of light mode during load. The theme preference survived the refresh.
result: [pending]

### 23. Session persistence across browser sessions
expected: Send some messages in a chat session with linked files. Close the browser tab completely. Open the app again and log in. Navigate to the same session in the sidebar. All messages are there with full conversation history. Linked files are still linked.
result: [pending]

### 24. Multiple independent sessions
expected: Create 2-3 different chat sessions, each with different files linked and different conversations. Switch between them using the sidebar. Each session shows its own messages, its own linked files, and maintains its own conversation context independently.
result: [pending]

### 25. Sidebar collapse to icon mode
expected: Click the collapse control on the left sidebar. The sidebar collapses to a narrow icon-only mode. Click again to expand. The sidebar state is toggled smoothly.
result: [pending]

## Summary

total: 25
passed: 0
issues: 1
pending: 24
skipped: 0

## Gaps

- truth: "Sessions are only created intentionally, not on every page load"
  status: failed
  reason: "User reported: every page load auto-creates a new empty session, causing 'New Chat' entries to pile up in sidebar. Sessions should only be created when user sends first message, not on load."
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
