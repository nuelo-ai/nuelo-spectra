---
phase: 06-frontend-ui-interactive-data-cards
plan: 05
subsystem: frontend-data-visualization
status: complete
completed: 2026-02-04
duration: 4min

tags:
  - data-cards
  - tanstack-table
  - progressive-rendering
  - data-visualization

requires:
  phases: [06-04]
  context: [SSE streaming, chat interface, streaming events]

provides:
  infrastructure: [DataTable with TanStack Table, progressive DataCard rendering]
  components: [DataCard, DataTable]
  patterns: [progressive rendering, collapsible cards, table sorting/filtering/pagination]

affects:
  - 06-06: Download functionality will add buttons to DataCard
  - 06-07: Code display will integrate into DataCard

tech-stack:
  added:
    - "@tanstack/react-table": "^8.21.3" (already installed)
  patterns:
    - TanStack Table v8 for interactive data tables
    - Progressive rendering based on streaming events
    - Collapsible UI pattern for card management

key-files:
  created:
    - frontend/src/components/data/DataTable.tsx
    - frontend/src/components/chat/DataCard.tsx
    - frontend/src/components/ui/table.tsx
    - frontend/src/components/ui/collapsible.tsx
    - frontend/src/components/ui/badge.tsx
  modified:
    - frontend/src/components/chat/ChatMessage.tsx
    - frontend/src/components/chat/ChatInterface.tsx

decisions:
  - decision: "Collapsible component for card expand/collapse"
    rationale: "Prevents visual clutter with multiple result cards; users can focus on latest results"
    impact: "Auto-collapse previous cards when new card completes; manual toggle via header click"
  - decision: "Parse execution_result as JSON for table data"
    rationale: "Backend returns execution results as JSON strings; need to extract columns/rows"
    impact: "ChatMessage handles parsing and passes structured data to DataCard"
  - decision: "Progressive rendering via streaming events"
    rationale: "Show sections as data becomes available (brief -> table -> explanation)"
    impact: "DataCard receives isStreaming prop and shows loading states for pending sections"
  - decision: "TanStack Table v8 for data tables"
    rationale: "Industry standard, headless table library with built-in sorting/filtering/pagination"
    impact: "DataTable component is fully interactive without custom state management"
  - decision: "First line of content as query brief"
    rationale: "Simple extraction for card header without additional backend changes"
    impact: "Query Brief shows first line of analysis text"
---

# Phase 06 Plan 05: Interactive Data Cards with TanStack Table Summary

**One-liner:** Progressive-rendering Data Cards with sortable/filterable/paginated tables using TanStack Table v8

---

## What Was Built

### DataTable Component

**Interactive Table with TanStack Table:**
- TanStack Table v8 state management (sorting, filtering, pagination)
- Click column headers to toggle sort: ascending → descending → unsorted
- Sort indicators: ChevronUp (asc), ChevronDown (desc), ChevronsUpDown (unsorted)
- Global search filter across all columns with search input
- Pagination: 10 rows per page with Previous/Next controls
- Page indicator: "Page X of Y"
- Alternate row backgrounds for readability (even/odd styling)
- Rounded borders matching card aesthetic
- Horizontal scroll for wide tables (overflow-x-auto)

**Edge Case Handling:**
- Empty data: "No data available" message
- Empty columns: "No columns defined" message
- Null/undefined cell values: render as empty string

### DataCard Component

**3-Section Progressive Rendering:**

**Section 1: Query Brief (Header)**
- Always visible in collapsible trigger
- Shows first line of analysis as card title
- Badge: "Data Card"
- Chevron icon rotates on collapse/expand
- Clickable to toggle expand/collapse

**Section 2: Data Table**
- Renders when execution_result contains tabular data
- Uses DataTable component for full interactivity
- Loading state: spinning loader with "Loading data..." while streaming
- Heading: "Data Results"

**Section 3: AI Explanation**
- Renders when analysis text is available
- Formatted text in muted background container
- Loading state: TypingIndicator while streaming
- Heading: "Analysis"

**Progressive Flow:**
1. Query Brief appears immediately (from first line of content)
2. Data Table appears when execution_result arrives in node_complete event
3. AI Explanation streams character-by-character via content_chunk events

**Collapsible Behavior:**
- Cards default to expanded when first created
- Auto-collapse previous cards when new card completes
- Manual toggle via header click
- Smooth collapse/expand animation

**Placeholders for Future Plans:**
- Comment: `{/* Download buttons added by Plan 06 */}`
- Comment: `{/* Code display added by Plan 06 */}`

### ChatMessage Integration

**Structured Data Detection:**
- Checks `message.metadata_json` for:
  - `generated_code`
  - `execution_result`
  - Analysis text in `content`
- Renders DataCard for assistant messages with metadata
- Falls back to plain text bubble for non-structured messages (user messages, errors, simple responses)

**Execution Result Parsing:**
- Handles JSON string parsing
- Extracts columns/rows from array of objects
- Supports pre-structured `{columns: [], rows: []}` format
- Handles arrays directly (extracts keys from first object)

### ChatInterface Updates

**Collapse State Management:**
- Tracks collapsed cards via Set<messageId>
- `toggleCardCollapse(messageId)` for manual toggle
- Auto-collapse on stream completion:
  - Collapses all previous assistant messages with structured data
  - Keeps newest card expanded

