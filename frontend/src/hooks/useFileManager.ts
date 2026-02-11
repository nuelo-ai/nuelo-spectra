import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import {
  FileListItem,
  FileUploadResponse,
  FileSummaryResponse,
  FileDetailResponse,
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
        const errorText = await response.text();
        console.error("GET /files/ failed:", {
          status: response.status,
          statusText: response.statusText,
          body: errorText,
          url: response.url
        });
        throw new Error(`Failed to fetch files: ${response.status} ${errorText}`);
      }
      return response.json();
    },
    refetchOnWindowFocus: true,
    // Independent fallback: sidebar discovers new files within 10s
    // even if button handler fails to trigger manual refetch
    refetchInterval: 10000,
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

/**
 * TanStack Query mutation for updating file context (FILE-06)
 */
export function useUpdateFileContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      fileId,
      context,
    }: {
      fileId: string;
      context: string;
    }): Promise<FileDetailResponse> => {
      const response = await apiClient.post(`/files/${fileId}/context`, {
        context,
      });
      if (!response.ok) {
        throw new Error("Failed to update file context");
      }
      return response.json();
    },
    onSuccess: (_data, variables) => {
      // Invalidate summary to show updated user_context
      queryClient.invalidateQueries({
        queryKey: ["files", "summary", variables.fileId],
      });
    },
  });
}

/**
 * TanStack Query mutation for downloading a file via blob URL
 */
export function useDownloadFile() {
  return useMutation({
    mutationFn: async ({
      fileId,
      filename,
    }: {
      fileId: string;
      filename: string;
    }) => {
      const response = await apiClient.get(`/files/${fileId}/download`);
      if (!response.ok) {
        throw new Error("Failed to download file");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      try {
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } finally {
        URL.revokeObjectURL(url);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to download file");
    },
  });
}

/**
 * Derives recent files from existing useFiles query (no extra API call).
 * Returns last N files sorted by created_at descending.
 */
export function useRecentFiles(limit: number = 5) {
  const { data: files, ...rest } = useFiles();
  const recentFiles = useMemo(() => {
    if (!files) return [];
    return [...files]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      .slice(0, limit);
  }, [files, limit]);
  return { data: recentFiles, ...rest };
}

/**
 * TanStack Query mutation for bulk-deleting multiple files.
 * Uses Promise.allSettled for parallel deletion with partial failure handling.
 */
export function useBulkDeleteFiles() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fileIds: string[]) => {
      const results = await Promise.allSettled(
        fileIds.map(async (fileId) => {
          const response = await apiClient.delete(`/files/${fileId}`);
          if (!response.ok) throw new Error(`Failed to delete file ${fileId}`);
        })
      );
      const failures = results.filter((r) => r.status === "rejected");
      if (failures.length > 0) {
        throw new Error(`Failed to delete ${failures.length} file(s)`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["files"] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}
