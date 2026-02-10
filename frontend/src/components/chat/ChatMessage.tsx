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
  onFollowUpClick?: (suggestion: string) => void;
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
  onFollowUpClick,
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

  // Parse execution result for table data - handles multiple pandas output formats
  const parseExecutionResult = (result: any): { columns: string[]; rows: Record<string, any>[] } | null => {
    if (!result) return null;

    // If result is a string, try to parse as JSON
    let parsed = result;
    if (typeof result === "string") {
      try {
        parsed = JSON.parse(result);
      } catch {
        // Not valid JSON, return null
        return null;
      }
    }

    // Format 1: Array of objects (df.to_dict('records') - preferred format)
    // Example: [{"col1": "a", "col2": 1}, {"col1": "b", "col2": 2}]
    if (Array.isArray(parsed)) {
      // Handle empty array - show empty table
      if (parsed.length === 0) {
        return { columns: [], rows: [] };
      }
      // Array of objects
      if (typeof parsed[0] === "object" && parsed[0] !== null) {
        return {
          columns: Object.keys(parsed[0]),
          rows: parsed,
        };
      }
      // Array of scalars - not tabular data
      return null;
    }

    // Format 2: Object with columns and rows/data keys (df.to_dict('split') or custom)
    // Example: {columns: ["col1", "col2"], data: [["a", 1], ["b", 2]]}
    // Example: {columns: ["col1", "col2"], rows: [{col1: "a"}, {col2: "b"}]}
    if (parsed && typeof parsed === "object") {
      if (Array.isArray(parsed.columns)) {
        // If rows is array of objects, use directly
        if (Array.isArray(parsed.rows)) {
          return {
            columns: parsed.columns,
            rows: parsed.rows,
          };
        }
        // If data is array of arrays (split format), convert to array of objects
        if (Array.isArray(parsed.data)) {
          const rows = parsed.data.map((row: any[]) => {
            const obj: Record<string, any> = {};
            parsed.columns.forEach((col: string, i: number) => {
              obj[col] = row[i];
            });
            return obj;
          });
          return { columns: parsed.columns, rows };
        }
      }

      // Format 3: df.to_dict() default format: {column: {index: value}}
      // Example: {"col1": {"0": "a", "1": "b"}, "col2": {"0": 1, "1": 2}}
      // Detect by checking if all values are objects with numeric string keys
      const keys = Object.keys(parsed);
      if (keys.length > 0) {
        const firstValue = parsed[keys[0]];
        if (firstValue && typeof firstValue === "object" && !Array.isArray(firstValue)) {
          // Check if keys of nested object look like indices (numeric strings)
          const indexKeys = Object.keys(firstValue);
          const looksLikeDefaultFormat = indexKeys.length > 0 &&
            indexKeys.every(k => /^\d+$/.test(k));

          if (looksLikeDefaultFormat) {
            // Convert {col: {idx: val}} to [{col: val}, ...]
            const rows: Record<string, any>[] = [];
            indexKeys.forEach(idx => {
              const row: Record<string, any> = {};
              keys.forEach(col => {
                row[col] = parsed[col][idx];
              });
              rows.push(row);
            });
            return { columns: keys, rows };
          }
        }
      }
    }

    // Not a recognized tabular format
    return null;
  };

  // If this is a structured data message, render DataCard
  if (hasStructuredData) {
    const tableData = parseExecutionResult(message.metadata_json?.execution_result);
    const followUpSuggestions = message.metadata_json?.follow_up_suggestions as string[] | undefined;
    const searchSources = message.metadata_json?.search_sources as { title: string; url: string }[] | undefined;

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
          followUpSuggestions={followUpSuggestions}
          onFollowUpClick={onFollowUpClick}
          searchSources={searchSources}
        />
      </div>
    );
  }

  // Check for follow-up suggestions without structured data (e.g., MEMORY_SUFFICIENT responses)
  const hasFollowUpSuggestions =
    !isUser &&
    !isError &&
    message.metadata_json?.follow_up_suggestions &&
    Array.isArray(message.metadata_json.follow_up_suggestions) &&
    message.metadata_json.follow_up_suggestions.length > 0;

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
      style={{ animation: "var(--animate-fadeIn)" }}
      className={`flex gap-3 p-4 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={
            isUser
              ? "gradient-primary text-white"
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
          className={`rounded-2xl px-4 py-2.5 transition-all duration-200 ${
            isUser
              ? "gradient-primary text-white shadow-sm"
              : isError
              ? "bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-900 dark:text-red-300"
              : "bg-muted text-foreground border-l-2 border-l-primary/30"
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
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
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

        {/* Follow-up suggestions for non-DataCard messages */}
        {hasFollowUpSuggestions && onFollowUpClick && (
          <div className="mt-2 space-y-2">
            <h4 className="text-xs font-medium text-muted-foreground">Continue exploring</h4>
            <div className="flex flex-wrap gap-2">
              {(message.metadata_json!.follow_up_suggestions as string[]).map((suggestion: string) => (
                <button
                  key={suggestion}
                  onClick={() => onFollowUpClick(suggestion)}
                  className="px-3 py-1.5 rounded-full border text-xs hover:bg-accent hover:border-primary/30 transition-all duration-200 bg-background cursor-pointer"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
