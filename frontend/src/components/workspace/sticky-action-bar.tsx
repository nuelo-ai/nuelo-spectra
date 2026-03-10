"use client";

import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface StickyActionBarProps {
  selectedCount: number;
  onAddToCollection: () => void;
  isLoading?: boolean;
}

export function StickyActionBar({
  selectedCount,
  onAddToCollection,
  isLoading = false,
}: StickyActionBarProps) {
  return (
    <div
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-40",
        "flex items-center gap-6 rounded-xl px-6 py-3",
        "bg-card/80 backdrop-blur-xl border border-border/60 shadow-2xl shadow-black/20"
      )}
    >
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        <span className="font-semibold text-foreground">{selectedCount}</span>{" "}
        {selectedCount === 1 ? "file" : "files"} selected
      </span>

      <Button
        onClick={onAddToCollection}
        disabled={isLoading}
        className="gap-2"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Plus className="h-4 w-4" />
        )}
        Add to Collection
      </Button>
    </div>
  );
}
