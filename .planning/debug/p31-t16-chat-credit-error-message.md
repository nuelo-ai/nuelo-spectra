---
status: diagnosed
trigger: "When a user with zero credits sends a chat message, the frontend shows a generic 'Error: Something went wrong. Please try again.' instead of a specific 'out of credits' error message."
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — useSSEStream.ts reads errorBody.detail (an object) and passes it directly to new Error(), producing "[object Object]" instead of the message string
test: traced data flow from backend 402 response through frontend error handling
expecting: confirmed
next_action: return diagnosis

## Symptoms

expected: When user has zero credits and sends a chat message, frontend shows a specific "out of credits" or "insufficient credits" error message
actual: Frontend shows generic "Error: Something went wrong. Please try again."
errors: Generic error toast instead of credit-specific message
reproduction: Set user credits to 0, attempt to send a chat message
started: Since Phase 27 credit system was implemented

## Eliminated

- hypothesis: Backend does not return 402
  evidence: backend/app/routers/chat.py line 41 raises HTTPException with status_code=402 and a structured detail dict containing error, message, balance, next_reset
  timestamp: 2026-02-17

- hypothesis: Frontend has no 402 handling at all
  evidence: useSSEStream.ts lines 119-123 explicitly checks response.status === 402 and reads errorBody.detail
  timestamp: 2026-02-17

- hypothesis: ChatInterface has no credit check in error display
  evidence: ChatInterface.tsx line 600 checks streamError.includes("credits") — the check exists, but it never matches because streamError is "[object Object]"
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/routers/chat.py lines 40-51
  found: When credits are insufficient, raises HTTPException(status_code=402, detail={"error": "insufficient_credits", "message": deduction.error_message, "balance": ..., "next_reset": ...}). FastAPI serializes this as JSON: {"detail": {"error": "insufficient_credits", "message": "...", ...}}
  implication: The 402 response body contains a nested object under the "detail" key

- timestamp: 2026-02-17
  checked: backend/app/services/credit.py lines 81-89
  found: error_message is set to "You're out of credits. Credits reset on {date}." or "You're out of credits." — both contain the word "credits"
  implication: If the message string reaches the frontend intact, the streamError.includes("credits") check on ChatInterface line 600 would pass

- timestamp: 2026-02-17
  checked: frontend/src/hooks/useSSEStream.ts lines 119-124
  found: |
    if (response.status === 402) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.detail || "You have run out of credits. Please contact your administrator.");
    }
  The problem: errorBody.detail is a JavaScript OBJECT {error: "insufficient_credits", message: "...", ...}, not a string.
  new Error(someObject) calls someObject.toString() which produces "[object Object]".
  implication: streamError in ChatInterface becomes "[object Object]" — it does NOT contain "credits", so the fallback "Something went wrong. Please try again." is shown instead

- timestamp: 2026-02-17
  checked: frontend/src/components/chat/ChatInterface.tsx lines 600-602
  found: |
    content: streamError.includes("credits")
      ? streamError
      : "Something went wrong. Please try again.",
  implication: The credit-message display path works correctly IF streamError contains "credits". The bug is upstream in useSSEStream.ts where the message is extracted

## Resolution

root_cause: In useSSEStream.ts line 122, errorBody?.detail is a JavaScript object (not a string), so passing it to new Error() yields "[object Object]" instead of the actual credit error message. The fix is to extract the nested message string: errorBody?.detail?.message instead of errorBody?.detail.

fix: N/A (research-only mode)

verification: N/A

files_changed: []

---

## Summary for Fix

**File to change:** `frontend/src/hooks/useSSEStream.ts`

**Line 122 — current:**
```typescript
throw new Error(errorBody?.detail || "You have run out of credits. Please contact your administrator.");
```

**Line 122 — fixed:**
```typescript
const detail = errorBody?.detail;
const creditMessage = typeof detail === "string" ? detail : detail?.message;
throw new Error(creditMessage || "You have run out of credits. Please contact your administrator.");
```

Or concisely:
```typescript
throw new Error(errorBody?.detail?.message || errorBody?.detail || "You have run out of credits. Please contact your administrator.");
```

This ensures the human-readable message string (e.g. "You're out of credits. Credits reset on February 28, 2026.") is passed to the Error constructor, not the entire detail object. With this fix, `streamError` will contain "credits" and ChatInterface line 600 will display the specific message instead of the generic fallback.
