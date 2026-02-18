---
phase: 10-smart-query-suggestions
plan: 02
subsystem: ui, frontend
tags: [react, tailwind, react-markdown, suggestions, chips, query-suggestions]

# Dependency graph
requires:
  - phase: 10-smart-query-suggestions
    plan: 01
    provides: "query_suggestions in DB and API, follow_up_suggestions in stream events and metadata_json"
  - phase: 06-interactive-data-cards
    provides: "DataCard component, ChatMessage structured data rendering"
provides:
  - "QuerySuggestions component with grouped chips, fade animation, ReactMarkdown rendering"
  - "ChatInterface empty state shows categorized suggestions when available"
  - "DataCard renders follow-up suggestion chips after analysis section"
  - "FileSummaryResponse type extended with query_suggestions and suggestion_auto_send"
  - "ChatInput initialValue prop for non-auto-send mode"
affects: [smart-query-suggestions-feature-complete]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Suggestion chip component with fade-out animation on selection"
    - "Conditional empty state: suggestions when available, generic fallback otherwise"
    - "Prop threading: onFollowUpClick through ChatMessage to DataCard"

key-files:
  created:
    - frontend/src/components/chat/QuerySuggestions.tsx
  modified:
    - frontend/src/types/file.ts
    - frontend/src/components/chat/ChatInterface.tsx
    - frontend/src/components/chat/ChatMessage.tsx
    - frontend/src/components/chat/DataCard.tsx
    - frontend/src/components/chat/ChatInput.tsx

key-decisions:
  - "Auto-send as default behavior: clicking suggestion calls handleSend directly, no input population step"
  - "Non-auto-send fallback via ChatInput initialValue prop (useEffect-based) for configurable behavior"
  - "SVG icon replaces emoji in fallback empty state for consistent cross-platform rendering"
  - "Follow-up chips are plain text (no ReactMarkdown) since they are shorter and simpler than initial suggestions"
  - "followUpSuggestions extracted from both metadata_json (historical) and stream events (live)"

patterns-established:
  - "Suggestion chip pattern: rounded-full border with hover:bg-accent hover:border-primary/30 transition"
  - "Fade-out selection: set selected state, opacity-0 on siblings, setTimeout hide after 300ms"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 10 Plan 02: Frontend Query Suggestions UI Summary

**QuerySuggestions component with categorized chips in empty chat state and follow-up suggestion chips on DataCards with auto-send click behavior**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T21:08:21Z
- **Completed:** 2026-02-08T21:11:31Z
- **Tasks:** 3/3 (2 auto + 1 human verification: PASSED)
- **Files modified:** 6

## Accomplishments
- QuerySuggestions component renders LLM-generated suggestions as grouped chips with category headers
- ChatInterface shows suggestions in empty state, gracefully falls back for files without suggestions
- DataCard renders follow-up suggestion chips at bottom after analysis completes
- Full prop threading from ChatInterface through ChatMessage to DataCard for follow-up click handling
- TypeScript compiles with zero errors across all changes

## Task Commits

Each task was committed atomically:

1. **Task 1: QuerySuggestions component and ChatInterface empty state integration** - `369d58a` (feat)
2. **Task 2: DataCard follow-up suggestions and stream event type updates** - `d15b4ac` (feat)

## Files Created/Modified
- `frontend/src/components/chat/QuerySuggestions.tsx` - New component: grouped suggestion chips with fade animation and ReactMarkdown rendering
- `frontend/src/types/file.ts` - Extended FileSummaryResponse with query_suggestions and suggestion_auto_send
- `frontend/src/components/chat/ChatInterface.tsx` - Integrated QuerySuggestions in empty state, wired onFollowUpClick, added useFileSummary hook
- `frontend/src/components/chat/ChatMessage.tsx` - Added onFollowUpClick prop, extracts follow_up_suggestions from metadata_json
- `frontend/src/components/chat/DataCard.tsx` - Added followUpSuggestions and onFollowUpClick props, renders follow-up chips
- `frontend/src/components/chat/ChatInput.tsx` - Added initialValue prop for non-auto-send suggestion mode

## Decisions Made
- Auto-send is the default behavior: clicking a suggestion chip calls handleSend directly
- Non-auto-send mode populates ChatInput via initialValue prop (useEffect watches for changes)
- Fallback empty state uses inline SVG chat icon instead of emoji for cross-platform consistency
- Follow-up chips are plain text (no ReactMarkdown) since they contain shorter, simpler text
- Follow-up suggestions extracted from both metadata_json (persisted messages) and stream events (live streaming)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced emoji with SVG icon in fallback empty state**
- **Found during:** Task 1 (ChatInterface integration)
- **Issue:** Original empty state used emoji character which renders inconsistently across platforms
- **Fix:** Replaced with inline SVG chat bubble icon for consistent rendering
- **Files modified:** frontend/src/components/chat/ChatInterface.tsx
- **Committed in:** 369d58a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor cosmetic improvement, no scope creep.

## Bugfix During Human Verification

**LLM JSON code fence wrapping + schema mismatch** - `54a5aa2` (fix)
- LLM wrapped JSON response in markdown code fences (```json...```), causing json.loads() to fail and store raw JSON as data_summary
- Prompt schema used `queries` key but frontend expected `suggestions` key in category objects
- Fix: Added code fence stripping in onboarding.py and data_analysis.py; aligned frontend types to use `queries`

## Human Verification Results

All 5 test scenarios PASSED:
1. Initial suggestions on new file upload - suggestions grouped by categories with real column names
2. Suggestion click auto-sends - streaming starts immediately, chips fade out
3. Follow-up suggestions on DataCard - 2-3 chips with "Continue exploring" header
4. Existing file backward compatibility - old empty state works, no console errors
5. Page refresh persistence - follow-up suggestions persist on DataCards

## Issues Encountered
None beyond the code fence bugfix noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete Smart Query Suggestions feature verified end-to-end
- Backend (Plan 01) + Frontend (Plan 02) integration complete and human-tested
- Ready for phase verification

## Self-Check: PASSED

- frontend/src/components/chat/QuerySuggestions.tsx: FOUND
- frontend/src/types/file.ts: FOUND (contains query_suggestions)
- frontend/src/components/chat/ChatInterface.tsx: FOUND (contains QuerySuggestions import)
- frontend/src/components/chat/ChatMessage.tsx: FOUND (contains onFollowUpClick)
- frontend/src/components/chat/DataCard.tsx: FOUND (contains followUpSuggestions)
- frontend/src/components/chat/ChatInput.tsx: FOUND (contains initialValue)
- Commit 369d58a (Task 1): verified in git log
- Commit d15b4ac (Task 2): verified in git log
- TypeScript compilation: zero errors

---
*Phase: 10-smart-query-suggestions*
*Completed: 2026-02-08*
