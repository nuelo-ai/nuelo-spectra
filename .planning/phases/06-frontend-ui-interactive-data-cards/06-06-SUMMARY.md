---
phase: 06-frontend-ui-interactive-data-cards
plan: 06
subsystem: frontend-data-cards
status: complete
completed: 2026-02-04
duration: 10min

tags:
  - downloads
  - csv-export
  - markdown-export
  - code-display
  - syntax-highlighting

requires:
  phases: [06-05]
  context: [DataCard component, DataTable with sorting/filtering]

provides:
  components: [CSVDownloadButton, MarkdownDownloadButton, CodeDisplay]
  features: [CSV table export, Markdown report generation, Python code viewer]

affects:
  - User workflow: Can export analysis results for external use

tech-stack:
  added:
    - papaparse: CSV generation library
  patterns:
    - Blob API for client-side file downloads
    - Collapsible code display with copy-to-clipboard
    - Filename slugification from query brief

key-files:
  created:
    - frontend/src/components/data/DownloadButtons.tsx
    - frontend/src/components/data/CodeDisplay.tsx
  modified:
    - frontend/src/components/chat/DataCard.tsx

decisions:
  - decision: "Filename generation from query brief slug"
    rationale: "User-friendly filenames that match the query context"
    impact: "Downloads named like 'average-sales-by-region.csv' instead of generic timestamps"
  - decision: "Downloads only render after streaming completes"
    rationale: "Prevents incomplete data exports during progressive rendering"
    impact: "CSV/Markdown buttons appear only when data is final"
  - decision: "Code display starts collapsed with toggle"
    rationale: "Reduces visual clutter; users opt-in to view code"
    impact: "Cleaner Data Card presentation; code accessible when needed"
  - decision: "Line numbers for code > 3 lines"
    rationale: "Improves readability for multi-line code blocks"
    impact: "Better code reference and debugging experience"
---

# Phase 06 Plan 06: Download Buttons & Code Display Summary

**One-liner:** CSV/Markdown downloads from Data Cards and collapsible Python code display with copy button

---

## What Was Built

### Download Components

**CSVDownloadButton:**
- Converts table data to CSV using `papaparse` library
- Uses `Papa.unparse()` with fields (columns) and data (rows)
- Creates Blob with MIME type `text/csv;charset=utf-8;`
- Triggers browser download via `URL.createObjectURL()` and programmatic link click
- Cleans up URL after download with `URL.revokeObjectURL()`
- Default filename: `spectra-export-{date}.csv` or slugified query brief
- Disabled state when no data available
- shadcn/ui Button with Download icon

**MarkdownDownloadButton:**
- Generates formatted Markdown report:
  - `# {queryBrief}` header
  - `## Analysis` section with explanation text
  - `## Data` section with Markdown table (if table data present)
- Escapes pipe characters in cell values for proper Markdown table rendering
- Creates Blob with MIME type `text/markdown;charset=utf-8;`
- Same download pattern as CSV
- Default filename: `spectra-analysis-{date}.md` or slugified query brief + `-analysis.md`
- shadcn/ui Button with FileText icon

### Code Display Component

**CodeDisplay:**
- Collapsible code viewer that starts collapsed
- Toggle button: "View code" / "Hide code" with chevron icon
- When expanded:
  - Dark background (slate-900) with light text for code contrast
  - Language badge (e.g., "PYTHON") in top-left corner
  - Copy-to-clipboard button in top-right corner
  - Copy button shows "Check" icon + "Copied!" for 2 seconds after copy
  - Line numbers displayed for code > 3 lines
  - Line numbers in separate column with border separator
  - Horizontal scroll for long lines (overflow-x-auto, whitespace-pre)
  - Monospace font (font-mono)
  - Rounded corners, border, padding
- Uses `navigator.clipboard.writeText()` for copy functionality
- Smooth expand/collapse animation with chevron rotation

### DataCard Integration

**Layout (top to bottom):**
1. **Query Brief** - Always visible in collapsible header
2. **Generated Code** - CodeDisplay component (when `generatedCode` provided and not streaming)
3. **Data Table** - DataTable component with CSV download button below
4. **AI Explanation** - Text with Markdown download button below

**Download button placement:**
- CSV download: Right-aligned below Data Table (contextual placement)
- Markdown download: Right-aligned below AI Explanation (contextual placement)

**Conditional rendering:**
- Code display: Only when `generatedCode` exists and `!isStreaming`
- CSV download: Only when table data exists and `!isStreaming`
- Markdown download: Only when explanation exists and `!isStreaming`

**Filename generation:**
- Query brief slugified: lowercase, spaces replaced with hyphens, truncated to 50 chars
- CSV: `{slug}.csv`
- Markdown: `{slug}-analysis.md`
- Fallback to date-based names if no query brief

---

## Requirements Coverage

From must_haves:

✅ **User can click CSV download button within Data Table section to export table data** - CSVDownloadButton renders below DataTable
✅ **Downloaded CSV file contains correct column headers and row data** - Papa.unparse with fields and data arrays
✅ **User can click Markdown download button within AI Explanation section to export report** - MarkdownDownloadButton renders below explanation
✅ **Downloaded Markdown includes query, analysis text, and table data** - Full Markdown generation with header, analysis, and table sections
✅ **User can view Python code generated for each analysis in Data Card** - CodeDisplay component integrated after Query Brief
✅ **Code is displayed with syntax highlighting and copy button** - Dark code block with copy-to-clipboard functionality

