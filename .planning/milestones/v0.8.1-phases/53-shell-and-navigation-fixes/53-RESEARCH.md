# Phase 53: Shell & Navigation Fixes - Research

**Researched:** 2026-03-10
**Domain:** Next.js app shell, shadcn/ui Sidebar, React component layout
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LBAR-01 | Leftbar collapse toggle is visible when Pulse Analysis is selected (positioned at top left of main screen next to the leftbar) | WorkspacePage (`/workspace/page.tsx`) renders no top-bar header at all — no `SidebarTrigger` present. The toggle must be added to the workspace page header. |
| LBAR-02 | Menu items (Pulse Analysis, Chat, Files, Admin Panel) have correct left padding aligned with other icons | `UnifiedSidebar.tsx` `SidebarMenuButton` items render without explicit `pl-*` class; padding is controlled by shadcn defaults. Needs inspection when collapsed vs expanded. |
| CHAT-01 | Spectra logo is not shown in the top left of the Chat main panel when Chat section is selected | `WelcomeScreen.tsx` (rendered by `/sessions/new` and sessions with no messages) shows a hardcoded Spectra logo block (lines 305-313). Must be removed or conditioned out. |
| CHAT-02 | Chat dashboard (new chat) rightbar expand toggle is visible after the rightbar is collapsed (positioned at top right of the chat area) | `WelcomeScreen.tsx` has a `SidebarTrigger` and Spectra logo in its header, but NO rightbar expand toggle button. `LinkedFilesPanel` collapses to `w-0` with no visible trigger remaining. |
| CHAT-03 | Chat screen (existing chat) rightbar collapse/expand toggle is positioned at top right of the chat area (not top middle) | `ChatInterface.tsx` header uses `max-w-3xl mx-auto` centering for the entire header row including the toggle button, centering it rather than pinning it to the right edge. |
| FILES-01 | Spectra logo is not shown in the top left of the Files main panel when Files section is selected | `my-files/page.tsx` (lines 86-91) shows the same Spectra logo block. Must be removed. |
| FILES-02 | Leftbar collapse toggle is in the correct position in Files section (at top of main screen next to leftbar) | `my-files/page.tsx` does include `SidebarTrigger` (line 86), but it's inside a scrollable content area with `px-6 py-8` padding, not at the fixed top of the screen. |
</phase_requirements>

---

## Summary

Phase 53 targets seven cosmetic/layout bugs across the app shell chrome. All bugs are in the frontend (`/frontend/src/`), all purely presentational — no backend changes, no API calls, no state schema changes.

The bugs cluster into three categories:

1. **Missing SidebarTrigger:** WorkspacePage (`/workspace/page.tsx`) has no page header at all — it renders directly into `<div className="p-8 max-w-7xl mx-auto">`. The leftbar collapse toggle (`SidebarTrigger`) exists in `WelcomeScreen`, `ChatInterface`, and `MyFilesPage` headers, but was never added to the workspace collection list page. FILES-02 is a variant: `MyFilesPage` has the trigger but inside a deeply padded scrollable content area, not pinned to the top.

2. **Unwanted Spectra logo:** `WelcomeScreen` and `MyFilesPage` both render a hardcoded logo block (`gradient-primary` div + "Spectra" text). This logo is intentional only in the Chat context when navigating within sessions — but it also appears when Chat is first loaded (`/sessions/new`) and always in My Files. Requirements say it must be removed from both panels.

3. **Chat rightbar toggle position:** Two separate problems:
   - `WelcomeScreen` has no rightbar expand button at all after the rightbar is hidden. The rightbar only appears in `DashboardLayout` when `currentSessionId` is set, and the expand toggle only lives inside `LinkedFilesPanel`'s header (visible only when the panel is open). When the panel is collapsed (`w-0`), the toggle disappears entirely.
   - `ChatInterface` wraps its entire header row (including the rightbar toggle) inside `max-w-3xl mx-auto` centering, which positions the toggle in the middle of the screen width rather than the true right edge.

