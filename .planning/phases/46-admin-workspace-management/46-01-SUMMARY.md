---
phase: 46-admin-workspace-management
plan: 01
subsystem: ui
tags: [nextjs, react, recharts, admin, dashboard, mock-data]

# Dependency graph
requires:
  - phase: 45-what-if-scenarios
    provides: completed mockup foundation with sidebar pattern and mock-data.ts structure
provides:
  - Admin route shell (/admin) with AdminSidebar and collapsible layout
  - Workspace Activity Dashboard with KPI row, line chart, donut chart, grouped bar, funnel, stacked bar
  - Extended mock-data.ts with all admin mock data (ADMIN_USERS, COLLECTIONS_OVER_TIME, COLLECTION_STATUS_BREAKDOWN, ACTIVITY_BY_TYPE, PIPELINE_ADOPTION, CREDIT_USAGE_OVER_TIME, USER_WORKSPACE_DATA, CREDIT_COST_CONFIG, MOCK_ALERTS)
affects: [46-02-users-management, 46-03-settings-credit-config]

# Tech tracking
tech-stack:
  added: []
  patterns: [Admin shell mirrors AppShell pattern with AdminSidebar instead of Sidebar; CSS funnel approximation using proportional width divs; dark Recharts chart styling with #111827 tooltip bg and #1e293b grid lines]

key-files:
  created:
    - pulse-mockup/src/app/admin/layout.tsx
    - pulse-mockup/src/components/layout/admin-sidebar.tsx
    - pulse-mockup/src/app/admin/page.tsx
  modified:
    - pulse-mockup/src/lib/mock-data.ts
    - pulse-mockup/src/components/layout/sidebar.tsx

key-decisions:
  - "Admin layout has no Header component — each admin page renders its own page title inline"
  - "Funnel chart implemented as CSS/HTML approximation (proportional-width colored divs) — no external library"
  - "Admin Panel link added to workspace Sidebar.tsx with /admin whitelisted as a real route"
  - "AdminSidebar uses exact-match for /admin Dashboard to avoid false-active on child routes"

patterns-established:
  - "Admin shell: AdminSidebar (collapsed/expanded) + ml-16/ml-60 offset main content — mirrors AppShell"
  - "Dark chart styling: CartesianGrid stroke=#1e293b, axis tick fill=#94a3b8, tooltip bg=#111827 border=#1e293b"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03]

# Metrics
duration: 4min
completed: 2026-03-05
---

# Phase 46 Plan 01: Admin Shell and Workspace Activity Dashboard Summary

**Admin route shell with AdminSidebar + Workspace Activity Dashboard featuring KPI row, Recharts line/donut/bar charts, CSS funnel, and stacked credit usage chart**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-05T18:17:35Z
- **Completed:** 2026-03-05T18:21:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Extended mock-data.ts with 10 new admin mock data exports covering users, time-series charts, funnel, credit usage, workspace per-user data, credit cost config, and alerts
- Created AdminSidebar (Dashboard/Users/Settings nav + API Keys/Audit Log placeholders) with same collapse/expand behavior as workspace Sidebar
- Created admin/layout.tsx providing sidebar-offset shell without a top Header (admin pages own their headings)
- Built /admin/page.tsx with all 4 dashboard sections: KPI row, Workspace Activity (line + donut + grouped bar), Pipeline Adoption (CSS funnel), Credit Usage (stacked bar + KPI card)
- Added "Admin Panel" nav item to workspace Sidebar with ShieldCheck icon linking to /admin

## Task Commits

1. **Task 1: Admin shell — layout, sidebar, mock data extensions** - `6508f80` (feat)
2. **Task 2: Workspace Activity Dashboard page** - `d2f9451` (feat)

## Files Created/Modified

- `pulse-mockup/src/lib/mock-data.ts` — Appended admin mock data section (AdminUser, ADMIN_USERS, chart data arrays, USER_WORKSPACE_DATA, CREDIT_COST_CONFIG, MOCK_ALERTS)
- `pulse-mockup/src/components/layout/admin-sidebar.tsx` — New admin navigation sidebar with 5 nav items
- `pulse-mockup/src/app/admin/layout.tsx` — Admin route layout with AdminSidebar offset
- `pulse-mockup/src/app/admin/page.tsx` — Workspace Activity Dashboard page with all chart sections
- `pulse-mockup/src/components/layout/sidebar.tsx` — Added Admin Panel nav item with ShieldCheck icon

## Decisions Made

- Admin layout has no Header component — admin pages render their own `<h1>` headings inline, keeping the shell minimal
- Funnel chart uses CSS/HTML proportional-width divs rather than any external library (Recharts lacks a native funnel in older versions)
- Admin Panel link added to workspace Sidebar and whitelisted as a real route (alongside /workspace and /chat)
- AdminSidebar uses exact-match for `/admin` path so Dashboard is only active on the exact page, not on /admin/users etc.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Self-Check: PASSED

- `pulse-mockup/src/app/admin/layout.tsx` — FOUND
- `pulse-mockup/src/app/admin/page.tsx` — FOUND
- `pulse-mockup/src/components/layout/admin-sidebar.tsx` — FOUND
- Commits `6508f80` and `d2f9451` — FOUND
- `npx tsc --noEmit` — PASSED (no errors)

## Next Phase Readiness

- Admin shell and mock data are in place; Plans 02 (Users Management) and 03 (Settings / Credit Config) can import all admin mock data from mock-data.ts
- AdminSidebar Users and Settings nav items are wired to /admin/users and /admin/settings routes ready to be built

---
*Phase: 46-admin-workspace-management*
*Completed: 2026-03-05*
