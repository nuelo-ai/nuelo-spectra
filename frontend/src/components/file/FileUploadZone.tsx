"use client";

import { useCallback, useState, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import { useUploadFile, useFileSummary } from "@/hooks/useFileManager";
import { useTabStore } from "@/stores/tabStore";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiClient } from "@/lib/api-client";

interface FileUploadZoneProps {
  onUploadComplete?: () => void;
  initialFiles?: File[];
}

type UploadStage = "idle" | "uploading" | "analyzing" | "ready";

/**
 * Drag-and-drop file upload zone with staged progress indicators
 */
export function FileUploadZone({ onUploadComplete, initialFiles }: FileUploadZoneProps) {
  const queryClient = useQueryClient();
  const { mutate: uploadFile } = useUploadFile();
  const { openTab } = useTabStore();

  const [uploadStage, setUploadStage] = useState<UploadStage>("idle");
  const [progress, setProgress] = useState(0);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [analysisText, setAnalysisText] = useState<string | null>(null);
  const [userContextInput, setUserContextInput] = useState<string>("");

  // Poll for file summary when in analyzing stage
  const { data: summary } = useFileSummary(
    uploadStage === "analyzing" || uploadStage === "ready" ? uploadedFileId : null
  );

  // Track if we've already transitioned to ready state to prevent duplicate transitions
  const hasTransitioned = useRef(false);

  // Check if analysis is complete and transition to ready state
  useEffect(() => {
    if (uploadStage === "analyzing" && summary?.data_summary && !hasTransitioned.current) {
      hasTransitioned.current = true;
      setAnalysisText(summary.data_summary);
      setUploadStage("ready");
      setProgress(100);
    }
  }, [uploadStage, summary?.data_summary]);

  // Guard ref for initialFiles processing
  const initialProcessed = useRef(false);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) {
        return;
      }

      const file = acceptedFiles[0];

      // Start upload stage
      setUploadStage("uploading");
      setProgress(0);

      // Simulate progress during upload
      const uploadProgressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 50) {
            clearInterval(uploadProgressInterval);
            return 50;
          }
          return prev + 10;
        });
      }, 200);

      uploadFile(
        { file },
        {
          onSuccess: (data) => {
            clearInterval(uploadProgressInterval);
            setProgress(50);
            setUploadedFileId(data.id);
            setUploadedFileName(data.original_filename);

            // Move to analyzing stage
            setUploadStage("analyzing");

            // Simulate progress during analysis
            const analyzeProgressInterval = setInterval(() => {
              setProgress((prev) => {
                if (prev >= 80) {
                  clearInterval(analyzeProgressInterval);
                  return 80;
                }
                return prev + 5;
              });
            }, 300);
          },
          onError: (error) => {
            clearInterval(uploadProgressInterval);
            setUploadStage("idle");
            setProgress(0);
            toast.error(error instanceof Error ? error.message : "Failed to upload file");
          },
        }
      );
    },
    [uploadFile, queryClient]
  );

  // Auto-trigger upload when initialFiles are provided (from parent drag-drop)
  // setTimeout(0) defers execution past React Strict Mode unmount-remount cycle
  // so the MutationObserver stays subscribed when onDrop fires
  useEffect(() => {
    if (initialFiles && initialFiles.length > 0 && !initialProcessed.current && uploadStage === "idle") {
      const timer = setTimeout(() => {
        initialProcessed.current = true;
        onDrop(initialFiles);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [initialFiles, onDrop, uploadStage]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
  });

  const getStageText = () => {
    switch (uploadStage) {
      case "uploading":
        return "Uploading...";
      case "analyzing":
        return "Analyzing data...";
      case "ready":
        return "Ready!";
      default:
        return "";
    }
  };

  return (
    <div className="w-full">
      {uploadStage === "idle" ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
            transition-all duration-200 ease-in-out
            ${
              isDragActive
                ? "border-primary bg-primary/5 scale-[1.02]"
                : "border-border hover:border-primary/50 hover:bg-accent/50 scale-100"
            }
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            <div className={`rounded-full p-3 ${isDragActive ? "bg-primary/10" : "bg-accent"}`}>
              <Upload className={`h-8 w-8 ${isDragActive ? "text-primary" : "text-muted-foreground"}`} />
            </div>
            <div>
              <p className="font-medium mb-1">
                {isDragActive ? "Drop your file here" : "Drag & drop your file"}
              </p>
              <p className="text-sm text-muted-foreground">or click to browse</p>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Supports CSV, Excel (.xlsx, .xls) • Max 50MB
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6 py-8">
          {/* File icon and stage indicator */}
          <div className="flex flex-col items-center gap-3">
            {uploadStage === "ready" ? (
              <div className="rounded-full p-3 bg-green-500/10" style={{ animation: "var(--animate-fadeIn)" }}>
                <CheckCircle2 className="h-12 w-12 text-green-500" style={{ animation: "var(--animate-slideUp)" }} />
              </div>
            ) : (
              <div className="rounded-full p-3 bg-primary/10">
                <FileSpreadsheet className="h-12 w-12 text-primary" style={{ animation: "var(--animate-pulse-gentle)" }} />
              </div>
            )}
            <p className="font-medium text-lg transition-opacity duration-300">{getStageText()}</p>
          </div>

          {/* Progress bar with gradient */}
          <div className="space-y-2">
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full gradient-primary transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span className={uploadStage === "uploading" ? "font-medium text-primary" : ""}>Uploading</span>
              <span className={uploadStage === "analyzing" ? "font-medium text-primary" : ""}>Analyzing</span>
              <span className={uploadStage === "ready" ? "font-medium text-green-500" : ""}>Ready</span>
            </div>
          </div>

          {uploadedFileName && (
            <p className="text-sm text-center text-muted-foreground">
              {uploadedFileName}
            </p>
          )}

          {/* Analysis result display when ready */}
          {uploadStage === "ready" && analysisText && (
            <div className="space-y-4">
              <div className="max-h-[40vh] overflow-y-auto bg-accent/50 rounded-lg p-4">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysisText}</ReactMarkdown>
                </div>
              </div>

              {/* Optional user context (FILE-05) */}
              <div className="space-y-2">
                <label htmlFor="user-context" className="text-sm font-medium text-muted-foreground">
                  Add context about your data (optional)
                </label>
                <textarea
                  id="user-context"
                  value={userContextInput}
                  onChange={(e) => setUserContextInput(e.target.value)}
                  placeholder="e.g., This is Q4 2025 sales data. The 'region' column maps to our sales territories..."
                  className="w-full min-h-[80px] rounded-lg border border-border bg-background p-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  Help the AI understand your data better for more accurate analysis.
                </p>
              </div>

              <div className="flex justify-center">
                <button
                  onClick={async () => {
                    try {
                      // Step 1: Save user context (non-blocking, fire-and-forget)
                      // Context is OPTIONAL -- failure must never block dialog close or tab open
                      if (userContextInput.trim() && uploadedFileId) {
                        try {
                          await apiClient.post(`/files/${uploadedFileId}/context`, {
                            context: userContextInput,
                          });
                        } catch (error) {
                          console.error("Failed to save user context:", error);
                          toast.error("Context could not be saved, but your file is ready.");
                          // Do NOT return -- proceed with dialog close and tab open
                        }
                      }

                      // Step 2: Refresh sidebar file list
                      try {
                        queryClient.invalidateQueries({ queryKey: ["files"], exact: true });
                        await queryClient.refetchQueries({ queryKey: ["files"], exact: true });
                      } catch (error) {
                        console.error("Failed to refresh file list:", error);
                        // Sidebar will catch up via refetchInterval fallback
                      }

                      // Step 3: Open file tab
                      if (uploadedFileId) {
                        openTab(uploadedFileId, uploadedFileName);
                      }
                    } catch (error) {
                      console.error("Continue to Chat handler error:", error);
                      toast.error("Something went wrong. Your file was uploaded successfully.");
                    } finally {
                      // ALWAYS close dialog and reset state, regardless of any errors above
                      if (onUploadComplete) {
                        onUploadComplete();
                      }
                      setUploadStage("idle");
                      setProgress(0);
                      setUploadedFileId(null);
                      setUploadedFileName("");
                      setAnalysisText(null);
                      setUserContextInput("");
                      hasTransitioned.current = false;
                    }
                  }}
                  className="bg-primary text-primary-foreground rounded py-2 px-6 hover:opacity-90 transition-opacity"
                >
                  Continue to Chat
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
