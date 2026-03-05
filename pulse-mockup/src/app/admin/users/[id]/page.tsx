"use client";

import { useParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { ADMIN_USERS, USER_WORKSPACE_DATA } from "@/lib/mock-data";

function getInitials(name: string): string {
  const parts = name.trim().split(" ");
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (
    parts[0].charAt(0).toUpperCase() +
    parts[parts.length - 1].charAt(0).toUpperCase()
  );
}

function TierBadge({ tier }: { tier: "free" | "pro" | "enterprise" }) {
  if (tier === "pro") {
    return (
      <Badge variant="outline" className="text-blue-400 border-blue-400/30">
        pro
      </Badge>
    );
  }
  if (tier === "enterprise") {
    return (
      <Badge variant="outline" className="text-purple-400 border-purple-400/30">
        enterprise
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-muted-foreground">
      free
    </Badge>
  );
}

function StatusBadge({ status }: { status: "active" | "suspended" }) {
  if (status === "active") {
    return (
      <Badge variant="outline" className="text-emerald-400 border-emerald-400/30">
        active
      </Badge>
    );
  }
  return <Badge variant="destructive">suspended</Badge>;
}

export default function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const user = ADMIN_USERS.find((u) => u.id === id) ?? ADMIN_USERS[0];
  const workspace = USER_WORKSPACE_DATA[user.id];

  const usagePercent =
    workspace.creditLimit > 0
      ? Math.round((workspace.creditsUsed / workspace.creditLimit) * 100)
      : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header card */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-start gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-semibold">{user.name}</h1>
            <p className="text-sm text-muted-foreground">{user.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={user.status} />
              <TierBadge tier={user.tier} />
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {workspace.creditsUsed} credits used this month
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="workspace">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="workspace">Workspace</TabsTrigger>
          <TabsTrigger value="apikeys">API Keys</TabsTrigger>
        </TabsList>

        {/* Overview tab — placeholder stat cards */}
        <TabsContent value="overview" className="mt-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: "Sessions", value: 12 },
              { label: "Files", value: 8 },
              { label: "Reports", value: 4 },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-card border border-border rounded-lg p-4"
              >
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="text-2xl font-bold mt-1">{stat.value}</p>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Workspace tab — fully built */}
        <TabsContent value="workspace" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* LEFT COLUMN */}
            <div className="space-y-4">
              {/* Collections list */}
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Collections
              </h3>
              {workspace.collections.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No collections yet.
                </p>
              ) : (
                <div className="bg-card border border-border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Signals</TableHead>
                        <TableHead>Credits</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {workspace.collections.map((c) => (
                        <TableRow key={c.id}>
                          <TableCell className="font-medium">
                            {c.name}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                c.status === "active"
                                  ? "text-emerald-400 border-emerald-400/30"
                                  : "text-muted-foreground"
                              }
                            >
                              {c.status}
                            </Badge>
                          </TableCell>
                          <TableCell>{c.signals}</TableCell>
                          <TableCell>{c.credits}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Activity Timeline */}
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mt-6">
                Activity
              </h3>
              <div className="space-y-3">
                {workspace.activityTimeline.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No activity recorded.
                  </p>
                ) : (
                  workspace.activityTimeline.map((event, i) => (
                    <div key={i} className="flex gap-3 items-start">
                      <div className="mt-1 h-2 w-2 rounded-full bg-primary shrink-0" />
                      <div>
                        <p className="text-sm">{event.event}</p>
                        <p className="text-xs text-muted-foreground">
                          {event.timestamp}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* RIGHT COLUMN */}
            <div className="space-y-4">
              {/* Credit breakdown donut chart */}
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Credit Breakdown
              </h3>
              <div className="bg-card border border-border rounded-lg p-4">
                {workspace.creditBreakdown.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={workspace.creditBreakdown}
                        innerRadius={50}
                        outerRadius={80}
                        dataKey="value"
                      >
                        {workspace.creditBreakdown.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value) => [`${value} credits`, ""]}
                        contentStyle={{
                          backgroundColor: "#111827",
                          border: "1px solid #1e293b",
                          borderRadius: "6px",
                          color: "#f1f5f9",
                        }}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No credit usage yet.
                  </p>
                )}
              </div>

              {/* Monthly limit progress bar */}
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Monthly Limit
              </h3>
              <div className="bg-card border border-border rounded-lg p-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span>{workspace.creditsUsed} credits used</span>
                  <span className="text-muted-foreground">
                    {workspace.creditLimit} limit
                  </span>
                </div>
                <Progress
                  value={(workspace.creditsUsed / workspace.creditLimit) * 100}
                  className="h-2"
                />
                <p className="text-xs text-muted-foreground">
                  {usagePercent}% of monthly limit
                </p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* API Keys tab — placeholder */}
        <TabsContent value="apikeys" className="mt-4">
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <p className="text-sm">API key management coming soon</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
