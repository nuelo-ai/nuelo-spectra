"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface SubscriptionStatus {
  has_subscription: boolean;
  plan_tier: string | null;
  status: string | null;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
}

export function useSubscription() {
  return useQuery<SubscriptionStatus>({
    queryKey: ["subscription", "status"],
    queryFn: async () => {
      const res = await apiClient.get("/subscriptions/status");
      if (!res.ok) throw new Error("Failed to fetch subscription status");
      return res.json();
    },
    staleTime: 30000,
  });
}
