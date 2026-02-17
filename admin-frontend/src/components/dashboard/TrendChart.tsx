"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { TrendDataPoint } from "@/types/dashboard";

interface TrendChartProps {
  title: string;
  data: TrendDataPoint[];
  color: string;
  dataKey?: string;
}

/**
 * Format a date string (YYYY-MM-DD) to short display (MMM DD).
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/**
 * Time-series trend chart using Recharts AreaChart.
 * Supports time range filtering (7d/30d/90d) and theme-aware colors.
 */
export function TrendChart({
  title,
  data,
  color,
  dataKey = "count",
}: TrendChartProps) {
  const [range, setRange] = useState<string>("all");

  const filteredData = React.useMemo(() => {
    if (range === "all") return data;
    const days = parseInt(range);
    return data.slice(-days);
  }, [data, range]);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">{title}</CardTitle>
        <Tabs value={range} onValueChange={setRange}>
          <TabsList className="h-7">
            <TabsTrigger value="7" className="text-xs px-2 py-0.5">
              7d
            </TabsTrigger>
            <TabsTrigger value="30" className="text-xs px-2 py-0.5">
              30d
            </TabsTrigger>
            <TabsTrigger value="all" className="text-xs px-2 py-0.5">
              All
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart
            data={filteredData}
            margin={{ top: 5, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              className="text-xs"
              tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-card)",
                borderColor: "var(--color-border)",
                borderRadius: "0.5rem",
                color: "var(--color-card-foreground)",
                fontSize: "0.875rem",
              }}
              labelFormatter={formatDate}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              fill={`url(#gradient-${title})`}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
