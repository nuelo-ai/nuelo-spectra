---
status: diagnosed
trigger: "P29-T6 — Password reset page blocked by auth guard when logged in"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Focus

hypothesis: Auth layout redirects authenticated users to /dashboard, but reset-password lives inside (auth) route group and inherits this layout
test: Read (auth)/layout.tsx and confirm the redirect guard
expecting: Confirmed — redirect fires for ALL pages under (auth) including reset-password
next_action: none — root cause confirmed

## Symptoms

expected: Password reset page loads regardless of login state
actual: Authenticated browser session is redirected away from reset-password page (to /dashboard)
errors: none visible — silent redirect
reproduction: Log in as user A, open a reset-password link emailed to user B (or any reset link)
started: By design (auth layout guards all auth pages) — never worked correctly for reset-password

## Eliminated

- hypothesis: Next.js middleware blocking the route
  evidence: No middleware.ts exists in frontend/src/
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: frontend/src/app/(auth)/layout.tsx
  found: useEffect redirects to /dashboard when isAuthenticated; render returns null while isLoading OR isAuthenticated
  implication: Every page under (auth) group — including reset-password — is blocked for authenticated users

- timestamp: 2026-02-17
  checked: frontend/src/app/(auth)/reset-password/page.tsx
  found: Page is a plain child of (auth) layout; has no auth-override logic
  implication: reset-password inherits the auth guard unconditionally

- timestamp: 2026-02-17
  checked: frontend/src/app/(auth)/ directory
  found: Routes: forgot-password, invite, login, register, reset-password — all share one layout
  implication: reset-password and invite need to be exempt from the authenticated-user redirect; others do not

## Resolution

root_cause: The (auth) route group layout.tsx applies a blanket "redirect authenticated users to /dashboard" guard to ALL pages in the group, including reset-password (and invite), which must be accessible regardless of login state.
fix: not applied (diagnose-only mode)
verification: not applied
files_changed: []
