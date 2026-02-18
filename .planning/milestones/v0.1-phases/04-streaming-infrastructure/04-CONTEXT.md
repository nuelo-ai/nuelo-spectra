# Phase 4: Streaming Infrastructure - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Real-time streaming of AI responses from backend to frontend with reliable connection handling and persistent chat history. Users see AI processing in real-time as the 4-agent pipeline (Coding → Code Checker → Execute → Data Analysis) generates responses. Streaming infrastructure enables responsive UX where users observe thinking process rather than waiting for a black-box result.

</domain>

<decisions>
## Implementation Decisions

### Streaming Format & Event Types
- **High detail granularity**: Every agent step visible to users
  - Stream each agent transition: 'Coding Agent thinking...', 'Code Checker validating...', 'Executing code...', 'Data Analysis interpreting...'
- **Error visibility**: Stream error events with retry status
  - Show 'Code validation failed: X', then 'Regenerating code (attempt 2/3)...', keep user informed of retry progress
- **Event types included**:
  - Status events: `coding_started`, `validation_started`, `execution_started`, `analysis_started`, `completed`
  - Progress events: Numeric progress like 'step 2 of 4', 'validation 50% complete' - quantitative feedback

### Connection Reliability & Reconnection
- **Timeout duration**: Medium timeout (2-3 minutes)
  - Wait for complex queries that might take time, balance patience vs frustration
- **Partial results on failure**: No - clear partial results on failure
  - Remove incomplete results, show clean error state, avoid confusion from partial data
- **Unstable connections**: Keep retrying indefinitely with user control
  - Show 'Reconnecting...' with manual 'Cancel' option, let user decide when to give up

### Chat History Persistence Timing
- **AI response persistence**: Save on completion only
  - Wait until full response arrives, then save complete message - simpler, atomic writes
- **Failed stream handling**: Save nothing if stream fails
  - Rollback entire interaction on failure - only successful completions appear in history
- **Stream metadata**: Yes - store full stream metadata
  - Log duration, retry count, error details - useful for debugging and analytics

### Frontend Streaming UX
- **Progress indicators** (multiple approaches):
  - Typing indicator (animated dots) while AI is thinking/generating
  - Status text updates: 'Generating code...', 'Validating...', 'Analyzing...' - explicit phase labels
  - Progress bar or percentage: Visual bar showing '2 of 4 steps complete' - quantitative feedback
- **Thinking visibility**: Partially visible - show phases but not agent names
  - User sees: 'Generating code...', 'Validating...', 'Executing...', 'Analyzing...' - no agent terminology exposed
- **Content rendering**: Chunk-based (word or line at a time)
  - Content appears in small chunks - faster than typewriter, still feels live
- **Completion state**: Success indicator - show checkmark or 'Complete'
  - Brief success message or icon: '✓ Analysis complete' - confirms success explicitly

### Claude's Discretion
- Whether to show intermediate results (generated code) as they stream or only when complete
- Network reconnection strategy (auto-reconnect vs manual retry)
- When to save user messages to database (immediately vs after validation)
- Specific event payload format and SSE protocol details

</decisions>

<specifics>
## Specific Ideas

- Show every agent step visibly so users understand the multi-agent pipeline is working
- Error transparency: users should see when validation fails and retries are happening (builds trust in the system)
- Clean failure states: don't show broken/partial results - either success or clean error
- Give users control over unstable connections: show 'Reconnecting...' with Cancel button rather than auto-deciding
- Store metadata about streaming (duration, retries, errors) for debugging and potential user-facing analytics later

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-streaming-infrastructure*
*Context gathered: 2026-02-03*
