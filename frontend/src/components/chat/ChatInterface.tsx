"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  useChatMessages,
  useAddLocalMessage,
} from "@/hooks/useChatMessages";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useSearchToggle } from "@/hooks/useSearchToggle";
import { useFiles } from "@/hooks/useFileManager";
import { useLinkFile } from "@/hooks/useSessionMutations";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { DataCard } from "./DataCard";
import { Globe, PanelRightOpen, PanelRightClose, Upload } from "lucide-react";
import { useSessionStore } from "@/stores/sessionStore";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { FileLinkingDropdown } from "@/components/file/FileLinkingDropdown";
import { FileUploadZone } from "@/components/file/FileUploadZone";
import type { FileListItem } from "@/types/file";

interface ChatInterfaceProps {
  sessionId: string;
  sessionTitle: string;
}

/**
 * Complete chat interface for a session.
 * Manages message history, streaming, and user input.
 */
export function ChatInterface({ sessionId, sessionTitle }: ChatInterfaceProps) {
  const { data: chatData, isLoading, refetch } = useChatMessages(sessionId);
  const addLocalMessage = useAddLocalMessage();
  const { data: sessionDetail } = useSessionDetail(sessionId);
  const rightPanelOpen = useSessionStore((s) => s.rightPanelOpen);
  const toggleRightPanel = useSessionStore((s) => s.toggleRightPanel);
  const setRightPanelOpen = useSessionStore((s) => s.setRightPanelOpen);

  const {
    isStreaming,
    streamedText,
    currentStatus,
    error: streamError,
    completedData,
    events,
    currentSearchQuery,
    searchSources: streamSearchSources,
    startStream,
    resetStream,
  } = useSSEStream();

  const searchToggle = useSearchToggle();

  // Drag-and-drop upload state
  const queryClient = useQueryClient();
  const { data: allFiles } = useFiles();
  const { mutate: linkFile } = useLinkFile();
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [droppedFiles, setDroppedFiles] = useState<File[]>([]);
  const prevFileIdsRef = useRef<Set<string>>(new Set());

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      // Snapshot current file IDs before opening upload dialog
      prevFileIdsRef.current = new Set(allFiles?.map((f) => f.id) || []);
      setDroppedFiles(acceptedFiles);
      setShowUploadDialog(true);
    },
    [allFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
  });

  const handleDragUploadComplete = async () => {
    setShowUploadDialog(false);
    setDroppedFiles([]);
    await queryClient.invalidateQueries({ queryKey: ["files"] });
    await queryClient.refetchQueries({ queryKey: ["files"] });
    const updatedFiles = queryClient.getQueryData<FileListItem[]>(["files"]);
    if (updatedFiles) {
      const newFiles = updatedFiles.filter(
        (f) => !prevFileIdsRef.current.has(f.id)
      );
      for (const newFile of newFiles) {
        linkFile(
          { sessionId, fileId: newFile.id },
          {
            onSuccess: () => {
              toast.success(
                `${newFile.original_filename} linked to session`
              );
              setRightPanelOpen(true);
            },
            onError: (error: Error) => toast.error(error.message),
          }
        );
      }
    }
  };

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevStreamingRef = useRef(isStreaming);

  // Pick up pending stream from WelcomeScreen handoff.
  // Uses setTimeout(0) to survive React Strict Mode double-mount cycle:
  // Without delay, Strict Mode cleanup aborts the in-flight stream before
  // the second mount can pick it up (sessionStorage already consumed, ref guard blocks retry).
  useEffect(() => {
    if (isStreaming) return;
    const pending = sessionStorage.getItem("spectra_pending_stream");
    if (!pending) return;

    const { message, searchEnabled } = JSON.parse(pending);

    const timer = setTimeout(() => {
      const stillPending = sessionStorage.getItem("spectra_pending_stream");
      if (stillPending) {
        sessionStorage.removeItem("spectra_pending_stream");
        startStream(sessionId, message, searchEnabled);
      }
    }, 0);

    return () => clearTimeout(timer);
  }, [sessionId, startStream, isStreaming]);

  // Track which cards are collapsed (by message ID)
  const [collapsedCards, setCollapsedCards] = useState<Set<string>>(new Set());

  // Track trim confirmation dialog state
  const [showTrimDialog, setShowTrimDialog] = useState(false);

  // Suggestion input state for non-auto-send mode
  const [suggestionInput, setSuggestionInput] = useState<string | undefined>(undefined);

  // Messages from chat data
  const messages = chatData?.messages || [];

  // Scroll to bottom helper
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior, block: 'end' });
    }
  };

  // Auto-scroll to bottom when messages change or streaming updates
  useEffect(() => {
    scrollToBottom('auto');
  }, [chatData?.messages, streamedText, isStreaming, events]);

  // Initial scroll to bottom on mount
  useEffect(() => {
    if (chatData?.messages && chatData.messages.length > 0) {
      // Use setTimeout to ensure DOM is fully rendered
      setTimeout(() => {
        scrollToBottom('auto');
      }, 100);
    }
  }, []);

  // Handle stream completion - detect transition from streaming to not streaming
  useEffect(() => {
    // Check if streaming just completed (was true, now false)
    const streamJustCompleted = prevStreamingRef.current && !isStreaming && !streamError;

    if (streamJustCompleted) {
      // Immediately refetch messages from server and wait for completion
      (async () => {
        const result = await refetch();

        // Reset stream state only after messages are loaded
        resetStream();

        // Auto-collapse previous cards when new card completes
        if (chatData?.messages) {
          const newCollapsed = new Set<string>();
          chatData.messages.forEach((msg) => {
            // Collapse all previous assistant messages with structured data
            if (
              msg.role === "assistant" &&
              msg.metadata_json &&
              (msg.metadata_json.generated_code || msg.metadata_json.execution_result)
            ) {
              newCollapsed.add(msg.id);
            }
          });
          setCollapsedCards(newCollapsed);
        }
      })();
    }

    // Update ref for next render
    prevStreamingRef.current = isStreaming;
  }, [isStreaming, streamError, refetch, resetStream, chatData?.messages]);

  const handleSend = async (message: string) => {
    // Optimistically add user message
    addLocalMessage(sessionId, message);

    // Start streaming AI response with search flag
    await startStream(sessionId, message, searchToggle.enabled);
  };

  const toggleCardCollapse = (messageId: string) => {
    setCollapsedCards((prev) => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  };

  // TODO: Phase 18 - Migrate trim-context to session-based endpoint
  const handleTrimContext = async () => {
    try {
      // NOTE: trim-context endpoint still uses file-based URL.
      // This will be migrated to session-based in Phase 18.
      console.warn('[ChatInterface] trim-context not yet available for session-based flow');
      setShowTrimDialog(false);
    } catch (e) {
      console.error("Failed to trim context:", e);
    }
  };

  // Parse streaming events to extract progressive data for DataCard
  const getStreamingDataCard = () => {
    if (!isStreaming) return null;

    // Extract query brief from first user message in stream
    const queryBrief = "Analyzing your request...";

    // Check if we have execution result in node_complete events
    let tableData: { columns: string[]; rows: Record<string, any>[] } | undefined = undefined;
    const executionEvent = events.find((e) => e.type === "node_complete" && e.node === "execute");
    if (executionEvent?.execution_result) {
      // Parse execution result for table
      const result = executionEvent.execution_result;
      if (typeof result === "string") {
        try {
          const parsed = JSON.parse(result);
          if (Array.isArray(parsed) && parsed.length > 0) {
            tableData = {
              columns: Object.keys(parsed[0]),
              rows: parsed,
            };
          }
        } catch {
          // Ignore parse errors
        }
      }
    }

    // Extract generated code from coding_agent node
    let generatedCode: string | undefined = undefined;
    const codingEvent = events.find((e) => e.type === "node_complete" && e.node === "coding_agent");
    if (codingEvent?.generated_code) {
      generatedCode = codingEvent.generated_code;
    }

    // Extract analysis/explanation from da_response node
    let explanation = streamedText || undefined;
    const analysisEvent = events.find((e) => e.type === "node_complete" && e.node === "da_response");
    if (analysisEvent?.analysis) {
      explanation = analysisEvent.analysis;
    }

    // Extract follow-up suggestions from da_response node_complete event
    let followUpSuggestions: string[] | undefined = undefined;
    if (analysisEvent?.follow_up_suggestions) {
      followUpSuggestions = analysisEvent.follow_up_suggestions;
    }

    // Extract search sources from da_response node_complete event
    let searchSources: { title: string; url: string }[] | undefined = undefined;
    if (analysisEvent?.search_sources && analysisEvent.search_sources.length > 0) {
      searchSources = analysisEvent.search_sources;
    } else if (streamSearchSources.length > 0) {
      searchSources = streamSearchSources;
    }

    return { queryBrief, tableData, explanation, generatedCode, followUpSuggestions, searchSources };
  };

  // Refresh search config when quota exceeded event received
  useEffect(() => {
    const hasQuotaExceeded = events.some((e) => e.type === "search_quota_exceeded");
    if (hasQuotaExceeded) {
      searchToggle.checkConfig();
    }
  }, [events, searchToggle.checkConfig]);

  const hasMessages = messages.length > 0;
  const showEmptyState = !hasMessages && !isStreaming;

  return (
    <div {...getRootProps()} className="flex flex-col h-full relative">
      <input {...getInputProps()} />

      {/* Drag-and-drop overlay */}
      {isDragActive && (
        <div className="absolute inset-0 z-50 bg-primary/5 border-2 border-dashed border-primary rounded-lg flex items-center justify-center backdrop-blur-sm">
          <div className="text-center">
            <Upload className="h-12 w-12 mx-auto mb-2 text-primary" />
            <p className="text-base font-medium text-primary">
              Drop file to upload and link
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              CSV, Excel files up to 50MB
            </p>
          </div>
        </div>
      )}

      {/* Upload dialog for drag-and-drop */}
      <Dialog open={showUploadDialog} onOpenChange={(open) => {
        setShowUploadDialog(open);
        if (!open) setDroppedFiles([]);
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

      {/* Header */}
      <div className="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SidebarTrigger className="-ml-1" />
            <h2 className="text-lg font-semibold truncate">{sessionTitle}</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* TODO: Phase 18 - Migrate ContextUsage to session-based endpoint */}
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-muted-foreground hover:text-foreground"
              onClick={toggleRightPanel}
              title={rightPanelOpen ? "Close linked files" : "Open linked files"}
            >
              {rightPanelOpen ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
              <span className="text-xs">
                Files{sessionDetail?.files?.length ? ` (${sessionDetail.files.length})` : ""}
              </span>
            </Button>
          </div>
        </div>
      </div>

      {/* Trim confirmation dialog */}
      {showTrimDialog && (
        <div className="mx-4 my-2 p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm">
          <p className="text-orange-800 font-medium">Context limit reached</p>
          <p className="text-orange-700 mt-1">
            Oldest messages will be removed to make room for new queries.
            This cannot be undone.
          </p>
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleTrimContext}
              className="px-3 py-1 bg-orange-600 text-white rounded text-xs hover:bg-orange-700"
            >
              Trim older messages
            </button>
            <button
              onClick={() => setShowTrimDialog(false)}
              className="px-3 py-1 bg-white border rounded text-xs hover:bg-gray-50"
            >
              Keep all messages
            </button>
          </div>
        </div>
      )}

      {/* Messages area - scrollable */}
      <div ref={scrollAreaRef} className="flex-1 overflow-y-auto">
        <div className="w-full py-4">
          {/* Loading state */}
          {isLoading && (
            <div className="max-w-3xl mx-auto px-4">
              <div className="space-y-6">
                {/* Skeleton chat messages */}
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-3">
                    <div className="skeleton h-8 w-8 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <div className="skeleton h-16 w-2/3 rounded-lg" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {showEmptyState && (
            <div className="flex items-center justify-center min-h-[60vh] p-8 text-center">
              <div className="max-w-md opacity-60" style={{ animation: "var(--animate-fadeIn)" }}>
                <div className="mb-4">
                  <div className="h-16 w-16 rounded-full gradient-primary mx-auto mb-3 flex items-center justify-center">
                    <span className="text-2xl text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    </span>
                  </div>
                </div>
                <p className="text-muted-foreground font-medium">
                  Ask a question about your data to get started
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Your AI assistant will analyze your data and provide insights
                </p>
              </div>
            </div>
          )}

          {/* Message list */}
          {hasMessages && (
            <div className="max-w-3xl mx-auto px-4 space-y-6">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isCollapsed={collapsedCards.has(message.id)}
                  onToggleCollapse={() => toggleCardCollapse(message.id)}
                  onFollowUpClick={handleSend}
                />
              ))}
            </div>
          )}

          {/* Streaming message */}
          {isStreaming && (
            <div className="max-w-3xl mx-auto px-4 mt-6">
              <div className="animate-in fade-in duration-200">
                {(() => {
                  // Detect if this is a memory-only route (no code generation)
                  const isMemoryRoute = events.some(
                    (e) => e.type === "routing_decided" && e.route === "MEMORY_SUFFICIENT"
                  ) || events.some(
                    (e) =>
                      e.type === "node_complete" &&
                      e.routing_decision?.route === "MEMORY_SUFFICIENT"
                  );

                  // Memory route: render analysis as plain text message (no DataCard)
                  if (isMemoryRoute) {
                    const analysisEvent = events.find(
                      (e) => e.type === "node_complete" && e.node === "da_response"
                    );
                    const analysisText =
                      analysisEvent?.analysis ||
                      analysisEvent?.final_response ||
                      streamedText;

                    // Extract follow-up suggestions from da_response event
                    const followUpSuggestions: string[] | undefined =
                      analysisEvent?.follow_up_suggestions;

                    if (analysisText) {
                      return (
                        <div>
                          <ChatMessage
                            message={{
                              id: "streaming",
                              file_id: null,
                              role: "assistant",
                              content: analysisText,
                              message_type: null,
                              metadata_json: null,
                              created_at: new Date().toISOString(),
                            }}
                            isStreaming={!analysisEvent}
                            streamedText={analysisText}
                          />
                          {/* Follow-up suggestions for memory route */}
                          {followUpSuggestions && followUpSuggestions.length > 0 && analysisEvent && (
                            <div className="max-w-[70%] ml-11 mt-2 space-y-2">
                              <h4 className="text-xs font-medium text-muted-foreground">Continue exploring</h4>
                              <div className="flex flex-wrap gap-2">
                                {followUpSuggestions.map((suggestion) => (
                                  <button
                                    key={suggestion}
                                    onClick={() => handleSend(suggestion)}
                                    className="px-3 py-1.5 rounded-full border text-xs hover:bg-accent hover:border-primary/30 transition-all duration-200 bg-background cursor-pointer"
                                  >
                                    {suggestion}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    }
                    return <TypingIndicator />;
                  }

                  // Code routes (CODE_MODIFICATION, NEW_ANALYSIS): existing DataCard logic
                  const hasStructuredNode = events.some(
                    (e) =>
                      e.type === "node_complete" &&
                      (e.node === "execute" || e.node === "coding_agent" || e.node === "da_response")
                  );

                  if (streamedText || events.some((e) => e.type === "node_complete")) {
                    if (hasStructuredNode) {
                      const streamingData = getStreamingDataCard()!;
                      return (
                        <DataCard
                          {...streamingData}
                          isStreaming={true}
                          followUpSuggestions={streamingData.followUpSuggestions}
                          onFollowUpClick={handleSend}
                          searchSources={streamingData.searchSources}
                        />
                      );
                    } else if (streamedText) {
                      return (
                        <ChatMessage
                          message={{
                            id: "streaming",
                            file_id: null,
                            role: "assistant",
                            content: streamedText,
                            message_type: null,
                            metadata_json: null,
                            created_at: new Date().toISOString(),
                          }}
                          isStreaming={true}
                          streamedText={streamedText}
                        />
                      );
                    } else {
                      return <TypingIndicator />;
                    }
                  }

                  return <TypingIndicator />;
                })()}
              </div>
            </div>
          )}

          {/* Stream error */}
          {streamError && (
            <div className="max-w-3xl mx-auto px-4 mt-6">
              <ChatMessage
                message={{
                  id: "error",
                  file_id: null,
                  role: "assistant",
                  content: "Something went wrong. Please try again.",
                  message_type: "error",
                  metadata_json: null,
                  created_at: new Date().toISOString(),
                }}
              />
            </div>
          )}

          {/* Bottom marker for auto-scroll */}
          <div ref={bottomRef} className="h-1" />
        </div>
      </div>

      {/* Status indicator - fixed at bottom */}
      {currentStatus && (
        <div className="border-t bg-muted/50 py-2" style={{ animation: "var(--animate-slideUp)" }}>
          <div className="max-w-3xl mx-auto px-4">
            <div className="flex items-center gap-2">
              {currentSearchQuery ? (
                /* Search activity: Globe icon with pulsing animation */
                <Globe className="h-3.5 w-3.5 text-primary" style={{ animation: "var(--animate-pulse-gentle)" }} />
              ) : (
                <div className="flex gap-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "0ms" }} />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "200ms" }} />
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "400ms" }} />
                </div>
              )}
              <p className="text-xs text-muted-foreground">{currentStatus}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat input - fixed at bottom */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            disabled={isStreaming || isLoading}
            initialValue={suggestionInput}
            searchEnabled={searchToggle.enabled}
            onSearchToggle={searchToggle.toggle}
            searchConfigured={searchToggle.isConfigured}
            searchQuotaExceeded={searchToggle.isQuotaExceeded}
            linkedFileIds={sessionDetail?.files?.map((f) => f.id) ?? []}
            leftSlot={
              <FileLinkingDropdown
                sessionId={sessionId}
                linkedFileIds={
                  sessionDetail?.files?.map((f) => f.id) ?? []
                }
              />
            }
          />
        </div>
      </div>
    </div>
  );
}
