---
status: diagnosed
phase: 31-dashboard-admin-frontend
source: 31-01-SUMMARY.md, 31-02-SUMMARY.md, 31-03-SUMMARY.md, 31-04-SUMMARY.md, 31-05-SUMMARY.md
started: 2026-02-17T00:25:00Z
updated: 2026-02-17T00:40:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Admin Frontend Login
expected: Navigating to localhost:3001 shows the admin login page. Entering valid admin credentials logs in and redirects to the dashboard. Invalid credentials show a clear error message.
result: pass

### 2. Dashboard Metric Cards
expected: Dashboard displays 6 metric cards: total users (active vs inactive), active today, new signups (today/week/month), total chat sessions, total messages sent, and credit balance summary (total used / total remaining).
result: issue
reported: "Active today shows 0 value while many users were actually active. Credit used shows 0 while many were used today."
severity: major

### 3. Dashboard Trend Charts
expected: Dashboard renders Recharts trend charts for signups over time and messages over time, with time range selectors and theme-aware styling. Auto-refreshes every 60 seconds.
result: pass

### 4. Dashboard Credit Distribution
expected: Dashboard shows a BarChart of credit distribution by tier and a table of low-credit users (balance < 10).
result: pass

### 5. Admin Sidebar Navigation
expected: Collapsible sidebar with navigation links to all admin pages: Dashboard, Users, Invitations, Credits, Settings, Audit Log. Current page is highlighted.
result: pass

### 6. Credits Page
expected: Credits overview page shows summary cards (distributed/used/remaining) and a tier breakdown table showing credit allocation per tier.
result: pass

### 7. Settings Page
expected: Settings page displays a sectioned form with: signup control toggle, default tier dropdown, invite expiry, credit reset policy, cost per message. Changes save successfully.
result: issue
reported: "1) Tier dropdown hardcoded to Free/Standard/Premium, not aligned with user_classes.yaml. 2) Credit Reset Policy shown as global setting but should be per-tier — each tier has its own reset_policy in yaml. UI needs to edit at tier level, not globally."
severity: major

### 8. Audit Log Page
expected: Audit log page shows a paginated table of admin actions with filters for action type, admin, date range. Rows are expandable to show details JSON.
result: issue
reported: "Looks good but sorting is not available on table columns"
severity: minor

### 9. Dark Mode Support
expected: Admin frontend supports dark mode with Nord Frost blue (#81A1C1) accent. Theme toggle works and persists.
result: pass

## Summary

total: 9
passed: 6
issues: 3
pending: 0
skipped: 0

## Gaps

- truth: "Dashboard active today and credit used metrics show accurate values"
  status: failed
  reason: "User reported: Active today shows 0 despite many active users. Credit used shows 0 despite credits being used today."
  severity: major
  test: 2
  root_cause: "Two bugs: (1) last_login_at never committed (db.flush without db.commit in login — same as P29-T1), (2) dashboard.py filters transaction_type=='deduction' but credit service writes 'usage'"
  artifacts:
    - path: "backend/app/routers/auth.py"
      issue: "db.flush() without db.commit() — last_login_at never persisted"
    - path: "backend/app/routers/admin/dashboard.py"
      issue: "Line 91: filters transaction_type=='deduction' but actual value is 'usage'"
  missing:
    - "Fix db.commit() in login (shared fix with P29-T1)"
    - "Change filter from 'deduction' to 'usage' in dashboard.py"

- truth: "Settings page tier dropdown fetches from API and credit reset policy is per-tier"
  status: failed
  reason: "User reported: 1) Tier dropdown hardcoded, not aligned with yaml. 2) Credit Reset Policy is global but should be per-tier as defined in user_classes.yaml."
  severity: major
  test: 7
  root_cause: "SettingsForm has hardcoded tier dropdown; no useTiers hook; credit_reset_policy stored as single global key but YAML defines per-tier reset_policy"
  artifacts:
    - path: "admin-frontend/src/components/settings/SettingsForm.tsx"
      issue: "Hardcoded tier options and global credit_reset_policy"
    - path: "backend/app/services/platform_settings.py"
      issue: "credit_reset_policy as single global key — functionally unused by tier logic"
  missing:
    - "Fetch tiers from API for dropdown"
    - "Remove global credit_reset_policy; display per-tier reset_policy from tiers endpoint read-only"

- truth: "Audit log table supports column sorting"
  status: failed
  reason: "User reported: sorting not available on table columns"
  severity: minor
  test: 8
  root_cause: "Sorting never implemented at any layer — no getSortedRowModel in TanStack config, no sort params in hook/types, no sort_by/sort_order in backend endpoint"
  artifacts:
    - path: "admin-frontend/src/components/audit/AuditLogTable.tsx"
      issue: "No getSortedRowModel, no sorting state, no sort handlers on headers"
    - path: "admin-frontend/src/hooks/useAuditLog.ts"
      issue: "No sort params forwarded"
    - path: "admin-frontend/src/types/audit.ts"
      issue: "AuditLogParams missing sort_by/sort_order"
    - path: "backend/app/routers/admin/audit.py"
      issue: "No sort_by/sort_order query params; hardcoded order_by"
  missing:
    - "Add sort params to backend endpoint"
    - "Add sort fields to types and hook"
    - "Configure TanStack Table with manualSorting and sort UI"
