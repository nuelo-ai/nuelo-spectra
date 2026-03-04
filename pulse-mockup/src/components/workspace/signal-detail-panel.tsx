"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SignalChart } from "@/components/workspace/signal-chart";
import { Search } from "lucide-react";
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
}

export function SignalDetailPanel({ signal }: SignalDetailPanelProps) {
  const severity = severityConfig[signal.severity];
  const evidence = parseStatisticalEvidence(signal.statisticalEvidence);

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

        {/* Actions */}
        <div className="pt-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="gap-2 opacity-60 cursor-not-allowed"
                disabled
              >
                <Search className="h-4 w-4" />
                Investigate
              </Button>
            </TooltipTrigger>
            <TooltipContent>Coming soon in a future update</TooltipContent>
          </Tooltip>
        </div>
      </div>
    </ScrollArea>
  );
}
