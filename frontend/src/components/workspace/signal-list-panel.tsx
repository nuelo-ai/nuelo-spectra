"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { SignalDetail } from "@/types/workspace";

const severityOrder: Record<SignalDetail["severity"], number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

const severityConfig = {
  critical: {
    label: "Critical",
    className:
      "bg-severity-critical/15 text-severity-critical border-severity-critical/30",
  },
  warning: {
    label: "Warning",
    className:
      "bg-severity-warning/15 text-severity-warning border-severity-warning/30",
  },
  info: {
    label: "Info",
    className:
      "bg-severity-info/15 text-severity-info border-severity-info/30",
  },
} as const;

interface SignalListPanelProps {
  signals: SignalDetail[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function SignalListPanel({
  signals,
  selectedId,
  onSelect,
}: SignalListPanelProps) {
  const sorted = [...signals].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  if (signals.length === 0) {
    return (
      <div className="w-[350px] shrink-0 border-r border-border flex flex-col h-full bg-card/50">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold">Signals</h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">No signals found</p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Run detection to generate signals
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-[350px] shrink-0 border-r border-border flex flex-col h-full bg-card/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold">Signals</h3>
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
          {signals.length} signals
        </Badge>
      </div>

      {/* Signal List */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="p-2 space-y-1.5">
          {sorted.map((signal) => {
            const severity = severityConfig[signal.severity];
            return (
              <button
                key={signal.id}
                onClick={() => onSelect(signal.id)}
                className={cn(
                  "w-full text-left rounded-lg border p-3 transition-all duration-150",
                  "hover:bg-accent/50",
                  selectedId === signal.id
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border bg-transparent"
                )}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h4 className="text-sm font-medium leading-snug line-clamp-2 flex-1">
                    {signal.title}
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-[10px] px-1.5 py-0 h-5 font-semibold",
                      severity.className
                    )}
                  >
                    {severity.label}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground">
                    {signal.category}
                  </span>
                </div>
                {signal.analysis && (
                  <p className="text-[11px] text-muted-foreground/80 mt-1.5 line-clamp-2">
                    {signal.analysis}
                  </p>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
