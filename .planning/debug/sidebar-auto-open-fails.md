---
status: diagnosed
trigger: "Right sidebar does not auto-open when file is linked to session (post-fix re-UAT)"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:00:00Z
---

## Current Focus

hypothesis: Fix commit cae5f9a added setRightPanelOpen(true) to FileLinkingDropdown and ChatInterface but missed WelcomeScreen linkFileAsync calls
test: Audit all linkFile/linkFileAsync call sites for setRightPanelOpen(true)
expecting: WelcomeScreen call sites are uncovered
next_action: Report root cause

## Symptoms

expected: When user links a file to a session via any method, the right sidebar should auto-open
actual: Right sidebar stays closed after file link (re-UAT test 11 still fails after fix commit cae5f9a)
errors: None reported
reproduction: Test 11 in 19-UAT.md -- link a file via any method, sidebar does not open
started: Fix commit cae5f9a added setRightPanelOpen(true) to 4 handlers but missed 2 others in WelcomeScreen

## Eliminated

- sessionStore correctness: Verified. setRightPanelOpen(open) correctly sets rightPanelOpen in store (line 50-52). Store is a singleton Zustand store, no duplication risk.
- LinkedFilesPanel correctness: Verified. Reads rightPanelOpen from store (line 21), applies w-80 when true, w-0 when false (line 27). Close button calls setRightPanelOpen(false) -- only place it's reset to false besides initial state.
- Layout rendering: Verified. LinkedFilesPanel is rendered in layout.tsx when currentSessionId is truthy (line 56-60). SessionPage sets currentSessionId on mount.
- Store reset / timing: Verified. No code resets rightPanelOpen to false other than close button and initial state. Query invalidation from useLinkFile onSuccess does not reset Zustand state.
- Module duplication: Verified. All 7 imports use identical path @/stores/sessionStore. No webpack config that would cause duplication.
- CSS issue: Verified. transition-all duration-300 with w-80/w-0 toggle is correct approach.

## Evidence

- timestamp: 2026-02-12T00:00:00Z
  checked: All linkFile/linkFileAsync call sites across entire frontend (6 total)
  found: |
    COVERED (have setRightPanelOpen(true) in onSuccess):
    1. FileLinkingDropdown.tsx:77 -- handleUploadComplete
    2. FileLinkingDropdown.tsx:92 -- handleFileSelected
    3. FileLinkingDropdown.tsx:105 -- handleRecentFileClick
    4. ChatInterface.tsx:106 -- handleDragUploadComplete

    UNCOVERED (NO setRightPanelOpen(true)):
    5. WelcomeScreen.tsx:188 -- handleDragUploadComplete (drag-drop with existing sessionId)
    6. WelcomeScreen.tsx:222 -- handleSend session creation (links pending files before navigation)
  implication: Two file-linking flows in WelcomeScreen never open the sidebar.

- timestamp: 2026-02-12T00:00:00Z
  checked: WelcomeScreen.tsx handleDragUploadComplete (lines 173-202)
  found: When sessionId exists, drag-drop upload calls linkFileAsync().then(() => toast.success(...)) at line 188-190. No setRightPanelOpen(true) in the .then() chain.
  implication: Drag-drop file linking on WelcomeScreen (with existing session) does not open sidebar.

- timestamp: 2026-02-12T00:00:00Z
  checked: WelcomeScreen.tsx handleSend session creation flow (lines 204-237)
  found: At line 222, linkFileAsync is called to link pending files during session creation. No setRightPanelOpen(true) is called before or after. After linking, navigation occurs (line 230), and the new session page loads with rightPanelOpen=false.
  implication: The most common new-user flow (New Chat -> add files -> send message -> session created -> navigate) never sets rightPanelOpen=true. User arrives at session page with sidebar closed.

- timestamp: 2026-02-12T00:00:00Z
  checked: Whether the covered paths (FileLinkingDropdown) are actually reachable during the test
  found: FileLinkingDropdown is rendered in WelcomeScreen only when sessionId exists (line 348-351). On /sessions/new (NewSessionPage), sessionId is undefined, so PendingFilePicker is used instead. PendingFilePicker stores files in local state and never calls linkFile API or setRightPanelOpen.
  implication: On /sessions/new, ALL file-linking goes through PendingFilePicker (no sidebar auto-open). Files are linked via API only in handleSend, which also has no setRightPanelOpen.

- timestamp: 2026-02-12T00:00:00Z
  checked: Fix commit cae5f9a scope
  found: Commit only modified FileLinkingDropdown.tsx and ChatInterface.tsx. Did not modify WelcomeScreen.tsx. WelcomeScreen has its own independent linkFileAsync calls that were not covered by the fix.
  implication: Fix was incomplete -- addressed 4 of 6 call sites but missed the 2 in WelcomeScreen.

## Resolution

root_cause: |
  Fix commit cae5f9a added setRightPanelOpen(true) to FileLinkingDropdown (3 handlers) and ChatInterface (1 handler), but missed two linkFileAsync call sites in WelcomeScreen.tsx:

  1. WelcomeScreen.tsx:188 -- handleDragUploadComplete: When an existing session has drag-drop file upload, linkFileAsync is called with only a toast in .then(), no setRightPanelOpen(true).

  2. WelcomeScreen.tsx:222 -- handleSend session creation: When user starts from /sessions/new, adds files via PendingFilePicker, then sends first message, files are linked via linkFileAsync during session creation. No setRightPanelOpen(true) is called. After navigation to the new session page, rightPanelOpen remains false.

  The most common new-user flow (New Chat -> add file -> send message) always goes through path #2, so the sidebar NEVER auto-opens on first file link for new sessions. The fix only works for users who are already on an existing session (ChatInterface or WelcomeScreen with sessionId) and use the FileLinkingDropdown paperclip button.

fix: Add setRightPanelOpen(true) to both WelcomeScreen linkFileAsync call sites. For path #2 (session creation), call setRightPanelOpen(true) before navigation so the panel is open when the new session page loads.

verification: N/A (diagnosis only)

files_changed: []
