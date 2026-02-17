"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type { PlatformSettings, PlatformSettingsUpdate } from "@/types/settings";

/**
 * Fetch platform settings from /api/admin/settings.
 */
export function usePlatformSettings() {
  return useQuery<PlatformSettings>({
    queryKey: ["admin", "settings"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/settings");
      if (!res.ok) throw new Error("Failed to fetch platform settings");
      return res.json();
    },
  });
}

/**
 * Update platform settings via PATCH /api/admin/settings.
 */
export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation<PlatformSettings, Error, PlatformSettingsUpdate>({
    mutationFn: async (payload) => {
      const res = await adminApiClient.patch("/api/admin/settings", payload);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail =
          typeof body.detail === "string"
            ? body.detail
            : "Failed to update settings";
        throw new Error(detail);
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "settings"] });
    },
  });
}
