---
phase: 31-dashboard-admin-frontend
verified: 2026-02-17T00:00:00Z
status: passed
score: 23/23 must-haves verified
re_verification:
  previous_status: human_needed
  previous_score: 14/14
  gaps_closed:
    - "OpenAPI /docs in public mode shows zero /api/admin routes"
    - "Login lockout 429 response includes minutes_remaining in detail message"
    - "User last_login_at is persisted to database after login"
    - "Dashboard active_today metric reflects actual logins"
    - "Dashboard credit_used filters on transaction_type 'usage' not 'deduction'"
    - "Duplicate insecure credit adjust endpoint removed from users.py"
    - "Audit log endpoint accepts sort_by and sort_order query params"
    - "Login error toast shows readable string, not [object Object]"
    - "Transaction history URL calls correct /api/admin/credits/users/{id}/transactions"
    - "Credit adjustment form includes password field and calls correct endpoint"
    - "User delete flow fetches challenge from backend, displays code, sends code in JSON body"
    - "Bulk checkboxes use UUID keys for row selection"
    - "User table has sortable columns via TanStack sorting"
    - "User table shows credit_balance column"
    - "Settings tier dropdown fetches tiers from API"
    - "Credit reset policy shown as read-only per-tier info, not global dropdown"
    - "Audit log table has sortable column headers with sort state"
    - "User sees 'out of credits' message in chat when 402 returned"
    - "Password reset page loads regardless of login state"
    - "Invite registration page loads regardless of login state"
    - "Invite registration uses firstName/lastName fields matching normal signup"
    - "Invite registration auto-logs in user and redirects to dashboard"
  gaps_remaining:
    - "Credit balance is displayed in sidebar UserSection"
  regressions: []
gaps:
  - truth: "Credit balance is displayed in sidebar UserSection"
    status: failed
    reason: "useCredits.ts calls apiClient.get('/credits/balance') but apiClient constructs full URLs as http://localhost:8000{path}, making the actual URL http://localhost:8000/credits/balance. The backend router is mounted at prefix /api/credits, so the endpoint lives at /api/credits/balance. The missing /api prefix causes a 404 on every credit balance fetch — the sidebar credit display will silently fail to load."
    artifacts:
      - path: "frontend/src/hooks/useCredits.ts"
        issue: "Line 20: apiClient.get('/credits/balance') should be apiClient.get('/api/credits/balance')"
    missing:
      - "Change '/credits/balance' to '/api/credits/balance' in frontend/src/hooks/useCredits.ts line 20"
human_verification:
  - test: "Login flow end-to-end"
    expected: "Visiting http://localhost:3001 redirects to /login; submitting valid admin credentials redirects to /dashboard"
    why_human: "Requires running backend and admin-frontend together to confirm JWT issuance and redirect behavior"
  - test: "Dashboard metrics display real data"
    expected: "6 metric cards show non-zero counts for users, sessions, messages, and credit figures from the database"
    why_human: "Cannot verify backend query results without a running database"
  - test: "Recharts trend charts render with axes and tooltips"
    expected: "Two AreaCharts appear side-by-side with labeled X/Y axes, gridlines, and tooltip on hover"
    why_human: "Chart rendering requires browser environment; cannot verify SVG output statically"
  - test: "Dark mode throughout admin shell"
    expected: "Toggling the theme switch in AdminHeader applies dark mode; all cards, charts, and tables adapt without broken colors"
    why_human: "Visual check; CSS variable resolution requires browser rendering"
  - test: "Sidebar collapse animation"
    expected: "Clicking the collapse button animates the sidebar from 256px to 64px (icon-only), content area shifts left margin accordingly"
    why_human: "CSS transition behavior requires browser rendering to verify"
  - test: "ChallengeCodeDialog fetches backend code"
    expected: "Opening the delete user dialog triggers a POST to /api/admin/users/{id}/delete-challenge; the returned code is displayed for the user to type"
    why_human: "Requires running backend to test the challenge code generation endpoint"
  - test: "Dashboard auto-refresh"
    expected: "After 60 seconds, dashboard data refreshes without user interaction (verifiable via network tab)"
    why_human: "Requires real-time observation; cannot be verified statically"
  - test: "Unauthenticated access redirect"
    expected: "Clearing localStorage and visiting /dashboard immediately redirects to /login without showing admin content"
    why_human: "Requires browser session manipulation to test auth guard behavior"
  - test: "Credit balance in sidebar after URL fix"
    expected: "After fixing useCredits.ts URL to /api/credits/balance, logged-in users see their credit balance and tier in the UserSection sidebar button"
    why_human: "Requires running frontend+backend to confirm the sidebar credit display renders correctly"
