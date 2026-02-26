---
status: resolved
trigger: "admin-frontend-users-activity-tab-empty"
created: 2026-02-25T00:00:00Z
updated: 2026-02-25T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - asyncpg.exceptions.GroupingError. The func.date_trunc("month", col) expression is rendered with SEPARATE bind parameters for each usage in SELECT, GROUP BY, and ORDER BY (e.g., $1 in SELECT, $4 in GROUP BY). PostgreSQL cannot verify these are the same expression, so it throws GroupingError saying created_at must be in GROUP BY. The fix: reuse the same SQLAlchemy expression object for all usages (SELECT, GROUP BY, ORDER BY) so SQLAlchemy generates a single bind parameter.

test: ran get_user_activity directly against live DB and got exact traceback
expecting: reusing the expression object in GROUP BY and ORDER BY will produce same $1 parameter reference and fix the error
next_action: fix get_user_activity to use literal("month") or reuse the date_trunc column expression

## Symptoms

expected: Activity tab displays a monthly timeline of message_count and session_count per user, sourced from GET /api/admin/users/{user_id}/activity (returns UserActivityResponse: { user_id, months: [{ month, message_count, session_count }] })
actual: Activity tab shows nothing — blank/empty, no data rendered
errors: Unknown — not yet checked
reproduction: Open admin frontend → /users → click any user → open Activity tab
started: Unknown if it ever worked

## Eliminated

- hypothesis: Backend endpoint is missing or misconfigured
  evidence: Router at /api/admin/users/{user_id}/activity is correctly registered in admin_router (admin/__init__.py includes admin_users.router). Route matches the frontend call.
  timestamp: 2026-02-25

- hypothesis: URL mismatch between frontend hook and backend route
  evidence: useUserActivity calls `/api/admin/users/${userId}/activity`. Backend route is `GET /{user_id}/activity` under prefix `/users` under `/api/admin`. Full path = /api/admin/users/{user_id}/activity. Exact match.
  timestamp: 2026-02-25

- hypothesis: Type mismatch between backend response and frontend types
  evidence: Backend UserActivityResponse: {user_id: UUID, months: list[ActivityMonth]}. Frontend: {user_id: string, months: ActivityMonth[]}. ActivityMonth fields match exactly.
  timestamp: 2026-02-25

- hypothesis: ChatMessage does not have user_id set
  evidence: Both chat.py create_message() and create_session_message() explicitly set user_id=user_id.
  timestamp: 2026-02-25

- hypothesis: Query key collision prevents data from loading
  evidence: useUserDetail key is ["admin", "users", userId], useUserActivity key is ["admin", "users", userId, "activity"]. Different keys, no collision.
  timestamp: 2026-02-25

- hypothesis: ActivityTab never mounts
  evidence: Radix UI TabsContent unmounts inactive tabs by default. ActivityTab mounts when user clicks Activity trigger. userId comes from user.id (valid string) so enabled: true.
  timestamp: 2026-02-25

- hypothesis: backend date_trunc / strftime causes error
  evidence: date_trunc("month", TIMESTAMPTZ) returns a timezone-aware datetime in asyncpg/PostgreSQL. row.month.strftime("%Y-%m") works on timezone-aware datetime. No issue.
  timestamp: 2026-02-25

## Evidence

- timestamp: 2026-02-25
  checked: backend/app/routers/admin/users.py
  found: GET /{user_id}/activity route registered, calls get_user_activity service, returns UserActivityResponse
  implication: Backend route exists and is correctly connected

- timestamp: 2026-02-25
  checked: backend/app/services/admin/users.py - get_user_activity function
  found: Queries ChatMessage and ChatSession grouped by month using date_trunc, builds activity_map, returns {"user_id": user_id, "months": activity_months}. Logic is correct.
  implication: Service is correct

- timestamp: 2026-02-25
  checked: admin-frontend/src/hooks/useUsers.ts - useUserActivity hook
  found: Correctly calls /api/admin/users/${userId}/activity, has enabled: !!userId, throws on !res.ok, returns res.json()
  implication: Hook is correct

