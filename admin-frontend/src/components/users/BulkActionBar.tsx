"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { ChallengeCodeDialog } from "@/components/shared/ChallengeCodeDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useBulkActivate,
  useBulkDeactivate,
  useBulkChangeTier,
  useBulkAdjustCredits,
  useBulkDelete,
  useBulkDeleteChallenge,
} from "@/hooks/useUsers";
import { useTiers } from "@/hooks/useTiers";
import { toast } from "sonner";

interface BulkActionBarProps {
  selectedIds: string[];
  onClearSelection: () => void;
}

export function BulkActionBar({
  selectedIds,
  onClearSelection,
}: BulkActionBarProps) {
  const [confirmAction, setConfirmAction] = useState<
    "activate" | "deactivate" | null
  >(null);
  const [showTierDialog, setShowTierDialog] = useState(false);
  const [showCreditDialog, setShowCreditDialog] = useState(false);
  const [showDeleteChallenge, setShowDeleteChallenge] = useState(false);
  const [selectedTier, setSelectedTier] = useState("free");
  const [creditDelta, setCreditDelta] = useState("");
  const [creditReason, setCreditReason] = useState("");

  const { data: tiers } = useTiers();
  const bulkActivate = useBulkActivate();
  const bulkDeactivate = useBulkDeactivate();
  const bulkChangeTier = useBulkChangeTier();
  const bulkAdjustCredits = useBulkAdjustCredits();
  const bulkDelete = useBulkDelete();
  const bulkDeleteChallenge = useBulkDeleteChallenge();

  const count = selectedIds.length;
  if (count === 0) return null;

  const handleBulkActivate = async () => {
    try {
      const result = await bulkActivate.mutateAsync({ user_ids: selectedIds });
      toast.success(`Activated ${result.succeeded} users`);
      onClearSelection();
    } catch (e: any) {
      toast.error(e.message);
    }
    setConfirmAction(null);
  };

  const handleBulkDeactivate = async () => {
    try {
      const result = await bulkDeactivate.mutateAsync({ user_ids: selectedIds });
      toast.success(`Deactivated ${result.succeeded} users`);
      onClearSelection();
    } catch (e: any) {
      toast.error(e.message);
    }
    setConfirmAction(null);
  };

  const handleBulkTierChange = async () => {
    try {
      const result = await bulkChangeTier.mutateAsync({
        user_ids: selectedIds,
        user_class: selectedTier,
      });
      toast.success(`Changed tier for ${result.succeeded} users`);
      onClearSelection();
    } catch (e: any) {
      toast.error(e.message);
    }
    setShowTierDialog(false);
  };

  const handleBulkCreditAdjust = async () => {
    const delta = parseFloat(creditDelta);
    if (isNaN(delta) || !creditReason.trim()) {
      toast.error("Enter a valid amount and reason");
      return;
    }
    try {
      const result = await bulkAdjustCredits.mutateAsync({
        user_ids: selectedIds,
        delta,
        reason: creditReason.trim(),
      });
      toast.success(`Adjusted credits for ${result.succeeded} users`);
      onClearSelection();
    } catch (e: any) {
      toast.error(e.message);
    }
    setShowCreditDialog(false);
    setCreditDelta("");
    setCreditReason("");
  };

  const handleFetchBulkDeleteChallenge = async () => {
    return bulkDeleteChallenge.mutateAsync(selectedIds);
  };

  const handleBulkDelete = async (challengeCode: string) => {
    try {
      const result = await bulkDelete.mutateAsync({
        user_ids: selectedIds,
        challenge_code: challengeCode,
      });
      toast.success(`Deleted ${result.succeeded} users`);
      onClearSelection();
    } catch (e: any) {
      toast.error(e.message);
    }
    setShowDeleteChallenge(false);
  };

  return (
    <>
      <div className="sticky top-0 z-10 flex items-center gap-3 rounded-lg border bg-muted/80 px-4 py-3 backdrop-blur-sm">
        <span className="text-sm font-medium">
          {count} user{count !== 1 ? "s" : ""} selected
        </span>
        <div className="flex items-center gap-2 ml-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConfirmAction("activate")}
          >
            Activate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConfirmAction("deactivate")}
          >
            Deactivate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTierDialog(true)}
          >
            Change Tier
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCreditDialog(true)}
          >
            Adjust Credits
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteChallenge(true)}
          >
            Delete
          </Button>
          <Button variant="ghost" size="sm" onClick={onClearSelection}>
            Clear
          </Button>
        </div>
      </div>

      {/* Activate / Deactivate confirm */}
      <ConfirmModal
        open={confirmAction === "activate"}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleBulkActivate}
        title="Activate Users"
        description={`Are you sure you want to activate ${count} user${count !== 1 ? "s" : ""}?`}
        confirmLabel="Activate"
        loading={bulkActivate.isPending}
      />
      <ConfirmModal
        open={confirmAction === "deactivate"}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleBulkDeactivate}
        title="Deactivate Users"
        description={`Are you sure you want to deactivate ${count} user${count !== 1 ? "s" : ""}? They will be immediately logged out.`}
        confirmLabel="Deactivate"
        variant="destructive"
        loading={bulkDeactivate.isPending}
      />

      {/* Tier change dialog */}
      <Dialog open={showTierDialog} onOpenChange={setShowTierDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Tier</DialogTitle>
            <DialogDescription>
              Change tier for {count} selected user{count !== 1 ? "s" : ""}. This
              will reset their credit balance to the new tier allocation.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Label htmlFor="bulk-tier">New Tier</Label>
            <Select value={selectedTier} onValueChange={setSelectedTier}>
              <SelectTrigger id="bulk-tier" className="mt-1.5">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {tiers?.map((tier) => (
                  <SelectItem key={tier.name} value={tier.name}>
                    {tier.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTierDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleBulkTierChange} disabled={bulkChangeTier.isPending}>
              {bulkChangeTier.isPending ? "Processing..." : "Change Tier"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Credit adjust dialog */}
      <Dialog open={showCreditDialog} onOpenChange={setShowCreditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adjust Credits</DialogTitle>
            <DialogDescription>
              Adjust credits for {count} selected user{count !== 1 ? "s" : ""}.
              Use positive values to add, negative to deduct.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label htmlFor="bulk-credit-amount">Amount</Label>
              <Input
                id="bulk-credit-amount"
                type="number"
                value={creditDelta}
                onChange={(e) => setCreditDelta(e.target.value)}
                placeholder="e.g. 10 or -5"
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="bulk-credit-reason">Reason</Label>
              <Input
                id="bulk-credit-reason"
                value={creditReason}
                onChange={(e) => setCreditReason(e.target.value)}
                placeholder="Reason for adjustment"
                className="mt-1.5"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleBulkCreditAdjust} disabled={bulkAdjustCredits.isPending}>
              {bulkAdjustCredits.isPending ? "Processing..." : "Adjust Credits"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete challenge */}
      <ChallengeCodeDialog
        open={showDeleteChallenge}
        onClose={() => setShowDeleteChallenge(false)}
        onFetchChallenge={handleFetchBulkDeleteChallenge}
        onConfirm={handleBulkDelete}
        title="Delete Users"
        description={`This will permanently delete ${count} user${count !== 1 ? "s" : ""} and all their data. This action cannot be undone.`}
        loading={bulkDelete.isPending}
      />
    </>
  );
}
