---
status: diagnosed
trigger: "P31-T8 — Audit log table missing column sorting"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Focus

hypothesis: Sorting is entirely absent — no client-side getSortedRowModel, no column enableSorting flags, no sort state, and no server-side sort_by/sort_order params.
test: Confirmed by reading all relevant files.
expecting: N/A (diagnosis complete)
next_action: Return structured diagnosis

## Symptoms

expected: Clicking column headers (timestamp, action, admin, target) sorts the table
actual: Clicking column headers does nothing — headers are rendered as plain text with no sort indicator or handler
errors: No runtime error; feature simply absent
reproduction: Open /audit-log in admin frontend, click any column header
started: Always — feature was never implemented

## Eliminated

- hypothesis: getSortedRowModel is imported but misconfigured
  evidence: The import block in AuditLogTable.tsx only imports getCoreRowModel — getSortedRowModel is never imported at all
  timestamp: 2026-02-17

- hypothesis: Column definitions have enableSorting: false set explicitly
  evidence: Column definitions have no enableSorting property at all — sorting simply was not set up
  timestamp: 2026-02-17

- hypothesis: Backend supports sort_by/sort_order but frontend ignores it
  evidence: Backend router (audit.py line 18-28) accepts no sort_by/sort_order query params — order is hardcoded as created_at DESC (line 79)
  timestamp: 2026-02-17

- hypothesis: AuditLogParams type has sort fields but hook omits them
  evidence: AuditLogParams in types/audit.ts has no sort_by or sort_order fields at all
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: admin-frontend/src/components/audit/AuditLogTable.tsx — TanStack Table import block (lines 4-9)
  found: Only getCoreRowModel is imported from @tanstack/react-table; getSortedRowModel is absent
  implication: Client-side sorting model is not registered

- timestamp: 2026-02-17
  checked: AuditLogTable.tsx — useReactTable config (lines 183-187)
  found: Table is configured with only { data, columns, getCoreRowModel: getCoreRowModel() } — no onSortingChange, no getSortedRowModel, no manualSorting flag
  implication: TanStack Table has no sorting capability wired up at all

- timestamp: 2026-02-17
  checked: AuditLogTable.tsx — column definitions (lines 110-181)
  found: No column has enableSorting property set; headers are plain strings not wrapped in sort-trigger buttons
  implication: No visual sort indicator or click handler on any column header

- timestamp: 2026-02-17
  checked: admin-frontend/src/types/audit.ts — AuditLogParams interface (lines 26-34)
  found: Fields: page, page_size, action, admin_id, target_type, date_from, date_to — no sort_by, no sort_order
  implication: Even if UI emitted sort params, the type contract and hook would drop them

- timestamp: 2026-02-17
  checked: admin-frontend/src/hooks/useAuditLog.ts
  found: Hook builds URLSearchParams from AuditLogParams with no sort fields forwarded
  implication: No sort params ever reach the backend

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/audit.py — endpoint signature (lines 18-28) and ordering (line 79)
  found: No sort_by or sort_order Query params; order_by is hardcoded as AdminAuditLog.created_at.desc()
  implication: Backend cannot honor sort requests even if frontend sent them

## Resolution

root_cause: Column sorting was never implemented — missing at all three layers: (1) TanStack Table has no getSortedRowModel or sort state, (2) AuditLogParams/hook carry no sort fields, (3) backend endpoint has no sort_by/sort_order params and hardcodes the order.

fix: Not applied (diagnose-only mode)

verification: N/A

files_changed: []
