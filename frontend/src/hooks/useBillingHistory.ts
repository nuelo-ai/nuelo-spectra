"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface BillingHistoryItem {
  id: string;
  date: string;
  payment_type: string;
  type_display: string;
  amount_cents: number;
  amount_display: string;
  credit_amount: number | null;
  status: string;
}

export interface BillingHistoryData {
  items: BillingHistoryItem[];
}

export function useBillingHistory() {
  return useQuery<BillingHistoryData>({
    queryKey: ["subscriptions", "billing-history"],
    queryFn: async () => {
      const res = await apiClient.get("/subscriptions/billing-history");
      if (!res.ok) throw new Error("Failed to fetch billing history");
      return res.json();
    },
    staleTime: 30000,
  });
}
