---
status: investigating
trigger: "Investigate TWO related drag-and-drop / upload issues: My Files drag-drop redundant dialog (Test 15) and Chat area drag-drop broken (Test 19)"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:00:00Z
---

## Current Focus

hypothesis: Both issues share the same root cause — the drop handler discards the actual dropped file and just opens an empty FileUploadZone dialog, forcing the user to drag/drop again
test: Read MyFilesPage.onDrop and ChatInterface.onDrop to confirm they ignore acceptedFiles
expecting: Both onDrop callbacks call setDialogOpen(true) without passing the file to FileUploadZone
next_action: Trace full flow from drop to FileUploadZone

## Symptoms

expected_issue1: Drag file to My Files upload area -> file uploads directly
actual_issue1: Dragging to upload area opens ANOTHER dialog asking to upload — redundant
expected_issue2: Drag file to chat area -> overlay appears -> drop triggers upload -> auto-links
actual_issue2_new_session: No drop overlay, file gets downloaded to Downloads folder instead
actual_issue2_existing_session: Overlay appears but then opens redundant upload dialog (must drag file again into that dialog)
reproduction: Drag any CSV/Excel file to My Files zone or Chat area
started: Current behavior since implementation

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-02-12T00:01:00Z
  checked: MyFilesPage onDrop handler (my-files/page.tsx lines 29-44)
  found: onDrop callback IGNORES acceptedFiles parameter completely — just calls setUploadDialogOpen(true). The dropped file is thrown away.
  implication: This is root cause of Issue 1. User drops file -> file is consumed by outer dropzone -> dialog opens with empty FileUploadZone -> user must drag/drop AGAIN into the dialog.

- timestamp: 2026-02-12T00:02:00Z
  checked: ChatInterface onDrop handler (ChatInterface.tsx lines 67-75)
  found: onDrop callback also IGNORES acceptedFiles parameter — just snapshots fileIds and calls setShowUploadDialog(true). Dropped file is discarded.
  implication: This is root cause of Issue 2 on existing sessions. Same pattern as Issue 1 — file consumed, dialog opens empty.

- timestamp: 2026-02-12T00:03:00Z
  checked: WelcomeScreen (new session page) for drag-drop handling
  found: WelcomeScreen has NO useDropzone / drag-drop handling at all. No getRootProps, no onDragOver, no drop zone.
  implication: This is root cause of Issue 2 on new sessions. Without any drag-drop handler, the browser's DEFAULT behavior applies — downloading the file.

- timestamp: 2026-02-12T00:04:00Z
  checked: FileUploadZone component (FileUploadZone.tsx)
  found: FileUploadZone has its OWN useDropzone with onDrop that properly handles files. But it receives NO prop to accept pre-dropped files. It only handles files dropped directly onto it or selected via click.
  implication: FileUploadZone cannot accept files forwarded from parent components. Missing a `initialFiles` or `droppedFiles` prop.

## Resolution

root_cause: |
  THREE distinct but related problems, all stemming from the same architectural gap:

  1. **MyFilesPage (Issue 1):** The page has its own useDropzone that catches the drop event, but its
     onDrop callback (line 30) discards the dropped file and merely calls setUploadDialogOpen(true).
     The dialog then renders FileUploadZone which has its OWN dropzone — but the file is already gone.
     User must re-drop into the inner zone.

  2. **ChatInterface (Issue 2, existing session):** Same pattern — onDrop (line 67-75) discards
     acceptedFiles and opens an empty dialog containing FileUploadZone.

  3. **WelcomeScreen (Issue 2, new session):** Has NO drag-drop handler at all. When user drags a file
     over the new-session page, the browser's default behavior kicks in (downloading the file).

  Root architectural gap: FileUploadZone has no mechanism to receive pre-dropped files from a parent.
  All parent components discard the actual File object and just open the dialog.

fix: (pending)
verification: (pending)
files_changed: []
