import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  FileListItem,
  FileUploadResponse,
  FileSummaryResponse,
} from "@/types/file";

/**
 * TanStack Query hook for fetching user's file list
 */
export function useFiles() {
  return useQuery({
    queryKey: ["files"],
    queryFn: async (): Promise<FileListItem[]> => {
      const response = await apiClient.get("/files/");
      if (!response.ok) {
        throw new Error("Failed to fetch files");
      }
      return response.json();
    },
    refetchOnWindowFocus: true,
  });
}

/**
 * TanStack Query mutation for uploading files
 */
export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      userContext,
    }: {
      file: File;
      userContext?: string;
    }): Promise<FileUploadResponse> => {
      const formData = new FormData();
      formData.append("file", file);
      if (userContext) {
        formData.append("user_context", userContext);
      }

      const response = await apiClient.upload("/files/upload", formData);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upload file");
      }
      return response.json();
    },
    onSuccess: () => {
      // Sidebar update handled by Continue to Chat button's explicit refetch
      // Do NOT refetch here -- premature refetch conflicts with button's awaited refetch
    },
  });
}

/**
 * TanStack Query mutation for deleting files
 */
export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fileId: string): Promise<void> => {
      const response = await apiClient.delete(`/files/${fileId}`);
      if (!response.ok) {
        throw new Error("Failed to delete file");
      }
    },
    onSuccess: () => {
      // Invalidate files list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ["files"] });
    },
  });
}

/**
 * TanStack Query hook for fetching file summary (polls until data_summary available)
 */
export function useFileSummary(fileId: string | null) {
  return useQuery({
    queryKey: ["files", "summary", fileId],
    queryFn: async (): Promise<FileSummaryResponse> => {
      if (!fileId) {
        throw new Error("File ID is required");
      }

      const response = await apiClient.get(`/files/${fileId}/summary`);
      if (!response.ok) {
        throw new Error("Failed to fetch file summary");
      }
      return response.json();
    },
    enabled: !!fileId,
    // Poll every 3 seconds until data_summary is available
    refetchInterval: (query) => {
      const data = query.state.data as FileSummaryResponse | undefined;
      return data?.data_summary ? false : 3000;
    },
  });
}
