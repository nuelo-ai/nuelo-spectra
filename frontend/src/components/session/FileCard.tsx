"use client";

import { useState } from "react";
import { FileSpreadsheet, FileText, Info, X } from "lucide-react";
import { useUnlinkFile } from "@/hooks/useSessionMutations";
import { FileInfoModal } from "@/components/file/FileInfoModal";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import type { FileBasicInfo } from "@/types/session";

interface FileCardProps {
  file: FileBasicInfo;
  sessionId: string;
}

/**
 * Individual file card displayed in the LinkedFilesPanel.
 * Shows file name, type icon, (i) info button to open FileInfoModal,
 * and remove button with confirmation dialog to unlink file from session.
 */
export function FileCard({ file, sessionId }: FileCardProps) {
  const [showInfoModal, setShowInfoModal] = useState(false);
  const unlinkFile = useUnlinkFile();

  const isSpreadsheet = ["csv", "xlsx", "xls"].some(
    (ext) =>
      file.file_type?.toLowerCase().includes(ext) ||
      file.original_filename?.toLowerCase().endsWith(`.${ext}`)
  );

  const FileIcon = isSpreadsheet ? FileSpreadsheet : FileText;

  const handleUnlink = () => {
    unlinkFile.mutate({ sessionId, fileId: file.id });
  };

  // Truncate long filenames
  const displayName =
    file.original_filename.length > 28
      ? file.original_filename.slice(0, 25) + "..."
      : file.original_filename;

  return (
    <>
      <div className="group flex items-start gap-3 rounded-lg border border-border/60 bg-card p-3 transition-colors hover:border-border hover:bg-accent/30">
        {/* File type icon */}
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted/60">
          <FileIcon className="h-4.5 w-4.5 text-muted-foreground" />
        </div>

        {/* File info */}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium leading-tight truncate" title={file.original_filename}>
            {displayName}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {file.file_type?.toUpperCase() || "File"}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Info button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setShowInfoModal(true)}
            title="File information"
          >
            <Info className="h-3.5 w-3.5" />
          </Button>

          {/* Remove button with confirmation */}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 hover:text-destructive"
                title="Remove from session"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>
                  Remove {file.original_filename} from this chat?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  This will unlink the file from this session. The file itself
                  will not be deleted.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleUnlink}
                  variant="destructive"
                >
                  Remove
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* File info modal */}
      {showInfoModal && (
        <FileInfoModal
          fileId={file.id}
          onClose={() => setShowInfoModal(false)}
        />
      )}
    </>
  );
}
