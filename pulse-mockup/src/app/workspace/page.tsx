"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CollectionList } from "@/components/workspace/collection-list";
import { MOCK_COLLECTIONS } from "@/lib/mock-data";

export default function WorkspacePage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Collections</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your data collections and detect signals
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="shrink-0">
          <Plus className="h-4 w-4 mr-2" />
          Create Collection
        </Button>
      </div>

      {/* Collection grid */}
      <CollectionList
        collections={MOCK_COLLECTIONS}
        onCreateClick={() => setDialogOpen(true)}
      />
    </div>
  );
}
