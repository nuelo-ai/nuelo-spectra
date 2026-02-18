# Phase 24: Chart Types & Export - Research

**Researched:** 2026-02-13
**Domain:** Plotly chart type implementation, LLM prompt engineering for chart generation, browser-based image export, dynamic chart type switching
**Confidence:** HIGH

## Summary

Phase 24 builds on Phase 23's working chart rendering foundation to add comprehensive chart type support (all 7 types: bar, line, scatter, histogram, box plot, pie, donut), meaningful chart labels, and export/switching capabilities. The technical challenges are: (1) prompt engineering the Visualization Agent to reliably generate correct Plotly code for all chart types with human-readable labels, (2) implementing client-side PNG/SVG export using Plotly.downloadImage() API, and (3) building a chart type switcher UI that only shows applicable types for given data shape.

The existing visualization pipeline already works end-to-end: Manager Agent provides chart_hint, Visualization Agent generates code, backend executes in E2B sandbox, chart JSON streams via SSE, and ChartRenderer displays it. This phase enhances the Visualization Agent's prompt (backend) and adds export/switcher UI components (frontend).

**Primary recommendation:** Enhance visualization agent's system prompt with specific rules for all 7 chart types and label formatting guidance. Implement export buttons using Plotly.downloadImage() with format parameter. Build chart type switcher using Plotly.restyle() to change trace type without full re-render. Apply data shape validation to determine which chart types are compatible (bar/line/scatter share 2D cartesian space, pie/donut require categorical+numeric, etc.).

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| plotly.js-dist-min | 3.3.1 | Chart rendering & export | Contains Plotly.downloadImage() API, supports all 7 required chart types, browser-native export (no server-side Kaleido needed) |
| Plotly Python | 6.0.1+ (E2B) | Server-side chart code execution | Plotly Express (px) for all 7 chart types, fig.to_json() for JSON transport, consistent API across types |
| lucide-react | 0.563.0 | UI icons | Download, RefreshCw, ChevronDown icons for export/switcher buttons |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None required | - | All dependencies satisfied | Export and switcher use existing Plotly.js API, no new packages needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plotly.downloadImage() | Server-side Kaleido export | Kaleido adds backend complexity, requires file storage/cleanup, slower UX (round-trip vs instant browser download). Prior decision: client-side export only. |
| Plotly.restyle() for switching | Full re-execution of Viz Agent | Re-execution wastes LLM tokens, adds latency, requires backend round-trip. Restyle is instant and free. |
| Chart type validation | Allow all types always | Poor UX: switching pie→scatter with categorical data produces garbage chart. Validation prevents invalid switches. |

**Installation:**
```bash
# No new dependencies - all capabilities exist in current stack
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── agents/
│   └── visualization.py        # Enhanced prompt with 7 chart types + label rules
├── config/
│   └── prompts.yaml            # Visualization agent system prompt (enhanced)

frontend/src/components/
├── chart/
│   ├── ChartRenderer.tsx       # Existing (add export button integration)
│   ├── ChartExportButtons.tsx  # NEW: PNG/SVG download buttons
│   └── ChartTypeSwitcher.tsx   # NEW: Dropdown for bar/line/scatter switching
├── chat/
│   └── DataCard.tsx            # Integrate export + switcher below chart
```

### Pattern 1: Visualization Agent Prompt - Chart Type Rules

**What:** System prompt rules that map data characteristics → appropriate chart type, with specific Plotly code patterns for each type.

**When to use:** When designing/enhancing the visualization agent's prompt in prompts.yaml.

