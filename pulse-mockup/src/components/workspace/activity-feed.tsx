import { Zap, FileUp, FileText, MessageSquare } from "lucide-react";
import { type ActivityItem } from "@/lib/mock-data";

interface ActivityFeedProps {
  items: ActivityItem[];
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getIcon(icon: ActivityItem["icon"]) {
  switch (icon) {
    case "pulse":
      return Zap;
    case "file":
      return FileUp;
    case "report":
      return FileText;
    case "chat":
      return MessageSquare;
    default:
      return Zap;
  }
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No activity yet.</p>
    );
  }

  return (
    <div className="flex flex-col">
      {items.map((item, index) => {
        const Icon = getIcon(item.icon);
        const isLast = index === items.length - 1;
        return (
          <div key={item.id} className="flex gap-3">
            {/* Timeline column */}
            <div className="flex flex-col items-center">
              <div className="rounded-full bg-muted p-1.5 shrink-0">
                <Icon className="w-3.5 h-3.5 text-muted-foreground" />
              </div>
              {!isLast && (
                <div className="w-px flex-1 border-l border-dashed border-border mt-1 mb-1" />
              )}
            </div>
            {/* Content column */}
            <div className={`pb-4 ${isLast ? "" : ""}`}>
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
