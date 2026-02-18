/**
 * TypeScript types for admin invitation management.
 * Mirrors backend schemas: invitation.py
 */

export interface Invitation {
  id: string;
  email: string;
  status: string;
  created_at: string;
  expires_at: string;
  accepted_at: string | null;
}

export interface InvitationListResponse {
  items: Invitation[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateInvitationRequest {
  email: string;
}

export interface InvitationListParams {
  page?: number;
  page_size?: number;
  status?: string | null;
}
