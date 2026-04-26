"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Loader2, Check } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { PlanInfo } from "@/hooks/usePlanPricing";
import type { SubscriptionStatus } from "@/hooks/useSubscription";

interface PlanChangePreview {
  proration_amount_cents: number;
  proration_display: string;
  new_plan_display: string;
  new_credit_allocation: number;
  change_type: string;
  effective_at: string;
}

interface PlanCardProps {
  plan: PlanInfo;
  isCurrentPlan: boolean;
  hasSubscription: boolean;
  currentTierKey: string;
  subscription: SubscriptionStatus | undefined;
  isTrial?: boolean;
  trialExpiresAt?: Date | null;
}

export function PlanCard({ plan, isCurrentPlan, hasSubscription, currentTierKey, subscription, isTrial, trialExpiresAt }: PlanCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [preview, setPreview] = useState<PlanChangePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const queryClient = useQueryClient();

  // Determine upgrade vs downgrade for subscribed users
  const tierOrder: Record<string, number> = { on_demand: 0, standard: 1, premium: 2 };
  const currentRank = tierOrder[currentTierKey] ?? 0;
  const newRank = tierOrder[plan.tier_key] ?? 0;
  const isUpgrade = newRank > currentRank;

  const periodEnd = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "end of billing cycle";

  const handleOpenDialog = async () => {
    setPreviewLoading(true);
    setDialogOpen(true);
    setPreview(null);
    try {
      const res = await apiClient.get(`/subscriptions/preview-change?plan_tier=${plan.tier_key}`);
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data?.detail || "Failed to preview plan change");
      }
      const data: PlanChangePreview = await res.json();
      setPreview(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load pricing preview");
      setDialogOpen(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSelectPlan = async () => {
    setIsLoading(true);
    try {
      if (plan.tier_key === "on_demand") {
        const res = await apiClient.post("/subscriptions/select-on-demand", {});
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data?.detail?.detail || "Failed to switch plan");
        }
        await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
        await queryClient.invalidateQueries({ queryKey: ["subscription"] });
        await queryClient.invalidateQueries({ queryKey: ["subscriptions", "plans"] });
        if (hasSubscription) {
          toast.success(`Your plan will switch to On Demand on ${periodEnd}. You won't be billed again.`);
        } else {
          toast.success("Switched to On Demand plan.");
        }
        setDialogOpen(false);
        window.location.href = "/settings/billing";
      } else if (hasSubscription) {
        const res = await apiClient.post("/subscriptions/change", { plan_tier: plan.tier_key });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data?.detail?.detail || "Failed to change plan");
        }
        const result = await res.json();
        await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
        await queryClient.invalidateQueries({ queryKey: ["subscription"] });
        await queryClient.invalidateQueries({ queryKey: ["subscriptions", "plans"] });
        await queryClient.invalidateQueries({ queryKey: ["credits"] });
        if (result.change_type === "upgrade") {
          toast.success(`Plan upgraded to ${result.new_plan}! New credits added.`);
        } else {
          toast.success(`Plan will change to ${result.new_plan} at end of billing cycle.`);
        }
        setDialogOpen(false);
        window.location.href = "/settings/billing";
      } else {
        const res = await apiClient.post("/subscriptions/checkout", { plan_tier: plan.tier_key });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data?.detail?.detail || "Failed to create checkout");
        }
        const { checkout_url } = await res.json();
        window.location.href = checkout_url;
        return;
      }
    } catch (err: any) {
      toast.error(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Determine button label
  let buttonLabel: string;
  if (isCurrentPlan) {
    buttonLabel = "Current Plan";
  } else if (plan.tier_key === "on_demand") {
    buttonLabel = "Select On Demand";
  } else if (hasSubscription) {
    buttonLabel = isUpgrade
      ? `Upgrade to ${plan.display_name}`
      : `Downgrade to ${plan.display_name}`;
  } else {
    buttonLabel = `Subscribe to ${plan.display_name}`;
  }

  const isOnDemandSwitch = plan.tier_key === "on_demand" && (hasSubscription || isTrial);
  const needsConfirmation = (hasSubscription && !isCurrentPlan) || isOnDemandSwitch;

  const handleOpenOnDemandDialog = () => {
    setDialogOpen(true);
  };

  const actionButton = (
    <Button
      className="w-full"
      variant={plan.is_popular && !isCurrentPlan ? "default" : "outline"}
      disabled={isCurrentPlan || isLoading || previewLoading}
      onClick={isOnDemandSwitch ? handleOpenOnDemandDialog : needsConfirmation ? handleOpenDialog : handleSelectPlan}
    >
      {(isLoading || previewLoading) ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          {previewLoading ? "Loading..." : "Processing..."}
        </>
      ) : (
        buttonLabel
      )}
    </Button>
  );

  return (
    <Card className={plan.is_popular ? "border-l-[3px] border-l-primary relative" : ""}>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">{plan.display_name}</h2>
          <div className="flex gap-2">
            {plan.is_popular && (
              <Badge className="bg-primary text-primary-foreground">Most Popular</Badge>
            )}
            {isCurrentPlan && (
              <Badge variant="secondary">Current Plan</Badge>
            )}
          </div>
        </div>
        <p className="text-2xl font-semibold">
          {plan.price_display}
        </p>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 mb-6">
          {plan.features.map((feature) => (
            <li key={feature} className="flex items-start gap-2 text-sm text-muted-foreground">
              <Check className="h-4 w-4 mt-0.5 text-primary shrink-0" />
              <span>{feature}</span>
            </li>
          ))}
        </ul>

        {actionButton}

        {needsConfirmation && (
          <AlertDialog open={dialogOpen} onOpenChange={(open) => { if (!isLoading) setDialogOpen(open); }}>
            <AlertDialogContent>
              {isOnDemandSwitch ? (
                <>
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      {isLoading ? "Processing..." : "Switch to On Demand?"}
                    </AlertDialogTitle>
                    <AlertDialogDescription asChild>
                      <div className="space-y-3">
                        {isLoading ? (
                          <div className="flex flex-col items-center gap-3 py-4">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p>{isTrial ? "Switching your account..." : "Cancelling your subscription..."}</p>
                          </div>
                        ) : isTrial ? (
                          <>
                            <p>Your free trial credits will remain available until your trial period ends{trialExpiresAt && (<> on <strong>{trialExpiresAt.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</strong></>)}. After that, any remaining trial credits will be removed.</p>
                            <p>As an On Demand user, there are no monthly fees. You can purchase credits anytime based on your needs.</p>
                          </>
                        ) : (
                          <>
                            <p>Your current subscription will be cancelled and you will not be billed again at the next renewal.</p>
                            <p>Your plan remains active with full access until <strong>{periodEnd}</strong>. After that date, your account will switch to On Demand.</p>
                            <p>As an On Demand user, you can purchase credits anytime based on your needs — no monthly commitment required.</p>
                            <p className="text-sm text-muted-foreground">Note: Subscription credits will be removed when your plan expires. Any purchased credits will be preserved.</p>
                          </>
                        )}
                      </div>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  {!isLoading && (
                    <AlertDialogFooter>
                      <AlertDialogCancel>{isTrial ? "Stay on Free Trial" : "Keep Current Plan"}</AlertDialogCancel>
                      <Button variant={isTrial ? "default" : "destructive"} onClick={handleSelectPlan} disabled={isLoading}>
                        Switch to On Demand
                      </Button>
                    </AlertDialogFooter>
                  )}
                </>
              ) : (
                <>
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      {isLoading
                        ? "Processing payment..."
                        : isUpgrade ? `Upgrade to ${plan.display_name}?` : `Downgrade to ${plan.display_name}?`}
                    </AlertDialogTitle>
                    <AlertDialogDescription asChild>
                      <div className="space-y-2">
                        {isLoading ? (
                          <div className="flex flex-col items-center gap-3 py-4">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p>Charging {preview?.proration_display} and updating your plan...</p>
                          </div>
                        ) : previewLoading ? (
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Calculating price...</span>
                          </div>
                        ) : preview ? (
                          isUpgrade ? (
                            <>
                              <p>You&apos;ll be charged <strong>{preview.proration_display}</strong> now (prorated for remaining days in your billing cycle).</p>
                              <p>Your credits will be reset to <strong>{preview.new_credit_allocation}</strong> immediately.</p>
                            </>
                          ) : (
                            <p>Your plan change takes effect at end of your billing cycle on <strong>{periodEnd}</strong>. You&apos;ll continue on your current plan until then.</p>
                          )
                        ) : null}
                      </div>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  {!isLoading && (
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <Button onClick={handleSelectPlan} disabled={isLoading || previewLoading || !preview}>
                        {isUpgrade ? "Confirm Upgrade" : "Confirm Downgrade"}
                      </Button>
                    </AlertDialogFooter>
                  )}
                </>
              )}
            </AlertDialogContent>
          </AlertDialog>
        )}
      </CardContent>
    </Card>
  );
}