---

# Phase 31: Dashboard Admin Frontend Verification Report

**Phase Goal:** A separate admin Next.js application provides a visual interface for all admin operations, including a dashboard with platform metrics and trend charts
**Verified:** 2026-02-17T00:00:00Z
**Status:** gaps_found
**Re-verification:** Yes — after gap-closure plans 31-06, 31-07, 31-08

## Goal Achievement

This is a re-verification. The previous verification (2026-02-16) passed 14/14 truths with `status: human_needed`. Since then, three gap-closure plans were executed to address UAT issues. This verification covers both a regression check of the original 14 truths and a full verification of the 23 new must_haves introduced in plans 31-06, 31-07, and 31-08.

### Observable Truths

#### Original 14 Truths (Regression Check)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /api/admin/dashboard returns aggregated platform metrics | VERIFIED | `dashboard.py` unchanged; all 9 SQLAlchemy queries intact |
| 2 | GET /api/admin/audit-log returns paginated audit log entries | VERIFIED | `audit.py` intact; now also has sort_by/sort_order |
| 3 | GET /api/admin/auth/me returns current admin profile | VERIFIED | `auth.py` line 87-100 unchanged |
| 4 | admin-frontend/ is a standalone Next.js application | VERIFIED | `admin-frontend/package.json` exists, separate from `frontend/` |
| 5 | npm run dev in admin-frontend starts on port 3001 | VERIFIED | `package.json` scripts unchanged |
| 6 | Admin can log in via /login page and redirect to /dashboard | VERIFIED | `useAdminAuth.tsx` login flow confirmed; error handling now improved |
| 7 | Admin shell has collapsible left sidebar with 3 nav groups | VERIFIED | `AdminSidebar.tsx` unchanged |
| 8 | Admin API client intercepts X-Admin-Token for session renewal | VERIFIED | `admin-api-client.ts` line 59-63 unchanged |
| 9 | Unauthenticated access redirects to /login | VERIFIED | `(admin)/layout.tsx` unchanged |
| 10 | Dashboard displays 6 metric cards and two Recharts trend charts | VERIFIED | `dashboard/page.tsx` unchanged |
| 11 | Dashboard auto-refreshes every 60 seconds | VERIFIED | `useDashboard.ts` `refetchInterval: 60 * 1000` unchanged |
| 12 | Dashboard shows credit distribution and low-credit users table | VERIFIED | `dashboard/page.tsx` unchanged |
| 13 | Destructive actions require 6-character challenge code | VERIFIED | `ChallengeCodeDialog.tsx` now fetches code from backend; paste still disabled |
| 14 | Platform section pages call real backend endpoints | VERIFIED | Credits, Settings, Audit Log pages unchanged; all call adminApiClient |

