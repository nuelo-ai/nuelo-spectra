---
status: diagnosed
phase: 06-frontend-ui-interactive-data-cards
source:
  - All Phase 6 SUMMARY files (06-01 through 06-19)
  - Streaming display fix (refetchQueries)
  - Cursor bug fix (ChatInterface conditional rendering)
started: 2026-02-05T00:00:00Z
updated: 2026-02-05T00:25:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Authentication and Dashboard Access
expected: Navigate to http://localhost:3000. You should see a login page with modern gradient styling. Log in with your email and password. Dashboard loads showing file sidebar on left, empty state in center prompting "No files yet - upload to get started", and top navigation with user avatar/menu.
result: pass

### 2. File Upload with Progress States
expected: Click "+ Upload File" button in sidebar or drag/drop a CSV/Excel file. Progress bar appears showing: "Uploading..." (0-90%), then "Analyzing..." (90-100%), then "Ready" (100%). Progress transitions are smooth with visual feedback.
result: pass

### 3. Analysis Display in Upload Dialog
expected: When upload reaches "Ready" state, analysis text displays as formatted markdown in the dialog. Tables, bold text, and lists render properly. Analysis area is scrollable if content is long. Dialog is wide (~896px) and comfortable to read.
result: pass

### 4. Continue to Chat Button
expected: "Continue to Chat" button is visible at bottom of upload dialog when ready. Click button → dialog closes smoothly, file tab opens automatically, sidebar shows uploaded file within 1-2 seconds (name, size, date visible).
result: pass

### 5. File Sidebar Population
expected: After clicking "Continue to Chat", sidebar updates within 1-2 seconds showing the uploaded file with metadata. No long delays (5+ seconds), no need to refresh page. File appears automatically.
result: pass

### 6. File Info Modal
expected: Click info icon (i) next to file in sidebar. Modal opens wide (~896px) showing data_summary as formatted markdown. Can scroll if analysis is long. Modal is comfortable to read.
result: pass

### 7. File Deletion
expected: Click trash icon next to file in sidebar. Confirmation dialog appears asking "Are you sure?". Click Delete → file removed from sidebar immediately, associated tab closes if it was open.
result: pass

### 8. Chat Query - Streaming Behavior
expected: Select a file tab. Type simple query like "What are the column names?" and press Enter. Typing indicator (three dots) appears. Status updates show at bottom ("Generating code...", "Validating code...", "Executing code..."). Text streams in smoothly character by character. NO phantom cursor character ("|") appears before text. Response completes without errors.
result: issue
reported: "three dots appears but status updates not showing at the bottom. Only showing static 'analyzing result' text"
severity: minor

### 9. Message Immediate Display
expected: After streaming completes, message appears in chat immediately with no page refresh needed. Message stays visible and readable. Data Card renders if query returned structured data.
result: pass

### 10. Data Card Display
expected: After AI completes analysis query, Data Card appears with four sections: Query Brief header at top, collapsible Python code section, interactive sortable/filterable data table, AI explanation at bottom. Each section is clearly separated and styled.
result: issue
reported: "it does show, however, how the presentation of the table is not consistent. It sometimes display a table with a nice scrollable and button to download, and sometimes it only shows simple markdown table that is static. This needs to be set consistently using the table that can be downloaded"
severity: major

### 11. Data Table Interactions
expected: Click column headers in data table to sort ascending/descending. Use search box to filter rows. Click pagination controls to navigate pages (10 rows per page). All interactions work smoothly without page reload.
result: pass

### 12. Code Display Toggle
expected: Python code section in Data Card starts collapsed. Click "View Code" button → code expands with syntax highlighting and line numbers. Click "Hide Code" → code collapses. Toggle works smoothly.
result: pass

### 13. CSV Download
expected: Click "Download CSV" button below data table. Browser downloads CSV file with descriptive filename (slugified query, not generic timestamp). File contains all table data with proper formatting.
result: pass

### 14. Markdown Download
expected: Click "Download Markdown" button below explanation. Browser downloads .md file containing formatted report: query brief, data table in markdown format, and AI explanation. File is readable and well-structured.
result: pass

### 15. Card Collapse/Expand
expected: Click Data Card header to collapse the card. Content hides, only header visible. Click header again → card expands showing full content. When new query completes, previous cards auto-collapse to reduce clutter.
result: pass

