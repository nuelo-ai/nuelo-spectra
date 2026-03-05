"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Search,
  Brain,
  Sparkles,
  BarChart3,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  MOCK_SIGNALS,
  MOCK_INVESTIGATION_SESSIONS,
  MOCK_REPORTS,
} from "@/lib/mock-data";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "Sustain enterprise revenue growth into Q4",
  "Reduce risk of post-pricing churn in mid-market",
  "Identify expansion opportunities in analytics add-on",
  "Model Q4 revenue under seasonal reversion assumptions",
];

const LOADING_STEPS = [
  { label: "Analyzing root cause", icon: Brain, duration: 2500 },
  { label: "Generating scenarios", icon: Sparkles, duration: 3000 },
  { label: "Scoring confidence", icon: BarChart3, duration: 2500 },
  { label: "Finalizing scenarios", icon: CheckCircle, duration: 2000 },
];

const TOTAL_DURATION = LOADING_STEPS.reduce((sum, s) => sum + s.duration, 0);

function WhatIfLoading({
  collectionId,
  signalId,
}: {
  collectionId: string;
  signalId: string;
}) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let elapsed = 0;
    let stepIndex = 0;

    const interval = setInterval(() => {
      elapsed += 100;
      const pct = Math.min((elapsed / TOTAL_DURATION) * 100, 100);
      setProgress(pct);

      let cumulative = 0;
      for (let i = 0; i < LOADING_STEPS.length; i++) {
        cumulative += LOADING_STEPS[i].duration;
        if (elapsed < cumulative) {
          stepIndex = i;
          break;
        }
        if (i === LOADING_STEPS.length - 1) {
          stepIndex = LOADING_STEPS.length;
        }
      }
      setCurrentStep(stepIndex);

      if (elapsed >= TOTAL_DURATION) {
        clearInterval(interval);
        setTimeout(() => {
          router.push(
            `/workspace/collections/${collectionId}/signals/${signalId}/whatif/wif-001`
          );
        }, 500);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [collectionId, signalId, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-10">
      <div className="flex flex-col gap-4 w-full max-w-sm">
        {LOADING_STEPS.map((step, index) => {
          const Icon = step.icon;
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isUpcoming = index > currentStep;

          return (
            <div
              key={step.label}
              className={cn(
                "flex items-center gap-4 rounded-lg px-4 py-3 transition-all duration-300",
                isCompleted && "bg-emerald-500/10",
                isCurrent && "bg-primary/10 ring-1 ring-primary/30",
                isUpcoming && "opacity-40"
              )}
            >
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full transition-colors shrink-0",
                  isCompleted && "bg-emerald-500/20",
                  isCurrent && "bg-primary/20",
                  isUpcoming && "bg-muted"
                )}
              >
                {isCompleted ? (
                  <CheckCircle className="h-5 w-5 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="h-5 w-5 text-primary animate-spin" />
                ) : (
                  <Icon className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <span
                className={cn(
                  "text-sm font-medium transition-colors",
                  isCompleted && "text-emerald-400",
                  isCurrent && "text-primary",
                  isUpcoming && "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
              {isCompleted && (
                <CheckCircle className="h-4 w-4 text-emerald-400 ml-auto" />
              )}
            </div>
          );
        })}
      </div>

      <div className="w-full max-w-md space-y-2">
        <Progress value={progress} className="h-1.5" />
        <p className="text-xs text-center text-muted-foreground">
          Estimated time: 10–15 seconds
        </p>
      </div>
    </div>
  );
}

export default function WhatIfObjectivePage() {
  const params = useParams();
  const collectionId = params.id as string;
  const signalId = params.signalId as string;

  const signal = MOCK_SIGNALS.find((s) => s.id === signalId) ?? null;

  // Look up most recent complete investigation session for this signal
  const completeSessions = MOCK_INVESTIGATION_SESSIONS.filter(
    (s) => s.signalId === signalId && s.status === "complete"
  ).sort(
    (a, b) =>
      new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
  );
  const latestSession = completeSessions[0] ?? null;
  const investigationReport = latestSession?.reportId
    ? MOCK_REPORTS.find((r) => r.id === latestSession.reportId) ?? null
    : null;

  const [objective, setObjective] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showLoading, setShowLoading] = useState(false);

  function handleSuggestionClick(suggestion: string) {
    setObjective(suggestion);
    setIsFocused(false);
  }

  function handleGenerateClick() {
    if (!objective.trim()) return;
    setShowLoading(true);
  }

  if (showLoading) {
    return (
      <div className="flex flex-col h-full">
        {/* Sticky header */}
        <div className="sticky top-0 z-20 flex items-center gap-3 px-6 py-3 bg-background border-b border-border">
          <Button variant="ghost" size="sm" className="gap-1.5" disabled>
            <ArrowLeft className="h-4 w-4" />
            Back to Signals
          </Button>
          <div className="h-4 w-px bg-border" />
          <span className="text-sm font-medium">What-If Scenarios</span>
          <Badge variant="secondary" className="text-xs">
            5 credits
          </Badge>
          <div className="ml-auto text-xs text-muted-foreground">
            {signal?.title ?? signalId}
          </div>
        </div>
        <div className="flex-1 overflow-auto px-6 py-8">
          <WhatIfLoading collectionId={collectionId} signalId={signalId} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Sticky header */}
      <div className="sticky top-0 z-20 flex items-center gap-3 px-6 py-3 bg-background border-b border-border">
        <Link href={`/workspace/collections/${collectionId}/signals`}>
          <Button variant="ghost" size="sm" className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Back to Signals
          </Button>
        </Link>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-medium">What-If Scenarios</span>
        <Badge variant="secondary" className="text-xs">
          5 credits
        </Badge>
        <div className="ml-auto text-xs text-muted-foreground">
          {signal?.title ?? signalId}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
          {/* Root cause context card */}
          {investigationReport && (
            <div className="rounded-lg bg-muted/30 border border-border/50 p-4 space-y-2">
              <p className="text-xs text-muted-foreground">Root Cause</p>
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-medium">
                  {investigationReport.title}
                </p>
                <Badge className="text-xs bg-emerald-500/15 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20">
                  High confidence
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {signalId === "sig-001"
                  ? "The Q3 revenue spike is attributable to a successful enterprise tier pricing update that triggered accelerated upgrades from mid-market accounts."
                  : investigationReport.markdownContent
                      .split("## Root Cause")[1]
                      ?.split("\n")
                      .filter((l) => l.trim().length > 0)[0]
                      ?.replace(/^[> *#]+/, "")
                      .trim() ?? ""}
              </p>
            </div>
          )}

          {/* Objective input section */}
          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-semibold">Define your objective</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Select a suggested objective or type your own, then generate scenarios.
              </p>
            </div>

            {/* Action search bar */}
            <div className="relative">
              <div className="border border-border rounded-lg bg-background flex items-center gap-2 px-3 py-2 focus-within:ring-1 focus-within:ring-primary/50">
                <Search className="h-4 w-4 text-muted-foreground shrink-0" />
                <input
                  type="text"
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                  placeholder="Type your objective or select a suggestion..."
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => {
                    setTimeout(() => setIsFocused(false), 150);
                  }}
                />
                <Button
                  size="sm"
                  className="shrink-0"
                  disabled={!objective.trim()}
                  onClick={handleGenerateClick}
                >
                  Generate Scenarios →
                </Button>
              </div>

              {/* Suggestions dropdown */}
              {isFocused && (
                <div className="absolute left-0 right-0 top-full mt-1 z-30 rounded-lg border border-border bg-background shadow-md overflow-hidden">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      className="w-full text-left px-4 py-2.5 text-sm hover:bg-muted/60 transition-colors"
                      onMouseDown={(e) => {
                        // Prevent blur from firing before click registers
                        e.preventDefault();
                        handleSuggestionClick(suggestion);
                      }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
