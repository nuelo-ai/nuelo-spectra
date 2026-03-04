"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { FileUploadZone } from "@/components/workspace/file-upload-zone";
import { FileTable } from "@/components/workspace/file-table";
import { DataSummaryPanel } from "@/components/workspace/data-summary-panel";
import { StickyActionBar } from "@/components/workspace/sticky-action-bar";
import { DetectionLoading } from "@/components/workspace/detection-loading";
import {
  MOCK_COLLECTIONS,
  type FileItem,
} from "@/lib/mock-data";

export default function CollectionDetailPage() {
  const params = useParams();
  const collectionId = params.id as string;

  // Find collection from mock data
  const collection = MOCK_COLLECTIONS.find((c) => c.id === collectionId) ??
    MOCK_COLLECTIONS[0]; // Fallback to first collection if ID not found

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
  );
}
