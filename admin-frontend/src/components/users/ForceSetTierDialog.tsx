"use client";

import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useForceSetTier } from "@/hooks/useBilling";
import { useTiers } from "@/hooks/useTiers";

interface ForceSetTierDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  currentTier: string;
}

export function ForceSetTierDialog({
  open,
  onOpenChange,
  userId,
  currentTier,
}: ForceSetTierDialogProps) {
  const [newTier, setNewTier] = useState("");
  const [reason, setReason] = useState("");
  const { data: tiers } = useTiers();
  const forceSetTier = useForceSetTier();

  const handleSubmit = async () => {
    try {
      await forceSetTier.mutateAsync({
        userId,
        new_tier: newTier,
        reason: reason.trim(),
      });
      toast.success(`Tier changed to ${newTier}`);
      setNewTier("");
      setReason("");
      onOpenChange(false);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const handleOpenChange = (value: boolean) => {
    if (!value) {
      setNewTier("");
      setReason("");
    }
    onOpenChange(value);
  };

  const isDisabled =
    !newTier || newTier === currentTier || !reason.trim() || forceSetTier.isPending;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Force Set Tier</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Current tier:</span>
            <StatusBadge type="tier" value={currentTier} />
          </div>

          <div>
            <Label htmlFor="new-tier">New Tier</Label>
            <Select value={newTier} onValueChange={setNewTier}>
              <SelectTrigger className="mt-1.5" id="new-tier">
                <SelectValue placeholder="Select tier" />
              </SelectTrigger>
              <SelectContent>
                {tiers
                  ?.filter((t) => t.name !== currentTier)
                  .map((tier) => (
                    <SelectItem key={tier.name} value={tier.name}>
                      {tier.display_name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="tier-reason">Reason</Label>
            <Input
              id="tier-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Reason for tier change"
              className="mt-1.5"
            />
          </div>

          <p className="text-sm text-muted-foreground">
            Stripe subscription will be updated to match. If setting to On
            Demand, any active subscription will be cancelled.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isDisabled}
          >
            {forceSetTier.isPending ? "Processing..." : "Force Set Tier"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
