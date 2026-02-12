---
status: investigating
trigger: "Right sidebar does not auto-open when linking a file on a NEW session (from the Welcome Screen). It works correctly on existing sessions."
created: 2026-02-12T10:00:00Z
updated: 2026-02-12T10:30:00Z
---

## Current Focus

hypothesis: The pre-session file-linking flow on WelcomeScreen (no sessionId) never calls setRightPanelOpen(true), and the LinkedFilesPanel cannot render anyway because currentSessionId is null. Post-navigation, Zustand's in-memory state may lose the rightPanelOpen=true set before router.replace.
test: Trace full state lifecycle from WelcomeScreen setRightPanelOpen(true) through router.replace to SessionPage mount
expecting: Confirm whether rightPanelOpen=true survives navigation or gets lost
next_action: Report root cause with two dimensions

## Symptoms

expected: When user links a file to a new session (from Welcome Screen), the right sidebar panel should automatically open to show the linked file — both immediately upon linking and after session creation/navigation.
actual: File links successfully (shown as chip or toast), but right sidebar stays hidden (w-0). User must manually click the PanelRightOpen button in the header after the session page loads.
errors: None — no runtime errors or console warnings.
reproduction: 1. Click "New Chat" in sidebar -> /sessions/new loads WelcomeScreen. 2. Link a file (via paperclip or drag-drop). 3. Sidebar does NOT open. 4. Send a message -> session created, navigates to /sessions/{id}. 5. Sidebar STILL does not open. 6. On an existing session (/sessions/{id} with ChatInterface), linking a file via paperclip DOES open sidebar.
started: After Plan 19-04 fix added setRightPanelOpen(true) to all 6 linkFileAsync call sites — but the pre-session pending-file flow was missed.

## Eliminated

(none — root cause identified on first pass through evidence)

## Evidence

- timestamp: 2026-02-12T10:05:00Z
  checked: WelcomeScreen.tsx — all file-linking paths when sessionId is undefined
  found: |
    When sessionId is undefined (i.e. /sessions/new):
    - PendingFilePicker.onRecentFileClick -> handlePendingFileSelect (line 138-144): Adds to pendingFileIds local state. NO setRightPanelOpen(true).
    - handleUploadComplete (line 155-173): Adds to pendingFileIds. NO setRightPanelOpen(true).
    - handleDragUploadComplete else-branch (line 197-205): Adds to pendingFileIds. NO setRightPanelOpen(true).
    Only the if-branch (sessionId exists, line 187-196) calls setRightPanelOpen(true) after linkFileAsync.
  implication: Pre-session file linking never signals the sidebar to open. But this is moot because LinkedFilesPanel cannot render without currentSessionId.

- timestamp: 2026-02-12T10:08:00Z
  checked: Dashboard layout.tsx (line 56-61) — LinkedFilesPanel rendering condition
  found: |
    {currentSessionId && (
      <LinkedFilesPanel sessionId={currentSessionId} files={sessionDetail?.files ?? []} />
    )}
    LinkedFilesPanel only renders when currentSessionId is truthy.
    At /sessions/new, no component calls setCurrentSession(), so currentSessionId remains null.
  implication: Even if setRightPanelOpen(true) were called during pending file linking, the panel physically cannot render. This is a structural constraint, not a bug in the file-linking code.

- timestamp: 2026-02-12T10:12:00Z
  checked: WelcomeScreen.tsx handleSend — the !sessionId branch (lines 211-244)
  found: |
    Flow: createSession -> linkFileAsync (for each pending file) -> setRightPanelOpen(true) [line 231] -> router.replace(/sessions/{newId}) [line 238].
    setRightPanelOpen(true) IS called before navigation.
    Zustand store update is synchronous (no async middleware, no persist).
  implication: The store value rightPanelOpen=true is set before router.replace fires. Question is whether it survives navigation.

- timestamp: 2026-02-12T10:15:00Z
  checked: sessionStore.ts — persistence and reset mechanisms
  found: |
    Store is pure in-memory Zustand (no persist middleware, no sessionStorage/localStorage).
    rightPanelOpen defaults to false (line 36).
    Only two places set rightPanelOpen to false: initial state and LinkedFilesPanel close button.
    No reset on session change, navigation, or any lifecycle event.
  implication: The store SHOULD retain rightPanelOpen=true across client-side navigation. But if the navigation triggers a full page reload or module re-evaluation, the store would reinitialize with rightPanelOpen=false.

- timestamp: 2026-02-12T10:18:00Z
  checked: SessionPage.tsx (/sessions/[sessionId]/page.tsx) — mount sequence
  found: |
    1. Mounts, starts loading session detail and messages
    2. useEffect calls setCurrentSession(sessionId) -> layout now renders LinkedFilesPanel
    3. While loading: shows Spinner (no WelcomeScreen or ChatInterface)
    4. After load: if no messages, shows WelcomeScreen(sessionId)
    5. WelcomeScreen useEffect detects pending message -> adds local message -> SessionPage re-renders -> shows ChatInterface
    Cleanup: setCurrentSession(null) on unmount.
  implication: There's a brief loading phase where Spinner is shown. LinkedFilesPanel should render during this phase (currentSessionId is set in useEffect). If rightPanelOpen=true survived navigation, panel opens. If not, panel stays closed.