**Primary recommendation:** Make targeted edits to four files: `WorkspacePage`, `WelcomeScreen`, `MyFilesPage`, and `ChatInterface`. No new components needed; existing primitives (`SidebarTrigger`, `Button`, `PanelRightOpen`) cover all cases.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui Sidebar | project-local (`sidebar.tsx`) | Left sidebar with icon-collapse behavior | Already used; `SidebarTrigger` is the canonical toggle |
| Tailwind CSS | (project-configured) | Layout and positioning | All existing layout uses Tailwind |
| lucide-react | (project dependency) | Icons (`PanelRightOpen`, `PanelRightClose`) | Already imported in `ChatInterface` |
| Zustand (`sessionStore`) | (project dependency) | `rightPanelOpen` / `toggleRightPanel` state | Already used in `ChatInterface` and `LinkedFilesPanel` |

### No new dependencies needed
All building blocks are already present in the codebase. This phase requires only JSX edits and Tailwind class adjustments.

---

## Architecture Patterns

### Current Layout Hierarchy
```
(dashboard)/layout.tsx      — SidebarProvider + UnifiedSidebar + main + LinkedFilesPanel
  /sessions/new/page.tsx    — WelcomeScreen (has logo + SidebarTrigger, no rightbar toggle)
  /sessions/[id]/page.tsx   — WelcomeScreen (no messages) OR ChatInterface (has messages)
    ChatInterface            — has logo + SidebarTrigger + centered rightbar toggle

(workspace)/layout.tsx      — SidebarProvider + UnifiedSidebar + main (NO LinkedFilesPanel)
  /workspace/page.tsx        — NO header at all, no SidebarTrigger

(dashboard)/layout.tsx
  /my-files/page.tsx         — has logo + SidebarTrigger inside scrollable content
```

### Pattern: Page Header Strip
Used by `WelcomeScreen` (lines 305-313) and `ChatInterface` (lines 362-394) and `MyFilesPage` (lines 85-98):
```tsx
// Canonical pattern: sticky top bar, full width, contains SidebarTrigger
<div className="px-4 py-3 border-b bg-background/95 backdrop-blur ...">
  <div className="flex items-center gap-2">
    <SidebarTrigger className="-ml-1" />
    {/* optional: logo, breadcrumb, actions */}
  </div>
</div>
```

`WorkspacePage` currently has no such header strip. It must receive one (a minimal header containing just `SidebarTrigger`) inserted before the `p-8` content div, or the outer `div` must be restructured to `flex flex-col h-full` with a sticky header.

### Pattern: Rightbar Expand Toggle (float-out)
When `LinkedFilesPanel` is collapsed (`w-0`), there is no visible button to re-open it. The correct fix adds a floating/absolute-positioned expand button that appears only when the panel is closed, positioned at the top-right of the chat area:
```tsx
{!rightPanelOpen && (
  <Button
    variant="ghost"
    size="icon"
    className="absolute top-3 right-3 z-10"
    onClick={toggleRightPanel}
    title="Open linked files"
  >
    <PanelRightOpen className="h-4 w-4" />
  </Button>
)}
```
The parent container (`flex flex-col h-full relative`) is already `relative` in both `WelcomeScreen` and `ChatInterface`, so `absolute` positioning works.

