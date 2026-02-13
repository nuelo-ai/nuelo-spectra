"use client";

import { useState } from "react";
import { AlertCircle, X } from "lucide-react";

interface ChartErrorAlertProps {
  /** Error message to display */
  message: string;
}

/**
 * Subtle dismissible error alert for chart generation failures.
 * Persistent until user clicks the X button.
 */
export default function ChartErrorAlert({ message }: ChartErrorAlertProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
      <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
      <p className="flex-1 text-sm text-destructive/90">{message}</p>
      <button
        onClick={() => setDismissed(true)}
        className="text-destructive/70 hover:text-destructive transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