- timestamp: 2026-02-12T10:22:00Z
  checked: Next.js App Router behavior with router.replace for client-side navigation
  found: |
    router.replace() in Next.js App Router performs soft (client-side) navigation.
    Shared layouts stay mounted. Module-level singletons (like Zustand store) persist.
    HOWEVER: The key concern is that between setRightPanelOpen(true) and the destination page mounting, there is an async gap. React 18's automatic batching could potentially delay the Zustand subscription update until after the navigation triggers a re-render cycle.
    More importantly: The navigation from /sessions/new to /sessions/{id} causes SessionPage to mount. Its useEffect is async (runs after paint). So the sequence is:
    a) router.replace fires
    b) Layout re-renders with new children (SessionPage)
    c) SessionPage renders (loading state initially)
    d) useEffect fires: setCurrentSession(sessionId)
    e) Layout re-renders, LinkedFilesPanel renders
    f) LinkedFilesPanel reads rightPanelOpen from store
    At step (f), rightPanelOpen SHOULD be true (set before step a).
  implication: Theoretically works. But real-world React batching and Next.js navigation lifecycle may introduce subtle timing. The safest fix is to not rely on Zustand in-memory state surviving navigation, but instead use sessionStorage (like spectra_pending_message already does).

- timestamp: 2026-02-12T10:25:00Z
  checked: All 6 linkFileAsync call sites for setRightPanelOpen(true)
  found: |
    1. WelcomeScreen.tsx line 190-193 (handleDragUploadComplete, sessionId branch): HAS setRightPanelOpen(true)
    2. WelcomeScreen.tsx line 231 (handleSend, !sessionId branch): HAS setRightPanelOpen(true)
    3. ChatInterface.tsx line 113 (handleDragUploadComplete): HAS setRightPanelOpen(true)
    4. FileLinkingDropdown.tsx line 82 (handleUploadComplete): HAS setRightPanelOpen(true)
    5. FileLinkingDropdown.tsx line 97 (handleFileSelected): HAS setRightPanelOpen(true)
    6. FileLinkingDropdown.tsx line 110 (handleRecentFileClick): HAS setRightPanelOpen(true)
    All 6 API-based linkFile call sites DO have the fix from Plan 19-04.
  implication: The Plan 19-04 fix is complete for all API-based linking. The gap is the pre-session LOCAL-ONLY linking (pendingFileIds) which never calls linkFileAsync and therefore never triggers setRightPanelOpen(true). But the real issue is that even handleSend's setRightPanelOpen(true) before router.replace may not survive navigation reliably.

## Resolution

root_cause: |
  TWO interrelated issues prevent the right sidebar from auto-opening on new sessions:

  **Issue 1 — No setRightPanelOpen(true) in pre-session file linking paths:**
  On /sessions/new, WelcomeScreen renders without a sessionId. File linking goes through
  PendingFilePicker -> handlePendingFileSelect (or handleUploadComplete / handleDragUploadComplete
  else-branch), which only adds to local pendingFileIds state. None of these paths call
  setRightPanelOpen(true). This is partly by design — LinkedFilesPanel only renders when
  currentSessionId is set in the dashboard layout (layout.tsx line 56), and at /sessions/new
  currentSessionId is null, so the panel cannot appear regardless.

  **Issue 2 — Zustand in-memory state may not survive navigation reliably:**
  When handleSend creates the session, it calls setRightPanelOpen(true) (line 231) BEFORE
  router.replace (line 238). In theory, this Zustand update should persist across the
  client-side navigation. But the store has no persistence middleware (no sessionStorage
  backup). If React's navigation lifecycle causes the Zustand subscription to miss the
  update, or if the navigation triggers any full re-render that re-evaluates the store
  module, rightPanelOpen would reset to its default (false).

  The pattern already used for message handoff (spectra_pending_message in sessionStorage)
  should be applied here: store a "pending_sidebar_open" flag in sessionStorage alongside
  the pending message, and have SessionPage (or ChatInterface) read it on mount.

  FILES INVOLVED:
  - /frontend/src/components/session/WelcomeScreen.tsx (line 231): setRightPanelOpen(true) in handleSend may not survive router.replace
  - /frontend/src/stores/sessionStore.ts (line 36): rightPanelOpen defaults to false, no persistence
  - /frontend/src/app/(dashboard)/layout.tsx (line 56-60): LinkedFilesPanel only renders when currentSessionId is set
  - /frontend/src/app/(dashboard)/sessions/[sessionId]/page.tsx (line 29-35): setCurrentSession runs in useEffect after mount

fix: |
  Recommended approach (parallels existing spectra_pending_message pattern):

  1. In WelcomeScreen.handleSend (!sessionId branch), add sessionStorage flag:
     sessionStorage.setItem("spectra_pending_sidebar_open", "1");
     (Keep the existing setRightPanelOpen(true) as a belt-and-suspenders measure.)

  2. In SessionPage or ChatInterface mount effect, check for the flag:
     useEffect(() => {
       const pendingSidebar = sessionStorage.getItem("spectra_pending_sidebar_open");
       if (pendingSidebar) {
         sessionStorage.removeItem("spectra_pending_sidebar_open");
         setRightPanelOpen(true);
       }
     }, []);

  This ensures the sidebar opens reliably after navigation, regardless of Zustand timing.

  Alternative: Add Zustand persist middleware to sessionStore for rightPanelOpen. This is
  heavier but provides general-purpose state persistence across navigations.

verification: N/A (diagnosis only)

files_changed: []
