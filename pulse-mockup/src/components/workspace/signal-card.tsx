"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Signal } from "@/lib/mock-data";

const severityConfig = {
  critical: {
    label: "Critical",
    className: "bg-severity-critical/15 text-severity-critical border-severity-critical/30",
  },
  warning: {
    label: "Warning",
    className: "bg-severity-warning/15 text-severity-warning border-severity-warning/30",
  },
  info: {
    label: "Info",
    className: "bg-severity-info/15 text-severity-info border-severity-info/30",
  },
} as const;

interface SignalCardProps {
  signal: Signal;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

export function SignalCard({ signal, isSelected, onSelect }: SignalCardProps) {
  const severity = severityConfig[signal.severity];

  return (
    <button
      onClick={() => onSelect(signal.id)}
      className={cn(
        "w-full text-left rounded-lg border p-3 transition-all duration-150",
        "hover:bg-accent/50",
        isSelected
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
          className={cn("text-[10px] px-1.5 py-0 h-5 font-semibold", severity.className)}
        >
          {severity.label}
        </Badge>
        <span className="text-[10px] text-muted-foreground">
          {signal.category}
        </span>
      </div>
    </button>
  );
}
