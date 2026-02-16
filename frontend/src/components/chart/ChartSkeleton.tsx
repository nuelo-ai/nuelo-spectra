"use client";

interface ChartSkeletonProps {
  /** Current stage text from SSE (e.g., "Analyzing data...") */
  stage?: string;
}

/**
 * Loading skeleton for chart generation.
 * Shows a spinner with stage text and a shimmer placeholder.
 */
export default function ChartSkeleton({ stage }: ChartSkeletonProps) {
  return (
    <div className="w-full space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-b-primary" />
        <span className="text-sm text-muted-foreground">
          {stage || "Generating visualization..."}
        </span>
      </div>
      <div className="skeleton h-[350px] w-full rounded-lg" />
    </div>
  );
}
