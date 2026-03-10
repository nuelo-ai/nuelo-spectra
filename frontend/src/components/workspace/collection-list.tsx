"use client";

import { CollectionCard } from "./collection-card";
import { EmptyState } from "./empty-state";
import type { CollectionListItem } from "@/types/workspace";

interface CollectionListProps {
  collections: CollectionListItem[];
  onCreateClick: () => void;
  onRename: (collection: CollectionListItem) => void;
  onDelete: (collection: CollectionListItem) => void;
}

export function CollectionList({
  collections,
  onCreateClick,
  onRename,
  onDelete,
}: CollectionListProps) {
  if (collections.length === 0) {
    return <EmptyState onCreateClick={onCreateClick} />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {collections.map((collection) => (
        <CollectionCard
          key={collection.id}
          collection={collection}
          onRename={onRename}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
