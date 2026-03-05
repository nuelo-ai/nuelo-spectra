"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { FileText, CheckCircle } from "lucide-react";
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
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
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

  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(
    session.scenarios[0]?.id ?? ""
  );

  const selectedScenario =
    session.scenarios.find((s) => s.id === selectedScenarioId) ??
    session.scenarios[0];

  return (
    <div className="flex h-full overflow-hidden">
      {/* Scenario List Panel */}
      <div className="w-[280px] flex-shrink-0 border-r border-border flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Scenarios
          </p>
          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
            {session.objective}
          </p>
        </div>

        {/* Scenario Cards */}
        <div className="flex-1 overflow-y-auto py-2">
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
                      {confidenceLabel(scenario.confidence)}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {scenario.estimatedImpact}
                  </p>
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer — Generate Report Button */}
        <div className="px-3 py-3 border-t border-border">
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

      {/* Scenario Detail Panel */}
      <div className="flex-1 min-w-0 border-r border-border">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-5 max-w-2xl">
            {/* Name + Confidence Badge */}
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold">{selectedScenario.name}</h2>
              <Badge
                variant="outline"
                className={cn(confidenceBadgeClass(selectedScenario.confidence))}
              >
                {confidenceLabel(selectedScenario.confidence)}
              </Badge>
            </div>

            {/* Narrative */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  Narrative
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
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm"
                    >
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

      {/* Refinement Chat Panel — key prop causes React to remount on scenario switch,
          reinitializing chat state with the new scenario's initialMessages */}
      <WhatIfRefinementChat
        key={selectedScenarioId}
        scenario={selectedScenario}
        initialMessages={session.chatHistory[selectedScenarioId] ?? []}
      />
    </div>
  );
}
