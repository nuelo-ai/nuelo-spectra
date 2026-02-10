import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { SearchConfig } from "@/types/chat";

/**
 * Hook for managing the web search toggle state.
 *
 * On mount, fetches search configuration from the backend to determine
 * if search is configured and quota status. Exposes toggle controls
 * and quota-aware state for the ChatInput component.
 */
export function useSearchToggle() {
  const [enabled, setEnabled] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [isQuotaExceeded, setIsQuotaExceeded] = useState(false);

  const checkConfig = useCallback(async () => {
    try {
      const res = await apiClient.get("/search/config");
      if (res.ok) {
        const data: SearchConfig = await res.json();
        setIsConfigured(data.configured);
        setIsQuotaExceeded(data.quota_exceeded);
        // Auto-disable if quota exceeded
        if (data.quota_exceeded) {
          setEnabled(false);
        }
      }
    } catch (e) {
      // Silently fail -- search toggle stays in unconfigured state
      console.warn("Failed to fetch search config:", e);
    }
  }, []);

  // Fetch config on mount
  useEffect(() => {
    checkConfig();
  }, [checkConfig]);

  const toggle = useCallback(() => {
    if (isQuotaExceeded) return;
    setEnabled((prev) => !prev);
  }, [isQuotaExceeded]);

  const resetToggle = useCallback(() => {
    setEnabled(false);
  }, []);

  return {
    enabled,
    toggle,
    isConfigured,
    isQuotaExceeded,
    resetToggle,
    checkConfig,
  };
}
