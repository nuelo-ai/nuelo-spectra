"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
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
import { Textarea } from "@/components/ui/textarea";
import { useCreateCollection, useUpdateCollection } from "@/hooks/useWorkspace";
import { FolderX } from "lucide-react";
import { toast } from "sonner";
import type { CollectionListItem } from "@/types/workspace";

interface CreateCollectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  collection?: CollectionListItem;  // when present: edit mode
}

export function CreateCollectionDialog({
  open,
  onOpenChange,
  collection,
}: CreateCollectionDialogProps) {
  const router = useRouter();
  const [name, setName] = useState(collection?.name ?? "");
  const [description, setDescription] = useState(collection?.description ?? "");
  const [collectionLimit, setCollectionLimit] = useState<number | null>(null);
  const createMutation = useCreateCollection();
  const updateMutation = useUpdateCollection(collection?.id ?? "");

  const isEditMode = !!collection;

  useEffect(() => {
    if (open) {
      setName(collection?.name ?? "");
      setDescription(collection?.description ?? "");
    }
  }, [open, collection]);

  async function handleSubmit() {
    if (!name.trim()) return;
    if (isEditMode) {
      try {
        await updateMutation.mutateAsync({
          name: name.trim(),
          description: description.trim() || undefined,
        });
        toast.success("Collection updated");
        onOpenChange(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to update collection";
        toast.error(message);
      }
    } else {
      try {
        const created = await createMutation.mutateAsync({
          name: name.trim(),
          description: description.trim() || undefined,
        });
        onOpenChange(false);
        setName("");
        setDescription("");
        router.push(`/workspace/collections/${created.id}`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "";
        const match = message.match(/Collection limit reached \((\d+)/);
        if (match) {
          onOpenChange(false);
          setCollectionLimit(Number(match[1]));
        }
      }
    }
  }

  function handleCancel() {
    onOpenChange(false);
    setName("");
    setDescription("");
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{isEditMode ? "Edit Collection" : "Create New Collection"}</DialogTitle>
            <DialogDescription>
              A collection groups your data files for signal detection analysis.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label
                htmlFor="collection-name"
                className="text-sm font-medium leading-none"
              >
                Name <span className="text-destructive">*</span>
              </label>
              <Input
                id="collection-name"
                placeholder="e.g., Q3 Sales Analysis"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="collection-description"
                className="text-sm font-medium leading-none"
              >
                Description{" "}
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </label>
              <Textarea
                id="collection-description"
                placeholder="Describe the purpose of this collection..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="ghost" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!name.trim() || (isEditMode ? updateMutation.isPending : createMutation.isPending)}
            >
              {isEditMode
                ? (updateMutation.isPending ? "Saving..." : "Save")
                : (createMutation.isPending ? "Creating..." : "Create")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={collectionLimit !== null}
        onOpenChange={(open) => { if (!open) setCollectionLimit(null); }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-1">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <FolderX className="h-5 w-5 text-destructive" />
              </div>
              <DialogTitle>Collection Limit Reached</DialogTitle>
            </div>
            <DialogDescription>
              Your current plan allows a maximum of{" "}
              <span className="font-medium text-foreground">
                {collectionLimit} collection{collectionLimit === 1 ? "" : "s"}
              </span>
              . To create a new collection, please delete an existing one first.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setCollectionLimit(null)}>Got it</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
