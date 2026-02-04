"use client";

import { useState } from "react";
import { FileSpreadsheet, Info, Trash2, Upload } from "lucide-react";
import { useFiles, useDeleteFile } from "@/hooks/useFileManager";
import { useTabStore } from "@/stores/tabStore";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { FileUploadZone } from "./FileUploadZone";
import { FileInfoModal } from "./FileInfoModal";

/**
 * File sidebar component displaying user's uploaded files
 * with actions to open tabs, view info, and delete files
 */
export function FileSidebar() {
  const { data: files, isLoading } = useFiles();
  const { mutate: deleteFile } = useDeleteFile();
  const { tabs, currentTabId, openTab, closeTabForDeletedFile } = useTabStore();

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<{ id: string; name: string } | null>(null);
  const [infoModalFileId, setInfoModalFileId] = useState<string | null>(null);

  const handleFileClick = (fileId: string, fileName: string) => {
    const opened = openTab(fileId, fileName);
    if (!opened) {
      toast.error("Maximum 5 tabs. Close a tab first.");
    }
  };

  const handleDeleteClick = (fileId: string, fileName: string) => {
    setFileToDelete({ id: fileId, name: fileName });
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (!fileToDelete) return;

    deleteFile(fileToDelete.id, {
      onSuccess: () => {
        closeTabForDeletedFile(fileToDelete.id);
        toast.success(`"${fileToDelete.name}" deleted`);
        setDeleteDialogOpen(false);
        setFileToDelete(null);
      },
      onError: (error) => {
        toast.error(error instanceof Error ? error.message : "Failed to delete file");
      },
    });
  };

  const truncateFilename = (filename: string, maxLength: number = 20) => {
    if (filename.length <= maxLength) return filename;
    return filename.substring(0, maxLength - 3) + "...";
  };

  return (
    <>
      <div className="w-[260px] border-r bg-background flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b">
          <h2 className="font-semibold text-lg">Files</h2>
        </div>

        {/* File list */}
        <ScrollArea className="flex-1 px-2 py-2">
          {isLoading ? (
            <div className="space-y-2 p-2">
              {/* Skeleton loader for files */}
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-12 rounded-lg" />
              ))}
            </div>
          ) : files && files.length > 0 ? (
            <div className="space-y-1">
              {files.map((file, index) => {
                const isActive = currentTabId === file.id;
                return (
                  <div
                    key={file.id}
                    style={{
                      animation: "var(--animate-slideRight)",
                      animationDelay: `${index * 50}ms`,
                    }}
                    className={`
                      group rounded-lg p-2 transition-all duration-200 ease-in-out
                      ${isActive ? "bg-accent text-accent-foreground border-l-2 border-l-primary" : "hover:bg-accent/50"}
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4 flex-shrink-0 text-primary" />
                      <button
                        onClick={() => handleFileClick(file.id, file.original_filename)}
                        className="flex-1 text-left text-sm truncate"
                        title={file.original_filename}
                      >
                        {truncateFilename(file.original_filename)}
                      </button>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 ease-in-out">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => setInfoModalFileId(file.id)}
                              >
                                <Info className="h-3.5 w-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>View analysis</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 hover:bg-destructive hover:text-destructive-foreground"
                                onClick={() => handleDeleteClick(file.id, file.original_filename)}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Delete file</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center opacity-60">
              <FileSpreadsheet className="h-12 w-12 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground font-medium">No files yet</p>
              <p className="text-xs text-muted-foreground mt-1">Upload your first file to get started</p>
            </div>
          )}
        </ScrollArea>

        {/* Upload button */}
        <div className="p-4 border-t">
          <Button
            onClick={() => setUploadDialogOpen(true)}
            className="w-full"
            variant="default"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload File
          </Button>
        </div>
      </div>

      {/* Upload dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
          </DialogHeader>
          <FileUploadZone onUploadComplete={() => setUploadDialogOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete "{fileToDelete?.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all chat history for this file. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setFileToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* File info modal */}
      {infoModalFileId && (
        <FileInfoModal
          fileId={infoModalFileId}
          onClose={() => setInfoModalFileId(null)}
        />
      )}
    </>
  );
}
