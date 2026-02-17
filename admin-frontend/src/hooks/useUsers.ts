"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type {
  UserListParams,
  UserListResponse,
  UserDetail,
  UserActivityResponse,
  BulkActionResult,
  CreditAdjustRequest,
  CreditTransaction,
} from "@/types/user";

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

export function useUserList(params: UserListParams = {}) {
  return useQuery<UserListResponse>({
    queryKey: ["admin", "users", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params.page) searchParams.set("page", String(params.page));
      if (params.search) searchParams.set("search", params.search);
      if (params.is_active !== undefined && params.is_active !== null)
        searchParams.set("is_active", String(params.is_active));
      if (params.user_class) searchParams.set("user_class", params.user_class);
      if (params.signup_after)
        searchParams.set("signup_after", params.signup_after);
      if (params.signup_before)
        searchParams.set("signup_before", params.signup_before);
      if (params.sort_by) searchParams.set("sort_by", params.sort_by);
      if (params.sort_order) searchParams.set("sort_order", params.sort_order);

      const qs = searchParams.toString();
      const res = await adminApiClient.get(
        `/api/admin/users${qs ? `?${qs}` : ""}`
      );
      if (!res.ok) throw new Error("Failed to fetch users");
      return res.json();
    },
  });
}

export function useUserDetail(userId: string | undefined) {
  return useQuery<UserDetail>({
    queryKey: ["admin", "users", userId],
    queryFn: async () => {
      const res = await adminApiClient.get(`/api/admin/users/${userId}`);
      if (!res.ok) throw new Error("Failed to fetch user detail");
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useUserActivity(userId: string | undefined) {
  return useQuery<UserActivityResponse>({
    queryKey: ["admin", "users", userId, "activity"],
    queryFn: async () => {
      const res = await adminApiClient.get(
        `/api/admin/users/${userId}/activity`
      );
      if (!res.ok) throw new Error("Failed to fetch user activity");
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useUserCreditTransactions(userId: string | undefined) {
  return useQuery<CreditTransaction[]>({
    queryKey: ["admin", "users", userId, "credits"],
    queryFn: async () => {
      const res = await adminApiClient.get(
        `/api/admin/users/${userId}/credits/transactions`
      );
      if (!res.ok) return [];
      return res.json();
    },
    enabled: !!userId,
  });
}

// ---------------------------------------------------------------------------
// Single-user mutation hooks
// ---------------------------------------------------------------------------

function useUserMutation<TPayload = void>(
  mutationFn: (payload: TPayload) => Promise<Response>
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TPayload) => {
      const res = await mutationFn(payload);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useActivateUser() {
  return useUserMutation<{ userId: string }>((p) =>
    adminApiClient.post(`/api/admin/users/${p.userId}/activate`)
  );
}

export function useDeactivateUser() {
  return useUserMutation<{ userId: string }>((p) =>
    adminApiClient.post(`/api/admin/users/${p.userId}/deactivate`)
  );
}

export function useResetPassword() {
  return useUserMutation<{ userId: string }>((p) =>
    adminApiClient.post(`/api/admin/users/${p.userId}/password-reset`)
  );
}

export function useChangeTier() {
  return useUserMutation<{ userId: string; user_class: string }>((p) =>
    adminApiClient.put(`/api/admin/users/${p.userId}/tier`, {
      user_class: p.user_class,
    })
  );
}

export function useAdjustCredits() {
  return useUserMutation<{ userId: string } & CreditAdjustRequest>((p) =>
    adminApiClient.post(`/api/admin/users/${p.userId}/credits/adjust`, {
      amount: p.amount,
      reason: p.reason,
    })
  );
}

export function useDeleteUser() {
  return useUserMutation<{ userId: string; challenge_code: string }>((p) =>
    adminApiClient.delete(
      `/api/admin/users/${p.userId}?challenge_code=${p.challenge_code}`
    )
  );
}

export function useDeleteChallenge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      const res = await adminApiClient.post(
        `/api/admin/users/${userId}/delete-challenge`
      );
      if (!res.ok) throw new Error("Failed to get challenge code");
      return res.json() as Promise<{ challenge_code: string; expires_in: number }>;
    },
  });
}

// ---------------------------------------------------------------------------
// Bulk mutation hooks
// ---------------------------------------------------------------------------

function useBulkMutation<TPayload>(
  mutationFn: (payload: TPayload) => Promise<Response>
) {
  const qc = useQueryClient();
  return useMutation<BulkActionResult, Error, TPayload>({
    mutationFn: async (payload: TPayload) => {
      const res = await mutationFn(payload);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Bulk operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useBulkActivate() {
  return useBulkMutation<{ user_ids: string[] }>((p) =>
    adminApiClient.post("/api/admin/users/bulk/activate", p)
  );
}

export function useBulkDeactivate() {
  return useBulkMutation<{ user_ids: string[] }>((p) =>
    adminApiClient.post("/api/admin/users/bulk/deactivate", p)
  );
}

export function useBulkChangeTier() {
  return useBulkMutation<{ user_ids: string[]; user_class: string }>((p) =>
    adminApiClient.post("/api/admin/users/bulk/tier-change", p)
  );
}

export function useBulkAdjustCredits() {
  return useBulkMutation<{
    user_ids: string[];
    delta?: number;
    amount?: number;
    reason: string;
  }>((p) => adminApiClient.post("/api/admin/users/bulk/credit-adjust", p));
}

export function useBulkDeleteChallenge() {
  return useMutation({
    mutationFn: async (user_ids: string[]) => {
      const res = await adminApiClient.post(
        "/api/admin/users/bulk/delete-challenge",
        { user_ids }
      );
      if (!res.ok) throw new Error("Failed to get bulk delete challenge");
      return res.json() as Promise<{ challenge_code: string; expires_in: number }>;
    },
  });
}

export function useBulkDelete() {
  return useBulkMutation<{ user_ids: string[]; challenge_code: string }>((p) =>
    adminApiClient.post("/api/admin/users/bulk/delete", p)
  );
}
