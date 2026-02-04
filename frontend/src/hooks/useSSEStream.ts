import { useState, useCallback, useRef, useEffect } from "react";
import { StreamEvent, StreamEventType } from "@/types/chat";
import { getAccessToken } from "@/lib/api-client";

export interface StreamState {
  events: StreamEvent[];
  isStreaming: boolean;
  error: string | null;
  currentStatus: string | null;
  streamedText: string;
  completedData: Record<string, any> | null;
}

/**
 * SSE streaming hook for chat queries.
 * Manages POST-based SSE streaming with fetch + ReadableStream.
 */
export function useSSEStream() {
  const [state, setState] = useState<StreamState>({
    events: [],
    isStreaming: false,
    error: null,
    currentStatus: null,
    streamedText: "",
    completedData: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // Map status event types to user-friendly messages
  const getStatusMessage = useCallback((type: StreamEventType): string => {
    switch (type) {
      case "coding_started":
        return "Generating code...";
      case "validation_started":
        return "Validating code...";
      case "execution_started":
        return "Running analysis...";
      case "analysis_started":
        return "Interpreting results...";
      default:
        return "Processing...";
    }
  }, []);

  const startStream = useCallback(
    async (fileId: string, message: string) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new AbortController for this stream
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // Reset state
      setState({
        events: [],
        isStreaming: true,
        error: null,
        currentStatus: null,
        streamedText: "",
        completedData: null,
      });

      try {
        const accessToken = getAccessToken();
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }

        const response = await fetch(`/api/chat/${fileId}/stream`, {
          method: "POST",
          headers,
          body: JSON.stringify({ content: message }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No reader available");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;

            // Parse SSE format: "data: {json}"
            if (line.startsWith("data: ")) {
              try {
                const jsonData = line.slice(6); // Remove "data: " prefix
                const event: StreamEvent = JSON.parse(jsonData);

                // Update state based on event type
                setState((prev) => {
                  const newState = { ...prev };
                  newState.events = [...prev.events, event];

                  switch (event.type) {
                    case "coding_started":
                    case "validation_started":
                    case "execution_started":
                    case "analysis_started":
                      newState.currentStatus = getStatusMessage(event.type);
                      break;

                    case "progress":
                      newState.currentStatus = event.message || null;
                      break;

                    case "retry":
                      newState.currentStatus = `Retrying... (attempt ${event.attempt}/${event.max_attempts})`;
                      break;

                    case "content_chunk":
                      if (event.text) {
                        newState.streamedText = prev.streamedText + event.text;
                      }
                      break;

                    case "node_complete":
                      // Node completion stored in events array
                      break;

                    case "completed":
                      newState.completedData = event.data || null;
                      newState.isStreaming = false;
                      newState.currentStatus = null;
                      break;

                    case "error":
                      newState.error = event.message || "An error occurred";
                      newState.isStreaming = false;
                      newState.currentStatus = null;
                      break;
                  }

                  return newState;
                });
              } catch (parseError) {
                console.error("Failed to parse SSE event:", parseError);
              }
            }
          }
        }

        // Stream ended
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          currentStatus: null,
        }));
      } catch (error: any) {
        if (error.name === "AbortError") {
          // Stream was cancelled, just stop
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            currentStatus: null,
          }));
        } else {
          // Real error
          setState((prev) => ({
            ...prev,
            error: error.message || "Failed to connect to stream",
            isStreaming: false,
            currentStatus: null,
          }));
        }
      }
    },
    [getStatusMessage]
  );

  const resetStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState({
      events: [],
      isStreaming: false,
      error: null,
      currentStatus: null,
      streamedText: "",
      completedData: null,
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    ...state,
    startStream,
    resetStream,
  };
}
