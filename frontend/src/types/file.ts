/**
 * File request and response types.
 * These types mirror backend schemas in backend/app/schemas/file.py
 */

export interface FileUploadResponse {
  id: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  created_at: string;
  data_summary: string | null;
  user_context: string | null;
}

export interface FileListItem {
  id: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  created_at: string;
  updated_at: string;
  has_summary: boolean;
}

export interface FileDetailResponse {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  file_type: string;
  created_at: string;
  updated_at: string;
  data_summary: string | null;
  user_context: string | null;
}

export interface FileSummaryResponse {
  data_summary: string | null;
  user_context: string | null;
  query_suggestions: {
    categories: Array<{
      name: string;
      queries: string[];
    }>;
  } | null;
  suggestion_auto_send: boolean;
}
