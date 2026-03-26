"use client";

import { useState, useEffect } from "react";
import { Clock, AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTrialState } from "@/hooks/useTrialState";
import { useMonetization } from "@/hooks/useCredits";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

export function TrialBanner() {
  const [dismissed, setDismissed] = useState(false);
  const { isTrial, isExpired, daysRemaining } = useTrialState();
  const monetizationEnabled = useMonetization();
  const [creditBalance, setCreditBalance] = useState<number | null>(null);

  useEffect(() => {
    if (!isTrial || isExpired) return;
    async function fetchCredits() {
      try {
        const res = await apiClient.get("/credits/balance");
        if (res.ok) {
          const data = await res.json();
          setCreditBalance(Math.floor(Number(data.total_balance)));
        }
      } catch {}
    }
    fetchCredits();
  }, [isTrial, isExpired]);

  // Don't render if: not trial, already expired (overlay handles), dismissed,
  // or monetization is disabled platform-wide (no upgrade path to show).
  if (!isTrial || isExpired || dismissed || !monetizationEnabled) return null;

  const isUrgent = (daysRemaining !== null && daysRemaining <= 3) || (creditBalance !== null && creditBalance <= 10);
  const borderColor = isUrgent ? "border-amber-500/50" : "border-primary/30";
  const bgColor = isUrgent ? "bg-amber-500/10" : "bg-primary/5";
  const Icon = isUrgent ? AlertTriangle : Clock;
  const iconColor = isUrgent ? "text-amber-500" : "text-primary";

  const handleDismiss = () => {
    setDismissed(true);
  };

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} px-4 py-3 flex items-center gap-3 mx-4 mt-3`}>
      <Icon className={`h-4 w-4 ${iconColor} shrink-0`} />
      <p className="text-sm text-foreground flex-1">
        {daysRemaining} day{daysRemaining !== 1 ? "s" : ""} remaining in your trial
        {creditBalance !== null && (
          <>{" "}&middot;{" "}{creditBalance} credit{creditBalance !== 1 ? "s" : ""} left</>
        )}
      </p>
      <Button asChild size="sm" variant={isUrgent ? "default" : "outline"}>
        <Link href="/settings/plan">Choose Plan</Link>
      </Button>
      <button
        onClick={handleDismiss}
        className="text-muted-foreground hover:text-foreground"
        aria-label="Dismiss trial banner"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
