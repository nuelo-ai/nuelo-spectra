import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ChatMessageList, ChatMessageResponse } from "@/types/chat";

/**
 * TanStack Query hook for fetching chat message history for a file.
 */
export function useChatMessages(fileId: string | null) {
  return useQuery({
    queryKey: ["chat", "messages", fileId],
    queryFn: async (): Promise<ChatMessageList> => {
      if (!fileId) {
        throw new Error("File ID is required");
      }

      const response = await apiClient.get(`/chat/${fileId}/messages`);
      if (!response.ok) {
        throw new Error("Failed to fetch chat messages");
      }

      return response.json();
    },
    enabled: !!fileId,
    refetchOnWindowFocus: true,
  });
}

/**
 * Helper hook to optimistically add a user message to the chat.
 * Called immediately when user sends a message for instant feedback.
 */
export function useAddLocalMessage() {
  const queryClient = useQueryClient();

  return (fileId: string, message: string) => {
    const optimisticMessage: ChatMessageResponse = {
      id: `temp-${Date.now()}`,
      file_id: fileId,
      role: "user",
      content: message,
      message_type: null,
      metadata_json: null,
      created_at: new Date().toISOString(),
    };

    queryClient.setQueryData<ChatMessageList>(
      ["chat", "messages", fileId],
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
 * Helper hook to invalidate chat messages after stream completes.
 * Forces refetch from server to get persisted messages.
 */
export function useInvalidateChatMessages() {
  const queryClient = useQueryClient();

  return (fileId: string) => {
    queryClient.invalidateQueries({
      queryKey: ["chat", "messages", fileId],
    });
  };
}
