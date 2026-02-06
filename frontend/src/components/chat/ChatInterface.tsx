"use client";

import { useEffect, useRef, useState } from "react";
import {
  useChatMessages,
  useAddLocalMessage,
  useInvalidateChatMessages,
} from "@/hooks/useChatMessages";
import { useSSEStream } from "@/hooks/useSSEStream";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { DataCard } from "./DataCard";
import { Separator } from "@/components/ui/separator";

interface ChatInterfaceProps {
  fileId: string;
  fileName: string;
}

/**
 * Complete chat interface for a file tab.
 * Manages message history, streaming, and user input.
 */
export function ChatInterface({ fileId, fileName }: ChatInterfaceProps) {
  const { data: chatData, isLoading, refetch } = useChatMessages(fileId);
  const addLocalMessage = useAddLocalMessage();

  const {
    isStreaming,
    streamedText,
    currentStatus,
    error: streamError,
    completedData,
    events,
    startStream,
    resetStream,
  } = useSSEStream();

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevStreamingRef = useRef(isStreaming);

  // Track which cards are collapsed (by message ID)
  const [collapsedCards, setCollapsedCards] = useState<Set<string>>(new Set());

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
      console.log('[ChatInterface] Stream completed, refetching messages...');

      // Immediately refetch messages from server and wait for completion
      (async () => {
        const result = await refetch();
        console.log('[ChatInterface] Messages refetched successfully:', result);

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
    addLocalMessage(fileId, message);

    // Start streaming AI response
    await startStream(fileId, message);
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

  // Parse streaming events to extract progressive data for DataCard
  const getStreamingDataCard = () => {
    if (!isStreaming) return null;

    console.log('[ChatInterface] getStreamingDataCard called, events:', events.length, 'isStreaming:', isStreaming);

    // Extract query brief from first user message in stream
    const queryBrief = "Analyzing your request...";

    // Check if we have execution result in node_complete events
    let tableData: { columns: string[]; rows: Record<string, any>[] } | undefined = undefined;
    const executionEvent = events.find((e) => e.type === "node_complete" && e.node === "execute");
    console.log('[ChatInterface] executionEvent:', executionEvent ? 'found' : 'not found');
    if (executionEvent?.data?.execution_result) {
      // Parse execution result for table
      const result = executionEvent.data.execution_result;
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
    if (codingEvent?.data?.generated_code) {
      generatedCode = codingEvent.data.generated_code;
    }
    console.log('[ChatInterface] generatedCode:', generatedCode ? 'found' : 'not found');

    // Extract analysis/explanation from data_analysis node
    let explanation = streamedText || undefined;
    const analysisEvent = events.find((e) => e.type === "node_complete" && e.node === "data_analysis");
    if (analysisEvent?.data?.analysis) {
      explanation = analysisEvent.data.analysis;
    }
    console.log('[ChatInterface] explanation:', explanation ? 'found' : 'not found');

    return { queryBrief, tableData, explanation, generatedCode };
  };

  const messages = chatData?.messages || [];
  const hasMessages = messages.length > 0;
  const showEmptyState = !hasMessages && !isStreaming;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-lg font-semibold truncate">{fileName}</h2>
        </div>
      </div>

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
                    <span className="text-2xl text-white">💬</span>
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
                />
              ))}
            </div>
          )}

          {/* Streaming message */}
          {isStreaming && (
            <div className="max-w-3xl mx-auto px-4 mt-6">
              <div className="animate-in fade-in duration-200">
                {(() => {
                  const hasNodeComplete = events.some((e) => e.type === "node_complete");
                  const hasStructuredNode = events.some(
                    (e) =>
                      e.type === "node_complete" &&
                      (e.node === "execute" || e.node === "coding" || e.node === "data_analysis")
                  );
                  console.log('[ChatInterface] Render check:', {
                    streamedText: !!streamedText,
                    hasNodeComplete,
                    hasStructuredNode,
                    eventsCount: events.length
                  });
                  return null;
                })()}
                {streamedText || events.some((e) => e.type === "node_complete") ? (
                  // If we have streaming data, check if it's structured data
                  events.some(
                    (e) =>
                      e.type === "node_complete" &&
                      (e.node === "execute" || e.node === "coding" || e.node === "data_analysis")
                  ) ? (
                    // Render as DataCard for structured response
                    <DataCard
                      {...getStreamingDataCard()!}
                      isStreaming={true}
                    />
                  ) : streamedText ? (
                    // Only render as regular message if we have text
                    <ChatMessage
                      message={{
                        id: "streaming",
                        file_id: fileId,
                        role: "assistant",
                        content: streamedText,
                        message_type: null,
                        metadata_json: null,
                        created_at: new Date().toISOString(),
                      }}
                      isStreaming={true}
                      streamedText={streamedText}
                    />
                  ) : (
                    // Show typing indicator if no text yet
                    <TypingIndicator />
                  )
                ) : (
                  <TypingIndicator />
                )}
              </div>
            </div>
          )}

          {/* Stream error */}
          {streamError && (
            <div className="max-w-3xl mx-auto px-4 mt-6">
              <ChatMessage
                message={{
                  id: "error",
                  file_id: fileId,
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
              <div className="flex gap-1">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "0ms" }} />
                <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "200ms" }} />
                <div className="h-1.5 w-1.5 rounded-full bg-primary" style={{ animation: "var(--animate-pulse-gentle)", animationDelay: "400ms" }} />
              </div>
              <p className="text-xs text-muted-foreground">{currentStatus}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat input - fixed at bottom */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput onSend={handleSend} disabled={isStreaming || isLoading} />
        </div>
      </div>
    </div>
  );
}
