"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Zap, FileText, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useCollectionDetail,
  useCollectionFiles,
  useCollectionSignals,
  useCollectionReports,
  useTriggerPulse,
  usePulseStatus,
} from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { OverviewStatCards } from "@/components/workspace/overview-stat-cards";
import { RunDetectionBanner } from "@/components/workspace/run-detection-banner";
import { SignalCard } from "@/components/workspace/signal-card";
import { ActivityFeed } from "@/components/workspace/activity-feed";
import { DetectionLoading } from "@/components/workspace/detection-loading";
import { FileTable } from "@/components/workspace/file-table";
import { FileUploadZone } from "@/components/workspace/file-upload-zone";
import { DataSummaryPanel } from "@/components/workspace/data-summary-panel";
import { StickyActionBar } from "@/components/workspace/sticky-action-bar";
import type { CollectionFile, SignalDetail } from "@/types/workspace";

const CREDIT_COST = 5;
const severityOrder: Record<string, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

function sortBySeverity(signals: SignalDetail[]): SignalDetail[] {
  return [...signals].sort(
    (a, b) =>
      (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
  );
}

export default function CollectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const collectionId = params.id as string;

  // Data hooks
  const { data: collection, isLoading: loadingCollection } =
    useCollectionDetail(collectionId);
  const { data: files = [], isLoading: loadingFiles } =
    useCollectionFiles(collectionId);
  const {
    data: signals = [],
    isLoading: loadingSignals,
    refetch: refetchSignals,
  } = useCollectionSignals(collectionId);
  const { data: reports = [], isLoading: loadingReports } =
    useCollectionReports(collectionId);

  // Store
  const {
    selectedFileIds,
    toggleFileSelection,
    clearFileSelection,
    detectionStatus,
    setDetectionStatus,
    pulseRunId,
    setPulseRunId,
    setSelectedSignalId,
  } = useWorkspaceStore();

  // Pulse
  const triggerPulse = useTriggerPulse(collectionId);
  const { data: pulseRun } = usePulseStatus(collectionId, pulseRunId);

  // Local state
  const [activeTab, setActiveTab] = useState("overview");
  const [summaryFile, setSummaryFile] = useState<CollectionFile | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);

  // Sort signals by severity (SIGNAL-01)
  const sortedSignals = useMemo(() => sortBySeverity(signals), [signals]);

  // Auto-select highest severity signal (SIGNAL-02)
  useEffect(() => {
    if (sortedSignals.length > 0) {
      setSelectedSignalId(sortedSignals[0].id);
    }
  }, [sortedSignals, setSelectedSignalId]);

  // Monitor pulse status
  useEffect(() => {
    if (!pulseRun) return;
    if (pulseRun.status === "complete") {
      setDetectionStatus("complete");
      setPulseRunId(null);
      refetchSignals();
      setActiveTab("signals");
    } else if (pulseRun.status === "failed") {
      setDetectionStatus("failed");
      setPulseRunId(null);
    }
  }, [
    pulseRun,
    setDetectionStatus,
    setPulseRunId,
    refetchSignals,
  ]);

  // File selection handlers
  const handleSelectedChange = useCallback(
    (ids: string[]) => {
      // Clear and set all at once
      clearFileSelection();
      ids.forEach((id) => toggleFileSelection(id));
    },
    [clearFileSelection, toggleFileSelection]
  );

  const handleFileClick = useCallback((file: CollectionFile) => {
    setSummaryFile(file);
    setSummaryOpen(true);
  }, []);

  // Trigger detection
  const handleRunDetection = useCallback(async () => {
    if (selectedFileIds.length === 0) return;
    try {
      const result = await triggerPulse.mutateAsync({
        file_ids: selectedFileIds,
      });
      setPulseRunId(result.pulse_run_id);
      setDetectionStatus("running");
      clearFileSelection();
    } catch {
      // Error handled by TanStack Query
    }
  }, [
    selectedFileIds,
    triggerPulse,
    setPulseRunId,
    setDetectionStatus,
    clearFileSelection,
  ]);

  // Navigate to files tab for detection banner CTA
  const handleGoToFiles = useCallback(() => {
    setActiveTab("files");
  }, []);

  // Detection loading overlay
  if (detectionStatus === "running") {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <DetectionLoading />
      </div>
    );
  }

  const hasFilesNoSignals =
    (collection?.file_count ?? 0) > 0 && (collection?.signal_count ?? 0) === 0;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/workspace">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          {loadingCollection ? (
            <Skeleton className="h-7 w-48" />
          ) : (
            <h1 className="text-2xl font-bold">{collection?.name}</h1>
          )}
        </div>
        {/* Credit usage pill (NAV-04) */}
        <Badge
          variant="secondary"
          className="gap-1.5 px-3 py-1 text-sm font-medium"
        >
          <Zap className="h-3.5 w-3.5 text-amber-400" />
          {CREDIT_COST} credits / run
        </Badge>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="signals">Signals</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {loadingCollection ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 rounded-lg" />
              ))}
            </div>
          ) : (
            <OverviewStatCards
              filesCount={collection?.file_count ?? 0}
              signalCount={collection?.signal_count ?? 0}
              reportsCount={collection?.report_count ?? 0}
              creditsUsed={CREDIT_COST}
            />
          )}

          {hasFilesNoSignals && (
            <RunDetectionBanner
              fileCount={collection?.file_count ?? 0}
              onRunDetection={handleGoToFiles}
            />
          )}

          {/* Signal previews (up to 4) */}
          {sortedSignals.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Recent Signals
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedSignals.slice(0, 4).map((signal) => (
                  <SignalCard key={signal.id} signal={signal} preview />
                ))}
              </div>
            </div>
          )}

          {/* Compact file table (3 rows) */}
          {files.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-muted-foreground">
                  Files
                </h3>
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => setActiveTab("files")}
                >
                  View all files
                </Button>
              </div>
              <FileTable
                files={files}
                selectedFileIds={[]}
                onSelectedChange={() => {}}
                onFileClick={handleFileClick}
                selectable={false}
                maxRows={3}
              />
            </div>
          )}

          {/* Activity feed */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Activity
            </h3>
            {loadingSignals || loadingReports ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <ActivityFeed signals={signals} reports={reports} />
            )}
          </div>
        </TabsContent>

        {/* Files Tab */}
        <TabsContent value="files" className="space-y-6 mt-6">
          <FileUploadZone collectionId={collectionId} />

          {loadingFiles ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <FileTable
              files={files}
              selectedFileIds={selectedFileIds}
              onSelectedChange={handleSelectedChange}
              onFileClick={handleFileClick}
            />
          )}

          {selectedFileIds.length > 0 && (
            <StickyActionBar
              selectedCount={selectedFileIds.length}
              creditCost={CREDIT_COST}
              onRunDetection={handleRunDetection}
              isLoading={triggerPulse.isPending}
            />
          )}

          <DataSummaryPanel
            file={summaryFile}
            open={summaryOpen}
            onOpenChange={setSummaryOpen}
          />
        </TabsContent>

        {/* Signals Tab (NAV-03) */}
        <TabsContent value="signals" className="space-y-6 mt-6">
          {loadingSignals ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-24 rounded-lg" />
              ))}
            </div>
          ) : sortedSignals.length === 0 ? (
            <div className="flex flex-col items-center py-16">
              <p className="text-sm text-muted-foreground mb-4">
                No signals detected yet
              </p>
              <Button variant="outline" onClick={handleGoToFiles}>
                Go to Files tab to run detection
              </Button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedSignals.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} preview />
                ))}
              </div>
              <div className="flex justify-center pt-4">
                <Button variant="outline" asChild>
                  <Link
                    href={`/workspace/collections/${collectionId}/signals`}
                    className="gap-2"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Open Signals View
                  </Link>
                </Button>
              </div>
            </>
          )}
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-4 mt-6">
          {loadingReports ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : reports.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No reports generated yet. Run detection to generate reports.
            </p>
          ) : (
            <div className="rounded-lg border bg-card divide-y divide-border">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div>
                      <p className="text-sm font-medium">{report.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(report.created_at).toLocaleDateString(
                          "en-US",
                          { month: "short", day: "numeric", year: "numeric" }
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="text-xs">
                      {report.report_type}
                    </Badge>
                    <Button variant="outline" size="sm" asChild>
                      <Link
                        href={`/workspace/collections/${collectionId}/reports/${report.id}`}
                      >
                        View Report
                      </Link>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
