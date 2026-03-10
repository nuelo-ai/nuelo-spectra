---
phase: 54-pulse-analysis-fixes
verified: 2026-03-10T17:30:00Z
status: human_needed
score: 8/8 automated must-haves verified
re_verification: false
human_verification:
  - test: "PULSE-01: Open a Collection that has completed pulse runs, go to Overview tab, check Credits Used card shows non-zero value reflecting actual cumulative spend"
    expected: "Credits Used shows the sum of credit_cost from completed PulseRun records, not a flat config value"
    why_human: "Requires a live backend with pulse run history to confirm the aggregate SQL query returns accurate data in production"
  - test: "PULSE-02: Open any Collection Signals page, resize browser to below 640px width (or use DevTools), verify only signals list shows initially; click a signal, verify detail panel appears full-width and list is hidden; click Back to Signals, verify list returns"
    expected: "Mobile panel toggle works: selecting a signal shows detail-only, back button returns to list; desktop (640px+) shows both panels side by side"
    why_human: "Responsive CSS behavior and touch interaction cannot be verified programmatically — requires live browser render"
  - test: "PULSE-03: On Signal detail panel, verify Chat with Spectra button (green, between Analysis and Statistical Evidence); click it, verify spinner appears, a new browser tab opens navigating to /sessions/{id}, and collection files are pre-linked in the new session"
    expected: "Green button is visible in correct placement; clicking creates session, links all collection files, opens new tab at /sessions/{id}; if no files are present, button is disabled"
    why_human: "Session creation flow, file linking, and new-tab navigation require a running app with API access"
  - test: "PULSE-04: Open a Collection with activity history (Overview tab, Activity History section), verify each entry shows both date AND time, e.g. 'Mar 10, 2026, 02:34 PM'"
    expected: "Timestamps include time component — not date-only 'Mar 10, 2026'"
    why_human: "Visual rendering of formatted timestamps requires a live browser with real data"
  - test: "PULSE-05: Open a Collection Files tab, verify the Added column shows both date AND time per row, e.g. 'Mar 10, 2026, 02:34 PM'"
    expected: "File timestamps include time component — not date-only"
    why_human: "Visual rendering of formatted timestamps requires a live browser with real data"
---

# Phase 54: Pulse Analysis Fixes Verification Report

**Phase Goal:** Fix 5 Pulse Analysis bugs/gaps identified in v0.8.1 UAT: Credits Used stat accuracy, mobile Signal View, Chat bridge button, and timestamp display (activity feed + files table).
**Verified:** 2026-03-10T17:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /collections/{id} response includes credits_used field with actual cumulative credits spent | VERIFIED | `services/collection.py:126-134` — COALESCE(SUM(credit_cost)) correlated subquery; `schemas/collection.py:62` — `credits_used: float = 0.0`; `routers/collections.py:121,154` — passed in both get and update responses |
| 2 | Credits Used card on Collection Overview displays actual cumulative spend, not cost-per-run config value | VERIFIED | `collections/[id]/page.tsx:310` — `creditsUsed={collection?.credits_used ?? 0}` (replaces old `creditCosts?.pulse_run ?? 0`) |
| 3 | Collections with no completed runs show credits_used as 0.0 | VERIFIED | COALESCE guard confirmed in service; 2 backend tests pass (zero-spend + nonzero-spend: 2 passed) |
| 4 | Activity history entries display both date and time | VERIFIED | `activity-feed.tsx:18` — `toLocaleString` with `hour: "2-digit", minute: "2-digit"` at lines 22-23; no `toLocaleDateString` remaining |
| 5 | Files Added list entries display both date and time | VERIFIED | `file-table.tsx:21` — `toLocaleString` with `hour: "2-digit", minute: "2-digit"` at lines 25-26; no `toLocaleDateString` remaining |
| 6 | UserFileTable inside collections/[id]/page.tsx also shows date and time | VERIFIED | `collections/[id]/page.tsx:687` — `toLocaleString` with `hour: "2-digit", minute: "2-digit"` at lines 691-692 |
| 7 | On mobile (<640px) Signal View shows single panel (list or detail) with toggle; on desktop both panels side by side | VERIFIED | `signals/page.tsx:65-66,178,192` — `showDetail` state drives `cn(showDetail ? "hidden sm:flex" : "flex")` on list wrapper and `cn(showDetail ? "flex" : "hidden sm:flex")` on detail wrapper |
| 8 | Chat bridge button between Analysis and Statistical Evidence creates session, links files, and opens /sessions/{id} in a new tab | VERIFIED | `signal-detail-panel.tsx:143-158` — button rendered after Analysis block (`{signal.analysis && ...}`) and before Evidence Grid (`{signal.evidence && ...}`); `handleChatBridge` at lines 65-80 uses `useCreateSession` + `useLinkFile` + `window.open(_blank)` |

