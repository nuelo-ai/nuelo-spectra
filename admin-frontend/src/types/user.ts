/**
 * TypeScript types for admin user management.
 * Mirrors backend schemas: admin_users.py
 */

export interface UserSummary {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  user_class: string;
  created_at: string;
  last_login_at: string | null;
  credit_balance: number;
}

export interface UserDetail extends UserSummary {
  is_admin: boolean;
  updated_at: string;
  file_count: number;
  session_count: number;
  message_count: number;
  last_message_at: string | null;
}

export interface ActivityMonth {
  month: string; // ISO format "2026-01"
  message_count: number;
  session_count: number;
}

export interface UserActivityResponse {
  user_id: string;
  months: ActivityMonth[];
}

export interface UserListResponse {
  users: UserSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface UserListParams {
  page?: number;
  search?: string;
  is_active?: boolean | null;
  user_class?: string | null;
  signup_after?: string | null;
  signup_before?: string | null;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface CreditAdjustRequest {
  amount: number;
  reason: string;
  password: string;
}

export interface CreditTransaction {
  id: string;
  user_id: string;
  amount: number;
  balance_after: number;
  transaction_type: string;
  reason: string | null;
  admin_id: string | null;
  created_at: string;
}

export interface BulkActionResult {
  succeeded: number;
  failed: number;
  errors: Array<{ user_id: string; error: string }>;
}
