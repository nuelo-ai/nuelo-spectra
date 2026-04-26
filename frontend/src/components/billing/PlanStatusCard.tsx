"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { apiClient } from "@/lib/api-client";
import { useMonetization } from "@/hooks/useCredits";
import type { SubscriptionStatus } from "@/hooks/useSubscription";
import { Skeleton } from "@/components/ui/skeleton";

// Display name mapping (DB key -> user-facing name)
const TIER_DISPLAY: Record<string, string> = {
  standard: "Basic",
  premium: "Premium",
  on_demand: "On Demand",
  free_trial: "Free Trial",
};

interface PlanStatusCardProps {
  subscription: SubscriptionStatus | undefined;
  userClass: string;
  isLoading: boolean;
}

export function PlanStatusCard({ subscription, userClass, isLoading }: PlanStatusCardProps) {
  const [cancelling, setCancelling] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();
  const monetizationEnabled = useMonetization();

  if (isLoading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-6 w-40" /></CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-60" />
          <Skeleton className="h-4 w-48" />
        </CardContent>
      </Card>
    );
  }

  const planName = TIER_DISPLAY[userClass] || userClass;
  const hasSubscription = subscription?.has_subscription ?? false;
  const status = subscription?.status ?? null;
  const cancelAtPeriodEnd = subscription?.cancel_at_period_end ?? false;
  const periodEnd = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : null;

  // Status badge
  let badgeVariant: "default" | "secondary" | "destructive" | "outline" = "secondary";
  let badgeLabel = planName;
  if (hasSubscription) {
    if (cancelAtPeriodEnd) {
      badgeLabel = "Cancelled";
      badgeVariant = "outline"; // amber styled via className
    } else if (status === "active") {
      badgeLabel = "Active";
      badgeVariant = "default";
    } else if (status === "past_due") {
      badgeLabel = "At Risk";
      badgeVariant = "destructive";
    }
  } else if (userClass === "free_trial") {
    badgeLabel = "Free Trial";
    badgeVariant = "outline";
  } else {
    badgeLabel = "On Demand";
    badgeVariant = "secondary";
  }

  const handleCancel = async () => {
    setCancelling(true);
    try {
      const res = await apiClient.post("/subscriptions/cancel", {});
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data?.detail?.detail || "Failed to cancel subscription");
      }
      const result = await res.json();
      const cancelDate = result.cancel_at
        ? new Date(result.cancel_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
        : "end of billing cycle";
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success(`Subscription cancelled. Access continues until ${cancelDate}.`);
    } catch (err: any) {
      toast.error(err.message || "Something went wrong. Please try again.");
    } finally {
      setCancelling(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-normal uppercase tracking-wide text-muted-foreground">Plan Status</h3>
          <Badge
            variant={badgeVariant}
            className={cancelAtPeriodEnd ? "border-amber-500 text-amber-600" : status === "active" ? "bg-green-500/10 text-green-600 border-green-500/20" : ""}
          >
            {badgeLabel}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Current Plan</span>
            <p className="font-medium">{planName}</p>
          </div>
          {hasSubscription && periodEnd && (
            <div>
              <span className="text-muted-foreground">
                {cancelAtPeriodEnd ? "Active until" : "Next billing"}
              </span>
              <p className="font-medium">{periodEnd}</p>
            </div>
          )}
          {!hasSubscription && !cancelAtPeriodEnd && (
            <div>
              <span className="text-muted-foreground">Status</span>
              <p className="font-medium">No active subscription</p>
            </div>
          )}
        </div>

        <div className="flex gap-3">
          {monetizationEnabled && (hasSubscription || userClass === "free_trial" || userClass === "on_demand") && (
            <Button variant="outline" onClick={() => router.push("/settings/plan")}>
              {hasSubscription ? "Change Plan" : "Choose a Plan"}
            </Button>
          )}
          {hasSubscription && !cancelAtPeriodEnd && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" className="text-destructive border-destructive/50 hover:bg-destructive/10">
                  Cancel Plan
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Cancel your subscription?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Your access continues until {periodEnd || "end of billing cycle"}. After that,
                    subscription credits reset to zero and you&apos;ll move to the On Demand plan.
                    Your purchased credits will be preserved.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Keep Plan</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {cancelling ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Cancelling...</>
                    ) : (
                      "Cancel Plan"
                    )}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
