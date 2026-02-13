# Phase 23: Frontend Chart Rendering - Research

**Researched:** 2026-02-13
**Domain:** Plotly.js integration with React/Next.js, client-side chart rendering, responsive design
**Confidence:** HIGH

## Summary

Phase 23 implements frontend chart rendering for AI-generated Plotly visualizations delivered via SSE from Phase 22's backend. The technical challenge is integrating plotly.js-dist-min (~1MB) into a Next.js 16 App Router application while avoiding SSR issues, implementing responsive resize behavior, and creating polished loading/error states that don't alarm users.

The existing codebase already handles SSE streaming, progressive DataCard rendering with skeleton loaders, and Tailwind CSS theming (Nord dark theme). The integration strategy uses Next.js dynamic imports with `ssr: false` to defer plotly.js loading until chart data arrives, then renders using `Plotly.react()` (not `newPlot()`) for efficient updates.

**Primary recommendation:** Use Next.js dynamic import with `ssr: false`, render charts with `Plotly.react()` via useRef/useEffect, implement ResizeObserver for container-aware responsiveness (not just window resize), and use existing skeleton infrastructure for loading states.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Chart Placement & Data Relationship (LOCKED)
- Chart appears **below the data table** (table first priority, chart as supplementary visual)
- Chart is **always visible when present** - no collapse/hide controls, simpler UI
- Table scrolls independently with max height - chart stays visible above scrolling table
- Full design discretion to **revamp DataCard design** for visual appeal (using frontend design best practices)

### Loading States & Progression (LOCKED)
- Loading visual: **Spinner with text** ("Generating visualization...")
- Progress indication: **Stage indicators** showing progression ("Analyzing data..." → "Creating chart...")
- Chart transition: **Fade in smoothly** when loading completes
- Charts are interactive by default (zoom, pan, hover tooltips via Plotly.js)

