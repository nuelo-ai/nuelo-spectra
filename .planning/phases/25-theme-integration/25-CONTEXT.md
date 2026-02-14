# Phase 25: Theme Integration - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Charts visually integrate with the platform's light and dark themes, using matching color palettes and readable text. This phase themes the Plotly charts and their surrounding elements — it does not add new chart types, new export formats, or new interactive features.

</domain>

<decisions>
## Implementation Decisions

### Color Palette
- Dark mode: Nord Aurora colors (Nord 11-15: red, orange, yellow, green, purple) for chart traces — vivid and high-contrast against dark backgrounds
- Light mode: Slightly darkened Nord Aurora variants — pure Aurora yellow/orange washes out on white, so deepen for legibility
- Priority is contrast and visibility above all else
- Chart backgrounds: subtle card-like tint (not fully transparent) to visually separate chart area from surrounding content
- Gridlines: very subtle (e.g. Nord 2 #434C5E at ~30% opacity) — visible but doesn't compete with data

### Theme Switching
- Instant swap when user toggles theme — no animated transitions
- App follows system dark/light preference with manual override (existing behavior)
- Only newly generated charts pick up the current theme — already-rendered charts in the conversation keep their original theme styling

### Chart Element Styling
- Text (titles, axis labels): Nord Snow (#D8DEE9, #E5E9F0, #ECEFF4) in dark mode — high contrast, bright white
- Axis tick marks and numbers: one step dimmer than axis labels — creates visual hierarchy (labels > ticks > gridlines)
- Tooltips: match the platform's existing tooltip style for consistency
- Legends: positioned below the chart (horizontal) — doesn't eat into chart width
- Pie/donut slice labels: white text overlaid on colored slices for high contrast

### Export Behavior
- Exported charts (PNG/SVG) use the current theme at time of export — dark mode exports dark chart
- PNG exports have filled background (theme background color) — looks complete as standalone image, not transparent
- SVG exports follow the same pattern

### Claude's Discretion
- Whether export buttons and chart type switcher need additional theming work (check if existing components already follow theme)
- Exact Nord Aurora darkened variants for light mode (tune for best contrast)
- Light mode card background tint color
- Tooltip styling specifics (match existing implementation)

</decisions>

<specifics>
## Specific Ideas

- Contrast and visibility is the top priority — colors must be clearly distinguishable in both themes
- Visual hierarchy for axis elements: labels brightest, tick marks slightly dimmer, gridlines very subtle

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 25-theme-integration*
*Context gathered: 2026-02-13*
