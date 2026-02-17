"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useActivateUser,
  useDeactivateUser,
  useResetPassword,
  useChangeTier,
  useAdjustCredits,
  useUserActivity,
  useUserCreditTransactions,
} from "@/hooks/useUsers";
import type { UserDetail, CreditTransaction } from "@/types/user";
import {
  CalendarIcon,
  CreditCardIcon,
  MailIcon,
  ShieldIcon,
  UserIcon,
  ActivityIcon,
  MonitorIcon,
} from "lucide-react";

interface UserDetailTabsProps {
  user: UserDetail;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatShortDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ---------------------------------------------------------------------------
// Overview Tab
// ---------------------------------------------------------------------------
function OverviewTab({ user }: { user: UserDetail }) {
  const [confirmAction, setConfirmAction] = useState<
    "activate" | "deactivate" | "reset-password" | null
  >(null);
  const [showTierChange, setShowTierChange] = useState(false);
  const [newTier, setNewTier] = useState(user.user_class);

  const activateUser = useActivateUser();
  const deactivateUser = useDeactivateUser();
  const resetPassword = useResetPassword();
  const changeTier = useChangeTier();

  const handleConfirmAction = async () => {
    try {
      switch (confirmAction) {
        case "activate":
          await activateUser.mutateAsync({ userId: user.id });
          toast.success("User activated");
          break;
        case "deactivate":
          await deactivateUser.mutateAsync({ userId: user.id });
          toast.success("User deactivated");
          break;
        case "reset-password":
          await resetPassword.mutateAsync({ userId: user.id });
          toast.success("Password reset email sent");
          break;
      }
    } catch (e: any) {
      toast.error(e.message);
    }
    setConfirmAction(null);
  };

  const handleTierChange = async () => {
    try {
      await changeTier.mutateAsync({ userId: user.id, user_class: newTier });
      toast.success(`Tier changed to ${newTier}`);
    } catch (e: any) {
      toast.error(e.message);
    }
    setShowTierChange(false);
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Profile info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <UserIcon className="size-4" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Name</span>
            <span className="font-medium">
              {user.first_name || user.last_name
                ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
                : "-"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground flex items-center gap-1">
              <MailIcon className="size-3" /> Email
            </span>
            <span className="font-medium">{user.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status</span>
            <StatusBadge
              type="status"
              value={user.is_active ? "active" : "inactive"}
            />
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Tier</span>
            <StatusBadge type="tier" value={user.user_class} />
          </div>
          {user.is_admin && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Role</span>
              <Badge variant="outline" className="gap-1">
                <ShieldIcon className="size-3" /> Admin
              </Badge>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-muted-foreground flex items-center gap-1">
              <CalendarIcon className="size-3" /> Created
            </span>
            <span>{formatDate(user.created_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Login</span>
            <span>{formatDate(user.last_login_at)}</span>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {user.is_active ? (
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => setConfirmAction("deactivate")}
            >
              Deactivate User
            </Button>
          ) : (
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => setConfirmAction("activate")}
            >
              Activate User
            </Button>
          )}
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => setConfirmAction("reset-password")}
          >
            Reset Password
          </Button>
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => {
              setNewTier(user.user_class);
              setShowTierChange(true);
            }}
          >
            Change Tier
          </Button>
        </CardContent>
      </Card>

      {/* Confirm modals */}
      <ConfirmModal
        open={confirmAction === "activate"}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirmAction}
        title="Activate User"
        description={`Re-activate ${user.email}?`}
        confirmLabel="Activate"
        loading={activateUser.isPending}
      />
      <ConfirmModal
        open={confirmAction === "deactivate"}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirmAction}
        title="Deactivate User"
        description={`Deactivate ${user.email}? They will be immediately logged out.`}
        confirmLabel="Deactivate"
        variant="destructive"
        loading={deactivateUser.isPending}
      />
      <ConfirmModal
        open={confirmAction === "reset-password"}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirmAction}
        title="Reset Password"
        description={`Send a password reset email to ${user.email}?`}
        confirmLabel="Send Reset Email"
        loading={resetPassword.isPending}
      />