### Pattern: Rightbar Toggle — Full-width Right Pin (CHAT-03)
`ChatInterface` header currently:
```tsx
<div className="px-4 py-3 border-b ...">
  <div className="max-w-3xl mx-auto flex items-center justify-between">
    <div>{/* left: SidebarTrigger + logo + title */}</div>
    <div>{/* right: rightbar toggle — appears at max-w-3xl right edge, not screen right edge */}</div>
  </div>
</div>
```
Fix: move the rightbar toggle button OUTSIDE the `max-w-3xl` centered div, or restructure the header to keep left content centered and right toggle pinned to the viewport edge:
```tsx
<div className="px-4 py-3 border-b ... flex items-center">
  {/* Left side, centered content area */}
  <div className="flex-1 max-w-3xl flex items-center gap-2">
    <SidebarTrigger className="-ml-1" />
    {/* logo + title */}
  </div>
  {/* Right side — rightbar toggle, always pinned to right edge */}
  <Button onClick={toggleRightPanel} ...>
    {/* icon */}
  </Button>
</div>
```
This ensures the toggle is visually at the top-right corner regardless of viewport width.

### Anti-Patterns to Avoid
- **Adding the Spectra logo to WorkspacePage:** LBAR-01 only requires a `SidebarTrigger`, not a full logo block. Keep the workspace header minimal.
- **Removing SidebarTrigger from WelcomeScreen when removing the logo:** The requirements remove the logo from the Chat panel header (CHAT-01), NOT the sidebar trigger. Keep `SidebarTrigger` in place; only remove the `<div>` logo block and the `<span>Spectra</span>` text.
- **Adding LinkedFilesPanel to WorkspacePage layout:** WorkspaceLayout intentionally does not have a right panel. Do not add one.
- **Moving the rightbar toggle into LinkedFilesPanel only:** When the panel is collapsed, the panel is `w-0 overflow-hidden` and anything inside it is invisible. The expand trigger for CHAT-02 must live outside `LinkedFilesPanel`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Leftbar collapse toggle | Custom toggle button | `SidebarTrigger` from `@/components/ui/sidebar` | Already wired to `useSidebar().toggleSidebar()` |
| Rightbar open/close state | Local React state | `useSessionStore` (`rightPanelOpen`, `toggleRightPanel`) | Shared across `LinkedFilesPanel` and `ChatInterface`; must be consistent |
| Positioning icons | Custom CSS | Tailwind `absolute`, `relative`, `top-*`, `right-*` | Consistent with existing codebase |

---

## Common Pitfalls

### Pitfall 1: Removing Logo Breaks SidebarTrigger Spacing
**What goes wrong:** The Spectra logo block and SidebarTrigger share the same `flex items-center gap-2` container. Removing the logo div leaves the SidebarTrigger alone — the visual result is fine, but the intent must be checked: the requirements say "no logo," NOT "no header." Verify the trigger remains.

**How to avoid:** After removing the logo `<div>` and `<span>`, keep the outer `<div className="px-4 py-3">` and `<div className="flex items-center gap-2">` with just `<SidebarTrigger />` inside, OR remove the top header bar entirely from `WelcomeScreen` if the sidebar trigger is no longer needed there. Given that CHAT-02 also requires an expand button in the chat area, a minimal header bar containing at least the `SidebarTrigger` should remain.

### Pitfall 2: WorkspacePage Has No `flex flex-col h-full` Wrapper
**What goes wrong:** WorkspacePage renders `<div className="p-8 max-w-7xl mx-auto">` directly. Adding a sticky header requires wrapping in `flex flex-col h-full` with a `shrink-0` header and a scrollable content body.

**How to avoid:** Restructure WorkspacePage outer div:
```tsx
<div className="flex flex-col h-full">
  <div className="px-4 py-3 shrink-0">
    <SidebarTrigger className="-ml-1" />
  </div>
  <div className="flex-1 overflow-y-auto">
    <div className="p-8 max-w-7xl mx-auto">
      {/* existing content */}
    </div>
  </div>
</div>
```
Without `overflow-y-auto` on the inner div, the page may fail to scroll when content overflows.

### Pitfall 3: FILES-02 — SidebarTrigger Already Present, Wrong Position
**What goes wrong:** MyFilesPage already has a `SidebarTrigger` (line 86) but it's inside `<div className="flex-1 overflow-y-auto"><div className="max-w-6xl mx-auto px-6 py-8 space-y-6">` — it scrolls out of view with the page content.

