"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useCreateSession, useLinkFile } from "@/hooks/useSessionMutations";
import { useAddLocalMessage } from "@/hooks/useChatMessages";
import { useSearchToggle } from "@/hooks/useSearchToggle";
import { useFiles, useRecentFiles } from "@/hooks/useFileManager";
import { ChatInput } from "@/components/chat/ChatInput";
import { QuerySuggestions } from "@/components/chat/QuerySuggestions";
import { FileLinkingDropdown } from "@/components/file/FileLinkingDropdown";
import { FileSelectionModal } from "@/components/file/FileSelectionModal";
import { FileUploadZone } from "@/components/file/FileUploadZone";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import {
  Sparkles,
  Paperclip,
  Upload,
  FileSpreadsheet,
  X,
} from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface WelcomeScreenProps {
  /** If provided, the session already exists (user navigated to /sessions/[id] with no messages yet) */
  sessionId?: string;
}

/**
 * Welcome screen shown when a user starts a new session or has no messages yet.
 * Displays a warm, personalized greeting with the user's first name,
 * an always-active chat input, and query suggestions when files are linked.
 *
 * Session creation is deferred: no session is created in the DB until the user
 * sends their first message. Files are tracked in local state until then.
 */
export function WelcomeScreen({ sessionId }: WelcomeScreenProps) {
  const { user } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: sessionDetail } = useSessionDetail(sessionId ?? null);
  const createSession = useCreateSession();
  const { mutateAsync: linkFileAsync } = useLinkFile();
  const addLocalMessage = useAddLocalMessage();
  const searchToggle = useSearchToggle();
  const creatingSession = useRef(false);

  // Pending file tracking for pre-session state
  const [pendingFileIds, setPendingFileIds] = useState<string[]>([]);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectionModalOpen, setSelectionModalOpen] = useState(false);
  const [dragUploadDialogOpen, setDragUploadDialogOpen] = useState(false);
  const [droppedFiles, setDroppedFiles] = useState<File[]>([]);
  const prevFileIdsRef = useRef<Set<string>>(new Set());

  const { data: allFiles } = useFiles();
  const { data: recentFiles } = useRecentFiles(5);
  const pendingMessageSent = useRef(false);

  // Drag-and-drop support
  const onWelcomeDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      prevFileIdsRef.current = new Set(allFiles?.map((f) => f.id) || []);
      setDroppedFiles(acceptedFiles);
      setDragUploadDialogOpen(true);
    },
    [allFiles]
  );

  const { getRootProps: getWelcomeDropProps, getInputProps: getWelcomeDropInput, isDragActive: isWelcomeDragActive } = useDropzone({
    onDrop: onWelcomeDrop,
    noClick: true,
    noKeyboard: true,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
  });

  // Auto-send pending message after lazy session creation + navigation
  // Instead of starting the stream here (which gets killed on unmount),
  // we store pending stream info and add an optimistic message so ChatInterface
  // picks up the stream after it mounts.
  useEffect(() => {
    if (!sessionId || pendingMessageSent.current) return;
    const linkedFileCount = sessionDetail?.files?.length ?? 0;
    if (linkedFileCount === 0) return;

    const pendingMessage = sessionStorage.getItem("spectra_pending_message");
    if (!pendingMessage) return;

    pendingMessageSent.current = true;
    const searchEnabled = sessionStorage.getItem("spectra_pending_search") === "1";
    sessionStorage.removeItem("spectra_pending_message");
    sessionStorage.removeItem("spectra_pending_search");

    sessionStorage.setItem("spectra_pending_stream", JSON.stringify({
      message: pendingMessage,
      searchEnabled,
    }));
    addLocalMessage(sessionId, pendingMessage);
  }, [sessionId, sessionDetail?.files?.length, addLocalMessage]);

  const firstName = user?.first_name || "there";
  const linkedFiles = sessionDetail?.files ?? [];
  const hasLinkedFiles = sessionId ? linkedFiles.length > 0 : pendingFileIds.length > 0;

  // Get display info for pending files
  const pendingFileNames = pendingFileIds
    .map((id) => allFiles?.find((f) => f.id === id)?.original_filename)
    .filter(Boolean) as string[];

  const handlePendingFileSelect = (fileId: string) => {
    if (!pendingFileIds.includes(fileId)) {
      setPendingFileIds((prev) => [...prev, fileId]);
      const file = allFiles?.find((f) => f.id === fileId);
      if (file) toast.success(`${file.original_filename} selected`);
    }
  };

  const handlePendingRemove = (fileId: string) => {
    setPendingFileIds((prev) => prev.filter((id) => id !== fileId));
  };

  const handleOpenUploadDialog = () => {
    prevFileIdsRef.current = new Set(allFiles?.map((f) => f.id) || []);
    setUploadDialogOpen(true);
  };

  const handleUploadComplete = async () => {
    setUploadDialogOpen(false);
    await queryClient.invalidateQueries({ queryKey: ["files"] });
    await queryClient.refetchQueries({ queryKey: ["files"] });
    const updatedFiles = queryClient.getQueryData<
      { id: string; original_filename: string }[]
    >(["files"]);
    if (updatedFiles) {
      const newFiles = updatedFiles.filter(
        (f) => !prevFileIdsRef.current.has(f.id)
      );
      for (const newFile of newFiles) {
        if (!pendingFileIds.includes(newFile.id)) {
          setPendingFileIds((prev) => [...prev, newFile.id]);
          toast.success(`${newFile.original_filename} selected`);
        }
      }
    }
  };

  const handleDragUploadComplete = async () => {
    setDragUploadDialogOpen(false);
    setDroppedFiles([]);
    await queryClient.invalidateQueries({ queryKey: ["files"] });
    await queryClient.refetchQueries({ queryKey: ["files"] });
    const updatedFiles = queryClient.getQueryData<
      { id: string; original_filename: string }[]
    >(["files"]);
    if (updatedFiles) {
      const newFiles = updatedFiles.filter(
        (f) => !prevFileIdsRef.current.has(f.id)
      );
      if (sessionId) {
        // Session exists: link files directly via API
        for (const newFile of newFiles) {
          linkFileAsync({ sessionId, fileId: newFile.id })
            .then(() => toast.success(`${newFile.original_filename} linked to session`))
            .catch((error: Error) => toast.error(error.message));
        }
      } else {
        // No session: add to pending files
        for (const newFile of newFiles) {
          if (!pendingFileIds.includes(newFile.id)) {
            setPendingFileIds((prev) => [...prev, newFile.id]);
            toast.success(`${newFile.original_filename} selected`);
          }
        }
      }
    }
  };

  const handleSend = async (message: string) => {
    // Case 1: No session yet — create session, link pending files, then navigate
    if (!sessionId) {
      if (pendingFileIds.length === 0) {
        toast.info("Please add a file first to start analyzing your data", {
          duration: 4000,
        });
        return;
      }

      if (creatingSession.current) return;
      creatingSession.current = true;

      try {
        const newSession = await createSession.mutateAsync("New Chat");

        // Link all pending files
        for (const fileId of pendingFileIds) {
          await linkFileAsync({ sessionId: newSession.id, fileId });
        }

        // Store message for auto-send after navigation (component unmounts on navigate)
        sessionStorage.setItem("spectra_pending_message", message);
        sessionStorage.setItem("spectra_pending_search", searchToggle.enabled ? "1" : "0");

        // Navigate to the real session page
        router.replace(`/sessions/${newSession.id}`);
      } catch (err) {
        console.error("[WelcomeScreen] Session creation failed:", err);
        toast.error("Failed to create session. Please try again.");
        creatingSession.current = false;
      }
      return;
    }

    // Case 2: Session exists but no linked files
    if (!hasLinkedFiles) {
      toast.info("Please add a file first to start analyzing your data", {
        duration: 4000,
      });
      return;
    }

    // Case 3: Session exists and has linked files — delegate stream to ChatInterface
    sessionStorage.setItem("spectra_pending_stream", JSON.stringify({
      message,
      searchEnabled: searchToggle.enabled,
    }));
    addLocalMessage(sessionId!, message);
  };

  return (
    <div {...getWelcomeDropProps()} className="flex flex-col h-full relative">
      <input {...getWelcomeDropInput()} />

      {/* Drag-and-drop overlay */}
      {isWelcomeDragActive && (
        <div className="absolute inset-0 z-50 bg-primary/5 border-2 border-dashed border-primary rounded-lg flex items-center justify-center backdrop-blur-sm">
          <div className="text-center">
            <Upload className="h-12 w-12 mx-auto mb-2 text-primary" />
            <p className="text-base font-medium text-primary">Drop file to upload and link</p>
            <p className="text-sm text-muted-foreground mt-1">CSV, Excel files up to 50MB</p>
          </div>
        </div>
      )}

      {/* Sidebar toggle */}
      <div className="px-4 py-3">
        <SidebarTrigger className="-ml-1" />
      </div>

      {/* Main content area — centered greeting */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-2xl w-full space-y-8 text-center">
          {/* Subtle decorative element */}
          <div className="flex justify-center">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-blue-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-indigo-500/70" />
            </div>
          </div>

          {/* Greeting */}
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              Hi {firstName}! What would you like to analyze today?
            </h1>
            {!hasLinkedFiles && (
              <p className="text-muted-foreground text-base">
                Add a file to start exploring your data
              </p>
            )}
          </div>

          {/* Pending file chips (pre-session) */}
          {!sessionId && pendingFileNames.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2">
              {pendingFileIds.map((fileId, i) => (
                <span
                  key={fileId}
                  className="inline-flex items-center gap-1.5 rounded-full bg-accent px-3 py-1.5 text-sm"
                >
                  <FileSpreadsheet className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="truncate max-w-[200px]">
                    {pendingFileNames[i]}
                  </span>
                  <button
                    type="button"
                    onClick={() => handlePendingRemove(fileId)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-muted-foreground/20"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Query suggestions when files are linked */}
          {hasLinkedFiles && sessionId && sessionDetail && (
            <QuerySuggestions
              categories={[]}
              onSelect={(suggestion) => handleSend(suggestion)}
              autoSend={true}
            />
          )}
        </div>
      </div>

      {/* Chat input — fixed at bottom */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            disabled={false}
            searchEnabled={searchToggle.enabled}
            onSearchToggle={searchToggle.toggle}
            searchConfigured={searchToggle.isConfigured}
            searchQuotaExceeded={searchToggle.isQuotaExceeded}
            linkedFileIds={
              sessionId
                ? linkedFiles.map((f) => f.id)
                : pendingFileIds
            }
            leftSlot={
              sessionId ? (
                <FileLinkingDropdown
                  sessionId={sessionId}
                  linkedFileIds={linkedFiles.map((f) => f.id)}
                />
              ) : (
                <PendingFilePicker
                  pendingFileIds={pendingFileIds}
                  recentFiles={recentFiles ?? []}
                  onOpenUpload={handleOpenUploadDialog}
                  onOpenSelection={() => setSelectionModalOpen(true)}
                  onRecentFileClick={handlePendingFileSelect}
                />
              )
            }
          />
        </div>
      </div>

      {/* Dialogs for pre-session file picking */}
      {!sessionId && (
        <>
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>Upload File</DialogTitle>
              </DialogHeader>
              <FileUploadZone onUploadComplete={handleUploadComplete} />
            </DialogContent>
          </Dialog>

          <FileSelectionModal
            open={selectionModalOpen}
            onOpenChange={setSelectionModalOpen}
            onFileSelected={handlePendingFileSelect}
            linkedFileIds={pendingFileIds}
          />
        </>
      )}

      {/* Drag-drop upload dialog (works with and without session) */}
      <Dialog open={dragUploadDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setDragUploadDialogOpen(false);
          setDroppedFiles([]);
        }
      }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
          </DialogHeader>
          <FileUploadZone
            onUploadComplete={handleDragUploadComplete}
            initialFiles={droppedFiles.length > 0 ? droppedFiles : undefined}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * Paperclip dropdown for pre-session file picking.
 * Same UI as FileLinkingDropdown but stores selections in local state
 * instead of making API calls. Session is created later on first message send.
 */
function PendingFilePicker({
  pendingFileIds,
  recentFiles,
  onOpenUpload,
  onOpenSelection,
  onRecentFileClick,
}: {
  pendingFileIds: string[];
  recentFiles: { id: string; original_filename: string }[];
  onOpenUpload: () => void;
  onOpenSelection: () => void;
  onRecentFileClick: (fileId: string) => void;
}) {
  const pendingSet = new Set(pendingFileIds);
  const hasRecentFiles = recentFiles.length > 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          aria-label="Add file to chat"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="top" className="w-56">
        <DropdownMenuItem onClick={onOpenUpload}>
          <Upload className="mr-2 h-4 w-4" />
          Upload File
        </DropdownMenuItem>

        <DropdownMenuItem onClick={onOpenSelection}>
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          Link Existing File
        </DropdownMenuItem>

        {hasRecentFiles && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Recent</DropdownMenuLabel>
            {recentFiles.map((file) => {
              const isPending = pendingSet.has(file.id);
              const displayName =
                file.original_filename.length > 30
                  ? file.original_filename.slice(0, 27) + "..."
                  : file.original_filename;

              return (
                <DropdownMenuItem
                  key={file.id}
                  disabled={isPending}
                  onClick={() => !isPending && onRecentFileClick(file.id)}
                >
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  <span className="truncate">
                    {displayName}
                    {isPending && (
                      <span className="text-muted-foreground ml-1">
                        (selected)
                      </span>
                    )}
                  </span>
                </DropdownMenuItem>
              );
            })}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
