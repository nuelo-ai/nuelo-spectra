"use client";

import { useCallback } from "react";
import { FileSpreadsheet, FileText } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { MOCK_FILES, type FileItem, type ProfilingStatus } from "@/lib/mock-data";

// --- Status badge rendering ---

function StatusBadge({ status }: { status: ProfilingStatus }) {
  switch (status) {
    case "ready":
      return (
        <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/15">
          Ready
        </Badge>
      );
    case "profiling":
      return (
        <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/30 hover:bg-amber-500/15">
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
          Profiling...
        </Badge>
      );
    case "error":
      return (
        <Badge className="bg-red-500/15 text-red-400 border-red-500/30 hover:bg-red-500/15">
          Error
        </Badge>
      );
  }
}

// --- File type icon ---

function FileTypeIcon({ type }: { type: FileItem["type"] }) {
  switch (type) {
    case "csv":
      return <FileText className="h-4 w-4 text-emerald-400 shrink-0" />;
    case "xlsx":
    case "xls":
      return <FileSpreadsheet className="h-4 w-4 text-blue-400 shrink-0" />;
    default:
      return <FileText className="h-4 w-4 text-muted-foreground shrink-0" />;
  }
}

// --- Props ---

interface FileTableProps {
  selectedFileIds: string[];
  onSelectedChange: (ids: string[]) => void;
  onFileClick: (file: FileItem) => void;
}

export function FileTable({
  selectedFileIds,
  onSelectedChange,
  onFileClick,
}: FileTableProps) {
  const allSelected =
    MOCK_FILES.length > 0 && selectedFileIds.length === MOCK_FILES.length;
  const someSelected =
    selectedFileIds.length > 0 && selectedFileIds.length < MOCK_FILES.length;

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      onSelectedChange([]);
    } else {
      onSelectedChange(MOCK_FILES.map((f) => f.id));
    }
  }, [allSelected, onSelectedChange]);

  const handleSelectOne = useCallback(
    (id: string) => {
      if (selectedFileIds.includes(id)) {
        onSelectedChange(selectedFileIds.filter((fid) => fid !== id));
      } else {
        onSelectedChange([...selectedFileIds, id]);
      }
    },
    [selectedFileIds, onSelectedChange]
  );

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[40px]">
              <Checkbox
                checked={allSelected ? true : someSelected ? "indeterminate" : false}
                onCheckedChange={handleSelectAll}
                aria-label="Select all files"
              />
            </TableHead>
            <TableHead>File Name</TableHead>
            <TableHead className="w-[100px]">Size</TableHead>
            <TableHead className="w-[120px]">Upload Date</TableHead>
            <TableHead className="w-[120px]">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {MOCK_FILES.map((file) => {
            const isSelected = selectedFileIds.includes(file.id);
            return (
              <TableRow
                key={file.id}
                data-state={isSelected ? "selected" : undefined}
                className="group"
              >
                <TableCell>
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => handleSelectOne(file.id)}
                    aria-label={`Select ${file.name}`}
                  />
                </TableCell>
                <TableCell>
                  <button
                    type="button"
                    onClick={() => onFileClick(file)}
                    className={cn(
                      "flex items-center gap-2 text-left hover:text-primary transition-colors",
                      "focus-visible:outline-none focus-visible:underline"
                    )}
                  >
                    <FileTypeIcon type={file.type} />
                    <span className="font-medium">{file.name}</span>
                  </button>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {file.size}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {file.uploadDate}
                </TableCell>
                <TableCell>
                  <StatusBadge status={file.profilingStatus} />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
