"use client";

import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CollectionList } from "@/components/workspace/collection-list";
import { CreateCollectionDialog } from "@/components/workspace/create-collection-dialog";
import { DeleteCollectionDialog } from "@/components/workspace/delete-collection-dialog";
import { useCollections } from "@/hooks/useWorkspace";
import { SidebarTrigger } from "@/components/ui/sidebar";
import type { CollectionListItem } from "@/types/workspace";

export default function WorkspacePage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<CollectionListItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CollectionListItem | null>(null);
  const { data: collections, isLoading, isError, refetch } = useCollections();

  return (
    <div className="flex flex-col h-full">
      {/* Fixed header strip — SidebarTrigger only, no logo per anti-pattern in research */}
      <div className="px-4 py-3 shrink-0 border-b">
        <SidebarTrigger className="-ml-1" />
      </div>
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
      <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Collections</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your data collections for signal detection
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Collection
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-lg border bg-card p-6 space-y-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex gap-4 pt-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-24 px-4">
          <p className="text-sm text-muted-foreground mb-4">
            Failed to load collections
          </p>
          <Button variant="outline" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Try again
          </Button>
        </div>
      )}

      {!isLoading && !isError && collections && (
        <CollectionList
          collections={collections}
          onCreateClick={() => setCreateOpen(true)}
          onRename={(collection) => setRenameTarget(collection)}
          onDelete={(collection) => setDeleteTarget(collection)}
        />
      )}

      {/* Create dialog */}
      <CreateCollectionDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
      />

      {/* Rename dialog — edit mode */}
      <CreateCollectionDialog
        open={renameTarget !== null}
        onOpenChange={(open) => { if (!open) setRenameTarget(null); }}
        collection={renameTarget ?? undefined}
      />

      {/* Delete confirmation dialog */}
      <DeleteCollectionDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        collection={deleteTarget}
      />
    </div>
    </div>
    </div>
  );
}
