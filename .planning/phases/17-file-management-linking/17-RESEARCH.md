# Phase 17: File Management & Linking - Research

**Researched:** 2026-02-11
**Domain:** File management UI, file linking workflows, drag-and-drop patterns, table-based file lists
**Confidence:** HIGH

## Summary

This phase implements a comprehensive file management and linking system with two main surfaces: a standalone My Files screen (table-based file list with bulk actions) and in-chat file linking (paperclip dropdown, drag-and-drop, file selection modal). The project already has strong foundations for this work: react-dropzone for drag-and-drop, TanStack Table v8 for table UI, Radix UI primitives for modals/dialogs/dropdowns, and established file upload/onboarding flows. Backend APIs for file CRUD and session file linking are complete with config-driven limits (5 files per session default, 10 ceiling).

The research reveals this is primarily a composition challenge — building new UI surfaces from existing patterns rather than introducing new libraries or paradigms. Critical design decisions (table vs card layout, single vs multi-select, bulk action scope) are locked from CONTEXT.md. Key implementation areas: (1) TanStack Table with row selection for My Files, (2) reusable file selection modal for linking existing files, (3) drag-and-drop overlay for in-chat uploads, (4) config-driven limit enforcement with clear error messages.

**Primary recommendation:** Build on existing FileUploadZone and DataTable patterns. Use TanStack Table's row selection APIs for bulk actions. Reuse Dialog/DropdownMenu components. Fetch file limit from backend config, not hardcoded. Follow accessibility best practices for keyboard navigation and error messaging.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### My Files Screen
- Follow Julius.ai structure as reference
- Table/list view layout (rows with columns, not card grid)
- Columns: file name (with type icon), size, upload date — essential metadata only
- Drag-and-drop zone at top of page (dashed border, upload icon, "Drag files to upload")
- "Upload file" button below the drag zone
- Search bar for filtering files by name
- Bulk action: Delete only (Download and Chat with files removed from bulk actions)
- Checkboxes for multi-select (select-all in header, per-row checkboxes)
- Per-row inline icon: chat icon (start new chat with this file)
- Per-row three-dot menu: View context, Download, Delete

#### File Selection Modal
- Single file selection per modal interaction (not multi-select)
- Shows file name with type icon, size, and upload date (consistent with My Files table)
- Search field at top for filtering files by name
- Already-linked files shown but disabled with a "linked" badge (not hidden)

#### In-Chat File Adding
- Paperclip icon below chat input (like Julius.ai)
- Dropdown on click with three sections:
  - "Upload File" — triggers upload with modal overlay for onboarding
  - "Link Existing File" — opens file selection modal
  - "Recent" section — lists recent files for quick one-click linking
- Clicking a recent file links it immediately (no confirmation step)
- Drag-and-drop works on full chat area — drop zone overlay appears on drag
- Upload from chat uses modal overlay for onboarding (same flow as My Files), file auto-links to session on completion

#### File Context Details
- "View context" opens a modal/dialog showing file profiling details (data summary, columns, row count)
- Same modal used from both My Files three-dot menu and right sidebar info icon — consistent experience

#### File Deletion
- Simple confirmation dialog: "Delete file? This cannot be undone."
- No impact details shown (messages preserved, file context removed — handled silently)

#### File Limit Enforcement
- When user tries to add a file beyond the configured maximum (from config settings), show an error message indicating the limit has been reached
- Limit is config-driven, not hardcoded

