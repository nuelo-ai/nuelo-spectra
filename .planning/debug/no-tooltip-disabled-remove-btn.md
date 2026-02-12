---
status: diagnosed
trigger: "no tooltip feedback when clicking the disabled remove button on the last remaining file in a session"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:00:00Z
---

## Current Focus

hypothesis: The remove button uses a native HTML `title` attribute instead of the Radix Tooltip component, AND the button is disabled inside an AlertDialogTrigger which swallows pointer events — preventing even the native title from appearing.
test: Compare FileCard remove button (title attr, no Tooltip) vs FileSidebar buttons (Tooltip component)
expecting: FileCard uses title, FileSidebar uses Tooltip — confirming the missing component
next_action: Return diagnosis

## Symptoms

expected: With 1 file linked, the remove button should show a tooltip "Cannot remove last file — at least one file must be linked"
actual: Button is correctly disabled/non-functional, but no tooltip or feedback is shown
errors: None — purely a missing UX affordance
reproduction: Open a session with exactly 1 linked file, hover over the X remove button
started: Always broken — tooltip was never implemented with the Tooltip component

## Eliminated

- hypothesis: isLastFile prop not being passed to FileCard
  evidence: LinkedFilesPanel.tsx line 74 passes `isLastFile={files.length === 1}` correctly
  timestamp: 2026-02-12

- hypothesis: Button not actually disabled
  evidence: FileCard.tsx line 98 has `disabled={isLastFile}` which correctly disables the button
  timestamp: 2026-02-12

## Evidence

- timestamp: 2026-02-12
  checked: FileCard.tsx remove button implementation (lines 92-103)
  found: Button uses native HTML `title` attribute (line 99) instead of Radix Tooltip component. The button is a child of AlertDialogTrigger via `asChild`.
  implication: Two compounding issues prevent tooltip from showing.

- timestamp: 2026-02-12
  checked: FileSidebar.tsx for comparison (lines 126-159)
  found: FileSidebar uses proper TooltipProvider > Tooltip > TooltipTrigger > TooltipContent pattern from Radix UI for its info and delete buttons
  implication: The project already has the Tooltip component available and uses it elsewhere — FileCard just never adopted it.

- timestamp: 2026-02-12
  checked: How disabled + AlertDialogTrigger interacts with pointer events
  found: Radix AlertDialogTrigger renders as a button. When `asChild` merges with a disabled Button, the disabled attribute sets `pointer-events: none` (via Tailwind's `disabled:pointer-events-none` in the Button component). This kills hover detection, so even the native `title` attribute cannot trigger a browser tooltip on hover.
  implication: The native `title` attribute is doubly ineffective: (1) it's not a styled tooltip, and (2) it can't even appear because pointer-events are disabled.

- timestamp: 2026-02-12
  checked: tooltip.tsx component (lines 1-57)
  found: Full Radix Tooltip implementation exists at @/components/ui/tooltip.tsx with TooltipProvider, Tooltip, TooltipTrigger, TooltipContent exports
  implication: The fix is straightforward — wrap the button in the existing Tooltip component

## Resolution

root_cause: |
  Two compounding issues in FileCard.tsx (lines 92-103):

  1. **Wrong tooltip mechanism**: The remove button uses a native HTML `title` attribute (line 99)
     instead of the project's Radix UI Tooltip component (`@/components/ui/tooltip`). Native `title`
     attributes produce an unstyled, delayed browser tooltip — inconsistent with the rest of the app.

  2. **Disabled button kills pointer events**: The Button component with `disabled={isLastFile}`
     applies `pointer-events: none` (standard Tailwind disabled styling). Since the button is the
     direct child of AlertDialogTrigger (via `asChild`), all mouse events including hover are
     suppressed. This means even the native `title` tooltip CANNOT appear — the browser never
     registers a hover event on the element.

  The combination means: when `isLastFile=true`, the button is visually dimmed but provides
  zero feedback about WHY it's disabled. The user sees a grayed-out X with no explanation.

fix: not applied (diagnosis only)
verification: not performed
files_changed: []
