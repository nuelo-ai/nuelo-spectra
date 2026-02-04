"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import { useUploadFile, useFileSummary } from "@/hooks/useFileManager";
import { useTabStore } from "@/stores/tabStore";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";

interface FileUploadZoneProps {
  onUploadComplete?: () => void;
}

type UploadStage = "idle" | "uploading" | "analyzing" | "ready";

/**
 * Drag-and-drop file upload zone with staged progress indicators
 */
export function FileUploadZone({ onUploadComplete }: FileUploadZoneProps) {
  const { mutate: uploadFile } = useUploadFile();
  const { openTab } = useTabStore();

  const [uploadStage, setUploadStage] = useState<UploadStage>("idle");
  const [progress, setProgress] = useState(0);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");

  // Poll for file summary when in analyzing stage
  const { data: summary } = useFileSummary(uploadStage === "analyzing" ? uploadedFileId : null);

  // Check if analysis is complete
  if (uploadStage === "analyzing" && summary?.data_summary) {
    setUploadStage("ready");
    setProgress(100);

    // Auto-close dialog after brief delay
    setTimeout(() => {
      if (uploadedFileId) {
        openTab(uploadedFileId, uploadedFileName);
      }
      if (onUploadComplete) {
        onUploadComplete();
      }
      // Reset state
      setUploadStage("idle");
      setProgress(0);
      setUploadedFileId(null);
      setUploadedFileName("");
    }, 1500);
  }

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
    [uploadFile, openTab, onUploadComplete]
  );

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
            transition-all duration-200
            ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-accent/50"
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
              <div className="rounded-full p-3 bg-green-500/10">
                <CheckCircle2 className="h-12 w-12 text-green-500" />
              </div>
            ) : (
              <div className="rounded-full p-3 bg-primary/10">
                <FileSpreadsheet className="h-12 w-12 text-primary animate-pulse" />
              </div>
            )}
            <p className="font-medium text-lg">{getStageText()}</p>
          </div>

          {/* Progress bar with gradient */}
          <div className="space-y-2">
            <Progress
              value={progress}
              className="h-2"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Uploading</span>
              <span>Analyzing</span>
              <span>Ready</span>
            </div>
          </div>

          {uploadedFileName && (
            <p className="text-sm text-center text-muted-foreground">
              {uploadedFileName}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