### Claude's Discretion
- Empty state design for My Files when no files exist
- Exact styling of drag-and-drop overlay on chat area
- "Recent" section: how many recent files to show, how "recent" is defined
- Loading states and skeleton patterns
- Error handling for failed uploads and failed file linking

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.21.3 | Table state management and UI | Already in use (DataTable.tsx), headless design allows full styling control, excellent TypeScript support, powerful row selection APIs |
| react-dropzone | 14.4.0 | Drag-and-drop file uploads | Already in use (FileUploadZone.tsx), HTML5 compliant, flexible configuration, multi-zone support |
| @tanstack/react-query | 5.90.20 | Data fetching and caching | Already in use for file management (useFileManager.ts), optimistic updates, automatic refetching |
| radix-ui | 1.4.3 | Accessible UI primitives | Already in use for Dialog, DropdownMenu, AlertDialog — consistent component architecture |
| lucide-react | 0.563.0 | Icon library | Already in use project-wide, includes FileSpreadsheet, Paperclip, Upload, Trash2, Download icons |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sonner | 2.0.7 | Toast notifications | Already in use — feedback for upload success, deletion, errors |
| zustand | 5.0.11 | Client state management | Already in use — could extend sessionStore for right panel state |
| next | 16.1.6 | Routing and pages | Already in use — My Files will be a new route under (dashboard) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Table | Plain HTML table + useState | TanStack provides row selection, sorting, filtering out of box. Manual implementation error-prone. |
| react-dropzone | react-dnd | react-dropzone specialized for file uploads (simpler API, smaller bundle). react-dnd for general drag-drop. |
| Radix UI | Headless UI | Both are headless. Radix has better TypeScript support and more comprehensive primitives. Already standardized. |

**Installation:**
No new dependencies required — all needed libraries already installed.

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── app/(dashboard)/
│   └── my-files/
│       └── page.tsx                    # My Files screen (new)
├── components/
│   ├── file/
│   │   ├── FileUploadZone.tsx          # Existing - reuse for My Files
│   │   ├── FileInfoModal.tsx           # Existing - reuse for View context
│   │   ├── MyFilesTable.tsx            # New - TanStack Table with row selection
│   │   ├── FileSelectionModal.tsx      # New - single file picker for linking
│   │   └── FileLinkingDropdown.tsx     # New - paperclip dropdown (Upload/Link/Recent)
│   ├── chat/
│   │   └── ChatInterface.tsx           # Existing - add paperclip button
│   └── session/
│       ├── FileCard.tsx                # Existing - used in LinkedFilesPanel
│       └── LinkedFilesPanel.tsx        # Existing - shows linked files in sidebar
├── hooks/
│   ├── useFileManager.ts               # Existing - add useDownloadFile, useRecentFiles
│   └── useChatSessions.ts              # Existing - add useLinkFileToSession
└── types/
    └── file.ts                          # Existing - may need FileWithLinkedStatus type
```

### Pattern 1: TanStack Table with Row Selection
**What:** Use TanStack Table's built-in row selection state management for checkboxes and bulk actions.
**When to use:** My Files table with multi-select delete.
**Example:**
```typescript
// Source: Verified from project's DataTable.tsx and TanStack Table v8 docs
// https://tanstack.com/table/latest/docs/framework/react/react-table

import { useReactTable, getCoreRowModel, getFilteredRowModel,
         getSortedRowModel, flexRender, type RowSelectionState } from "@tanstack/react-table";

const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
const [globalFilter, setGlobalFilter] = useState("");

const table = useReactTable({
  data: files,
  columns,
  state: {
    rowSelection,
    globalFilter,
  },
  onRowSelectionChange: setRowSelection,
  onGlobalFilterChange: setGlobalFilter,
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSortedRowModel: getSortedRowModel(),
  enableRowSelection: true,
  getRowId: (row) => row.id, // Use file ID as row ID
});

// Column definition with checkbox
const columns: ColumnDef<FileListItem>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected()}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
      />
    ),
  },
  // ... other columns
];

// Get selected rows
const selectedRows = table.getSelectedRowModel().rows;
const selectedFileIds = selectedRows.map(row => row.original.id);
```

### Pattern 2: File Selection Modal for Linking
**What:** Reusable modal that lists user's files, filters by search, shows linked status, returns single selected file.
**When to use:** Link existing file from chat session.
**Example:**
```typescript
// Source: Verified from project's Dialog and useFiles patterns

interface FileSelectionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onFileSelected: (fileId: string) => void;
  linkedFileIds: string[]; // Files already linked to session
}

