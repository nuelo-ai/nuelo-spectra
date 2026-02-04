/**
 * Settings hooks for profile update and password change.
 * Uses TanStack Query for mutations with optimistic updates and toast notifications.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import type {
  ProfileUpdateRequest,
  ChangePasswordRequest,
  UserResponse,
} from "@/types/auth";

/**
 * Hook for updating user profile (first_name, last_name).
 * On success: invalidates user query and shows success toast.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ProfileUpdateRequest) => {
      const response = await apiClient.patch("/auth/me", data);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update profile");
      }

      return (await response.json()) as UserResponse;
    },
    onSuccess: (updatedUser) => {
      // Invalidate user query to refetch latest data
      queryClient.invalidateQueries({ queryKey: ["user"] });
      toast.success("Profile updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update profile");
    },
  });
}

/**
 * Hook for changing user password.
 * Requires current password verification.
 * On success: shows success toast.
 * On 401: shows "Current password is incorrect" error.
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: ChangePasswordRequest) => {
      const response = await apiClient.post("/auth/change-password", data);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Current password is incorrect");
        }
        const error = await response.json();
        throw new Error(error.detail || "Failed to change password");
      }

      return await response.json();
    },
    onSuccess: () => {
      toast.success("Password changed successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to change password");
    },
  });
}
