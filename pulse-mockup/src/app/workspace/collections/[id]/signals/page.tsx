"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { MOCK_SIGNALS, MOCK_COLLECTIONS } from "@/lib/mock-data";
import type { SignalSeverity } from "@/lib/mock-data";
import { SignalListPanel } from "@/components/workspace/signal-list-panel";
import { SignalDetailPanel } from "@/components/workspace/signal-detail-panel";

const severityOrder: Record<SignalSeverity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

export default function SignalsPage() {
  const params = useParams();
  const collectionId = params.id as string;

  const collection = MOCK_COLLECTIONS.find((c) => c.id === collectionId);
  const signals = MOCK_SIGNALS;

  // Auto-select highest severity signal on mount
  const highestSeverityId = useMemo(() => {
    const sorted = [...signals].sort(
      (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
    );
    return sorted[0]?.id ?? null;
  }, [signals]);

  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(
    highestSeverityId
  );

  const selectedSignal = signals.find((s) => s.id === selectedSignalId) ?? null;

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Page Header */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3 mb-1">
          <Link
            href={`/workspace/collections/${collectionId}`}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link
              href="/workspace"
              className="hover:text-foreground transition-colors"
            >
              Collections
            </Link>
            <span>/</span>
            <Link
              href={`/workspace/collections/${collectionId}`}
              className="hover:text-foreground transition-colors"
            >
              {collection?.name ?? "Collection"}
            </Link>
            <span>/</span>
            <span className="text-foreground font-medium">
              Detection Results
            </span>
          </div>
        </div>
      </div>

      {/* Content: Signal List + Detail */}
      <div className="flex flex-1 min-h-0">
        <SignalListPanel
          signals={signals}
          selectedSignalId={selectedSignalId}
          onSelectSignal={setSelectedSignalId}
        />

        <div className="flex-1 min-w-0">
          {selectedSignal ? (
            <SignalDetailPanel signal={selectedSignal} />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              Select a signal to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
