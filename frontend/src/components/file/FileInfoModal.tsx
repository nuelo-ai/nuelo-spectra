"use client";

import { useState } from "react";
import { useFileSummary, useUpdateFileContext } from "@/hooks/useFileManager";
import { useFiles } from "@/hooks/useFileManager";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

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
  const { mutate: updateContext, isPending: isSubmitting } = useUpdateFileContext();

  const [feedbackInput, setFeedbackInput] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const file = files?.find((f) => f.id === fileId);

  const handleSubmitFeedback = () => {
    if (!feedbackInput.trim()) return;
    updateContext(
      { fileId, context: feedbackInput },
      {
        onSuccess: () => {
          setFeedbackInput("");
          setSubmitSuccess(true);
          setTimeout(() => setSubmitSuccess(false), 3000);
        },
        onError: () => {
          toast.error("Failed to save feedback");
        },
      }
    );
  };

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

          {/* Refine AI Understanding (FILE-06) */}
          <div className="border-t pt-4">
            <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
              Refine AI Understanding
            </h3>
            <p className="text-xs text-muted-foreground mb-2">
              Provide additional context to improve how the AI interprets your data.
            </p>
            <textarea
              value={feedbackInput}
              onChange={(e) => setFeedbackInput(e.target.value)}
              placeholder="e.g., The 'status' column values mean: 1=Active, 2=Inactive, 3=Pending..."
              className="w-full min-h-[80px] rounded-lg border border-border bg-background p-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
              rows={3}
            />
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedbackInput.trim() || isSubmitting}
                className="bg-primary text-primary-foreground rounded py-1.5 px-4 text-sm hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Saving..." : "Save Feedback"}
              </button>
              {submitSuccess && (
                <span className="text-sm text-green-600">Saved!</span>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
