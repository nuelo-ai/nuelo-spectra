"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { useSubscription } from "@/hooks/useSubscription";
import { useCredits } from "@/hooks/useCredits";
import { useBillingHistory } from "@/hooks/useBillingHistory";
import { useCreditPackages } from "@/hooks/useCreditPackages";
import { useTrialState } from "@/hooks/useTrialState";
import { useMonetization } from "@/hooks/useCredits";
import { PlanStatusCard } from "@/components/billing/PlanStatusCard";
import { CreditBalanceSection } from "@/components/billing/CreditBalanceSection";
import { CreditPackageCard } from "@/components/billing/CreditPackageCard";
import { BillingHistoryTable } from "@/components/billing/BillingHistoryTable";

function BillingPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { data: subscription, isLoading: subLoading } = useSubscription();
  const { data: credits, isLoading: creditsLoading } = useCredits();
  const { data: history, isLoading: historyLoading, isError: historyError, refetch: refetchHistory } = useBillingHistory();
  const { data: packages } = useCreditPackages();
  const { isTrial } = useTrialState();
  const monetizationEnabled = useMonetization();

  const userClass = user?.user_class ?? "free_trial";

  // Handle post-Stripe redirect toasts
  useEffect(() => {
    if (searchParams.get("session_id")) {
      toast.success("Subscription activated!");
      router.replace("/settings/billing");
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
      queryClient.invalidateQueries({ queryKey: ["credits", "balance"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "billing-history"] });
    }
    if (searchParams.get("topup") === "success") {
      toast.success("Credits added to your balance!");
      router.replace("/settings/billing");
      queryClient.invalidateQueries({ queryKey: ["credits", "balance"] });
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "billing-history"] });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold">Manage Plan</h2>
        <p className="text-muted-foreground mt-1">
          View your subscription, credits, and billing history.
        </p>
      </div>

      {/* Plan Status Card */}
      <PlanStatusCard
        subscription={subscription}
        userClass={userClass}
        isLoading={subLoading}
      />

      {/* Credits Section */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-normal uppercase tracking-wide text-muted-foreground">Credits</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <CreditBalanceSection
            credits={credits}
            userClass={userClass}
            isLoading={creditsLoading}
          />

          {/* Buy Credits -- hidden for trial users and when monetization is off */}
          {!isTrial && monetizationEnabled && packages && packages.length > 0 && (
            <>
              <Separator />
              <div className="space-y-3">
                <h4 className="text-sm font-medium">Buy Credits</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {packages.map((pkg) => (
                    <CreditPackageCard key={pkg.id} pkg={pkg} />
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-normal uppercase tracking-wide text-muted-foreground">Billing History</h3>
        </CardHeader>
        <CardContent>
          <BillingHistoryTable
            items={history?.items}
            isLoading={historyLoading}
            isError={historyError}
            refetch={refetchHistory}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense>
      <BillingPageContent />
    </Suspense>
  );
}
