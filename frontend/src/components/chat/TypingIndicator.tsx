"use client";

/**
 * Three-dot animated typing indicator.
 * Shows while waiting for first AI response.
 */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 p-3">
      <div
        className="h-2 w-2 rounded-full bg-muted-foreground animate-pulse"
        style={{ animationDelay: "0s" }}
      />
      <div
        className="h-2 w-2 rounded-full bg-muted-foreground animate-pulse"
        style={{ animationDelay: "0.2s" }}
      />
      <div
        className="h-2 w-2 rounded-full bg-muted-foreground animate-pulse"
        style={{ animationDelay: "0.4s" }}
      />
    </div>
  );
}
