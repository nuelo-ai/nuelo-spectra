"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { SignalCard } from "@/components/workspace/signal-card";
import type { Signal, SignalSeverity } from "@/lib/mock-data";

const severityOrder: Record<SignalSeverity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

interface SignalListPanelProps {
  signals: Signal[];
  selectedSignalId: string | null;
  onSelectSignal: (id: string) => void;
}

export function SignalListPanel({
  signals,
  selectedSignalId,
  onSelectSignal,
}: SignalListPanelProps) {
  const sorted = [...signals].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="w-[280px] shrink-0 border-r border-border flex flex-col h-full bg-card/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold">Signals</h3>
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
          {signals.length} signals
        </Badge>
      </div>

      {/* Signal List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1.5">
          {sorted.map((signal) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              isSelected={selectedSignalId === signal.id}
              onSelect={onSelectSignal}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
