import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  CollectionListItem,
  CollectionDetail,
  CollectionFile,
  SignalDetail,
  ReportListItem,
  PulseRunDetail,
  PulseRunTrigger,
  PulseRunCreate,
} from "@/types/workspace";

// --- Query hooks ---

export function useCollections() {
  return useQuery<CollectionListItem[]>({
    queryKey: ["collections"],
    queryFn: async () => {
      const response = await apiClient.get("/collections");
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    refetchOnMount: "always",
  });
}

export function useCollectionDetail(id: string) {
  return useQuery<CollectionDetail>({
    queryKey: ["collections", id],
    queryFn: async () => {
      const response = await apiClient.get(`/collections/${id}`);
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!id,
  });
}

export function useCollectionFiles(collectionId: string) {
  return useQuery<CollectionFile[]>({
    queryKey: ["collections", collectionId, "files"],
    queryFn: async () => {
      const response = await apiClient.get(
        `/collections/${collectionId}/files`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!collectionId,
  });
}

export function useCollectionSignals(collectionId: string) {
  return useQuery<SignalDetail[]>({
    queryKey: ["collections", collectionId, "signals"],
    queryFn: async () => {
      const response = await apiClient.get(
        `/collections/${collectionId}/signals`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!collectionId,
  });
}

export function useCollectionReports(collectionId: string) {
  return useQuery<ReportListItem[]>({
    queryKey: ["collections", collectionId, "reports"],
    queryFn: async () => {
      const response = await apiClient.get(
        `/collections/${collectionId}/reports`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!collectionId,
  });
}

export function usePulseStatus(
  collectionId: string,
  pulseRunId: string | null
) {
  return useQuery<PulseRunDetail>({
    queryKey: ["collections", collectionId, "pulse", pulseRunId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/collections/${collectionId}/pulse-runs/${pulseRunId}`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!pulseRunId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 3000;
    },
  });
}

// --- Mutation hooks ---

export function useTriggerPulse(collectionId: string) {
  const queryClient = useQueryClient();
  return useMutation<PulseRunTrigger, Error, PulseRunCreate>({
    mutationFn: async (body) => {
      const response = await apiClient.post(
        `/collections/${collectionId}/pulse`,
        body
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId],
      });
    },
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();
  return useMutation<CollectionDetail, Error, { name: string; description?: string }>({
    mutationFn: async (body) => {
      const response = await apiClient.post("/collections", body);
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useUploadFile(collectionId: string) {
  const queryClient = useQueryClient();
  return useMutation<CollectionFile, Error, FormData>({
    mutationFn: async (formData) => {
      const response = await apiClient.upload(
        `/collections/${collectionId}/files`,
        formData
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId, "files"],
      });
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId],
      });
    },
  });
}

export function useLinkFilesToCollection(collectionId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (fileIds) => {
      const results = await Promise.allSettled(
        fileIds.map(async (fileId) => {
          const response = await apiClient.post(
            `/collections/${collectionId}/files/link`,
            { file_id: fileId }
          );
          if (!response.ok) {
            // 409 = already linked, treat as success
            if (response.status === 409) return;
            throw new Error(`Failed: ${response.status}`);
          }
        })
      );
      const failures = results.filter((r) => r.status === "rejected");
      if (failures.length > 0) {
        throw new Error(`Failed to link ${failures.length} file(s)`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId, "files"],
      });
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId],
      });
    },
  });
}

export function useRemoveFile(collectionId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (fileId) => {
      const response = await apiClient.delete(
        `/collections/${collectionId}/files/${fileId}`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId, "files"],
      });
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId],
      });
    },
  });
}
