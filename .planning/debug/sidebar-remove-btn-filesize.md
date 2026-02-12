---
status: diagnosed
trigger: "Investigate why the remove button is not shown on files in the right sidebar panel when there are more than 1 file linked to a session. Also investigate why file size is not displayed."
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:01:00Z
---

## Current Focus

hypothesis: Two bugs — (1) remove button logic is CORRECT in code (user report may describe symptom inaccurately, or there is a subtle Radix/disabled interaction), (2) file_size is missing from 3 layers of the stack
test: Full code review of FileCard, LinkedFilesPanel, backend schema, frontend type, Button component, AlertDialog component
expecting: Confirm root causes for both issues
next_action: Report final diagnosis

## Symptoms

expected: Each file in the right sidebar shows name, size, and action buttons (info, remove) on hover — even when multiple files are linked.
actual: With 1 file — actions show. With >1 file — remove button disappears. Also no file size shown, only name and type.
errors: None (UI logic bug, not runtime error)
reproduction: Link 2+ files to a session, open right panel, hover over file cards
started: Since implementation

## Eliminated

- hypothesis: "isLastFile prop is computed incorrectly in LinkedFilesPanel"
  evidence: LinkedFilesPanel.tsx line 74 passes `isLastFile={files.length === 1}` which is semantically correct — true when 1 file, false when >1
  timestamp: 2026-02-12

- hypothesis: "Remove button is conditionally rendered (hidden from DOM) based on file count"
  evidence: FileCard.tsx lines 92-103 — the remove button (AlertDialog + Button with X icon) is rendered unconditionally. There is NO `{!isLastFile && ...}` or `{files.length > 1 && ...}` conditional. The only dynamic prop is `disabled={isLastFile}` on line 98.
  timestamp: 2026-02-12

- hypothesis: "CSS group-hover breaks with multiple FileCard instances"
  evidence: Each FileCard has its own `group` class on its root div (line 62). The `group-hover:opacity-100` on line 79 targets the nearest ancestor with `group`. Multiple cards each have their own independent group scope. This is standard Tailwind and works correctly with multiple instances.
  timestamp: 2026-02-12

- hypothesis: "AlertDialogTrigger with asChild causes invisible rendering when button is enabled"
  evidence: AlertDialogTrigger (Radix) with asChild passes trigger props to child. Button component uses Slot when asChild, but here asChild is on AlertDialogTrigger (not Button). The Button renders as a normal `<button>` element. No evidence that enabled state causes rendering issues.
  timestamp: 2026-02-12

- hypothesis: "Fragment wrapper in FileCard breaks space-y-2 layout causing hover issues"
  evidence: FileCard returns `<>...<Dialog>...</Dialog></>`. The Dialog component renders a portal when open and minimal DOM when closed. The `space-y-2` parent may add margin to the Dialog wrapper, but this would be a spacing issue, not a visibility issue for the hover buttons.
  timestamp: 2026-02-12

## Evidence

- timestamp: 2026-02-12
  checked: LinkedFilesPanel.tsx line 74
  found: `isLastFile={files.length === 1}` — semantically correct computation
  implication: When 1 file, isLastFile=true (disable remove). When >1 files, isLastFile=false (enable remove). Logic is correct.

- timestamp: 2026-02-12
  checked: FileCard.tsx lines 78-125 — full action buttons section
  found: Both Info button (lines 81-89) and Remove button (lines 92-124) are inside the SAME div (line 79) that has `opacity-0 group-hover:opacity-100`. Neither button has any additional conditional rendering. The only difference is `disabled={isLastFile}` on the remove Button.
  implication: Both buttons should always appear/disappear together on hover. It is impossible for only the remove button to be hidden while the info button shows, based on this code alone.

- timestamp: 2026-02-12
  checked: Button component (button.tsx) — disabled styles
  found: Base variants include `disabled:pointer-events-none disabled:opacity-50`. When disabled=true, button gets 50% opacity and no pointer events. When disabled=false, button is fully opaque and interactive.
  implication: A disabled button is VISIBLE (at 50% opacity), not hidden. An enabled button is MORE visible. The disabled state cannot cause the button to disappear.

- timestamp: 2026-02-12
  checked: Backend FileBasicInfo schema (chat_session.py lines 27-35)
  found: Schema only includes: id, original_filename, file_type, created_at. No file_size field.
  implication: API response for session detail does not include file_size for linked files.

- timestamp: 2026-02-12
  checked: Backend File model (models/file.py line 32)
  found: `file_size: Mapped[int] = mapped_column(BigInteger)` — the field EXISTS on the database model
  implication: The data is in the database but the serialization schema omits it.

- timestamp: 2026-02-12
  checked: Frontend FileBasicInfo type (types/session.ts lines 6-11)
  found: Type only includes: id, original_filename, file_type, created_at. No file_size field.
  implication: Frontend type mirrors backend schema — both missing file_size.

- timestamp: 2026-02-12
  checked: FileCard.tsx lines 69-76 — file info display
  found: Only renders `file.file_type?.toUpperCase() || "File"`. No file_size display exists.
  implication: Even if the data were available, the UI has no rendering for it.

- timestamp: 2026-02-12
  checked: Frontend file types (types/file.ts)
  found: Other file types like FileListItem and FileUploadResponse DO include file_size. Only FileBasicInfo (used for session-linked files) omits it.
  implication: The omission is specific to the session detail context, not a general oversight.

## Resolution

root_cause: |
  BUG 1 — Remove button with >1 files:
  After exhaustive code review, the remove button rendering logic is CORRECT. The button is unconditionally rendered inside the hover-reveal container (FileCard.tsx line 79). The `disabled={isLastFile}` prop on line 98 correctly disables it when there's 1 file and enables it when there are >1 files. There is NO code path that hides the remove button based on file count.

  POSSIBLE EXPLANATIONS for the user-reported behavior:
  (a) The user may be observing that with 1 file, the remove button shows but is DISABLED (grayed out at 50% opacity, non-clickable due to pointer-events-none). With >1 files, the button is ENABLED and fully functional. The user may have perceived the disabled/grayed state as "showing" and the enabled state differently.
  (b) There may be a browser-specific or Radix version-specific rendering issue not visible in code review.
  (c) The `disabled:pointer-events-none` on the Button when isLastFile=true means the AlertDialog trigger cannot fire. When isLastFile=false, the AlertDialog trigger CAN fire. This is correct behavior but may have caused confusion during testing if the user expected different interaction patterns.

  ACTUAL CODE ISSUE FOUND: The `handleUnlink` function (line 47) has a redundant guard — it checks `isLastFile` and shows a toast, but this code path can never be reached because:
  - When isLastFile=true, the button is disabled with pointer-events-none, so the AlertDialog can never open, so the AlertDialogAction (which calls handleUnlink) can never be clicked.
  - This dead code should be cleaned up.

  BUG 2 — File size not displayed:
  CONFIRMED ROOT CAUSE across 3 layers:
  (a) Backend: FileBasicInfo Pydantic schema (backend/app/schemas/chat_session.py lines 27-35) does NOT include `file_size`, even though the File model has it as `file_size: Mapped[int] = mapped_column(BigInteger)`.
  (b) Frontend type: FileBasicInfo TypeScript type (frontend/src/types/session.ts lines 6-11) does NOT include `file_size`.
  (c) Frontend UI: FileCard component (frontend/src/components/session/FileCard.tsx lines 73-75) has NO rendering for file size — only displays file_type.

fix: Not applied (diagnosis only)
verification: N/A
files_changed: []