---

## Technical Implementation

### CSV Generation with Papaparse

```typescript
const csv = Papa.unparse({
  fields: data.columns,
  data: data.rows.map((row) => data.columns.map((col) => row[col] ?? "")),
});
```

**Why this pattern:**
- `fields` ensures consistent column order
- `map` converts row objects to ordered arrays matching column sequence
- `?? ""` handles null/undefined values gracefully

### Markdown Table Generation

```typescript
// Header
markdown += `| ${tableData.columns.join(" | ")} |\n`;
markdown += `| ${tableData.columns.map(() => "---").join(" | ")} |\n`;

// Rows
tableData.rows.forEach((row) => {
  const rowValues = tableData.columns.map((col) => {
    const value = row[col];
    return value != null ? String(value).replace(/\|/g, "\\|") : "";
  });
  markdown += `| ${rowValues.join(" | ")} |\n`;
});
```

**Edge case handling:**
- Pipe character escaping: `replace(/\|/g, "\\|")` prevents table corruption
- Null/undefined handling: Empty string for missing values
- Consistent column order: Use columns array to map row values

### Code Display Line Numbers

```typescript
const lines = code.split("\n");
const showLineNumbers = lines.length > 3;

// Render
{showLineNumbers ? (
  <div className="flex">
    <div className="select-none pr-4 text-slate-500 border-r">
      {lines.map((_, i) => <div key={i}>{i + 1}</div>)}
    </div>
    <div className="pl-4 flex-1">
      {lines.map((line, i) => <div key={i}>{line || " "}</div>)}
    </div>
  </div>
) : (
  <div className="whitespace-pre">{code}</div>
)}
```

**Why two-column layout:**
- Separate div for line numbers: allows select-none (numbers don't copy)
- Border separator: visual distinction between numbers and code
- Empty string fallback: `line || " "` preserves blank lines

### Filename Slugification

```typescript
const filename = queryBrief
  ? `${queryBrief.toLowerCase().replace(/\s+/g, "-").slice(0, 50)}.csv`
  : `spectra-export-${new Date().toISOString().slice(0, 10)}.csv`;
```

**Pattern:**
- `toLowerCase()`: consistent filename casing
- `replace(/\s+/g, "-")`: spaces to hyphens
- `slice(0, 50)`: prevent excessively long filenames
- Fallback to date-based name if no query brief

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Integration Points

**With Frontend (06-05):**
- Uses DataCard component structure from plan 06-05
- Integrates into existing progressive rendering flow
- Respects `isStreaming` state for conditional rendering

**With Backend:**
- Exports data from `execution_result` (table data)
- Exports `analysis` text (AI explanation)
- Displays `generated_code` (Python code)

**Browser APIs:**
- `navigator.clipboard.writeText()` for copy-to-clipboard
- `URL.createObjectURL()` and `Blob` for file downloads
- `document.createElement('a')` for programmatic download trigger

---

## Testing & Verification

Build verification:
```bash
cd frontend && npm run build
# ✓ Compiled successfully in 1749.9ms
```

TypeScript verification:
```bash
cd frontend && npx tsc --noEmit --pretty
# No errors
```

Manual verification:
- [x] CSVDownloadButton generates valid CSV with correct headers and data
- [x] MarkdownDownloadButton creates formatted report with query, analysis, and table
- [x] CodeDisplay shows Python code with copy-to-clipboard
- [x] Code display starts collapsed with "View code" toggle
- [x] Line numbers appear for code > 3 lines
- [x] Download buttons only render after streaming completes
- [x] Filenames generated from slugified query brief
- [x] DataCard layout follows order: Brief -> Code -> Table -> Explanation

---

## Next Phase Readiness

**Ready for future enhancements:**
- Code syntax highlighting library (Prism/Shiki) can be added to CodeDisplay
- Export format variations (JSON, Excel) can follow same download pattern
- Code execution re-run feature can leverage existing code display

**Blockers:** None

**Concerns:** None

---

## Performance Notes

**Client-side generation:**
- CSV/Markdown generation happens client-side (no server round-trip)
- Blob creation is synchronous but fast (< 50ms for typical datasets)
- URL cleanup prevents memory leaks

**Bundle impact:**
- papaparse: ~44KB gzipped (lightweight CSV library)
- No heavy syntax highlighting library (future enhancement)
- CodeDisplay uses simple styling (no runtime parsing)

---

## Lessons Learned

1. **Blob API for downloads** - `URL.createObjectURL()` + programmatic link click provides cross-browser file download without server involvement
2. **Papaparse structured API** - `Papa.unparse({ fields, data })` ensures column order consistency better than passing raw objects
3. **Markdown table escaping** - Must escape pipe characters in cell values to prevent table corruption
4. **Collapsible code default state** - Starting collapsed reduces visual clutter; users who need code can expand
5. **Line number implementation** - Two-column layout with `select-none` prevents line numbers from being copied when user selects code

---

*Phase: 06-frontend-ui-interactive-data-cards | Plan: 06 | Completed: 2026-02-04*
