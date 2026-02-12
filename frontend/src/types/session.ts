/**
 * Chat session request and response types.
 * These types mirror backend schemas in backend/app/schemas/chat_session.py
 */

export interface FileBasicInfo {
  id: string;
  original_filename: string;
  file_type: string;
  created_at: string;
}

export interface ChatSessionResponse {
  id: string;
  user_id: string;
  title: string;
  file_count: number;
  created_at: string;
  updated_at: string;
  user_modified: boolean;
}

export interface ChatSessionDetail extends ChatSessionResponse {
  files: FileBasicInfo[];
}

export interface ChatSessionList {
  sessions: ChatSessionResponse[];
  total: number;
}

export interface ChatSessionCreate {
  title: string;
}

export interface ChatSessionUpdate {
  title: string;
}
