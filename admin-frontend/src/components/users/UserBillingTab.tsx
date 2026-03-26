"use client";

import { useState } from "react";
import { toast } from "sonner";
import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import {
  useUserBillingDetail,
  useAdminCancelSubscription,
} from "@/hooks/useBilling";
import { ForceSetTierDialog } from "./ForceSetTierDialog";
import { RefundDialog } from "./RefundDialog";
import type { UserDetail } from "@/types/user";

interface UserBillingTabProps {
  user: UserDetail;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTimestamp(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function UserBillingTab({ user }: UserBillingTabProps) {
  const { data, isLoading, isError, refetch } = useUserBillingDetail(user.id);
  const cancelSubscription = useAdminCancelSubscription();

  const [showForceSetTier, setShowForceSetTier] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [refundPayment, setRefundPayment] = useState<
    | {
        id: string;
        amount_cents: number;
        credit_amount: number | null;
        payment_type: string;
        stripe_payment_intent_id: string | null;
      }
    | null
  >(null);

  // Pagination state
  const [paymentLimit, setPaymentLimit] = useState(20);
  const [eventLimit, setEventLimit] = useState(50);

  const handleCancelSubscription = async () => {
    try {
      await cancelSubscription.mutateAsync({ userId: user.id });
      toast.success("Subscription cancelled");
    } catch (e: any) {
      toast.error(e.message);
    }
    setShowCancelConfirm(false);
  };

  if (isError) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground space-y-3">
          <p>Failed to load data. Check your connection and try again.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Section 1: Subscription Status Card */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            Subscription
            {data && (
              <StatusBadge
                type="status"
                value={data.subscription.status || "none"}
              />
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : data?.subscription.has_subscription ? (
            <div className="space-y-4">
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div className="flex justify-between sm:flex-col sm:gap-0.5">
                  <span className="text-muted-foreground">Plan</span>
                  <span className="font-medium">
                    {data.subscription.plan_tier || "-"}
                  </span>
                </div>
                <div className="flex justify-between sm:flex-col sm:gap-0.5">
                  <span className="text-muted-foreground">Status</span>
                  <span className="font-medium">
                    {data.subscription.status || "-"}
                  </span>
                </div>
                <div className="flex justify-between sm:flex-col sm:gap-0.5">
                  <span className="text-muted-foreground">Period</span>
                  <span className="font-medium">
                    {formatDate(data.subscription.current_period_start)} &ndash;{" "}
                    {formatDate(data.subscription.current_period_end)}
                  </span>
                </div>
                <div className="flex justify-between sm:flex-col sm:gap-0.5">
                  <span className="text-muted-foreground">
                    Stripe Customer
                  </span>
                  {data.subscription.stripe_customer_id ? (
                    <a
                      href={`https://dashboard.stripe.com/customers/${data.subscription.stripe_customer_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline font-mono text-xs inline-flex items-center gap-1"
                    >
                      {data.subscription.stripe_customer_id}
                      <ExternalLink className="size-3" />
                    </a>
                  ) : (
                    <span className="font-medium">-</span>
                  )}
                </div>
              </div>

              {data.subscription.cancel_at_period_end && (
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  Subscription will cancel at end of current period.
                </p>
              )}

              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() => setShowForceSetTier(true)}
                >
                  Force Set Tier
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => setShowCancelConfirm(true)}
                >
                  Cancel Subscription
                </Button>
                {data.subscription.stripe_subscription_id && (
                  <Button size="sm" variant="outline" asChild>
                    <a
                      href={`https://dashboard.stripe.com/subscriptions/${data.subscription.stripe_subscription_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View in Stripe
                      <ExternalLink className="size-3 ml-1" />
                    </a>
                  </Button>
                )}
                <Button size="sm" variant="outline" disabled>
                  Initiate Refund
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-4 text-center text-sm">
              <p className="font-medium">No active subscription</p>
              <p className="text-muted-foreground mt-1">
                This user is on the On Demand plan with no Stripe subscription.
              </p>
              <div className="flex justify-center gap-2 mt-4">
                <Button
                  size="sm"
                  onClick={() => setShowForceSetTier(true)}
                >
                  Force Set Tier
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Section 2: Payment History Card */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payment History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !data || data.payments.length === 0 ? (
            <div className="py-4 text-center text-sm">
              <p className="font-medium">No payments yet</p>
              <p className="text-muted-foreground mt-1">
                This user has no payment history.
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Credits</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Stripe ID</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.payments.slice(0, paymentLimit).map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell className="text-muted-foreground">
                        {formatDate(payment.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {payment.payment_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        ${(payment.amount_cents / 100).toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {payment.credit_amount != null
                          ? payment.credit_amount
                          : "-"}
                      </TableCell>
                      <TableCell>
                        <StatusBadge
                          type="status"
                          value={payment.status === "succeeded" ? "active" : "inactive"}
                        />
                      </TableCell>
                      <TableCell>
                        {payment.stripe_payment_intent_id ? (
                          <span className="font-mono text-xs truncate max-w-[120px] inline-block">
                            {payment.stripe_payment_intent_id}
                          </span>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>
                        {payment.status === "succeeded" &&
                        payment.stripe_payment_intent_id ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() =>
                              setRefundPayment({
                                id: payment.id,
                                amount_cents: payment.amount_cents,
                                credit_amount: payment.credit_amount,
                                payment_type: payment.payment_type,
                                stripe_payment_intent_id:
                                  payment.stripe_payment_intent_id,
                              })
                            }
                          >
                            Refund
                          </Button>
                        ) : null}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {data.payments.length > paymentLimit && (
                <div className="mt-4 text-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPaymentLimit((l) => l + 20)}
                  >
                    Load More
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Section 3: Stripe Event Log Card */}
      {/* ----------------------------------------------------------------- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Stripe Events</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !data || data.stripe_events.length === 0 ? (
            <div className="py-4 text-center text-sm">
              <p className="font-medium">No Stripe events</p>
              <p className="text-muted-foreground mt-1">
                No webhook events have been recorded for this user.
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Event Type</TableHead>
                    <TableHead>Event ID</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.stripe_events.slice(0, eventLimit).map((event) => (
                    <TableRow key={event.id}>
                      <TableCell className="text-muted-foreground">
                        {formatTimestamp(event.processed_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {event.event_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-xs truncate max-w-[160px] inline-block">
                          {event.stripe_event_id}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-400 border-transparent"
                        >
                          processed
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {data.stripe_events.length > eventLimit && (
                <div className="mt-4 text-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEventLimit((l) => l + 50)}
                  >
                    Load More
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ----------------------------------------------------------------- */}
      {/* Dialogs */}
      {/* ----------------------------------------------------------------- */}
      <ForceSetTierDialog
        open={showForceSetTier}
        onOpenChange={setShowForceSetTier}
        userId={user.id}
        currentTier={data?.subscription.plan_tier || user.user_class}
      />

      <RefundDialog
        open={!!refundPayment}
        onOpenChange={(v) => {
          if (!v) setRefundPayment(null);
        }}
        userId={user.id}
        payment={refundPayment}
      />

      <ConfirmModal
        open={showCancelConfirm}
        onClose={() => setShowCancelConfirm(false)}
        onConfirm={handleCancelSubscription}
        title="Cancel Subscription"
        description={`Cancel ${user.email}'s subscription? Access continues until the end of the current billing period. Purchased credits are preserved.`}
        confirmLabel="Cancel Subscription"
        variant="destructive"
        loading={cancelSubscription.isPending}
      />
    </div>
  );
}
