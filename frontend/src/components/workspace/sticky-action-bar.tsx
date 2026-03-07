"use client";

import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface StickyActionBarProps {
  selectedCount: number;
  creditCost: number;
  onRunDetection: () => void;
  isLoading?: boolean;
}

export function StickyActionBar({
  selectedCount,
  creditCost,
  onRunDetection,
  isLoading = false,
}: StickyActionBarProps) {
  const hasSelection = selectedCount > 0;

  return (
    <div
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-40",
        "flex items-center gap-6 rounded-xl px-6 py-3",
        "bg-card/80 backdrop-blur-xl border border-border/60 shadow-2xl shadow-black/20"
      )}
    >
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {hasSelection ? (
          <>
            <span className="font-semibold text-foreground">
              {selectedCount}
            </span>{" "}
            {selectedCount === 1 ? "file" : "files"} selected
          </>
        ) : (
          "No files selected"
        )}
      </span>

      {hasSelection && (
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          ~<span className="font-semibold text-primary">{creditCost}</span>{" "}
          credits
        </span>
      )}

      <Button
        onClick={onRunDetection}
        disabled={!hasSelection || isLoading}
        className="gap-2"
      >
        <Zap className="h-4 w-4" />
        Run Detection ({creditCost} credits)
      </Button>
    </div>
  );
}
