"use client";

import { useState, useMemo } from "react";
import { Search, FileSpreadsheet, FileText } from "lucide-react";
import { useFiles } from "@/hooks/useFileManager";
import { formatFileSize } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface FileSelectionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onFileSelected: (fileId: string) => void;
  linkedFileIds: string[]; // Files already linked to session (shown disabled with badge)
}

/**
 * Single-select file picker modal for linking existing files to a session.
 * Shows all user files with search, linked badge on already-linked files,
 * and single-click selection behavior.
 */
export function FileSelectionModal({
  open,
  onOpenChange,
  onFileSelected,
  linkedFileIds,
}: FileSelectionModalProps) {
  const { data: files, isLoading } = useFiles();
  const [searchQuery, setSearchQuery] = useState("");

  const linkedSet = useMemo(() => new Set(linkedFileIds), [linkedFileIds]);

  const filteredFiles = useMemo(() => {
    if (!files) return [];
    if (!searchQuery.trim()) return files;
    const query = searchQuery.toLowerCase();
    return files.filter((f) =>
      f.original_filename.toLowerCase().includes(query)
    );
  }, [files, searchQuery]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const handleSelect = (fileId: string) => {
    onFileSelected(fileId);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Link Existing File</DialogTitle>
        </DialogHeader>

        {/* Search field */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="pl-9"
          />
        </div>

        {/* File list */}
        <ScrollArea className="max-h-[400px]">
          <div className="space-y-1">
            {isLoading && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                Loading files...
              </div>
            )}

            {!isLoading && files && files.length === 0 && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No files available. Upload files from My Files first.
              </div>
            )}

            {!isLoading &&
              files &&
              files.length > 0 &&
              filteredFiles.length === 0 && (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No files match your search.
                </div>
              )}

            {filteredFiles.map((file) => {
              const isLinked = linkedSet.has(file.id);
              const isSpreadsheet = ["csv", "xlsx", "xls"].some(
                (ext) =>
                  file.file_type?.toLowerCase().includes(ext) ||
                  file.original_filename?.toLowerCase().endsWith(`.${ext}`)
              );
              const FileIcon = isSpreadsheet ? FileSpreadsheet : FileText;

              return (
                <button
                  key={file.id}
                  type="button"
                  disabled={isLinked}
                  onClick={() => handleSelect(file.id)}
                  className={`w-full flex items-center gap-3 rounded-md px-3 py-2.5 text-left transition-colors ${
                    isLinked
                      ? "opacity-50 cursor-not-allowed"
                      : "hover:bg-accent cursor-pointer"
                  }`}
                >
                  <FileIcon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">
                      {file.original_filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.file_size)} &middot;{" "}
                      {formatDate(file.created_at)}
                    </p>
                  </div>
                  {isLinked && <Badge variant="secondary">Linked</Badge>}
                </button>
              );
            })}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
