"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, CheckCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUploadFile } from "@/hooks/useWorkspace";

interface FileUploadZoneProps {
  collectionId: string;
}

export function FileUploadZone({ collectionId }: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadFile(collectionId);

  // Use a ref to always have latest mutate function without re-creating callbacks
  const mutateRef = useRef(uploadMutation.mutate);
  mutateRef.current = uploadMutation.mutate;

  const handleFiles = useCallback((fileList: FileList) => {
    Array.from(fileList).forEach((file) => {
      const formData = new FormData();
      formData.append("file", file);
      mutateRef.current(formData);
    });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
        e.target.value = "";
      }
    },
    [handleFiles]
  );

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(e) => e.key === "Enter" && handleClick()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "relative flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-8 transition-all duration-200 cursor-pointer",
        "border-border/60 hover:border-primary/50 hover:bg-muted/30",
        isDragOver && "border-primary bg-primary/5 scale-[1.01]",
        uploadMutation.isPending && "pointer-events-none opacity-70"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls,.json"
        multiple
        onChange={handleInputChange}
        className="hidden"
      />
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-full bg-muted transition-colors",
          isDragOver && "bg-primary/20"
        )}
      >
        {uploadMutation.isPending ? (
          <Loader2 className="h-5 w-5 text-primary animate-spin" />
        ) : uploadMutation.isSuccess ? (
          <CheckCircle className="h-5 w-5 text-emerald-400" />
        ) : (
          <Upload
            className={cn(
              "h-5 w-5 text-muted-foreground transition-colors",
              isDragOver && "text-primary"
            )}
          />
        )}
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-foreground">
          {uploadMutation.isPending
            ? "Uploading..."
            : uploadMutation.isError
              ? "Upload failed — click to retry"
              : "Drop files here or click to upload"}
        </p>
        {uploadMutation.isError && (
          <p className="mt-1 text-xs text-red-400">
            {uploadMutation.error?.message || "Unknown error"}
          </p>
        )}
        <p className="mt-1 text-xs text-muted-foreground">
          Supported: CSV, Excel, JSON
        </p>
      </div>
    </div>
  );
}
