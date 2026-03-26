"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UserBillingDetail {
  subscription: {
    has_subscription: boolean;
    plan_tier: string | null;
    status: string | null;
    stripe_customer_id: string | null;
    stripe_subscription_id: string | null;
    current_period_start: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
  };
  payments: Array<{
    id: string;
    created_at: string;
    payment_type: string;
    amount_cents: number;
    currency: string;
    credit_amount: number | null;
    status: string;
    stripe_payment_intent_id: string | null;
  }>;
  stripe_events: Array<{
    id: string;
    stripe_event_id: string;
    event_type: string;
    processed_at: string;
  }>;
}

export interface BillingSettings {
  monetization_enabled: boolean;
  price_standard_monthly_cents: number;
  price_premium_monthly_cents: number;
  stripe_price_standard_monthly: string;
  stripe_price_premium_monthly: string;
}

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

export function useUserBillingDetail(userId: string | undefined) {
  return useQuery<UserBillingDetail>({
    queryKey: ["admin", "billing", userId],
    queryFn: async () => {
      const res = await adminApiClient.get(
        `/api/admin/billing/users/${userId}`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to fetch billing detail");
      }
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useBillingSettings() {
  return useQuery<BillingSettings>({
    queryKey: ["admin", "billing-settings"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/billing-settings");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to fetch billing settings");
      }
      return res.json();
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

export function useForceSetTier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      userId: string;
      new_tier: string;
      reason: string;
    }) => {
      const res = await adminApiClient.post(
        `/api/admin/billing/users/${payload.userId}/force-set-tier`,
        { new_tier: payload.new_tier, reason: payload.reason }
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "billing"] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useAdminCancelSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { userId: string }) => {
      const res = await adminApiClient.post(
        `/api/admin/billing/users/${payload.userId}/cancel`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "billing"] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useRefundPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      userId: string;
      payment_id: string;
      amount_cents?: number;
    }) => {
      const res = await adminApiClient.post(
        `/api/admin/billing/users/${payload.userId}/refund`,
        { payment_id: payload.payment_id, amount_cents: payload.amount_cents }
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "billing"] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useUpdateBillingSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<BillingSettings>) => {
      const res = await adminApiClient.put(
        "/api/admin/billing-settings",
        payload
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "billing-settings"] });
    },
  });
}
