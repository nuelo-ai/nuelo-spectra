"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Zap, FileText, ExternalLink, Loader2, MoreVertical, Pencil, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { CreateCollectionDialog } from "@/components/workspace/create-collection-dialog";
import { DeleteCollectionDialog } from "@/components/workspace/delete-collection-dialog";
import { toast } from "sonner";
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
  useLinkFilesToCollection,
  useRemoveFile,
} from "@/hooks/useWorkspace";
import { useFiles } from "@/hooks/useFileManager";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { OverviewStatCards } from "@/components/workspace/overview-stat-cards";
import { RunDetectionBanner } from "@/components/workspace/run-detection-banner";
import { SignalCard } from "@/components/workspace/signal-card";
import { ActivityFeed } from "@/components/workspace/activity-feed";
import { DetectionProgressBanner } from "@/components/workspace/detection-progress-banner";
import { RerunDetectionDialog } from "@/components/workspace/rerun-detection-dialog";
import { FileTable } from "@/components/workspace/file-table";
import { FileUploadZone } from "@/components/workspace/file-upload-zone";
import { DataSummaryModal } from "@/components/workspace/data-summary-panel";
import { StickyActionBar } from "@/components/workspace/sticky-action-bar";
import type { CollectionFile } from "@/types/workspace";
import type { FileListItem } from "@/types/file";
import type { SignalDetail } from "@/types/workspace";
import { useCreditCosts } from "@/hooks/useCreditCosts";
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
  const { data: creditCosts, isLoading: isLoadingCreditCosts } = useCreditCosts();
  const { data: collection, isLoading: loadingCollection } =
    useCollectionDetail(collectionId);
  const { data: collectionFiles = [], isLoading: loadingCollectionFiles } =
    useCollectionFiles(collectionId);
  const { data: allUserFiles = [], isLoading: loadingUserFiles } = useFiles();
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
    setDetectionStatus,
    setPulseRunId,
    setSelectedSignalId,
  } = useWorkspaceStore();

  const detectionStatus = useWorkspaceStore(
    (s) => s.collectionDetection[collectionId]?.detectionStatus ?? "idle"
  );
  const pulseRunId = useWorkspaceStore(
    (s) => s.collectionDetection[collectionId]?.pulseRunId ?? null
  );

  // Mutations
  const triggerPulse = useTriggerPulse(collectionId);
  const linkFiles = useLinkFilesToCollection(collectionId);
  const removeFile = useRemoveFile(collectionId);
  const { data: pulseRun } = usePulseStatus(collectionId, pulseRunId);

  // Local state
  const [activeTab, setActiveTab] = useState("overview");
  const [summaryFileId, setSummaryFileId] = useState<string | null>(null);
  const [summaryFilename, setSummaryFilename] = useState<string | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [showRerunDialog, setShowRerunDialog] = useState(false);
  const [pendingUserContext, setPendingUserContext] = useState<string | undefined>();
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // Sort signals by severity (SIGNAL-01)
  const sortedSignals = useMemo(() => sortBySeverity(signals), [signals]);

  // Reset detection state on mount if no active pulse run
  useEffect(() => {
    if (!pulseRunId) {
      setDetectionStatus(collectionId, "idle");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-select highest severity signal (SIGNAL-02)
  useEffect(() => {
    if (sortedSignals.length > 0) {
      setSelectedSignalId(sortedSignals[0].id);
    }
  }, [sortedSignals, setSelectedSignalId]);

  // Monitor pulse status
  useEffect(() => {
    if (!pulseRun) return;
    if (pulseRun.status === "completed") {
      setDetectionStatus(collectionId, "complete");
      setPulseRunId(collectionId, null);
      refetchSignals();
      toast.success("Detection complete", {
        description: `${pulseRun.signal_count ?? 0} signals identified`,
        action: {
          label: "View Signals",
          onClick: () => router.push(`/workspace/collections/${collectionId}/signals`),
        },
      });
    } else if (pulseRun.status === "failed") {
      setDetectionStatus(collectionId, "failed");
      setPulseRunId(collectionId, null);
    }
  }, [pulseRun, setDetectionStatus, setPulseRunId, refetchSignals]);

  // File selection handlers (for Files tab - user files)
  const handleSelectedChange = useCallback(
    (ids: string[]) => {
      clearFileSelection();
      ids.forEach((id) => toggleFileSelection(id));
    },
    [clearFileSelection, toggleFileSelection]
  );

  // Click file → open summary modal
  const handleCollectionFileClick = useCallback((file: CollectionFile) => {
    setSummaryFileId(file.file_id);
    setSummaryFilename(file.filename);
    setSummaryOpen(true);
  }, []);

  const handleUserFileClick = useCallback((file: FileListItem) => {
    setSummaryFileId(file.id);
    setSummaryFilename(file.original_filename);
    setSummaryOpen(true);
  }, []);

  // Run detection against ALL collection files
  const handleRunDetection = useCallback(async (userContext?: string) => {
    if (loadingCollectionFiles) return; // Wait for data to load
    const fileIds = collectionFiles.map((f) => f.file_id);
    if (fileIds.length === 0) {
      setActiveTab("files");
      return;
    }
    try {
      const result = await triggerPulse.mutateAsync({
        file_ids: fileIds,
        user_context: userContext,
      });
      setPulseRunId(collectionId, result.pulse_run_id);
      setDetectionStatus(collectionId, "running");
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes("409")) {
        toast.error("A detection run is already in progress");
      } else if (err instanceof Error && err.message.includes("402")) {
        toast.error("Insufficient credits", {
          description: "You don't have enough credits to run detection. Contact your admin to top up.",
        });
      }
    }
  }, [collectionFiles, loadingCollectionFiles, triggerPulse, setPulseRunId, setDetectionStatus]);

  // Add selected files to collection, then go back to overview
  const handleAddToCollection = useCallback(async () => {
    if (selectedFileIds.length === 0) return;
    try {
      await linkFiles.mutateAsync(selectedFileIds);
      clearFileSelection();
      setActiveTab("overview");
    } catch {
      // Error handled by TanStack Query
    }
  }, [selectedFileIds, linkFiles, clearFileSelection]);

  // Remove file from collection
  const handleRemoveFile = useCallback(
    async (fileId: string) => {
      try {
        await removeFile.mutateAsync(fileId);
      } catch {
        // Error handled by TanStack Query
      }
    },
    [removeFile]
  );

  const isDetectionRunning = detectionStatus === "running";
  const signalCount = collection?.signal_count ?? 0;
  const reportCount = collection?.report_count ?? 0;
  const hasFiles = !loadingCollectionFiles && collectionFiles.length > 0;
  const hasNoFiles = !loadingCollectionFiles && collectionFiles.length === 0;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/workspace">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex items-center gap-2">
          {loadingCollection ? (
            <Skeleton className="h-7 w-48" />
          ) : (
            <h1 className="text-2xl font-bold">{collection?.name}</h1>
          )}
          {!loadingCollection && collection && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                  <span className="sr-only">Collection options</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setRenameOpen(true)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Rename
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => setDeleteOpen(true)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        {/* Credit usage pill (NAV-04) */}
        <Badge
          variant="secondary"
          className="ml-auto gap-1.5 px-3 py-1 text-sm font-medium"
        >
          <Zap className="h-3.5 w-3.5 text-amber-400" />
          {isLoadingCreditCosts ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <>{creditCosts?.pulse_run} credits / run</>
          )}
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
              creditsUsed={creditCosts?.pulse_run ?? 0}
            />
          )}

          {/* Inline progress banner (replaces full-page takeover) */}
          {isDetectionRunning && pulseRun && (
            <DetectionProgressBanner status={pulseRun.status} />
          )}
          {isDetectionRunning && !pulseRun && (
            <DetectionProgressBanner status="pending" />
          )}

          {/* Run Detection — always visible */}
          {hasFiles ? (
            <RunDetectionBanner
              fileCount={collection?.file_count ?? 0}
              isRunning={isDetectionRunning}
              onRunDetection={(ctx) => {
                if (signalCount > 0) {
                  setPendingUserContext(ctx);
                  setShowRerunDialog(true);
                } else {
                  handleRunDetection(ctx);
                }
              }}
            />
          ) : hasNoFiles ? (
            <RunDetectionBanner
              fileCount={0}
              onRunDetection={() => setActiveTab("files")}
            />
          ) : null}

          {/* Signal previews (up to 4) */}
          {loadingSignals ? (
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Signals Identified
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Array.from({ length: 2 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 rounded-lg" />
                ))}
              </div>
            </div>
          ) : sortedSignals.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Signals Identified
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedSignals.slice(0, 4).map((signal) => (
                  <div
                    key={signal.id}
                    className="cursor-pointer hover:border-primary/50 rounded-lg transition-colors"
                    onClick={() => router.push(`/workspace/collections/${collectionId}/signals?selected=${signal.id}`)}
                  >
                    <SignalCard signal={signal} preview />
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* View Signal Report button */}
          {reports.length > 0 && (
            <div>
              <Button
                variant="default"
                className="gap-2"
                asChild
              >
                <Link href={`/workspace/collections/${collectionId}/reports/${reports[0].id}`}>
                  <FileText className="h-4 w-4" />
                  View Signal Report
                </Link>
              </Button>
            </div>
          )}

          {/* Collection files table */}
          {loadingCollectionFiles ? (
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Files
              </h3>
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            </div>
          ) : collectionFiles.length > 0 ? (
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
                  Add more files
                </Button>
              </div>
              <FileTable
                files={collectionFiles}
                selectedFileIds={[]}
                onSelectedChange={() => {}}
                onFileClick={handleCollectionFileClick}
                selectable={false}
                onRemoveFile={handleRemoveFile}
              />
            </div>
          ) : null}

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

        {/* Files Tab - All user files (file picker) */}
        <TabsContent value="files" className="space-y-6 mt-6">
          <FileUploadZone collectionId={collectionId} />

          {loadingUserFiles ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <UserFileTable
              files={allUserFiles}
              collectionFileIds={collectionFiles.map((f) => f.file_id)}
              selectedFileIds={selectedFileIds}
              onSelectedChange={handleSelectedChange}
              onFileClick={handleUserFileClick}
            />
          )}

          {selectedFileIds.length > 0 && (
            <StickyActionBar
              selectedCount={selectedFileIds.length}
              onAddToCollection={handleAddToCollection}
              isLoading={linkFiles.isPending}
            />
          )}
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
              <Button variant="outline" onClick={() => handleRunDetection()}>
                Run Detection
              </Button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sortedSignals.map((signal) => (
                  <SignalCard
                    key={signal.id}
                    signal={signal}
                    onSelect={(id) =>
                      router.push(
                        `/workspace/collections/${collectionId}/signals?selected=${id}`
                      )
                    }
                  />
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

      {/* Re-run confirmation dialog (controlled) */}
      <RerunDetectionDialog
        creditCost={creditCosts?.pulse_run ?? 0}
        open={showRerunDialog}
        onOpenChange={setShowRerunDialog}
        onConfirm={() => {
          setShowRerunDialog(false);
          handleRunDetection(pendingUserContext);
        }}
      />

      {/* Data summary modal (shared across tabs) */}
      <DataSummaryModal
        fileId={summaryFileId}
        filename={summaryFilename}
        open={summaryOpen}
        onOpenChange={setSummaryOpen}
      />

      {/* Rename dialog — edit mode */}
      <CreateCollectionDialog
        open={renameOpen}
        onOpenChange={setRenameOpen}
        collection={collection ?? undefined}
      />

      {/* Delete confirmation dialog */}
      <DeleteCollectionDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        collection={collection ?? null}
        onSuccess={() => router.push("/workspace")}
      />
    </div>
  );
}

