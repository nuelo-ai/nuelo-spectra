---
phase: 31-dashboard-admin-frontend
plan: 04
subsystem: ui
tags: [react, next.js, tanstack-table, tanstack-query, shadcn, admin, users, invitations]

requires:
  - phase: 31-02
    provides: Admin frontend scaffold with auth, sidebar, API client, shadcn primitives
  - phase: 29-admin-backend
    provides: Admin user management and invitation REST endpoints
provides:
  - Users list page with search, filter, pagination, row actions, bulk operations
  - User detail page with tabbed view (Overview, Credits, Activity, Sessions)
  - Invitations page with create, revoke, resend, status filter
  - Shared components (ConfirmModal, ChallengeCodeDialog, StatusBadge, DataTableShell)
  - User and invitation data hooks with TanStack Query
affects: [31-05]

tech-stack:
  added: []
  patterns: [data-table-shell-pattern, challenge-code-dialog, status-badge-component, admin-hook-pattern]

key-files:
  created:
    - admin-frontend/src/types/user.ts
    - admin-frontend/src/types/invitation.ts
    - admin-frontend/src/hooks/useUsers.ts
    - admin-frontend/src/hooks/useInvitations.ts
    - admin-frontend/src/components/shared/ConfirmModal.tsx
    - admin-frontend/src/components/shared/ChallengeCodeDialog.tsx
    - admin-frontend/src/components/shared/StatusBadge.tsx
    - admin-frontend/src/components/shared/DataTableShell.tsx
    - admin-frontend/src/components/users/UserTable.tsx
    - admin-frontend/src/components/users/UserFilters.tsx
    - admin-frontend/src/components/users/BulkActionBar.tsx
    - admin-frontend/src/components/users/UserDetailTabs.tsx
    - admin-frontend/src/components/invitations/InvitationTable.tsx
    - admin-frontend/src/components/invitations/CreateInviteDialog.tsx
  modified:
    - admin-frontend/src/app/(admin)/users/page.tsx
    - admin-frontend/src/app/(admin)/users/[userId]/page.tsx
    - admin-frontend/src/app/(admin)/invitations/page.tsx

key-decisions:
  - "ChallengeCodeDialog generates code client-side with paste disabled via onPaste preventDefault"
  - "StatusBadge supports three types (status, tier, invitation) with distinct color palettes"
  - "DataTableShell handles server-side pagination with medium density rows"
  - "User hooks follow pattern: query hooks for reads, mutation hooks that invalidate query cache on success"

patterns-established:
  - "DataTableShell pattern: reusable TanStack Table wrapper with pagination controls for all admin data tables"
  - "Admin hook pattern: useXxxList for paginated queries, individual mutation hooks per action, bulk mutation hooks"
  - "Confirmation pattern: ConfirmModal for standard actions, ChallengeCodeDialog for destructive actions"

requirements-completed: [ARCH-06, ARCH-07]

duration: 6min
completed: 2026-02-17
---

# Phase 31 Plan 04: Users & Invitations Pages Summary

**Users list with search/filter/bulk operations, user detail with 4 tabbed sections, and invitations page with create/revoke/resend using TanStack Table and shared confirmation components**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-17T02:29:17Z
- **Completed:** 2026-02-17T02:35:35Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- Built full Users list page with searchable, filterable, paginated TanStack Table including avatar+name column, status/tier badges, and three-dot row action menus
- Created User detail page with 4-tab layout: Overview (profile + actions), Credits (balance + adjustment + transaction history), Activity (monthly timeline), Sessions (usage stats)
- Implemented Invitations page with create dialog, status filter, and revoke/resend row actions
- Created reusable shared components: DataTableShell (pagination), StatusBadge (color-coded), ConfirmModal (standard), ChallengeCodeDialog (destructive with paste disabled)
- Built comprehensive hook layer with 11 individual mutation hooks and 5 bulk mutation hooks for user operations

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared components, user data hooks, and Users list page** - `0d8a85d` (feat)
2. **Task 2: Create User detail page and Invitations page** - `71067f6` (feat)

## Files Created/Modified
- `admin-frontend/src/types/user.ts` - UserSummary, UserDetail, UserActivity, UserListResponse, CreditTransaction types
- `admin-frontend/src/types/invitation.ts` - Invitation, InvitationListResponse, CreateInvitationRequest types
- `admin-frontend/src/hooks/useUsers.ts` - 4 query hooks + 6 single-user mutations + 5 bulk mutations
- `admin-frontend/src/hooks/useInvitations.ts` - List query + create/revoke/resend mutations
- `admin-frontend/src/components/shared/ConfirmModal.tsx` - Standard confirm/cancel dialog with variant support
- `admin-frontend/src/components/shared/ChallengeCodeDialog.tsx` - 6-char challenge code with paste disabled
- `admin-frontend/src/components/shared/StatusBadge.tsx` - Color-coded badge for status, tier, invitation states
- `admin-frontend/src/components/shared/DataTableShell.tsx` - Reusable TanStack Table wrapper with server-side pagination
- `admin-frontend/src/components/users/UserTable.tsx` - User data table with selection, row actions, confirmation dialogs
- `admin-frontend/src/components/users/UserFilters.tsx` - Search bar + status/tier dropdowns + active filter chips
- `admin-frontend/src/components/users/BulkActionBar.tsx` - Sticky bulk action bar with 5 operations
- `admin-frontend/src/components/users/UserDetailTabs.tsx` - 4-tab user detail with Overview, Credits, Activity, Sessions
- `admin-frontend/src/components/invitations/InvitationTable.tsx` - Invitation data table with revoke/resend actions
- `admin-frontend/src/components/invitations/CreateInviteDialog.tsx` - Email-validated create invitation dialog
- `admin-frontend/src/app/(admin)/users/page.tsx` - Users list page assembling filters, bulk bar, table
- `admin-frontend/src/app/(admin)/users/[userId]/page.tsx` - User detail page with back nav and tabbed content
- `admin-frontend/src/app/(admin)/invitations/page.tsx` - Invitations page with create button and status filter

## Decisions Made
- ChallengeCodeDialog generates codes client-side using alphanumeric chars (excluding ambiguous O/0/I/1) with paste disabled via onPaste preventDefault
- StatusBadge uses three distinct color mappings: green/red for status, gray/blue/purple for tier, yellow/green/red/gray for invitation status
- DataTableShell provides a reusable wrapper pattern for all admin data tables with medium density rows (h-12)
- User hooks follow a consistent pattern: query hooks for reads, individual mutation hooks per action, bulk mutation hooks for multi-select operations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Users and Invitations pages are fully built with all CRUD operations wired to backend API
- Shared components (DataTableShell, StatusBadge, ConfirmModal, ChallengeCodeDialog) are ready for reuse in remaining admin pages
- Plan 31-05 (Dashboard, Settings, Audit Log) can build upon these patterns

## Self-Check: PASSED

All 17 key files verified present. Both task commits (0d8a85d, 71067f6) confirmed in git log.

---
*Phase: 31-dashboard-admin-frontend*
*Completed: 2026-02-17*
