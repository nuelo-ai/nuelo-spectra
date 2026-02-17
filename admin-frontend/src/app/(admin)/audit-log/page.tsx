"use client";

import { useState } from "react";
import { AuditLogTable } from "@/components/audit/AuditLogTable";
import { useAuditLog } from "@/hooks/useAuditLog";
import type { AuditLogParams } from "@/types/audit";

export default function AuditLogPage() {
  const [params, setParams] = useState<AuditLogParams>({
    page: 1,
    page_size: 25,
  });

  const { data, isLoading, error } = useAuditLog(params);

  const handleParamsChange = (partial: Partial<AuditLogParams>) => {
    setParams((prev) => ({ ...prev, ...partial }));
  };

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-destructive">
          Failed to load audit log: {error.message}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Audit Log</h1>
        <p className="text-muted-foreground">
          Track all administrative actions on the platform
        </p>
      </div>
      <AuditLogTable
        data={data?.items ?? []}
        total={data?.total ?? 0}
        page={data?.page ?? 1}
        pageSize={data?.page_size ?? 25}
        totalPages={data?.total_pages ?? 1}
        isLoading={isLoading}
        params={params}
        onParamsChange={handleParamsChange}
      />
    </div>
  );
}
