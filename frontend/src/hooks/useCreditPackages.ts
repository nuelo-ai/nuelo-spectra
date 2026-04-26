"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface CreditPackage {
  id: string;
  name: string;
  credit_amount: number;
  price_cents: number;
  price_display: string;
}

export function useCreditPackages() {
  return useQuery<CreditPackage[]>({
    queryKey: ["credits", "packages"],
    queryFn: async () => {
      const res = await apiClient.get("/credits/packages");
      if (!res.ok) throw new Error("Failed to fetch credit packages");
      return res.json();
    },
    staleTime: 60000,
  });
}
