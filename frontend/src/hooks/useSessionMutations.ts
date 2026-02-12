import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  ChatSessionResponse,
  ChatSessionDetail,
  ChatSessionList,
} from "@/types/session";

/**
 * Mutation for creating a new chat session.
 * POST /sessions with { title }.
 * Invalidates session list on success.
 */
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      title: string = "New Chat"
    ): Promise<ChatSessionResponse> => {
      const response = await apiClient.post("/sessions/", { title });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create session");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}

/**
 * Mutation for updating a chat session title.
 * PATCH /sessions/{sessionId} with { title }.
 * Uses optimistic update: updates cache immediately, rolls back on error.
 */
export function useUpdateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      title,
    }: {
      sessionId: string;
      title: string;
    }): Promise<ChatSessionResponse> => {
      const response = await apiClient.patch(`/sessions/${sessionId}`, {
        title,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update session");
      }
      return response.json();
    },
    onMutate: async ({ sessionId, title }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["sessions"] });

      // Snapshot previous value
      const previousSessions = queryClient.getQueryData<ChatSessionList>([
        "sessions",
      ]);

      // Optimistically update the cache
      if (previousSessions) {
        queryClient.setQueryData<ChatSessionList>(["sessions"], {
          ...previousSessions,
          sessions: previousSessions.sessions.map((s) =>
            s.id === sessionId ? { ...s, title } : s
          ),
        });
      }

      return { previousSessions };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousSessions) {
        queryClient.setQueryData(["sessions"], context.previousSessions);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}

/**
 * Mutation for deleting a chat session.
 * DELETE /sessions/{sessionId}.
 * Invalidates session list on success.
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string): Promise<void> => {
      const response = await apiClient.delete(`/sessions/${sessionId}`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete session");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}

/**
 * Mutation for linking a file to a session.
 * POST /sessions/{sessionId}/files with { file_id }.
 * Invalidates both session list and session detail caches.
 */
export function useLinkFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      fileId,
    }: {
      sessionId: string;
      fileId: string;
    }): Promise<ChatSessionDetail> => {
      const response = await apiClient.post(`/sessions/${sessionId}/files`, {
        file_id: fileId,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to link file to session");
      }
      return response.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({
        queryKey: ["sessions", variables.sessionId],
      });
    },
  });
}

/**
 * Mutation for unlinking a file from a session.
 * DELETE /sessions/{sessionId}/files/{fileId}.
 * Invalidates both session list and session detail caches.
 */
export function useUnlinkFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      fileId,
    }: {
      sessionId: string;
      fileId: string;
    }): Promise<ChatSessionDetail> => {
      const response = await apiClient.delete(
        `/sessions/${sessionId}/files/${fileId}`
      );
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to unlink file from session");
      }
      return response.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({
        queryKey: ["sessions", variables.sessionId],
      });
    },
  });
}

/**
 * Mutation for generating a session title via LLM.
 * POST /sessions/{sessionId}/generate-title (no body -- backend reads from DB).
 * Invalidates session list and detail caches on success.
 * Fails silently -- caller doesn't need to handle errors.
 *
 * Security: No user content sent in request. Backend reads the first
 * user message directly from the database to prevent LLM proxy abuse.
 */
export function useGenerateTitle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
    }: {
      sessionId: string;
    }): Promise<ChatSessionResponse> => {
      const response = await apiClient.post(
        `/sessions/${sessionId}/generate-title`,
        {}
      );
      if (!response.ok) {
        throw new Error("Failed to generate title");
      }
      return response.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({
        queryKey: ["sessions", variables.sessionId],
      });
    },
    // Fail silently -- title generation is non-critical
    onError: () => {},
  });
}
