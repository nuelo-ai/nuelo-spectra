/**
 * Dashboard metric types matching the backend DashboardMetricsResponse schema.
 */

export interface TrendDataPoint {
  date: string;
  count: number;
}

export interface CreditDistributionItem {
  tier: string;
  user_count: number;
  total_credits: number;
}

export interface LowCreditUser {
  user_id: string;
  email: string;
  name: string;
  balance: number;
  tier: string;
}

export interface CreditSummary {
  total_used: number;
  total_remaining: number;
}

export interface DashboardMetrics {
  // DASH-01: User counts
  total_users: number;
  active_users: number;
  inactive_users: number;
  active_today: number;

  // DASH-02: Signup counts
  signups_today: number;
  signups_this_week: number;
  signups_this_month: number;

  // DASH-03, DASH-04, DASH-05: Platform totals
  total_sessions: number;
  total_files: number;
  total_messages: number;

  // DASH-06: Credit summary
  credit_summary: CreditSummary;

  // DASH-07: Time-series trends
  signup_trend: TrendDataPoint[];
  message_trend: TrendDataPoint[];

  // Additional credit analytics
  credit_distribution: CreditDistributionItem[];
  low_credit_users: LowCreditUser[];
}
