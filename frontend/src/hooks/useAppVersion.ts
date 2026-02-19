"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface AppVersion {
  version: string;
  environment: string;
}

export function useAppVersion() {
  return useQuery<AppVersion>({
    queryKey: ["app", "version"],
    queryFn: async () => {
      const res = await apiClient.get("/version");
      if (!res.ok) throw new Error("Failed to fetch version");
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes — version rarely changes
  });
}
