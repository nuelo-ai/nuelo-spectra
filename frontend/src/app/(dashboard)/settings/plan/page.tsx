"use client";

import { AlertTriangle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useTrialState } from "@/hooks/useTrialState";
import { usePlanPricing } from "@/hooks/usePlanPricing";
import { useSubscription } from "@/hooks/useSubscription";
import { PlanCard } from "@/components/billing/PlanCard";

export default function PlanPage() {
  const { isTrial, trialExpiresAt } = useTrialState();
  const { data: pricing, isLoading: pricingLoading } = usePlanPricing();
  const { data: subscription } = useSubscription();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Choose Your Plan</h2>
        <p className="text-muted-foreground mt-1">
          Select the plan that works best for you.
        </p>
      </div>

      {isTrial && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span>
            You&apos;re on a free trial. Choose a plan below to continue
            after your trial ends.
          </span>
        </div>
      )}

      {pricingLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-80 w-full rounded-lg" />
          ))}
        </div>
      ) : pricing ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pricing.plans.map((plan) => (
            <PlanCard
              key={plan.tier_key}
              plan={plan}
              isCurrentPlan={pricing.current_tier === plan.tier_key}
              hasSubscription={subscription?.has_subscription ?? false}
              currentTierKey={pricing.current_tier}
              subscription={subscription}
              isTrial={isTrial}
              trialExpiresAt={trialExpiresAt}
            />
          ))}
        </div>
      ) : (
        <p className="text-muted-foreground">Failed to load plan pricing. Please try again.</p>
      )}
    </div>
  );
}
