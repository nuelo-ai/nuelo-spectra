"use client";

import { useState } from "react";
import { useInvitationList } from "@/hooks/useInvitations";
import { InvitationTable } from "@/components/invitations/InvitationTable";
import { CreateInviteDialog } from "@/components/invitations/CreateInviteDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircleIcon, MailPlusIcon, MailIcon } from "lucide-react";
import type { InvitationListParams } from "@/types/invitation";

export default function InvitationsPage() {
  const [filters, setFilters] = useState<InvitationListParams>({ page: 1 });
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, isError, refetch } = useInvitationList(filters);

  const handleStatusChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      status: value === "all" ? null : value,
      page: 1,
    }));
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MailIcon className="size-6 text-muted-foreground" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Invitations
            </h1>
            <p className="text-sm text-muted-foreground">
              Manage user invitations
            </p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <MailPlusIcon className="mr-1.5 size-4" />
          Create Invitation
        </Button>
      </div>

      {/* Status filter */}
      <div className="flex items-center gap-3">
        <Select
          value={filters.status || "all"}
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="accepted">Accepted</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
      </div>

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
          <p className="text-muted-foreground">Failed to load invitations</p>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : (
        <InvitationTable
          invitations={data?.items ?? []}
          total={data?.total ?? 0}
          page={data?.page ?? 1}
          pageSize={data?.page_size ?? 20}
          filters={filters}
          onFilterChange={setFilters}
        />
      )}

      {/* Create dialog */}
      <CreateInviteDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
      />
    </div>
  );
}
