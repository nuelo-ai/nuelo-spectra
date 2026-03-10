---
phase: 45-what-if-scenarios
verified: 2026-03-05T00:00:00Z
status: human_needed
score: 10/10 automated checks verified
re_verification: false
human_verification:
  - test: "Load /workspace/collections/col-001/signals/sig-001/whatif and verify objective selection page renders"
    expected: "Root cause context card visible with 'Enterprise Pricing Impact' title and High confidence badge; action search bar present; 4 suggestions appear on focus; clicking suggestion populates input without submitting; Generate Scenarios button disabled until text entered"
    why_human: "Visual layout and dropdown interaction cannot be verified programmatically"
  - test: "Click Generate Scenarios and observe loading state"
    expected: "Full-page loading state with 4 labeled animated steps (Analyzing root cause, Generating scenarios, Scoring confidence, Finalizing scenarios), progress bar fills, auto-navigates to /whatif/wif-001 after ~10 seconds"
    why_human: "Animation timing and auto-navigation require runtime browser verification"
  - test: "Load /workspace/collections/col-001/signals/sig-001/whatif/wif-001 and verify 3-panel layout with refinement chat access"
    expected: "Scenario list (280px) with 3 cards showing name + confidence badge (High=emerald, Medium=amber, Low=muted) + impact range; first scenario auto-selected; detail panel shows full 5-section content; 'Refine' toggle button opens slide-out chat panel"
    why_human: "Multi-panel layout, badge colors, and slide-out animation require visual verification"
  - test: "Test per-scenario refinement chat"
    expected: "Scenario 1 chat shows 2 pre-existing messages on open; scenario 2 chat shows empty state with placeholder text; typing a message and clicking Send appends user message + AI reply; switching scenarios resets chat to that scenario's history"
    why_human: "Chat state management and scenario-switching behavior require interactive testing"
  - test: "Click Generate What-If Report button and verify report viewer"
    expected: "Navigates to /reports/rep-whatif-001; violet 'What-If Scenario Report' badge visible in sticky header; report content includes Objective, Root Cause Context, all 3 evaluated scenarios, AI-Recommended Approach"
    why_human: "Report rendering and badge display require visual verification"
  - test: "Navigate to an investigation report (e.g., /reports/rpt-inv-001) and verify What-If CTA"
    expected: "Violet 'Explore What-If Scenarios' card visible at the bottom with 'Start What-If ->' button linking to /signals/sig-001/whatif"
    why_human: "CTA card appearance and link target require visual verification"
  - test: "Verify WHAT-05 and WHAT-06 intentional deferral status"
    expected: "Reviewer confirms: no 'Add Scenario' action visible, no side-by-side comparison view — consistent with user decision documented in CONTEXT.md"
    why_human: "Requires human confirmation that absence of these features is intentional and not a regression; REQUIREMENTS.md marks them as Complete which contradicts CONTEXT.md deferral documentation"
---

# Phase 45: What-If Scenarios Verification Report

**Phase Goal:** The reviewer can see the complete What-If Scenarios flow — from objective selection through scenario generation, per-scenario refinement chat, side-by-side comparison, and the generated What-If report section — all as static mockup screens.
**Verified:** 2026-03-05
**Status:** human_needed (all automated checks pass; 7 items require human visual/interactive verification)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | WhatIf types exported from mock-data.ts | VERIFIED | Lines 685–717: `WhatIfConfidence`, `WhatIfScenario`, `WhatIfChatMessage`, `WhatIfSession` all exported |
| 2 | MOCK_WHATIF_SESSIONS contains 1 session with 3 scenarios for sig-001 | VERIFIED | Lines 718–800 in mock-data.ts: wif-001 session with wif-sc-001, wif-sc-002, wif-sc-003 |
| 3 | MOCK_REPORTS includes rep-whatif-001 as "What-If Scenario Report" | VERIFIED | Line 439–445 in mock-data.ts: id="rep-whatif-001", type="What-If Scenario Report" |
| 4 | Objective selection page exists at /whatif route with root cause card, search bar, suggestions, loading state | VERIFIED | `whatif/page.tsx` exists, 314 lines; root cause card, SUGGESTIONS array, WhatIfLoading component all present |
| 5 | 4-panel session page at /whatif/[sessionId] with scenario list, detail, and chat access | VERIFIED | `whatif/[sessionId]/page.tsx` exists, 308 lines; 3 panels + slide-out chat toggle implemented |
| 6 | WhatIfRefinementChat component with per-scenario chat history, send, auto-scroll | VERIFIED | `whatif-refinement-chat.tsx` exists, 112 lines; handleSend, useEffect scroll, key-prop remount documented |
| 7 | What-If button on signal detail panel with enabled/disabled logic | VERIFIED | signal-detail-panel.tsx line 51: hasCompleteInvestigation; line 160-170: What-If button with Wand2 icon |
| 8 | "What-If Scenario Report" badge in report viewer sticky header | VERIFIED | report viewer page.tsx line 48-50: conditional badge on report.type |
| 9 | "Explore What-If Scenarios" CTA on investigation reports | VERIFIED | report viewer page.tsx lines 138-163: violet CTA card with "Start What-If ->" link |
| 10 | TypeScript compiles clean | VERIFIED | `npx tsc --noEmit` returned no errors |