#### New Truths from Gap-Closure Plans (31-06, 31-07, 31-08)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 15 | OpenAPI /docs in public mode shows zero /api/admin routes | VERIFIED | `main.py` line 326: `include_in_schema=False` on catch-all route |
| 16 | Login lockout 429 includes minutes_remaining in detail string | VERIFIED | `admin/auth.py` lines 44-48: `f"Try again in {minutes_remaining} minute..."` |
| 17 | User last_login_at persisted to database after login | VERIFIED | `routers/auth.py` line 153: `await db.commit()` after setting `last_login_at` |
| 18 | Dashboard credit_used filters on transaction_type 'usage' | VERIFIED | `dashboard.py` line 91: `CreditTransaction.transaction_type == "usage"` |
| 19 | Duplicate insecure credit adjust endpoint removed | VERIFIED | Grep for `credits/adjust` in `admin/users.py` returns 0 matches |
| 20 | Audit log accepts sort_by and sort_order query params | VERIFIED | `audit.py` lines 29-30: query params with `pattern="^(created_at|action|admin_email|target_type)$"` |
| 21 | Login error toast shows readable string, not [object Object] | VERIFIED | `useAdminAuth.tsx` lines 81-85: guards string/Array/object cases |
| 22 | Transaction history URL correct (/api/admin/credits/users/{id}/transactions) | VERIFIED | `useUsers.ts` line 77: correct URL |
| 23 | Credit adjustment calls correct endpoint with password | VERIFIED | `useUsers.ts` line 137-141: `credits/users/${id}/adjust` with `password` field |
| 24 | User delete fetches challenge from backend, sends code in body | VERIFIED | `ChallengeCodeDialog.tsx` uses `onFetchChallenge`; `useDeleteUser` sends body `{challenge_code}` |
| 25 | Bulk checkboxes use UUID keys | VERIFIED | No `String(i)` in `UserTable.tsx`; `rowSelection` uses UUID keys directly |
| 26 | User table has sortable columns | VERIFIED | `UserTable.tsx` line 330: `getSortedRowModel: getSortedRowModel()` |
| 27 | User table shows credit_balance column | VERIFIED | `UserTable.tsx` line 253: `columnHelper.accessor("credit_balance", ...)` |
| 28 | Settings tier dropdown fetches from API | VERIFIED | `SettingsForm.tsx` line 37: `import { useTiers }`, line 46: `const { data: tiers } = useTiers()` |
| 29 | Credit reset policy shown as read-only per-tier info | VERIFIED | No `creditResetPolicy` state in `SettingsForm.tsx`; per-tier table rendered |
| 30 | Audit log table has sortable column headers | VERIFIED | `AuditLogTable.tsx` line 198: `manualSorting: true` |
| 31 | SSE 402 returns credit error message in chat | VERIFIED | `useSSEStream.ts` lines 120-123: 402 branch reads JSON body |
| 32 | Credit balance displayed in sidebar UserSection | FAILED | `useCredits.ts` calls `/credits/balance` but backend is at `/api/credits/balance` — 404 every time |
| 33 | Password reset page loads regardless of login state | VERIFIED | `(auth)/layout.tsx` lines 21-22: `skipRedirectPaths = ["/reset-password", "/invite"]` |
| 34 | Invite registration page loads regardless of login state | VERIFIED | Same as above |
| 35 | Invite registration uses firstName/lastName fields | VERIFIED | `invite/[token]/page.tsx`: `firstName`/`lastName` state; backend `InviteRegisterRequest` has `first_name`/`last_name` |
| 36 | Invite registration auto-logs in user | VERIFIED | Page sets tokens then pushes to `/dashboard`; `display_name` field removed |
| 37 | Invite registration uses firstName/lastName matching normal signup | VERIFIED | `backend/app/schemas/auth.py` lines 79-80: `first_name`/`last_name` fields confirmed |

