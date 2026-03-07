"use client";

import ChartRenderer from "@/components/chart/ChartRenderer";
import type { SignalDetail } from "@/types/workspace";

const SEVERITY_COLORS: Record<SignalDetail["severity"], string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#22c55e",
};

/**
 * Build a Plotly JSON string from a SignalDetail's chart_data + chart_type.
 * - bar -> Plotly bar trace
 * - line -> Plotly scatter with mode "lines" + fill "tozeroy" (area chart)
 * - scatter -> Plotly scatter with mode "markers"
 */
function buildSignalPlotlyJSON(signal: SignalDetail): string {
  const chartData = signal.chart_data as Record<string, unknown> | null;
  if (!chartData) return "";

  const color = SEVERITY_COLORS[signal.severity];

  // chart_data may already be Plotly-compatible { data, layout } from backend
  // or it may be raw data arrays that need wrapping
  const existingData = chartData.data as unknown[] | undefined;
  const existingLayout = chartData.layout as Record<string, unknown> | undefined;

  let traces: unknown[];
  if (existingData && Array.isArray(existingData)) {
    // Backend already provides Plotly traces — apply severity color to first trace
    traces = existingData.map((trace: unknown, i: number) => {
      const t = trace as Record<string, unknown>;
      if (i === 0) {
        return { ...t, marker: { ...(t.marker as Record<string, unknown> || {}), color } };
      }
      return t;
    });
  } else {
    // Raw data object — extract x/y arrays and build trace from chart_type
    const x = (chartData.x as unknown[]) || (chartData.labels as unknown[]) || [];
    const y = (chartData.y as unknown[]) || (chartData.values as unknown[]) || [];

    const baseTrace: Record<string, unknown> = { x, y, marker: { color } };

    switch (signal.chart_type) {
      case "bar":
        baseTrace.type = "bar";
        break;
      case "line":
        baseTrace.type = "scatter";
        baseTrace.mode = "lines";
        baseTrace.fill = "tozeroy";
        baseTrace.fillcolor = `${color}1a`; // 10% opacity fill
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
  }

  const layout = {
    ...existingLayout,
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#94a3b8" },
    xaxis: {
      ...(existingLayout?.xaxis as Record<string, unknown> || {}),
      gridcolor: "#1e293b",
      zerolinecolor: "#1e293b",
    },
    yaxis: {
      ...(existingLayout?.yaxis as Record<string, unknown> || {}),
      gridcolor: "#1e293b",
      zerolinecolor: "#1e293b",
    },
    margin: { l: 50, r: 20, t: 30, b: 50 },
    showlegend: false,
    height: 300,
  };

  return JSON.stringify({ data: traces, layout });
}

interface SignalChartRendererProps {
  signal: SignalDetail;
}

export function SignalChartRenderer({ signal }: SignalChartRendererProps) {
  if (!signal.chart_data || !signal.chart_type) {
    return (
      <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  const plotlyJSON = buildSignalPlotlyJSON(signal);
  if (!plotlyJSON) {
    return (
      <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  return <ChartRenderer data={plotlyJSON} height={300} />;
}
