import { create } from "zustand";

type DetectionStatus = "idle" | "running" | "complete" | "failed";

interface CollectionDetectionState {
  detectionStatus: DetectionStatus;
  pulseRunId: string | null;
}

interface WorkspaceState {
  /** Currently selected signal ID in detection results */
  selectedSignalId: string | null;
  setSelectedSignalId: (id: string | null) => void;

  /** Selected file IDs for pulse detection */
  selectedFileIds: string[];
  toggleFileSelection: (id: string) => void;
  clearFileSelection: () => void;

  /** Per-collection pulse detection state */
  collectionDetection: Record<string, CollectionDetectionState>;
  getDetectionStatus: (collectionId: string) => DetectionStatus;
  setDetectionStatus: (collectionId: string, status: DetectionStatus) => void;
  getPulseRunId: (collectionId: string) => string | null;
  setPulseRunId: (collectionId: string, id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  selectedSignalId: null,
  setSelectedSignalId: (id) => set({ selectedSignalId: id }),

  selectedFileIds: [],
  toggleFileSelection: (id) =>
    set((s) => ({
      selectedFileIds: s.selectedFileIds.includes(id)
        ? s.selectedFileIds.filter((f) => f !== id)
        : [...s.selectedFileIds, id],
    })),
  clearFileSelection: () => set({ selectedFileIds: [] }),

  collectionDetection: {},
  getDetectionStatus: (collectionId) =>
    get().collectionDetection[collectionId]?.detectionStatus ?? "idle",
  setDetectionStatus: (collectionId, status) =>
    set((s) => ({
      collectionDetection: {
        ...s.collectionDetection,
        [collectionId]: {
          ...s.collectionDetection[collectionId],
          detectionStatus: status,
          pulseRunId: s.collectionDetection[collectionId]?.pulseRunId ?? null,
        },
      },
    })),
  getPulseRunId: (collectionId) =>
    get().collectionDetection[collectionId]?.pulseRunId ?? null,
  setPulseRunId: (collectionId, id) =>
    set((s) => ({
      collectionDetection: {
        ...s.collectionDetection,
        [collectionId]: {
          ...s.collectionDetection[collectionId],
          detectionStatus:
            s.collectionDetection[collectionId]?.detectionStatus ?? "idle",
          pulseRunId: id,
        },
      },
    })),
}));
