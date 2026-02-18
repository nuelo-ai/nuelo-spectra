---
status: diagnosed
trigger: "P29-T8 — Bulk operation checkboxes not selectable (BLOCKER)"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - rowSelection state uses numeric indices as keys but getRowId returns UUID strings, causing permanent key mismatch
test: Read UserTable.tsx lines 275-305 — rowSelection built with String(i) keys vs getRowId using row.id
expecting: Root cause confirmed via code analysis
next_action: Return diagnosis

## Symptoms

expected: Clicking a checkbox next to a user row selects that user for bulk operations
actual: Checkboxes cannot be clicked/selected — no selection state change occurs visually; internal state may partially update
errors: None reported (visual/interaction bug)
reproduction: Open admin user list page, attempt to click any checkbox in the user rows
started: Unknown — reported in P29-T8 UAT

## Eliminated

- hypothesis: z-index/overlay blocking clicks
  evidence: No overlapping elements; BulkActionBar only renders when count > 0 (so it's absent when first trying to select)
  timestamp: 2026-02-17

- hypothesis: pointer-events CSS issue
  evidence: No pointer-events:none or related CSS found on table cells or checkbox wrappers
  timestamp: 2026-02-17

- hypothesis: enableRowSelection not set
  evidence: enableRowSelection: true is explicitly set on the table instance (line 303)
  timestamp: 2026-02-17

- hypothesis: onRowSelectionChange missing
  evidence: onRowSelectionChange is wired up correctly at lines 294-302
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: UserTable.tsx lines 275-283 — rowSelection construction
  found: |
    rowSelection is built as: selection[String(i)] = true
    i is the numeric array index (0, 1, 2...) of the user in the current page
  implication: rowSelection keys are "0", "1", "2" etc.

- timestamp: 2026-02-17
  checked: UserTable.tsx line 304 — getRowId configuration
  found: getRowId: (row) => row.id  (UUID string like "abc-def-123")
  implication: TanStack Table uses UUID strings as row identifiers internally

- timestamp: 2026-02-17
  checked: TanStack Table behavior — row.getIsSelected()
  found: |
    When getRowId is set, TanStack Table stores selection as { [getRowId(row)]: true }
    i.e., { "abc-def-123": true }
    But the controlled rowSelection state has { "0": true }
    These never match, so row.getIsSelected() always returns false
  implication: Checkbox checked={row.getIsSelected()} is always false — visually never checks

- timestamp: 2026-02-17
  checked: UserTable.tsx lines 294-301 — onRowSelectionChange handler
  found: |
    Handler correctly extracts IDs and calls onSelectionChange(newIds)
    But newIds come from: users[Number(idx)]?.id where idx is the key from newSelection
    Since TanStack Table updater uses UUID keys (from getRowId), Number("abc-def-123") = NaN
    users[NaN] = undefined, so .filter(Boolean) drops them all
    Result: onSelectionChange([]) — empty array every time
  implication: Both the visual state AND the data state fail to update on click

## Resolution

root_cause: |
  UserTable.tsx has a key mismatch between getRowId and rowSelection state.
  getRowId returns row.id (UUID string), but rowSelection is built with numeric
  array indices as keys (String(i)). TanStack Table uses getRowId to key its
  internal row selection state — so when it looks up rowSelection["uuid-string"]
  it finds nothing, causing row.getIsSelected() to always return false.
  Additionally the onRowSelectionChange handler tries to reverse-map UUID keys
  back to array indices via Number(idx), which yields NaN for UUID strings,
  making every lookup return undefined — so onSelectionChange is always called
  with an empty array. Both display and data state are broken.
fix: (not applied — research-only mode)
verification: (not applied)
files_changed: []
