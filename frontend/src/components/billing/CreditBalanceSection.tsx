"use client";

import { Skeleton } from "@/components/ui/skeleton";
import type { CreditBalance } from "@/hooks/useCredits";

interface CreditBalanceSectionProps {
  credits: CreditBalance | undefined;
  userClass: string;
  isLoading: boolean;
}

export function CreditBalanceSection({ credits, userClass, isLoading }: CreditBalanceSectionProps) {
  if (isLoading) {
    return (
      <div className="space-y-1">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-36" />
      </div>
    );
  }

  if (!credits) return null;

  const isTrial = userClass === "free_trial";
  const isOnDemand = userClass === "on_demand";

  return (
    <div className="space-y-1">
      {isTrial ? (
        <div className="text-sm">
          <span className="text-muted-foreground">Trial credits: </span>
          <span className="font-medium">
            {credits.balance} / {credits.tier_allocation}
          </span>
        </div>
      ) : (
        <>
          {!isOnDemand && (
            <div className="text-sm">
              <span className="text-muted-foreground">Subscription: </span>
              <span className="font-medium">
                {credits.balance} / {credits.tier_allocation}
              </span>
            </div>
          )}
          <div className="text-sm">
            <span className="text-muted-foreground">Purchased: </span>
            <span className="font-medium">{credits.purchased_balance} credits</span>
          </div>
          <div className="text-sm font-medium pt-1">
            Total available: {credits.total_balance}
          </div>
        </>
      )}
    </div>
  );
}
