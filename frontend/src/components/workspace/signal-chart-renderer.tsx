"use client";

import { useMemo } from "react";
import ChartRenderer from "@/components/chart/ChartRenderer";
import type { SignalDetail } from "@/types/workspace";

const SEVERITY_COLORS: Record<SignalDetail["severity"], string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#22c55e",
};

/**
 * Attempt to find two arrays in an object that look like x and y data.
 * Prioritizes keys with common naming patterns, then falls back to
 * the first two arrays of matching length found.
 */
function extractXY(obj: Record<string, unknown>): {
  x: unknown[];
  y: unknown[];
  xLabel?: string;
  yLabel?: string;
} | null {
  const arrayEntries: [string, unknown[]][] = [];
  let xLabel: string | undefined;
  let yLabel: string | undefined;

  // Collect axis labels if present
  if (typeof obj.x_label === "string") xLabel = obj.x_label;
  if (typeof obj.y_label === "string") yLabel = obj.y_label;

  // Collect all array-valued keys
  for (const [key, val] of Object.entries(obj)) {
    if (Array.isArray(val) && val.length > 0) {
      arrayEntries.push([key, val]);
    }
  }

  if (arrayEntries.length === 0) return null;

  // Priority x-axis key patterns (labels, categories, names, dates, months, bins)
  const xPatterns =
    /^(x|x_values|labels|categories|names|product_names|months|dates|bins)$/i;
  // Priority y-axis key patterns (values, counts, amounts, etc.)
  const yPatterns =
    /^(y|y_values|values|counts|amounts|mean_amounts|transaction_counts|sellthrough_pct|cumulative_pct|profit_values|remaining_qty|cv_values|std_amounts)$/i;

  let xArr: unknown[] | undefined;
  let yArr: unknown[] | undefined;
  let xKey: string | undefined;
  let yKey: string | undefined;

  // Try to find explicit x/y matches
  for (const [key, val] of arrayEntries) {
    if (xPatterns.test(key) && !xArr) {
      xArr = val;
      xKey = key;
    }
    if (yPatterns.test(key) && !yArr) {
      yArr = val;
      yKey = key;
    }
  }

  // If only one found, pick another array with matching length
  if (xArr && !yArr) {
    const other = arrayEntries.find(
      ([k, v]) => k !== xKey && v.length === xArr!.length
    );
    if (other) {
      yArr = other[1];
      yKey = other[0];
    }
  }
  if (yArr && !xArr) {
    const other = arrayEntries.find(
      ([k, v]) => k !== yKey && v.length === yArr!.length
    );
    if (other) {
      xArr = other[1];
      xKey = other[0];
    }
  }

  // Fallback: just use first two arrays
  if (!xArr && !yArr && arrayEntries.length >= 2) {
    xArr = arrayEntries[0][1];
    yArr = arrayEntries[1][1];
    xKey = arrayEntries[0][0];
    yKey = arrayEntries[1][0];
  }

  // Single array: use index as x
  if (!xArr && yArr) {
    xArr = yArr.map((_, i) => i);
  }
  if (xArr && !yArr) {
    yArr = xArr;
    xArr = xArr.map((_, i) => i);
  }

  if (!xArr || !yArr) return null;

  return {
    x: xArr,
    y: yArr,
    xLabel: xLabel || xKey,
    yLabel: yLabel || yKey,
  };
}

/**
 * Build Plotly JSON from a SignalDetail's chart_data + chart_type.
 * Handles: Plotly-native {data,layout}, points arrays, histogram bins,
 * grouped data (box plots), and arbitrary key-value arrays.
 */
