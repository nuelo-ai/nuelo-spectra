"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface PlanInfo {
  tier_key: string;
  display_name: string;
  price_cents: number;
  price_display: string;
  credit_allocation: number;
  features: string[];
  is_popular: boolean;
}

export interface PlanPricingData {
  plans: PlanInfo[];
  current_tier: string;
}

export function usePlanPricing() {
  return useQuery<PlanPricingData>({
    queryKey: ["subscriptions", "plans"],
    queryFn: async () => {
      const res = await apiClient.get("/subscriptions/plans");
      if (!res.ok) throw new Error("Failed to fetch plan pricing");
      return res.json();
    },
    staleTime: 60000,
  });
}
