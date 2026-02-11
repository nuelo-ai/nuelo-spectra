"use client";

import { useState, useEffect, KeyboardEvent } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { Send, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  /** External value to populate the input (e.g., from suggestion chips) */
  initialValue?: string;
  /** Whether web search is currently toggled on */
  searchEnabled?: boolean;
  /** Callback to toggle search on/off */
  onSearchToggle?: () => void;
  /** Whether search is configured (API key set) */
  searchConfigured?: boolean;
  /** Whether daily search quota is exceeded */
  searchQuotaExceeded?: boolean;
  /** Optional content rendered in the toolbar row (e.g., paperclip button) */
  leftSlot?: React.ReactNode;
}

/**
 * Auto-expanding textarea with Enter-to-send and Shift+Enter for newlines.
 * Send button always visible as alternative to Enter key.
 */
export function ChatInput({
  onSend,
  disabled = false,
  initialValue,
  searchEnabled = false,
  onSearchToggle,
  searchConfigured = false,
  searchQuotaExceeded = false,
  leftSlot,
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  // When initialValue changes externally, populate the input
  useEffect(() => {
    if (initialValue) {
      setMessage(initialValue);
    }
  }, [initialValue]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const trimmed = message.trim();
      if (trimmed && !disabled) {
        onSend(trimmed);
        setMessage("");
      }
    }
    // Shift+Enter allows default behavior (new line)
  };

  const handleSend = () => {
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setMessage("");
    }
  };

  const isEmpty = !message.trim();

  const searchToggleDisabled = !searchConfigured || searchQuotaExceeded || disabled;

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-3">
        <TextareaAutosize
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask about your data..."
          minRows={3}
          maxRows={10}
          className="flex-1 resize-none rounded-xl border border-input bg-background px-4 py-3 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
        />
        <Button
          onClick={handleSend}
          disabled={disabled || isEmpty}
          size="icon"
          className="shrink-0 h-12 w-12 rounded-xl"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
      {/* Toolbar row */}
      <div className="flex items-center gap-2">
        {leftSlot}
        {leftSlot && <div className="h-4 w-px bg-border" />}
        <button
          type="button"
          role="switch"
          aria-checked={searchEnabled}
          onClick={onSearchToggle}
          disabled={searchToggleDisabled}
          className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
            searchEnabled ? "bg-primary" : "bg-muted"
          }`}
        >
          <span
            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow-lg ring-0 transition-transform duration-200 ease-in-out ${
              searchEnabled ? "translate-x-4" : "translate-x-0"
            }`}
          />
        </button>
        <label className="text-xs text-muted-foreground flex items-center gap-1">
          <Globe className="h-3 w-3" />
          Search web
        </label>
        {!searchConfigured && (
          <span className="text-xs text-muted-foreground/60 italic" title="Search not configured">
            (not configured)
          </span>
        )}
        {searchQuotaExceeded && (
          <span className="text-xs text-destructive italic">
            Search quota reached
          </span>
        )}
      </div>
    </div>
  );
}