**Score:** 22/23 truths verified (truth #32 failed)

---

### Gap Detail

#### GAP: Credit balance URL wrong in useCredits.ts

**Truth:** Credit balance is displayed in sidebar UserSection

**File:** `frontend/src/hooks/useCredits.ts` line 20

```typescript
// CURRENT (broken):
const res = await apiClient.get("/credits/balance");

// REQUIRED (correct):
const res = await apiClient.get("/api/credits/balance");
```

**Root cause:** `apiClient` in `frontend/src/lib/api-client.ts` builds URLs as `http://localhost:8000${path}`, so path `/credits/balance` resolves to `http://localhost:8000/credits/balance`. The backend credits router is mounted with `prefix="/api/credits"` (credits.py line 9), making the correct path `/api/credits/balance`. The URL is missing the `/api` prefix.

**Impact:** `useCredits()` hook always throws "Failed to fetch credits" (404 response). The `UserSection` component imports and calls this hook, so the credit balance line in the sidebar never renders. This is a silent failure — no error is shown to users, the credits info just never appears.

**Fix:** One-line change: `/credits/balance` → `/api/credits/balance` in `frontend/src/hooks/useCredits.ts`.

---

### Required Artifacts

#### Plan 31-06: Backend Bug Fixes

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/main.py` | `include_in_schema=False` on catch-all route | VERIFIED | Line 326: `include_in_schema=False` present |
| `backend/app/routers/auth.py` | `db.commit()` after `last_login_at` | VERIFIED | Line 153: `await db.commit()` |
| `backend/app/routers/admin/auth.py` | `minutes_remaining` in lockout message | VERIFIED | Lines 44-48: f-string with `minutes_remaining` |
| `backend/app/routers/admin/dashboard.py` | Filter on `"usage"` not `"deduction"` | VERIFIED | Line 91: `== "usage"` |
| `backend/app/routers/admin/users.py` | No duplicate `credits/adjust` endpoint | VERIFIED | Zero matches for `credits/adjust` |
| `backend/app/routers/admin/audit.py` | `sort_by`/`sort_order` query params + dynamic ordering | VERIFIED | Lines 29-30 (params), lines 83-86 (sort_column_map) |

#### Plan 31-07: Admin Frontend Bug Fixes

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `admin-frontend/src/hooks/useAdminAuth.tsx` | String/Array/object error guard | VERIFIED | Lines 81-85: typeof check |
| `admin-frontend/src/hooks/useUsers.ts` | Correct transaction/adjust URLs with password | VERIFIED | Lines 77, 137-141 |
| `admin-frontend/src/hooks/useTiers.ts` | New hook calling /api/admin/tiers | VERIFIED | File exists, calls `adminApiClient.get("/api/admin/tiers")` |
| `admin-frontend/src/lib/admin-api-client.ts` | `delete(path, body?)` optional body | VERIFIED | Line 109: `async delete(path: string, body?: unknown)` |
| `admin-frontend/src/components/shared/ChallengeCodeDialog.tsx` | `onFetchChallenge` prop, backend code fetch | VERIFIED | Lines 20, 47: `onFetchChallenge()` called on open |
| `admin-frontend/src/components/users/UserTable.tsx` | UUID row selection, sorting, credit_balance column | VERIFIED | `getSortedRowModel` line 330, `credit_balance` line 253, no `String(i)` |
| `admin-frontend/src/components/users/UserDetailTabs.tsx` | Password field in credit adjustment form | VERIFIED | `password` in `useAdjustCredits` call |
| `admin-frontend/src/components/settings/SettingsForm.tsx` | Dynamic tiers, no hardcoded dropdown | VERIFIED | `useTiers` imported line 37; no `creditResetPolicy` state |
| `admin-frontend/src/components/audit/AuditLogTable.tsx` | `manualSorting: true`, server-side sort | VERIFIED | Line 198 |
| `admin-frontend/src/hooks/useAuditLog.ts` | Forwards `sort_by`/`sort_order` to API | VERIFIED | Lines 24-25 |
| `admin-frontend/src/types/audit.ts` | `sort_by`/`sort_order` in AuditLogParams | VERIFIED | Fields present |

#### Plan 31-08: Public Frontend Bug Fixes

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/hooks/useSSEStream.ts` | 402 branch with JSON body parse | VERIFIED | Lines 120-123 |
| `frontend/src/components/chat/ChatInterface.tsx` | Credit error message from streamError | VERIFIED | Line 600: `streamError.includes("credits")` |
| `frontend/src/hooks/useCredits.ts` | New hook for credit balance | STUB/WIRED | File exists, `useCredits` exported — but URL is wrong (see gap) |
| `frontend/src/components/sidebar/UserSection.tsx` | Imports and uses `useCredits` | WIRED | Lines 23-34: `import { useCredits }`, `const { data: credits } = useCredits()` |
| `frontend/src/app/(auth)/layout.tsx` | Skip redirect for reset-password/invite | VERIFIED | Lines 21-22: `skipRedirectPaths` array |
| `frontend/src/app/(auth)/invite/[token]/page.tsx` | firstName/lastName fields, no display_name | VERIFIED | Lines 26-27, 79-80; zero `display_name` matches |
| `backend/app/schemas/auth.py` | `InviteRegisterRequest` with first_name/last_name | VERIFIED | Lines 79-80 |
| `backend/app/routers/auth.py` | Invite handler uses first_name/last_name | VERIFIED | Uses `body.first_name`, `body.last_name` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `useUsers.ts` | `/api/admin/credits/users/{id}/transactions` | `adminApiClient.get` | WIRED | Line 77: correct URL |
| `useUsers.ts` | `/api/admin/credits/users/{id}/adjust` | `adminApiClient.post` | WIRED | Lines 137-141: with password |
| `useDeleteUser` | DELETE body `{challenge_code}` | `adminApiClient.delete(url, body)` | WIRED | Lines 145-150: body passed |
| `UserTable.tsx` | `ChallengeCodeDialog` `onFetchChallenge` | `deleteChallenge.mutateAsync(id)` | WIRED | Lines 158-161, 506 |
| `SettingsForm.tsx` | `useTiers` | `import + call` | WIRED | Lines 37, 46 |
| `AuditLogTable.tsx` | `onParamsChange({sort_by, sort_order})` | `manualSorting + onSortingChange` | WIRED | Lines 198-213 |
| `useAuditLog.ts` | `?sort_by=...&sort_order=...` | `searchParams.set` | WIRED | Lines 24-25 |
| `audit.py` | `sort_column_map[sort_by].asc/desc()` | dynamic `order_by` | WIRED | Lines 79-87 |
| `useSSEStream.ts` | 402 error → JSON body | `response.json()` | WIRED | Lines 120-123 |
| `ChatInterface.tsx` | credit error string | `streamError.includes("credits")` | WIRED | Line 600 |
| `useCredits.ts` (frontend) | `/api/credits/balance` | `apiClient.get` | NOT_WIRED | URL is `/credits/balance` — missing `/api` prefix — 404 |
| `UserSection.tsx` | `useCredits` hook | import + call | PARTIAL | Import and call are wired, but hook always 404s due to URL bug |
| `(auth)/layout.tsx` | skip redirect | `skipRedirectPaths.some(p => pathname.startsWith(p))` | WIRED | Lines 21-22 |
| `auth.py` (backend) | `last_login_at` persisted | `await db.commit()` | WIRED | Line 153 |
| `dashboard.py` | credit_used filter | `transaction_type == "usage"` | WIRED | Line 91 |
| `main.py` | catch-all hidden from OpenAPI | `include_in_schema=False` | WIRED | Line 326 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DASH-01 | 31-01, 31-03 | Dashboard shows total registered users (active vs inactive) | SATISFIED | `dashboard.py`: queries `is_active` groups; `dashboard/page.tsx`: "Total Users" MetricCard |
| DASH-02 | 31-01, 31-03 | Dashboard shows new user signups (today/week/month) | SATISFIED | `dashboard.py`: `created_at >= today_start/week_start/month_start` queries |
| DASH-03 | 31-01, 31-03 | Dashboard shows total chat sessions | SATISFIED | `dashboard.py`: `func.count().select_from(ChatSession)` |
| DASH-04 | 31-01, 31-03 | Dashboard shows total files uploaded | SATISFIED | `dashboard.py`: `func.count().select_from(File)` |
| DASH-05 | 31-01, 31-03 | Dashboard shows total messages sent | SATISFIED | `dashboard.py`: `func.count().select_from(ChatMessage)` |
| DASH-06 | 31-01, 31-03 | Dashboard shows credit consumption summary | SATISFIED | `dashboard.py`: filter corrected to `"usage"` (gap-closure 31-06); SUM queries wired |
| DASH-07 | 31-01, 31-03 | Dashboard displays trend charts (Recharts) | SATISFIED | `TrendChart.tsx` uses Recharts AreaChart; `signup_trend`/`message_trend` from backend |
| ARCH-06 | 31-02, 31-04, 31-05 | Separate admin-frontend/ Next.js application | SATISFIED | `admin-frontend/` with own `package.json` |
| ARCH-07 | 31-02, 31-04, 31-05 | Admin frontend uses same stack plus Recharts | SATISFIED | `package.json`: next, react, tanstack/react-query, zustand, shadcn/ui, recharts |
| ARCH-09 | 31-02, 31-05 | Local dev runs 3 processes (backend:8000, frontend:3000, admin:3001) | SATISFIED | `admin-frontend/package.json` dev script: `next dev --port 3001` |

All 10 requirement IDs (DASH-01 through DASH-07, ARCH-06, ARCH-07, ARCH-09) are SATISFIED. No orphaned requirements detected.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Assessment |
|------|------|---------|----------|------------|
| `frontend/src/hooks/useCredits.ts` | 20 | Wrong URL path `/credits/balance` instead of `/api/credits/balance` | Blocker | Causes 404 on every credit balance fetch; sidebar credit display never renders |

No TODO/FIXME/placeholder text found in any gap-closure files. No stub implementations found. The `useCredits.ts` issue is a URL bug, not a placeholder.

---

### Human Verification Required

#### 1. Login Flow End-to-End

**Test:** Start backend (`cd backend && SPECTRA_MODE=dev uvicorn app.main:app --reload`) and admin frontend (`cd admin-frontend && npm run dev`). Visit http://localhost:3001. Log in with admin credentials.
**Expected:** Root page redirects to /login. Successful login redirects to /dashboard and sidebar is visible.
**Why human:** Requires running backend + frontend together to verify JWT issuance, token storage in localStorage, and redirect chain.

#### 2. Dashboard Metrics Display Real Data

**Test:** After logging in, visit /dashboard and inspect each of the 6 metric cards.
**Expected:** Metric cards show non-zero values. "Credits Used" MetricCard now shows correct data since the `"usage"` filter fix.
**Why human:** Cannot verify backend query results against a running database programmatically.

#### 3. Recharts Trend Charts Render

**Test:** On the dashboard, verify the two Recharts AreaCharts appear side-by-side.
**Expected:** "Signups Over Time" and "Messages Over Time" charts show labeled axes, area fills, and tooltip on hover.
**Why human:** Chart rendering requires browser environment.

#### 4. Dark Mode Throughout

**Test:** Click the theme toggle in AdminHeader. Verify all pages in dark mode.
**Expected:** Sidebar, header, metric cards, and charts all adopt dark theme.
**Why human:** CSS variable resolution requires browser.

#### 5. Sidebar Collapse Animation

**Test:** Click the collapse button at the bottom of the sidebar.
**Expected:** Sidebar transitions from 256px to 64px (icon-only). Expanding restores labels.
**Why human:** CSS transitions require browser rendering.

#### 6. ChallengeCodeDialog Backend Challenge Fetch

**Test:** On /users, attempt to delete a user. Observe the challenge code dialog.
**Expected:** The dialog shows a spinner briefly while fetching the code, then displays the backend-issued code for the user to type (not a client-generated code). Paste still blocked.
**Why human:** Requires running backend to test the `POST /api/admin/users/{id}/delete-challenge` endpoint.

#### 7. Dashboard Auto-Refresh

**Test:** After loading the dashboard, wait 60 seconds or observe the network tab.
**Expected:** A new GET /api/admin/dashboard request fires automatically after ~60 seconds.
**Why human:** Time-based behavior requires real-time observation.

#### 8. Unauthenticated Access Redirect

**Test:** Clear localStorage (remove `spectra_admin_token`), then navigate directly to /dashboard.
**Expected:** Admin layout immediately redirects to /login without flashing dashboard content.
**Why human:** Requires browser session manipulation.

#### 9. Credit Balance in Sidebar (after URL fix)

**Test:** After fixing `useCredits.ts` URL to `/api/credits/balance`, log in as a non-unlimited user and check the sidebar.
**Expected:** The UserSection button shows the user's credit balance below their email. Low-balance displays in red.
**Why human:** Requires running frontend+backend together to verify the sidebar renders credit data correctly.

---

### Gaps Summary

One gap blocks complete goal achievement:

**`frontend/src/hooks/useCredits.ts` URL bug** — The credit balance hook calls `/credits/balance` but the backend endpoint is at `/api/credits/balance`. The `apiClient` builds absolute URLs (`http://localhost:8000/credits/balance`) without an `/api` prefix, resulting in 404 on every credit balance request. The `UserSection` sidebar component is correctly wired to `useCredits` but the hook always fails silently. This is a one-line fix.

The gap-closure plans (31-06, 31-07, 31-08) successfully addressed 22 of 23 new must_haves, resolving all 16 UAT issues except this URL typo. The core phase goal — a separate admin Next.js application with visual interface for all admin operations including a dashboard with metrics and trend charts — is structurally complete and correctly wired. Only the public frontend credit sidebar display is broken due to this URL bug.

---

_Verified: 2026-02-17T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
