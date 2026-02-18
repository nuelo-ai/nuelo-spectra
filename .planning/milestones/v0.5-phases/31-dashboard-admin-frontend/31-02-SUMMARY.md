---
phase: 31-dashboard-admin-frontend
plan: 02
subsystem: ui
tags: [next.js, react, shadcn, zustand, tanstack-query, admin, auth, sidebar]

requires:
  - phase: 29-admin-backend
    provides: Admin auth endpoints (/admin/auth/login, /admin/auth/me), X-Admin-Token middleware
provides:
  - Standalone admin-frontend/ Next.js 16.1.6 app on port 3001
  - Admin API client with X-Admin-Token sliding window interception
  - AdminAuthProvider with login/logout/session verification
  - Collapsible admin sidebar with Overview/People/Platform navigation
  - Admin header with theme toggle and user dropdown
  - Login page with admin branding
  - Protected admin layout with auth redirect
  - All shadcn/ui primitives for admin pages
  - Placeholder routes for dashboard, users, invitations, credits, settings, audit-log
affects: [31-03, 31-04, 31-05]

tech-stack:
  added: [recharts]
  patterns: [admin-api-client-pattern, admin-auth-context, sidebar-store-zustand]

key-files:
  created:
    - admin-frontend/package.json
    - admin-frontend/src/lib/admin-api-client.ts
    - admin-frontend/src/hooks/useAdminAuth.tsx
    - admin-frontend/src/components/layout/AdminSidebar.tsx
    - admin-frontend/src/components/layout/AdminHeader.tsx
    - admin-frontend/src/components/providers.tsx
    - admin-frontend/src/stores/sidebarStore.ts
    - admin-frontend/src/types/admin-auth.ts
    - admin-frontend/src/app/(auth)/login/page.tsx
    - admin-frontend/src/app/(admin)/layout.tsx
  modified:
    - admin-frontend/src/app/layout.tsx

key-decisions:
  - "Admin-distinct theme: indigo/blue primary in light mode, Nord Frost blue (#81A1C1) in dark mode"
  - "Root page redirects to /dashboard (admin layout handles auth redirect to /login)"
  - "Admin API client uses relative paths with Next.js rewrites proxy (not direct backend URLs)"

patterns-established:
  - "Admin API client pattern: fetchWithAdminAuth with X-Admin-Token interception and 401 redirect"
  - "Admin auth context: AdminAuthProvider wrapping all routes with login/logout/session check"
  - "Sidebar store: Zustand store for collapse state shared between sidebar and admin layout"

requirements-completed: [ARCH-06, ARCH-07, ARCH-09]

duration: 5min
completed: 2026-02-17
---

# Phase 31 Plan 02: Admin Frontend Scaffold Summary

**Standalone admin-frontend Next.js app with admin API client (X-Admin-Token interception), login page, and collapsible sidebar shell layout on port 3001**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-17T02:21:48Z
- **Completed:** 2026-02-17T02:26:30Z
- **Tasks:** 2
- **Files modified:** 48

## Accomplishments
- Scaffolded standalone admin-frontend/ Next.js 16.1.6 app with full matching stack plus Recharts
- Created admin API client with X-Admin-Token interception for sliding window session renewal
- Built login page, auth context, and protected admin shell with collapsible sidebar navigation
- Installed 17 shadcn/ui primitives covering all future admin page needs
- Admin-distinct theme with indigo/blue accent differentiating from public frontend

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold admin-frontend Next.js app with dependencies and config** - `7177d63` (feat)
2. **Task 2: Create admin API client, auth context, login page, and admin shell layout** - `43cf592` (feat)

## Files Created/Modified
- `admin-frontend/package.json` - Admin frontend package with matching stack plus Recharts
- `admin-frontend/tsconfig.json` - TypeScript config copied from frontend
- `admin-frontend/next.config.ts` - API rewrites to proxy to backend on port 8000
- `admin-frontend/postcss.config.mjs` - PostCSS with Tailwind v4
- `admin-frontend/eslint.config.mjs` - ESLint config matching frontend
- `admin-frontend/components.json` - shadcn/ui config (new-york style)
- `admin-frontend/src/app/globals.css` - Admin theme with indigo primary (light) and Nord Frost blue (dark)
- `admin-frontend/src/app/layout.tsx` - Root layout with Geist fonts and Providers
- `admin-frontend/src/app/page.tsx` - Root redirect to /dashboard
- `admin-frontend/src/lib/utils.ts` - cn() utility
- `admin-frontend/src/lib/admin-api-client.ts` - API client with X-Admin-Token interception
- `admin-frontend/src/lib/query-client.ts` - TanStack Query client (30s stale, 1 retry)
- `admin-frontend/src/types/admin-auth.ts` - AdminUser, AdminLoginRequest/Response types
- `admin-frontend/src/hooks/useAdminAuth.tsx` - Auth context with login/logout/session verify
- `admin-frontend/src/components/providers.tsx` - QueryClient, Theme, Tooltip, Auth, Toaster
- `admin-frontend/src/stores/sidebarStore.ts` - Zustand sidebar collapse store
- `admin-frontend/src/components/layout/AdminSidebar.tsx` - Collapsible sidebar with 3 nav sections
- `admin-frontend/src/components/layout/AdminHeader.tsx` - Header with title, theme toggle, user menu
- `admin-frontend/src/app/(auth)/layout.tsx` - Centered auth layout
- `admin-frontend/src/app/(auth)/login/page.tsx` - Admin login form
- `admin-frontend/src/app/(admin)/layout.tsx` - Protected admin shell layout
- `admin-frontend/src/app/(admin)/dashboard/page.tsx` - Dashboard placeholder
- `admin-frontend/src/app/(admin)/users/page.tsx` - Users placeholder
- `admin-frontend/src/app/(admin)/users/[userId]/page.tsx` - User detail placeholder
- `admin-frontend/src/app/(admin)/invitations/page.tsx` - Invitations placeholder
- `admin-frontend/src/app/(admin)/credits/page.tsx` - Credits placeholder
- `admin-frontend/src/app/(admin)/settings/page.tsx` - Settings placeholder
- `admin-frontend/src/app/(admin)/audit-log/page.tsx` - Audit log placeholder
- `admin-frontend/src/components/ui/*.tsx` - 17 shadcn/ui component primitives

## Decisions Made
- Admin-distinct theme uses indigo/blue primary (`oklch(0.45 0.2 260)`) in light mode and Nord Frost blue (`#81A1C1`) in dark mode, differentiating from the public frontend's neutral/Snow Storm palette
- Root page redirects to /dashboard rather than /login; the admin layout handles the auth check and redirects unauthenticated users to /login
- Admin API client uses relative paths (`/api/admin/...`) so Next.js rewrites proxy to the backend, avoiding CORS issues

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Admin frontend scaffold is complete and building successfully
- All routes are in place with placeholder content, ready for real page implementations
- Auth flow, API client, and shell layout provide the foundation for all subsequent admin pages
- Next plans (31-03 through 31-05) can build actual page content within this shell

## Self-Check: PASSED

All key files verified present. Both task commits (7177d63, 43cf592) confirmed in git log.

---
*Phase: 31-dashboard-admin-frontend*
*Completed: 2026-02-17*
