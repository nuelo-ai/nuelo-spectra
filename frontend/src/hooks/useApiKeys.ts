/**
 * API key management hooks using TanStack Query.
 * Provides hooks for listing, creating, and revoking API keys.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

export interface ApiKeyListItem {
  id: string;
  name: string;
  description: string | null;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  total_credits_used: number;
  created_by_admin_id: string | null;
}

export interface ApiKeyCreateResponse {
  id: string;
  name: string;
  key_prefix: string;
  full_key: string; // Only present on create response
  created_at: string;
}

export interface ApiKeyCreateRequest {
  name: string;
  description?: string;
}

/**
 * Hook for listing all API keys for the current user.
 */
export function useApiKeys() {
  return useQuery<ApiKeyListItem[]>({
    queryKey: ["api-keys"],
    queryFn: async () => {
      const response = await apiClient.get("/v1/keys");

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch API keys");
      }

      return await response.json();
    },
  });
}

/**
 * Hook for creating a new API key.
 * On success: invalidates key list and shows success toast.
 */
export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation<ApiKeyCreateResponse, Error, ApiKeyCreateRequest>({
    mutationFn: async (data) => {
      const response = await apiClient.post("/v1/keys", data);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create API key");
      }

      return await response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key created successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create API key");
    },
  });
}

/**
 * Hook for revoking an API key by ID.
 * On success: invalidates key list and shows success toast.
 */
export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (keyId) => {
      const response = await apiClient.delete(`/v1/keys/${keyId}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to revoke API key");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key revoked");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to revoke API key");
    },
  });
}
