"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CreditDistributionItem } from "@/types/dashboard";

interface CreditDistributionChartProps {
  data: CreditDistributionItem[];
}

/**
 * Chart colors derived from the theme's chart CSS variables.
 * Falls back to hardcoded values for SSR safety.
 */
const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

/**
 * Credit distribution by tier shown as a horizontal bar chart.
 * Each tier gets a distinct chart color from the theme palette.
 */
export function CreditDistributionChart({
  data,
}: CreditDistributionChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Credit Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground py-8 text-center">
            No credit distribution data available
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Credit Distribution by Tier</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              horizontal={false}
            />
            <XAxis
              type="number"
              tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              dataKey="tier"
              type="category"
              tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-card)",
                borderColor: "var(--color-border)",
                borderRadius: "0.5rem",
                color: "var(--color-card-foreground)",
                fontSize: "0.875rem",
              }}
              formatter={(value: number, name: string) => {
                if (name === "user_count") return [value, "Users"];
                if (name === "total_credits")
                  return [value.toLocaleString(), "Credits"];
                return [value, name];
              }}
            />
            <Bar dataKey="user_count" name="user_count" radius={[0, 4, 4, 0]}>
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        {/* Credits legend below chart */}
        <div className="mt-4 grid grid-cols-2 gap-2">
          {data.map((item, index) => (
            <div key={item.tier} className="flex items-center gap-2 text-xs">
              <div
                className="h-2.5 w-2.5 rounded-full shrink-0"
                style={{
                  backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                }}
              />
              <span className="text-muted-foreground truncate">
                {item.tier}: {item.total_credits.toLocaleString()} credits
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
