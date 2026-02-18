"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type { CreditDistribution } from "@/types/credit";

/**
 * Fetch credit distribution by tier from /api/admin/credits/distribution.
 */
export function useCreditDistribution() {
  return useQuery<CreditDistribution[]>({
    queryKey: ["admin", "credits", "distribution"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/credits/distribution");
      if (!res.ok) throw new Error("Failed to fetch credit distribution");
      return res.json();
    },
  });
}

/**
 * Fetch low-balance users from /api/admin/credits/low-balance.
 */
export function useLowBalanceUsers(thresholdPct: number = 0.1) {
  return useQuery<
    Array<{
      user_id: string;
      email: string;
      user_class: string;
      balance: number;
      tier_allocation: number;
    }>
  >({
    queryKey: ["admin", "credits", "low-balance", thresholdPct],
    queryFn: async () => {
      const res = await adminApiClient.get(
        `/api/admin/credits/low-balance?threshold_pct=${thresholdPct}`
      );
      if (!res.ok) throw new Error("Failed to fetch low balance users");
      return res.json();
    },
  });
}
