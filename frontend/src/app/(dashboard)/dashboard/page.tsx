"use client";

import { useAuth } from "@/hooks/useAuth";
import { useTabStore } from "@/stores/tabStore";
import { Button } from "@/components/ui/button";
import { X, Upload, FileSpreadsheet } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

/**
 * Dashboard page - shows tab bar and content area for file chats.
 * Empty state when no tabs are open.
 */
export default function DashboardPage() {
  const { user, logout } = useAuth();
  const { tabs, currentTabId, switchTab, closeTab } = useTabStore();

  const currentTab = tabs.find((tab) => tab.fileId === currentTabId);

  return (
    <div className="flex flex-col h-full">
      {/* Header with user info and logout */}
      <div className="border-b px-6 py-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Spectra</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">{user?.email}</span>
          <Button onClick={logout} variant="outline" size="sm">
            Log out
          </Button>
        </div>
      </div>

      {/* Tab bar */}
      {tabs.length > 0 && (
        <div className="border-b bg-accent/30">
          <ScrollArea className="w-full">
            <div className="flex gap-1 px-4 py-2">
              {tabs.map((tab) => {
                const isActive = tab.fileId === currentTabId;
                return (
                  <div
                    key={tab.fileId}
                    role="button"
                    tabIndex={0}
                    onClick={() => switchTab(tab.fileId)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        switchTab(tab.fileId);
                      }
                    }}
                    className={`
                      group flex items-center gap-2 px-4 py-2 rounded-t-lg
                      transition-all duration-200 min-w-[180px] max-w-[220px]
                      cursor-pointer
                      ${
                        isActive
                          ? "bg-background text-foreground border-b-2 border-primary"
                          : "bg-transparent text-muted-foreground hover:bg-accent"
                      }
                    `}
                  >
                    <FileSpreadsheet className="h-4 w-4 flex-shrink-0" />
                    <span className="text-sm truncate flex-1 text-left">
                      {tab.fileName}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        closeTab(tab.fileId);
                      }}
                      className="opacity-0 group-hover:opacity-100 hover:bg-accent rounded p-0.5 transition-opacity"
                      aria-label={`Close ${tab.fileName}`}
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        {currentTab ? (
          <div className="p-6">
            <div className="max-w-4xl mx-auto">
              <div className="bg-accent/30 border border-dashed rounded-lg p-8 text-center">
                <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h2 className="text-lg font-medium mb-2">
                  Chat for {currentTab.fileName}
                </h2>
                <p className="text-sm text-muted-foreground">
                  Chat interface will be implemented in Plan 04
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full px-8">
            <div className="max-w-md text-center space-y-4">
              <div className="rounded-full p-6 bg-accent mx-auto w-fit">
                <Upload className="h-12 w-12 text-muted-foreground" />
              </div>
              <h2 className="text-2xl font-semibold">Get started</h2>
              <p className="text-muted-foreground">
                Select a file from the sidebar or upload a new one to begin analyzing your data
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
