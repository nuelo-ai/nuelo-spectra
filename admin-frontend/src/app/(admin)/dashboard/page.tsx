"use client";

import React from "react";
import {
  Users,
  UserCheck,
  UserPlus,
  MessageSquare,
  Send,
  CreditCard,
  RefreshCw,
} from "lucide-react";
import { useDashboardMetrics } from "@/hooks/useDashboard";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { CreditDistributionChart } from "@/components/dashboard/CreditDistributionChart";
import { LowCreditTable } from "@/components/dashboard/LowCreditTable";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const { data: metrics, isLoading, isError, error, refetch } =
    useDashboardMetrics();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <p className="text-destructive font-medium">
          Failed to load dashboard metrics
        </p>
        <p className="text-sm text-muted-foreground">
          {error?.message || "An unexpected error occurred"}
        </p>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Row 1: Metric Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          title="Total Users"
          value={metrics.total_users}
          subtitle={`${metrics.active_users} active / ${metrics.inactive_users} inactive`}
          icon={<Users className="h-5 w-5" />}
        />
        <MetricCard
          title="Active Today"
          value={metrics.active_today}
          icon={<UserCheck className="h-5 w-5" />}
        />
        <MetricCard
          title="New Signups"
          value={metrics.signups_this_month}
          subtitle={`today: ${metrics.signups_today} / week: ${metrics.signups_this_week} / month: ${metrics.signups_this_month}`}
          icon={<UserPlus className="h-5 w-5" />}
        />
        <MetricCard
          title="Total Sessions"
          value={metrics.total_sessions}
          icon={<MessageSquare className="h-5 w-5" />}
        />
        <MetricCard
          title="Messages Sent"
          value={metrics.total_messages}
          icon={<Send className="h-5 w-5" />}
        />
        <MetricCard
          title="Credit Balance"
          value={metrics.credit_summary.total_remaining.toLocaleString(
            undefined,
            { maximumFractionDigits: 0 }
          )}
          subtitle={`${metrics.credit_summary.total_used.toLocaleString(undefined, { maximumFractionDigits: 0 })} used / ${metrics.credit_summary.total_remaining.toLocaleString(undefined, { maximumFractionDigits: 0 })} remaining`}
          icon={<CreditCard className="h-5 w-5" />}
        />
      </div>

      {/* Row 2: Trend Charts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendChart
          title="Signups Over Time"
          data={metrics.signup_trend}
          color="var(--color-chart-1)"
        />
        <TrendChart
          title="Messages Over Time"
          data={metrics.message_trend}
          color="var(--color-chart-2)"
        />
      </div>

      {/* Row 3: Credit Section */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CreditDistributionChart data={metrics.credit_distribution} />
        <LowCreditTable users={metrics.low_credit_users} />
      </div>
    </div>
  );
}
