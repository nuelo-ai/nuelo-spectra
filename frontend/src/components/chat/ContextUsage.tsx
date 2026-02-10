"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface ContextUsageData {
  current_tokens: number;
  max_tokens: number;
  percentage: number;
  message_count: number;
  is_warning: boolean;
  is_limit_exceeded: boolean;
}

interface ContextUsageProps {
  fileId: string;
  /** Trigger refetch when message count changes */
  messageCount: number;
  /** Callback when context exceeds limit and needs trimming */
  onLimitExceeded?: () => void;
}

export function ContextUsage({ fileId, messageCount, onLimitExceeded }: ContextUsageProps) {
  const { data } = useQuery<ContextUsageData>({
    queryKey: ["context-usage", fileId, messageCount],
    queryFn: async () => {
      const res = await apiClient.get(`/chat/${fileId}/context-usage`);
      if (!res.ok) return null;
      return res.json();
    },
    // Refetch when messageCount changes (after each query)
    // Also refetch periodically for background updates
    refetchInterval: 60000,  // Every 60 seconds
    enabled: !!fileId,  // Fetch whenever fileId exists (handles browser refresh with existing messages)
  });

  // Trigger callback when limit exceeded
  if (data?.is_limit_exceeded && onLimitExceeded) {
    onLimitExceeded();
  }

  if (!data || data.message_count === 0) return null;

  const isWarning = data.is_warning;
  const isExceeded = data.is_limit_exceeded;

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={
        isExceeded
          ? "text-red-600 font-semibold"
          : isWarning
            ? "text-orange-600 font-medium"
            : "text-muted-foreground"
      }>
        {data.current_tokens.toLocaleString()} / {data.max_tokens.toLocaleString()} tokens
      </span>
      {isWarning && !isExceeded && (
        <span className="text-orange-600 text-xs">
          Context limit approaching
        </span>
      )}
      {isExceeded && (
        <span className="text-red-600 text-xs">
          Context limit exceeded
        </span>
      )}
    </div>
  );
}
