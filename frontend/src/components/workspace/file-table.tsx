"use client";

import { useCallback } from "react";
import { FileSpreadsheet, FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { formatFileSize } from "@/lib/utils";
import type { CollectionFile } from "@/types/workspace";

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function FileTypeIcon({ filename }: { filename: string }) {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "csv":
      return <FileText className="h-4 w-4 text-emerald-400 shrink-0" />;
    case "xlsx":
    case "xls":
      return <FileSpreadsheet className="h-4 w-4 text-blue-400 shrink-0" />;
    default:
      return <FileText className="h-4 w-4 text-muted-foreground shrink-0" />;
  }
}

interface FileTableProps {
  files: CollectionFile[];
  selectedFileIds: string[];
  onSelectedChange: (ids: string[]) => void;
  onFileClick: (file: CollectionFile) => void;
  /** Show checkboxes for selection */
  selectable?: boolean;
  /** Limit rows displayed (for compact overview mode) */
  maxRows?: number;
  /** Show remove button per row */
  onRemoveFile?: (fileId: string) => void;
}

export function FileTable({
  files,
  selectedFileIds,
  onSelectedChange,
  onFileClick,
  selectable = true,
  maxRows,
  onRemoveFile,
}: FileTableProps) {
  const displayFiles = maxRows ? files.slice(0, maxRows) : files;

  const allSelected =
    files.length > 0 && selectedFileIds.length === files.length;
  const someSelected =
    selectedFileIds.length > 0 && selectedFileIds.length < files.length;

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      onSelectedChange([]);
    } else {
      onSelectedChange(files.map((f) => f.id));
    }
  }, [allSelected, onSelectedChange, files]);

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

  if (files.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">No files uploaded yet.</p>
    );
  }

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {selectable && (
              <TableHead className="w-[40px]">
                <Checkbox
                  checked={
                    allSelected ? true : someSelected ? "indeterminate" : false
                  }
                  onCheckedChange={handleSelectAll}
                  aria-label="Select all files"
                />
              </TableHead>
            )}
            <TableHead>File Name</TableHead>
            <TableHead className="w-[100px]">Size</TableHead>
            <TableHead className="w-[120px]">Added</TableHead>
            {onRemoveFile && <TableHead className="w-[50px]" />}
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayFiles.map((file) => {
            const isSelected = selectedFileIds.includes(file.id);
            return (
              <TableRow
                key={file.id}
                data-state={isSelected ? "selected" : undefined}
                className="group"
              >
                {selectable && (
                  <TableCell>
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => handleSelectOne(file.id)}
                      aria-label={`Select ${file.filename}`}
                    />
                  </TableCell>
                )}
                <TableCell>
                  <button
                    type="button"
                    onClick={() => onFileClick(file)}
                    className={cn(
                      "flex items-center gap-2 text-left hover:text-primary transition-colors",
                      "focus-visible:outline-none focus-visible:underline"
                    )}
                  >
                    <FileTypeIcon filename={file.filename} />
                    <span className="font-medium">{file.filename}</span>
                  </button>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {file.file_size ? formatFileSize(file.file_size) : "—"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(file.added_at)}
                </TableCell>
                {onRemoveFile && (
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveFile(file.file_id);
                      }}
                      aria-label={`Remove ${file.filename} from collection`}
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
