"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileUploadZone } from "@/components/workspace/file-upload-zone";
import { FileTable } from "@/components/workspace/file-table";
import { DataSummaryPanel } from "@/components/workspace/data-summary-panel";
import { StickyActionBar } from "@/components/workspace/sticky-action-bar";
import { DetectionLoading } from "@/components/workspace/detection-loading";
import { SignalCard } from "@/components/workspace/signal-card";
import { OverviewStatCards } from "@/components/workspace/overview-stat-cards";
import { ActivityFeed } from "@/components/workspace/activity-feed";
import { RunDetectionBanner } from "@/components/workspace/run-detection-banner";
import { FileText, Zap } from "lucide-react";
import {
  MOCK_COLLECTIONS,
  MOCK_SIGNALS,
  MOCK_REPORTS,
  MOCK_ACTIVITY,
  type FileItem,
} from "@/lib/mock-data";

export default function CollectionDetailPage() {
  const params = useParams();
  const collectionId = params.id as string;

  // Find collection from mock data
  const collection =
    MOCK_COLLECTIONS.find((c) => c.id === collectionId) ?? MOCK_COLLECTIONS[0];

  // Filter mock data for this collection
  const reportsForCollection = MOCK_REPORTS.filter(
    (r) => r.collectionId === collectionId
  );
  const activityForCollection = MOCK_ACTIVITY.filter(
    (a) => a.collectionId === collectionId
  );

  // Tab state (controlled so Overview can switch to Files tab)
  const [activeTab, setActiveTab] = useState("overview");

  // File selection state
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);

  // Data summary panel state
  const [summaryFile, setSummaryFile] = useState<FileItem | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);

  // Detection loading state
  const [isDetecting, setIsDetecting] = useState(false);

  const handleFileClick = (file: FileItem) => {
    setSummaryFile(file);
    setSummaryOpen(true);
  };

  const handleRunDetection = () => {
    setIsDetecting(true);
  };

  // Detection loading replaces the full page content
  if (isDetecting) {
    return <DetectionLoading collectionId={collectionId || collection.id} />;
  }

  return (
    <div className="flex flex-col gap-6 pb-24">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {collection.name}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Created {collection.createdAt}
            </p>
          </div>
          <Badge
            className={
              collection.status === "active"
                ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/15"
                : "bg-muted text-muted-foreground hover:bg-muted"
            }
          >
            {collection.status === "active" ? "Active" : "Archived"}
          </Badge>
        </div>
        {/* Credits used pill */}
        <span className="flex items-center gap-1.5 text-sm text-muted-foreground shrink-0">
          <Zap className="h-3.5 w-3.5 text-primary" />
          Credits used: {collection.creditsUsed}
        </span>
      </div>

      {/* Four-tab layout */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="signals">Signals</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Overview tab */}
        <TabsContent value="overview">
          <div className="flex flex-col gap-6 pt-4">
            {/* Stat cards */}
            <OverviewStatCards
              filesCount={collection.filesCount}
              signalCount={collection.signalCount}
              reportsCount={reportsForCollection.length}
              creditsUsed={collection.creditsUsed}
            />

            {/* Run Detection banner */}
            <RunDetectionBanner onRunDetection={handleRunDetection} />

            {/* Signals hero section */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Signals
              </h2>
              {MOCK_SIGNALS.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No signals yet — upload files and run detection to discover
                  insights
                </p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {MOCK_SIGNALS.slice(0, 4).map((signal) => (
                    <Link
                      key={signal.id}
                      href={`/workspace/collections/${collectionId}/signals`}
                    >
                      <SignalCard
                        signal={signal}
                        isSelected={false}
                        onSelect={() => {}}
                      />
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Compact files section */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Files
              </h2>
              <FileTable
                selectedFileIds={[]}
                onSelectedChange={() => {}}
                onFileClick={handleFileClick}
              />
              <div className="mt-3">
                <button
                  onClick={() => setActiveTab("files")}
                  className="text-sm text-primary hover:underline"
                >
                  View all files in Files tab
                </button>
              </div>
            </div>

            {/* Activity feed */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Activity
              </h2>
              <ActivityFeed items={activityForCollection} />
            </div>
          </div>
        </TabsContent>

        {/* Files tab */}
        <TabsContent value="files">
          <div className="flex flex-col gap-6 pt-4">
            {/* File upload zone */}
            <FileUploadZone />

            {/* File table */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Files
              </h2>
              <FileTable
                selectedFileIds={selectedFileIds}
                onSelectedChange={setSelectedFileIds}
                onFileClick={handleFileClick}
              />
            </div>

            {/* Data summary side panel */}
            <DataSummaryPanel
              file={summaryFile}
              open={summaryOpen}
              onOpenChange={setSummaryOpen}
            />

            {/* Sticky action bar */}
            <StickyActionBar
              selectedCount={selectedFileIds.length}
              onRunDetection={handleRunDetection}
            />
          </div>
        </TabsContent>

        {/* Signals tab */}
        <TabsContent value="signals">
          <div className="flex flex-col gap-4 pt-4">
            <p className="text-sm text-muted-foreground">
              View detected signals and their details in the dedicated signals
              page.
            </p>
            <Link
              href={`/workspace/collections/${collectionId}/signals`}
            >
              <Button variant="outline">Open Signals View</Button>
            </Link>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {MOCK_SIGNALS.map((signal) => (
                <SignalCard
                  key={signal.id}
                  signal={signal}
                  isSelected={false}
                  onSelect={() => {}}
                />
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Reports tab */}
        <TabsContent value="reports">
          <div className="flex flex-col gap-3 pt-4">
            {reportsForCollection.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Reports will appear here after investigation is complete.
              </p>
            ) : (
              reportsForCollection.map((report) => {
                const sourceSignal = report.signalId
                  ? MOCK_SIGNALS.find((s) => s.id === report.signalId)
                  : null;
                const sourceLabel =
                  sourceSignal
                    ? `Signal — ${sourceSignal.title}`
                    : report.type === "Chat Report"
                    ? "Chat Session"
                    : report.type === "Detection Summary"
                    ? "Detection Run"
                    : null;

                return (
                  <div
                    key={report.id}
                    className="bg-card border border-border rounded-lg px-4 py-3 flex items-start gap-4 hover:border-border/80 transition-colors"
                  >
                    <FileText className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="shrink-0 text-xs">
                          {report.type}
                        </Badge>
                        <span className="font-medium text-sm truncate">
                          {report.title}
                        </span>
                      </div>
                      {sourceLabel && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Source: {sourceLabel}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-muted-foreground">
                        {report.generatedAt}
                      </span>
                      <Link
                        href={`/workspace/collections/${collectionId}/reports/${report.id}`}
                      >
                        <Button variant="ghost" size="sm">
                          View Report
                        </Button>
                      </Link>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
