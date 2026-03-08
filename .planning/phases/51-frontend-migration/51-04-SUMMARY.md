---
phase: 51-frontend-migration
plan: 04
subsystem: ui
tags: [react, nextjs, plotly, signals, workspace, detection-results]

requires:
  - phase: 51-01
    provides: "Hex.tech palette, UI components, workspace types/hooks/store"
  - phase: 51-02
    provides: "UnifiedSidebar, (workspace) route group layout"
  - phase: 51-03
    provides: "Collection detail page, signal hooks, workspace store"
provides:
  - "Detection Results page with split-panel layout (signal list + detail)"
  - "SignalChartRenderer converting chart_data + chart_type to Plotly"
  - "SignalListPanel with severity-sorted signal cards"
  - "SignalDetailPanel with chart, analysis markdown, evidence grid, disabled action buttons"
affects: [52-admin-and-qa]

tech-stack:
  added: []
  patterns:
    - "Plotly chart rendering via existing ChartRenderer with signal-specific JSON builder"
    - "ReactMarkdown + remarkGfm for analysis text rendering"
    - "Split-panel layout with fixed-width list and flex-1 detail"

key-files:
  created:
    - frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx
  modified:
    - frontend/src/components/workspace/signal-chart-renderer.tsx
    - frontend/src/components/workspace/signal-list-panel.tsx
    - frontend/src/components/workspace/signal-detail-panel.tsx

decisions:
  - "Signal chart_data is Plotly fig.to_json() output rendered by existing ChartRenderer"
  - "Investigation and What-If buttons disabled (opacity-50) with 'Coming in a future update' tooltip"
  - "Highest-severity signal auto-selected on page load via useEffect"

verification:
  build: pass
  uat: pass — 4 signals rendered in split-panel, Plotly charts visible, severity sorting correct
---

## What Was Done

Built the Detection Results page at `/workspace/collections/[id]/signals` with split-panel layout matching the pulse-mockup design.

**SignalChartRenderer**: Converts signal `chart_data` + `chart_type` into Plotly JSON, renders via existing `ChartRenderer` component. Multi-strategy extraction handles various Plotly output formats (native, points arrays, histograms, bubble charts, grouped data).

**SignalListPanel**: Scrollable signal card list sorted by severity (critical → warning → info). Selected signal highlighted with border accent.

**SignalDetailPanel**: Full signal detail with title, severity/category badges, Plotly chart, analysis text (ReactMarkdown + remarkGfm), 2x2 evidence grid, and disabled Investigation/What-If buttons.

**Detection Results Page**: Split layout with 350px signal list (left) and flex-1 detail panel (right). Back button to collection detail. Skeleton loading, error with retry, empty state with "Run Detection" link. Auto-selects highest-severity signal on load.

## Additional Fixes (Pipeline & Frontend)

22 bug fixes applied across backend and frontend during Phase 51 execution:

1. MissingGreenlet fix: direct INSERT into pulse_run_files association table
2. Polling URL fix: `/pulse-runs/{id}` matches backend route
3. Status mismatch fix: `"completed"` not `"complete"`
4. Sticky loading page: reset detectionStatus on mount
5. CreditService.refund: added missing balance_after field
6. User context textarea added to RunDetectionBanner
7. Double-click fix: collectionFiles as single source of truth
8. scipy/openpyxl/plotly added to allowlist.yaml
9. Sandbox FileNotFoundError: correct filenames in code gen prompt
10. Re-fetch pulse_run after graph.ainvoke() to avoid stale session
11. Per-signal try/catch in persistence loop
12. Signal title fix: merge candidate metadata into validated results
13. Chart renderer multi-strategy extraction
14. Analysis markdown rendering with ReactMarkdown
15. Report detail page created matching mockup design
16. onClick handler type fix for handleRunDetection
17. Moved code_gen_prompt to prompts.yaml
18. Added get_agent_config_field() helper
19. Updated code_gen_prompt to use Plotly fig.to_json()
20. Debug logging cleaned up (removed *** markers)
21. GET /collections/{id}/signals endpoint added (missing from Phase 48)
22. DataSummaryPanel uses Sheet instead of Dialog

## Known Issues

- Pipeline architecture mismatch: `_validate_single_candidate` does inline LLM code gen instead of reusing Coding Agent + Visualization Agent. Deferred to dedicated refactor phase.
- LLM-generated code sometimes guesses wrong column names, causing candidate validation failures. Same root cause — pipeline refactor will address.
