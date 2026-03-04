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
import { Badge } from "@/components/ui/badge";
import type { Collection } from "@/lib/mock-data";

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface CollectionCardProps {
  collection: Collection;
}

export function CollectionCard({ collection }: CollectionCardProps) {
  const isActive = collection.status === "active";

  return (
    <Link href={`/workspace/collections/${collection.id}`} className="group">
      <Card className="h-full transition-all duration-200 hover:border-primary/40 hover:shadow-md hover:shadow-primary/5 cursor-pointer">
        <CardHeader className="pb-0 gap-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base leading-snug line-clamp-2">
              {collection.name}
            </CardTitle>
            <Badge
              variant="secondary"
              className={
                isActive
                  ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/20"
                  : "bg-muted text-muted-foreground border-border"
              }
            >
              {isActive ? "Active" : "Archived"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0 pb-0">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {collection.description}
          </p>
        </CardContent>
        <CardFooter className="mt-auto pt-0">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              {formatDate(collection.createdAt)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              {collection.signalCount} signals
            </span>
            <span className="inline-flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              {collection.filesCount} files
            </span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