export function FileSelectionModal({
  open, onOpenChange, onFileSelected, linkedFileIds
}: FileSelectionModalProps) {
  const { data: files } = useFiles();
  const [search, setSearch] = useState("");

  const filteredFiles = files?.filter(f =>
    f.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Select File to Link</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Search files..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <ScrollArea className="max-h-[400px]">
          {filteredFiles?.map(file => {
            const isLinked = linkedFileIds.includes(file.id);
            return (
              <button
                key={file.id}
                disabled={isLinked}
                onClick={() => {
                  onFileSelected(file.id);
                  onOpenChange(false);
                }}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-lg",
                  isLinked ? "opacity-50 cursor-not-allowed" : "hover:bg-accent"
                )}
              >
                <FileSpreadsheet className="h-5 w-5" />
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium">{file.original_filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(file.file_size)} • {formatDate(file.created_at)}
                  </p>
                </div>
                {isLinked && (
                  <Badge variant="secondary">Linked</Badge>
                )}
              </button>
            );
          })}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
```

### Pattern 3: Drag-and-Drop Overlay for Chat Area
**What:** Full-page drop zone overlay that appears when user drags file over chat area. Uses react-dropzone's `noClick` and `noKeyboard` for overlay-only drop.
**When to use:** In-chat file upload via drag-and-drop.
**Example:**
```typescript
// Source: Verified from react-dropzone docs and project's FileUploadZone.tsx
// https://react-dropzone.js.org/

export function ChatInterface({ sessionId }: { sessionId: string }) {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFileToUpload(acceptedFiles[0]);
        setUploadDialogOpen(true); // Open modal for onboarding flow
      }
    },
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
    noClick: true, // Only drag-and-drop, not click-to-upload
    noKeyboard: true,
  });

  return (
    <div {...getRootProps()} className="relative h-full">
      <input {...getInputProps()} />

      {/* Drop overlay */}
      {isDragActive && (
        <div className="absolute inset-0 z-50 bg-primary/5 border-2 border-dashed border-primary rounded-lg flex items-center justify-center">
          <div className="text-center">
            <Upload className="h-12 w-12 mx-auto mb-2 text-primary" />
            <p className="font-medium">Drop file to upload</p>
          </div>
        </div>
      )}

      {/* Chat messages and input */}
      {/* ... */}
    </div>
  );
}
```

### Pattern 4: Config-Driven File Limit Enforcement
**What:** Fetch file limit from backend config endpoint, display clear error when limit reached.
**When to use:** Before attempting to link file to session.
**Example:**
```typescript
// Source: Verified from backend settings.yaml and chat_session.py

// Frontend hook
export function useLinkFileToSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sessionId, fileId }: { sessionId: string; fileId: string }) => {
      const response = await apiClient.post(`/sessions/${sessionId}/files`, {
        file_id: fileId,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to link file");
      }
      return response.json();
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["sessions", variables.sessionId] });
      toast.success("File linked to session");
    },
    onError: (error: Error) => {
      // Backend returns "Maximum 5 files per session" from config
      toast.error(error.message);
    },
  });
}

// Usage in component
const { mutate: linkFile, isLoading } = useLinkFileToSession();

const handleLinkFile = (fileId: string) => {
  linkFile({ sessionId, fileId });
};
```

### Pattern 5: Recent Files for Quick Linking
**What:** Query user's files, sort by created_at DESC, take top N for "Recent" section in dropdown.
**When to use:** Paperclip dropdown Recent section.
**Example:**
```typescript
// Source: Verified from existing useFiles hook pattern

export function useRecentFiles(limit: number = 5) {
  const { data: files, ...rest } = useFiles();

  const recentFiles = useMemo(() => {
    if (!files) return [];
    return [...files]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, limit);
  }, [files, limit]);

  return { data: recentFiles, ...rest };
}

