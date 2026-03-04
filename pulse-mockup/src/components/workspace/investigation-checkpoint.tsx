"use client";

import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface InvestigationCheckpointProps {
  onProceed: () => void;
  onAddContext: (text: string) => void;
  isGenerating: boolean;
}

export function InvestigationCheckpoint({
  onProceed,
  onAddContext,
  isGenerating,
}: InvestigationCheckpointProps) {
  const [additionalContext, setAdditionalContext] = useState("");

  const handleAddContext = () => {
    if (additionalContext.trim()) {
      onAddContext(additionalContext.trim());
      setAdditionalContext("");
    }
  };

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold text-foreground">
          Ready to generate report
        </span>
      </div>

      {/* Body text */}
      <p className="text-sm text-muted-foreground">
        Based on your inputs, I have enough context to form a root cause
        analysis. You can proceed now or add more context first.
      </p>

      {/* Optional additional context */}
      <div className="space-y-2">
        <Textarea
          placeholder="Add more context before proceeding (optional)..."
          rows={2}
          value={additionalContext}
          onChange={(e) => setAdditionalContext(e.target.value)}
          className="resize-none"
          disabled={isGenerating}
        />
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
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
        {additionalContext.trim() && !isGenerating && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddContext}
          >
            Add context first
          </Button>
        )}
      </div>
    </div>
  );
}