function buildSignalPlotlyJSON(signal: SignalDetail): string {
  const chartData = signal.chart_data as Record<string, unknown> | null;
  if (!chartData) return "";

  const color = SEVERITY_COLORS[signal.severity];
  let traces: unknown[] = [];
  let extraLayout: Record<string, unknown> = {};

  // 1. Already Plotly-compatible { data, layout }
  const existingData = chartData.data as unknown[] | undefined;
  const existingLayout = chartData.layout as Record<string, unknown> | undefined;
  if (existingData && Array.isArray(existingData)) {
    traces = existingData.map((trace: unknown, i: number) => {
      const t = trace as Record<string, unknown>;
      if (i === 0) {
        return {
          ...t,
          marker: { ...((t.marker as Record<string, unknown>) || {}), color },
        };
      }
      return t;
    });
    if (existingLayout) extraLayout = existingLayout;
  }

  // 2. Grouped data object (box plots) — { data: { "Group A": [...], "Group B": [...] } }
  if (
    traces.length === 0 &&
    chartData.data &&
    typeof chartData.data === "object" &&
    !Array.isArray(chartData.data)
  ) {
    const groups = chartData.data as Record<string, unknown[]>;
    traces = Object.entries(groups).map(([name, values]) => ({
      y: values,
      name,
      type: "box",
      marker: { color },
    }));
  }

  // 3. Points array — [{ x, y, ... }, ...] (scatter/correlation data)
  if (traces.length === 0 && Array.isArray(chartData.points)) {
    const points = chartData.points as Record<string, unknown>[];
    const x = points.map((p) => p.x);
    const y = points.map((p) => p.y);
    traces = [
      {
        x,
        y,
        type: "scatter",
        mode: "markers",
        marker: { color, size: 6, opacity: 0.7 },
      },
    ];
    // Add regression line if present
    const reg = chartData.regression as Record<string, unknown> | undefined;
    if (reg && reg.slope !== undefined && reg.intercept !== undefined) {
      const xNum = x.filter((v): v is number => typeof v === "number");
      if (xNum.length > 0) {
        const xMin = Math.min(...xNum);
        const xMax = Math.max(...xNum);
        const slope = reg.slope as number;
        const intercept = reg.intercept as number;
        traces.push({
          x: [xMin, xMax],
          y: [slope * xMin + intercept, slope * xMax + intercept],
          type: "scatter",
          mode: "lines",
          line: { color: "#94a3b8", width: 1.5, dash: "dash" },
          name: "Regression",
        });
      }
    }
    if (chartData.x_label || chartData.y_label) {
      extraLayout = {
        xaxis: { title: chartData.x_label as string },
        yaxis: { title: chartData.y_label as string },
      };
    }
  }

  // 4. Histogram data — { bins: [...], counts: [...] }
  if (traces.length === 0 && Array.isArray(chartData.bins)) {
    const bins = chartData.bins as number[];
    const counts = (chartData.counts as number[]) || [];
    // bins has N+1 edges, counts has N values — use bin midpoints
    const midpoints = counts.map((_, i) => {
      if (i < bins.length - 1) return (bins[i] + bins[i + 1]) / 2;
      return bins[i];
    });
    traces = [
      {
        x: midpoints,
        y: counts,
        type: "bar",
        marker: { color },
      },
    ];
  }

  // 5. Nested histogram — { histogram: { bins, counts } }
  if (
    traces.length === 0 &&
    chartData.histogram &&
    typeof chartData.histogram === "object"
  ) {
    const hist = chartData.histogram as Record<string, unknown>;
    if (Array.isArray(hist.bins) && Array.isArray(hist.counts)) {
      const bins = hist.bins as number[];
      const counts = hist.counts as number[];
      const midpoints = counts.map((_, i) =>
        i < bins.length - 1 ? (bins[i] + bins[i + 1]) / 2 : bins[i]
      );
      traces = [
        {
          x: midpoints,
          y: counts,
          type: "bar",
          marker: { color },
        },
      ];
    }
  }

  // 6. Bubble chart — { x_values, y_values, bubble_sizes }
  if (
    traces.length === 0 &&
    Array.isArray(chartData.x_values) &&
    Array.isArray(chartData.y_values)
  ) {
    const bubbleSizes = chartData.bubble_sizes as number[] | undefined;
    traces = [
      {
        x: chartData.x_values,
        y: chartData.y_values,
        text: (chartData.labels as string[]) || undefined,
        type: "scatter",
        mode: "markers",
        marker: {
          color,
          size: bubbleSizes || 8,
          sizemode: bubbleSizes ? "area" : undefined,
          sizeref: bubbleSizes
            ? (2.0 * Math.max(...bubbleSizes)) / 40 ** 2
            : undefined,
          opacity: 0.7,
        },
      },
    ];
    if (chartData.x_label || chartData.y_label) {
      extraLayout = {
        xaxis: { title: chartData.x_label as string },
        yaxis: { title: chartData.y_label as string },
      };
    }
  }

  // 7. Generic fallback: find any two matching arrays
  if (traces.length === 0) {
    const xy = extractXY(chartData);
    if (xy) {
      const baseTrace: Record<string, unknown> = {
        x: xy.x,
        y: xy.y,
        marker: { color },
      };
      switch (signal.chart_type) {
        case "line":
          baseTrace.type = "scatter";
          baseTrace.mode = "lines";
          baseTrace.fill = "tozeroy";
          baseTrace.fillcolor = `${color}1a`;
          baseTrace.line = { color, width: 2 };
          break;
        case "scatter":
          baseTrace.type = "scatter";
          baseTrace.mode = "markers";
          baseTrace.marker = { color, size: 8, opacity: 0.8 };
          break;
        default:
          baseTrace.type = "bar";
      }
      traces = [baseTrace];
      if (xy.xLabel || xy.yLabel) {
        extraLayout = {
          xaxis: { title: xy.xLabel },
          yaxis: { title: xy.yLabel },
        };
      }
    }
  }

  if (traces.length === 0) return "";

  const layout = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#94a3b8" },
    xaxis: {
      gridcolor: "#1e293b",
      zerolinecolor: "#1e293b",
      ...(extraLayout.xaxis as Record<string, unknown> || {}),
    },
    yaxis: {
      gridcolor: "#1e293b",
      zerolinecolor: "#1e293b",
      ...(extraLayout.yaxis as Record<string, unknown> || {}),
    },
    margin: { l: 50, r: 20, t: 30, b: 50 },
    showlegend: traces.length > 1,
    height: 300,
    ...Object.fromEntries(
      Object.entries(extraLayout).filter(
        ([k]) => k !== "xaxis" && k !== "yaxis"
      )
    ),
  };

  return JSON.stringify({ data: traces, layout });
}

interface SignalChartRendererProps {
  signal: SignalDetail;
}

export function SignalChartRenderer({ signal }: SignalChartRendererProps) {
  // Memoize the 7-step transform — avoids recomputing on parent re-renders
  // (theme changes, store updates) when chart_data hasn't changed.
  const plotlyJSON = useMemo(
    () => buildSignalPlotlyJSON(signal),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [signal.id, signal.chart_data, signal.chart_type, signal.severity]
  );

  if (!signal.chart_data || !signal.chart_type || !plotlyJSON) {
    return (
      <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  return <ChartRenderer data={plotlyJSON} height={300} />;
}
