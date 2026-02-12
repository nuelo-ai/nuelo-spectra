# Debug: Spectra Branding Placement

## Symptom
Spectra branding (logo "S" icon + "Spectra" text) disappears when the sidebar is collapsed. The user expects ChatGPT-style branding in the top-left of the main content area, always visible regardless of sidebar state.

## Investigation

### 1. Current branding location — `ChatSidebar.tsx` (lines 38-44)

The branding element is inside `<SidebarHeader>` within the `<Sidebar>` component:

```tsx
<SidebarHeader>
  <div className="flex items-center gap-2 px-2 py-1.5 group-data-[collapsible=icon]:hidden">
    <div className="h-7 w-7 rounded-lg gradient-primary flex items-center justify-center">
      <span className="text-sm font-bold text-white">S</span>
    </div>
    <span className="font-semibold text-sm tracking-tight">Spectra</span>
  </div>
  ...
</SidebarHeader>
```

**Key problem:** The `group-data-[collapsible=icon]:hidden` class explicitly hides the branding when the sidebar is in icon/collapsed mode. This is intentional sidebar behavior for space-constrained elements, but the branding should never be hidden.

### 2. Dashboard layout — `layout.tsx`

The layout is structured as:
```
SidebarProvider
  └─ flex container (h-screen)
      ├─ ChatSidebar          ← branding is HERE (inside sidebar)
      ├─ <main> (children)    ← branding SHOULD be here
      └─ LinkedFilesPanel
```

The `<main>` element has no persistent header. Each page/component manages its own header internally.

### 3. Main content headers — where branding SHOULD go

**ChatInterface.tsx** (lines 354-381) — has a header bar:
```tsx
<div className="px-4 py-3 border-b bg-background/95 backdrop-blur ...">
  <div className="max-w-3xl mx-auto flex items-center justify-between">
    <div className="flex items-center gap-2">
      <SidebarTrigger className="-ml-1" />
      <h2 className="text-lg font-semibold truncate">{sessionTitle}</h2>
    </div>
    ...
  </div>
</div>
```

This header already has a `SidebarTrigger` (hamburger menu) on the left followed by the session title. The branding could be placed here, between the SidebarTrigger and the session title, or replacing the session title display.

**WelcomeScreen.tsx** (lines 270-273) — has a minimal top area:
```tsx
<div className="px-4 py-3">
  <SidebarTrigger className="-ml-1" />
</div>
```

This is a standalone `SidebarTrigger` with no header structure. The branding could be added next to it.

### 4. ChatGPT reference pattern

ChatGPT displays "ChatGPT" branding in the top-left of the main content area (not in the sidebar). It remains visible whether the sidebar is open or closed. The branding sits next to the sidebar toggle button in the main content header.

## Root Cause

The Spectra branding (logo + text) was placed inside `ChatSidebar.tsx`'s `<SidebarHeader>` element (line 39-44), which is part of the collapsible sidebar. The `group-data-[collapsible=icon]:hidden` class explicitly hides it when the sidebar collapses to icon mode. This means when a user closes the sidebar, the branding disappears entirely — there is no branding element anywhere in the main content area.

The correct placement should be in the **main content header area** — specifically in the persistent header bars of `ChatInterface.tsx` (line 357-359) and `WelcomeScreen.tsx` (line 271-273), next to the existing `SidebarTrigger` button. These headers are part of the `<main>` content area in the dashboard layout and are always visible regardless of sidebar state.

## Files Involved

| File | Role |
|------|------|
| `frontend/src/components/sidebar/ChatSidebar.tsx` | Lines 39-44: Contains branding that should be REMOVED from here |
| `frontend/src/components/chat/ChatInterface.tsx` | Lines 355-360: Main content header — branding should be ADDED here, next to `SidebarTrigger` |
| `frontend/src/components/session/WelcomeScreen.tsx` | Lines 270-273: Welcome page top area — branding should be ADDED here, next to `SidebarTrigger` |
| `frontend/src/app/(dashboard)/layout.tsx` | Dashboard layout — no changes needed, but provides context for the sidebar vs main content boundary |

## Fix Direction

1. **Remove** the branding block (lines 39-44) from `ChatSidebar.tsx`'s `<SidebarHeader>`
2. **Add** the branding element to `ChatInterface.tsx`'s header (line 357-359), between the `SidebarTrigger` and the `<h2>` session title
3. **Add** the same branding element to `WelcomeScreen.tsx`'s top area (line 271-273), next to the `SidebarTrigger`
4. Alternatively, create a shared `BrandingHeader` component used by both views, or add the branding to the dashboard `layout.tsx` as a persistent main-content header above `{children}` — but this would require restructuring since each child currently manages its own header
