"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
  { label: "Analyzing files", icon: FileSearch, duration: 3500 },
  { label: "Detecting patterns", icon: Search, duration: 3500 },
  { label: "Scoring signals", icon: BarChart3, duration: 3500 },
  { label: "Finalizing results", icon: CheckCircle, duration: 3000 },
];

const TOTAL_DURATION = STEPS.reduce((sum, s) => sum + s.duration, 0);

interface DetectionLoadingProps {
  collectionId: string;
}

export function DetectionLoading({ collectionId }: DetectionLoadingProps) {
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

      // Determine current step
      let cumulative = 0;
      for (let i = 0; i < STEPS.length; i++) {
        cumulative += STEPS[i].duration;
        if (elapsed < cumulative) {
          stepIndex = i;
          break;
        }
        if (i === STEPS.length - 1) {
          stepIndex = STEPS.length; // All done
        }
      }
      setCurrentStep(stepIndex);

      if (elapsed >= TOTAL_DURATION) {
        clearInterval(interval);
        // Auto-navigate after a brief pause
        setTimeout(() => {
          router.push(`/workspace/collections/${collectionId}/signals`);
        }, 500);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [collectionId, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-10">
      {/* Step stages */}
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

      {/* Progress bar */}
      <div className="w-full max-w-md space-y-2">
        <Progress value={progress} className="h-1.5" />
        <p className="text-xs text-center text-muted-foreground">
          Estimated time: 15-30 seconds
        </p>
      </div>
    </div>
  );
}
