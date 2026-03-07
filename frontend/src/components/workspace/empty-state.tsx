"use client";

import { BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  onCreateClick: () => void;
}

export function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4">
      <div className="flex items-center justify-center w-20 h-20 rounded-2xl bg-muted/50 mb-6">
        <BarChart3 className="h-10 w-10 text-muted-foreground/60" />
      </div>
      <h2 className="text-xl font-semibold mb-2">No collections yet</h2>
      <p className="text-sm text-muted-foreground text-center max-w-sm mb-8">
        Create your first collection to start detecting signals in your data
      </p>
      <Button onClick={onCreateClick} size="lg">
        Create Collection
      </Button>
    </div>
  );
}
