"use client";

import {
  FolderOpen,
  Users,
  Zap,
  TrendingUp,
  ChevronDown,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  COLLECTIONS_OVER_TIME,
  COLLECTION_STATUS_BREAKDOWN,
  ACTIVITY_BY_TYPE,
  PIPELINE_ADOPTION,
  CREDIT_USAGE_OVER_TIME,
} from "@/lib/mock-data";

// KPI stat card data
const KPI_CARDS = [
  {
    label: "Total Collections",
    value: "50",
    icon: FolderOpen,
    iconColor: "text-blue-400",
    iconBg: "bg-blue-500/10",
  },
  {
    label: "Active Users",
    value: "3",
    icon: Users,
    iconColor: "text-emerald-400",
    iconBg: "bg-emerald-500/10",
  },
  {
    label: "Credits Used This Month",
    value: "290",
    icon: Zap,
    iconColor: "text-yellow-400",
    iconBg: "bg-yellow-500/10",
  },
  {
    label: "Avg Credits per Collection",
    value: "5.8",
    icon: TrendingUp,
    iconColor: "text-violet-400",
    iconBg: "bg-violet-500/10",
  },
];

// Funnel widths as percentages
const funnelMax = PIPELINE_ADOPTION[0].count;

export default function AdminDashboardPage() {
  return (
    <div className="space-y-8">
      {/* Page heading */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Workspace Activity Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Platform-wide workspace metrics
        </p>
      </div>

      {/* Section 1 — KPI Row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {KPI_CARDS.map((card) => (
          <div
            key={card.label}
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4"
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${card.iconBg}`}
            >
              <card.icon className={`h-5 w-5 ${card.iconColor}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{card.value}</p>
              <p className="text-xs uppercase text-muted-foreground">
                {card.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Section 2 — Workspace Activity */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Workspace Activity
        </h2>

        {/* Row 1: Line chart + Donut chart */}
        <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Line chart */}
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="mb-3 text-sm font-medium text-muted-foreground">
              Collections Over Time
            </p>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={COLLECTIONS_OVER_TIME}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111827",
                    border: "1px solid #1e293b",
                    borderRadius: "6px",
                    color: "#f1f5f9",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Donut chart */}
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="mb-3 text-sm font-medium text-muted-foreground">
              Active vs. Archived Collections
            </p>
            <div className="relative">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={COLLECTION_STATUS_BREAKDOWN}
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    startAngle={90}
                    endAngle={-270}
                  >
                    {COLLECTION_STATUS_BREAKDOWN.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111827",
                      border: "1px solid #1e293b",
                      borderRadius: "6px",
                      color: "#f1f5f9",
                    }}
                  />
                  <Legend
                    wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
              {/* Center label */}
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-xl font-bold text-foreground">50</p>
                  <p className="text-xs text-muted-foreground">Total</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Row 2: Grouped bar chart — full width */}
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="mb-3 text-sm font-medium text-muted-foreground">
            Activity by Type per Month
          </p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={ACTIVITY_BY_TYPE}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="month"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
              />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111827",
                  border: "1px solid #1e293b",
                  borderRadius: "6px",
                  color: "#f1f5f9",
                }}
              />
              <Legend wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }} />
              <Bar dataKey="pulse" name="Pulse" fill="#3b82f6" />
              <Bar
                dataKey="investigation"
                name="Investigation"
                fill="#8b5cf6"
              />
              <Bar dataKey="whatif" name="What-If" fill="#a78bfa" />
              <Bar dataKey="report" name="Report" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Section 3 — Pipeline Adoption */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Pipeline Adoption
        </h2>
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="mx-auto max-w-2xl space-y-3">
            {PIPELINE_ADOPTION.map((stage, index) => {
              const widthPct = Math.round((stage.count / funnelMax) * 100);
              const prevCount =
                index > 0 ? PIPELINE_ADOPTION[index - 1].count : null;
              const dropPct =
                prevCount !== null
                  ? Math.round((1 - stage.count / prevCount) * 100)
                  : null;

              return (
                <div key={stage.stage}>
                  {/* Connector arrow between stages */}
                  {index > 0 && (
                    <div className="flex justify-center py-1">
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    </div>
                  )}
                  <div className="flex justify-center">
                    <div
                      style={{
                        width: `${widthPct}%`,
                        backgroundColor: stage.color,
                      }}
                      className="flex h-12 items-center rounded px-4"
                    >
                      <span className="flex-1 text-sm font-medium text-white">
                        {stage.stage}
                      </span>
                      <span className="shrink-0 text-right text-sm text-white/90">
                        {stage.count}
                        {dropPct !== null && (
                          <span className="ml-2 text-xs text-white/60">
                            (-{dropPct}%)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Section 4 — Credit Usage */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Credit Usage
        </h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Stacked bar chart — 2/3 width */}
          <div className="rounded-lg border border-border bg-card p-4 lg:col-span-2">
            <p className="mb-3 text-sm font-medium text-muted-foreground">
              Credits Used by Activity Type
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={CREDIT_USAGE_OVER_TIME}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111827",
                    border: "1px solid #1e293b",
                    borderRadius: "6px",
                    color: "#f1f5f9",
                  }}
                />
                <Legend wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }} />
                <Bar
                  dataKey="pulse"
                  name="Pulse"
                  stackId="a"
                  fill="#3b82f6"
                />
                <Bar
                  dataKey="investigation"
                  name="Investigation"
                  stackId="a"
                  fill="#8b5cf6"
                />
                <Bar
                  dataKey="whatif"
                  name="What-If"
                  stackId="a"
                  fill="#a78bfa"
                />
                <Bar
                  dataKey="report"
                  name="Report"
                  stackId="a"
                  fill="#6366f1"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Avg credits KPI card — 1/3 width */}
          <div className="flex flex-col justify-center rounded-lg border border-border bg-card p-6">
            <p className="text-5xl font-bold text-primary">5.8</p>
            <p className="mt-2 text-sm text-muted-foreground">Avg Credits</p>
            <p className="text-sm text-muted-foreground">per Collection</p>
            <p className="mt-4 text-xs text-muted-foreground/60">
              Based on 50 Collections this month
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
