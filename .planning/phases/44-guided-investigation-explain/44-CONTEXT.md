# Phase 44: Guided Investigation (Explain) - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add the full Guided Investigation flow to the existing `pulse-mockup/` app — triggered from the signal detail panel, conducted as an adaptive conversational Q&A, and culminating in a generated Investigation Report. The report is the investigation outcome. Investigation history per signal is shown as the list of reports generated from that signal. No separate root cause card exists.

</domain>

<decisions>
## Implementation Decisions

### Investigation Entry Point (Signal Detail Panel)
- "Investigate" button lives in the **signal detail panel only** — not on the compact signal list card
- Signal list card shows a **latest status badge only** (no button): None / In Progress / Complete
- A signal **can be investigated multiple times** — each session is independent and generates a new report
- The status badge reflects the latest investigation only; re-investigation is always available
- Signal detail panel has a dedicated **"Investigation" section** showing:
  - "Start New Investigation" / "Investigate Again" button (with credit cost) at the top
  - Compact list of all reports generated from this signal's investigations (most recent first)
  - Each row: date + auto-generated title (e.g., "Investigation — Internal inventory shortage") + status badge
  - Clicking a row navigates to the report viewer

### Investigation Page — Route & Layout
- Full-page route: `/workspace/collections/[id]/signals/[signalId]/investigate`
- Consistent with the signals page pattern (full-page detail views)
- Page layout: scrollable Q&A thread (past exchanges at top, active question anchored near bottom)

### Q&A Flow — Conversational, Not Wizard
- **No step indicator** — the flow is adaptive; length varies from 2-3 to 5-6 exchanges depending on user answers
- Each AI question determines the next based on the user's answer (branching logic)
- This is a **conversational Q&A thread**, similar to Claude Code's interactive Q&A pattern

### Q&A Flow — Single Exchange Layout
- AI question shown as a distinct block (card or colored section) — the hypothesis/question text
- Below it: **radio-button style choices** as styled selectable buttons
- A **free-text input** ("Add your own answer") is always available alongside the radio choices
- Completed exchanges collapse into compact pairs: AI question + user's selected/typed answer, shown in the scrollable thread above

### Q&A Flow — Checkpoint
- At the point where AI has gathered sufficient context, it presents a **special summary block** (visually distinct from regular Q&A exchanges):
  - Brief summary: "Based on your inputs, I have enough context to form a root cause analysis"
  - "Proceed with Report" button (primary action)
  - Free-text area: "Add more context before proceeding" — submitting this may trigger additional questions

### Report Generation & Navigation
- After "Proceed with Report": a **generation loading state** on the investigation page (e.g., "Generating investigation report...")
- Then **auto-navigates to the report viewer** — same document-style reader from Phase 43
- Re-investigating generates a new report; no reports are replaced

### Investigation Report Content
The report (not a root cause card) contains:
- Signal summary (the problem or opportunity that was investigated)
- AI analysis from the signal (what the signal detected)
- AI analysis from the investigation (synthesized from the Q&A exchanges)
- Supporting data: statistics, tables, and charts/visualizations
- AI recommendations

### Investigation History
- History = the list of investigation reports in the signal detail panel (most recent first)
- No separate history page — the signal detail panel section IS the history
- Exchange count not shown on individual rows (kept compact: date + title + status)

### Cross-Signal Links
- "Related Signals" section inside the **report viewer** at the bottom
- Shows other signals that share the same root cause as identified in this investigation report
- Linking logic is mocked as static data — no real computation in the mockup

### Q&A UI Design Principle
- **Simple and clean** — the Q&A interface should not feel complex or overwhelming
- Minimal visual noise; the focus is on the AI question and the user's choices
- Avoid heavy card borders, excessive shadows, or decorative elements in the Q&A thread

### Claude's Discretion
- Exact visual styling of the AI question block (minimal — clean text block, light separator)
- How completed Q&A exchange pairs look when collapsed in the thread
- Transition animation between Q&A thread and report generation loading state
- Mock content for investigation reports (questions, user answers, AI analysis text, chart types)
- How the "Related Signals" section is laid out in the report viewer

</decisions>

<specifics>
## Specific Ideas

- The Q&A flow is explicitly compared to Claude Code's interactive Q&A — adaptive, conversational, not a fixed wizard with step numbers
- Each investigation is a fresh session with its own assumptions — users can reach different root causes from the same signal (e.g., Session 1: internal inventory; Session 2: external factor)
- The report is the artifact, not a summary card — investigation outcome is a full document with signal context, analysis, data, and recommendations
- Signal detail panel should clearly communicate "you can investigate again" — the re-investigation action should not be hidden

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pulse-mockup/src/components/workspace/signal-card.tsx` — signal card in the list; add latest investigation status badge to it
- `pulse-mockup/src/lib/mock-data.ts` — extend with investigation sessions, Q&A exchanges, and investigation reports
- Phase 43 report viewer route and document-style reader — investigation reports use the same viewer; add "Investigation Report" as a new report type
- `pulse-mockup/src/components/ui/radio-group.tsx` (shadcn/ui) — base component for Q&A choices styled as selectable buttons
- `pulse-mockup/src/components/ui/textarea.tsx` — free-text "add your own answer" input in each Q&A exchange
- `pulse-mockup/src/components/ui/scroll-area.tsx` — scrollable Q&A thread container

### Established Patterns
- Full-page routes for detail views (`/signals`, `/reports/[id]`) — investigation page follows same pattern
- Document-style report viewer from Phase 43 — investigation report renders in same viewer
- Auto-navigate after action completes (detection → signals; investigation → report viewer)
- Sticky loading states with labeled steps (detection loading pattern) — reference for report generation loading

### Integration Points
- Signal detail panel (right column of 3-column signals layout) — needs a new "Investigation" section
- Signal list card — add investigation status badge
- Phase 43 report viewer — add "Investigation Report" type with its specific content sections
- `mock-data.ts` — new types needed: `InvestigationSession`, `QAExchange`, `InvestigationReport`
- Collection Reports tab (Phase 43) — investigation reports should also appear there as "Investigation Report" type

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 44-guided-investigation-explain*
*Context gathered: 2026-03-04*