**How to avoid:** Pull the header section (containing `SidebarTrigger`) out of the scrollable `flex-1 overflow-y-auto` wrapper into a fixed `shrink-0` header block at the top of `flex flex-col h-full`. The page already uses `flex flex-col h-full overflow-hidden` as its outer div — just add an inner sticky bar.

### Pitfall 4: CHAT-02 Rightbar Toggle Only Works When Session Exists
**What goes wrong:** `LinkedFilesPanel` is rendered in `DashboardLayout` conditionally on `currentSessionId`. At `/sessions/new`, there is no session yet, so `LinkedFilesPanel` never renders, and the rightbar state may be irrelevant. The expand button for CHAT-02 only needs to work in contexts where a session exists (i.e., on `/sessions/[id]` before or after messages).

**How to avoid:** In `WelcomeScreen`, show the expand toggle only when `sessionId` prop is provided (meaning a session exists). For `/sessions/new` (no `sessionId`), no rightbar toggle is needed because `LinkedFilesPanel` doesn't render.
```tsx
{sessionId && !rightPanelOpen && (
  <Button ... onClick={toggleRightPanel}>
    <PanelRightOpen ... />
  </Button>
)}
```

### Pitfall 5: LBAR-02 Left Padding Misalignment
**What goes wrong:** `SidebarMenuButton` has default internal padding from shadcn. When collapsed to icon-only mode, the icon is centered. When expanded, the icon + label appear with default `pl-2` from shadcn defaults. The padding is applied via shadcn's `cva` variants in `sidebar.tsx` — it is NOT overrideable with a simple `pl-*` class on `SidebarMenuButton` without using `className` with `!important` or restructuring.

**How to avoid:** Inspect the rendered HTML in the browser (dev tools) to see actual left padding values applied by shadcn. The fix is likely adding or removing a custom `className` on the `SidebarMenuButton` or its children. Do not guess — check devtools first. If the issue is specific to icon alignment when `isExpanded && <span>`, the gap between icon and text is `gap-2` which is standard.

---

## Code Examples

### SidebarTrigger Usage (existing pattern)
```tsx
// Source: frontend/src/components/session/WelcomeScreen.tsx lines 305-313
<div className="px-4 py-3">
  <div className="flex items-center gap-2">
    <SidebarTrigger className="-ml-1" />
    {/* logo removed per CHAT-01 */}
  </div>
</div>
```

### Floating Rightbar Expand Button (for CHAT-02)
```tsx
// Pattern to add to WelcomeScreen when sessionId is defined and rightPanelOpen is false
// Parent container already has className="flex flex-col h-full relative"
{sessionId && !rightPanelOpen && (
  <Button
    variant="ghost"
    size="icon"
    className="absolute top-3 right-3 z-10"
    onClick={toggleRightPanel}
    title="Open linked files"
  >
    <PanelRightOpen className="h-4 w-4" />
  </Button>
)}
```

### ChatInterface Header Restructure (for CHAT-03)
```tsx
// Source: frontend/src/components/chat/ChatInterface.tsx lines 362-394
// Current: toggle is inside max-w-3xl centered div
// Fix: pull toggle outside max-w-3xl div, pin to true right edge
<div className="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center">
  {/* Centered content */}
  <div className="flex-1 max-w-3xl flex items-center gap-2">
    <SidebarTrigger className="-ml-1" />
    <div className="h-7 w-7 rounded-lg gradient-primary flex items-center justify-center shrink-0">
      <span className="text-sm font-bold text-white">S</span>
    </div>
    <span className="font-semibold text-sm tracking-tight shrink-0">Spectra</span>
    <span className="text-muted-foreground/40 shrink-0">|</span>
    <h2 className="text-lg font-semibold truncate">{sessionTitle}</h2>
  </div>
  {/* Right toggle — pinned to right edge, NOT inside max-w-3xl */}
  <Button
    variant="ghost"
    size="sm"
    className="gap-1.5 text-muted-foreground hover:text-foreground ml-auto"
    onClick={toggleRightPanel}
    title={rightPanelOpen ? "Close linked files" : "Open linked files"}
  >
    {rightPanelOpen ? (
      <PanelRightClose className="h-4 w-4" />
    ) : (
      <PanelRightOpen className="h-4 w-4" />
    )}
    <span className="text-xs">
      Files{sessionDetail?.files?.length ? ` (${sessionDetail.files.length})` : ""}
    </span>
  </Button>
</div>
```

