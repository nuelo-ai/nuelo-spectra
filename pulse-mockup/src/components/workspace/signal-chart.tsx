"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  AreaChart,
} from "recharts";
import type { Signal, SignalSeverity } from "@/lib/mock-data";

const severityColors: Record<SignalSeverity, string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#22c55e",
};

interface SignalChartProps {
  signal: Signal;
}

function ChartTooltipContent({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-md">
      <p className="text-xs font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-xs text-muted-foreground">
          <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: entry.color }} />
          {entry.name}: {typeof entry.value === "number" ? entry.value.toLocaleString() : entry.value}
        </p>
      ))}
    </div>
  );
}

function LineSignalChart({ signal }: SignalChartProps) {
  const data = signal.chartData;
  const keys = Object.keys(data[0] || {}).filter((k) => k !== Object.keys(data[0])[0]);
  const xKey = Object.keys(data[0] || {})[0];
  const highlightColor = severityColors[signal.severity];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.5} />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltipContent />} />
        {keys.map((key, i) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stroke={i === 0 ? highlightColor : "#64748b"}
            fill={i === 0 ? highlightColor : "transparent"}
            fillOpacity={i === 0 ? 0.1 : 0}
            strokeWidth={i === 0 ? 2 : 1.5}
            strokeDasharray={i === 0 ? undefined : "5 5"}
            dot={false}
            name={key.charAt(0).toUpperCase() + key.slice(1)}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

function BarSignalChart({ signal }: SignalChartProps) {
  const data = signal.chartData;
  const allKeys = Object.keys(data[0] || {});
  // The first key is typically the category/label axis
  const xKey = allKeys[0];
  // Find numeric keys for bars
  const numericKeys = allKeys.filter((k) => typeof data[0][k] === "number");
  const highlightColor = severityColors[signal.severity];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.5} vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltipContent />} />
        {numericKeys.map((key, i) => (
          <Bar
            key={key}
            dataKey={key}
            fill={i === 0 ? highlightColor : "#3b82f6"}
            fillOpacity={0.85}
            radius={[4, 4, 0, 0]}
            name={key.charAt(0).toUpperCase() + key.slice(1)}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function ScatterSignalChart({ signal }: SignalChartProps) {
  const data = signal.chartData;
  const allKeys = Object.keys(data[0] || {});
  const numericKeys = allKeys.filter((k) => typeof data[0][k] === "number");
  const xKey = numericKeys[0] || allKeys[0];
  const yKey = numericKeys[1] || allKeys[1];
  const highlightColor = severityColors[signal.severity];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.5} />
        <XAxis
          dataKey={xKey}
          type="number"
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
          name={xKey.charAt(0).toUpperCase() + xKey.slice(1)}
        />
        <YAxis
          dataKey={yKey}
          type="number"
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          tickLine={false}
          name={yKey.charAt(0).toUpperCase() + yKey.slice(1)}
        />
        <Tooltip content={<ChartTooltipContent />} />
        <Scatter
          data={data}
          fill={highlightColor}
          fillOpacity={0.8}
          name="Data"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function SignalChart({ signal }: SignalChartProps) {
  switch (signal.chartType) {
    case "line":
      return <LineSignalChart signal={signal} />;
    case "bar":
      return <BarSignalChart signal={signal} />;
    case "scatter":
      return <ScatterSignalChart signal={signal} />;
    default:
      return <div className="text-muted-foreground text-sm">Unsupported chart type</div>;
  }
}
