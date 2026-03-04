"use client";

import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { COST_PER_FILE } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

interface StickyActionBarProps {
  selectedCount: number;
  onRunDetection: () => void;
}

export function StickyActionBar({
  selectedCount,
  onRunDetection,
}: StickyActionBarProps) {
  const estimatedCost = selectedCount * COST_PER_FILE;
  const hasSelection = selectedCount > 0;

  return (
    <div
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-40",
        "flex items-center gap-6 rounded-xl px-6 py-3",
        "bg-card/80 backdrop-blur-xl border border-border/60 shadow-2xl shadow-black/20"
      )}
    >
      {/* File count */}
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {hasSelection ? (
          <>
            <span className="font-semibold text-foreground">{selectedCount}</span>{" "}
            {selectedCount === 1 ? "file" : "files"} selected
          </>
        ) : (
          "No files selected"
        )}
      </span>

      {/* Credit estimate */}
      {hasSelection && (
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          ~<span className="font-semibold text-primary">{estimatedCost}</span>{" "}
          credits for {selectedCount} {selectedCount === 1 ? "file" : "files"}{" "}
          selected
        </span>
      )}

      {/* Run Detection button */}
      <div className="relative">
        <Button
          onClick={onRunDetection}
          disabled={!hasSelection}
          className="gap-2"
        >
          <Zap className="h-4 w-4" />
          Run Detection
        </Button>
        {!hasSelection && (
          <p className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground whitespace-nowrap">
            Select at least 1 file to run detection
          </p>
        )}
      </div>
    </div>
  );
}
