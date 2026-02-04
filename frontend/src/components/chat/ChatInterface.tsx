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
import { ScrollArea } from "@/components/ui/scroll-area";
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
  const { data: chatData, isLoading } = useChatMessages(fileId);
  const addLocalMessage = useAddLocalMessage();
  const invalidateMessages = useInvalidateChatMessages();

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

  const scrollRef = useRef<HTMLDivElement>(null);

  // Track which cards are collapsed (by message ID)
  const [collapsedCards, setCollapsedCards] = useState<Set<string>>(new Set());

  // Auto-scroll to bottom when messages change or streaming updates
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatData?.messages, streamedText, isStreaming]);

  // Handle stream completion
  useEffect(() => {
    if (completedData) {
      // Invalidate and refetch messages from server
      invalidateMessages(fileId);
      // Reset stream state
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
    }
  }, [completedData, fileId, invalidateMessages, resetStream, chatData?.messages]);

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

    // Extract query brief from first user message in stream
    const queryBrief = "Analyzing your request...";

    // Check if we have execution result in node_complete events
    let tableData: { columns: string[]; rows: Record<string, any>[] } | undefined = undefined;
    const executionEvent = events.find((e) => e.type === "node_complete" && e.node === "execute");
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

    // Explanation is the streamed text
    const explanation = streamedText || undefined;

    return { queryBrief, tableData, explanation };
  };

  const messages = chatData?.messages || [];
  const hasMessages = messages.length > 0;
  const showEmptyState = !hasMessages && !isStreaming;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <h2 className="text-lg font-semibold truncate">{fileName}</h2>
      </div>

      {/* Messages area */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="min-h-full">
          {/* Empty state */}
          {showEmptyState && (
            <div className="flex items-center justify-center h-full p-8 text-center">
              <div className="max-w-md">
                <p className="text-muted-foreground">
                  Ask a question about your data to get started
                </p>
              </div>
            </div>
          )}

          {/* Message list */}
          {hasMessages && (
            <div className="divide-y">
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
            <>
              {hasMessages && <Separator />}
              <div className="animate-in fade-in duration-200">
                {streamedText || events.some((e) => e.type === "node_complete") ? (
                  // If we have streaming data, check if it's structured data
                  events.some(
                    (e) =>
                      e.type === "node_complete" &&
                      (e.node === "execute" || e.node === "coding")
                  ) ? (
                    // Render as DataCard for structured response
                    <div className="p-4">
                      <DataCard
                        {...getStreamingDataCard()!}
                        isStreaming={true}
                      />
                    </div>
                  ) : (
                    // Render as regular message
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
                  )
                ) : (
                  <TypingIndicator />
                )}
              </div>
            </>
          )}

          {/* Stream error */}
          {streamError && (
            <>
              {(hasMessages || isStreaming) && <Separator />}
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
            </>
          )}
        </div>
      </ScrollArea>

      {/* Status indicator */}
      {currentStatus && (
        <div className="px-4 py-2 border-t bg-muted/50">
          <p className="text-xs text-muted-foreground">{currentStatus}</p>
        </div>
      )}

      {/* Chat input */}
      <ChatInput onSend={handleSend} disabled={isStreaming || isLoading} />
    </div>
  );
}