      {/* Tier change dialog -- inline card */}
      {showTierChange && (
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Change Tier</CardTitle>
          </CardHeader>
          <CardContent className="flex items-end gap-4">
            <div className="flex-1">
              <Label>New Tier</Label>
              <Select value={newTier} onValueChange={setNewTier}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="free">Free</SelectItem>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="premium">Premium</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleTierChange} disabled={changeTier.isPending}>
              {changeTier.isPending ? "Saving..." : "Save"}
            </Button>
            <Button variant="outline" onClick={() => setShowTierChange(false)}>
              Cancel
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Credits Tab
// ---------------------------------------------------------------------------
function CreditsTab({ user }: { user: UserDetail }) {
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const adjustCredits = useAdjustCredits();
  const { data: transactions, isLoading } = useUserCreditTransactions(user.id);

  const handleAdjust = async () => {
    const num = parseFloat(amount);
    if (isNaN(num) || !reason.trim()) {
      toast.error("Enter a valid amount and reason");
      return;
    }
    try {
      await adjustCredits.mutateAsync({
        userId: user.id,
        amount: num,
        reason: reason.trim(),
      });
      toast.success("Credits adjusted");
      setAmount("");
      setReason("");
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Balance display */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CreditCardIcon className="size-4" />
            Credit Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">
            {user.credit_balance.toFixed(1)}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Tier: {user.user_class}
          </p>
        </CardContent>
      </Card>

      {/* Adjustment form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Adjust Credits</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="credit-amount">Amount</Label>
              <Input
                id="credit-amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="e.g. 10 or -5"
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="credit-reason">Reason</Label>
              <Input
                id="credit-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Reason for adjustment"
                className="mt-1.5"
              />
            </div>
          </div>
          <Button
            onClick={handleAdjust}
            disabled={adjustCredits.isPending}
            size="sm"
          >
            {adjustCredits.isPending ? "Processing..." : "Adjust"}
          </Button>
        </CardContent>
      </Card>

      {/* Transaction history */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !transactions || transactions.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No credit transactions yet
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Balance After</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx: CreditTransaction) => (
                  <TableRow key={tx.id}>
                    <TableCell className="text-muted-foreground">
                      {formatShortDate(tx.created_at)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {tx.transaction_type}
                      </Badge>
                    </TableCell>
                    <TableCell
                      className={`text-right font-mono ${
                        tx.amount >= 0
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      {tx.amount >= 0 ? "+" : ""}
                      {tx.amount.toFixed(1)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {tx.balance_after.toFixed(1)}
                    </TableCell>
                    <TableCell className="text-muted-foreground max-w-[200px] truncate">
                      {tx.reason || "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------
function ActivityTab({ userId }: { userId: string }) {
  const { data, isLoading } = useUserActivity(userId);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!data || data.months.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          No activity data available
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ActivityIcon className="size-4" />
          Monthly Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Month</TableHead>
              <TableHead className="text-right">Messages</TableHead>
              <TableHead className="text-right">Sessions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.months.map((m) => (
              <TableRow key={m.month}>
                <TableCell className="font-medium">{m.month}</TableCell>
                <TableCell className="text-right">
                  {m.message_count.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  {m.session_count.toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Sessions Tab
// ---------------------------------------------------------------------------
function SessionsTab({ user }: { user: UserDetail }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MonitorIcon className="size-4" />
          Sessions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-3 mb-6">
          <div className="rounded-lg border p-4 text-center">
            <div className="text-2xl font-bold">{user.session_count}</div>
            <div className="text-xs text-muted-foreground">Total Sessions</div>
          </div>
          <div className="rounded-lg border p-4 text-center">
            <div className="text-2xl font-bold">{user.message_count}</div>
            <div className="text-xs text-muted-foreground">Total Messages</div>
          </div>
          <div className="rounded-lg border p-4 text-center">
            <div className="text-2xl font-bold">{user.file_count}</div>
            <div className="text-xs text-muted-foreground">Total Files</div>
          </div>
        </div>
        <p className="text-sm text-muted-foreground text-center">
          {user.last_message_at
            ? `Last active: ${formatDate(user.last_message_at)}`
            : "No session activity yet"}
        </p>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function UserDetailTabs({ user }: UserDetailTabsProps) {
  return (
    <Tabs defaultValue="overview" className="w-full">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="credits">Credits</TabsTrigger>
        <TabsTrigger value="activity">Activity</TabsTrigger>
        <TabsTrigger value="sessions">Sessions</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-4">
        <OverviewTab user={user} />
      </TabsContent>
      <TabsContent value="credits" className="mt-4">
        <CreditsTab user={user} />
      </TabsContent>
      <TabsContent value="activity" className="mt-4">
        <ActivityTab userId={user.id} />
      </TabsContent>
      <TabsContent value="sessions" className="mt-4">
        <SessionsTab user={user} />
      </TabsContent>
    </Tabs>
  );
}