### WorkspacePage Header Addition (for LBAR-01)
```tsx
// Source: frontend/src/app/(workspace)/workspace/page.tsx — current outer div
// Add a minimal sticky header with SidebarTrigger before the main content
<div className="flex flex-col h-full">
  <div className="px-4 py-3 shrink-0 border-b">
    <SidebarTrigger className="-ml-1" />
  </div>
  <div className="flex-1 overflow-y-auto">
    <div className="p-8 max-w-7xl mx-auto">
      {/* existing content unchanged */}
    </div>
  </div>
</div>
```

### MyFilesPage Header Fix (for FILES-01 + FILES-02)
```tsx
// Source: frontend/src/app/(dashboard)/my-files/page.tsx
// Current: SidebarTrigger + logo inside scrollable flex-1 div
// Fix: extract header to shrink-0 bar above the scrollable area
// Outer div already: className="flex flex-col h-full overflow-hidden"
<div className="flex flex-col h-full overflow-hidden">
  {/* Fixed header — above scrollable content */}
  <div className="px-6 py-3 shrink-0 border-b flex items-center gap-3">
    <SidebarTrigger className="-ml-1" />
    {/* Logo REMOVED per FILES-01 */}
    <div>
      <h1 className="text-2xl font-bold tracking-tight">My Files</h1>
      <p className="text-sm text-muted-foreground mt-1">Manage your uploaded data files</p>
    </div>
  </div>
  {/* Scrollable content */}
  <div className="flex-1 overflow-y-auto">
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      {/* drag zone, upload button, table — unchanged */}
    </div>
  </div>
  {/* Upload dialog — unchanged */}
</div>
```

---

## File Map (All Files to Touch)

| File | Requirements | Change |
|------|-------------|--------|
| `frontend/src/app/(workspace)/workspace/page.tsx` | LBAR-01 | Add sticky header strip with `SidebarTrigger`; restructure outer div to `flex flex-col h-full` |
| `frontend/src/components/sidebar/UnifiedSidebar.tsx` | LBAR-02 | Inspect and adjust left padding on `SidebarMenuButton` items if misaligned |
| `frontend/src/components/session/WelcomeScreen.tsx` | CHAT-01, CHAT-02 | Remove Spectra logo block (lines 308-311); add rightbar expand button when `sessionId` is set |
| `frontend/src/components/chat/ChatInterface.tsx` | CHAT-03 | Move rightbar toggle outside `max-w-3xl mx-auto` wrapper; pin to right edge |
| `frontend/src/app/(dashboard)/my-files/page.tsx` | FILES-01, FILES-02 | Remove Spectra logo block (lines 87-91); extract header to `shrink-0` fixed bar above scrollable content |

---

## Open Questions

1. **LBAR-02 — Exact padding issue**
   - What we know: `SidebarMenuButton` items in `UnifiedSidebar` render without explicit `pl-*` overrides. Icons are passed as `<Icon className="shrink-0" />`.
   - What's unclear: Whether the misalignment is visible in the collapsed (icon-only) state, the expanded state, or both. The specific pixel offset is not determinable without running the app.
   - Recommendation: Planner should specify "inspect in browser dev tools first" as Step 1 for LBAR-02 task. Fix is likely a small `className` addition to `SidebarMenuButton` or the `Link`/`a` child.

