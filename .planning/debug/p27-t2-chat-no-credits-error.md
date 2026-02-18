---
status: diagnosed
trigger: "P27-T2 — Chat UI no out-of-credits error or credit balance display"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Focus

hypothesis: Frontend has no 402 error handling in SSE hook and no credit balance display anywhere
test: Read useSSEStream.ts, ChatInterface.tsx, all frontend source for credit references
expecting: confirmed
next_action: return diagnosis (research-only mode)

## Symptoms

expected: 1) User sees "out of credits" error when sending with zero balance. 2) Credit balance visible in chat UI.
actual: No error shown on 402 response. No credit balance display anywhere in chat UI.
errors: API returns HTTP 402 with structured JSON body { error: "insufficient_credits", message, balance, next_reset }
reproduction: User with zero credits sends a chat message
started: Always broken — feature never implemented in frontend

## Eliminated

- hypothesis: Backend doesn't return 402
  evidence: backend/app/routers/chat.py lines 41-51 explicitly raises HTTP 402 with structured JSON detail
  timestamp: 2026-02-17

- hypothesis: Credits router not registered
  evidence: backend/app/main.py lines 311-312 show credits router is conditionally included
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: frontend/src/hooks/useSSEStream.ts lines 119-121
  found: "if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); }" — the 402 response body (which contains { error, message, balance, next_reset }) is NEVER READ. A generic string error is thrown.
  implication: The structured 402 payload from backend is discarded. The error surface in ChatInterface only gets "HTTP error! status: 402".

- timestamp: 2026-02-17
  checked: frontend/src/components/chat/ChatInterface.tsx lines 592-607
  found: streamError is displayed as a generic "Something went wrong. Please try again." message regardless of error content. No special handling for 402 vs other errors.
  implication: Even if the error message reached the UI, it would be replaced with a hardcoded fallback string.

- timestamp: 2026-02-17
  checked: all frontend/src files for "credit" keyword
  found: Zero occurrences. No credit balance hook, no credit display component, no API call to /api/credits/balance anywhere in the public frontend.
  implication: Credit balance display is completely absent from the public frontend — not just broken, never implemented.

- timestamp: 2026-02-17
  checked: backend/app/routers/credits.py
  found: GET /api/credits/balance endpoint exists and returns CreditBalanceResponse { balance, tier_allocation, reset_policy, next_reset_at, is_low, is_unlimited, display_class }
  implication: Backend is ready; frontend never calls it.

- timestamp: 2026-02-17
  checked: frontend/src/components/sidebar/UserSection.tsx and ChatSidebar.tsx
  found: UserSection shows only name, email, theme toggle, settings link, logout. No credit balance display.
  implication: No credit balance in sidebar — the natural location for this UI element.

- timestamp: 2026-02-17
  checked: frontend/src/components/chat/ChatInterface.tsx handleSend (line 221-227)
  found: handleSend calls startStream directly with no pre-check for credit balance, and no error discrimination on streamError.
  implication: No client-side pre-check either — even a pre-flight credit check before SSE is absent.

## Resolution

root_cause: Two separate gaps — (1) useSSEStream.ts discards the 402 response body and throws a generic error string, and ChatInterface.tsx shows a hardcoded fallback instead of a credit-specific message; (2) no credit balance hook, API call, or UI component exists anywhere in the public frontend.
fix: N/A (research-only mode)
verification: N/A
files_changed: []