// Usage
const { data: recentFiles } = useRecentFiles(5);
```

### Anti-Patterns to Avoid
- **Hardcoding file limits:** Always fetch from backend config. Limits may change per deployment.
- **Blocking UI during file operations:** Use optimistic updates for linking/unlinking. Show feedback via toast.
- **Hidden linked files in selection modal:** User decision is to show with "linked" badge, not hide. Visibility prevents confusion.
- **Multiple dropzones fighting for events:** Use `noClick: true` for overlay-only drop zones to prevent conflict with click-to-upload zones.
- **Not cleaning up blob URLs:** Always revoke blob URLs after download: `URL.revokeObjectURL(url)` to prevent memory leaks.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table row selection state | Custom checkbox state tracking | TanStack Table's `enableRowSelection` and `rowSelection` state | Handles select-all, partial selection, keyboard nav, performance optimization automatically |
| File drag-and-drop detection | Custom drag event handlers | react-dropzone's `useDropzone` hook | Cross-browser compatibility, mobile support, file validation, MIME type checking built-in |
| File download from blob | Manual fetch + link creation | Standardized fetch → blob → URL.createObjectURL → link.click pattern | Security (authenticated requests), memory management (URL cleanup), error handling |
| Modal accessibility | Custom focus trap and escape handling | Radix UI Dialog primitive | ARIA attributes, focus management, scroll locking, escape key handling per WAI-ARIA spec |
| Global search/filter for tables | Custom filter logic | TanStack Table's `getFilteredRowModel` with `globalFilter` | Optimized search across all columns, debouncing, memoization |

**Key insight:** File management UIs have hidden complexity: accessible keyboard navigation, screen reader announcements, error recovery, memory management for blob URLs, consistent state synchronization between server and client. Modern libraries (TanStack Table, react-dropzone, Radix UI) encode years of accessibility testing and edge case handling. Custom implementations miss these details and create maintenance burden.

## Common Pitfalls

### Pitfall 1: Blob URL Memory Leaks
**What goes wrong:** Creating blob URLs with `URL.createObjectURL()` for downloads but never revoking them causes memory to grow indefinitely.
**Why it happens:** Blob URLs stay in memory until page unload unless explicitly revoked.
**How to avoid:** Always call `URL.revokeObjectURL(url)` after download completes or component unmounts.
**Warning signs:** Memory usage grows over time, especially with repeated downloads.
**Code:**
```typescript
// BAD
const downloadFile = async (fileId: string) => {
  const response = await apiClient.get(`/files/${fileId}/download`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  // Missing: URL.revokeObjectURL(url)
};

// GOOD
const downloadFile = async (fileId: string) => {
  const response = await apiClient.get(`/files/${fileId}/download`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  } finally {
    URL.revokeObjectURL(url); // Clean up immediately after download
  }
};
```

### Pitfall 2: Race Conditions in File Linking
**What goes wrong:** User clicks "link file" multiple times rapidly, causing duplicate API calls and potential double-linking attempts.
**Why it happens:** No loading state or debounce on link action.
**How to avoid:** Disable link button while mutation is pending, use TanStack Query's `isLoading` state.
**Warning signs:** API errors like "File already linked to session" despite UI showing file as not linked.
**Code:**
```typescript
// BAD
const handleLinkFile = (fileId: string) => {
  linkFileMutation({ sessionId, fileId });
  // No disabled state, can click multiple times
};

// GOOD
const { mutate: linkFile, isLoading } = useLinkFileToSession();

<Button
  onClick={() => linkFile({ sessionId, fileId })}
  disabled={isLoading} // Prevents double-click
>
  {isLoading ? "Linking..." : "Link File"}
</Button>
```

### Pitfall 3: Not Handling Partial Selection State
**What goes wrong:** Select-all checkbox doesn't show indeterminate state when only some rows are selected, confusing users about selection state.
**Why it happens:** Checkbox only has checked/unchecked, not indeterminate.
**How to avoid:** Use TanStack Table's `getIsSomePageRowsSelected()` for indeterminate state.
**Warning signs:** Users confused about selection state, unexpected bulk action results.
**Code:**
```typescript
// BAD
<Checkbox
  checked={table.getIsAllPageRowsSelected()}
  onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
/>

// GOOD
<Checkbox
  checked={table.getIsAllPageRowsSelected()}
  indeterminate={table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected()}
  onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
/>
```

### Pitfall 4: File Search Not Debounced
**What goes wrong:** Global filter triggers re-render on every keystroke, causing performance issues with large file lists.
**Why it happens:** `setGlobalFilter` called directly from `onChange` without debounce.
**How to avoid:** Use `useMemo` with debounce or TanStack Table's built-in filtering which is already optimized.
**Warning signs:** Laggy typing in search input, high CPU usage during search.
**Code:**
```typescript
// BAD
<Input
  value={globalFilter}
  onChange={(e) => setGlobalFilter(e.target.value)} // Re-renders every keystroke
/>

// GOOD - TanStack Table handles this efficiently
// Just use globalFilter state as-is, Table memoizes filter computations
<Input
  value={globalFilter}
  onChange={(e) => setGlobalFilter(e.target.value)}
/>
// Table internally debounces and memoizes getFilteredRowModel()
```

### Pitfall 5: Missing Accessible Labels for Icon Buttons
**What goes wrong:** Icon-only buttons (three-dot menu, download, delete) have no text, making them unusable for screen reader users.
**Why it happens:** Forgetting `aria-label` or visually hidden text.
**How to avoid:** Always provide `aria-label` or use Tooltip with descriptive text.
**Warning signs:** Screen reader announces "button" with no context.
**Code:**
```typescript
// BAD
<Button variant="ghost" size="icon" onClick={handleDelete}>
  <Trash2 className="h-4 w-4" />
</Button>

// GOOD
<Tooltip>
  <TooltipTrigger asChild>
    <Button
      variant="ghost"
      size="icon"
      onClick={handleDelete}
      aria-label="Delete file"
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  </TooltipTrigger>
  <TooltipContent>Delete file</TooltipContent>
</Tooltip>
```

### Pitfall 6: Stale File List After Upload/Delete
**What goes wrong:** After uploading or deleting a file, the file list doesn't update until manual page refresh.
**Why it happens:** Query cache not invalidated after mutation.
**How to avoid:** Use TanStack Query's `invalidateQueries` in mutation's `onSuccess`.
**Warning signs:** User uploads file, doesn't see it in list. User deletes file, still sees it.
**Code:**
```typescript
// Already handled correctly in existing useDeleteFile hook
export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fileId: string) => {
      const response = await apiClient.delete(`/files/${fileId}`);
      if (!response.ok) throw new Error("Failed to delete file");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["files"] }); // ✓ Correct
    },
  });
}
```

## Code Examples

Verified patterns from official sources:

### File Download Implementation
```typescript
// Source: https://blog.filestack.com/the-ultimate-guide-to-file-downloads-in-react-using-apis/
// Verified: Blob download with proper cleanup

