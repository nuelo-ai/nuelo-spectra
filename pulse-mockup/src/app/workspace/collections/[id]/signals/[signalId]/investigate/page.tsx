"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import {
  MOCK_SIGNALS,
  MOCK_INVESTIGATION_SESSIONS,
  type QAExchange,
} from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { InvestigationQAThread } from "@/components/workspace/investigation-qa-thread";
import { InvestigationCheckpoint } from "@/components/workspace/investigation-checkpoint";

function getInitialExchanges(signalId: string): QAExchange[] {
  const sessions = MOCK_INVESTIGATION_SESSIONS.filter(
    (s) => s.signalId === signalId
  );

  // Prefer in-progress session
  const inProgress = sessions.find((s) => s.status === "in-progress");
  if (inProgress) {
    return inProgress.exchanges;
  }

  // Fall back to most recent complete session
  if (sessions.length > 0) {
    const mostRecent = [...sessions]
      .filter((s) => s.status === "complete")
      .sort(
        (a, b) =>
          new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
      )[0];
    if (mostRecent) {
      return mostRecent.exchanges;
    }
  }

  // Default: single unanswered exchange for signals with no session data
  return [
    {
      id: "default-001",
      question: "What do you believe is the primary driver of this signal?",
      choices: [
        "Internal process change",
        "External market factor",
        "Data quality issue",
        "Seasonal pattern",
      ],
      selectedChoice: null,
      freeTextAnswer: null,
    },
  ];
}

function allExchangesAnswered(exchanges: QAExchange[]): boolean {
  return (
    exchanges.length > 0 &&
    exchanges.every(
      (ex) => ex.selectedChoice !== null || ex.freeTextAnswer !== null
    )
  );
}

export default function InvestigatePage() {
  const params = useParams();
  const router = useRouter();
  const collectionId = params.id as string;
  const signalId = params.signalId as string;

  const signal = MOCK_SIGNALS.find((s) => s.id === signalId) ?? null;

  const [exchanges, setExchanges] = useState<QAExchange[]>(() =>
    getInitialExchanges(signalId)
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [showCheckpoint, setShowCheckpoint] = useState(() =>
    allExchangesAnswered(getInitialExchanges(signalId))
  );

  function checkForCheckpoint(updatedExchanges: QAExchange[]) {
    if (allExchangesAnswered(updatedExchanges)) {
      setShowCheckpoint(true);
    }
  }

  function handleSelectChoice(exchangeId: string, choice: string) {
    setExchanges((prev) => {
      const updated = prev.map((ex) =>
        ex.id === exchangeId ? { ...ex, selectedChoice: choice } : ex
      );
      checkForCheckpoint(updated);
      return updated;
    });
  }

  function handleFreeText(exchangeId: string, text: string) {
    setExchanges((prev) => {
      const updated = prev.map((ex) =>
        ex.id === exchangeId ? { ...ex, freeTextAnswer: text } : ex
      );
      checkForCheckpoint(updated);
      return updated;
    });
  }

  function handleProceed() {
    setIsGenerating(true);
    setTimeout(() => {
      router.push(
        `/workspace/collections/${collectionId}/reports/rpt-inv-001`
      );
    }, 2000);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Sticky header bar */}
      <div className="sticky top-0 z-20 flex items-center gap-3 px-6 py-3 bg-[#111827] border-b border-[#1e293b]">
        <Link href={`/workspace/collections/${collectionId}/signals`}>
          <Button variant="ghost" size="sm" className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Back to Signals
          </Button>
        </Link>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-medium">Guided Investigation</span>
        <Badge variant="secondary" className="text-xs">
          3 credits
        </Badge>
        <div className="ml-auto text-xs text-muted-foreground">
          Signal: {signal?.title ?? signalId}
        </div>
      </div>

      {/* Main content — scrollable thread */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
            {/* Brief context block at top */}
            <div className="rounded-lg bg-muted/30 border border-border/50 p-4">
              <p className="text-xs text-muted-foreground mb-1">
                Investigating signal
              </p>
              <p className="text-sm font-medium">
                {signal?.title ?? signalId}
              </p>
              {signal?.description && (
                <p className="text-xs text-muted-foreground mt-1">
                  {signal.description.slice(0, 120)}
                  {signal.description.length > 120 ? "..." : ""}
                </p>
              )}
            </div>

            {/* Q&A thread */}
            <InvestigationQAThread
              exchanges={exchanges}
              onSelectChoice={handleSelectChoice}
              onFreeText={handleFreeText}
            />

            {/* Checkpoint — shown only when all exchanges answered */}
            {showCheckpoint && (
              <InvestigationCheckpoint
                onProceed={handleProceed}
                onAddContext={() => {
                  /* noop for mockup */
                }}
                isGenerating={isGenerating}
              />
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
