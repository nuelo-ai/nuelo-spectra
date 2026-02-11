"use client";

import { ChevronRight, Files } from "lucide-react";
import { useSessionStore } from "@/stores/sessionStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { FileCard } from "./FileCard";
import type { FileBasicInfo } from "@/types/session";

interface LinkedFilesPanelProps {
  sessionId: string;
  files: FileBasicInfo[];
}

/**
 * Collapsible right sidebar panel showing files linked to the current session.
 * Default state is closed. Toggle via useSessionStore().rightPanelOpen.
 * Renders FileCard components in a scrollable list.
 */
export function LinkedFilesPanel({ sessionId, files }: LinkedFilesPanelProps) {
  const rightPanelOpen = useSessionStore((s) => s.rightPanelOpen);
  const setRightPanelOpen = useSessionStore((s) => s.setRightPanelOpen);

  return (
    <div
      className={`shrink-0 border-l border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 transition-all duration-300 ease-in-out overflow-hidden ${
        rightPanelOpen ? "w-80" : "w-0 border-l-0"
      }`}
    >
      <div className="flex h-full w-80 flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <Files className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">
              Linked Files{" "}
              <span className="text-muted-foreground font-normal">
                ({files.length})
              </span>
            </h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setRightPanelOpen(false)}
            title="Close panel"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* File list */}
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-2">
            {files.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <div className="h-10 w-10 rounded-full bg-muted/60 flex items-center justify-center mb-3">
                  <Files className="h-5 w-5 text-muted-foreground/60" />
                </div>
                <p className="text-sm text-muted-foreground font-medium">
                  No files linked yet
                </p>
                <p className="text-xs text-muted-foreground/60 mt-1">
                  Add files to this session to start analyzing your data
                </p>
              </div>
            ) : (
              files.map((file) => (
                <FileCard
                  key={file.id}
                  file={file}
                  sessionId={sessionId}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
