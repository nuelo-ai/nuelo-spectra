import { create } from "zustand";

interface WorkspaceState {
  /** Currently selected signal ID in detection results */
  selectedSignalId: string | null;
  setSelectedSignalId: (id: string | null) => void;

  /** Selected file IDs for pulse detection */
  selectedFileIds: string[];
  toggleFileSelection: (id: string) => void;
  clearFileSelection: () => void;

  /** Pulse detection status */
  detectionStatus: "idle" | "running" | "complete" | "failed";
  setDetectionStatus: (
    status: "idle" | "running" | "complete" | "failed"
  ) => void;

  /** Active pulse run ID for polling */
  pulseRunId: string | null;
  setPulseRunId: (id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
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

  detectionStatus: "idle",
  setDetectionStatus: (status) => set({ detectionStatus: status }),

  pulseRunId: null,
  setPulseRunId: (id) => set({ pulseRunId: id }),
}));
