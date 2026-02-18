"use client";

import { useState, useMemo, useCallback } from "react";
import {
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { MoreHorizontalIcon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTableShell } from "@/components/shared/DataTableShell";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import {
  useRevokeInvitation,
  useResendInvitation,
} from "@/hooks/useInvitations";
import type { Invitation, InvitationListParams } from "@/types/invitation";

const columnHelper = createColumnHelper<Invitation>();

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface InvitationTableProps {
  invitations: Invitation[];
  total: number;
  page: number;
  pageSize: number;
  filters: InvitationListParams;
  onFilterChange: (filters: InvitationListParams) => void;
}

export function InvitationTable({
  invitations,
  total,
  page,
  pageSize,
  filters,
  onFilterChange,
}: InvitationTableProps) {
  const [actionInvite, setActionInvite] = useState<Invitation | null>(null);
  const [actionType, setActionType] = useState<"revoke" | "resend" | null>(
    null
  );

  const revokeInvitation = useRevokeInvitation();
  const resendInvitation = useResendInvitation();

  const handleAction = useCallback(
    (invite: Invitation, type: "revoke" | "resend") => {
      setActionInvite(invite);
      setActionType(type);
    },
    []
  );

  const closeAction = useCallback(() => {
    setActionInvite(null);
    setActionType(null);
  }, []);

  const executeAction = useCallback(async () => {
    if (!actionInvite || !actionType) return;
    try {
      if (actionType === "revoke") {
        await revokeInvitation.mutateAsync(actionInvite.id);
        toast.success(`Invitation to ${actionInvite.email} revoked`);
      } else {
        await resendInvitation.mutateAsync(actionInvite.id);
        toast.success(`Invitation resent to ${actionInvite.email}`);
      }
    } catch (e: any) {
      toast.error(e.message);
    }
    closeAction();
  }, [actionInvite, actionType, revokeInvitation, resendInvitation, closeAction]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const columns = useMemo(
    () => [
      columnHelper.accessor("email", {
        header: "Email",
        cell: (info) => (
          <span className="font-medium">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => (
          <StatusBadge type="invitation" value={info.getValue()} />
        ),
      }),
      columnHelper.accessor("created_at", {
        header: "Created",
        cell: (info) => (
          <span className="text-muted-foreground">
            {formatDate(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("expires_at", {
        header: "Expires",
        cell: (info) => (
          <span className="text-muted-foreground">
            {formatDate(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("accepted_at", {
        header: "Accepted",
        cell: (info) => (
          <span className="text-muted-foreground">
            {formatDate(info.getValue())}
          </span>
        ),
      }),
      columnHelper.display({
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const invite = row.original;
          const canRevoke = invite.status === "pending";
          const canResend =
            invite.status === "pending" || invite.status === "expired";

          if (!canRevoke && !canResend) return null;

          return (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="size-8 p-0">
                  <MoreHorizontalIcon className="size-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {canResend && (
                  <DropdownMenuItem
                    onClick={() => handleAction(invite, "resend")}
                  >
                    Resend
                  </DropdownMenuItem>
                )}
                {canRevoke && (
                  <DropdownMenuItem
                    variant="destructive"
                    onClick={() => handleAction(invite, "revoke")}
                  >
                    Revoke
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
        size: 50,
      }),
    ],
    [handleAction]
  );

  const table = useReactTable({
    data: invitations,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: totalPages,
    getRowId: (row) => row.id,
  });

  return (
    <>
      <DataTableShell
        table={table}
        columns={columns.length}
        page={page}
        pageSize={pageSize}
        total={total}
        totalPages={totalPages}
        onPageChange={(p) => onFilterChange({ ...filters, page: p })}
        emptyMessage="No invitations found."
      />

      {/* Revoke confirm */}
      <ConfirmModal
        open={actionType === "revoke"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Revoke Invitation"
        description={`Are you sure you want to revoke the invitation to ${actionInvite?.email}?`}
        confirmLabel="Revoke"
        variant="destructive"
        loading={revokeInvitation.isPending}
      />

      {/* Resend confirm */}
      <ConfirmModal
        open={actionType === "resend"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Resend Invitation"
        description={`Resend the invitation to ${actionInvite?.email}? A new invitation link will be generated.`}
        confirmLabel="Resend"
        loading={resendInvitation.isPending}
      />
    </>
  );
}