export function useDownloadFile() {
  return useMutation({
    mutationFn: async ({ fileId, filename }: { fileId: string; filename: string }) => {
      const response = await apiClient.get(`/files/${fileId}/download`);
      if (!response.ok) {
        throw new Error("Failed to download file");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } finally {
        URL.revokeObjectURL(url); // Clean up
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to download file");
    },
  });
}
```

### Bulk Delete with Confirmation
```typescript
// Source: Verified from project's AlertDialog pattern and TanStack Table selection

export function MyFilesTable({ files }: { files: FileListItem[] }) {
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const { mutate: deleteFile } = useDeleteFile();

  const table = useReactTable({
    data: files,
    columns,
    state: { rowSelection },
    onRowSelectionChange: setRowSelection,
    enableRowSelection: true,
    getRowId: (row) => row.id,
    getCoreRowModel: getCoreRowModel(),
  });

  const selectedRows = table.getSelectedRowModel().rows;
  const selectedCount = selectedRows.length;

  const handleBulkDelete = () => {
    selectedRows.forEach(row => {
      deleteFile(row.original.id);
    });
    setRowSelection({});
    setDeleteDialogOpen(false);
    toast.success(`${selectedCount} file(s) deleted`);
  };

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {selectedCount > 0 ? `${selectedCount} selected` : `${files.length} files`}
        </p>
        {selectedCount > 0 && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteDialogOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Selected
          </Button>
        )}
      </div>

      <Table>
        {/* Table implementation */}
      </Table>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedCount} file(s)?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBulkDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
