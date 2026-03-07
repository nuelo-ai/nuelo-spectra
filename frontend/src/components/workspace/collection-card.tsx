"use client";

import Link from "next/link";
import { Calendar, BarChart3, FileText } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import type { CollectionListItem } from "@/types/workspace";

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface CollectionCardProps {
  collection: CollectionListItem;
}

export function CollectionCard({ collection }: CollectionCardProps) {
  return (
    <Link href={`/workspace/collections/${collection.id}`} className="group">
      <Card className="h-full transition-all duration-200 hover:border-primary/40 hover:shadow-md hover:shadow-primary/5 cursor-pointer">
        <CardHeader className="pb-0 gap-3">
          <CardTitle className="text-base leading-snug line-clamp-2">
            {collection.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 pb-0">
          {collection.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {collection.description}
            </p>
          )}
        </CardContent>
        <CardFooter className="mt-auto pt-0">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              {formatDate(collection.created_at)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              {collection.signal_count} signals
            </span>
            <span className="inline-flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              {collection.file_count} files
            </span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
