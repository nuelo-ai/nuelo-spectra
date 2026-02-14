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
}

/**
 * Calculate dynamic chart height based on data complexity.
 * Base: 400px, +10px per 100 data points, capped at 700px.
 * If backend layout explicitly sets height, that takes priority (handled by caller).
 */
function calculateChartHeight(chartData: Plotly.PlotData[]): number {
  const BASE_HEIGHT = 400;
  const MAX_HEIGHT = 700;

  let totalPoints = 0;
  for (const trace of chartData) {
    // Count data points from common trace properties
    const traceAny = trace as unknown as Record<string, unknown>;
    if (Array.isArray(traceAny.x)) {
      totalPoints += traceAny.x.length;
    } else if (Array.isArray(traceAny.y)) {
      totalPoints += traceAny.y.length;
    } else if (Array.isArray(traceAny.values)) {
      totalPoints += traceAny.values.length;
    }
  }

  const dynamicHeight = BASE_HEIGHT + Math.floor(totalPoints / 100) * 10;
  return Math.min(dynamicHeight, MAX_HEIGHT);
}

const ChartRenderer = forwardRef<ChartRendererHandle, ChartRendererProps>(
  function ChartRenderer({ data, height }, ref) {
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

    try {
      const chartData = JSON.parse(data);
      const traces: Plotly.PlotData[] = chartData.data || [];

      // Determine chart height: prop override > backend layout > dynamic calculation
      const chartHeight =
        height ?? chartData.layout?.height ?? calculateChartHeight(traces);

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
        margin: { l: 50, r: 30, t: 60, b: 80 }, // top margin clears modebar, bottom for legend
      };

      const config: Partial<Plotly.Config> = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["sendDataToCloud"] as Plotly.ModeBarDefaultButtons[],
      };

      Plotly.react(chartRef.current, themedTraces, layout, config);
      setError(null);

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

    // Cleanup: disconnect observer and purge Plotly (memory leak prevention)
    return () => {
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