**Score:** 8/8 truths verified (automated)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/collection.py` | credits_used correlated scalar_subquery | VERIFIED | Lines 126-134: subquery with `func.coalesce(func.sum(PulseRunModel.credit_cost), 0.0)`, `status == "completed"`, `float(row[4])` in return dict |
| `backend/app/schemas/collection.py` | credits_used: float = 0.0 field | VERIFIED | Line 62: `credits_used: float = 0.0` on `CollectionDetailResponse` |
| `backend/app/routers/collections.py` | credits_used passed in response | VERIFIED | Lines 121 and 154: `credits_used=detail["credits_used"]` in both get_collection and update_collection |
| `frontend/src/types/workspace.ts` | credits_used: number on CollectionDetail | VERIFIED | Line 20: `credits_used: number;` on `CollectionDetail` interface |
| `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` | credits_used wired to stat card; formatDate with time | VERIFIED | Line 310: `creditsUsed={collection?.credits_used ?? 0}`; lines 687-692: `toLocaleString` with `hour/minute` options |
| `frontend/src/components/workspace/activity-feed.tsx` | formatTimestamp with toLocaleString + hour/minute | VERIFIED | Line 18: `toLocaleString`; lines 22-23: `hour: "2-digit", minute: "2-digit"` |
| `frontend/src/components/workspace/file-table.tsx` | formatDate with toLocaleString + hour/minute | VERIFIED | Line 21: `toLocaleString`; lines 25-26: `hour: "2-digit", minute: "2-digit"` |
| `frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx` | showDetail state, mobile wrappers, collectionFiles, onBack | VERIFIED | Lines 65-66: state + hook; lines 178, 192: `sm:flex` breakpoint classes; lines 196-198: `onBack`, `collectionFiles`, `collectionId` props passed |
| `frontend/src/components/workspace/signal-detail-panel.tsx` | Chat bridge button + mobile back button + updated props | VERIFIED | Lines 43-44: `onBack?`, `collectionFiles?` props; lines 65-80: `handleChatBridge` with `window.open(_blank)`; lines 86-95: mobile back button (`sm:hidden`); lines 143-158: Chat bridge button between Analysis and Evidence sections |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/collection.py` | `models/pulse_run.py` | `PulseRunModel.credit_cost` scalar_subquery | WIRED | Line 10: `from app.models.pulse_run import PulseRun as PulseRunModel`; lines 127,129,130: query on `PulseRunModel.credit_cost` with `status == "completed"` |
| `routers/collections.py` | `schemas/collection.py` | `CollectionDetailResponse(credits_used=detail["credits_used"])` | WIRED | Lines 121 and 154: `credits_used=detail["credits_used"]` present in both endpoints |
| `collections/[id]/page.tsx` | `types/workspace.ts` | `collection?.credits_used` | WIRED | Line 310: `creditsUsed={collection?.credits_used ?? 0}` references field defined in `CollectionDetail` interface |
| `activity-feed.tsx` | DOM | `formatTimestamp(item.timestamp)` | WIRED | `toLocaleString` used in the only `formatTimestamp` function; called in JSX render |
| `file-table.tsx` | DOM | `formatDate(file.added_at)` | WIRED | `toLocaleString` used in `formatDate`; called in JSX render |
| `signals/page.tsx` | `signal-detail-panel.tsx` | `onBack` + `collectionFiles` props | WIRED | Lines 196-198: `onBack={() => setShowDetail(false)}`, `collectionFiles={collectionFiles}`, `collectionId={id}` passed to `SignalDetailPanel` |
| `signal-detail-panel.tsx` | `useSessionMutations.ts` | `useCreateSession` + `useLinkFile` | WIRED | Line 20: import present; lines 61-62: hooks instantiated; lines 68-71: `createSession.mutateAsync` + `linkFileAsync` called in `handleChatBridge` |
| `signal-detail-panel.tsx` | `/sessions/{id}` (new tab) | `window.open(_blank)` after session creation | WIRED | Line 74: `window.open(\`/sessions/${session.id}\`, '_blank')` — post-verification design fix committed as `befe78b` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PULSE-01 | 54-01 | Credits Used card reflects actual credits used after pulse runs | SATISFIED | Backend aggregate subquery + schema field + router pass-through + frontend wiring all confirmed in codebase; 22/22 collection tests pass |
| PULSE-02 | 54-03 | Signal View mobile responsive — detail panel accessible on small screens | SATISFIED | `showDetail` state with `sm:flex`/`hidden` breakpoint classes confirmed; `onBack` prop and mobile back button confirmed |
| PULSE-03 | 54-03 | "Chat with Spectra" button between Analysis and Statistical Evidence, opens new Chat session with collection files pre-linked | SATISFIED | Button rendered at correct position in JSX; `handleChatBridge` wired to `useCreateSession` + `useLinkFile` + `window.open(_blank)`; toast error on failure confirmed |
| PULSE-04 | 54-02 | Activity history list displays both date and time per entry | SATISFIED | `activity-feed.tsx` `formatTimestamp` uses `toLocaleString` with `hour: "2-digit", minute: "2-digit"`; no `toLocaleDateString` remaining in file |
| PULSE-05 | 54-02 | File added list displays both date and time per entry | SATISFIED | `file-table.tsx` `formatDate` uses `toLocaleString` with `hour: "2-digit", minute: "2-digit"`; no `toLocaleDateString` remaining in file |

