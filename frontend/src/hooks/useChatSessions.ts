import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ChatSessionList, ChatSessionDetail } from "@/types/session";

/**
 * TanStack Query hook for fetching the user's session list.
 * Fetches from GET /sessions?limit=50&offset=0, sorted by updated_at desc (backend default).
 */
export function useChatSessions() {
  return useQuery({
    queryKey: ["sessions"],
    queryFn: async (): Promise<ChatSessionList> => {
      const response = await apiClient.get("/sessions/?limit=50&offset=0");
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to fetch sessions: ${response.status} ${errorText}`
        );
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * TanStack Query hook for fetching a single session with file details.
 * Fetches from GET /sessions/{sessionId}.
 * Disabled when sessionId is null.
 */
export function useSessionDetail(sessionId: string | null) {
  return useQuery({
    queryKey: ["sessions", sessionId],
    queryFn: async (): Promise<ChatSessionDetail> => {
      const response = await apiClient.get(`/sessions/${sessionId}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to fetch session: ${response.status} ${errorText}`
        );
      }
      return response.json();
    },
    enabled: !!sessionId,
  });
}