**Example:**
```yaml
visualization:
  system_prompt: |
    **Chart Type Selection Rules:**
    1. If chart_hint specified: use that type
    2. Date/time column + numeric: LINE (sort by date ascending)
    3. One categorical + one numeric:
       - ≤8 unique categories: PIE
       - >8 categories: horizontal BAR
    4. Two numeric columns: SCATTER
    5. Single numeric column: HISTOGRAM
    6. Distribution analysis: BOX plot
    7. Part-to-whole with hole needed: DONUT (pie with hole parameter)

    **Chart Type Code Patterns:**

    BAR CHART:
    ```python
    import plotly.express as px
    fig = px.bar(df, x='category', y='value',
                 title='Sales by Region',
                 labels={'category': 'Region', 'value': 'Total Sales ($)'})
    ```

    LINE CHART:
    ```python
    fig = px.line(df, x='date', y='revenue',
                  title='Revenue Over Time',
                  labels={'date': 'Month', 'revenue': 'Revenue ($)'})
    ```

    SCATTER PLOT:
    ```python
    fig = px.scatter(df, x='age', y='income',
                     title='Income vs Age Relationship',
                     labels={'age': 'Age (years)', 'income': 'Annual Income ($)'})
    ```

    HISTOGRAM:
    ```python
    fig = px.histogram(df, x='price',
                       title='Price Distribution',
                       labels={'price': 'Price ($)'})
    ```

    BOX PLOT:
    ```python
    fig = px.box(df, y='score', x='category',
                 title='Score Distribution by Category',
                 labels={'score': 'Test Score', 'category': 'Grade Level'})
    ```

    PIE CHART:
    ```python
    fig = px.pie(df, values='amount', names='category',
                 title='Budget Breakdown by Department')
    ```

    DONUT CHART:
    ```python
    fig = px.pie(df, values='sales', names='product',
                 hole=0.4,  # Creates donut hole (40% of radius)
                 title='Market Share by Product')
    ```
```

