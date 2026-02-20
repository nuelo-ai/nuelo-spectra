"use client";

/**
 * AccountInfo component for displaying read-only account details.
 * Shows email, creation date, and account status.
 */

import { useAuth } from "@/hooks/useAuth";
import { useAppVersion } from "@/hooks/useAppVersion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

export function AccountInfo() {
  const { user } = useAuth();
  const { data: versionData } = useAppVersion();

  if (!user) {
    return null;
  }

  // Format creation date as readable string
  const createdDate = new Date(user.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Information</CardTitle>
        <CardDescription>Your account details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Email Address</Label>
          <p className="text-sm text-muted-foreground">{user.email}</p>
        </div>

        <div className="space-y-2">
          <Label>Account Created</Label>
          <p className="text-sm text-muted-foreground">{createdDate}</p>
        </div>

        <div className="space-y-2">
          <Label>Account Status</Label>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
              Active
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <Label>App Version</Label>
          <p className="text-sm text-muted-foreground">
            {versionData?.version ?? "\u2014"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