**Streaming DataCard Rendering:**
- `getStreamingDataCard()` extracts progressive data from events:
  - Query brief: "Analyzing your request..."
  - Table data: parsed from node_complete events with execution_result
  - Explanation: streamed text from content_chunk events
- Renders DataCard if node_complete events indicate structured response
- Falls back to regular ChatMessage for non-structured streams

---

## Requirements Coverage

From must_haves:

✅ **Query results display as Data Cards inline with chat messages** - DataCard renders in ChatMessage for structured data
✅ **Data Cards show Query Brief section at the top** - First line as collapsible header
✅ **Data Cards show Data Table section in the middle when table data is available** - Section 2 with DataTable
✅ **Data Cards show AI Explanation section at the bottom** - Section 3 with analysis text
✅ **Data tables are sortable by clicking column headers** - TanStack Table sorting with arrow indicators
✅ **Data tables are filterable with a global search input** - Search input above table
✅ **Data tables paginate with Previous/Next controls** - 10 rows/page with page indicator
✅ **Sections appear progressively during streaming** - Query brief first, table second, explanation last
✅ **Older Data Cards are collapsible to show just the Query Brief** - Auto-collapse previous cards on new completion

---

## Technical Implementation

### TanStack Table Setup

```typescript
const tableColumns = useMemo<ColumnDef<Record<string, any>>[]>(
  () =>
    columns.map((col) => ({
      accessorKey: col,
      header: col,
      cell: (info) => String(info.getValue() ?? ""),
    })),
  [columns]
);

const table = useReactTable({
  data,
  columns: tableColumns,
  state: { sorting, globalFilter },
  onSortingChange: setSorting,
  onGlobalFilterChange: setGlobalFilter,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  initialState: {
    pagination: { pageSize: 10 },
  },
});
```

### Execution Result Parsing

```typescript
const parseExecutionResult = (result: any) => {
  if (!result) return null;

  // Parse JSON string
  if (typeof result === "string") {
    try {
      const parsed = JSON.parse(result);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return {
          columns: Object.keys(parsed[0]),
          rows: parsed,
        };
      }
    } catch {
      return null;
    }
  }

  // Handle pre-structured data
  if (result.columns && Array.isArray(result.columns)) {
    return {
      columns: result.columns,
      rows: result.rows || result.data || [],
    };
  }

  return null;
};
```

### Progressive Rendering Flow

```typescript
// In ChatInterface during streaming:
const getStreamingDataCard = () => {
  const queryBrief = "Analyzing your request...";

  // Extract table data from execution node_complete event
  let tableData = undefined;
  const executionEvent = events.find(
    (e) => e.type === "node_complete" && e.node === "execute"
  );
  if (executionEvent?.data?.execution_result) {
    // Parse and structure table data
  }

  // Explanation from streamed text
  const explanation = streamedText || undefined;

  return { queryBrief, tableData, explanation };
};
```

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Integration Points

**With Backend:**
- Consumes metadata_json from ChatMessageResponse:
  - generated_code
  - execution_result (parsed for table data)
  - analysis (rendered as explanation)

**With Frontend (06-04):**
- Uses useSSEStream events for progressive rendering
- Integrates into ChatInterface and ChatMessage
- Auto-scrolls on card expand/collapse

**For Future Plans:**
- 06-06: Download buttons will be added to DataCard
- 06-07: Code display will be integrated into DataCard

---

## Testing & Verification

Build verification:
```bash
cd frontend && npm run build
# ✓ Compiled successfully in 2.4s
```

TypeScript verification:
```bash
cd frontend && npx tsc --noEmit --pretty
# No errors
```

Manual verification:
- [x] DataTable renders with sorting (click headers)
- [x] DataTable global filter searches across all columns
- [x] DataTable pagination shows 10 rows/page with Previous/Next
- [x] DataCard renders 3 sections progressively during streaming
- [x] Older Data Cards collapse to show Query Brief only
- [x] ChatMessage correctly decides between plain text and DataCard
- [x] Empty data tables show "No data available"
- [x] Build passes with zero TypeScript errors

---

## Next Phase Readiness

**Ready for 06-06 (Download Functionality):**
- DataCard has placeholders for download buttons
- execution_result available for CSV/JSON export
- DataTable ready for data export

**Ready for 06-07 (Code Display):**
- DataCard has placeholder for code display
- generated_code available in metadata_json
- Collapsible pattern established for code blocks

**Blockers:** None

**Concerns:** None

---

## Performance Notes

**Rendering:**
- useMemo for TanStack Table column definitions prevents re-creation on every render
- Pagination limits DOM nodes to 10 rows per page (improves performance for large datasets)
- Progressive rendering shows data as soon as available (better perceived performance)

**State Management:**
- Set<string> for collapsed cards is efficient for add/remove operations
- Auto-collapse only triggers on stream completion (not on every message)

**Table Interactivity:**
- TanStack Table handles all table state internally (no prop drilling)
- Sorting/filtering/pagination state isolated to DataTable component

---

## Lessons Learned

1. **TanStack Table simplifies complex table features** - Sorting, filtering, and pagination work out-of-the-box with minimal setup
2. **Progressive rendering improves UX** - Showing sections as they arrive makes long AI responses feel faster
3. **Collapsible pattern reduces clutter** - Auto-collapse previous cards keeps focus on latest result
4. **Execution result parsing needs flexibility** - Backend can return JSON strings or structured objects; parsing layer handles both

---

*Phase: 06-frontend-ui-interactive-data-cards | Plan: 05 | Completed: 2026-02-04*
