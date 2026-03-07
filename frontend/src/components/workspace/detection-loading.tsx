"use client";

import { useEffect, useState } from "react";
import {
  FileSearch,
  Search,
  BarChart3,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const STEPS = [
  { label: "Profiling data", icon: FileSearch },
  { label: "Detecting anomalies", icon: Search },
  { label: "Analyzing trends", icon: BarChart3 },
  { label: "Generating signals", icon: CheckCircle },
];

interface DetectionLoadingProps {
  /** Current step index driven by pulse status polling (0-3), or null for timer-based animation */
  currentStep?: number;
}

export function DetectionLoading({ currentStep: externalStep }: DetectionLoadingProps) {
  const [internalStep, setInternalStep] = useState(0);
  const [progress, setProgress] = useState(0);

  // Timer-based animation when no external step is provided
  const useTimer = externalStep === undefined;
  const currentStep = useTimer ? internalStep : externalStep;

  useEffect(() => {
    if (!useTimer) return;

    let elapsed = 0;
    const totalDuration = 13500; // sum of step durations
    const stepDurations = [3500, 3500, 3500, 3000];

    const interval = setInterval(() => {
      elapsed += 100;
      const pct = Math.min((elapsed / totalDuration) * 100, 100);
      setProgress(pct);

      let cumulative = 0;
      for (let i = 0; i < stepDurations.length; i++) {
        cumulative += stepDurations[i];
        if (elapsed < cumulative) {
          setInternalStep(i);
          break;
        }
        if (i === stepDurations.length - 1) {
          setInternalStep(stepDurations.length);
        }
      }

      if (elapsed >= totalDuration) {
        clearInterval(interval);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [useTimer]);

  const progressValue = useTimer
    ? progress
    : Math.min(((currentStep + 1) / STEPS.length) * 100, 100);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-10">
      <div className="flex flex-col gap-4 w-full max-w-sm">
        {STEPS.map((step, index) => {
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
        <Progress value={progressValue} className="h-1.5" />
        <p className="text-xs text-center text-muted-foreground">
          Estimated time: 15-30 seconds
        </p>
      </div>
    </div>
  );
}
