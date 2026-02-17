/**
 * TypeScript types for admin audit log.
 * Mirrors backend schemas: admin_audit.py
 */

export interface AuditLogEntry {
  id: string;
  admin_id: string | null;
  admin_email: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditLogParams {
  page?: number;
  page_size?: number;
  action?: string | null;
  admin_id?: string | null;
  target_type?: string | null;
  date_from?: string | null;
  date_to?: string | null;
}
