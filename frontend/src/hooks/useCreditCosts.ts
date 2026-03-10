"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface CreditCosts {
  chat: number;
  pulse_run: number;
}

export function useCreditCosts() {
  return useQuery<CreditCosts>({
    queryKey: ["credit-costs"],
    queryFn: async () => {
      const res = await apiClient.get("/credit-costs");
      if (!res.ok) throw new Error("Failed to fetch credit costs");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}
