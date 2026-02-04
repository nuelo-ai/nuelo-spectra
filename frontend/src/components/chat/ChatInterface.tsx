"use client";

import { useEffect, useRef } from "react";
import {
  useChatMessages,
  useAddLocalMessage,
  useInvalidateChatMessages,
} from "@/hooks/useChatMessages";
import { useSSEStream } from "@/hooks/useSSEStream";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
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
    startStream,
    resetStream,
  } = useSSEStream();

  const scrollRef = useRef<HTMLDivElement>(null);

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
    }
  }, [completedData, fileId, invalidateMessages, resetStream]);

  const handleSend = async (message: string) => {
    // Optimistically add user message
    addLocalMessage(fileId, message);

    // Start streaming AI response
    await startStream(fileId, message);
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
                <ChatMessage key={message.id} message={message} />
              ))}
            </div>
          )}

          {/* Streaming message */}
          {isStreaming && (
            <>
              {hasMessages && <Separator />}
              <div className="animate-in fade-in duration-200">
                {streamedText ? (
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
