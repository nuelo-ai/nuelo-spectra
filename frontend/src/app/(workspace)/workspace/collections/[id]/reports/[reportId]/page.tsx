"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useQuery } from "@tanstack/react-query";
import { apiClient, getAccessToken } from "@/lib/api-client";
import type { ReportDetail } from "@/types/workspace";

/** Map report_type to badge styling */
const typeBadgeConfig: Record<string, { className: string }> = {
  pulse_detection: {
    className: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  },
  investigation: {
    className: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  },
  whatif: {
    className: "bg-violet-500/10 text-violet-400 border-violet-500/30",
  },
};

function formatReportType(type: string): string {
  const map: Record<string, string> = {
    pulse_detection: "Detection Summary",
    investigation: "Investigation Report",
    whatif: "What-If Scenario Report",
  };
  return map[type] ?? type;
}

export default function ReportDetailPage() {
  const params = useParams();
  const collectionId = params.id as string;
  const reportId = params.reportId as string;

  const {
    data: report,
    isLoading,
    isError,
  } = useQuery<ReportDetail>({
    queryKey: ["collections", collectionId, "reports", reportId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/collections/${collectionId}/reports/${reportId}`
      );
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!reportId,
  });

  const handleDownloadMarkdown = async () => {
    const token = getAccessToken();
    const res = await fetch(
      `/api/collections/${collectionId}/reports/${reportId}/download`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report?.title?.replace(/\s+/g, "-").toLowerCase() || "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="relative min-h-screen">
        <div className="sticky top-0 z-30 flex items-center px-6 py-3 bg-background border-b border-border">
          <SidebarTrigger className="-ml-1 mr-3" />
          <Skeleton className="h-8 w-32" />
          <div className="h-4 w-px bg-border mx-3" />
          <Skeleton className="h-5 w-48" />
        </div>
        <div className="flex justify-center py-10 px-4 bg-muted min-h-screen">
          <div className="w-full max-w-3xl space-y-6 pt-12">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-10 w-96" />
            <Skeleton className="h-[400px] w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="relative min-h-screen">
        <div className="sticky top-0 z-30 flex items-center px-6 py-3 bg-background border-b border-border">
          <SidebarTrigger className="-ml-1 mr-3" />
          <Link href={`/workspace/collections/${collectionId}`}>
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
          </Link>
        </div>
        <div className="flex items-center justify-center min-h-[60vh]">
          <p className="text-sm text-muted-foreground">
            Failed to load report.
          </p>
        </div>
      </div>
    );
  }

  const badgeConfig = typeBadgeConfig[report.report_type] ?? typeBadgeConfig.pulse_detection;

  return (
    <div className="relative min-h-screen">
      {/* Sticky header bar */}
      <div className="sticky top-0 z-30 flex items-center justify-between px-6 py-3 bg-background border-b border-border backdrop-blur-md">
        <div className="flex items-center gap-3">
          <SidebarTrigger className="-ml-1" />
          <Link href={`/workspace/collections/${collectionId}`}>
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
          </Link>
          <div className="h-4 w-px bg-border" />
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium truncate max-w-xs">
            {report.title}
          </span>
          <Badge
            variant="outline"
            className={`text-xs ${badgeConfig.className}`}
          >
            {formatReportType(report.report_type)}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={handleDownloadMarkdown}
          >
            <Download className="h-3.5 w-3.5" /> Download as Markdown
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 opacity-60 cursor-not-allowed"
            disabled
          >
            <Download className="h-3.5 w-3.5" /> Download as PDF
          </Button>
        </div>
      </div>

      {/* Document paper area */}
      <div className="flex justify-center py-10 px-4 bg-muted min-h-screen">
        <div className="w-full max-w-3xl bg-white rounded-lg shadow-2xl shadow-black/40 px-16 py-12 text-gray-900">
          {/* Report metadata header within the paper */}
          <div className="mb-8 pb-6 border-b border-gray-200">
            <Badge className="mb-3 bg-blue-100 text-blue-700 border-0 text-xs">
              {formatReportType(report.report_type)}
            </Badge>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {report.title}
            </h1>
            <p className="text-sm text-gray-500">
              Generated{" "}
              {new Date(report.created_at).toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </p>
          </div>

          {/* Markdown content */}
          {report.content ? (
            <div className="prose prose-slate max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No content available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
