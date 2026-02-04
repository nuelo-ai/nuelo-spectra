"use client";

import { ChatMessageResponse } from "@/types/chat";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { AlertCircle } from "lucide-react";
import { DataCard } from "./DataCard";

interface ChatMessageProps {
  message: ChatMessageResponse;
  isStreaming?: boolean;
  streamedText?: string;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

/**
 * Individual chat message component.
 * Supports user messages (right-aligned) and assistant messages (left-aligned).
 * Handles streaming text and error states.
 * Renders DataCard for assistant messages with structured data.
 */
export function ChatMessage({
  message,
  isStreaming = false,
  streamedText = "",
  isCollapsed = false,
  onToggleCollapse,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.message_type === "error";

  // For streaming assistant messages, use streamedText
  const displayContent = isStreaming ? streamedText : message.content;

  // Check if this is a structured data message (has metadata with code/execution/analysis)
  const hasStructuredData =
    !isUser &&
    !isError &&
    message.metadata_json &&
    (message.metadata_json.generated_code ||
      message.metadata_json.execution_result ||
      message.content);

  // Parse execution result for table data
  const parseExecutionResult = (result: any) => {
    if (!result) return null;

    // If result is a string, try to parse as JSON
    if (typeof result === "string") {
      try {
        const parsed = JSON.parse(result);
        // Check if it has tabular structure
        if (Array.isArray(parsed)) {
          // Array of objects -> extract columns and rows
          if (parsed.length > 0 && typeof parsed[0] === "object") {
            return {
              columns: Object.keys(parsed[0]),
              rows: parsed,
            };
          }
        } else if (parsed.columns && Array.isArray(parsed.columns)) {
          // Already has columns/rows structure
          return {
            columns: parsed.columns,
            rows: parsed.rows || parsed.data || [],
          };
        }
      } catch {
        // Not valid JSON, return null
        return null;
      }
    }

    // If result is already an array
    if (Array.isArray(result) && result.length > 0 && typeof result[0] === "object") {
      return {
        columns: Object.keys(result[0]),
        rows: result,
      };
    }

    // If result is already structured
    if (result.columns && Array.isArray(result.columns)) {
      return {
        columns: result.columns,
        rows: result.rows || result.data || [],
      };
    }

    return null;
  };

  // If this is a structured data message, render DataCard
  if (hasStructuredData) {
    const tableData = parseExecutionResult(message.metadata_json?.execution_result);

    return (
      <div className="p-4">
        <DataCard
          queryBrief={message.content.split("\n")[0]} // First line as brief
          tableData={tableData || undefined}
          explanation={message.content}
          generatedCode={message.metadata_json?.generated_code}
          isStreaming={isStreaming}
          isCollapsed={isCollapsed}
          onToggleCollapse={onToggleCollapse}
        />
      </div>
    );
  }

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
