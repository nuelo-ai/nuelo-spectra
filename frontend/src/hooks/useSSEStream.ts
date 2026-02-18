import { useState, useCallback, useRef, useEffect } from "react";
import { StreamEvent, StreamEventType, SearchSource } from "@/types/chat";
import { getAccessToken } from "@/lib/api-client";

export interface StreamState {
  events: StreamEvent[];
  isStreaming: boolean;
  error: string | null;
  currentStatus: string | null;
  streamedText: string;
  completedData: Record<string, any> | null;
  /** Current search query being executed (null when not searching) */
  currentSearchQuery: string | null;
  /** Search sources extracted from stream events */
  searchSources: SearchSource[];
  /** Chart specs JSON string from chart_completed event */
  chartSpecs: string | null;
  /** Chart error message from chart_failed event */
  chartError: string | null;
  /** Whether visualization has been requested (chart generation in progress) */
  visualizationInProgress: boolean;
  /** Current visualization stage message */
  visualizationStage: string | null;
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
    currentSearchQuery: null,
    searchSources: [],
    chartSpecs: null,
    chartError: null,
    visualizationInProgress: false,
    visualizationStage: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // Map status event types to user-friendly messages
  const getStatusMessage = useCallback((type: StreamEventType): string => {
    switch (type) {
      case "routing_started":
        return "Analyzing your query...";
      case "routing_decided":
        return "Processing...";
      case "coding_started":
        return "Generating code...";
      case "validation_started":
        return "Validating code...";
      case "execution_started":
        return "Running analysis...";
      case "analysis_started":
        return "Interpreting results...";
      case "search_started":
        return "Searching the web...";
      case "search_completed":
        return "Search complete";
      case "search_failed":
        return "Web search unavailable";
      case "visualization_started":
        return "Generating visualization...";
      default:
        return "Processing...";
    }
  }, []);

  const startStream = useCallback(
    async (sessionId: string, message: string, webSearchEnabled: boolean = false) => {
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
        currentSearchQuery: null,
        searchSources: [],
        chartSpecs: null,
        chartError: null,
        visualizationInProgress: false,
        visualizationStage: null,
      });

      try {
        const accessToken = getAccessToken();
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }

        const response = await fetch(`http://localhost:8000/chat/sessions/${sessionId}/stream`, {
          method: "POST",
          headers,
          body: JSON.stringify({ content: message, web_search_enabled: webSearchEnabled }),
          signal: controller.signal,
        });

        if (!response.ok) {
          if (response.status === 402) {
            const errorBody = await response.json().catch(() => null);
            const detail = errorBody?.detail;
            const nextReset = typeof detail === "object" ? detail?.next_reset : null;
            let creditMsg = "You're out of credits.";
            if (nextReset) {
              const resetDate = new Date(nextReset);
              const timeFmt: Intl.DateTimeFormatOptions = {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              };
              const earliest = new Date(resetDate.getTime() - 15 * 60 * 1000);
              const latest = new Date(resetDate.getTime() + 15 * 60 * 1000);
              creditMsg += ` Credits reset between ${earliest.toLocaleString(undefined, timeFmt)} and ${latest.toLocaleString(undefined, timeFmt)}.`;
            } else {
              creditMsg += " Please contact your administrator.";
            }
            throw new Error(creditMsg);
          }
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
                    case "routing_started":
                      newState.currentStatus = "Analyzing your query...";
                      break;

                    case "routing_decided":
                      newState.currentStatus = event.message || "Processing...";
                      break;

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

                    case "search_started":
                      // Extract query from message like "Searching: 'query text'..."
                      {
                        const match = event.message?.match(/Searching:\s*'(.+?)'/);
                        newState.currentSearchQuery = match ? match[1] : (event.message || null);
                        newState.currentStatus = event.message || "Searching the web...";
                      }
                      break;

                    case "search_completed":
                      newState.currentSearchQuery = null;
                      newState.currentStatus = getStatusMessage("analysis_started");
                      break;

                    case "search_failed":
                      newState.currentSearchQuery = null;
                      newState.currentStatus = "Web search unavailable -- answering from available data";
                      break;

                    case "search_quota_exceeded":
                      newState.currentSearchQuery = null;
                      newState.currentStatus = "Search quota exceeded";
                      break;

                    case "visualization_started":
                      newState.visualizationInProgress = true;
                      newState.visualizationStage = event.message || "Analyzing data...";
                      newState.currentStatus = event.message || "Generating visualization...";
                      break;

                    case "chart_completed":
                      newState.chartSpecs = event.chart_specs || null;
                      newState.visualizationInProgress = false;
                      newState.visualizationStage = null;
                      newState.currentStatus = getStatusMessage("analysis_started");
                      break;

                    case "chart_failed":
                      newState.chartError = event.message || "Chart generation failed";
                      newState.visualizationInProgress = false;
                      newState.visualizationStage = null;
                      break;

                    case "node_complete":
                      // Node completion stored in events array
                      // Extract search sources from da_response node_complete
                      if (event.node === "da_response" && event.search_sources) {
                        newState.searchSources = event.search_sources;
                      }
                      // Extract chart data from viz_response or any node_complete with chart fields
                      if (event.chart_specs) {
                        newState.chartSpecs = event.chart_specs;
                        newState.visualizationInProgress = false;
                      }
                      if (event.chart_error) {
                        newState.chartError = event.chart_error;
                        newState.visualizationInProgress = false;
                      }
                      break;

                    case "completed":
                      newState.completedData = null;
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
      currentSearchQuery: null,
      searchSources: [],
      chartSpecs: null,
      chartError: null,
      visualizationInProgress: false,
      visualizationStage: null,
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
