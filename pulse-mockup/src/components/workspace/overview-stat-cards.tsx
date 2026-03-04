import { FolderOpen, Activity, FileText, Zap } from "lucide-react";

interface OverviewStatCardsProps {
  filesCount: number;
  signalCount: number;
  reportsCount: number;
  creditsUsed: number;
}

export function OverviewStatCards({
  filesCount,
  signalCount,
  reportsCount,
  creditsUsed,
}: OverviewStatCardsProps) {
  const cards = [
    {
      icon: FolderOpen,
      value: filesCount,
      label: "Files",
    },
    {
      icon: Activity,
      value: signalCount,
      label: "Signals",
    },
    {
      icon: FileText,
      value: reportsCount,
      label: "Reports",
    },
    {
      icon: Zap,
      value: creditsUsed,
      label: "Credits Used",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className="bg-card border border-border rounded-lg p-4 flex items-center gap-3"
          >
            <div className="rounded-md bg-muted p-2 shrink-0">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-2xl font-bold leading-none">{card.value}</p>
              <p className="text-xs text-muted-foreground uppercase tracking-wide mt-1">
                {card.label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
