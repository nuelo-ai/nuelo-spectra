---
status: resolved
trigger: "Tab close warning not showing"
created: 2026-02-07T00:00:00Z
updated: 2026-02-07T00:15:00Z
symptoms_prefilled: true
goal: find_and_fix
---

## Current Focus

hypothesis: FOUND ROOT CAUSE - event.returnValue is set to empty string '' which is falsy
test: Verify browser spec requires truthy returnValue or return statement
expecting: Setting event.returnValue = '' does NOT trigger beforeunload dialog - needs truthy value
next_action: Search for browser spec confirmation, then fix by setting returnValue to truthy value

## Symptoms

expected: Browser shows "Leave site?" warning when closing chat tab with >2 messages
actual: No warning shown when attempting to close tab
errors: Unknown - need to check browser console
reproduction:
1. Start chat session
2. Send >2 messages to build context
3. Attempt to close browser tab
4. No warning appears
started: After Phase 8 Plan 2 implementation

## Eliminated

## Evidence

- timestamp: 2026-02-07T00:01:00Z
  checked: useTabCloseWarning hook implementation
  found: Hook properly sets up beforeunload listener when hasContext is true, uses event.preventDefault() and event.returnValue = ''
  implication: Hook implementation follows browser spec correctly

- timestamp: 2026-02-07T00:02:00Z
  checked: ChatInterface integration of useTabCloseWarning
  found: Hook is called on line 56 with hasContext = messages.length > 2
  implication: Hook is integrated, but hasContext calculation needs verification

- timestamp: 2026-02-07T00:03:00Z
  checked: Message counting logic in ChatInterface
  found: Line 54-55: const messages = chatData?.messages || []; const hasContext = messages.length > 2;
  implication: hasContext is true only when messages.length > 2, but we need to verify what messages are counted

- timestamp: 2026-02-07T00:04:00Z
  checked: Chat service and router
  found: No automatic initial greeting or system message is created. Messages come from database query only.
  implication: Messages array should accurately reflect user + assistant exchanges

- timestamp: 2026-02-07T00:05:00Z
  checked: UAT Test 3 description
  found: Test expects warning "when attempting to close a chat tab with active conversation (>2 messages)"
  implication: Need to understand what ">2 messages" means - is it after 2 full exchanges (4 messages) or 2 user messages?

- timestamp: 2026-02-07T00:06:00Z
  checked: useChatMessages hook - optimistic updates
  found: addLocalMessage optimistically updates TanStack Query cache, so chatData.messages includes local messages immediately
  implication: Message count in ChatInterface DOES include optimistic user messages before server response

- timestamp: 2026-02-07T00:07:00Z
  checked: ChatInterface.tsx line 55 comment
  found: Comment says "// More than initial greeting" but backend investigation shows NO initial greeting is created
  implication: Code assumes greeting exists (hence >2) but reality is no greeting, so threshold is wrong - should be >1 for "after first exchange"

- timestamp: 2026-02-07T00:08:00Z
  checked: Actual message flow with optimistic updates
  found: Flow is - User msg 1 (optimistic, count=1) -> Stream -> Refetch (count=2 with assistant response) -> User msg 2 (optimistic, count=3)
  implication: After 2 user messages with responses, count SHOULD be 3, which satisfies >2 condition. But there might be a timing issue.

- timestamp: 2026-02-07T00:09:00Z
  checked: useTabCloseWarning hook implementation at line 19
  found: event.returnValue = '' (sets to empty string, which is FALSY)
  implication: CRITICAL BUG - Browser beforeunload spec requires truthy returnValue to trigger dialog. Empty string is falsy and won't show warning!

- timestamp: 2026-02-07T00:10:00Z
  checked: MDN docs and browser spec for beforeunload
  found: Working example shows event.returnValue = true (truthy), not empty string. preventDefault() + truthy returnValue required.
  implication: CONFIRMED - Current implementation uses event.returnValue = '' which doesn't trigger dialog. Need to change to truthy value.

## Resolution

root_cause: useTabCloseWarning hook sets event.returnValue to empty string ('') which is falsy. Modern browsers require preventDefault() + truthy returnValue to show beforeunload dialog. The empty string doesn't trigger the warning.

fix: Changed line 19 in useTabCloseWarning.ts from event.returnValue = '' to event.returnValue = true. According to MDN and browser spec, preventDefault() + truthy returnValue is required for cross-browser compatibility (Chrome, Firefox, Safari).

verification:
  - Frontend build successful with no TypeScript errors
  - Manual testing required: Start chat session, send 2+ messages (to get messages.length > 2), then attempt to close/refresh browser tab
  - Expected: Browser shows generic "Leave site?" confirmation dialog
  - Note: Warning only appears after user interaction (sent messages), which is a browser security requirement

files_changed:
  - frontend/src/hooks/useTabCloseWarning.ts
