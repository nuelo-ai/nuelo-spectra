"use client";

import { useState, useRef } from "react";
import {
  Paperclip,
  Upload,
  FileSpreadsheet,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useFiles, useRecentFiles } from "@/hooks/useFileManager";
import { useLinkFile } from "@/hooks/useSessionMutations";
import { useSessionStore } from "@/stores/sessionStore";
import { FileSelectionModal } from "./FileSelectionModal";
import { FileUploadZone } from "./FileUploadZone";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { FileListItem } from "@/types/file";

interface FileLinkingDropdownProps {
  sessionId: string;
  linkedFileIds: string[]; // Currently linked file IDs for the session
}

/**
 * Paperclip dropdown for adding files to a chat session.
 * Three sections: Upload File, Link Existing File, and Recent files.
 */
export function FileLinkingDropdown({
  sessionId,
  linkedFileIds,
}: FileLinkingDropdownProps) {
  const queryClient = useQueryClient();
  const { data: files } = useFiles();
  const { data: recentFiles } = useRecentFiles(5);
  const { mutate: linkFile } = useLinkFile();
  const setRightPanelOpen = useSessionStore((s) => s.setRightPanelOpen);

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectionModalOpen, setSelectionModalOpen] = useState(false);

  // Track file IDs before upload to detect newly uploaded files
  const prevFileIdsRef = useRef<Set<string>>(new Set());

  const linkedSet = new Set(linkedFileIds);

  const handleOpenUploadDialog = () => {
    prevFileIdsRef.current = new Set(files?.map((f) => f.id) || []);
    setUploadDialogOpen(true);
  };

  const handleUploadComplete = async () => {
    setUploadDialogOpen(false);
    // Wait for files query to refresh
    await queryClient.invalidateQueries({ queryKey: ["files"] });
    // Small delay to let the invalidation settle
    await queryClient.refetchQueries({ queryKey: ["files"] });
    const updatedFiles = queryClient.getQueryData<FileListItem[]>(["files"]);
    if (updatedFiles) {
      const newFiles = updatedFiles.filter(
        (f) => !prevFileIdsRef.current.has(f.id)
      );
      for (const newFile of newFiles) {
        linkFile(
          { sessionId, fileId: newFile.id },
          {
            onSuccess: () => {
              toast.success(`${newFile.original_filename} linked to session`);
              setRightPanelOpen(true);
            },
            onError: (error: Error) => toast.error(error.message),
          }
        );
      }
    }
  };

  const handleFileSelected = (fileId: string) => {
    linkFile(
      { sessionId, fileId },
      {
        onSuccess: () => {
          toast.success("File linked to session");
          setRightPanelOpen(true);
        },
        onError: (error: Error) => toast.error(error.message),
      }
    );
  };

  const handleRecentFileClick = (fileId: string, filename: string) => {
    linkFile(
      { sessionId, fileId },
      {
        onSuccess: () => {
          toast.success(`${filename} linked to session`);
          setRightPanelOpen(true);
        },
        onError: (error: Error) => toast.error(error.message),
      }
    );
  };

  // Filter recent files that aren't already linked
  const visibleRecentFiles = recentFiles ?? [];
  const hasRecentFiles = visibleRecentFiles.length > 0;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            aria-label="Add file to chat"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="top" className="w-56">
          {/* Section 1: Upload File */}
          <DropdownMenuItem onClick={handleOpenUploadDialog}>
            <Upload className="mr-2 h-4 w-4" />
            Upload File
          </DropdownMenuItem>

          {/* Section 2: Link Existing File */}
          <DropdownMenuItem onClick={() => setSelectionModalOpen(true)}>
            <FileSpreadsheet className="mr-2 h-4 w-4" />
            Link Existing File
          </DropdownMenuItem>

          {/* Section 3: Recent files */}
          {hasRecentFiles && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Recent</DropdownMenuLabel>
              {visibleRecentFiles.map((file) => {
                const isLinked = linkedSet.has(file.id);
                const displayName =
                  file.original_filename.length > 30
                    ? file.original_filename.slice(0, 27) + "..."
                    : file.original_filename;

                return (
                  <DropdownMenuItem
                    key={file.id}
                    disabled={isLinked}
                    onClick={() =>
                      !isLinked &&
                      handleRecentFileClick(file.id, file.original_filename)
                    }
                  >
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    <span className="truncate">
                      {displayName}
                      {isLinked && (
                        <span className="text-muted-foreground ml-1">
                          (linked)
                        </span>
                      )}
                    </span>
                  </DropdownMenuItem>
                );
              })}
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Upload dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
          </DialogHeader>
          <FileUploadZone onUploadComplete={handleUploadComplete} />
        </DialogContent>
      </Dialog>

      {/* File selection modal */}
      <FileSelectionModal
        open={selectionModalOpen}
        onOpenChange={setSelectionModalOpen}
        onFileSelected={handleFileSelected}
        linkedFileIds={linkedFileIds}
      />
    </>
  );
}
