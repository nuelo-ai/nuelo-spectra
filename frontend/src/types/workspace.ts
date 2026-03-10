/**
 * Workspace TypeScript types matching backend API schemas
 * (backend/app/schemas/collection.py, backend/app/schemas/pulse.py)
 */

// --- Collection types ---

export interface CollectionListItem {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  file_count: number;
  signal_count: number;
}

export interface CollectionDetail extends CollectionListItem {
  report_count: number;
  credits_used: number;
}

export interface CollectionFile {
  id: string;
  file_id: string;
  added_at: string;
  filename: string;
  file_size: number | null;
  data_summary: string | null;
}

// --- Signal types ---

export interface SignalEvidence {
  metric: string;
  context: string;
  benchmark: string;
  impact: string;
}

export interface SignalDetail {
  id: string;
  title: string;
  severity: "critical" | "warning" | "info";
  category: string;
  analysis: string | null;
  evidence: SignalEvidence | null;
  chart_data: Record<string, unknown> | null;
  chart_type: "bar" | "line" | "scatter" | null;
  created_at: string;
}

// Alias used in plan frontmatter must_haves
export type SignalDetailResponse = SignalDetail;

// --- Pulse types ---

export interface PulseRunTrigger {
  pulse_run_id: string;
  status: string;
  credit_cost: number;
}

export interface PulseRunDetail {
  id: string;
  collection_id: string;
  status: string;
  credit_cost: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  signal_count: number;
  signals: SignalDetail[];
}

export interface PulseRunCreate {
  file_ids: string[];
  user_context?: string;
}

// --- Report types ---

export interface ReportListItem {
  id: string;
  title: string;
  report_type: string;
  created_at: string;
  pulse_run_id: string | null;
}

export interface ReportDetail extends ReportListItem {
  content: string | null;
  signal_count: number;
}