- timestamp: 2026-02-25
  checked: admin-frontend/src/components/users/UserDetailTabs.tsx - ActivityTab component
  found: |
    The component only destructures { data, isLoading } from useUserActivity.
    It NEVER checks isError.
    When the API fails: isLoading=false, data=undefined, isError=true (ignored).
    Component falls through to `if (!data || data.months.length === 0)` which renders "No activity data available".
    User sees "blank/empty" with no indication of error. This is indistinguishable from genuinely empty data.
  implication: PRIMARY BUG - error state is silently swallowed

- timestamp: 2026-02-25
  checked: admin-frontend/src/app/api/[...slug]/route.ts - proxy
  found: Correctly proxies /api/* to BACKEND_URL/api/*. No issues.
  implication: Proxy path is correct

- timestamp: 2026-02-25
  checked: admin-frontend/src/types/user.ts
  found: UserActivityResponse and ActivityMonth types match backend schema exactly
  implication: No type mismatch

- timestamp: 2026-02-25
  checked: ran get_user_activity() directly against live PostgreSQL database
  found: |
    asyncpg.exceptions.GroupingError: column "chat_messages.created_at" must appear in the GROUP BY clause or be used in an aggregate function

    SQL generated:
    SELECT date_trunc($1::VARCHAR, chat_messages.created_at) AS month, count(chat_messages.id) AS count
    FROM chat_messages
    WHERE ... GROUP BY date_trunc($4::VARCHAR, chat_messages.created_at) ORDER BY date_trunc($5::VARCHAR, ...)

    SQLAlchemy creates a NEW bind parameter for each occurrence of func.date_trunc("month", col).
    SELECT uses $1, GROUP BY uses $4, ORDER BY uses $5.
    PostgreSQL cannot determine at parse time that $1 = $4 = $5 = 'month', so it treats
    date_trunc($1, created_at) and date_trunc($4, created_at) as potentially different expressions.
    This causes GroupingError: created_at in date_trunc is not directly in GROUP BY or aggregated.
  implication: ROOT CAUSE - needs fix to reuse the same expression in SELECT/GROUP BY/ORDER BY

## Resolution

root_cause: |
  TWO bugs, both now fixed:

  BUG 1 (Backend - Primary): asyncpg.exceptions.GroupingError in get_user_activity().
  SQLAlchemy generates a SEPARATE bind parameter for each occurrence of the literal "month" string in
  func.date_trunc("month", col). The SELECT uses $1, GROUP BY uses $4, ORDER BY uses $5.
  PostgreSQL cannot verify at parse time that $1 == $4 == $5 (all equal "month"), so it treats
  date_trunc($1, col) and date_trunc($4, col) as potentially different expressions. This causes
  GroupingError: column "chat_messages.created_at" must appear in the GROUP BY clause.
  The endpoint throws an unhandled exception and returns HTTP 500 for every request.

  BUG 2 (Frontend - Secondary): ActivityTab silently swallows API errors.
  The component only checked isLoading and data, never isError. A 500 error caused data=undefined
  which fell through to "No activity data available" — indistinguishable from genuinely empty data.

fix: |
  FIX 1 (Backend): Changed GROUP BY and ORDER BY in both queries (messages and sessions) from
  func.date_trunc("month", col) to text("1") — positional reference to the first SELECT column.
  This is valid PostgreSQL syntax and avoids the duplicate bind parameter issue entirely.
  Also added text import to the sqlalchemy imports.
  Files: backend/app/services/admin/users.py

  FIX 2 (Frontend): Added isError + refetch to ActivityTab.
  Destructures isError and refetch from useUserActivity. Shows "Failed to load activity data"
  with a Retry button when isError is true, instead of silently showing the empty state.
  Files: admin-frontend/src/components/users/UserDetailTabs.tsx

  Live verification: running the fixed query against the DB returns:
  - user 5149ad16: 1 month row (2026-02, message_count=2, session_count=1)
  - row.month is datetime(2026-02-01, tzinfo=utc), strftime works correctly

verification: confirmed by human — backend now returns 200 OK, activity tab shows monthly data table
files_changed:
  - backend/app/services/admin/users.py
  - admin-frontend/src/components/users/UserDetailTabs.tsx
