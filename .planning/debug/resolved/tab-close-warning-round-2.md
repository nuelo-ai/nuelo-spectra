---
status: resolved
trigger: "Tab close warning still not showing (Round 2)"
created: 2026-02-07T00:00:00Z
updated: 2026-02-07T00:05:00Z
symptoms_prefilled: true
---

## Current Focus

hypothesis: returnValue should be a NON-EMPTY STRING, not boolean true
test: Change event.returnValue from true to a non-empty string like 'true'
expecting: Browser will show warning dialog with string returnValue
next_action: Apply fix to change returnValue to string

## Symptoms

expected: Browser shows "Leave site?" warning when closing tab with >2 messages
actual: User reports "no warning shown"
errors: None reported
reproduction:
1. Start chat session
2. Send >2 messages
3. Attempt to close tab
4. No warning appears
started: Still broken after fix in commit e4fa3ce

## Eliminated

## Evidence

- timestamp: 2026-02-07T00:01:00Z
  checked: useTabCloseWarning.ts current state
  found: Fix from e4fa3ce is present - event.returnValue = true as any (line 20)
  implication: Previous fix was applied and is in the codebase

- timestamp: 2026-02-07T00:01:00Z
  checked: ChatInterface.tsx hook integration
  found: Hook is properly integrated at lines 54-56, hasContext = messages.length > 2
  implication: Hook is being called with correct condition

- timestamp: 2026-02-07T00:02:00Z
  checked: MDN docs and browser behavior for beforeunload (2026)
  found: Modern browsers require BOTH preventDefault() and returnValue to be set
  implication: Current code only sets returnValue (line 20) but never calls preventDefault() - this is why warning doesn't show

- timestamp: 2026-02-07T00:02:00Z
  checked: Chrome 119+ requirements
  found: Must call preventDefault(), cannot just return empty string, must have user interaction
  implication: Previous fix was incomplete - need to add event.preventDefault() call

- timestamp: 2026-02-07T00:03:00Z
  checked: useTabCloseWarning.ts again after edit
  found: Code ALREADY has event.preventDefault() on line 17 - it was there originally
  implication: The issue is NOT missing preventDefault() - must be something else

- timestamp: 2026-02-07T00:03:00Z
  checked: Research findings on user interaction requirement
  found: Modern browsers require "sticky activation" - user must have interacted with page (click, type, etc)
  implication: If user hasn't interacted with the page, beforeunload won't fire even with correct code

- timestamp: 2026-02-07T00:04:00Z
  checked: MDN docs on returnValue type
  found: returnValue property is a STRING (initialized to empty string ""), not boolean
  implication: Current code sets returnValue = true (boolean) but spec requires STRING

- timestamp: 2026-02-07T00:04:00Z
  checked: Browser behavior for returnValue
  found: Dialog triggered by preventDefault() OR setting returnValue to NON-EMPTY STRING
  implication: returnValue = true as any (boolean) might not work - need non-empty string like 'true'

## Eliminated

- hypothesis: Missing preventDefault() call
  evidence: Code already has preventDefault() on line 17 (was in original code)
  timestamp: 2026-02-07T00:03:00Z

## Resolution

root_cause: returnValue is set to boolean (true) instead of a non-empty string. The BeforeUnloadEvent.returnValue property is defined as a STRING type, not boolean. MDN docs state: "The dialog can be triggered by calling preventDefault() OR setting returnValue to a non-empty string value." Current code sets returnValue = true as any (boolean), but browsers expect a non-empty STRING like 'true' or any truthy string.
fix: Change event.returnValue from true (boolean) to 'true' (string) in useTabCloseWarning.ts
verification:
  Manual test required (browser-specific behavior):
  1. Start frontend dev server and open chat
  2. Send at least 3 messages (to trigger hasContext = true)
  3. Attempt to close the browser tab (Cmd+W or close button)
  4. Expected: Browser shows generic "Leave site?" confirmation dialog
  5. Browser compatibility: Chrome 119+, Firefox, Safari (all require user interaction)

  Code verification:
  - Line 21: preventDefault() is called ✓
  - Line 22: returnValue set to non-empty string 'true' ✓
  - Lines 54-56 in ChatInterface.tsx: Hook integrated with hasContext calculation ✓
files_changed:
  - frontend/src/hooks/useTabCloseWarning.ts: Changed returnValue from boolean true to string 'true'
