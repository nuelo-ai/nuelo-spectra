"use client";

import { useState } from "react";
import { AlertCircle, FolderPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface RunDetectionBannerProps {
  fileCount: number;
  onRunDetection: (userContext?: string) => void;
}

export function RunDetectionBanner({
  fileCount,
  onRunDetection,
}: RunDetectionBannerProps) {
  const noFiles = fileCount === 0;
  const [userContext, setUserContext] = useState("");

  return (
    <div className="rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {noFiles ? (
            <FolderPlus className="h-4 w-4 text-primary shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 text-primary shrink-0" />
          )}
          <p className="text-sm text-foreground">
            {noFiles
              ? "Add files to this collection to run detection"
              : `You have ${fileCount} ${fileCount === 1 ? "file" : "files"} — Run Detection to discover signals`}
          </p>
        </div>
        <Button
          variant="default"
          size="sm"
          onClick={() => onRunDetection(userContext.trim() || undefined)}
        >
          {noFiles ? "Add Files" : "Run Detection"}
        </Button>
      </div>
      {!noFiles && (
        <Textarea
          placeholder='Optional: guide the analysis (e.g. "check Q4 revenue anomalies" or "look for correlation between marketing spend and churn")'
          value={userContext}
          onChange={(e) => setUserContext(e.target.value)}
          rows={2}
          className="resize-none text-sm bg-background/50"
        />
      )}
    </div>
  );
}