```

### Paperclip Dropdown with Sections
```typescript
// Source: Verified from project's DropdownMenu pattern and requirements

export function FileLinkingDropdown({ sessionId }: { sessionId: string }) {
  const [selectionModalOpen, setSelectionModalOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const { data: recentFiles } = useRecentFiles(5);
  const { mutate: linkFile } = useLinkFileToSession();

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Add file to chat">
            <Paperclip className="h-5 w-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuItem onClick={() => setUploadDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload File
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setSelectionModalOpen(true)}>
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Link Existing File
          </DropdownMenuItem>

          {recentFiles && recentFiles.length > 0 && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Recent</DropdownMenuLabel>
              {recentFiles.map(file => (
                <DropdownMenuItem
                  key={file.id}
                  onClick={() => linkFile({ sessionId, fileId: file.id })}
                >
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                  <span className="truncate">{file.original_filename}</span>
                </DropdownMenuItem>
              ))}
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
          </DialogHeader>
          <FileUploadZone
            onUploadComplete={(fileId) => {
              linkFile({ sessionId, fileId });
              setUploadDialogOpen(false);
            }}
          />
        </DialogContent>
      </Dialog>

      <FileSelectionModal
        open={selectionModalOpen}
        onOpenChange={setSelectionModalOpen}
        onFileSelected={(fileId) => linkFile({ sessionId, fileId })}
        linkedFileIds={[]} // Get from session detail
      />
    </>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-table v7 | TanStack Table v8 | 2022 | TypeScript-first rewrite, headless design, framework-agnostic, better tree-shaking |
| Custom drag-drop handlers | react-dropzone hook | N/A (industry standard) | Simplified API, better mobile support, accessibility improvements |
| Imperative modals (ReactDOM.createPortal) | Radix UI Dialog primitive | 2021-2023 adoption | Declarative API, accessibility (ARIA) built-in, focus management automatic |
| File download via hidden iframe | Blob + URL.createObjectURL | ~2015 (Blob API standard) | Better security (no external URLs), memory control, works with authenticated APIs |
| Class-based state management | React hooks (useState, useMemo) | 2019 (React 16.8) | Simpler composition, better code reuse, easier testing |

**Deprecated/outdated:**
- TanStack Table v7 `useTable` hook → v8 `useReactTable` (migration required for column definitions, cell rendering)
- Dropzone.js (non-React library) → react-dropzone (React-specific, hook-based)
- Checkbox without indeterminate state for partial selection → Modern pattern uses tri-state (checked, unchecked, indeterminate)

## Open Questions

1. **Backend download endpoint implementation**
   - What we know: Backend has file CRUD endpoints but no explicit `/files/{id}/download` endpoint in reviewed code
   - What's unclear: Does backend serve files directly, or return pre-signed URLs? How is authentication handled?
   - Recommendation: Implement `/files/{id}/download` endpoint that returns file as response with proper Content-Disposition header, or add to FILE-07 requirement implementation

2. **File size formatting consistency**
   - What we know: Files have `file_size` in bytes (from backend schema)
   - What's unclear: Is there a shared utility for formatting bytes to KB/MB/GB?
   - Recommendation: Create shared `formatFileSize(bytes: number): string` utility, use across My Files table and file selection modal

3. **Recent files time window definition**
   - What we know: User decision defers to Claude's discretion
   - What's unclear: Define "recent" as last 5 uploaded? Last 7 days? Most recently used?
   - Recommendation: Use "last 5 uploaded" (sort by created_at DESC, limit 5) — simple, predictable, no time dependency

4. **File type icon mapping**
   - What we know: lucide-react has FileSpreadsheet icon, used for all files currently
   - What's unclear: Differentiate .csv vs .xlsx vs .xls with different icons?
   - Recommendation: Use FileSpreadsheet for all (consistent with existing FileSidebar.tsx), or add file extension badge if visual differentiation needed

## Sources

### Primary (HIGH confidence)
- Project codebase: frontend/package.json, frontend/src/components (Dialog, Table, DropdownMenu, FileUploadZone, DataTable)
- Project codebase: backend/app/routers/files.py, backend/app/routers/chat_sessions.py, backend/app/config/settings.yaml
- Project codebase: frontend/src/hooks/useFileManager.ts
- [TanStack Table v8 Official Docs](https://tanstack.com/table/latest/docs/framework/react/react-table)
- [react-dropzone Official Docs](https://react-dropzone.js.org/)
- [Radix UI Primitives Docs](https://www.radix-ui.com/primitives)
- [lucide-react Icon Library](https://lucide.dev/guide/packages/lucide-react)

### Secondary (MEDIUM confidence)
- [TanStack Table Migration Guide](https://tanstack.com/table/latest/docs/guide/migrating) - v7 to v8 migration patterns
- [LogRocket: TanStack Table Guide](https://blog.logrocket.com/tanstack-table-formerly-react-table/) - Best practices and patterns
- [react-dropzone GitHub](https://github.com/react-dropzone/react-dropzone) - Multiple dropzone examples
- [Radix UI Checkbox](https://www.radix-ui.com/primitives/docs/components/checkbox) - Tri-state checkbox pattern
- [Filestack: File Download in React](https://blog.filestack.com/the-ultimate-guide-to-file-downloads-in-react-using-apis/) - Blob download patterns
- [Uploadcare: File Uploader UX](https://uploadcare.com/blog/file-uploader-ux-best-practices/) - Error handling and user feedback
- [Eleken: Bulk Actions UX](https://www.eleken.co/blog-posts/bulk-actions-ux) - Checkbox selection and bulk action patterns

### Tertiary (LOW confidence)
- [PatternFly Bulk Selection](https://www.patternfly.org/patterns/bulk-selection/) - Enterprise UI patterns (design reference only)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, versions verified from package.json
- Architecture: HIGH - Patterns verified from existing codebase (DataTable.tsx, FileUploadZone.tsx, Dialog usage)
- Pitfalls: HIGH - Common React/TypeScript pitfalls verified with official docs and project patterns
- Backend integration: HIGH - API endpoints and config verified from backend codebase
- UX patterns: MEDIUM - Bulk actions and file management patterns from industry sources, not project-specific

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (30 days - stable libraries, Next.js framework)

---

## Recommendations Summary

1. **Reuse existing patterns extensively**: FileUploadZone, Dialog, DropdownMenu, AlertDialog, DataTable — all patterns needed for this phase already exist in the codebase
2. **TanStack Table for My Files**: Use `enableRowSelection` with `rowSelection` state for checkboxes and bulk actions
3. **Single file selection modal**: Build new component based on Dialog primitive, filter by search, show linked files as disabled
4. **Paperclip dropdown**: Use DropdownMenu with three sections (Upload File, Link Existing, Recent), Recent section shows last 5 files by created_at
5. **Drag-and-drop overlay**: Use react-dropzone with `noClick: true` on full chat area for drop-only zone
6. **Config-driven limits**: Fetch from backend `/config` or parse error messages from link API (`Maximum 5 files per session`)
7. **Accessibility first**: Always provide aria-labels for icon buttons, use Tooltip for visual context, handle keyboard navigation
8. **Error handling**: Clear toast messages for limit exceeded, upload failures, linking failures — follow existing toast patterns with sonner
9. **Memory management**: Always revoke blob URLs after download
10. **Optimistic updates**: Use TanStack Query's invalidateQueries after mutations to keep UI in sync with server

This phase is well-supported by existing infrastructure. Primary work is composition and UI wiring, not new library integration.
