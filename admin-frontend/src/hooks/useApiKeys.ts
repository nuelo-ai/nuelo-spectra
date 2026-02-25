"use client";

/**
 * Admin API key management hooks using TanStack Query.
 * Provides hooks for listing, creating, and revoking API keys for any user.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import { toast } from "sonner";

export interface AdminApiKeyListItem {
  id: string;
  name: string;
  description: string | null;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
  total_credits_used: number;
  created_by_admin_id: string | null;
}

export interface ApiKeyCreateResponse {
  id: string;
  name: string;
  key_prefix: string;
  full_key: string;
  created_at: string;
}

export interface ApiKeyCreateRequest {
  name: string;
  description?: string;
}

/**
 * Hook for listing all API keys for a specific user.
 * Fetches active and revoked keys via admin endpoint.
 */
export function useUserApiKeys(userId: string | undefined) {
  return useQuery<AdminApiKeyListItem[]>({
    queryKey: ["admin", "users", userId, "api-keys"],
    queryFn: async () => {
      const res = await adminApiClient.get(
        `/api/admin/users/${userId}/api-keys`
      );
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to fetch API keys");
      }
      return await res.json();
    },
    enabled: !!userId,
  });
}

/**
 * Hook for creating an API key on behalf of a user.
 * On success: invalidates key list and shows success toast.
 */
export function useCreateUserApiKey(userId: string) {
  const queryClient = useQueryClient();
  return useMutation<ApiKeyCreateResponse, Error, ApiKeyCreateRequest>({
    mutationFn: async (data) => {
      const res = await adminApiClient.post(
        `/api/admin/users/${userId}/api-keys`,
        data
      );
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to create API key");
      }
      return await res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["admin", "users", userId, "api-keys"],
      });
      toast.success("API key created");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create API key");
    },
  });
}

/**
 * Hook for revoking a user's API key.
 * On success: invalidates key list and shows success toast.
 */
export function useRevokeUserApiKey(userId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (keyId) => {
      const res = await adminApiClient.delete(
        `/api/admin/users/${userId}/api-keys/${keyId}`
      );
      if (!res.ok) {
        // 204 has no body; guard against empty-body JSON parse failure
        let detail = "Failed to revoke API key";
        try {
          const error = await res.json();
          detail = error.detail || detail;
        } catch {
          // Response body empty or not JSON — use default message
        }
        throw new Error(detail);
      }
      // Success (200, 204, etc.) — do not call res.json() since 204 has no body
    },
    onSuccess: () => {
      toast.success("API key revoked");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to revoke API key");
    },
    onSettled: () => {
      // Invalidate cache on both success and error — server may have processed
      // the revocation even if the client-side handling encountered an issue
      queryClient.invalidateQueries({
        queryKey: ["admin", "users", userId, "api-keys"],
      });
    },
  });
}
