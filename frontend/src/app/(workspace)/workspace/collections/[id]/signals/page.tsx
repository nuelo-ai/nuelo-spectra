"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { SignalListPanel } from "@/components/workspace/signal-list-panel";
import { SignalDetailPanel } from "@/components/workspace/signal-detail-panel";
import {
  useCollectionSignals,
  useCollectionDetail,
  useCollectionFiles,
} from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/lib/utils";
import type { SignalDetail } from "@/types/workspace";

const severityOrder: Record<SignalDetail["severity"], number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

export default function DetectionResultsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const selectedFromUrl = searchParams.get("selected");

  const { data: collection } = useCollectionDetail(id);
  const {
    data: signals,
    isLoading,
    isError,
    refetch,
  } = useCollectionSignals(id);

  const selectedSignalId = useWorkspaceStore((s) => s.selectedSignalId);
  const setSelectedSignalId = useWorkspaceStore((s) => s.setSelectedSignalId);

  // Sort signals by severity
  const sortedSignals = signals
    ? [...signals].sort(
        (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
      )
    : [];

  // Select signal from URL param, or auto-select highest severity
  useEffect(() => {
    if (sortedSignals.length > 0) {
      if (selectedFromUrl && sortedSignals.some((s) => s.id === selectedFromUrl)) {
        setSelectedSignalId(selectedFromUrl);
      } else if (!selectedSignalId) {
        setSelectedSignalId(sortedSignals[0].id);
      }
    }
  }, [sortedSignals.length, selectedFromUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedSignal =
    sortedSignals.find((s) => s.id === selectedSignalId) ?? null;

  const [showDetail, setShowDetail] = useState(false);
  const { data: collectionFiles = [] } = useCollectionFiles(id);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b border-border flex items-center gap-3">
          <SidebarTrigger className="-ml-1" />
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-5 w-48" />
        </div>
        <div className="flex flex-1 overflow-hidden">
          <div className="w-[350px] shrink-0 border-r border-border p-2 space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-lg" />
            ))}
          </div>
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-[300px] w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b border-border flex items-center gap-3">
          <SidebarTrigger className="-ml-1" />
          <Link
            href={`/workspace/collections/${id}`}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Collection
          </Link>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <AlertTriangle className="h-10 w-10 text-severity-warning mx-auto" />
            <p className="text-sm text-muted-foreground">
              Failed to load signals
            </p>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (sortedSignals.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b border-border flex items-center gap-3">
          <SidebarTrigger className="-ml-1" />
          <Link
            href={`/workspace/collections/${id}`}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Collection
          </Link>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <p className="text-sm font-medium">No signals detected</p>
            <p className="text-xs text-muted-foreground">
              Run Pulse detection on your collection files to generate signals.
            </p>
            <Link href={`/workspace/collections/${id}`}>
              <Button size="sm" variant="outline">
                Go to Files
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center gap-3">
        <SidebarTrigger className="-ml-1" />
        <Link
          href={`/workspace/collections/${id}`}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-sm font-semibold">Detection Results</h1>
          {collection && (
            <p className="text-xs text-muted-foreground">{collection.name}</p>
          )}
        </div>
      </div>

      {/* Split Panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* List panel: hidden on mobile when detail is shown */}
        <div className={cn(
          "w-[350px] shrink-0 border-r border-border flex flex-col h-full",
          showDetail ? "hidden sm:flex" : "flex"
        )}>
          <SignalListPanel
            signals={sortedSignals}
            selectedId={selectedSignalId}
            onSelect={(id) => {
              setSelectedSignalId(id);
              setShowDetail(true);
            }}
          />
        </div>
        {/* Detail panel: hidden on mobile when list is shown */}
        <div className={cn(
          "flex-1 overflow-hidden",
          showDetail ? "flex" : "hidden sm:flex"
        )}>
          <SignalDetailPanel
            signal={selectedSignal}
            onBack={() => setShowDetail(false)}
            collectionFiles={collectionFiles}
            collectionId={id}
          />
        </div>
      </div>
    </div>
  );
}
