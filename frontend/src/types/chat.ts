/**
 * Chat message request and response types.
 * These types mirror backend schemas in backend/app/schemas/chat.py
 */

export interface ChatMessageResponse {
  id: string;
  file_id: string;
  role: string;
  content: string;
  message_type: string | null;
  metadata_json: Record<string, any> | null;
  created_at: string;
}

export interface ChatMessageList {
  messages: ChatMessageResponse[];
  total: number;
}

export interface ChatQueryRequest {
  content: string;
}

export interface ChatAgentResponse {
  user_query: string;
  generated_code: string | null;
  execution_result: string | null;
  analysis: string;
  error: string | null;
  retry_count: number;
}

export type StreamEventType =
  | "routing_started"
  | "routing_decided"
  | "coding_started"
  | "validation_started"
  | "execution_started"
  | "analysis_started"
  | "progress"
  | "retry"
  | "content_chunk"
  | "node_complete"
  | "completed"
  | "error";

export interface StreamEvent {
  type: StreamEventType;
  event?: string;
  message?: string;
  step?: number;
  total_steps?: number;
  node?: string;
  text?: string;
  attempt?: number;
  max_attempts?: number;
  data?: Record<string, any>;
  route?: string;
  routing_decision?: {
    route: string;
    reasoning: string;
    context_summary: string;
  };
}
