---
phase: 06-frontend-ui-interactive-data-cards
plan: 04
subsystem: frontend-chat
status: complete
completed: 2026-02-04
duration: 2min

tags:
  - chat-interface
  - sse-streaming
  - real-time-ui
  - react-hooks

requires:
  phases: [06-01]
  context: [JWT auth, API client, TanStack Query setup]

provides:
  infrastructure: [SSE streaming hook, chat message query]
  components: [ChatInterface, ChatInput, ChatMessage, TypingIndicator]
  patterns: [POST-based SSE, optimistic UI updates, auto-scroll]

affects:
  - 06-05: Data Cards will integrate into ChatInterface for visualization

tech-stack:
  added:
    - react-textarea-autosize: auto-expanding textarea
  patterns:
    - POST-based SSE streaming with fetch + ReadableStream
    - TanStack Query for chat history with optimistic updates
    - AbortController for stream cleanup

key-files:
  created:
    - frontend/src/hooks/useSSEStream.ts
    - frontend/src/hooks/useChatMessages.ts
    - frontend/src/components/chat/ChatInterface.tsx
    - frontend/src/components/chat/ChatInput.tsx
    - frontend/src/components/chat/ChatMessage.tsx
    - frontend/src/components/chat/TypingIndicator.tsx
    - frontend/src/components/ui/textarea.tsx
    - frontend/src/components/ui/separator.tsx
    - frontend/src/components/ui/avatar.tsx

decisions:
  - decision: "POST-based SSE with fetch + ReadableStream instead of EventSource"
    rationale: "EventSource doesn't support POST body; need to send user message in request body"
    impact: "Manual SSE parsing required but allows proper request/response model"
  - decision: "Optimistic UI updates for user messages"
    rationale: "Instant visual feedback before server persistence"
    impact: "useAddLocalMessage updates query cache immediately on send"
  - decision: "Invalidate + refetch on stream completion"
    rationale: "Server-side persistence happens atomically after stream completes"
    impact: "Fresh data from server after AI response finishes"
  - decision: "AbortController for stream cleanup"
    rationale: "Prevent memory leaks and abandoned streams"
    impact: "Automatic cleanup on component unmount or new stream start"
  - decision: "Status messages mapped from event types"
    rationale: "User-friendly agent phase descriptions (not raw node names)"
    impact: "Displays 'Generating code...' instead of 'coding_started'"
---

# Phase 06 Plan 04: Chat Interface with SSE Streaming Summary

**One-liner:** POST-based SSE streaming, auto-expanding chat input, typing indicator, and character-by-character text rendering

---

## What Was Built

### SSE Streaming Infrastructure

