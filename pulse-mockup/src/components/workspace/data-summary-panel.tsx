"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  FileSpreadsheet,
  FileText,
  Rows3,
  Columns3,
  Hash,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
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
  aiAnalysis: {
    summary:
      "This dataset contains transactional records spanning Q3 2025 with strong temporal patterns. Revenue concentration in 3 regions suggests geographic dependency risk.",
    keyFindings: [
      "68% of transactions cluster in Mon-Wed, suggesting weekly cyclicality",
      "Amount distribution is right-skewed with outliers above $12,000",
      "Missing values in 'region' column (2.3%) correlate with bulk imports",
    ],
    dataQuality: {
      score: 87,
      issues: [
        "2.3% missing values in region",
        "12 duplicate transaction_ids detected",
      ],
    },
    suggestedAnalyses: [
      "Anomaly detection on amount time series",
      "Category-based segmentation analysis",
      "Regional trend comparison",
    ],
  },
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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        {file && (
          <>
            <DialogHeader>
              <div className="flex items-center gap-3">
                <FileTypeIcon type={file.type} />
                <div>
                  <DialogTitle className="text-lg">{file.name}</DialogTitle>
                  <DialogDescription>
                    Data profiling summary and AI analysis
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            {/* File metadata row */}
            <div className="grid grid-cols-4 gap-3 mt-2">
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-xs text-muted-foreground mb-1">Type</p>
                <p className="text-sm font-medium uppercase">{file.type}</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-xs text-muted-foreground mb-1">Size</p>
                <p className="text-sm font-medium">{file.size}</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-xs text-muted-foreground mb-1">Uploaded</p>
                <p className="text-sm font-medium">{file.uploadDate}</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-xs text-muted-foreground mb-1">Status</p>
                <p className="text-sm font-medium capitalize">
                  {file.profilingStatus}
                </p>
              </div>
            </div>

            <Separator className="my-2" />

            {/* Two-column layout: left = data overview, right = AI analysis */}
            <div className="grid grid-cols-2 gap-8">
              {/* Left column: Data Overview */}
              <div className="space-y-6">
                {/* Row & column counts */}
                <div>
                  <h4 className="text-sm font-semibold mb-3">Data Summary</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex items-center gap-3 rounded-lg bg-muted/50 p-4">
                      <Rows3 className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Rows</p>
                        <p className="text-lg font-semibold">
                          {MOCK_SUMMARY.rowCount.toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 rounded-lg bg-muted/50 p-4">
                      <Columns3 className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Columns</p>
                        <p className="text-lg font-semibold">
                          {MOCK_SUMMARY.columnCount}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Data types */}
                <div>
                  <h4 className="text-sm font-semibold mb-2">
                    Data Types Detected
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {MOCK_SUMMARY.dataTypes.map((dt) => (
                      <Badge
                        key={dt}
                        variant="secondary"
                        className="text-xs capitalize px-3 py-1"
                      >
                        <Hash className="h-3 w-3 mr-1" />
                        {dt}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Sample columns */}
                <div>
                  <h4 className="text-sm font-semibold mb-3">Columns</h4>
                  <div className="space-y-2">
                    {MOCK_SUMMARY.sampleColumns.map((col) => (
                      <div
                        key={col.name}
                        className="flex items-center justify-between rounded-lg bg-muted/50 px-4 py-2.5"
                      >
                        <code className="text-sm font-mono text-foreground">
                          {col.name}
                        </code>
                        <Badge
                          variant="outline"
                          className="text-xs capitalize"
                        >
                          {col.type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right column: AI Analysis */}
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <h4 className="text-sm font-semibold">AI Analysis</h4>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {MOCK_SUMMARY.aiAnalysis.summary}
                  </p>
                </div>

                {/* Key Findings */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    <h5 className="text-sm font-semibold">Key Findings</h5>
                  </div>
                  <div className="space-y-2">
                    {MOCK_SUMMARY.aiAnalysis.keyFindings.map((finding, i) => (
                      <div
                        key={i}
                        className="rounded-lg bg-muted/50 px-4 py-3 text-sm text-foreground/90 leading-relaxed"
                      >
                        {finding}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Data Quality */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    <h5 className="text-sm font-semibold">Data Quality</h5>
                  </div>
                  <div className="rounded-lg bg-muted/50 p-4 mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">
                        Quality Score
                      </span>
                      <span className="text-lg font-semibold text-emerald-400">
                        {MOCK_SUMMARY.aiAnalysis.dataQuality.score}/100
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-emerald-400 transition-all"
                        style={{
                          width: `${MOCK_SUMMARY.aiAnalysis.dataQuality.score}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    {MOCK_SUMMARY.aiAnalysis.dataQuality.issues.map(
                      (issue, i) => (
                        <p
                          key={i}
                          className="text-sm text-amber-400/80 pl-3 border-l-2 border-amber-400/30"
                        >
                          {issue}
                        </p>
                      )
                    )}
                  </div>
                </div>

                {/* Suggested Analyses */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-4 w-4 text-primary" />
                    <h5 className="text-sm font-semibold">
                      Suggested Analyses
                    </h5>
                  </div>
                  <div className="space-y-2">
                    {MOCK_SUMMARY.aiAnalysis.suggestedAnalyses.map(
                      (suggestion, i) => (
                        <div
                          key={i}
                          className="rounded-lg bg-primary/5 border border-primary/10 px-4 py-3"
                        >
                          <span className="text-sm text-foreground/90">
                            {suggestion}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
