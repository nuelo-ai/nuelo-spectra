"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusType = "active" | "inactive";
type TierType = "free_trial" | "free" | "standard" | "premium" | "internal";
type InvitationStatusType = "pending" | "accepted" | "revoked" | "expired";

interface StatusBadgeProps {
  type: "status" | "tier" | "invitation";
  value: string;
  className?: string;
}

const statusStyles: Record<StatusType, string> = {
  active: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-400",
  inactive: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400",
};

const tierStyles: Record<TierType, string> = {
  free_trial: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400",
  free: "bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-400",
  standard: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400",
  premium: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-400",
  internal: "bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-400",
};

const invitationStyles: Record<InvitationStatusType, string> = {
  pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-400",
  accepted: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-400",
  revoked: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400",
  expired: "bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-400",
};

function getLabel(type: string, value: string): string {
  if (type === "status") {
    return value === "active" || value === "true" ? "Active" : "Inactive";
  }
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function getStyle(type: string, value: string): string {
  if (type === "status") {
    const key = (value === "true" || value === "active" ? "active" : "inactive") as StatusType;
    return statusStyles[key] || "";
  }
  if (type === "tier") {
    return tierStyles[value.toLowerCase() as TierType] || tierStyles.free;
  }
  if (type === "invitation") {
    return invitationStyles[value.toLowerCase() as InvitationStatusType] || "";
  }
  return "";
}

export function StatusBadge({ type, value, className }: StatusBadgeProps) {
  const normalizedValue =
    type === "status"
      ? String(value).toLowerCase() === "true"
        ? "active"
        : String(value).toLowerCase() === "false"
        ? "inactive"
        : value.toLowerCase()
      : value.toLowerCase();

  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        getStyle(type, normalizedValue),
        className
      )}
    >
      {getLabel(type, normalizedValue)}
    </Badge>
  );
}
