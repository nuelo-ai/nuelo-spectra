---
status: diagnosed
trigger: "P30-T4 — Invite registration issues (auth guard, no auto-login, Display Name)"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:01:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: All three bugs confirmed
test: Read layout.tsx, invite page, useAuth hook, backend endpoint, schema
expecting: Clear root causes identified
next_action: Return diagnosis

## Symptoms

expected:
  1. Invite registration page loads regardless of login state
  2. After completing registration, user is automatically logged in
  3. Form fields match normal registration (First Name, Last Name)

actual:
  1. Redirected to /dashboard when logged in (auth guard)
  2. Redirected to login page after registration (no auto-login)
  3. Shows 'Display Name' field instead of 'First Name'/'Last Name'

errors: none reported
reproduction: visit /invite/[token] while logged in; complete invite registration
started: unknown

## Eliminated

## Evidence

- timestamp: 2026-02-17T00:01:00Z
  checked: frontend/src/app/(auth)/layout.tsx
  found: |
    AuthLayout wraps ALL routes under (auth)/ group, including /invite/[token].
    Lines 19-28: if (!isLoading && isAuthenticated) { router.push("/dashboard"); }
    Line 26: if (isLoading || isAuthenticated) { return null; }
    The invite page is nested under (auth)/ route group — it inherits this layout.
  implication: Any authenticated user visiting /invite/[token] is immediately redirected to /dashboard. This is Issue 1.

- timestamp: 2026-02-17T00:01:00Z
  checked: frontend/src/app/(auth)/invite/[token]/page.tsx lines 86-88
  found: |
    After successful registration:
      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      router.push("/");
    setTokens() stores tokens in localStorage correctly.
    router.push("/") goes to app/page.tsx which redirects to /sessions/new.
    /sessions/new is in (dashboard)/ layout which checks isAuthenticated.
    But isAuthenticated in AuthContext is derived from user !== null (line 154 of useAuth.tsx).
    setTokens() stores the token in localStorage but does NOT call setUser() in AuthContext.
    The AuthContext user state remains null after setTokens(), so isAuthenticated = false.
    Dashboard layout then redirects to /login.
  implication: Token is stored but AuthContext state is never updated. Dashboard guard sees isAuthenticated=false and redirects to /login. This is Issue 2.

- timestamp: 2026-02-17T00:01:00Z
  checked: frontend/src/app/(auth)/invite/[token]/page.tsx lines 135-145
  found: |
    Single field: displayName (state), Label "Display name", Input id="displayName"
    Body sent to API: { token, display_name: displayName.trim(), password }
  implication: Invite form uses a single "Display name" field instead of separate "First name" / "Last name" fields. This is Issue 3.

- timestamp: 2026-02-17T00:01:00Z
  checked: frontend/src/app/(auth)/register/page.tsx lines 89-112
  found: |
    Two fields in a grid: firstName (Label "First name (optional)") + lastName (Label "Last name (optional)")
    Body sent via signup(): { email, password, first_name, last_name }
  implication: Normal registration uses split first/last name. Invite registration does not match.

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/schemas/auth.py lines 75-80
  found: |
    InviteRegisterRequest: token (str), display_name (str), password (str)
    Backend endpoint uses body.display_name and stuffs it into first_name, last_name=None.
  implication: Backend schema also uses display_name single field. Both frontend and backend need to be updated together for Issue 3.

- timestamp: 2026-02-17T00:01:00Z
  checked: frontend/src/hooks/useAuth.tsx line 154
  found: |
    isAuthenticated: user !== null
    setTokens() in api-client.ts only writes to localStorage — it does not touch AuthContext user state.
    After invite-register, tokens are in localStorage but user is still null in context.
  implication: Confirms Issue 2 mechanism. Fix requires calling /auth/me and setUser() after setTokens(), mirroring what login() and signup() do in useAuth.tsx lines 78-85 / 110-118.

## Resolution

root_cause:
  issue_1: "The invite page (/invite/[token]) is nested under the (auth)/ route group, which applies AuthLayout to all children. AuthLayout unconditionally redirects authenticated users to /dashboard."
  issue_2: "After invite-register, the page calls setTokens() (localStorage only) but never calls /auth/me or updates AuthContext user state. isAuthenticated remains false (user === null), causing the dashboard layout to redirect to /login."
  issue_3: "The invite registration form uses a single 'displayName' field instead of separate 'firstName'/'lastName' fields. The backend schema (InviteRegisterRequest) also uses display_name. Both frontend and backend need updating."

fix: not applied (diagnose-only mode)
verification: not applicable
files_changed: []
