import { AlertCircle, FolderPlus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RunDetectionBannerProps {
  fileCount: number;
  onRunDetection: () => void;
}

export function RunDetectionBanner({
  fileCount,
  onRunDetection,
}: RunDetectionBannerProps) {
  const noFiles = fileCount === 0;

  return (
    <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
      <div className="flex items-center gap-2">
        {noFiles ? (
          <FolderPlus className="h-4 w-4 text-primary shrink-0" />
        ) : (
          <AlertCircle className="h-4 w-4 text-primary shrink-0" />
        )}
        <p className="text-sm text-foreground">
          {noFiles
            ? "Add files to this collection to run detection"
            : `You have ${fileCount} ${fileCount === 1 ? "file" : "files"} — Run Detection to discover signals`}
        </p>
      </div>
      <Button variant="default" size="sm" onClick={onRunDetection}>
        {noFiles ? "Add Files" : "Run Detection"}
      </Button>
    </div>
  );
}