### Failure States & Recovery (LOCKED)
- Failure display: **Subtle notification only** (small dismissible alert at top of DataCard, doesn't take chart space)
- Notification: **Persistent but dismissible** - stays until user clicks X to close
- **No retry in frontend** - Phase 22 backend handles retry logic (max 1 retry = 2 attempts). If frontend receives error, it's final.
- Error details: **Helpful context** - brief user-friendly explanation (e.g., "Chart couldn't be generated for this data type")

### Chart Sizing & Responsiveness (LOCKED)
- Height: **Dynamic based on data** - adjusts to data complexity (more data points = taller chart)
- Width: **Full container width** - chart spans entire DataCard width
- **Responsive to future changes** - if DataCard width increases later, chart follows responsively

### Claude's Discretion (FREEDOM AREAS)
- DataCard visual design and layout styling (open to full redesign)
- Loading state timing (when to show, perceived performance optimization)
- Mobile chart behavior (responsive design patterns)
- Resize event handling (performance/UX balance)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| plotly.js-dist-min | 3.3.1 (latest) | Plotly.js minimal bundle | ~1MB minified bundle (vs 3MB full), supports all core chart types, official partial distribution |
| @types/plotly.js-dist-min | latest | TypeScript definitions | Type safety for Plotly API calls, function signatures, config options |
| next/dynamic | 16.1.6 (included) | Client-side only imports | Next.js built-in for disabling SSR, prevents window/DOM errors during server render |
| React useRef + useEffect | 19.2.3 (included) | DOM manipulation pattern | Standard React pattern for imperative DOM APIs like Plotly.newPlot/react |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| use-resize-observer | 9.x (optional) | Container resize detection | If implementing ResizeObserver pattern (recommended over window resize) |
| @react-hook/resize-observer | 1.x (alternative) | Lightweight resize detection | Alternative to use-resize-observer, more performant (single observer) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| plotly.js-dist-min | react-plotly.js | Wrapper is outdated, not maintained for React 19, adds unnecessary abstraction |
| plotly.js-dist-min | plotly.js-basic-dist-min | Basic excludes 3D/mapbox/geo - safe for this project if only 2D charts needed, saves ~200KB |
| Plotly.react() | Plotly.newPlot() | newPlot() recreates entire chart on every update, react() intelligently diffs and updates |
| Dynamic import | Direct import | Direct import forces SSR rendering attempt, causes "window is not defined" errors |

**Installation:**
```bash
npm install plotly.js-dist-min
npm install --save-dev @types/plotly.js-dist-min
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/components/
├── chart/
│   ├── ChartRenderer.tsx        # Dynamic import wrapper, no SSR
│   ├── ChartSkeleton.tsx        # Loading state with stage indicators
│   └── ChartErrorAlert.tsx      # Subtle dismissible error notification
├── chat/
│   └── DataCard.tsx             # Modified to include chart section
```

### Pattern 1: Dynamic Import with SSR Disabled

**What:** Use Next.js dynamic import to load ChartRenderer component only on client-side, avoiding SSR hydration mismatch.

**When to use:** Any time importing libraries that depend on browser APIs (window, document) or DOM manipulation.

**Example:**
```typescript
// In DataCard.tsx
import dynamic from 'next/dynamic';

const ChartRenderer = dynamic(() => import('@/components/chart/ChartRenderer'), {
  ssr: false, // CRITICAL: Prevents server-side rendering
  loading: () => <ChartSkeleton />, // Shown while JS bundle loads
});

export function DataCard({ chartSpecs, ... }) {
  return (
    <div>
      {chartSpecs && <ChartRenderer data={chartSpecs} />}
    </div>
  );
}
```

**Source:** [Next.js Official Docs - Lazy Loading](https://nextjs.org/docs/pages/guides/lazy-loading)

### Pattern 2: Plotly.react() with useRef/useEffect

**What:** Use `Plotly.react()` (not `newPlot()`) to render/update charts efficiently. Attach to DOM via useRef.

**When to use:** Initial chart render and any subsequent updates (data changes, theme changes).

**Example:**
```typescript
// ChartRenderer.tsx
'use client';

import { useRef, useEffect } from 'react';
import Plotly from 'plotly.js-dist-min';

interface ChartRendererProps {
  data: string; // JSON string from backend
}

export function ChartRenderer({ data }: ChartRendererProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !data) return;

    try {
      const chartData = JSON.parse(data);

      // Plotly.react() intelligently updates existing chart or creates new one
      Plotly.react(
        chartRef.current,
        chartData.data || [],
        chartData.layout || {},
        {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        }
      );
    } catch (error) {
      console.error('Failed to render chart:', error);
    }

    // Cleanup on unmount
    return () => {
      if (chartRef.current) {
        Plotly.purge(chartRef.current); // Prevents memory leaks
      }
    };
  }, [data]);

  return <div ref={chartRef} className="w-full h-[400px]" />;
}
```

**Source:** [Plotly.js Function Reference](https://plotly.com/javascript/plotlyjs-function-reference/)

### Pattern 3: ResizeObserver for Container-Aware Responsiveness

**What:** Use ResizeObserver to detect container size changes (not just window resize) and trigger Plotly.Plots.resize().

**When to use:** When chart container can resize independently of window (collapsible panels, responsive grids, future layout changes).

**Example:**
```typescript
// ChartRenderer.tsx with ResizeObserver
import { useRef, useEffect } from 'react';
import Plotly from 'plotly.js-dist-min';

export function ChartRenderer({ data }: ChartRendererProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !data) return;

    const chartData = JSON.parse(data);
    Plotly.react(chartRef.current, chartData.data, chartData.layout, {
      responsive: true,
    });

    // Container-aware resize detection
    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current) {
        Plotly.Plots.resize(chartRef.current);
      }
    });

    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
  }, [data]);

  return <div ref={chartRef} className="w-full h-auto" />;
}
```

**Source:** [LogRocket - Using ResizeObserver in React](https://blog.logrocket.com/using-resizeobserver-react-responsive-designs/)

### Pattern 4: Progressive Loading with Stage Indicators

**What:** Show stage-aware skeleton loader while chart generates (backend) and bundle loads (frontend).

**When to use:** During SSE streaming when `visualization_requested` is true but `chart_specs` hasn't arrived yet.

**Example:**
```typescript
// ChartSkeleton.tsx
export function ChartSkeleton({ stage }: { stage?: string }) {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="flex items-center gap-2">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
        <p className="text-sm text-muted-foreground">
          {stage || "Generating visualization..."}
        </p>
      </div>
      <div className="skeleton h-[400px] w-full rounded-lg" />
    </div>
  );
}

// In DataCard.tsx
{isStreaming && visualizationRequested && !chartSpecs && (
  <ChartSkeleton stage={currentStatus} />
)}

{chartSpecs && (
  <div style={{ animation: "var(--animate-fadeIn)" }}>
    <ChartRenderer data={chartSpecs} />
  </div>
)}
```

**Source:** Project's existing skeleton infrastructure in `frontend/src/app/globals.css`

### Anti-Patterns to Avoid

- **Using react-plotly.js wrapper:** Outdated, not updated for React 19, adds unnecessary layer. Use plotly.js-dist-min directly.
- **Direct import without dynamic():** Causes "window is not defined" SSR errors in Next.js.
- **Only window resize listener:** Misses container resizes (collapsible panels, grid layouts). Use ResizeObserver.
- **Calling newPlot() on every update:** Destroys and recreates entire chart. Use react() for efficient diffing.
- **Forgetting Plotly.purge():** Memory leak - event listeners and internal state never cleaned up.
- **Hardcoding chart height:** User wants dynamic height based on data complexity. Calculate from data.length.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chart rendering engine | Custom SVG/Canvas charting | Plotly.js | Interactive zoom/pan/hover requires complex event handling, coordinate transforms, render optimization |
| Resize detection | `window.addEventListener('resize')` polling | ResizeObserver API or `use-resize-observer` hook | Container can resize without window resize (collapsible panels, grid layout changes), polling causes performance issues |
| Dynamic imports | Manual script tag injection with `document.createElement` | Next.js `next/dynamic` | Next.js handles bundle splitting, loading states, error boundaries, SSR/CSR coordination automatically |
| Loading skeletons | Custom keyframe animations | Project's existing `.skeleton` class with shimmer | Already theme-aware (light/dark), matches design system, avoid inconsistency |
| JSON validation | Manual try/catch with custom error messages | Zod or existing validation patterns | Plotly JSON schema is complex (data arrays, layout objects, config), edge cases are hard to predict |

**Key insight:** Plotly.js is 1.5MB minified because interactive charting is deceptively complex. Pan/zoom state, axis rescaling, hover tooltips, responsive layout recalculation, and cross-browser event handling have thousands of edge cases. Don't underestimate this domain.

## Common Pitfalls

### Pitfall 1: Memory Leaks from Unpurged Charts
**What goes wrong:** Component unmounts but Plotly's internal state, event listeners, and DOM references remain in memory. Browser tab memory grows over time, eventually causing crashes.

**Why it happens:** Plotly.newPlot/react creates event listeners (click, hover, zoom) and stores internal state. React doesn't clean these up automatically on unmount.

**How to avoid:** Always call `Plotly.purge(divElement)` in useEffect cleanup function.

**Warning signs:**
- Memory usage grows during navigation between sessions/pages
- Browser DevTools shows increasing listener count
- Chart interactions get sluggish over time

```typescript
useEffect(() => {
  // ... render chart ...
  return () => {
    if (chartRef.current) {
      Plotly.purge(chartRef.current); // CRITICAL
    }
  };
}, [data]);
```

**Source:** [Plotly Community - Memory Leaks](https://community.plotly.com/t/memory-leaks-for-streaming-timeseries/52840)

### Pitfall 2: SSR Window/Document Access Errors
**What goes wrong:** Build fails or runtime error: "ReferenceError: window is not defined" or "document is not defined".

**Why it happens:** Next.js renders components on server first (SSR). Plotly.js expects browser globals (window, document) that don't exist in Node.js environment.

**How to avoid:** Use `dynamic(() => import(...), { ssr: false })` to force client-side only rendering.

**Warning signs:**
- Build succeeds locally but fails in CI/production
- Error occurs during `next build` or initial page load
- Error mentions "window", "document", or "navigator"

```typescript
// WRONG - causes SSR error
import Plotly from 'plotly.js-dist-min';

// RIGHT - defers loading until client-side
const ChartRenderer = dynamic(() => import('@/components/chart/ChartRenderer'), {
  ssr: false,
});
```

**Source:** [Next.js Docs - Dynamic Imports](https://nextjs.org/docs/pages/guides/lazy-loading)

### Pitfall 3: Responsive Charts Don't Resize on Container Changes
**What goes wrong:** Chart resizes on window resize, but not when container width changes (e.g., sidebar toggle, responsive grid reflow).

**Why it happens:** Plotly's `responsive: true` config only listens to window resize events, not container size changes.

**How to avoid:** Use ResizeObserver to watch container element directly, call `Plotly.Plots.resize()` manually.

**Warning signs:**
- Chart resizes when browser window changes, but not when sidebar opens/closes
- Chart overflows container or has incorrect width after layout shift
- Chart only updates on next window resize

```typescript
// Add ResizeObserver to watch container
useEffect(() => {
  if (!chartRef.current) return;

  const resizeObserver = new ResizeObserver(() => {
    if (chartRef.current) {
      Plotly.Plots.resize(chartRef.current);
    }
  });

  resizeObserver.observe(chartRef.current);

  return () => resizeObserver.disconnect();
}, []);
```

**Source:** [Plotly Community - Responsive Layout Issues](https://community.plotly.com/t/react-plotly-responsive-chart-not-working/47547)

### Pitfall 4: Bundle Size Explosion During Build
**What goes wrong:** `npm run build` fails with "JavaScript heap out of memory" or production bundle exceeds size limits.

**Why it happens:** Full plotly.js is 3MB+ minified. Even plotly.js-dist-min (1MB) can strain memory during Next.js bundle optimization with many imports.

**How to avoid:**
- Use plotly.js-dist-min (not full plotly.js)
- Consider plotly.js-basic-dist-min if only using 2D charts (excludes 3D/maps)
- Dynamic import prevents bundle from including Plotly in SSR chunks

**Warning signs:**
- Build process crashes with heap memory errors
- Production bundle size warnings in `next build` output
- Lighthouse performance score drops significantly

**Source:** [Plotly GitHub - Memory Issues](https://github.com/plotly/react-plotly.js/issues/130)

### Pitfall 5: Chart Doesn't Update When Props Change
**What goes wrong:** Component receives new `data` prop but chart doesn't update visually.

**Why it happens:**
- Forgot to include `data` in useEffect dependency array
- Using `Plotly.newPlot()` inside conditional that doesn't re-run
- JSON string parsing fails silently

**How to avoid:**
- Always include all props in useEffect dependencies
- Use `Plotly.react()` which handles updates intelligently
- Add error boundaries and logging for JSON parse failures

**Warning signs:**
- Chart renders once on mount but never updates
- Console shows no errors but chart is stale
- Forcing component remount (key change) "fixes" it

```typescript
// WRONG - missing dependency
useEffect(() => {
  Plotly.react(chartRef.current, chartData.data, chartData.layout);
}, []); // Empty deps - never re-runs

// RIGHT - includes data
useEffect(() => {
  if (!chartRef.current || !data) return;
  const chartData = JSON.parse(data);
  Plotly.react(chartRef.current, chartData.data, chartData.layout);
}, [data]); // Re-runs when data changes
```

### Pitfall 6: Treating chart_specs as Object Instead of JSON String
**What goes wrong:** TypeScript errors or runtime parse failures when accessing chart_specs.

**Why it happens:** Backend sends chart_specs as JSON string (`fig.to_json()`), not parsed object. Frontend must parse before use.

**How to avoid:**
- Type chart_specs as `string` in TypeScript interfaces
- Always `JSON.parse(chartSpecs)` before passing to Plotly
- Handle parse errors gracefully (malformed JSON, 2MB size limit exceeded)

**Warning signs:**
- "SyntaxError: Unexpected token" when accessing chart data
- TypeScript errors about string vs object type mismatch
- Chart renders as blank/broken

```typescript
// Backend state.py defines:
// chart_specs: str  # JSON string of Plotly figure

// Frontend must parse:
const chartData = JSON.parse(chartSpecs);
Plotly.react(chartRef.current, chartData.data, chartData.layout);
```

## Code Examples

### Example 1: Complete ChartRenderer Component
```typescript
// File: frontend/src/components/chart/ChartRenderer.tsx
'use client';

import { useRef, useEffect, useState } from 'react';
import Plotly from 'plotly.js-dist-min';

interface ChartRendererProps {
  /** JSON string from backend (fig.to_json() output) */
  data: string;
  /** Optional height in pixels, auto if not specified */
  height?: number;
}

export function ChartRenderer({ data, height }: ChartRendererProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data) return;

    try {
      const chartData = JSON.parse(data);

      // Merge user's layout with responsive defaults
      const layout = {
        ...chartData.layout,
        autosize: true,
        height: height || chartData.layout?.height || 400,
        margin: { l: 50, r: 50, t: 50, b: 50 },
      };

      // Config for modebar (download, zoom, pan controls)
      const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['sendDataToCloud'],
        toImageButtonOptions: {
          format: 'png',
          filename: 'chart',
          height: 800,
          width: 1200,
          scale: 2,
        },
      };

      Plotly.react(chartRef.current, chartData.data || [], layout, config);
      setError(null);
    } catch (err) {
      console.error('Chart render error:', err);
      setError('Failed to render chart');
    }

    // ResizeObserver for container-aware responsiveness
    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current) {
        Plotly.Plots.resize(chartRef.current);
      }
    });

    if (chartRef.current) {
      resizeObserver.observe(chartRef.current);
    }

    // Cleanup
    return () => {
      resizeObserver.disconnect();
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
  }, [data, height]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-[400px] text-destructive">
        {error}
      </div>
    );
  }

  return (
    <div
      ref={chartRef}
      className="w-full"
      style={{ minHeight: height || 400 }}
    />
  );
}
```

### Example 2: DataCard Integration with Chart Section
```typescript
// File: frontend/src/components/chat/DataCard.tsx (modified)
import dynamic from 'next/dynamic';
import { ChartSkeleton } from '@/components/chart/ChartSkeleton';

const ChartRenderer = dynamic(
  () => import('@/components/chart/ChartRenderer'),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

interface DataCardProps {
  // ... existing props ...
  chartSpecs?: string; // NEW: JSON string from backend
  chartError?: string; // NEW: Error message if chart generation failed
  visualizationRequested?: boolean; // NEW: True during chart generation
}

export function DataCard({
  queryBrief,
  tableData,
  explanation,
  chartSpecs,
  chartError,
  visualizationRequested,
  isStreaming,
  // ... other props
}: DataCardProps) {
  return (
    <Collapsible>
      <CollapsibleContent className="px-6 pb-6 space-y-6">

        {/* Chart Section - BELOW TABLE per user decision */}
        {chartError && (
          <ChartErrorAlert message={chartError} />
        )}

        {visualizationRequested && !chartSpecs && isStreaming && (
          <ChartSkeleton stage={currentStatus} />
        )}

        {chartSpecs && (
          <div
            className="space-y-2"
            style={{ animation: "var(--animate-fadeIn)" }}
          >
            <h4 className="text-sm font-medium text-muted-foreground">
              Visualization
            </h4>
            <ChartRenderer data={chartSpecs} />
          </div>
        )}

        {/* Data Table - ABOVE CHART per user decision */}
        {displayTableData && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">
              Data Results
            </h4>
            <DataTable columns={displayTableData.columns} data={displayTableData.rows} />
          </div>
        )}

        {/* Explanation section... */}
      </CollapsibleContent>
    </Collapsible>
  );
}
```

### Example 3: Chart Skeleton with Stage Indicators
```typescript
// File: frontend/src/components/chart/ChartSkeleton.tsx
export function ChartSkeleton({ stage }: { stage?: string }) {
  const stages = [
    "Analyzing data structure...",
    "Selecting visualization type...",
    "Generating chart code...",
    "Creating visualization...",
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
        <p className="text-sm text-muted-foreground">
          {stage || "Generating visualization..."}
        </p>
      </div>

      {/* Skeleton placeholder matching chart dimensions */}
      <div className="skeleton h-[400px] w-full rounded-lg" />

      {/* Optional: Progress dots */}
      <div className="flex justify-center gap-1">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-primary/30"
            style={{
              animation: `var(--animate-pulse-gentle)`,
              animationDelay: `${i * 200}ms`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
```

### Example 4: Subtle Dismissible Error Alert
```typescript
// File: frontend/src/components/chart/ChartErrorAlert.tsx
'use client';

import { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';

interface ChartErrorAlertProps {
  message: string;
}

export function ChartErrorAlert({ message }: ChartErrorAlertProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
      <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
      <p className="flex-1 text-sm text-destructive/90">
        {message}
      </p>
      <button
        onClick={() => setDismissed(true)}
        className="text-destructive/70 hover:text-destructive transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
```

### Example 5: Dynamic Height Calculation Based on Data
```typescript
// Calculate chart height based on data complexity
function calculateChartHeight(chartData: any): number {
  const baseHeight = 400;
  const maxHeight = 700;

  // Extract data point count (varies by chart type)
  let dataPointCount = 0;

  if (chartData.data && Array.isArray(chartData.data)) {
    // Sum data points across all traces
    dataPointCount = chartData.data.reduce((sum: number, trace: any) => {
      if (trace.x) return sum + trace.x.length;
      if (trace.y) return sum + trace.y.length;
      return sum;
    }, 0);
  }

  // Scale height: +10px per 100 data points
  const scaledHeight = baseHeight + Math.floor(dataPointCount / 100) * 10;

  return Math.min(scaledHeight, maxHeight);
}

// Usage in ChartRenderer
const chartData = JSON.parse(data);
const dynamicHeight = calculateChartHeight(chartData);

Plotly.react(chartRef.current, chartData.data, {
  ...chartData.layout,
  height: dynamicHeight,
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-plotly.js wrapper | Direct plotly.js-dist-min | 2023-2024 | Wrapper not updated for React 19, adds abstraction overhead, community moved to direct integration |
| window.onresize listener | ResizeObserver API | 2020-2021 | Container-aware resize detection, better performance, no polling |
| Plotly.newPlot() for updates | Plotly.react() | 2017 | Intelligent diffing vs full recreate, 10-100x faster for incremental updates |
| Server-side chart rendering (Kaleido) | Client-side interactive charts | Phase 22 decision | User wants interactive zoom/pan/hover, not static images |
| Custom skeleton animations | Tailwind animate-pulse + shimmer | 2023+ | Consistency across design system, theme-aware, less custom CSS |

**Deprecated/outdated:**
- **react-plotly.js**: Last updated 2021, not compatible with React 19, use direct plotly.js-dist-min
- **plotly.js Plot/Plots.plot**: Older API, use `newPlot()` or `react()` instead
- **Inline window resize handlers**: Use ResizeObserver for better performance and container awareness

## Open Questions

1. **Should we use plotly.js-basic-dist-min instead of plotly.js-dist-min?**
   - What we know: Basic is ~200KB smaller, excludes 3D/mapbox/geo charts
   - What's unclear: Does Phase 22 Visualization Agent generate 3D/geo charts? Need to check chart types in backend code.
   - Recommendation: Start with plotly.js-dist-min (full 2D support), switch to basic if bundle size becomes issue AND we verify no 3D charts.

2. **What chart height formula should we use?**
   - What we know: User wants "dynamic based on data complexity"
   - What's unclear: Exact formula (data points vs chart type vs axes count)
   - Recommendation: Start with `baseHeight + (dataPoints / 100) * 10` capped at 700px, iterate based on user feedback.

3. **Should we debounce ResizeObserver callbacks?**
   - What we know: ResizeObserver fires frequently during resize, Plotly.Plots.resize() has internal debouncing
   - What's unclear: Whether additional debouncing improves performance or is redundant
   - Recommendation: No manual debouncing initially - Plotly handles it internally. Add only if performance issues appear.

4. **How should mobile/small screens handle large charts?**
   - What we know: User mentioned "mobile chart behavior" as discretion area
   - What's unclear: Breakpoint thresholds, whether to reduce height, hide modebar, or adjust layout
   - Recommendation: Use responsive: true, reduce modebar size on mobile (<768px), let Plotly handle layout auto-adjustment.

## Sources

### Primary (HIGH confidence)
- Next.js Official Documentation - Lazy Loading: https://nextjs.org/docs/pages/guides/lazy-loading
- Next.js Official Documentation - Server and Client Components: https://nextjs.org/docs/app/getting-started/server-and-client-components
- Plotly.js Official Documentation - Responsive Layouts: https://plotly.com/javascript/responsive-fluid-layout/
- Plotly.js Official Documentation - Function Reference: https://plotly.com/javascript/plotlyjs-function-reference/
- Plotly.js Official Documentation - Configuration Options: https://plotly.com/javascript/configuration-options/
- npm package page - plotly.js-dist-min: https://www.npmjs.com/package/plotly.js-dist-min
- Project's existing codebase (DataCard.tsx, globals.css, chat.ts types)

### Secondary (MEDIUM confidence)
- LogRocket Blog - Using ResizeObserver in React: https://blog.logrocket.com/using-resizeobserver-react-responsive-designs/
- LogRocket Blog - React Loading Skeleton: https://blog.logrocket.com/handling-react-loading-states-react-loading-skeleton/
- GitHub - plotly/react-plotly.js Issues: https://github.com/plotly/react-plotly.js/issues/226
- Plotly Community Forum - Responsive Charts: https://community.plotly.com/t/react-plotly-responsive-chart-not-working/47547
- Flowbite - Tailwind Skeleton Components: https://flowbite.com/docs/components/skeleton/

### Tertiary (LOW confidence - cross-verify during implementation)
- Medium - Plotly React Integration Patterns (2020-2021 articles, may be outdated)
- Stack Overflow discussions on Plotly memory leaks (various dates, anecdotal)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - npm packages verified, versions checked, existing patterns in codebase
- Architecture: HIGH - Next.js patterns official, Plotly API documented, ResizeObserver is standard Web API
- Pitfalls: MEDIUM-HIGH - Memory leaks well-documented in Plotly community, SSR issues confirmed in Next.js docs, resize issues reported by multiple users

**Research date:** 2026-02-13
**Valid until:** ~30 days (stable libraries, but Next.js updates frequently - verify Next.js 16.x compatibility if version changes)

**Critical verification needed during implementation:**
- Confirm chart_specs format from backend matches Plotly JSON schema expectations
- Test ResizeObserver performance with rapid container resizing
- Verify theme CSS variables work with Plotly's default styling
- Check mobile breakpoints for modebar visibility and chart height adjustments
