"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { CreateDiscountDialog } from "@/components/discounts/CreateDiscountDialog";
import {
  useDiscountCodes,
  useDeactivateDiscountCode,
  useDeleteDiscountCode,
} from "@/hooks/useDiscountCodes";
import type { DiscountCode } from "@/hooks/useDiscountCodes";

export default function DiscountCodesPage() {
  const { data, isLoading, error, refetch } = useDiscountCodes();
  const deactivateMutation = useDeactivateDiscountCode();
  const deleteMutation = useDeleteDiscountCode();

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCode, setEditingCode] = useState<DiscountCode | null>(null);

  // Confirm modal state
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    description: string;
    action: "deactivate" | "delete";
    codeId: string;
  }>({ open: false, title: "", description: "", action: "deactivate", codeId: "" });

  function handleCreate() {
    setEditingCode(null);
    setDialogOpen(true);
  }

  function handleEdit(code: DiscountCode) {
    setEditingCode(code);
    setDialogOpen(true);
  }

  function handleDialogChange(open: boolean) {
    setDialogOpen(open);
    if (!open) setEditingCode(null);
  }

  function handleDeactivate(code: DiscountCode) {
    setConfirmModal({
      open: true,
      title: "Deactivate Discount Code",
      description: `Deactivate code '${code.code}'? Users will no longer be able to apply this code at checkout.`,
      action: "deactivate",
      codeId: code.id,
    });
  }

  function handleDelete(code: DiscountCode) {
    setConfirmModal({
      open: true,
      title: "Delete Discount Code",
      description: `Permanently delete code '${code.code}'? This cannot be undone. The Stripe coupon will also be deleted.`,
      action: "delete",
      codeId: code.id,
    });
  }

  async function handleConfirm() {
    try {
      if (confirmModal.action === "deactivate") {
        await deactivateMutation.mutateAsync(confirmModal.codeId);
        toast.success("Discount code deactivated");
      } else {
        await deleteMutation.mutateAsync(confirmModal.codeId);
        toast.success("Discount code deleted");
      }
      setConfirmModal((prev) => ({ ...prev, open: false }));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Operation failed");
    }
  }

  function formatAmount(code: DiscountCode): string {
    if (code.discount_type === "percent_off") {
      return `${code.discount_value}%`;
    }
    return `$${(code.discount_value / 100).toFixed(2)}`;
  }

  function formatExpiry(expiresAt: string | null): string {
    if (!expiresAt) return "Never";
    return new Date(expiresAt).toLocaleDateString();
  }

  const codes = data?.items ?? [];
  const isConfirmPending =
    deactivateMutation.isPending || deleteMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-semibold">Discount Codes</h2>
        <Button onClick={handleCreate}>Create Discount Code</Button>
      </div>

      {/* Table card */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-6">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center gap-4 py-20">
              <p className="text-sm text-muted-foreground">
                Failed to load data. Check your connection and try again.
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : codes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <p className="text-lg font-medium">No discount codes yet</p>
              <p className="text-sm text-muted-foreground">
                Create your first discount code to offer promotions to users.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Uses</TableHead>
                  <TableHead>Expiry</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {codes.map((code) => (
                  <TableRow key={code.id}>
                    <TableCell className="font-mono font-medium">
                      {code.code}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {code.discount_type === "percent_off"
                          ? "Percentage"
                          : "Fixed Amount"}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatAmount(code)}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          code.is_active
                            ? "border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-400"
                            : "border-transparent bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-400"
                        }
                      >
                        {code.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {code.times_redeemed}/
                      {code.max_redemptions ?? "unlimited"}
                    </TableCell>
                    <TableCell>{formatExpiry(code.expires_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(code)}
                        >
                          Edit
                        </Button>
                        {code.is_active && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeactivate(code)}
                          >
                            Deactivate
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDelete(code)}
                        >
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit dialog */}
      <CreateDiscountDialog
        open={dialogOpen}
        onOpenChange={handleDialogChange}
        initialValues={
          editingCode
            ? {
                id: editingCode.id,
                code: editingCode.code,
                discount_type: editingCode.discount_type,
                discount_value: editingCode.discount_value,
                max_redemptions: editingCode.max_redemptions,
                expires_at: editingCode.expires_at,
              }
            : null
        }
      />

      {/* Confirm modal for deactivate/delete */}
      <ConfirmModal
        open={confirmModal.open}
        onClose={() => setConfirmModal((prev) => ({ ...prev, open: false }))}
        onConfirm={handleConfirm}
        title={confirmModal.title}
        description={confirmModal.description}
        confirmLabel={
          confirmModal.action === "deactivate" ? "Deactivate" : "Delete"
        }
        variant="destructive"
        loading={isConfirmPending}
      />
    </div>
  );
}