2. **CHAT-01 — Logo removal scope in WelcomeScreen**
   - What we know: The logo block (lines 308-311) appears on the new-chat screen AND on existing sessions that have no messages yet.
   - What's unclear: Whether the logo should also be removed when WelcomeScreen is used as a fallback for sessions with no messages (`/sessions/[id]` with `!hasMessages`). The requirement says "Chat section" — both cases are the Chat section.
   - Recommendation: Remove the logo in all WelcomeScreen usages since it renders inside the Chat section layout in all cases.

---

## Validation Architecture

> `workflow.nyquist_validation` key is absent from `.planning/config.json` — treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — no `jest.config.*`, `vitest.config.*`, or `pytest.ini` found in frontend |
| Config file | None — Wave 0 gap |
| Quick run command | N/A |
| Full suite command | N/A |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LBAR-01 | SidebarTrigger visible on workspace page | manual-only | N/A — visual layout, no test framework configured | ❌ |
| LBAR-02 | Menu item padding aligned | manual-only | N/A — visual alignment, no test framework | ❌ |
| CHAT-01 | No Spectra logo in Chat panel | manual-only | N/A | ❌ |
| CHAT-02 | Rightbar expand toggle visible after collapse | manual-only | N/A — requires UI interaction | ❌ |
| CHAT-03 | Rightbar toggle at top-right corner | manual-only | N/A — visual position | ❌ |
| FILES-01 | No Spectra logo in Files panel | manual-only | N/A | ❌ |
| FILES-02 | SidebarTrigger at top of Files screen | manual-only | N/A — visual position | ❌ |

All requirements in this phase are visual/positional UI fixes. Automated testing is not feasible without a configured component test framework (e.g., Playwright, Cypress, Vitest + Testing Library). Verification is manual browser inspection per requirement.

### Sampling Rate
- **Per task commit:** Run `npm run build` in `/frontend` to confirm no TypeScript/compile errors
- **Per wave merge:** Manual browser verification of all 7 requirements
- **Phase gate:** All 7 success criteria visually confirmed before `/gsd:verify-work`

### Wave 0 Gaps
- No test framework currently configured for frontend. This phase does not require Wave 0 test setup — all verification is manual. If a test framework is added in a future phase, snapshot/component tests for these layout fixes can be backfilled.

---

## Sources

### Primary (HIGH confidence)
- Direct source reading of `frontend/src/components/sidebar/UnifiedSidebar.tsx` — sidebar structure and nav items
- Direct source reading of `frontend/src/app/(workspace)/workspace/page.tsx` — confirmed no header/SidebarTrigger
- Direct source reading of `frontend/src/app/(dashboard)/layout.tsx` — layout structure with LinkedFilesPanel
- Direct source reading of `frontend/src/app/(workspace)/layout.tsx` — no LinkedFilesPanel
- Direct source reading of `frontend/src/components/session/WelcomeScreen.tsx` — logo block confirmed lines 305-313
- Direct source reading of `frontend/src/components/chat/ChatInterface.tsx` — logo + centered header with toggle
- Direct source reading of `frontend/src/app/(dashboard)/my-files/page.tsx` — logo inside scrollable content confirmed
- Direct source reading of `frontend/src/components/session/LinkedFilesPanel.tsx` — toggle only in panel header, disappears at w-0
- Direct source reading of `frontend/src/components/ui/sidebar.tsx` — SidebarTrigger implementation

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — requirements text cross-referenced against source code findings

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all required primitives are already in the codebase
- Architecture: HIGH — root causes directly identified in source code; no speculation
- Pitfalls: HIGH — confirmed by reading actual code paths

**Research date:** 2026-03-10
**Valid until:** Stable — these findings reflect the committed codebase at time of research. Valid until any of the 5 target files are modified.
