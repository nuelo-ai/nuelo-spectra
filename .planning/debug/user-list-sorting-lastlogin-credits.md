---
status: diagnosed
trigger: "P29-T1 — User list missing sorting, last login empty, credit balance not shown"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T01:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - Three independent gaps: (1) frontend has no sort UI wired to the API, (2) last_login_at is flushed but never committed in login handler, (3) credit_balance column is absent from UserTable column definitions
test: Read all relevant files
expecting: Confirmed
next_action: return diagnosis

## Symptoms

expected: Sortable columns, populated last_login dates, credit balance visible in user list
actual: (1) Column sorting not available, (2) Last Login column empty, (3) Credit Balance not shown
errors: none reported
reproduction: Visit admin user list page
started: unknown

## Eliminated

- hypothesis: Backend endpoint does not support sort_by parameter
  evidence: backend/app/routers/admin/users.py lines 65-68 clearly defines sort_by Query param with pattern ^(created_at|last_login_at|first_name|credit_balance)$
  timestamp: 2026-02-17T01:00:00Z

- hypothesis: last_login_at column missing from User model or migration
  evidence: User model (models/user.py line 37-39) has last_login_at field; migration a66a91bbb9fa adds the column correctly
  timestamp: 2026-02-17T01:00:00Z

- hypothesis: credit_balance missing from API response schema or service
  evidence: UserSummary schema (admin_users.py line 23) includes credit_balance; service (services/admin/users.py line 107) LEFT JOINs user_credits and maps balance to credit_balance in response
  timestamp: 2026-02-17T01:00:00Z

- hypothesis: Frontend type UserSummary is missing last_login_at or credit_balance
  evidence: types/user.ts UserSummary (lines 14-15) defines both last_login_at and credit_balance correctly
  timestamp: 2026-02-17T01:00:00Z

## Evidence

- timestamp: 2026-02-17T01:00:00Z
  checked: backend/app/routers/admin/users.py
  found: sort_by parameter supported with pattern ^(created_at|last_login_at|first_name|credit_balance)$, all four fields accepted
  implication: Backend sorting is fully implemented

- timestamp: 2026-02-17T01:00:00Z
  checked: backend/app/services/admin/users.py
  found: list_users() builds sort_column_map including all four sort fields; applies asc/desc ordering with nullslast; response dict includes last_login_at and credit_balance
  implication: Service layer fully supports sorting and returns all fields

- timestamp: 2026-02-17T01:00:00Z
  checked: admin-frontend/src/components/users/UserTable.tsx
  found: useReactTable() initialized with getCoreRowModel() only - NO getSortedRowModel(), NO enableSorting: true, NO sorting state; table headers have no onClick handlers for sort toggling; column definitions use columnHelper.display() for name (no accessor), columnHelper.accessor() for email, is_active, user_class, created_at, last_login_at - NO credit_balance column defined at all
  implication: THREE gaps in UserTable: (1) sorting not wired to TanStack Table at all, (2) no sort UI in column headers, (3) credit_balance column is entirely absent

- timestamp: 2026-02-17T01:00:00Z
  checked: admin-frontend/src/hooks/useUsers.ts
  found: useUserList() does forward sort_by and sort_order params to API (lines 33-34); UserListParams type includes sort_by and sort_order fields
  implication: Hook infrastructure supports sort params - the gap is purely in the UI component not setting/using them

- timestamp: 2026-02-17T01:00:00Z
  checked: backend/app/routers/auth.py login handler (lines 151-153)
  found: user.last_login_at = datetime.now(timezone.utc) followed by await db.flush() - NO db.commit() call in the login handler
  implication: last_login_at write is flushed to SQLAlchemy's unit of work but the transaction is never committed. get_db() closes the session without committing (database.py line 25-29). The value is lost on every login.

- timestamp: 2026-02-17T01:00:00Z
  checked: backend/app/database.py
  found: get_db() yields session then calls session.close() in finally block - no commit. No auto-commit configured on async_session_maker. The autocommit:True at main.py line 238 is for the LangGraph psycopg checkpointer only, not for SQLAlchemy sessions.
  implication: Confirms last_login_at is never persisted to the database

- timestamp: 2026-02-17T01:00:00Z
  checked: admin-frontend/src/components/shared/DataTableShell.tsx
  found: Renders table headers via flexRender with no sort indicator or onClick wiring; purely a display component
  implication: Sorting UI would need to be added to column headers in UserTable, not in DataTableShell

## Resolution

root_cause: Three separate implementation gaps — (1) frontend UserTable never wired sort state to TanStack Table or column headers, so clicks do nothing and sort params are never sent to API; (2) login endpoint writes last_login_at with flush() but never commits the transaction, so the value is discarded on every login; (3) credit_balance column definition is entirely missing from UserTable column array.

fix:
verification:
files_changed: []
