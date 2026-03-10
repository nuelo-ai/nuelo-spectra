"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useDeleteCollection } from "@/hooks/useWorkspace";
import { toast } from "sonner";
import type { CollectionListItem } from "@/types/workspace";

interface DeleteCollectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  collection: CollectionListItem | null;
  onSuccess?: () => void;
}

export function DeleteCollectionDialog({
  open,
  onOpenChange,
  collection,
  onSuccess,
}: DeleteCollectionDialogProps) {
  const deleteMutation = useDeleteCollection();

  async function handleDelete() {
    if (!collection) return;
    try {
      await deleteMutation.mutateAsync(collection.id);
      toast.success("Collection deleted");
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete collection";
      toast.error(message);
    }
  }

  function handleCancel() {
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Collection</DialogTitle>
          <DialogDescription asChild>
            <div>
              <span>Are you sure you want to delete </span>
              <strong>{collection?.name}</strong>
              <span>? This will permanently remove all signals, reports, and detection runs in this collection.</span>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="ghost" onClick={handleCancel} disabled={deleteMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