**Score:** 10/10 truths verified (automated)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pulse-mockup/src/lib/mock-data.ts` | WhatIf types and mock data | VERIFIED | All 4 types + MOCK_WHATIF_SESSIONS exported; rep-whatif-001 in MOCK_REPORTS |
| `pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/page.tsx` | Objective selection page | VERIFIED | 314 lines; exports `WhatIfObjectivePage`; SUGGESTIONS, LOADING_STEPS, WhatIfLoading all substantive |
| `pulse-mockup/src/app/workspace/collections/[id]/signals/[signalId]/whatif/[sessionId]/page.tsx` | 4-panel session page | VERIFIED | 308 lines; exports `WhatIfSessionPage`; full scenario list, detail, and WhatIfRefinementChat wired |
| `pulse-mockup/src/components/workspace/whatif-refinement-chat.tsx` | Per-scenario refinement chat component | VERIFIED | 112 lines; exports `WhatIfRefinementChat`; handleSend, auto-scroll, key remount pattern |
| `pulse-mockup/src/components/workspace/signal-detail-panel.tsx` | What-If button in Investigation section | VERIFIED | Wand2 imported; hasCompleteInvestigation computed; enabled/disabled button present |
| `pulse-mockup/src/app/workspace/collections/[id]/reports/[reportId]/page.tsx` | What-If Scenario Report badge + investigation CTA | VERIFIED | Violet badge on report.type === "What-If Scenario Report"; CTA on "Investigation Report" |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `whatif/page.tsx` | `mock-data.ts` | `import MOCK_SIGNALS, MOCK_INVESTIGATION_SESSIONS, MOCK_REPORTS` | WIRED | Line 19-22: all three imported and used |
| `whatif/page.tsx loading state` | `/whatif/wif-001 route` | `router.push after TOTAL_DURATION timer` | WIRED | Lines 77-80: `router.push(.../whatif/wif-001)` in WhatIfLoading |
| `whatif/[sessionId]/page.tsx` | `mock-data.ts` | `import MOCK_WHATIF_SESSIONS` | WIRED | Line 17: MOCK_WHATIF_SESSIONS imported and used line 53-55 |
| `whatif/[sessionId]/page.tsx` | `whatif-refinement-chat.tsx` | `rendered as WhatIfRefinementChat component` | WIRED | Line 21: import; lines 299-303: rendered with key={selectedScenarioId} |
| `Generate What-If Report button` | `/reports/rep-whatif-001` | `router.push` | WIRED | Lines 143-148: `router.push(.../reports/${session.reportId ?? "rep-whatif-001"})` |
| `signal-detail-panel.tsx What-If button` | `/whatif route` | `Link href` | WIRED | Line 161: `Link href=".../whatif"` |
| `report viewer page` | `What-If Scenario Report badge` | `conditional render on report.type` | WIRED | Lines 48-51: `report.type === "What-If Scenario Report"` |
| `investigation report CTA` | `/whatif route` | `Link at bottom of paper` | WIRED | Line 152: `Link href=".../signals/${report.signalId}/whatif"` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| WHAT-01 | 45-01-PLAN.md | Objective selection screen: root cause context + selection choices + free-text | SATISFIED | `whatif/page.tsx`: root cause card, SUGGESTIONS dropdown, free-text input |
| WHAT-02 | 45-01-PLAN.md | Scenario generation loading state with progress indicator | SATISFIED | `WhatIfLoading` function in `whatif/page.tsx`: 4 animated steps + Progress component |
| WHAT-03 | 45-02-PLAN.md | Scenario cards with name, narrative, impact, assumptions, confidence badge, data backing | SATISFIED | `[sessionId]/page.tsx`: 5 Card sections rendering all 6 fields |
| WHAT-04 | 45-02-PLAN.md | Per-scenario refinement chat panel (scoped, not freeform) | SATISFIED | `WhatIfRefinementChat` component; slide-out panel toggled by "Refine" button; key-prop scopes to selected scenario |
| WHAT-05 | 45-02-PLAN.md | "Add Scenario" action (2 credits) alongside existing scenarios | NOT IMPLEMENTED | Intentionally dropped per user decision documented in CONTEXT.md lines 127-128; reviewer confirmed in Plan 03 human checkpoint. REQUIREMENTS.md traceability table marks as "Complete" — this is a documentation inconsistency |
| WHAT-06 | 45-02-PLAN.md | Side-by-side comparison view | NOT IMPLEMENTED | Intentionally deferred per user decision in CONTEXT.md line 127; reviewer confirmed. REQUIREMENTS.md marks as "Complete" — documentation inconsistency |
| WHAT-07 | 45-03-PLAN.md | What-If Report section: objective + evaluated scenarios + selected approach | SATISFIED | `rep-whatif-001` in MOCK_REPORTS with full markdown; report viewer shows violet badge; "Generate What-If Report" button wired to report route |

**Note on WHAT-05 and WHAT-06:** REQUIREMENTS.md marks both as `[x] Complete` in the feature list and "Complete" in the traceability table. CONTEXT.md explicitly documents these as dropped/deferred with user sign-off. The summaries confirm the reviewer approved all implemented requirements while acknowledging WHAT-05 and WHAT-06 as intentionally out of scope. The REQUIREMENTS.md traceability entries are inaccurate — these requirements were not implemented. This is a documentation discrepancy, not an implementation failure, as reviewer approval was obtained for the reduced scope.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODO/FIXME/stub patterns found in any phase 45 source files. All implementations are substantive.

---

### Implementation Deviation: Refinement Chat Panel Architecture

**CONTEXT.md spec (line 58):** "Refinement chat panel — always visible alongside the detail panel"

**Actual implementation:** The chat is a slide-out overlay panel (320px, positioned absolute, translates in/out) toggled by a "Refine" button in the detail panel header.

**Assessment:** This is a reviewer-accepted deviation. The Plan 03 human verification checkpoint (gate="blocking") was completed with reviewer approval. The "Refine" toggle pattern may be more practical for desktop widths where a 4th always-visible panel would be too narrow. WHAT-04 requirement ("per-scenario refinement chat panel, scoped, not freeform") is satisfied by this implementation — the chat is scoped to the selected scenario via key-prop remount.

---

### Human Verification Required

#### 1. Objective Selection Page — Visual and Interaction

**Test:** Navigate to `/workspace/collections/col-001/signals/sig-001/whatif` (via the What-If button on the sig-001 signal card).
**Expected:** Root cause context card shows "Enterprise Pricing Impact" (or similar investigation title) + High confidence badge (emerald) + root cause excerpt. Action search bar is present below. Clicking/focusing the bar reveals 4 suggestion items in a dropdown. Clicking a suggestion populates the input field without submitting. Input remains editable. "Generate Scenarios ->" button is disabled until input has text.
**Why human:** Visual layout, dropdown interaction timing (onMouseDown blur prevention), and disabled-state behavior require browser testing.

#### 2. Scenario Generation Loading State

**Test:** Type or select an objective, then click "Generate Scenarios ->".
**Expected:** Page transitions to a loading state showing 4 steps — "Analyzing root cause" (Brain icon), "Generating scenarios" (Sparkles), "Scoring confidence" (BarChart3), "Finalizing scenarios" (CheckCircle). Each step progresses in sequence with emerald completed state and primary current state. Progress bar fills. After ~10 seconds, auto-navigates to `/whatif/wif-001`.
**Why human:** Animation sequencing, progress timing, and auto-navigation require runtime browser verification.

#### 3. Session Page — Layout and Scenario Selection

**Test:** Arrive at `/workspace/collections/col-001/signals/sig-001/whatif/wif-001`.
**Expected:** Three visible panels — 280px scenario list on the left showing 3 scenario cards (each with name, confidence badge, impact range). First scenario "Enterprise Expansion Play" is auto-selected (highlighted). Center panel shows full scenario detail: Narrative, Estimated Impact (highlighted block), Assumptions (checklist), Confidence (badge + rationale), Data Backing. Clicking scenario 2 or 3 updates both the list selection and the detail panel content.
**Why human:** Panel layout widths, badge color accuracy, and scenario-switching behavior require visual verification.

#### 4. Refinement Chat — Per-Scenario Scoping

**Test:** With scenario 1 selected, click the "Refine" button in the detail panel header.
**Expected:** Slide-out chat panel appears from the right (320px). Scenario 1 shows 2 pre-existing messages in the thread (user: "Can you make the timeline more specific..." / assistant: "Updated the scenario..."). Type a new message and click Send — user message and AI reply both appear. Close and switch to scenario 2, reopen Refine — chat shows empty state with placeholder text. Switch to scenario 3 — chat shows its 2 pre-existing messages.
**Why human:** Chat state management, key-prop remount behavior on scenario switch, and slide-out animation require interactive testing.

#### 5. What-If Report Viewer

**Test:** Click "Generate What-If Report" button in the scenario list panel.
**Expected:** Navigates to `/workspace/collections/col-001/reports/rep-whatif-001`. Sticky header shows a violet "What-If Scenario Report" badge. Report body renders: Objective section, Root Cause Context, three scenario sections with their content (Expansion Play, Mid-Market Bridge, Seasonal Lock-In), and AI-Recommended Approach section.
**Why human:** Report content rendering and badge color (violet) require visual verification.

#### 6. Investigation Report CTA

**Test:** Navigate to an investigation report (e.g., `/workspace/collections/col-001/reports/rpt-inv-001`).
**Expected:** At the bottom of the report paper, a violet card appears with "Explore What-If Scenarios" heading (Wand2 icon), explanatory text, and a "Start What-If ->" button. Clicking the button navigates to the signal's `/whatif` route.
**Why human:** CTA card visibility, violet styling, and link target require visual verification.

#### 7. WHAT-05/WHAT-06 Scope Confirmation

**Test:** Review the session page at `/whatif/wif-001`.
**Expected:** No "Add Scenario" button is present. No side-by-side comparison view exists. The reviewer should confirm these absences are intentional per the scope decision in CONTEXT.md.
**Why human:** Requires human confirmation that REQUIREMENTS.md marking these as "Complete" is a documentation error and that the reduced scope was intentionally accepted. If the requirements table needs correction, that is a separate action.

---

### Gaps Summary

No automated gaps detected. All artifacts exist, are substantive (not stubs), and are wired correctly. TypeScript compiles clean. All 4 documented commits (9fab98a, 409f3d4, 0d2bc6a, 5e559a7) exist in git history.

**Documentation inconsistency flagged (not a code gap):** REQUIREMENTS.md traceability table marks WHAT-05 and WHAT-06 as Phase 45 "Complete" but these requirements were not implemented — intentionally dropped/deferred per user decision with reviewer approval. The REQUIREMENTS.md entries should reflect "Deferred" or "Dropped" rather than "Complete." This does not block the phase.

**Architecture deviation noted (reviewer-accepted):** The refinement chat panel is implemented as a slide-out overlay (toggle) rather than an always-visible 4th panel. This was accepted during the Plan 03 human verification checkpoint.

---

*Verified: 2026-03-05*
*Verifier: Claude (gsd-verifier)*
