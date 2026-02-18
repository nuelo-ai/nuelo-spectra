"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type { DashboardMetrics } from "@/types/dashboard";

/**
 * Fetch dashboard metrics from the admin API.
 * Auto-refreshes every 60 seconds with 30-second stale time.
 */
export function useDashboardMetrics(days: number = 30) {
  return useQuery<DashboardMetrics>({
    queryKey: ["admin", "dashboard", days],
    queryFn: async () => {
      const response = await adminApiClient.get(
        `/api/admin/dashboard?days=${days}`
      );
      if (!response.ok) {
        throw new Error(`Dashboard fetch failed: ${response.status}`);
      }
      return response.json();
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}
