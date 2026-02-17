"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type {
  InvitationListParams,
  InvitationListResponse,
  Invitation,
} from "@/types/invitation";

export function useInvitationList(params: InvitationListParams = {}) {
  return useQuery<InvitationListResponse>({
    queryKey: ["admin", "invitations", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params.page) searchParams.set("page", String(params.page));
      if (params.page_size)
        searchParams.set("page_size", String(params.page_size));
      if (params.status) searchParams.set("status", params.status);

      const qs = searchParams.toString();
      const res = await adminApiClient.get(
        `/api/admin/invitations${qs ? `?${qs}` : ""}`
      );
      if (!res.ok) throw new Error("Failed to fetch invitations");
      return res.json();
    },
  });
}

export function useCreateInvitation() {
  const qc = useQueryClient();
  return useMutation<Invitation, Error, { email: string }>({
    mutationFn: async (payload) => {
      const res = await adminApiClient.post("/api/admin/invitations", payload);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail =
          typeof body.detail === "string"
            ? body.detail
            : body.detail?.message || "Failed to create invitation";
        throw new Error(detail);
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "invitations"] });
    },
  });
}

export function useRevokeInvitation() {
  const qc = useQueryClient();
  return useMutation<Invitation, Error, string>({
    mutationFn: async (inviteId) => {
      const res = await adminApiClient.post(
        `/api/admin/invitations/${inviteId}/revoke`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to revoke invitation");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "invitations"] });
    },
  });
}

export function useResendInvitation() {
  const qc = useQueryClient();
  return useMutation<Invitation, Error, string>({
    mutationFn: async (inviteId) => {
      const res = await adminApiClient.post(
        `/api/admin/invitations/${inviteId}/resend`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to resend invitation");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "invitations"] });
    },
  });
}
