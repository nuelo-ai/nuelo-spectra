---
status: diagnosed
trigger: "P26-T6 — Login lockout shows [object Object] in toast"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T01:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — errorData.detail is an array of objects (Pydantic 422), not a string, causing new Error([{...}]) → error.message = "[object Object]"
test: Traced full backend → frontend error path
expecting: N/A — confirmed
next_action: Return diagnosis

## Symptoms

expected: Clear readable lockout message like "Account locked. Try again in X minutes."
actual: Toast shows "[object Object]" after 5 failed login attempts
errors: "[object Object]" displayed in toast notification
reproduction: Attempt admin login 5 times with wrong credentials (short password under 8 chars triggers it)
started: Unknown — part of UAT phase 26

## Eliminated

- hypothesis: 429 lockout HTTPException detail is an object
  evidence: Backend sends plain string detail="Too many login attempts. Try again later." for 429 — FastAPI wraps in {"detail": "string"}
  timestamp: 2026-02-17T01:00:00Z

- hypothesis: Sonner renders object as [object Object]
  evidence: React would throw "Objects are not valid as a React child" if a plain object were passed; the string "[object Object]" must come from error.message
  timestamp: 2026-02-17T01:00:00Z

- hypothesis: 401 interceptor redirect causes malformed error
  evidence: window.location.href assignment does not abort the async JSON parsing; errorData.detail is always a string for 401 responses
  timestamp: 2026-02-17T01:00:00Z

## Evidence

- timestamp: 2026-02-17T00:10:00Z
  checked: backend/app/routers/admin/auth.py
  found: 429 raises HTTPException(detail="Too many login attempts. Try again later.") — plain string
  implication: 429 response body will be {"detail": "string"} — correct

- timestamp: 2026-02-17T00:15:00Z
  checked: admin-frontend/src/hooks/useAdminAuth.tsx lines 77-82
  found: throw new Error(errorData?.detail || "fallback") — if errorData.detail is an object, new Error(object) sets error.message = "[object Object]"
  implication: The mechanism for [object Object] is new Error(nonStringValue)

- timestamp: 2026-02-17T00:20:00Z
  checked: admin-frontend/src/app/(auth)/login/page.tsx lines 33-35
  found: toast.error(error instanceof Error ? error.message : "Login failed...") — passes error.message directly
  implication: If error.message = "[object Object]", toast shows "[object Object]"

- timestamp: 2026-02-17T00:25:00Z
  checked: backend/app/schemas/admin.py line 13
  found: password: str = Field(..., min_length=8) — Pydantic min_length=8 constraint
  implication: Passwords shorter than 8 chars trigger 422 Unprocessable Entity with detail as array of objects: [{"type": "string_too_short", "loc": ["body","password"], "msg": "String should have at least 8 characters", ...}]

- timestamp: 2026-02-17T00:30:00Z
  checked: Full error propagation path for 422 response
  found: errorData.detail = [{type, loc, msg, input, ctx}] — array of objects, truthy; new Error([{...}]) → error.message = "[object Object]"; toast shows "[object Object]"
  implication: ROOT CAUSE CONFIRMED — Pydantic validation errors produce object-typed detail that is not handled as a string

- timestamp: 2026-02-17T00:35:00Z
  checked: admin-api-client.ts 401 interceptor
  found: 401 clears token and redirects, but also RETURNS the response; useAdminAuth.login() also processes 401 errors — double handling but not the root cause
  implication: Secondary issue: on 401, both redirect AND toast fire, but this doesn't cause [object Object]

- timestamp: 2026-02-17T00:40:00Z
  checked: Actual lockout 429 scenario with correct-length password
  found: 429 detail is "string" → new Error("Too many login attempts. Try again later.") → toast shows readable string
  implication: The [object Object] bug manifests on validation errors (short password), not on actual lockout — but ALSO the lockout message "Too many login attempts. Try again later." is not the expected "Account locked. Try again in X minutes."

## Resolution

root_cause: useAdminAuth.tsx throws new Error(errorData?.detail) without checking if detail is a string. When Pydantic validation fails (422), detail is an array of objects, so new Error([{...}]) sets error.message to "[object Object]". The UAT tester likely used a short password (< 8 chars) triggering this path.

fix: N/A (research only)
verification: N/A
files_changed: []
