---
phase: quick-5
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/components/chat/QuerySuggestions.tsx
autonomous: true
requirements:
  - QUICK-5
must_haves:
  truths:
    - "Query suggestions render as multiple columns (one per category)"
    - "Each column has an icon and category title as a header"
    - "Each suggestion item is a card matching the Signal card visual style (border, rounded-lg, hover accent)"
    - "Clicking a card still triggers onSelect and fades out remaining cards"
    - "Layout is responsive — collapses gracefully on narrow screens"
  artifacts:
    - path: "frontend/src/components/chat/QuerySuggestions.tsx"
      provides: "Redesigned query suggestions with column-per-category layout"
  key_links:
    - from: "frontend/src/components/session/WelcomeScreen.tsx"
      to: "frontend/src/components/chat/QuerySuggestions.tsx"
      via: "categories prop passthrough"
      pattern: "QuerySuggestions.*categories"
---

<objective>
Redesign the QuerySuggestions component on the chat welcome screen to use a beautiful multi-column card layout inspired by ChatGPT's welcome screen and Spectra's Signal card visual style.

Purpose: The current pill-chip layout feels flat and low-hierarchy. The new design groups suggestions into visually distinct columns with icon headers, and renders each suggestion as a bordered card for better scannability and visual polish.

Output: Redesigned `QuerySuggestions.tsx` — same props interface, same behavior, new visual layout.
</objective>

<execution_context>
@/Users/marwazisiagian/.claude/get-shit-done/workflows/execute-plan.md
@/Users/marwazisiagian/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Key reference files (read before implementing):
- `frontend/src/components/chat/QuerySuggestions.tsx` — current implementation (replace)
- `frontend/src/components/workspace/signal-card.tsx` — visual reference for card style
- `frontend/src/components/session/WelcomeScreen.tsx` — consumer (props must stay compatible)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Redesign QuerySuggestions with column-per-category card layout</name>
  <files>frontend/src/components/chat/QuerySuggestions.tsx</files>
  <action>
Replace the existing QuerySuggestions component with a new layout. Keep the exact same props interface (categories, onSelect, autoSend) and the same fade-out-on-select behavior.

**Layout structure:**

The outer container changes from `flex flex-col items-center` to a responsive grid of columns — one column per category. Use CSS grid: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` (adjust col count to match number of categories naturally). The container should be `w-full max-w-4xl mx-auto`.

Remove the existing greeting text ("What would you like to know...") — it lives in WelcomeScreen already.

**Column header (per category):**

Each category column renders a header with:
- A small icon from lucide-react. Assign icons based on common category name keywords:
  - words like "trend", "growth", "change" → `TrendingUp`
  - words like "compare", "segment", "break" → `BarChart2`
  - words like "summary", "overview", "general" → `Layers`
  - words like "forecast", "predict", "future" → `Sparkles`
  - fallback → `MessageSquare`
  The icon mapping should be a lookup that does a case-insensitive `.includes()` on the category name.
- Category name as text: `text-xs font-semibold uppercase tracking-widest text-muted-foreground`
- Icon: `h-3.5 w-3.5 text-muted-foreground`
- Header container: `flex items-center gap-1.5 mb-3 pb-2 border-b border-border`

**Suggestion cards (per item in category.queries):**

Each suggestion renders as a `<button>` styled as a card — matching the Signal card visual pattern from `signal-card.tsx`:

```
rounded-lg border border-border bg-transparent p-3 w-full text-left
transition-all duration-150
hover:bg-accent/50 hover:border-primary/30
```

When selected (`isSelected`): `border-primary bg-primary/5 shadow-sm`
When fading out (`isFadingOut`): `opacity-0 transition-opacity duration-300`
When `selected !== null` (any selected): `disabled` on all buttons

Inside the card:
- The suggestion text: `text-sm text-foreground leading-snug line-clamp-3`
- No badge or additional metadata needed (unlike SignalCard)

**ReactMarkdown:** Keep the same `ReactMarkdown` rendering inside the card text span for markdown bold support.

**Animation:** Wrap the entire grid in `<div style={{ animation: "var(--animate-fadeIn)" }}>` to keep the fade-in entrance.

**Import list needed:**
- `useState` from react
- `ReactMarkdown` from react-markdown
- `TrendingUp, BarChart2, Layers, Sparkles, MessageSquare` from lucide-react
- `LucideIcon` type from lucide-react

The `QuerySuggestionsProps` interface stays identical — do not change it.
  </action>
  <verify>
    <automated>cd /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend && npx tsc --noEmit --project tsconfig.json 2>&1 | grep -E "QuerySuggestions|error TS" | head -20</automated>
  </verify>
  <done>
    - TypeScript compiles with no errors in QuerySuggestions.tsx
    - Component renders categories as side-by-side columns (grid), not stacked rows
    - Each column has icon + uppercase label header with a bottom border
    - Each suggestion is a bordered card (rounded-lg border) with hover:bg-accent/50 and hover:border-primary/30
    - Selecting a card adds border-primary bg-primary/5 shadow-sm, fades out others
    - Props interface unchanged — WelcomeScreen integration requires no edits
  </done>
</task>

</tasks>

<verification>
1. Run TypeScript check: `cd frontend && npx tsc --noEmit` — must pass with no errors in the changed file
2. Visually confirm (dev server): query suggestions appear as a multi-column card grid, not pill chips
3. Confirm clicking a card sends the query (onSelect fires) and remaining cards fade out
</verification>

<success_criteria>
QuerySuggestions renders a responsive multi-column card layout where:
- Each category = one column with icon + label header
- Each suggestion = a Signal-card-style bordered card
- Click behavior and fade-out animation are identical to the original
- No TypeScript errors, no changes required to WelcomeScreen
</success_criteria>

<output>
After completion, create `.planning/quick/5-update-the-query-suggestion-on-the-chat-/5-SUMMARY.md`
</output>
