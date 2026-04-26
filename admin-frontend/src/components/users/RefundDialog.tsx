"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRefundPayment } from "@/hooks/useBilling";

interface RefundPayment {
  id: string;
  amount_cents: number;
  credit_amount: number | null;
  payment_type: string;
  stripe_payment_intent_id: string | null;
}

interface RefundDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  payment: RefundPayment | null;
}

export function RefundDialog({
  open,
  onOpenChange,
  userId,
  payment,
}: RefundDialogProps) {
  const [amountCents, setAmountCents] = useState(0);
  const refundPayment = useRefundPayment();

  useEffect(() => {
    if (payment) {
      setAmountCents(payment.amount_cents);
    }
  }, [payment]);

  if (!payment) return null;

  const creditDeduction = payment.credit_amount
    ? (amountCents / payment.amount_cents) * payment.credit_amount
    : 0;

  const isValid = amountCents > 0 && amountCents <= payment.amount_cents;

  const handleSubmit = async () => {
    try {
      await refundPayment.mutateAsync({
        userId,
        payment_id: payment.id,
        amount_cents: amountCents,
      });
      toast.success("Refund issued");
      onOpenChange(false);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const handleOpenChange = (value: boolean) => {
    if (!value) {
      setAmountCents(payment.amount_cents);
    }
    onOpenChange(value);
  };

  const refundDollars = `$${(amountCents / 100).toFixed(2)}`;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Issue Refund</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Payment type</span>
              <span>{payment.payment_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Original amount</span>
              <span className="font-mono">
                ${(payment.amount_cents / 100).toFixed(2)}
              </span>
            </div>
            {payment.stripe_payment_intent_id && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Stripe ID</span>
                <span className="font-mono text-xs">
                  {payment.stripe_payment_intent_id}
                </span>
              </div>
            )}
          </div>

          <div>
            <Label htmlFor="refund-amount">Refund Amount (cents)</Label>
            <Input
              id="refund-amount"
              type="number"
              min={1}
              max={payment.amount_cents}
              value={amountCents}
              onChange={(e) => setAmountCents(Number(e.target.value))}
              className="mt-1.5"
            />
          </div>

          {payment.credit_amount !== null && payment.credit_amount > 0 && (
            <p className="text-sm text-muted-foreground">
              Credits to deduct: {creditDeduction.toFixed(1)}
            </p>
          )}

          <p className="text-sm text-muted-foreground">
            Refund {refundDollars} for this payment?{" "}
            {payment.credit_amount
              ? `${creditDeduction.toFixed(1)} purchased credits will be deducted from the user's balance. `
              : ""}
            This triggers a Stripe refund.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleSubmit}
            disabled={!isValid || refundPayment.isPending}
          >
            {refundPayment.isPending ? "Processing..." : "Issue Refund"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
