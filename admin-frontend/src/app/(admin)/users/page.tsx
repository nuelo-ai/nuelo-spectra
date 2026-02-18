"use client";

import { useState } from "react";
import { useUserList } from "@/hooks/useUsers";
import { UserFilters } from "@/components/users/UserFilters";
import { UserTable } from "@/components/users/UserTable";
import { BulkActionBar } from "@/components/users/BulkActionBar";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircleIcon, UsersIcon } from "lucide-react";
import type { UserListParams } from "@/types/user";

export default function UsersPage() {
  const [filters, setFilters] = useState<UserListParams>({ page: 1 });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading, isError, refetch } = useUserList(filters);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <UsersIcon className="size-6 text-muted-foreground" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
          <p className="text-sm text-muted-foreground">
            Manage user accounts, tiers, and credits
          </p>
        </div>
      </div>

      {/* Filters */}
      <UserFilters filters={filters} onFilterChange={setFilters} />

      {/* Bulk action bar */}
      <BulkActionBar
        selectedIds={selectedIds}
        onClearSelection={() => setSelectedIds([])}
      />

      {/* Table content */}
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center gap-4 py-16">
          <AlertCircleIcon className="size-10 text-destructive" />
          <p className="text-muted-foreground">Failed to load users</p>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : (
        <UserTable
          users={data?.users ?? []}
          total={data?.total ?? 0}
          page={data?.page ?? 1}
          pageSize={data?.per_page ?? 20}
          totalPages={data?.total_pages ?? 1}
          filters={filters}
          onFilterChange={setFilters}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      )}
    </div>
  );
}
