"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useUserDetail } from "@/hooks/useUsers";
import { UserDetailTabs } from "@/components/users/UserDetailTabs";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeftIcon, AlertCircleIcon } from "lucide-react";

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = use(params);
  const router = useRouter();
  const { data: user, isLoading, isError, refetch } = useUserDetail(userId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-6 w-72" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (isError || !user) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16">
        <AlertCircleIcon className="size-10 text-destructive" />
        <p className="text-muted-foreground">Failed to load user details</p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push("/users")}>
            Back to Users
          </Button>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const displayName =
    user.first_name || user.last_name
      ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
      : user.email;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start gap-4">
        <Button
          variant="ghost"
          size="sm"
          className="mt-1"
          onClick={() => router.push("/users")}
        >
          <ArrowLeftIcon className="mr-1 size-4" />
          Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {displayName}
            </h1>
            <StatusBadge
              type="status"
              value={user.is_active ? "active" : "inactive"}
            />
            <StatusBadge type="tier" value={user.user_class} />
          </div>
          <p className="text-sm text-muted-foreground mt-1">{user.email}</p>
        </div>
      </div>

      {/* Tabs */}
      <UserDetailTabs user={user} />
    </div>
  );
}
