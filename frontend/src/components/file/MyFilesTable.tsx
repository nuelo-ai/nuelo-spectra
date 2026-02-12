"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type RowSelectionState,
} from "@tanstack/react-table";
import {
  FileSpreadsheet,
  FileText,
  Search,
  MoreHorizontal,
  Eye,
  Download,
  Trash2,
  MessageSquarePlus,
} from "lucide-react";
import { toast } from "sonner";
import { useCreateSession, useLinkFile } from "@/hooks/useSessionMutations";
import {
  useDeleteFile,
  useDownloadFile,
  useBulkDeleteFiles,
} from "@/hooks/useFileManager";
import { formatFileSize } from "@/lib/utils";
import type { FileListItem } from "@/types/file";
import { FileContextModal } from "@/components/file/FileContextModal";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface MyFilesTableProps {
  files: FileListItem[];
  isLoading?: boolean;
}

/**
 * TanStack Table for the My Files screen.
 * Supports row selection, search filtering, bulk delete, and per-row actions
 * (view context, download, delete, start chat).
 */
export function MyFilesTable({ files, isLoading }: MyFilesTableProps) {
  const router = useRouter();

  // Mutations
  const createSession = useCreateSession();
  const linkFile = useLinkFile();
  const deleteFile = useDeleteFile();
  const downloadFile = useDownloadFile();
  const bulkDeleteFiles = useBulkDeleteFiles();

  // Table state
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");

  // Modal / dialog state
  const [contextFileId, setContextFileId] = useState<string | null>(null);
  const [deleteFileId, setDeleteFileId] = useState<string | null>(null);
  const [deleteFileName, setDeleteFileName] = useState("");
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);

  // Track chat creation in progress per row
  const [chatPendingFileId, setChatPendingFileId] = useState<string | null>(
    null
  );

  const handleStartChat = async (fileId: string, filename: string) => {
    try {
      setChatPendingFileId(fileId);
      const session = await createSession.mutateAsync("New Chat");
      await linkFile.mutateAsync({ sessionId: session.id, fileId });
      toast.success(`Chat started with ${filename}`);
      router.push(`/sessions/${session.id}`);
    } catch {
      toast.error("Failed to start chat");
    } finally {
      setChatPendingFileId(null);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteFileId) return;
    try {
      await deleteFile.mutateAsync(deleteFileId);
      toast.success("File deleted");
    } catch {
      toast.error("Failed to delete file");
    }
    setDeleteFileId(null);
    setDeleteFileName("");
  };

  const handleBulkDeleteConfirm = async () => {
    const selectedIds = Object.keys(rowSelection).filter(
      (key) => rowSelection[key]
    );
    // selectedIds ARE already file UUIDs (via getRowId: row => row.id)
    if (selectedIds.length === 0) return;
    try {
      await bulkDeleteFiles.mutateAsync(selectedIds);
      toast.success(`${selectedIds.length} file(s) deleted`);
      setRowSelection({});
    } catch {
      toast.error("Failed to delete some files");
    }
    setBulkDeleteOpen(false);
  };

  const columns: ColumnDef<FileListItem>[] = [
    // 1. Select checkbox column
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={
            table.getIsAllPageRowsSelected() ||
            (table.getIsSomePageRowsSelected() && "indeterminate")
          }
          onCheckedChange={(value) =>
            table.toggleAllPageRowsSelected(!!value)
          }
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label={`Select ${row.original.original_filename}`}
        />
      ),
      enableSorting: false,
      enableGlobalFilter: false,
    },
    // 2. File name column
    {
      accessorKey: "original_filename",
      header: "Name",
      cell: ({ row }) => {
        const filename = row.original.original_filename;
        const ext = filename.split(".").pop()?.toLowerCase();
        const isSpreadsheet = ["csv", "xls", "xlsx"].includes(ext ?? "");
        return (
          <div className="flex items-center gap-2 min-w-0">
            {isSpreadsheet ? (
              <FileSpreadsheet className="h-4 w-4 shrink-0 text-green-600" />
            ) : (
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
            )}
            <span className="truncate font-medium">{filename}</span>
          </div>
        );
      },
    },
    // 3. Size column
    {
      accessorKey: "file_size",
      header: () => <span className="text-right block">Size</span>,
      cell: ({ row }) => (
        <span className="text-right block text-muted-foreground">
          {formatFileSize(row.original.file_size)}
        </span>
      ),
      enableGlobalFilter: false,
    },
    // 4. Upload date column
    {
      accessorKey: "created_at",
      header: "Uploaded",
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {new Date(row.original.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </span>
      ),
      enableGlobalFilter: false,
    },
    // 5. Chat icon column
    {
      id: "chat",
      header: "",
      cell: ({ row }) => {
        const isPending = chatPendingFileId === row.original.id;
        return (
          <Button
            variant="ghost"
            size="icon-xs"
            disabled={isPending}
            onClick={() =>
              handleStartChat(
                row.original.id,
                row.original.original_filename
              )
            }
            aria-label={`Start chat with ${row.original.original_filename}`}
          >
            <MessageSquarePlus className="h-4 w-4" />
          </Button>
        );
      },
      enableSorting: false,
      enableGlobalFilter: false,
    },
    // 6. Actions column (three-dot menu)
    {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-xs">
              <MoreHorizontal className="h-4 w-4" />
              <span className="sr-only">Open menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => setContextFileId(row.original.id)}
            >
              <Eye className="h-4 w-4" />
              View context
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() =>
                downloadFile.mutate({
                  fileId: row.original.id,
                  filename: row.original.original_filename,
                })
              }
            >
              <Download className="h-4 w-4" />
              Download
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              variant="destructive"
              onClick={() => {
                setDeleteFileId(row.original.id);
                setDeleteFileName(row.original.original_filename);
              }}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
      enableSorting: false,
      enableGlobalFilter: false,
    },
  ];

  const table = useReactTable({
    data: files,
    columns,
    state: { rowSelection, globalFilter },
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: true,
    getRowId: (row) => row.id,
  });

  const selectedCount = Object.keys(rowSelection).filter(
    (k) => rowSelection[k]
  ).length;

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-6" />
            <Skeleton className="h-4 w-6" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search bar and bulk actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-3">
          {selectedCount > 0 ? (
            <>
              <span className="text-sm text-muted-foreground">
                {selectedCount} selected
              </span>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setBulkDeleteOpen(true)}
                className="gap-1.5"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete Selected
              </Button>
            </>
          ) : (
            <span className="text-sm text-muted-foreground">
              {files.length} file{files.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  No files found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* FileContextModal */}
      <FileContextModal
        fileId={contextFileId}
        onClose={() => setContextFileId(null)}
      />

      {/* Single file delete AlertDialog */}
      <AlertDialog
        open={!!deleteFileId}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteFileId(null);
            setDeleteFileName("");
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete file?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &ldquo;{deleteFileName}&rdquo;?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDeleteConfirm}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bulk delete AlertDialog */}
      <AlertDialog open={bulkDeleteOpen} onOpenChange={setBulkDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedCount} file(s)?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. All selected files will be
              permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleBulkDeleteConfirm}
            >
              Delete {selectedCount} file(s)
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
