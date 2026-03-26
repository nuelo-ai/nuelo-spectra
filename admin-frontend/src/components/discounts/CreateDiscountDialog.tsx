"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import {
  useCreateDiscountCode,
  useUpdateDiscountCode,
} from "@/hooks/useDiscountCodes";

interface DiscountCodeInitialValues {
  id: string;
  code: string;
  discount_type: "percent_off" | "amount_off";
  discount_value: number;
  max_redemptions: number | null;
  expires_at: string | null;
}

interface CreateDiscountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialValues?: DiscountCodeInitialValues | null;
}

export function CreateDiscountDialog({
  open,
  onOpenChange,
  initialValues,
}: CreateDiscountDialogProps) {
  const isEditMode = !!initialValues;

  const [code, setCode] = useState("");
  const [discountType, setDiscountType] = useState<
    "percent_off" | "amount_off"
  >("percent_off");
  const [discountValue, setDiscountValue] = useState("");
  const [maxRedemptions, setMaxRedemptions] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  const createMutation = useCreateDiscountCode();
  const updateMutation = useUpdateDiscountCode();

  // Pre-fill form in edit mode
  useEffect(() => {
    if (initialValues) {
      setCode(initialValues.code);
      setDiscountType(initialValues.discount_type);
      setDiscountValue(String(initialValues.discount_value));
      setMaxRedemptions(
        initialValues.max_redemptions != null
          ? String(initialValues.max_redemptions)
          : ""
      );
      setExpiresAt(
        initialValues.expires_at
          ? initialValues.expires_at.split("T")[0]
          : ""
      );
    } else {
      resetForm();
    }
  }, [initialValues]);

  function resetForm() {
    setCode("");
    setDiscountType("percent_off");
    setDiscountValue("");
    setMaxRedemptions("");
    setExpiresAt("");
  }

  function validate(): string | null {
    if (!isEditMode) {
      if (!code.trim()) return "Code is required";
      if (!/^[A-Z0-9_-]+$/.test(code.toUpperCase()))
        return "Code must be alphanumeric (hyphens and underscores allowed)";
      const val = Number(discountValue);
      if (!discountValue || isNaN(val) || val <= 0)
        return "Discount value must be greater than 0";
      if (discountType === "percent_off" && val > 100)
        return "Percentage cannot exceed 100";
    }

    if (maxRedemptions) {
      const mr = Number(maxRedemptions);
      if (isNaN(mr) || mr < 1)
        return "Max redemptions must be at least 1";
    }

    if (expiresAt) {
      const expiry = new Date(expiresAt);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (expiry < today) return "Expiry date must be in the future";
    }

    return null;
  }

  async function handleSubmit() {
    const error = validate();
    if (error) {
      toast.error(error);
      return;
    }

    try {
      if (isEditMode && initialValues) {
        await updateMutation.mutateAsync({
          codeId: initialValues.id,
          max_redemptions: maxRedemptions ? Number(maxRedemptions) : null,
          expires_at: expiresAt || null,
        });
        toast.success("Discount code updated");
      } else {
        await createMutation.mutateAsync({
          code: code.toUpperCase(),
          discount_type: discountType,
          discount_value: Number(discountValue),
          ...(maxRedemptions ? { max_redemptions: Number(maxRedemptions) } : {}),
          ...(expiresAt ? { expires_at: expiresAt } : {}),
        });
        toast.success("Discount code created");
        resetForm();
      }
      onOpenChange(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Operation failed");
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Discount Code" : "Create Discount Code"}
          </DialogTitle>
          <DialogDescription>
            {isEditMode
              ? "Update redemption limits and expiry for this discount code."
              : "Create a new discount code synced with Stripe Coupons."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Code */}
          <div className="space-y-2">
            <Label htmlFor="discount-code">Code</Label>
            <Input
              id="discount-code"
              placeholder="e.g. SUMMER2026"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              disabled={isEditMode}
              className={isEditMode ? "text-muted-foreground" : ""}
            />
          </div>

          {/* Type */}
          <div className="space-y-2">
            <Label htmlFor="discount-type">Type</Label>
            <Select
              value={discountType}
              onValueChange={(v) =>
                setDiscountType(v as "percent_off" | "amount_off")
              }
              disabled={isEditMode}
            >
              <SelectTrigger
                id="discount-type"
                className={isEditMode ? "text-muted-foreground" : ""}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="percent_off">Percentage Off</SelectItem>
                <SelectItem value="amount_off">Fixed Amount Off</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Value */}
          <div className="space-y-2">
            <Label htmlFor="discount-value">
              {discountType === "percent_off"
                ? "Percentage (%)"
                : "Amount (cents)"}
            </Label>
            <Input
              id="discount-value"
              type="number"
              min={1}
              max={discountType === "percent_off" ? 100 : undefined}
              placeholder={
                discountType === "percent_off" ? "e.g. 20" : "e.g. 500"
              }
              value={discountValue}
              onChange={(e) => setDiscountValue(e.target.value)}
              disabled={isEditMode}
              className={isEditMode ? "text-muted-foreground" : ""}
            />
          </div>

          {/* Max Redemptions */}
          <div className="space-y-2">
            <Label htmlFor="max-redemptions">Max Redemptions</Label>
            <Input
              id="max-redemptions"
              type="number"
              min={1}
              placeholder="Unlimited if empty"
              value={maxRedemptions}
              onChange={(e) => setMaxRedemptions(e.target.value)}
            />
          </div>

          {/* Expiry Date */}
          <div className="space-y-2">
            <Label htmlFor="expires-at">Expires At (optional)</Label>
            <Input
              id="expires-at"
              type="date"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending}>
            {isPending
              ? "Processing..."
              : isEditMode
              ? "Save Changes"
              : "Create Discount Code"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
