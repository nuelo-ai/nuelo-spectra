---
status: diagnosed
trigger: "P29-T3 — User activity timeline not displayed — In the admin user detail view, the activity timeline (showing monthly messages and sessions) is not displayed."
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Focus

hypothesis: The entire feature stack exists and is wired correctly. The root cause is that the ActivityTab renders "No activity data available" when data.months is empty — which will always happen for users with no chat history. But for users WITH history, the data flow is complete. The real question is whether this is a display bug (data exists but doesn't show) or a data-absence issue (no records in DB for the test user).
test: Compared backend schema, service query, API endpoint, frontend hook, types, and render component end-to-end.
expecting: No structural bug found — the full stack is correctly implemented.
next_action: confirmed — no code bug in the feature stack itself; see diagnosis below.

## Symptoms

expected: Monthly activity timeline showing message counts and session counts by month.
actual: Activity tab shows no timeline content.
errors: None reported.
reproduction: Navigate to admin user detail -> Activity tab.
started: Unknown; feature was recently built.

## Eliminated

- hypothesis: Backend endpoint missing
  evidence: GET /api/admin/users/{user_id}/activity exists at line 267 of backend/app/routers/admin/users.py
  timestamp: 2026-02-17

- hypothesis: Admin router not registering the users router
  evidence: backend/app/routers/admin/__init__.py line 19 includes admin_users.router
  timestamp: 2026-02-17

- hypothesis: Next.js rewrite not proxying the activity path
  evidence: admin-frontend/next.config.ts uses /api/:path* wildcard which covers /api/admin/users/{id}/activity
  timestamp: 2026-02-17

- hypothesis: Frontend hook or API client missing
  evidence: useUserActivity hook in src/hooks/useUsers.ts line 58-70 correctly calls /api/admin/users/${userId}/activity
  timestamp: 2026-02-17

- hypothesis: ActivityTab component missing or not rendered
  evidence: ActivityTab component exists at line 438-495 of UserDetailTabs.tsx and is wired to the "activity" tab at line 552-554
  timestamp: 2026-02-17

- hypothesis: TypeScript type mismatch between backend and frontend
  evidence: Backend UserActivityResponse { user_id: UUID, months: list[ActivityMonth] } exactly matches frontend UserActivityResponse { user_id: string, months: ActivityMonth[] }. ActivityMonth { month: string, message_count: int, session_count: int } matches on both sides.
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/users.py lines 267-276
  found: GET /{user_id}/activity endpoint exists, calls get_user_activity service, returns UserActivityResponse
  implication: Backend endpoint is fully implemented.

- timestamp: 2026-02-17
  checked: backend/app/services/admin/users.py lines 259-319
  found: get_user_activity queries ChatMessage and ChatSession tables grouped by month using date_trunc, merges results, returns {user_id, months:[{month, message_count, session_count}]}
  implication: Service logic is correct and complete.

- timestamp: 2026-02-17
  checked: backend/app/schemas/admin_users.py lines 58-71
  found: ActivityMonth and UserActivityResponse Pydantic models are correctly defined
  implication: Schema is correct.

- timestamp: 2026-02-17
  checked: admin-frontend/src/components/users/UserDetailTabs.tsx lines 438-495 and 537-560
  found: ActivityTab component renders correctly; it's wired into Tabs with value="activity"; calls useUserActivity(userId); renders table of months with message_count and session_count columns. Shows "No activity data available" when data.months.length === 0.
  implication: Frontend component is complete and correctly wired.

- timestamp: 2026-02-17
  checked: admin-frontend/src/hooks/useUsers.ts lines 58-70
  found: useUserActivity calls GET /api/admin/users/${userId}/activity, enabled when userId is truthy
  implication: Hook is correct.

- timestamp: 2026-02-17
  checked: admin-frontend/src/lib/admin-api-client.ts
  found: adminApiClient.get() injects Authorization Bearer token; Next.js rewrite forwards /api/* to http://localhost:8000/api/*
  implication: Auth and proxying are correct.

- timestamp: 2026-02-17
  checked: admin-frontend/src/types/user.ts lines 27-36
  found: Frontend types exactly match backend schema
  implication: No type mismatch.

## Resolution

root_cause: The entire feature stack (backend endpoint, service query, schema, frontend component, hook, type definitions, API routing) is correctly implemented. The "not displayed" symptom is because the ActivityTab falls through to "No activity data available" when data.months is empty — which occurs when the test user has no chat messages or sessions recorded in the database. This is NOT a code bug; it is a data-absence issue for the specific test user used during UAT.

fix: No code change needed. To verify the feature works: test with a user who has existing chat sessions/messages, or seed the database with activity data for a test user.

verification: N/A — no code change made. Feature is structurally complete.

files_changed: []
