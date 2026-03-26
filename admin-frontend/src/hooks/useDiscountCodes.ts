"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DiscountCode {
  id: string;
  code: string;
  discount_type: "percent_off" | "amount_off";
  discount_value: number;
  currency: string;
  stripe_coupon_id: string | null;
  stripe_promotion_code_id: string | null;
  max_redemptions: number | null;
  times_redeemed: number;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DiscountCodeListResponse {
  items: DiscountCode[];
  total: number;
}

interface CreateDiscountCodePayload {
  code: string;
  discount_type: "percent_off" | "amount_off";
  discount_value: number;
  max_redemptions?: number;
  expires_at?: string;
}

interface UpdateDiscountCodePayload {
  codeId: string;
  max_redemptions?: number | null;
  expires_at?: string | null;
}

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

export function useDiscountCodes() {
  return useQuery<DiscountCodeListResponse>({
    queryKey: ["admin", "discount-codes"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/discount-codes");
      if (!res.ok) throw new Error("Failed to fetch discount codes");
      return res.json();
    },
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

export function useCreateDiscountCode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateDiscountCodePayload) => {
      const res = await adminApiClient.post(
        "/api/admin/discount-codes",
        payload
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to create discount code");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "discount-codes"] });
    },
  });
}

export function useUpdateDiscountCode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ codeId, ...body }: UpdateDiscountCodePayload) => {
      const res = await adminApiClient.put(
        `/api/admin/discount-codes/${codeId}`,
        body
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to update discount code");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "discount-codes"] });
    },
  });
}

export function useDeactivateDiscountCode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (codeId: string) => {
      const res = await adminApiClient.post(
        `/api/admin/discount-codes/${codeId}/deactivate`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to deactivate discount code");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "discount-codes"] });
    },
  });
}

export function useDeleteDiscountCode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (codeId: string) => {
      const res = await adminApiClient.delete(
        `/api/admin/discount-codes/${codeId}`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to delete discount code");
      }
      // 204 No Content — no body to parse
      return { status: "deleted" };
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "discount-codes"] });
    },
  });
}
