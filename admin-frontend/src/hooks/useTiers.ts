"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";

export interface TierInfo {
  name: string;
  display_name: string;
  credits: number;
  reset_policy: string;
  user_count: number;
}

export function useTiers() {
  return useQuery<TierInfo[]>({
    queryKey: ["admin", "tiers"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/tiers");
      if (!res.ok) throw new Error("Failed to fetch tiers");
      return res.json();
    },
  });
}
