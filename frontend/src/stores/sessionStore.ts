import { create } from "zustand";

/**
 * Session UI state and actions
 */
interface SessionStore {
  /** Currently active session ID */
  currentSessionId: string | null;

  /** Left sidebar open/closed state */
  leftSidebarOpen: boolean;

  /** Right panel open/closed state (default closed per user decision) */
  rightPanelOpen: boolean;

  /** Set the currently active session */
  setCurrentSession: (id: string | null) => void;

  /** Toggle the left sidebar */
  toggleLeftSidebar: () => void;

  /** Toggle the right panel */
  toggleRightPanel: () => void;

  /** Explicitly set right panel open state */
  setRightPanelOpen: (open: boolean) => void;
}

/**
 * Zustand store for session-centric UI state.
 * Replaces tabStore with session-based navigation.
 */
export const useSessionStore = create<SessionStore>((set) => ({
  currentSessionId: null,
  leftSidebarOpen: true,
  rightPanelOpen: false,

  setCurrentSession: (id: string | null) => {
    set({ currentSessionId: id });
  },

  toggleLeftSidebar: () => {
    set((state) => ({ leftSidebarOpen: !state.leftSidebarOpen }));
  },

  toggleRightPanel: () => {
    set((state) => ({ rightPanelOpen: !state.rightPanelOpen }));
  },

  setRightPanelOpen: (open: boolean) => {
    set({ rightPanelOpen: open });
  },
}));
