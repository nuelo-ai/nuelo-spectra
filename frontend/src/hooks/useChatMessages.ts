import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ChatMessageList, ChatMessageResponse } from "@/types/chat";

/**
 * TanStack Query hook for fetching chat message history for a session.
 */
export function useChatMessages(sessionId: string | null) {
  return useQuery({
    queryKey: ["session", "messages", sessionId],
    queryFn: async (): Promise<ChatMessageList> => {
      if (!sessionId) {
        throw new Error("Session ID is required");
      }

      const response = await apiClient.get(`/sessions/${sessionId}/messages`);
      if (!response.ok) {
        throw new Error("Failed to fetch chat messages");
      }

      return response.json();
    },
    enabled: !!sessionId,
    refetchOnWindowFocus: true,
  });
}

/**
 * Helper hook to optimistically add a user message to the chat.
 * Called immediately when user sends a message for instant feedback.
 */
export function useAddLocalMessage() {
  const queryClient = useQueryClient();

  return (sessionId: string, message: string) => {
    const optimisticMessage: ChatMessageResponse = {
      id: `temp-${Date.now()}`,
      file_id: null,
      role: "user",
      content: message,
      message_type: null,
      metadata_json: null,
      created_at: new Date().toISOString(),
    };

    queryClient.setQueryData<ChatMessageList>(
      ["session", "messages", sessionId],
      (old) => {
        if (!old) {
          return {
            messages: [optimisticMessage],
            total: 1,
          };
        }

        return {
          messages: [...old.messages, optimisticMessage],
          total: old.total + 1,
        };
      }
    );
  };
}

/**
 * Helper hook to refetch chat messages after stream completes.
 * Forces immediate refetch from server to get persisted messages.
 */
export function useInvalidateChatMessages() {
  const queryClient = useQueryClient();

  return async (sessionId: string) => {
    await queryClient.refetchQueries({
      queryKey: ["session", "messages", sessionId],
      exact: true,
    });
  };
}
