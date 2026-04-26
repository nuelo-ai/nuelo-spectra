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
  config_defaults: Record<string, number>;
  stripe_readiness: { ready: boolean; missing: string[] };
}

export interface AdminCreditPackageConfigDefaults {
  name: string;
  price_cents: number;
  credit_amount: number;
  display_order: number;
}

export interface AdminCreditPackage {
  id: string;
  name: string;
  price_cents: number;
  credit_amount: number;
  display_order: number;
  is_active: boolean;
  stripe_price_id: string;
  config_defaults: AdminCreditPackageConfigDefaults | null;
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
    mutationFn: async (payload: Partial<BillingSettings> & { password?: string }) => {
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

export function useAdminCreditPackages() {
  return useQuery<AdminCreditPackage[]>({
    queryKey: ["admin", "credit-packages"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/credit-packages");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to fetch credit packages");
      }
      return res.json();
    },
  });
}

export function useUpdateCreditPackage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      packageId: string;
      name: string;
      price_cents: number;
      credit_amount: number;
      display_order: number;
      is_active: boolean;
      password: string;
    }) => {
      const { packageId, ...body } = payload;
      const res = await adminApiClient.put(
        `/api/admin/credit-packages/${packageId}`,
        body
      );
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "credit-packages"] });
    },
  });
}

export function useResetSubscriptionPricing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { password: string }) => {
      const res = await adminApiClient.post(
        "/api/admin/billing-settings/reset",
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

export function useResetCreditPackages() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { password: string }) => {
      const res = await adminApiClient.post(
        "/api/admin/credit-packages/reset",
        payload
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "credit-packages"] });
      qc.invalidateQueries({ queryKey: ["admin", "billing-settings"] });
    },
  });
}
