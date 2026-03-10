"use client";

import { Loader2 } from "lucide-react";

const statusText: Record<string, string> = {
  pending: "Preparing detection...",
  profiling: "Profiling data files...",
  analyzing: "Analyzing patterns...",
};

interface DetectionProgressBannerProps {
  status: string;
}

export function DetectionProgressBanner({
  status,
}: DetectionProgressBannerProps) {
  return (
    <div className="rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 flex items-center gap-3">
      <Loader2 className="h-4 w-4 text-primary animate-spin shrink-0" />
      <p className="text-sm text-foreground font-medium">
        {statusText[status] ?? "Running detection..."}
      </p>
    </div>
  );
}
