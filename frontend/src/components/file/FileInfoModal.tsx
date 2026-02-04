"use client";

import { useFileSummary } from "@/hooks/useFileManager";
import { useFiles } from "@/hooks/useFileManager";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface FileInfoModalProps {
  fileId: string;
  onClose: () => void;
}

/**
 * Modal displaying onboarding analysis (data_summary) for a file
 */
export function FileInfoModal({ fileId, onClose }: FileInfoModalProps) {
  const { data: files } = useFiles();
  const { data: summary, isLoading } = useFileSummary(fileId);

  const file = files?.find((f) => f.id === fileId);

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{file?.original_filename || "File Information"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Data Summary Section */}
          <div>
            <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
              AI Analysis
            </h3>
            {isLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Loading analysis...</p>
              </div>
            ) : summary?.data_summary ? (
              <div className="bg-accent/50 p-4 rounded-lg">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown>{summary.data_summary}</ReactMarkdown>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 py-8 justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Analysis in progress...</p>
              </div>
            )}
          </div>

          {/* User Context Section */}
          {summary?.user_context && (
            <div>
              <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
                Your Context
              </h3>
              <div className="prose prose-sm max-w-none">
                <p className="text-sm bg-accent/30 p-4 rounded-lg">
                  {summary.user_context}
                </p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
