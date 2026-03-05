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
import { Textarea } from "@/components/ui/textarea";
import { InvestigationQAThread } from "@/components/workspace/investigation-qa-thread";
import { InvestigationCheckpoint } from "@/components/workspace/investigation-checkpoint";

type ClosingPhase = "hidden" | "asking" | "responding" | "done";

const FOLLOW_UP_QUESTIONS = [
  {
    question: "That's helpful context. Does this change how you'd prioritize the root cause?",
    choices: [
      "Yes, this should be the primary focus now",
      "No, my original assessment still holds",
      "It adds nuance — worth noting in the report",
      "I'm unsure — more data would help",
    ],
  },
  {
    question: "How does this factor affect the confidence level of the analysis?",
    choices: [
      "Increases my confidence significantly",
      "Slightly increases confidence",
      "Doesn't change my confidence",
      "Actually introduces more uncertainty",
    ],
  },
];

function getInitialExchanges(signalId: string): QAExchange[] {
  const sessions = MOCK_INVESTIGATION_SESSIONS.filter(
    (s) => s.signalId === signalId
  );

  const inProgress = sessions.find((s) => s.status === "in-progress");
  if (inProgress) return inProgress.exchanges;

  if (sessions.length > 0) {
    const mostRecent = [...sessions]
      .filter((s) => s.status === "complete")
      .sort(
        (a, b) =>
          new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
      )[0];
    if (mostRecent) return mostRecent.exchanges;
  }

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
    {
      id: "default-002",
      question: "How long has this pattern been observable in the data?",
      choices: [
        "Less than 2 weeks",
        "2–4 weeks",
        "1–3 months",
        "More than 3 months",
      ],
      selectedChoice: null,
      freeTextAnswer: null,
    },
    {
      id: "default-003",
      question: "Are other signals in this collection showing related patterns?",
      choices: [
        "Yes, clearly related",
        "Possibly — worth checking",
        "No, this appears isolated",
        "I haven't reviewed the others",
      ],
      selectedChoice: null,
      freeTextAnswer: null,
    },
  ];
}

function initClosingPhase(exchanges: QAExchange[]): ClosingPhase {
  const answered = exchanges.filter(
    (ex) => ex.selectedChoice !== null || ex.freeTextAnswer !== null
  );
  const hasActive = exchanges.some(
    (ex) => ex.selectedChoice === null && ex.freeTextAnswer === null
  );
  if (answered.length >= 3 && !hasActive) return "asking";
  return "hidden";
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
  const [closingPhase, setClosingPhase] = useState<ClosingPhase>(() =>
    initClosingPhase(getInitialExchanges(signalId))
  );
  const [respondingInput, setRespondingInput] = useState("");
  const [followUpCount, setFollowUpCount] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);

  function checkShowClosingQuestion(updatedExchanges: QAExchange[]) {
    const answered = updatedExchanges.filter(
      (ex) => ex.selectedChoice !== null || ex.freeTextAnswer !== null
    );
    const hasActive = updatedExchanges.some(
      (ex) => ex.selectedChoice === null && ex.freeTextAnswer === null
    );
    if (answered.length >= 3 && !hasActive) {
      setClosingPhase("asking");
    }
  }

  function handleSelectChoice(exchangeId: string, choice: string) {
    setExchanges((prev) => {
      const updated = prev.map((ex) =>
        ex.id === exchangeId ? { ...ex, selectedChoice: choice } : ex
      );
      checkShowClosingQuestion(updated);
      return updated;
    });
  }

  function handleFreeText(exchangeId: string, text: string) {
    setExchanges((prev) => {
      const updated = prev.map((ex) =>
        ex.id === exchangeId ? { ...ex, freeTextAnswer: text } : ex
      );
      checkShowClosingQuestion(updated);
      return updated;
    });
  }

  function handleClosingAllGood() {
    setClosingPhase("done");
  }

  function handleClosingDiscuss() {
    setClosingPhase("responding");
  }

  function handleDiscussSubmit() {
    if (!respondingInput.trim()) return;

    const userInput = respondingInput.trim();
    const followUp = FOLLOW_UP_QUESTIONS[followUpCount % FOLLOW_UP_QUESTIONS.length];
    const discussionId = `discussion-${Date.now()}`;
    const followUpId = `followup-${Date.now()}`;

    setExchanges((prev) => [
      ...prev,
      {
        id: discussionId,
        question: "Is there anything else you'd like to discuss?",
        choices: [],
        selectedChoice: null,
        freeTextAnswer: userInput,
      },
      {
        id: followUpId,
        question: followUp.question,
        choices: followUp.choices,
        selectedChoice: null,
        freeTextAnswer: null,
      },
    ]);

    setFollowUpCount((c) => c + 1);
    setRespondingInput("");
    setClosingPhase("hidden");
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
      {/* Sticky header — theme-aware */}
      <div className="sticky top-0 z-20 flex items-center gap-3 px-6 py-3 bg-background border-b border-border">
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
            {/* Signal context block */}
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

            {/* Closing question — shown after ≥3 Q&As answered */}
            {closingPhase === "asking" && (
              <div className="space-y-4">
                <p className="text-sm font-medium text-foreground leading-relaxed pl-3 border-l-2 border-primary/40">
                  Is there anything else you&apos;d like to discuss about this signal before I generate the report?
                </p>
                <div className="space-y-2">
                  <button
                    onClick={handleClosingAllGood}
                    className="border border-border rounded-lg px-4 py-2.5 text-sm text-left w-full hover:border-primary/50 hover:bg-primary/5 transition-colors duration-100"
                  >
                    No, that covers it — proceed with report
                  </button>
                  <button
                    onClick={handleClosingDiscuss}
                    className="border border-border rounded-lg px-4 py-2.5 text-sm text-left w-full hover:border-primary/50 hover:bg-primary/5 transition-colors duration-100"
                  >
                    Yes, I&apos;d like to discuss something
                  </button>
                </div>
              </div>
            )}

            {/* Responding state — free-text input */}
            {closingPhase === "responding" && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground pl-3 border-l-2 border-primary/40">
                  What would you like to discuss?
                </p>
                <div className="flex gap-2 items-end">
                  <Textarea
                    placeholder="Share what's on your mind..."
                    value={respondingInput}
                    onChange={(e) => setRespondingInput(e.target.value)}
                    rows={3}
                    className="flex-1 resize-none"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                        handleDiscussSubmit();
                      }
                    }}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDiscussSubmit}
                    disabled={!respondingInput.trim()}
                  >
                    Send
                  </Button>
                </div>
              </div>
            )}

            {/* Checkpoint — shown when user confirms all good */}
            {closingPhase === "done" && (
              <InvestigationCheckpoint
                onProceed={handleProceed}
                isGenerating={isGenerating}
              />
            )}

            <div className="h-8" />
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
