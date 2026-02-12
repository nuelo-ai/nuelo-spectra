"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { useCreateSession, useLinkFile } from "@/hooks/useSessionMutations";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useSearchToggle } from "@/hooks/useSearchToggle";
import { useFiles, useRecentFiles } from "@/hooks/useFileManager";
import { ChatInput } from "@/components/chat/ChatInput";
import { QuerySuggestions } from "@/components/chat/QuerySuggestions";
import { FileLinkingDropdown } from "@/components/file/FileLinkingDropdown";
import { FileSelectionModal } from "@/components/file/FileSelectionModal";
import { FileUploadZone } from "@/components/file/FileUploadZone";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
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
  const { startStream } = useSSEStream();
  const searchToggle = useSearchToggle();
  const creatingSession = useRef(false);

  // Pending file tracking for pre-session state
  const [pendingFileIds, setPendingFileIds] = useState<string[]>([]);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectionModalOpen, setSelectionModalOpen] = useState(false);
  const prevFileIdsRef = useRef<Set<string>>(new Set());

  const { data: allFiles } = useFiles();
  const { data: recentFiles } = useRecentFiles(5);
  const pendingMessageSent = useRef(false);

  // Auto-send pending message after lazy session creation + navigation
  useEffect(() => {
    if (!sessionId || pendingMessageSent.current) return;
    const linkedFileCount = sessionDetail?.files?.length ?? 0;
    if (linkedFileCount === 0) return;

    const pendingMessage = sessionStorage.getItem("spectra_pending_message");
    if (!pendingMessage) return;

    console.log("[WelcomeScreen] Auto-sending pending message:", {
      sessionId,
      linkedFileCount,
      message: pendingMessage.slice(0, 50),
    });

    pendingMessageSent.current = true;
    const searchEnabled = sessionStorage.getItem("spectra_pending_search") === "1";
    sessionStorage.removeItem("spectra_pending_message");
    sessionStorage.removeItem("spectra_pending_search");

    startStream(sessionId, pendingMessage, searchEnabled);
  }, [sessionId, sessionDetail?.files?.length, startStream]);

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

  const handleSend = async (message: string) => {
    console.log("[WelcomeScreen] handleSend called", {
      message: message.slice(0, 50),
      sessionId,
      pendingFileIds,
      hasLinkedFiles,
      linkedFilesCount: linkedFiles.length,
      creatingSession: creatingSession.current,
    });

    // Case 1: No session yet — create session, link pending files, then send
    if (!sessionId) {
      if (pendingFileIds.length === 0) {
        console.log("[WelcomeScreen] BLOCKED: no pending files");
        toast.info("Please add a file first to start analyzing your data", {
          duration: 4000,
        });
        return;
      }

      if (creatingSession.current) {
        console.log("[WelcomeScreen] BLOCKED: already creating session");
        return;
      }
      creatingSession.current = true;

      try {
        console.log("[WelcomeScreen] Creating session...");
        const newSession = await createSession.mutateAsync("New Chat");
        console.log("[WelcomeScreen] Session created:", newSession.id);

        // Link all pending files
        for (const fileId of pendingFileIds) {
          console.log("[WelcomeScreen] Linking file:", fileId);
          await linkFileAsync({ sessionId: newSession.id, fileId });
        }
        console.log("[WelcomeScreen] All files linked, navigating...");

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
      console.log("[WelcomeScreen] BLOCKED: session exists but no linked files");
      toast.info("Please add a file first to start analyzing your data", {
        duration: 4000,
      });
      return;
    }

    // Case 3: Session exists and has linked files — start streaming
    console.log("[WelcomeScreen] Starting stream for session:", sessionId);
    await startStream(sessionId, message, searchToggle.enabled);
  };

  return (
    <div className="flex flex-col h-full">
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