**useSSEStream Hook:**
- POST-based SSE streaming using fetch + ReadableStream (EventSource doesn't support POST body)
- Parses all 10 StreamEvent types: coding_started, validation_started, execution_started, analysis_started, progress, retry, content_chunk, node_complete, completed, error
- Maps event types to user-friendly status messages ("Generating code...", "Validating code...", etc.)
- AbortController cleanup prevents memory leaks on unmount or stream cancellation
- State tracking: events array, isStreaming, error, currentStatus, streamedText, completedData

**useChatMessages Hooks:**
- TanStack Query hook for chat message history (GET /chat/{fileId}/messages)
- useAddLocalMessage: optimistic UI updates for instant user message rendering
- useInvalidateChatMessages: refetch from server after stream completion

### Chat UI Components

**ChatInterface:**
- Complete chat experience orchestration for a single file tab
- Loads chat history on tab switch via useChatMessages
- Auto-scrolls to bottom on new messages or streaming updates (useRef + useEffect)
- Empty state: "Ask a question about your data to get started"
- Status indicator shows agent phase transitions during streaming
- Handles stream completion by invalidating query and resetting stream state
- Error messages inline: "Something went wrong. Please try again."

**ChatInput:**
- Auto-expanding textarea (react-textarea-autosize)
- Enter key sends message, Shift+Enter creates new line
- Send button always visible as alternative to Enter
- Disabled during streaming to prevent double-send
- Min 1 row, max 6 rows

**ChatMessage:**
- User messages: right-aligned, gradient blue-purple background, white text
- Assistant messages: left-aligned, muted background, dark text
- Error messages: red accent border with AlertCircle icon
- Streaming cursor: animated pulsing bar at end of streaming text
- Relative timestamps: "just now", "2m ago", "3h ago", "5d ago"
- Avatar with "U" (user) or "S" (Spectra) fallback

**TypingIndicator:**
- Three dots with staggered animation (0s, 0.2s, 0.4s delays)
- Shows while waiting for first AI response (before content_chunk events)

---

## Requirements Coverage

From must_haves:

✅ **User can type a message in chat input and send with Enter key** - ChatInput handles Enter to send
✅ **Shift+Enter creates a new line in chat input (does not send)** - Shift+Enter allows default newline behavior
✅ **Chat input auto-expands vertically as user types** - react-textarea-autosize with minRows=1, maxRows=6
✅ **Send button is always visible as alternative to Enter key** - Button with Send icon always rendered
✅ **User sees typing indicator (animated dots) while waiting for first AI response** - TypingIndicator shows when isStreaming && !streamedText
✅ **AI response text streams character-by-character for ChatGPT-like feel** - content_chunk events append to streamedText
✅ **Chat history loads from backend when switching to a file tab** - useChatMessages fetches on fileId change
✅ **User messages appear on the right, AI messages on the left** - ChatMessage uses flex-row-reverse for user messages
✅ **Errors during AI response show inline error message in chat flow** - streamError renders as ChatMessage with message_type="error"

---

## Technical Implementation

### SSE Parsing with ReadableStream

```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop() || "";

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const event: StreamEvent = JSON.parse(line.slice(6));
      // Handle event type...
    }
  }
}
```

### Optimistic UI Pattern

```typescript
const handleSend = async (message: string) => {
  // 1. Immediate visual feedback
  addLocalMessage(fileId, message);

  // 2. Start streaming (backend processes asynchronously)
  await startStream(fileId, message);
};

// On stream completion:
useEffect(() => {
  if (completedData) {
    invalidateMessages(fileId); // Refetch from server
    resetStream(); // Clear streaming state
  }
}, [completedData]);
```

### Auto-scroll Implementation

```typescript
const scrollRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (scrollRef.current) {
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }
}, [chatData?.messages, streamedText, isStreaming]);
```

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Integration Points

**With Backend:**
- POST /api/chat/{fileId}/stream - SSE streaming endpoint
- GET /api/chat/{fileId}/messages - Chat history fetch

**With Frontend (06-01):**
- Uses apiClient from lib/api-client.ts for auth token injection
- Uses TanStack Query from lib/query-client.ts
- Uses shadcn/ui components (Avatar, Button, ScrollArea, Separator)

**For Future Plans:**
- 06-05 Data Cards: Will check message.metadata_json for generated_code, execution_result, analysis and render Data Card inline

---

## Testing & Verification

Build verification:
```bash
cd frontend && npm run build
# ✓ Compiled successfully in 1803.1ms
```

TypeScript verification:
```bash
cd frontend && npx tsc --noEmit --pretty
# No errors
```

Manual verification:
- [x] ChatInput handles Enter (send) and Shift+Enter (newline) correctly
- [x] TypingIndicator renders animated dots
- [x] useSSEStream parses SSE events from POST stream
- [x] ChatInterface auto-scrolls on new messages
- [x] Streaming text appears progressively
- [x] Error messages appear inline in chat flow

---

## Next Phase Readiness

**Ready for 06-05 (Data Cards):**
- ChatInterface provides container for Data Card rendering
- message.metadata_json available for detecting Data Card content
- StreamEvent contains data payloads for progressive Data Card rendering

**Blockers:** None

**Concerns:** None

---

## Performance Notes

**Stream Handling:**
- AbortController ensures no memory leaks from abandoned streams
- ReadableStream processes data incrementally (no full buffering)
- useCallback stabilizes function references to prevent unnecessary re-renders

**Rendering:**
- Auto-scroll only triggers on message/streaming changes (not on every render)
- Optimistic updates provide instant feedback without waiting for server
- TanStack Query caching prevents redundant network requests

---

## Lessons Learned

1. **POST-based SSE requires manual parsing** - EventSource API doesn't support POST body, so fetch + ReadableStream is necessary for sending user message in request
2. **Buffer management for SSE parsing** - Must handle partial chunks by maintaining buffer and splitting on newlines
3. **Optimistic updates improve perceived performance** - Instant user message rendering makes chat feel responsive even before backend persistence
4. **Auto-scroll needs dependency tracking** - useEffect with message/streaming dependencies ensures scroll updates at right times

---

*Phase: 06-frontend-ui-interactive-data-cards | Plan: 04 | Completed: 2026-02-04*
