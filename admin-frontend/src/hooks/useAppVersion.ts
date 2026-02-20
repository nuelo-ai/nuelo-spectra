"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";

interface AppVersion {
  version: string;
  environment: string;
}

export function useAppVersion() {
  return useQuery<AppVersion>({
    queryKey: ["app", "version"],
    queryFn: async () => {
      // adminApiClient uses relative paths; /api/version proxied to backend /api/version
      const res = await adminApiClient.get("/api/version");
      if (!res.ok) throw new Error("Failed to fetch version");
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes — version rarely changes
  });
}
