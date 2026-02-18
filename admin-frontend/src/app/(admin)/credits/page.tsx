"use client";

import { CreditOverview } from "@/components/credits/CreditOverview";
import { useCreditDistribution } from "@/hooks/useCredits";

export default function CreditsPage() {
  const { data, isLoading, error } = useCreditDistribution();

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-destructive">
          Failed to load credit data: {error.message}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Credits</h1>
        <p className="text-muted-foreground">
          Platform-wide credit overview and distribution by tier
        </p>
      </div>
      <CreditOverview distributions={data} isLoading={isLoading} />
    </div>
  );
}
