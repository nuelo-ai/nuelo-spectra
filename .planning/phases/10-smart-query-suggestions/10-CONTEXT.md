# Phase 10: Smart Query Suggestions - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate and display intelligent, context-aware query suggestions that help users start interacting with their data. Covers two touchpoints: initial suggestions on empty chat state (generated at upload) and follow-up suggestions on Data Cards (generated per analysis). Reduces blank-page intimidation and guides users toward deeper analysis.

</domain>

<decisions>
## Implementation Decisions

### Suggestion content & quality
- LLM-generated from the data profile (columns, types, stats) — not template-based
- Use real column names but wrap in natural language that explains intent — users may not understand their own column headers (e.g., "See how **Revenue** breaks down across different **Region** categories" not just "Group Revenue by Region")
- Mix of simple and advanced suggestions — cover beginners and power users
- 5-6 initial suggestions total

### Suggestion categories
- LLM decides categories based on what makes sense for each specific dataset (not fixed General/Benchmarking/Trend)
- Categories shown as grouped headers above chips
- Claude's Discretion: exact category names and distribution of suggestions per category

### Visual presentation
- Clickable chips/pills style (compact rounded buttons)
- Grouped under category headers (not flat)
- Centered in empty chat area (like ChatGPT's suggestion layout)
- Generic greeting above chips: "What would you like to know about your data?"
- No loading skeleton needed — suggestions are pre-generated at upload time

### Generation timing & source
- Generated during onboarding (same LLM call as data summary — extend onboarding prompt)
- Stored in database alongside data_summary for instant loading
- Shown on empty chat state (zero messages in tab)
- No refresh/regenerate option — generated once at upload

### Interaction behavior
- Default: auto-send immediately on click (zero friction to first result)
- Configurable in global YAML settings to instead populate chat input for editing before send
- After clicking one suggestion, all remaining chips fade out with animation
- No loading state for suggestions — already in DB when chat opens

### Follow-up suggestions on Data Cards
- 2-3 follow-up suggestions shown at bottom of each Data Card
- Based on the analysis just completed (query + result → natural next steps)
- Same chip/pill visual style as initial suggestions for consistency
- Generated during Data Analysis Agent response (same LLM call, included in stream)
- Clicking a follow-up auto-sends (same behavior as initial suggestions, respects YAML config)

</decisions>

<specifics>
## Specific Ideas

- Suggestions should feel like a knowledgeable analyst looking at the data for the first time — "here's what I'd explore first"
- Follow-up suggestions should feel like a natural continuation — "now that we've seen X, you might want to..."
- The chip interaction should feel immediate — click and the analysis starts, no intermediate steps

</specifics>

<deferred>
## Deferred Ideas

- Show suggestions in Data Summary panel (info icon on sidebar) — surface stored suggestions alongside the data profile for re-discovery after initial chat
- Suggestion quality feedback (thumbs up/down) — could improve generation over time

</deferred>

---

*Phase: 10-smart-query-suggestions*
*Context gathered: 2026-02-08*
