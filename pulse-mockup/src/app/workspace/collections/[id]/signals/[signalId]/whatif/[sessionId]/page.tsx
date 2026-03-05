"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, CheckCircle, MessageSquare, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  MOCK_WHATIF_SESSIONS,
  MOCK_SIGNALS,
  WhatIfConfidence,
} from "@/lib/mock-data";
import { WhatIfRefinementChat } from "@/components/workspace/whatif-refinement-chat";
import { cn } from "@/lib/utils";

function confidenceBadgeClass(confidence: WhatIfConfidence) {
  switch (confidence) {
    case "high":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    case "medium":
      return "border-amber-500/30 bg-amber-500/10 text-amber-400";
    case "low":
      return "border-border bg-muted text-muted-foreground";
  }
}

function confidenceLabel(confidence: WhatIfConfidence) {
  switch (confidence) {
    case "high":
      return "High confidence";
    case "medium":
      return "Medium confidence";
    case "low":
      return "Low confidence";
  }
}

export default function WhatIfSessionPage() {
  const params = useParams();
  const router = useRouter();
  const collectionId = params.id as string;
  const signalId = params.signalId as string;
  const sessionId = params.sessionId as string;

  const session =
    MOCK_WHATIF_SESSIONS.find((s) => s.id === sessionId) ??
    MOCK_WHATIF_SESSIONS[0];

  const signal = MOCK_SIGNALS.find((s) => s.id === session.signalId);

  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(
    session.scenarios[0]?.id ?? ""
  );
  const [chatOpen, setChatOpen] = useState(false);

  const selectedScenario =
    session.scenarios.find((s) => s.id === selectedScenarioId) ??
    session.scenarios[0];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Page header — back to objective selection, signal + objective context */}
      <div className="flex items-center gap-3 px-6 py-3 bg-background border-b border-border shrink-0">
        <Link href={`/workspace/collections/${collectionId}/signals/${signalId}/whatif`}>
          <Button variant="ghost" size="sm" className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </Link>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-medium">What-If Scenarios</span>
        <div className="ml-auto flex flex-col items-end gap-0.5 min-w-0">
          <span className="text-xs text-muted-foreground">{signal?.title ?? signalId}</span>
          <span className="text-xs text-right">{session.objective}</span>
        </div>
      </div>

      {/* Three-panel layout */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* Scenario List */}
        <div className="w-[280px] flex-shrink-0 border-r border-border flex flex-col">
          <div className="px-4 py-3 border-b border-border shrink-0">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Scenarios
            </p>
          </div>

          <div className="py-2">
            {session.scenarios.map((scenario) => {
              const isSelected = scenario.id === selectedScenarioId;
              return (
                <div key={scenario.id} className="px-2">
                  <button
                    className={cn(
                      "w-full text-left rounded-lg px-3 py-3 transition-colors",
                      isSelected
                        ? "ring-1 ring-primary/30 bg-card"
                        : "hover:bg-muted/40"
                    )}
                    onClick={() => setSelectedScenarioId(scenario.id)}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-sm font-medium line-clamp-1">
                        {scenario.name}
                      </span>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs shrink-0",
                          confidenceBadgeClass(scenario.confidence)
                        )}
                      >
                        {confidenceLabel(scenario.confidence).split(" ")[0]}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {scenario.estimatedImpact}
                    </p>
                  </button>
                </div>
              );
            })}

            {/* Generate Report — immediately after last scenario with separator */}
            <div className="px-2 mt-1">
              <div className="border-t border-border pt-3 pb-1 px-1">
                <p className="text-xs text-muted-foreground mb-2">
                  Ready to document your findings?
                </p>
                <Button
                  variant="default"
                  size="sm"
                  className="w-full gap-2"
                  onClick={() =>
                    router.push(
                      `/workspace/collections/${collectionId}/reports/${
                        session.reportId ?? "rep-whatif-001"
                      }`
                    )
                  }
                >
                  <FileText className="h-4 w-4" />
                  Generate What-If Report
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Scenario Detail Panel */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Detail header: scenario name + Refine toggle */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-border shrink-0">
            <div className="flex items-center gap-2.5 min-w-0">
              <h2 className="text-sm font-semibold truncate">
                {selectedScenario.name}
              </h2>
              <Badge
                variant="outline"
                className={cn("text-xs shrink-0", confidenceBadgeClass(selectedScenario.confidence))}
              >
                {confidenceLabel(selectedScenario.confidence)}
              </Badge>
            </div>
            <Button
              variant={chatOpen ? "secondary" : "outline"}
              size="sm"
              className="gap-1.5 shrink-0 ml-4"
              onClick={() => setChatOpen((v) => !v)}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Refine
            </Button>
          </div>

          {/* Scrollable detail content */}
          <ScrollArea className="flex-1">
            <div className="p-6 space-y-5 max-w-2xl">
              {/* Narrative & Recommendations */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Narrative & Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">
                    {selectedScenario.narrative}
                  </p>
                </CardContent>
              </Card>

              {/* Estimated Impact */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Estimated Impact
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg bg-primary/10 border border-primary/20 px-4 py-3">
                    <p className="text-xs uppercase tracking-wider text-primary/70">
                      Projected Outcome
                    </p>
                    <p className="text-lg font-semibold text-primary mt-1">
                      {selectedScenario.estimatedImpact}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Assumptions */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Assumptions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 mt-1">
                    {selectedScenario.assumptions.map((assumption, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                        <span>{assumption}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Confidence */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Confidence
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge
                    variant="outline"
                    className={cn(confidenceBadgeClass(selectedScenario.confidence))}
                  >
                    {confidenceLabel(selectedScenario.confidence)}
                  </Badge>
                  <p className="text-sm text-muted-foreground leading-relaxed mt-2">
                    {selectedScenario.confidenceRationale}
                  </p>
                </CardContent>
              </Card>

              {/* Data Backing */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                    Data Backing
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {selectedScenario.dataBacking}
                  </p>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        </div>

        {/* Sliding Refine panel — overlays from the right */}
        <div
          className={cn(
            "absolute right-0 top-0 bottom-0 w-[320px] flex flex-col bg-background border-l border-border shadow-xl transition-transform duration-300 ease-in-out z-30",
            chatOpen ? "translate-x-0" : "translate-x-full"
          )}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Refine Scenario</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setChatOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* key remounts chat on scenario switch, resetting messages to new scenario's history */}
          <WhatIfRefinementChat
            key={selectedScenarioId}
            scenario={selectedScenario}
            initialMessages={session.chatHistory[selectedScenarioId] ?? []}
          />
        </div>
      </div>
    </div>
  );
}
