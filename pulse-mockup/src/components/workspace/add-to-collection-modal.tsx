"use client";

import { useState } from "react";
import { Search, CheckCircle2, FolderPlus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MOCK_COLLECTIONS } from "@/lib/mock-data";

interface AddToCollectionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cardTitle: string; // Title of the result card being saved
  onSaved?: (collectionId: string) => void;
}

export function AddToCollectionModal({
  open,
  onOpenChange,
  cardTitle,
  onSaved,
}: AddToCollectionModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [savedToId, setSavedToId] = useState<string | null>(null);

  const activeCollections = MOCK_COLLECTIONS.filter(
    (c) => c.status === "active"
  );

  const filteredCollections = activeCollections.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAdd = (collectionId: string) => {
    setSavedToId(collectionId);
    onSaved?.(collectionId);
    setTimeout(() => {
      onOpenChange(false);
      // Reset state after modal closes
      setTimeout(() => {
        setSavedToId(null);
        setSearchQuery("");
      }, 200);
    }, 1500);
  };

  const savedCollection = savedToId
    ? MOCK_COLLECTIONS.find((c) => c.id === savedToId)
    : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add to Collection</DialogTitle>
          <DialogDescription>
            Save &ldquo;{cardTitle}&rdquo; to a collection
          </DialogDescription>
        </DialogHeader>

        {savedCollection ? (
          <div className="flex items-center gap-3 rounded-md border border-border bg-card px-4 py-3 my-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
            <p className="text-sm text-foreground">
              Saved to{" "}
              <span className="font-medium">{savedCollection.name}</span>
            </p>
          </div>
        ) : (
          <>
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search collections..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Collection list */}
            <div className="flex flex-col gap-1 max-h-64 overflow-y-auto">
              {filteredCollections.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  No active collections match your search
                </p>
              ) : (
                filteredCollections.map((collection) => (
                  <div
                    key={collection.id}
                    className="flex items-center justify-between px-3 py-2.5 rounded-md hover:bg-accent cursor-pointer border border-transparent hover:border-border transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm truncate">
                        {collection.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {collection.signalCount} signals &middot;{" "}
                        {collection.filesCount} files
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="ml-3 shrink-0"
                      onClick={() => handleAdd(collection.id)}
                    >
                      Add
                    </Button>
                  </div>
                ))
              )}
            </div>

            {/* Footer link */}
            <div className="pt-1 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                className="w-full gap-2 text-muted-foreground hover:text-foreground"
                asChild
              >
                <a href="/workspace/collections">
                  <FolderPlus className="h-4 w-4" />
                  + Create new collection
                </a>
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