/**
 * User file table for the Files tab.
 * Shows all user files with checkboxes, marks already-linked files.
 */
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { FileSpreadsheet } from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";

function UserFileTable({
  files,
  collectionFileIds,
  selectedFileIds,
  onSelectedChange,
  onFileClick,
}: {
  files: FileListItem[];
  collectionFileIds: string[];
  selectedFileIds: string[];
  onSelectedChange: (ids: string[]) => void;
  onFileClick: (file: FileListItem) => void;
}) {
  // Files not yet in collection
  const availableFiles = files.filter(
    (f) => !collectionFileIds.includes(f.id)
  );
  const linkedFiles = files.filter((f) => collectionFileIds.includes(f.id));

  const allAvailableSelected =
    availableFiles.length > 0 &&
    availableFiles.every((f) => selectedFileIds.includes(f.id));
  const someSelected =
    selectedFileIds.length > 0 && !allAvailableSelected;

  const handleSelectAll = useCallback(() => {
    if (allAvailableSelected) {
      onSelectedChange([]);
    } else {
      onSelectedChange(availableFiles.map((f) => f.id));
    }
  }, [allAvailableSelected, onSelectedChange, availableFiles]);

  const handleSelectOne = useCallback(
    (id: string) => {
      if (selectedFileIds.includes(id)) {
        onSelectedChange(selectedFileIds.filter((fid) => fid !== id));
      } else {
        onSelectedChange([...selectedFileIds, id]);
      }
    },
    [selectedFileIds, onSelectedChange]
  );

  if (files.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No files uploaded yet. Upload files above to get started.
      </p>
    );
  }

  function FileIcon({ filename }: { filename: string }) {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "csv")
      return <FileText className="h-4 w-4 text-emerald-400 shrink-0" />;
    if (ext === "xlsx" || ext === "xls")
      return <FileSpreadsheet className="h-4 w-4 text-blue-400 shrink-0" />;
    return <FileText className="h-4 w-4 text-muted-foreground shrink-0" />;
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[40px]">
              <Checkbox
                checked={
                  allAvailableSelected
                    ? true
                    : someSelected
                      ? "indeterminate"
                      : false
                }
                onCheckedChange={handleSelectAll}
                aria-label="Select all available files"
              />
            </TableHead>
            <TableHead>File Name</TableHead>
            <TableHead className="w-[100px]">Size</TableHead>
            <TableHead className="w-[120px]">Uploaded</TableHead>
            <TableHead className="w-[120px]">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {availableFiles.map((file) => {
            const isSelected = selectedFileIds.includes(file.id);
            return (
              <TableRow
                key={file.id}
                data-state={isSelected ? "selected" : undefined}
                className="group"
              >
                <TableCell>
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => handleSelectOne(file.id)}
                    aria-label={`Select ${file.original_filename}`}
                  />
                </TableCell>
                <TableCell>
                  <button
                    type="button"
                    onClick={() => onFileClick(file)}
                    className={cn(
                      "flex items-center gap-2 text-left hover:text-primary transition-colors",
                      "focus-visible:outline-none focus-visible:underline"
                    )}
                  >
                    <FileIcon filename={file.original_filename} />
                    <span className="font-medium">
                      {file.original_filename}
                    </span>
                  </button>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatFileSize(file.file_size)}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(file.created_at)}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">
                    Available
                  </Badge>
                </TableCell>
              </TableRow>
            );
          })}
          {linkedFiles.map((file) => (
            <TableRow key={file.id} className="opacity-60">
              <TableCell>
                <Checkbox checked disabled aria-label="Already in collection" />
              </TableCell>
              <TableCell>
                <button
                  type="button"
                  onClick={() => onFileClick(file)}
                  className={cn(
                    "flex items-center gap-2 text-left hover:text-primary transition-colors",
                    "focus-visible:outline-none focus-visible:underline"
                  )}
                >
                  <FileIcon filename={file.original_filename} />
                  <span className="font-medium">
                    {file.original_filename}
                  </span>
                </button>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatFileSize(file.file_size)}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatDate(file.created_at)}
              </TableCell>
              <TableCell>
                <Badge variant="secondary" className="text-xs">
                  In Collection
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
