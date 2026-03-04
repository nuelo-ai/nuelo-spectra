"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FileSpreadsheet, FileText, Rows3, Columns3, Hash } from "lucide-react";
import type { FileItem } from "@/lib/mock-data";

// --- Mock data summary content (hardcoded per-file mockup) ---

const MOCK_SUMMARY = {
  rowCount: 12847,
  columnCount: 24,
  dataTypes: ["numeric", "categorical", "datetime", "text"],
  sampleColumns: [
    { name: "transaction_id", type: "text" },
    { name: "amount", type: "numeric" },
    { name: "category", type: "categorical" },
    { name: "created_at", type: "datetime" },
    { name: "region", type: "categorical" },
    { name: "quantity", type: "numeric" },
  ],
};

function FileTypeIcon({ type }: { type: FileItem["type"] }) {
  switch (type) {
    case "csv":
      return <FileText className="h-5 w-5 text-emerald-400" />;
    case "xlsx":
    case "xls":
      return <FileSpreadsheet className="h-5 w-5 text-blue-400" />;
    default:
      return <FileText className="h-5 w-5 text-muted-foreground" />;
  }
}

interface DataSummaryPanelProps {
  file: FileItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DataSummaryPanel({
  file,
  open,
  onOpenChange,
}: DataSummaryPanelProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:max-w-[400px] overflow-y-auto">
        {file && (
          <>
            <SheetHeader>
              <div className="flex items-center gap-2">
                <FileTypeIcon type={file.type} />
                <SheetTitle className="text-base">{file.name}</SheetTitle>
              </div>
              <SheetDescription>Data summary and column overview</SheetDescription>
            </SheetHeader>

            {/* File metadata */}
            <div className="px-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground mb-1">Type</p>
                  <p className="text-sm font-medium uppercase">{file.type}</p>
                </div>
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground mb-1">Size</p>
                  <p className="text-sm font-medium">{file.size}</p>
                </div>
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground mb-1">Uploaded</p>
                  <p className="text-sm font-medium">{file.uploadDate}</p>
                </div>
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground mb-1">Status</p>
                  <p className="text-sm font-medium capitalize">
                    {file.profilingStatus}
                  </p>
                </div>
              </div>

              <Separator />

              {/* Data summary */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Data Summary</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2 rounded-md bg-muted/50 p-3">
                    <Rows3 className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Rows</p>
                      <p className="text-sm font-medium">
                        {MOCK_SUMMARY.rowCount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-md bg-muted/50 p-3">
                    <Columns3 className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Columns</p>
                      <p className="text-sm font-medium">
                        {MOCK_SUMMARY.columnCount}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Data types */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Data Types Detected</h4>
                <div className="flex flex-wrap gap-1.5">
                  {MOCK_SUMMARY.dataTypes.map((dt) => (
                    <Badge key={dt} variant="secondary" className="text-xs capitalize">
                      <Hash className="h-3 w-3 mr-0.5" />
                      {dt}
                    </Badge>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Sample columns */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Sample Columns</h4>
                <div className="space-y-1.5">
                  {MOCK_SUMMARY.sampleColumns.map((col) => (
                    <div
                      key={col.name}
                      className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2"
                    >
                      <code className="text-xs font-mono text-foreground">
                        {col.name}
                      </code>
                      <Badge variant="outline" className="text-xs capitalize">
                        {col.type}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
