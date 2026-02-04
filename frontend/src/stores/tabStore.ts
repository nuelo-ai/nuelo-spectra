import { create } from "zustand";

/**
 * File tab interface
 */
export interface FileTab {
  fileId: string;
  fileName: string;
}

/**
 * Tab store state and actions
 */
interface TabStore {
  tabs: FileTab[];
  currentTabId: string | null;
  maxTabs: number;

  /**
   * Open a new tab or switch to existing tab for file
   * @returns true if tab opened/switched, false if at max tabs
   */
  openTab: (fileId: string, fileName: string) => boolean;

  /**
   * Close a tab and auto-switch to next available
   */
  closeTab: (fileId: string) => void;

  /**
   * Switch to a specific tab
   */
  switchTab: (fileId: string) => void;

  /**
   * Close tab for deleted file and switch to next
   */
  closeTabForDeletedFile: (fileId: string) => void;
}

/**
 * Zustand store for managing file tabs (max 5)
 */
export const useTabStore = create<TabStore>((set) => ({
  tabs: [],
  currentTabId: null,
  maxTabs: 5,

  openTab: (fileId: string, fileName: string) => {
    let opened = false;

    set((state) => {
      // Check if tab already exists - switch to it
      const existingTab = state.tabs.find((tab) => tab.fileId === fileId);
      if (existingTab) {
        opened = true;
        return { currentTabId: fileId };
      }

      // Check if at max tabs
      if (state.tabs.length >= state.maxTabs) {
        opened = false;
        return state; // No change
      }

      // Add new tab and set as current
      opened = true;
      return {
        tabs: [...state.tabs, { fileId, fileName }],
        currentTabId: fileId,
      };
    });

    return opened;
  },

  closeTab: (fileId: string) => {
    set((state) => {
      const newTabs = state.tabs.filter((tab) => tab.fileId !== fileId);

      // If closed tab was current, switch to first remaining or null
      let newCurrentTabId = state.currentTabId;
      if (state.currentTabId === fileId) {
        newCurrentTabId = newTabs.length > 0 ? newTabs[0].fileId : null;
      }

      return {
        tabs: newTabs,
        currentTabId: newCurrentTabId,
      };
    });
  },

  switchTab: (fileId: string) => {
    set({ currentTabId: fileId });
  },

  closeTabForDeletedFile: (fileId: string) => {
    // Same logic as closeTab
    set((state) => {
      const newTabs = state.tabs.filter((tab) => tab.fileId !== fileId);

      let newCurrentTabId = state.currentTabId;
      if (state.currentTabId === fileId) {
        newCurrentTabId = newTabs.length > 0 ? newTabs[0].fileId : null;
      }

      return {
        tabs: newTabs,
        currentTabId: newCurrentTabId,
      };
    });
  },
}));
