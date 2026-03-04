"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SignalChart } from "@/components/workspace/signal-chart";
import { Microscope } from "lucide-react";
import { MOCK_INVESTIGATION_SESSIONS, MOCK_REPORTS } from "@/lib/mock-data";
import type { Signal } from "@/lib/mock-data";

const severityConfig = {
  critical: {
    label: "Critical",
    className: "bg-severity-critical/15 text-severity-critical border-severity-critical/30",
  },
  warning: {
    label: "Warning",
    className: "bg-severity-warning/15 text-severity-warning border-severity-warning/30",
  },
  info: {
    label: "Informational",
    className: "bg-severity-info/15 text-severity-info border-severity-info/30",
  },
} as const;

function parseStatisticalEvidence(evidence: string) {
  return evidence.split("|").map((part) => {
    const trimmed = part.trim();
    const colonIndex = trimmed.indexOf(":");
    if (colonIndex === -1) return { label: trimmed, value: "" };
    return {
      label: trimmed.slice(0, colonIndex).trim(),
      value: trimmed.slice(colonIndex + 1).trim(),
    };
  });
}

interface SignalDetailPanelProps {
  signal: Signal;
  collectionId: string;
}

export function SignalDetailPanel({ signal, collectionId }: SignalDetailPanelProps) {
  const severity = severityConfig[signal.severity];
  const evidence = parseStatisticalEvidence(signal.statisticalEvidence);

  // Compute past investigation sessions for this signal, most recent first
  const signalSessions = MOCK_INVESTIGATION_SESSIONS
    .filter((s) => s.signalId === signal.id)
    .slice()
    .reverse();

  // Build list of sessions that have a completed report
  const investigationReports = signalSessions
    .filter((s) => s.reportId !== null)
    .map((s) => {
      const report = MOCK_REPORTS.find((r) => r.id === s.reportId);
      return { session: s, report };
    })
    .filter((entry): entry is { session: typeof signalSessions[number]; report: NonNullable<typeof entry.report> } =>
      entry.report !== undefined
    );

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6 max-w-4xl">
        {/* Header */}
        <div>
          <div className="flex items-start justify-between gap-4 mb-3">
            <h2 className="text-xl font-semibold leading-tight">{signal.title}</h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn("text-xs font-semibold", severity.className)}
            >
              {severity.label}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {signal.category}
            </Badge>
          </div>
        </div>

        {/* Chart */}
        <Card className="py-0 gap-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Visualization
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <SignalChart signal={signal} />
          </CardContent>
        </Card>

        {/* Description */}
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Analysis
          </h3>
          <p className="text-sm leading-relaxed text-foreground/90">
            {signal.description}
          </p>
        </div>

        {/* Statistical Evidence */}
        <Card className="py-0 gap-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Statistical Evidence
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="grid grid-cols-2 gap-3">
              {evidence.map((item, i) => (
                <div
                  key={i}
                  className="rounded-lg bg-muted/50 px-3 py-2.5"
                >
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
                    {item.label}
                  </p>
                  <p className="text-sm font-semibold">{item.value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Investigation */}
        <div className="pt-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Investigation
          </h3>

          <Link
            href={`/workspace/collections/${collectionId}/signals/${signal.id}/investigate`}
          >
            <Button size="sm" className="gap-2">
              <Microscope className="h-4 w-4" />
              Investigate{" "}
              <span className="text-xs opacity-70 ml-1">(3 credits)</span>
            </Button>
          </Link>

          <div className="mt-4">
            {investigationReports.length > 0 ? (
              <div className="space-y-0">
                {investigationReports.map((entry, i) => (
                  <div key={entry.session.id}>
                    {i > 0 && <div className="border-t border-border/50" />}
                    <Link
                      href={`/workspace/collections/${collectionId}/reports/${entry.report.id}`}
                      className="flex items-center gap-3 py-1.5 hover:text-foreground text-foreground/80 transition-colors"
                    >
                      <span className="text-[11px] text-muted-foreground shrink-0 w-12">
                        {formatDate(entry.session.completedAt ?? entry.session.startedAt)}
                      </span>
                      <span className="text-xs flex-1 line-clamp-1">
                        {entry.report.title}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1.5 py-0 h-5 bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shrink-0"
                      >
                        Complete
                      </Badge>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No investigations yet</p>
            )}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