### 16. Settings - Profile Update
expected: Click user avatar/menu in top-right → Settings. Profile section shows current first name, last name, email. Edit first/last name fields, click Save. Success message appears. Return to dashboard → top navigation immediately shows new name without page refresh.
result: pass

### 17. Settings - Password Change
expected: In Settings page, scroll to Security section. Enter current password, new password (minimum 8 characters), confirm new password. If passwords don't match, see inline error. If current password wrong, see error after submit. On success, see success message.
result: pass

### 18. Multi-Tab File Management
expected: Upload 2-3 files. Each file gets its own tab in horizontal tab bar. Click between tabs → chat history switches correctly. Each tab maintains independent chat history. Close tab with X button → tab disappears, sidebar file remains. Tab limit is 5 maximum.
result: pass

### 19. Visual Polish and Animations
expected: Throughout the app: smooth fade-in animations on messages, slide-up on Data Cards, gradient backgrounds on user messages, loading skeletons while fetching data, hover effects on interactive elements. App feels modern and polished, not janky or abrupt.
result: pass

### 20. Error Handling
expected: Trigger an error (e.g., very complex query that fails). Error message displays clearly with red styling and error icon. User can still interact with chat, send new query. Failed query doesn't break the interface.
result: skipped
reason: can't simulate error

## Summary

total: 20
passed: 18
issues: 2
pending: 0
skipped: 1

## Gaps

- truth: "Status updates show at bottom (\"Generating code...\", \"Validating code...\", \"Executing code...\") during streaming"
  status: failed
  reason: "User reported: three dots appears but status updates not showing at the bottom. Only showing static 'analyzing result' text"
  severity: minor
  test: 8
  root_cause: "Backend emits status events with nested structure {type: 'status', event: 'coding_started'} but frontend expects flat structure {type: 'coding_started'}. Frontend switch statement checks event.type directly, which never matches when type='status'."
  artifacts:
    - path: "backend/app/agents/coding.py"
      issue: "lines 104-118: emits {type: 'status', event: 'coding_started'}"
    - path: "backend/app/agents/graph.py"
      issue: "lines 80-86, 284-290: emits {type: 'status', event: 'validation_started'} and {type: 'status', event: 'execution_started'}"
    - path: "backend/app/agents/data_analysis.py"
      issue: "lines 60-66: emits {type: 'status', event: 'analysis_started'}"
    - path: "frontend/src/hooks/useSSEStream.ts"
      issue: "lines 117-123: expects flat structure, checks event.type directly"
  missing:
    - "Change backend agents to emit flat structure {type: 'coding_started', message: '...'}"
    - "Remove nested event field from all 4 backend agent status emissions"
  debug_session: ".planning/debug/status-updates-not-showing.md"

- truth: "Data Card always displays interactive sortable/filterable table with download capability"
  status: failed
  reason: "User reported: it does show, however, how the presentation of the table is not consistent. It sometimes display a table with a nice scrollable and button to download, and sometimes it only shows simple markdown table that is static. This needs to be set consistently using the table that can be downloaded"
  severity: major
  test: 10
  root_cause: "ChatMessage parseExecutionResult only recognizes array-of-objects or {columns, rows} formats, but fails when pandas df.to_dict() uses default format {column: {index: value}} without 'columns' key, or when result is empty array, causing inconsistent rendering."
  artifacts:
    - path: "frontend/src/components/chat/ChatMessage.tsx"
      issue: "lines 45-91: parseExecutionResult missing df.to_dict() default format handler and empty array handler"
    - path: "frontend/src/components/chat/ChatMessage.tsx"
      issue: "lines 53-60: strict validation rejects empty arrays instead of showing empty table"
    - path: "frontend/src/components/chat/DataCard.tsx"
      issue: "lines 52-75: dead code parseTableData never called due to line 75 logic error"
    - path: "backend/app/config/prompts.yaml"
      issue: "lines 18-43: coding agent prompt doesn't specify DataFrame conversion format"
  missing:
    - "Update parseExecutionResult to handle df.to_dict() default format {col: {idx: val}}"
    - "Update parseExecutionResult to handle empty arrays by returning {columns: [], rows: []}"
    - "Fix or remove DataCard parseTableData dead code at line 75"
    - "Update coding prompt to instruct .to_dict('records') for consistent format"
  debug_session: ".planning/debug/data-card-table-inconsistent.md"
