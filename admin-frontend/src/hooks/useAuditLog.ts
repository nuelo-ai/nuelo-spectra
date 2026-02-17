"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import type { AuditLogListResponse, AuditLogParams } from "@/types/audit";

/**
 * Fetch paginated audit log entries with optional filters.
 */
export function useAuditLog(params: AuditLogParams = {}) {
  return useQuery<AuditLogListResponse>({
    queryKey: ["admin", "audit-log", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params.page) searchParams.set("page", String(params.page));
      if (params.page_size)
        searchParams.set("page_size", String(params.page_size));
      if (params.action) searchParams.set("action", params.action);
      if (params.admin_id) searchParams.set("admin_id", params.admin_id);
      if (params.target_type)
        searchParams.set("target_type", params.target_type);
      if (params.date_from) searchParams.set("date_from", params.date_from);
      if (params.date_to) searchParams.set("date_to", params.date_to);
      if (params.sort_by) searchParams.set("sort_by", params.sort_by);
      if (params.sort_order) searchParams.set("sort_order", params.sort_order);

      const qs = searchParams.toString();
      const res = await adminApiClient.get(
        `/api/admin/audit-log${qs ? `?${qs}` : ""}`
      );
      if (!res.ok) throw new Error("Failed to fetch audit log");
      return res.json();
    },
  });
}
