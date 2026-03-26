"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useMonetization } from "@/hooks/useCredits";
import { useAuth } from "@/hooks/useAuth";

const ALL_TABS = [
  { label: "Profile", href: "/settings" },
  { label: "API Keys", href: "/settings/keys" },
  { label: "Plan", href: "/settings/plan" },
  { label: "Billing", href: "/settings/billing" },
];

const SUBSCRIBER_TIERS = new Set(["standard", "premium"]);

export function SettingsNav() {
  const pathname = usePathname();
  const monetizationEnabled = useMonetization();
  const { user } = useAuth();

  const isSubscriber = user ? SUBSCRIBER_TIERS.has(user.user_class) : false;

  // Per D-13: When monetization OFF, existing subscribers keep Billing tab
  // (so they can cancel), but Plan tab is hidden (no new plans).
  // Non-subscribers lose both tabs.
  const tabs = monetizationEnabled
    ? ALL_TABS
    : ALL_TABS.filter((tab) => {
        if (tab.href === "/settings/plan") return false;
        if (tab.href === "/settings/billing") return isSubscriber;
        return true;
      });

  function isActive(tab: typeof ALL_TABS[number]) {
    return pathname === tab.href;
  }

  return (
    <div className="border-b">
      <nav className="flex gap-0 -mb-px overflow-x-auto">
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
              isActive(tab)
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30"
            )}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
