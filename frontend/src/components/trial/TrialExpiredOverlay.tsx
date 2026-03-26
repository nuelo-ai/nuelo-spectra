"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useTrialState } from "@/hooks/useTrialState";
import { usePathname } from "next/navigation";
import Link from "next/link";

export function TrialExpiredOverlay() {
  const { logout } = useAuth();
  const { isTrial, isExpired } = useTrialState();
  const pathname = usePathname();

  // Don't block settings pages — expired trial users must reach /settings/plan
  const isSettingsPage = pathname?.startsWith("/settings");

  if (!isTrial || !isExpired || isSettingsPage) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background rounded-xl shadow-2xl p-8 max-w-md w-full mx-4 text-center space-y-6">
        <h2 className="text-2xl font-semibold">Your trial has expired</h2>
        <p className="text-muted-foreground">
          Choose a plan to continue using Spectra and access your data.
        </p>
        <div className="flex flex-col gap-3">
          <Button asChild size="lg">
            <Link href="/settings/plan">View Plans</Link>
          </Button>
          <Button variant="ghost" size="lg" onClick={logout}>
            Log Out
          </Button>
        </div>
      </div>
    </div>
  );
}
