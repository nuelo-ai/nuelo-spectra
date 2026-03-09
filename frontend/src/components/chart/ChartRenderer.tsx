"use client";

import { useRef, useEffect, useState, forwardRef, useImperativeHandle } from "react";
import Plotly from "plotly.js-dist-min";
import { useTheme } from "next-themes";
import { getChartThemeConfig, getPieChartOverrides } from "@/lib/chartTheme";

export interface ChartRendererHandle {
  getElement: () => HTMLDivElement | null;
}

interface ChartRendererProps {
  /** JSON string from backend fig.to_json() */
  data: string;
  /** Optional height override */
  height?: number;
  /** Called after Plotly finishes rendering */
  onReady?: () => void;
}

/**
 * Calculate dynamic chart height based on data complexity.
 *
 * General formula — works for any Plotly chart type:
 *   base (420px)
 *   + logarithmic boost from data point count (up to +140px)
 *   + multi-trace boost for legend overhead (+15px per extra trace, up to +60px)
 *   + small boost for marker-based charts that need vertical spread (+30px)
 *   capped at 620px
 */
function calculateChartHeight(traces: Plotly.PlotData[]): number {
  const BASE = 420;
  const MAX = 620;

  if (traces.length === 0) return BASE;

  let maxPoints = 0;
  for (const trace of traces) {
    const t = trace as unknown as Record<string, unknown>;
    const len = Array.isArray(t.x)
      ? (t.x as unknown[]).length
      : Array.isArray(t.y)
        ? (t.y as unknown[]).length
        : Array.isArray(t.values)
          ? (t.values as unknown[]).length
          : 0;
    if (len > maxPoints) maxPoints = len;
  }

  // Logarithmic scale: grows fast for small counts, flattens for large
  const pointBoost = Math.min(Math.floor(Math.log(maxPoints + 1) * 22), 140);

  // Extra traces → legend needs vertical space
  const traceBoost = Math.min((traces.length - 1) * 15, 60);

  // Marker-based charts (scatter, bubble) spread points vertically — give extra room
  const first = traces[0] as unknown as Record<string, unknown>;
  const mode = (first.mode as string) || "";
  const markerBoost = mode.includes("markers") ? 30 : 0;

  return Math.min(BASE + pointBoost + traceBoost + markerBoost, MAX);
}

const ChartRenderer = forwardRef<ChartRendererHandle, ChartRendererProps>(
  function ChartRenderer({ data, height, onReady }, ref) {
    const chartRef = useRef<HTMLDivElement>(null);
    const [error, setError] = useState<string | null>(null);
    const { resolvedTheme } = useTheme();
    const isDark = resolvedTheme === 'dark';

    useImperativeHandle(ref, () => ({
      getElement: () => chartRef.current,
    }));

    useEffect(() => {
    if (!chartRef.current || !data) return;

    let resizeObserver: ResizeObserver | null = null;
    let raf1: number;
    let raf2: number;

    // Double-rAF: ensures browser has painted spinner before Plotly blocks the main thread
    raf1 = requestAnimationFrame(() => {
    raf2 = requestAnimationFrame(() => {
    if (!chartRef.current) return;
    try {
      const chartData = JSON.parse(data);
      const traces: Plotly.PlotData[] = chartData.data || [];

      // Determine chart height: explicit prop override > dynamic calculation.
      // Backend layout.height is intentionally ignored — it is often stale or too small.
      const chartHeight = height ?? calculateChartHeight(traces);

      // Get theme configuration
      const themeConfig = getChartThemeConfig(isDark ? 'dark' : 'light');

      // Apply pie chart overrides to traces
      const themedTraces = traces.map(trace => {
        const traceAny = trace as any;
        if (traceAny.type === 'pie') {
          const pieOverrides = getPieChartOverrides(isDark ? 'dark' : 'light');
          return { ...trace, ...pieOverrides };
        }
        return trace;
      });

      // Merge layout with theme config (theme overrides backend colors, preserves backend text)
      const layout: Partial<Plotly.Layout> = {
        ...chartData.layout,
        ...themeConfig,
        xaxis: {
          ...chartData.layout?.xaxis,
          ...themeConfig.xaxis,
          title: {
            ...chartData.layout?.xaxis?.title,
            font: themeConfig.xaxis?.title?.font,
          },
        },
        yaxis: {
          ...chartData.layout?.yaxis,
          ...themeConfig.yaxis,
          title: {
            ...chartData.layout?.yaxis?.title,
            font: themeConfig.yaxis?.title?.font,
          },
        },
        title: {
          ...chartData.layout?.title,
          font: themeConfig.title?.font,
        },
        autosize: true,
        height: chartHeight,
        margin: { l: 50, r: 30, t: 100, b: 80 }, // top margin clears modebar, bottom for legend
      };

      const config: Partial<Plotly.Config> = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["sendDataToCloud"] as Plotly.ModeBarDefaultButtons[],
      };

      Plotly.react(chartRef.current, themedTraces, layout, config).then(() => {
        setError(null);
        onReady?.();
      });

      // Set up ResizeObserver for responsive resizing
      resizeObserver = new ResizeObserver(() => {
        if (chartRef.current) {
          Plotly.Plots.resize(chartRef.current);
        }
      });
      resizeObserver.observe(chartRef.current);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to render chart";
      console.error("ChartRenderer error:", err);
      setError(message);
    }
    }); // inner rAF
    }); // outer rAF

    // Cleanup: cancel pending rAFs, disconnect observer, purge Plotly (memory leak prevention)
    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
    }, [data, height, isDark]);

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
