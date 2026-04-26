"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface CreditBalance {
  balance: number;
  purchased_balance: number;
  total_balance: number;
  tier_allocation: number;
  reset_policy: string;
  next_reset_at: string | null;
  is_low: boolean;
  is_unlimited: boolean;
  display_class: string;
  monetization_enabled: boolean;
}

export function useCredits() {
  return useQuery<CreditBalance>({
    queryKey: ["credits", "balance"],
    queryFn: async () => {
      const res = await apiClient.get("/credits/balance");
      if (!res.ok) throw new Error("Failed to fetch credits");
      return res.json();
    },
    refetchInterval: 60000, // Refresh every 60 seconds
    staleTime: 30000,
  });
}

/**
 * Read the platform-level monetization toggle from the cached credit balance.
 * Returns true (default) while loading to avoid UI flicker.
 */
export function useMonetization(): boolean {
  const { data } = useCredits();
  return data?.monetization_enabled ?? true;
}
