"use client";

import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InvestigationCheckpointProps {
  onProceed: () => void;
  isGenerating: boolean;
}

export function InvestigationCheckpoint({
  onProceed,
  isGenerating,
}: InvestigationCheckpointProps) {
  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold text-foreground">
          Ready to generate report
        </span>
      </div>

      <p className="text-sm text-muted-foreground">
        I have enough context to form a root cause analysis. Generating your investigation report now.
      </p>

      <Button
        onClick={onProceed}
        disabled={isGenerating}
        className="flex items-center gap-2"
      >
        {isGenerating ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating report...
          </>
        ) : (
          "Proceed with Report"
        )}
      </Button>
    </div>
  );
}
