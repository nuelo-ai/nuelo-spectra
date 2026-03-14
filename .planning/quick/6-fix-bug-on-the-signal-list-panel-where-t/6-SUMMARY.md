---
phase: quick-6
plan: 6
subsystem: frontend/workspace
tags: [safari-fix, flex-layout, signal-list]
dependency_graph:
  requires: []
  provides: [safari-safe-signal-list-spacing]
  affects: [frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx, frontend/src/components/workspace/signal-list-panel.tsx]
tech_stack:
  added: []
  patterns: [flex-gap over space-y for Safari-safe spacing, h-full over h-screen inside nested flex layouts]
key_files:
  created: []
  modified:
    - frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
    - frontend/src/components/workspace/signal-list-panel.tsx
decisions:
  - "Use gap instead of space-y (margin-top) for card list spacing — gap is intrinsic to flex algorithm and does not expand unexpectedly in Safari"
  - "Use h-full instead of h-screen inside workspace shell — h-screen breaks the Safari height constraint chain by recalculating to full viewport, overriding parent bounds"
metrics:
  duration: "< 5 minutes"
  completed: "2026-03-14"
---

# Quick 6: Fix Safari Signal List Panel Spacing Summary

**One-liner:** Fixed Safari flex height constraint chain (h-screen -> h-full) and replaced margin-based spacing (space-y-1.5) with gap-based spacing (flex flex-col gap-1.5) in the signal list panel to eliminate excessive card spacing on Safari.

## What Was Done

Two targeted CSS class changes to fix Safari-specific rendering bugs in the Detection Results page signal list panel.

### Change 1 — signals/page.tsx (line 155)

Changed the main return container from `h-screen` to `h-full`.

- **Root cause:** Safari recalculates `h-screen` as full viewport height even when nested inside a bounded flex parent. This breaks the height constraint chain — the `flex-1 overflow-hidden` scroll container below it then over-expands, causing flex children to spread apart.
- **Fix:** `h-full` inherits the workspace shell's constrained height, restoring the chain.

### Change 2 — signal-list-panel.tsx (line 76)

Changed `p-2 space-y-1.5` to `p-2 flex flex-col gap-1.5` on the signal card list wrapper.

- **Root cause:** `space-y-*` applies `margin-top` on children. When a Safari flex scroll container's height is unconstrained (as caused by Change 1's bug), margin-based spacing can expand unpredictably.
- **Fix:** `gap` is intrinsic to the flex algorithm and behaves identically in Safari and Chrome regardless of container height.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Fix root container height and signal list spacing | 492c7b8 | signals/page.tsx, signal-list-panel.tsx |

## Verification

- TypeScript compilation: clean (no errors)
- Visual: Signal cards render with compact ~6px gaps between them in Safari, matching Chrome layout. No layout change in other browsers.

## Deviations from Plan

None - plan executed exactly as written.
