"use client";

import type { Signal } from "@/lib/mock-data";

interface SignalDetailPanelProps {
  signal: Signal;
}

export function SignalDetailPanel({ signal }: SignalDetailPanelProps) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-2">{signal.title}</h2>
      <p className="text-muted-foreground">{signal.description}</p>
      {/* Full detail panel with chart coming in Task 2 */}
    </div>
  );
}
