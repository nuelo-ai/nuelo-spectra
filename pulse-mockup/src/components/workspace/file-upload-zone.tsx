"use client";

import { useState, useCallback } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

export function FileUploadZone() {
  const [isDragOver, setIsDragOver] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    triggerFeedback();
  }, []);

  const handleClick = useCallback(() => {
    triggerFeedback();
  }, []);

  function triggerFeedback() {
    setShowFeedback(true);
    setTimeout(() => setShowFeedback(false), 600);
  }

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
        showFeedback && "border-primary bg-primary/10"
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-full bg-muted transition-colors",
          (isDragOver || showFeedback) && "bg-primary/20"
        )}
      >
        <Upload
          className={cn(
            "h-5 w-5 text-muted-foreground transition-colors",
            (isDragOver || showFeedback) && "text-primary"
          )}
        />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-foreground">
          Drop files here or click to upload
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supported: CSV, Excel, JSON
        </p>
      </div>
      {showFeedback && (
        <div className="absolute inset-0 rounded-lg bg-primary/5 animate-pulse pointer-events-none" />
      )}
    </div>
  );
}
