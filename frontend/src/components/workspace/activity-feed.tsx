import { Zap, FileText } from "lucide-react";
import type { SignalDetail, ReportListItem } from "@/types/workspace";

interface ActivityItem {
  id: string;
  description: string;
  timestamp: string;
  type: "signal" | "report";
}

interface ActivityFeedProps {
  signals: SignalDetail[];
  reports: ReportListItem[];
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ActivityFeed({ signals, reports }: ActivityFeedProps) {
  // Merge signals and reports into a timeline sorted by date descending
  const items: ActivityItem[] = [
    ...signals.map((s) => ({
      id: `signal-${s.id}`,
      description: `Signal detected: ${s.title}`,
      timestamp: s.created_at,
      type: "signal" as const,
    })),
    ...reports.map((r) => ({
      id: `report-${r.id}`,
      description: `Report generated: ${r.title}`,
      timestamp: r.created_at,
      type: "report" as const,
    })),
  ].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No activity yet.</p>
    );
  }

  return (
    <div className="flex flex-col">
      {items.map((item, index) => {
        const Icon = item.type === "signal" ? Zap : FileText;
        const isLast = index === items.length - 1;
        return (
          <div key={item.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="rounded-full bg-muted p-1.5 shrink-0">
                <Icon className="w-3.5 h-3.5 text-muted-foreground" />
              </div>
              {!isLast && (
                <div className="w-px flex-1 border-l border-dashed border-border mt-1 mb-1" />
              )}
            </div>
            <div className="pb-4">
              <p className="text-sm">{item.description}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatTimestamp(item.timestamp)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