**Sources:**
- [Plotly Python - Plotly Express](https://plotly.com/python/plotly-express/)
- [Plotly Python - Pie Charts](https://plotly.com/python/pie-charts/) (donut hole parameter)
- [Plotly Python - Box Plots](https://plotly.com/python/box-plots/)

### Pattern 2: Meaningful Chart Labels via LLM Prompt

**What:** Prompt guidance for generating human-readable axis labels and titles instead of raw column names.

**When to use:** In visualization agent prompt to ensure charts meet CHART-11 requirement.

**Example:**
```yaml
**Label Formatting Rules:**
1. Chart title: Natural language summary of what the chart shows
   - Good: "Sales by Region"
   - Bad: "col_sales vs col_region"

2. Axis labels: Human-readable with units
   - Good: "Revenue ($)", "Temperature (°C)", "Count"
   - Bad: "col_rev_2024", "temp_reading", "n"

3. Use Plotly Express `labels` parameter or update_layout():
   ```python
   # Method 1: Plotly Express labels parameter
   fig = px.bar(df, x='col_region', y='col_revenue_2024',
                labels={
                    'col_region': 'Region',
                    'col_revenue_2024': 'Revenue ($)'
                },
                title='2024 Revenue by Region')

   # Method 2: update_layout (Graph Objects)
   fig.update_layout(
       title='2024 Revenue by Region',
       xaxis_title='Region',
       yaxis_title='Revenue ($)'
   )
   ```

4. Infer units from column names or data context:
   - "revenue", "sales", "price" → add "$"
   - "temp", "temperature" → add "°C" or "°F"
   - "count", "quantity" → add "Count" or leave numeric

5. Follow accessibility standards:
   - Min 12pt font for titles (Plotly default is compliant)
   - High contrast (Plotly default meets 4.5:1 ratio)
```

**Sources:**
- [Plotly Python - Figure Labels](https://plotly.com/python/figure-labels/)
- [Python Plotly Bar Plot Axis Labels Guide](https://copyprogramming.com/howto/how-to-change-the-x-axis-and-y-axis-labels-in-plotly)

### Pattern 3: Client-Side Image Export with Plotly.downloadImage()

**What:** Browser-native chart export to PNG/SVG using Plotly's downloadImage() API.

**When to use:** For EXPORT-01 and EXPORT-02 requirements (PNG/SVG download buttons).

**Example:**
```typescript
// ChartExportButtons.tsx
'use client';

import { Download } from 'lucide-react';
import Plotly from 'plotly.js-dist-min';

interface ChartExportButtonsProps {
  chartRef: React.RefObject<HTMLDivElement>;
  filename?: string;
}

export function ChartExportButtons({ chartRef, filename = 'chart' }: ChartExportButtonsProps) {
  const handleExport = async (format: 'png' | 'svg') => {
    if (!chartRef.current) return;

    try {
      await Plotly.downloadImage(chartRef.current, {
        format: format,
        width: 1200,
        height: 800,
        filename: `${filename}.${format}`,
      });
    } catch (error) {
      console.error(`Failed to export chart as ${format}:`, error);
      // Optional: Show toast notification
    }
  };

  return (
    <div className="flex gap-2">
      <button
        onClick={() => handleExport('png')}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded hover:bg-accent"
      >
        <Download className="h-3.5 w-3.5" />
        PNG
      </button>
      <button
        onClick={() => handleExport('svg')}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded hover:bg-accent"
      >
        <Download className="h-3.5 w-3.5" />
        SVG
      </button>
    </div>
  );
}
```

**Integration into DataCard:**
```typescript
// DataCard.tsx (chart section)
{chartSpecs && (
  <div className="space-y-2">
    <h4 className="text-sm font-medium text-muted-foreground">
      Visualization
    </h4>
    <ChartRenderer
      ref={chartRef}  // Pass ref to ChartRenderer
      data={chartSpecs}
    />
    <ChartExportButtons
      chartRef={chartRef}
      filename={queryBrief ? queryBrief.toLowerCase().replace(/\s+/g, '-').slice(0, 30) : 'chart'}
    />
  </div>
)}
```

**Sources:**
- [Plotly.js Function Reference - downloadImage](https://plotly.com/javascript/plotlyjs-function-reference/)
- [Linux Hint - Plotly downloadImage Function](https://linuxhint.com/plotly-downloadimage/)

### Pattern 4: Chart Type Switching with Plotly.restyle()

**What:** Dynamic chart type switching using Plotly.restyle() to change trace type without re-executing backend code.

**When to use:** For EXPORT-04 requirement (switch between bar/line/scatter after generation).

**Example:**
```typescript
// ChartTypeSwitcher.tsx
'use client';

import { RefreshCw } from 'lucide-react';
import Plotly from 'plotly.js-dist-min';
import { useState } from 'react';

type ChartType = 'bar' | 'scatter' | 'line';

interface ChartTypeSwitcherProps {
  chartRef: React.RefObject<HTMLDivElement>;
  currentType: ChartType;
  compatibleTypes: ChartType[];  // Only show applicable types
}

export function ChartTypeSwitcher({
  chartRef,
  currentType: initialType,
  compatibleTypes
}: ChartTypeSwitcherProps) {
  const [currentType, setCurrentType] = useState<ChartType>(initialType);

  const handleTypeChange = async (newType: ChartType) => {
    if (!chartRef.current || newType === currentType) return;

    try {
      // Plotly.restyle changes trace properties without full re-render
      if (newType === 'line') {
        await Plotly.restyle(chartRef.current, {
          'type': 'scatter',
          'mode': 'lines'
        }, [0]);  // Apply to first trace
      } else if (newType === 'scatter') {
        await Plotly.restyle(chartRef.current, {
          'type': 'scatter',
          'mode': 'markers'
        }, [0]);
      } else if (newType === 'bar') {
        await Plotly.restyle(chartRef.current, {
          'type': 'bar'
        }, [0]);
      }

      setCurrentType(newType);
    } catch (error) {
      console.error('Failed to switch chart type:', error);
    }
  };

  if (compatibleTypes.length <= 1) return null;  // Hide if only 1 type applicable

  return (
    <div className="flex items-center gap-2">
      <RefreshCw className="h-3.5 w-3.5 text-muted-foreground" />
      <select
        value={currentType}
        onChange={(e) => handleTypeChange(e.target.value as ChartType)}
        className="text-xs border rounded px-2 py-1 bg-background"
      >
        {compatibleTypes.map(type => (
          <option key={type} value={type}>
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
}
```

**Data Shape Compatibility Logic:**
```typescript
// utils/chartTypeCompatibility.ts

export function getCompatibleChartTypes(chartData: Plotly.PlotData): ChartType[] {
  const trace = chartData[0];
  if (!trace) return [];

  const hasXY = trace.x && trace.y;
  const xIsNumeric = Array.isArray(trace.x) && typeof trace.x[0] === 'number';
  const yIsNumeric = Array.isArray(trace.y) && typeof trace.y[0] === 'number';

  // Compatible types for 2D cartesian data with numeric axes
  if (hasXY && xIsNumeric && yIsNumeric) {
    return ['bar', 'line', 'scatter'];
  }

  // Categorical X + numeric Y: bar and line compatible
  if (hasXY && !xIsNumeric && yIsNumeric) {
    return ['bar', 'line'];
  }

  // Single type only for pie, histogram, box plots
  return [trace.type as ChartType];
}
```

**Sources:**
- [Plotly.js Function Reference - restyle](https://plotly.com/javascript/plotlyjs-function-reference/)
- [Plotly Community - Chart Type Switching](https://community.plotly.com/t/change-chart-type-and-data-using-dropdown-menu/11767)

### Anti-Patterns to Avoid

**Anti-pattern: Raw column names in labels**
```python
# BAD - User sees technical column names
fig = px.bar(df, x='col_region_id', y='col_total_revenue_2024')
# Result: Axis shows "col_region_id" and "col_total_revenue_2024"

# GOOD - Human-readable labels
fig = px.bar(df, x='col_region_id', y='col_total_revenue_2024',
             labels={'col_region_id': 'Region', 'col_total_revenue_2024': 'Revenue ($)'},
             title='2024 Revenue by Region')
```

**Anti-pattern: No unit indicators**
```python
# BAD - Ambiguous what numbers represent
fig.update_layout(yaxis_title='Revenue')

# GOOD - Clear units
fig.update_layout(yaxis_title='Revenue ($)')
```

**Anti-pattern: Switching incompatible chart types**
```typescript
// BAD - Allowing pie → scatter switch with categorical data
const compatibleTypes = ['pie', 'scatter'];  // Will produce garbage

// GOOD - Only show compatible types for data shape
const compatibleTypes = getCompatibleChartTypes(chartData);
```

**Anti-pattern: Re-executing backend for type switch**
```typescript
// BAD - Wastes LLM tokens, adds latency
const handleTypeChange = (newType) => {
  // Call backend Viz Agent again to regenerate code
  fetch('/api/regenerate-chart', { type: newType });
};

// GOOD - Use Plotly.restyle for instant client-side update
const handleTypeChange = (newType) => {
  Plotly.restyle(chartRef.current, { type: newType }, [0]);
};
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image export | Custom canvas → blob → download flow | Plotly.downloadImage() | Handles HiDPI scaling, format encoding (PNG/SVG), cross-browser quirks, filename generation |
| Chart type detection | Manual if/else for column types | Data shape hints (existing) + LLM intelligence | LLM can infer semantic meaning ("revenue" → bar chart), not just type checking |
| Label formatting | String manipulation for units | LLM prompt with examples | LLM understands context ("price" likely needs $, "temp" needs °C) |
| Dynamic chart updates | Plotly.newPlot() on every change | Plotly.restyle() / Plotly.react() | restyle() is 10-100x faster for trace property updates, react() intelligently diffs |

**Key insight:** Plotly's API already handles the hard parts (export encoding, responsive resizing, data-ink optimization). The challenge is prompt engineering the Visualization Agent to generate *correct, well-labeled* code for each chart type, not building custom charting infrastructure.

## Common Pitfalls

### Pitfall 1: Overly Long Axis Titles Compressing Plot Area

**What goes wrong:** Long titles like "Total Revenue Generated from Product Sales in Q4 2024" squeeze the actual chart into a tiny space.

**Why it happens:** LLM generates verbose titles without considering visual real estate constraints.

**How to avoid:**
- Add prompt rule: "Chart titles max 8 words. Use concise terminology."
- Encourage subtitle usage (Plotly 5.23+): title + subtitle pattern
- Example prompt: "Title: 'Q4 Revenue', Subtitle: 'Product sales breakdown'"

**Warning signs:** User feedback about charts looking "cramped" or "hard to read."

**Sources:**
- [Common Visualization Mistakes - Plotivy](https://plotivy.app/blog/common-visualization-mistakes-and-fixes)

### Pitfall 2: Chart Export Fails on iOS Chrome

**What goes wrong:** Plotly.toImage() and downloadImage() silently fail on Chrome for iOS, no download occurs.

**Why it happens:** iOS Safari's rendering engine (used by Chrome on iOS) has restrictions on programmatic image download triggers.

**How to avoid:**
- Test export on iOS Safari and Chrome during QA
- Consider fallback: Show modal with chart image + long-press to save
- Document known limitation if unfixable

**Warning signs:** User reports "download button doesn't work on iPhone."

**Sources:**
- [Plotly Community - iOS Chrome toImage Issue](https://community.plotly.com/t/plotly-js-toimage-and-downloadimage-not-working-in-chrome-for-ios-iphone-and-ipad/53326)

### Pitfall 3: Missing Units Create Ambiguity

**What goes wrong:** Y-axis shows "15000" but user doesn't know if it's $15K, 15K units, or something else.

**Why it happens:** LLM doesn't infer units from column names, or column names lack semantic clues.

**How to avoid:**
- Prompt rule: "Always include units in axis labels. Infer from column name or data context."
- Provide examples: "revenue → Revenue ($)", "count → Count", "temp → Temperature (°C)"
- Fallback: If units unclear, use descriptive axis label without units but add context in title

**Warning signs:** User confusion questions like "Is this in thousands or millions?"

**Sources:**
- [Common Visualization Mistakes - Plotivy](https://plotivy.app/blog/common-visualization-mistakes-and-fixes)

### Pitfall 4: Histogram Misidentified as Bar Chart

**What goes wrong:** User has single numeric column (ages: 25, 30, 22, 35...), LLM generates bar chart with each data point as separate bar instead of histogram showing distribution.

**Why it happens:** Insufficient data shape analysis in prompt. Bar vs histogram distinction unclear.

**How to avoid:**
- Strengthen prompt rule: "Single numeric column with many unique values (>8) → HISTOGRAM, not bar chart"
- Data shape hints should flag "numeric column with N unique values"
- Example: "age: 150 unique values" → triggers histogram path

**Warning signs:** Chart has 50+ tiny bars instead of binned distribution.

### Pitfall 5: Pie Chart with Too Many Slices

**What goes wrong:** Pie chart with 30 categories becomes unreadable rainbow mess.

**Why it happens:** Prompt rule "categorical + numeric → pie" applied without cardinality check.

**How to avoid:**
- Refine rule: "≤8 categories → PIE, >8 → horizontal BAR"
- Prompt can suggest: "Too many categories for pie chart. Using bar chart for clarity."
- If user explicitly requests pie with many categories, LLM can show top 8 + "Other"

**Warning signs:** Pie chart with tiny slivers and overlapping labels.

**Sources:**
- Existing visualization.py prompt has this rule, ensure it's enforced

### Pitfall 6: Chart Type Switcher Shows Incompatible Types

**What goes wrong:** User switches from pie chart to scatter chart, resulting in broken visualization.

**Why it happens:** Switcher UI doesn't validate data shape compatibility before showing options.

**How to avoid:**
- Implement getCompatibleChartTypes() logic (Pattern 4 above)
- Only show switcher for cartesian charts with numeric axes (bar/line/scatter)
- Hide switcher entirely for pie, histogram, box plots (single-type only)

**Warning signs:** Error console messages after type switch, or weird/empty chart.

### Pitfall 7: Low-Quality PNG Export on HiDPI Displays

**What goes wrong:** Exported PNG looks blurry on retina displays.

**Why it happens:** Plotly.downloadImage() defaults to 1x scale, doesn't account for device pixel ratio.

**How to avoid:**
- Specify higher dimensions in downloadImage() call: width: 1200, height: 800 (2x normal)
- Or use `scale` parameter if supported: `{ scale: 2 }`
- SVG export unaffected (vector format)

**Warning signs:** User reports "downloaded chart looks pixelated."

**Sources:**
- [Plotly Community - Low Quality PNG](https://community.plotly.com/t/low-quality-of-download-plot-as-png-in-browser/5450)

## Code Examples

Verified patterns from official sources:

### All 7 Chart Types - Plotly Python Code

```python
import plotly.express as px
import pandas as pd
import json
import plotly.io as pio

# Sample data (embedded, not reading from df)
data = [
    {'region': 'East', 'revenue': 50000},
    {'region': 'West', 'revenue': 45000},
    {'region': 'North', 'revenue': 60000},
]

df = pd.DataFrame(data)

# 1. BAR CHART
fig = px.bar(df, x='region', y='revenue',
             title='Revenue by Region',
             labels={'region': 'Region', 'revenue': 'Revenue ($)'})

# 2. LINE CHART
# Data: time series
time_data = [
    {'month': '2024-01', 'sales': 12000},
    {'month': '2024-02', 'sales': 15000},
    {'month': '2024-03', 'sales': 18000},
]
df_time = pd.DataFrame(time_data)
fig = px.line(df_time, x='month', y='sales',
              title='Sales Trend Over Time',
              labels={'month': 'Month', 'sales': 'Sales ($)'})

# 3. SCATTER PLOT
scatter_data = [
    {'age': 25, 'income': 45000},
    {'age': 30, 'income': 55000},
    {'age': 35, 'income': 65000},
]
df_scatter = pd.DataFrame(scatter_data)
fig = px.scatter(df_scatter, x='age', y='income',
                 title='Income vs Age',
                 labels={'age': 'Age (years)', 'income': 'Annual Income ($)'})

# 4. HISTOGRAM
price_data = [
    {'price': 25}, {'price': 30}, {'price': 22}, {'price': 35},
    {'price': 28}, {'price': 40}, {'price': 32}, {'price': 27},
]
df_price = pd.DataFrame(price_data)
fig = px.histogram(df_price, x='price',
                   title='Price Distribution',
                   labels={'price': 'Price ($)'})

# 5. BOX PLOT
score_data = [
    {'category': 'A', 'score': 85},
    {'category': 'A', 'score': 90},
    {'category': 'B', 'score': 75},
    {'category': 'B', 'score': 80},
]
df_score = pd.DataFrame(score_data)
fig = px.box(df_score, x='category', y='score',
             title='Score Distribution by Category',
             labels={'category': 'Category', 'score': 'Test Score'})

# 6. PIE CHART
budget_data = [
    {'department': 'Engineering', 'budget': 150000},
    {'department': 'Marketing', 'budget': 100000},
    {'department': 'Sales', 'budget': 120000},
]
df_budget = pd.DataFrame(budget_data)
fig = px.pie(df_budget, values='budget', names='department',
             title='Budget Allocation by Department')

# 7. DONUT CHART (pie with hole parameter)
fig = px.pie(df_budget, values='budget', names='department',
             hole=0.4,  # Creates donut hole (40% of radius)
             title='Budget Allocation (Donut)')

# Common ending for all charts
fig.update_layout(
    template='plotly_white',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    height=400,
    margin=dict(l=40, r=40, t=50, b=40)
)

chart_json = json.loads(pio.to_json(fig))
print(json.dumps({"chart": chart_json}))
```

**Source:** [Plotly Python - Plotly Express](https://plotly.com/python/plotly-express/)

### Frontend - ChartRenderer with Export Support

```typescript
// ChartRenderer.tsx (enhanced with ref forwarding for export)
'use client';

import { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import Plotly from 'plotly.js-dist-min';

interface ChartRendererProps {
  data: string;
  height?: number;
}

export interface ChartRendererHandle {
  getElement: () => HTMLDivElement | null;
}

const ChartRenderer = forwardRef<ChartRendererHandle, ChartRendererProps>(
  ({ data, height }, ref) => {
    const chartRef = useRef<HTMLDivElement>(null);
    const [error, setError] = useState<string | null>(null);

    // Expose chart element to parent via ref
    useImperativeHandle(ref, () => ({
      getElement: () => chartRef.current,
    }));

    useEffect(() => {
      if (!chartRef.current || !data) return;

      let resizeObserver: ResizeObserver | null = null;

      try {
        const chartData = JSON.parse(data);
        const traces: Plotly.PlotData[] = chartData.data || [];
        const layout: Partial<Plotly.Layout> = {
          ...chartData.layout,
          autosize: true,
          height: height ?? chartData.layout?.height ?? 400,
        };

        const config: Partial<Plotly.Config> = {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['sendDataToCloud'] as Plotly.ModeBarDefaultButtons[],
        };

        Plotly.react(chartRef.current, traces, layout, config);
        setError(null);

        resizeObserver = new ResizeObserver(() => {
          if (chartRef.current) {
            Plotly.Plots.resize(chartRef.current);
          }
        });
        resizeObserver.observe(chartRef.current);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to render chart';
        console.error('ChartRenderer error:', err);
        setError(message);
      }

      return () => {
        if (resizeObserver) resizeObserver.disconnect();
        if (chartRef.current) Plotly.purge(chartRef.current);
      };
    }, [data, height]);

    if (error) {
      return (
        <div className="flex items-center justify-center min-h-[200px] w-full">
          <p className="text-sm text-muted-foreground">
            Unable to render chart: {error}
          </p>
        </div>
      );
    }

    return <div ref={chartRef} className="w-full" />;
  }
);

ChartRenderer.displayName = 'ChartRenderer';

export default ChartRenderer;
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Server-side Kaleido export | Client-side Plotly.downloadImage() | Phase 23 decision | Eliminates backend complexity, faster UX, no file cleanup needed |
| Manual chart type selection | LLM-based auto-selection with chart_hint override | Phase 22 | Better UX: automatic + user control when needed |
| Fixed chart titles | LLM-generated meaningful titles | Phase 24 (new) | Improves chart readability, accessibility compliance |
| Single chart type per query | Support all 7 types + switching | Phase 24 (new) | Users can explore data from multiple visual perspectives |

**Deprecated/outdated:**
- react-plotly.js wrapper: Not maintained for React 19, unnecessary abstraction layer
- Plotly.newPlot() for updates: Use Plotly.react() instead (intelligently diffs, faster)
- Plotly basic-dist: Project uses dist-min partial bundle (all 7 types supported)

## Open Questions

1. **Should chart type switcher persist across sessions?**
   - What we know: User can switch bar→line→scatter client-side with Plotly.restyle()
   - What's unclear: If user reloads page, should chart remember last-selected type or revert to LLM's original choice?
   - Recommendation: Revert to original (simpler, no state management). Type switching is exploratory, not a "save preference" feature. If user wants different type permanently, they can ask AI with explicit chart_hint.

2. **How to handle mobile export on iOS Safari download restrictions?**
   - What we know: iOS Safari blocks programmatic downloads in some contexts ([source](https://community.plotly.com/t/plotly-js-toimage-and-downloadimage-not-working-in-chrome-for-ios-iphone-and-ipad/53326))
   - What's unclear: Does Plotly.downloadImage() work reliably on iOS Safari, or do we need fallback UI?
   - Recommendation: Implement and test. If fails, add fallback modal showing chart image with "Long press to save" instruction. Document as known limitation in milestone notes.

3. **Should donut vs pie be auto-selected or always user-choice?**
   - What we know: Donut is pie with hole parameter. Visually distinct but functionally identical.
   - What's unclear: Is there a data characteristic that makes donut preferred over pie?
   - Recommendation: Default to pie (simpler). Allow user to request donut explicitly ("show as donut chart"). Donut is aesthetic preference, not data-driven decision like histogram vs bar.

4. **What should export filename format be?**
   - What we know: Plotly.downloadImage() accepts filename parameter
   - What's unclear: Should we use query brief, timestamp, chart title, or combination?
   - Recommendation: Use sanitized query brief (first 30 chars, lowercase, hyphens) + format. Example: "revenue-by-region.png". Matches pattern used for CSV/Markdown downloads in existing DataCard.

## Sources

### Primary (HIGH confidence)
- [Plotly.js Function Reference](https://plotly.com/javascript/plotlyjs-function-reference/) - downloadImage(), restyle() API
- [Plotly Python - Plotly Express](https://plotly.com/python/plotly-express/) - All 7 chart types
- [Plotly Python - Figure Labels](https://plotly.com/python/figure-labels/) - Labels parameter, update_layout()
- [Plotly Python - Pie Charts](https://plotly.com/python/pie-charts/) - hole parameter for donuts
- [Plotly Python API - px.pie()](https://plotly.com/python-api-reference/generated/plotly.express.pie) - Complete signature
- Existing codebase - visualization.py, ChartRenderer.tsx (verified working)

### Secondary (MEDIUM confidence)
- [Linux Hint - Plotly downloadImage](https://linuxhint.com/plotly-downloadimage/) - WebSearch verified with official docs
- [Plotly Community - Chart Type Dropdown](https://community.plotly.com/t/change-chart-type-and-data-using-dropdown-menu/11767) - restyle pattern
- [Plotly Community - Multiple Chart Types](https://plotly.com/python/graphing-multiple-chart-types/) - Compatibility info
- [Python Charts - Pie & Donut](https://www.pythoncharts.com/plotly/plotly-pie-charts-donut-charts/) - Donut examples
- [Plotivy - Common Visualization Mistakes](https://plotivy.app/blog/common-visualization-mistakes-and-fixes) - Label best practices

### Tertiary (LOW confidence - needs validation)
- [Plotly Community - iOS Chrome toImage Issue](https://community.plotly.com/t/plotly-js-toimage-and-downloadimage-not-working-in-chrome-for-ios-iphone-and-ipad/53326) - Known issue, test during QA
- [Plotly Community - Low Quality PNG](https://community.plotly.com/t/low-quality-of-download-plot-as-png-in-browser/5450) - HiDPI scaling issue, verify with testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All required capabilities exist in current dependencies (plotly.js-dist-min 3.3.1, Plotly Python 6.0.1+)
- Architecture: HIGH - Patterns verified with official Plotly documentation and existing working Phase 23 implementation
- Chart type implementation: HIGH - All 7 types confirmed in Plotly Express, code examples from official docs
- Export functionality: HIGH - Plotly.downloadImage() API verified in official function reference
- Chart type switching: MEDIUM - Plotly.restyle() API verified, but compatibility matrix built from community discussions (needs testing)
- Pitfalls: MEDIUM - iOS export issue documented in community forum (LOW source), other pitfalls from best practice articles (MEDIUM source)

**Research date:** 2026-02-13
**Valid until:** 30 days (stable technologies - Plotly.js API rarely changes)
