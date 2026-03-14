---
phase: quick-6
plan: 6
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
  - frontend/src/components/workspace/signal-list-panel.tsx
autonomous: true
requirements: [QUICK-6]

must_haves:
  truths:
    - Signal cards in the list panel show compact 1.5-unit gaps between them in Safari
    - Signal list panel scroll container does not expand beyond its available height in Safari
    - Layout is unchanged in Chrome and other browsers
  artifacts:
    - path: "frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx"
      provides: "Detection Results page root container height fix"
      contains: "h-full"
    - path: "frontend/src/components/workspace/signal-list-panel.tsx"
      provides: "Signal list panel with Safari-safe flex scroll container"
      contains: "flex flex-col gap-1.5"
  key_links:
    - from: "signals/page.tsx outer container"
      to: "SignalListPanel h-full"
      via: "constrained height chain"
      pattern: "h-full.*flex flex-col"
---

<objective>
Fix excessive vertical spacing between signal cards in the Signal List panel on Safari.

Purpose: Safari renders flex children differently when the root height is unconstrained — `h-screen` on the outer container breaks the height constraint chain, causing the inner `flex-1` scroll area to expand and push cards apart. Margin-based spacing (`space-y-*`) also behaves inconsistently in Safari flex containers compared to `gap`.

Output: Signal cards display with correct compact spacing (matching Chrome) in Safari without affecting other browsers.
</objective>

<execution_context>
@/Users/marwazisiagian/.claude/get-shit-done/workflows/execute-plan.md
@/Users/marwazisiagian/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Relevant files (read before editing):
@frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
@frontend/src/components/workspace/signal-list-panel.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix root container height and signal list spacing</name>
  <files>
    frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
    frontend/src/components/workspace/signal-list-panel.tsx
  </files>
  <action>
Two targeted changes to fix Safari's flex height miscalculation and margin-based spacing issue:

**Change 1 — signals/page.tsx, line 155:**
Change the outer container from `h-screen` to `h-full`:
```tsx
// BEFORE
<div className="flex flex-col h-screen">

// AFTER
<div className="flex flex-col h-full">
```
Reason: `h-screen` inside a nested flex layout breaks Safari's height constraint chain. The workspace shell already provides a bounded `h-full` context — using `h-screen` again inside it causes Safari to recalculate to full viewport height, unconstrained by the parent, which causes flex children to over-expand. `h-full` correctly inherits the parent's constrained height.

**Change 2 — signal-list-panel.tsx, inner list container (line 76):**
Change `space-y-1.5` to `flex flex-col gap-1.5` on the inner list wrapper div:
```tsx
// BEFORE
<div className="p-2 space-y-1.5">

// AFTER
<div className="p-2 flex flex-col gap-1.5">
```
Reason: `space-y-*` uses `margin-top` on children. In Safari, when a flex scroll container's height is not properly constrained, margin-based spacing can expand unexpectedly. `gap` on a flex column is intrinsic to the flex algorithm and does not have this issue — it behaves identically on Safari and Chrome.

Do NOT change anything else in these files. Only these two targeted edits.
  </action>
  <verify>
    <automated>cd /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend && npx tsc --noEmit 2>&1 | head -20</automated>
  </verify>
  <done>
    - `signals/page.tsx` outer wrapper uses `h-full` (not `h-screen`)
    - `signal-list-panel.tsx` inner list div uses `flex flex-col gap-1.5` (not `space-y-1.5`)
    - TypeScript compilation passes with no new errors
  </done>
</task>

</tasks>

<verification>
After the edit, visually verify in Safari (if available): open the Detection Results page for a collection with signals — cards should appear compact with ~6px gaps between them, matching Chrome's layout.
</verification>

<success_criteria>
Signal card list renders with correct compact spacing in Safari. No layout change visible in Chrome. TypeScript compilation clean.
</success_criteria>

<output>
After completion, create `.planning/quick/6-fix-bug-on-the-signal-list-panel-where-t/6-SUMMARY.md`
</output>
