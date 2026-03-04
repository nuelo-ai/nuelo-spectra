import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RunDetectionBannerProps {
  onRunDetection: () => void;
}

export function RunDetectionBanner({ onRunDetection }: RunDetectionBannerProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 text-primary shrink-0" />
        <p className="text-sm text-foreground">
          You have 2 new files — Run Detection to discover signals
        </p>
      </div>
      <Button variant="default" size="sm" onClick={onRunDetection}>
        Run Detection
      </Button>
    </div>
  );
}
