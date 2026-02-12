---
status: diagnosed
trigger: "Double-click to rename session in sidebar doesn't work, but edit control button does"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED - No onDoubleClick handler exists anywhere in the frontend
test: Grepped entire frontend/src for onDoubleClick, dblclick, double-click
expecting: Zero matches
next_action: Return diagnosis

## Symptoms

expected: Double-clicking a session title in the sidebar triggers inline rename mode
actual: Double-click does nothing; only the edit pencil/control button triggers rename
errors: none observed
reproduction: Double-click any session title in the sidebar
started: Feature was never implemented

## Eliminated

## Evidence

- timestamp: 2026-02-12T00:00:30Z
  checked: Grep for onDoubleClick|dblclick|double.click across entire frontend/src
  found: Zero matches - no double-click handler exists anywhere in the codebase
  implication: Feature was never wired up

- timestamp: 2026-02-12T00:00:40Z
  checked: ChatListItem.tsx - the sidebar session item component
  found: handleStartRename() exists (line 76-79) and correctly sets isEditing=true, but is ONLY called from DropdownMenuItem onClick (line 162). The SidebarMenuButton on line 142-151 only has onClick={handleClick} which navigates.
  implication: The rename trigger path exists but double-click was never connected to it

- timestamp: 2026-02-12T00:00:50Z
  checked: SidebarMenuButton in sidebar.tsx (line 498-546)
  found: Renders a <button> (or Slot) with no onDoubleClick prop forwarding restriction. It spreads ...props, so any onDoubleClick passed to SidebarMenuButton would work.
  implication: No blocker in the UI layer - just need to add the handler at ChatListItem level

## Resolution

root_cause: ChatListItem.tsx has no onDoubleClick handler on the SidebarMenuButton. The handleStartRename function exists and works (proven by the pencil-icon menu triggering it), but it is only wired to the dropdown menu item. No double-click event path was ever implemented.
fix: Add onDoubleClick={handleStartRename} to the SidebarMenuButton in ChatListItem.tsx (line 142)
verification: pending
files_changed: []
