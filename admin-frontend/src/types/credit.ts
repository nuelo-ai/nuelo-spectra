/**
 * TypeScript types for admin credit management.
 * Mirrors backend schemas: credit.py and CreditService distribution endpoint.
 */

export interface CreditDistribution {
  user_class: string;
  user_count: number;
  avg_balance: number;
}

export interface CreditOverviewData {
  distributions: CreditDistribution[];
  total_users: number;
  total_avg_balance: number;
}