No orphaned requirements — all 5 PULSE IDs are mapped to plans that cover them.

**Note:** REQUIREMENTS.md additionally shows LBAR-01, LBAR-02, CHAT-01–03, FILES-01–02 mapped to Phase 53 (not Phase 54). These are out of scope for this verification.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `collections/[id]/page.tsx` | 544 | `toLocaleDateString` for report list dates (not within scope of formatDate/UserFileTable) | Info | Noted by executor as deferred — out of scope for Phase 54; report list timestamps are not a PULSE requirement |

No blockers or warnings found. The one `toLocaleDateString` instance at line 544 is explicitly deferred (not a PULSE-04/PULSE-05 location) and was intentionally left untouched per the executor's scope boundary rules.

### Human Verification Required

All 5 PULSE requirements have automated evidence confirmed, but visual/behavioral confirmation in a running browser is needed to close the v0.8.1 gate. The following tests must be run with the dev server active.

#### 1. PULSE-01: Credits Used Card Shows Actual Spend

**Test:** Open a Collection with at least one completed pulse run. Navigate to the Overview tab. Inspect the Credits Used stat card value.
**Expected:** Value reflects the sum of `credit_cost` from completed PulseRun records — not the flat cost-per-run config value (e.g., "5").
**Why human:** Requires a live backend with pulse run history to confirm the COALESCE(SUM) aggregate returns accurate non-zero data in production.

#### 2. PULSE-02: Mobile Signal View Panel Toggle

**Test:** Open any Collection Signals page. Resize browser to below 640px (or use DevTools responsive mode). Verify only the signals list is initially visible. Click any signal — verify the detail panel appears full-width and the list is hidden. Click "Back to Signals" — verify the list returns. Resize to desktop — verify both panels appear side by side.
**Expected:** Panel toggle works correctly at mobile breakpoint; desktop behavior unchanged.
**Why human:** CSS responsive breakpoints and touch interaction require live browser rendering.

#### 3. PULSE-03: Chat Bridge Button Functionality

**Test:** On a Signal detail panel, verify the green "Chat with Spectra" button appears between the Analysis text and the Statistical Evidence card. Click it. Watch for the Loader2 spinner while the session is created. Confirm a new browser tab opens at `/sessions/{id}`. Confirm the new session has the collection's files pre-linked.
**Expected:** Button is green, correctly placed, shows spinner while bridging, opens new tab, files are linked. If no collection files, button should be disabled.
**Why human:** Session creation, file linking, and new-tab navigation require a running app with API access.

#### 4. PULSE-04: Activity History Timestamps Include Time

**Test:** Open a Collection with activity history (Overview tab, Activity History section). Inspect any entry.
**Expected:** Each entry shows date + time, e.g. "Mar 10, 2026, 02:34 PM" — NOT "Mar 10, 2026" alone.
**Why human:** Actual date/time rendering requires live browser with real data.

#### 5. PULSE-05: Files Added Timestamps Include Time

**Test:** Open a Collection's Files tab. Inspect the "Added" column.
**Expected:** Each file row shows date + time, e.g. "Mar 10, 2026, 02:34 PM" — NOT "Mar 10, 2026" alone.
**Why human:** Actual date/time rendering requires live browser with real data.

### Gaps Summary

No gaps found. All 5 PULSE requirements have full implementation evidence:

- PULSE-01: Backend aggregate query, schema field, router wiring, and frontend component all confirmed with correct code. 22/22 collection tests pass including 2 new credits_used tests.
- PULSE-02: Mobile panel toggle confirmed with `showDetail` state and `sm:flex`/`hidden` breakpoint classes in the correct wrapper divs.
- PULSE-03: Chat bridge button confirmed between Analysis and Statistical Evidence in JSX; `handleChatBridge` function fully wired to session creation hooks and `window.open(_blank)`. Post-verification design fix (green button style) confirmed at line 147.
- PULSE-04: `toLocaleString` with `hour`/`minute` confirmed in `activity-feed.tsx`; no `toLocaleDateString` remains.
- PULSE-05: `toLocaleString` with `hour`/`minute` confirmed in `file-table.tsx` and `collections/[id]/page.tsx` (UserFileTable). One unrelated `toLocaleDateString` at line 544 (report list) is explicitly out of scope and deferred.

All referenced commits verified present in git history: `8bd1e18`, `b8e140e`, `2532c5c`, `902e630`, `13d83d0`, `bfbe964`, `d1d125e`, `befe78b`.

---

_Verified: 2026-03-10T17:30:00Z_
_Verifier: Claude (gsd-verifier)_
