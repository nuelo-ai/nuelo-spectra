"use client";

import { ChatMessageResponse } from "@/types/chat";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { AlertCircle } from "lucide-react";

interface ChatMessageProps {
  message: ChatMessageResponse;
  isStreaming?: boolean;
  streamedText?: string;
}

/**
 * Individual chat message component.
 * Supports user messages (right-aligned) and assistant messages (left-aligned).
 * Handles streaming text and error states.
 */
export function ChatMessage({
  message,
  isStreaming = false,
  streamedText = "",
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.message_type === "error";

  // For streaming assistant messages, use streamedText
  const displayContent = isStreaming ? streamedText : message.content;

  // Calculate relative time
  const getRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div
      className={`flex gap-3 p-4 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={
            isUser
              ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
              : "bg-muted text-muted-foreground"
          }
        >
          {isUser ? "U" : "S"}
        </AvatarFallback>
      </Avatar>

      {/* Message content */}
      <div
        className={`flex flex-col gap-1 max-w-[70%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
              : isError
              ? "bg-red-50 border border-red-200 text-red-900"
              : "bg-muted text-foreground"
          }`}
        >
          {/* Error icon */}
          {isError && (
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Error</span>
            </div>
          )}

          {/* Message text */}
          <p className="text-sm whitespace-pre-wrap break-words">
            {displayContent}
          </p>

          {/* Streaming cursor */}
          {isStreaming && (
            <span className="inline-block w-1 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground px-1">
          {getRelativeTime(message.created_at)}
        </span>
      </div>
    </div>
  );
}
