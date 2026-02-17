"use client";

import { useState, useMemo, useCallback } from "react";
import {
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { MoreHorizontalIcon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTableShell } from "@/components/shared/DataTableShell";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { ChallengeCodeDialog } from "@/components/shared/ChallengeCodeDialog";
import {
  useActivateUser,
  useDeactivateUser,
  useResetPassword,
  useDeleteUser,
} from "@/hooks/useUsers";
import type { UserSummary, UserListParams } from "@/types/user";

const columnHelper = createColumnHelper<UserSummary>();

function getInitials(first: string | null, last: string | null, email: string): string {
  if (first && last) return `${first[0]}${last[0]}`.toUpperCase();
  if (first) return first[0].toUpperCase();
  return email[0].toUpperCase();
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface UserTableProps {
  users: UserSummary[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  filters: UserListParams;
  onFilterChange: (filters: UserListParams) => void;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

export function UserTable({
  users,
  total,
  page,
  pageSize,
  totalPages,
  filters,
  onFilterChange,
  selectedIds,
  onSelectionChange,
}: UserTableProps) {
  const router = useRouter();
  const [actionUser, setActionUser] = useState<UserSummary | null>(null);
  const [actionType, setActionType] = useState<
    "deactivate" | "activate" | "reset-password" | "delete" | null
  >(null);

  const activateUser = useActivateUser();
  const deactivateUser = useDeactivateUser();
  const resetPassword = useResetPassword();
  const deleteUser = useDeleteUser();

  const handleAction = useCallback(
    (user: UserSummary, type: typeof actionType) => {
      setActionUser(user);
      setActionType(type);
    },
    []
  );

  const closeAction = useCallback(() => {
    setActionUser(null);
    setActionType(null);
  }, []);

  const executeAction = useCallback(async () => {
    if (!actionUser || !actionType) return;
    try {
      switch (actionType) {
        case "activate":
          await activateUser.mutateAsync({ userId: actionUser.id });
          toast.success(`${actionUser.email} activated`);
          break;
        case "deactivate":
          await deactivateUser.mutateAsync({ userId: actionUser.id });
          toast.success(`${actionUser.email} deactivated`);
          break;
        case "reset-password":
          await resetPassword.mutateAsync({ userId: actionUser.id });
          toast.success(`Password reset email sent to ${actionUser.email}`);
          break;
        case "delete":
          // Challenge code is handled client-side via ChallengeCodeDialog
          await deleteUser.mutateAsync({
            userId: actionUser.id,
            challenge_code: "CLIENT",
          });
          toast.success(`${actionUser.email} deleted`);
          break;
      }
    } catch (e: any) {
      toast.error(e.message);
    }
    closeAction();
  }, [
    actionUser,
    actionType,
    activateUser,
    deactivateUser,
    resetPassword,
    deleteUser,
    closeAction,
  ]);

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && "indeterminate")
            }
            onCheckedChange={(value) =>
              table.toggleAllPageRowsSelected(!!value)
            }
            aria-label="Select all"
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
        ),
        size: 40,
      }),
      columnHelper.display({
        id: "name",
        header: "Name",
        cell: ({ row }) => {
          const user = row.original;
          const name =
            user.first_name || user.last_name
              ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
              : user.email;
          return (
            <div className="flex items-center gap-3">
              <Avatar className="size-8">
                <AvatarFallback className="text-xs">
                  {getInitials(user.first_name, user.last_name, user.email)}
                </AvatarFallback>
              </Avatar>
              <span className="font-medium">{name}</span>
            </div>
          );
        },
      }),
      columnHelper.accessor("email", {
        header: "Email",
        cell: (info) => (
          <span className="text-muted-foreground">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor("is_active", {
        header: "Status",
        cell: (info) => (
          <StatusBadge
            type="status"
            value={info.getValue() ? "active" : "inactive"}
          />
        ),
      }),
      columnHelper.accessor("user_class", {
        header: "Tier",
        cell: (info) => (
          <StatusBadge type="tier" value={info.getValue()} />
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
      columnHelper.accessor("last_login_at", {
        header: "Last Login",
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
          const user = row.original;
          return (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="size-8 p-0">
                  <MoreHorizontalIcon className="size-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => router.push(`/users/${user.id}`)}
                >
                  View Detail
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {user.is_active ? (
                  <DropdownMenuItem
                    onClick={() => handleAction(user, "deactivate")}
                  >
                    Deactivate
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem
                    onClick={() => handleAction(user, "activate")}
                  >
                    Activate
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  onClick={() => handleAction(user, "reset-password")}
                >
                  Reset Password
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant="destructive"
                  onClick={() => handleAction(user, "delete")}
                >
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
        size: 50,
      }),
    ],
    [router, handleAction]
  );

  const rowSelection = useMemo(() => {
    const selection: Record<string, boolean> = {};
    users.forEach((u, i) => {
      if (selectedIds.includes(u.id)) {
        selection[String(i)] = true;
      }
    });
    return selection;
  }, [selectedIds, users]);

  const table = useReactTable({
    data: users,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: totalPages,
    state: {
      rowSelection,
    },
    onRowSelectionChange: (updater) => {
      const newSelection =
        typeof updater === "function" ? updater(rowSelection) : updater;
      const newIds = Object.entries(newSelection)
        .filter(([, v]) => v)
        .map(([idx]) => users[Number(idx)]?.id)
        .filter(Boolean) as string[];
      onSelectionChange(newIds);
    },
    enableRowSelection: true,
    getRowId: (row) => row.id,
  });

  const isLoading =
    activateUser.isPending ||
    deactivateUser.isPending ||
    resetPassword.isPending ||
    deleteUser.isPending;

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
        emptyMessage="No users found matching your criteria."
      />

      {/* Deactivate confirm */}
      <ConfirmModal
        open={actionType === "deactivate"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Deactivate User"
        description={`Are you sure you want to deactivate ${actionUser?.email}? They will be immediately logged out.`}
        confirmLabel="Deactivate"
        variant="destructive"
        loading={isLoading}
      />

      {/* Activate confirm */}
      <ConfirmModal
        open={actionType === "activate"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Activate User"
        description={`Are you sure you want to activate ${actionUser?.email}?`}
        confirmLabel="Activate"
        loading={isLoading}
      />

      {/* Reset password confirm */}
      <ConfirmModal
        open={actionType === "reset-password"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Reset Password"
        description={`Send a password reset email to ${actionUser?.email}?`}
        confirmLabel="Send Reset Email"
        loading={isLoading}
      />

      {/* Delete challenge */}
      <ChallengeCodeDialog
        open={actionType === "delete"}
        onClose={closeAction}
        onConfirm={executeAction}
        title="Delete User"
        description={`This will permanently delete ${actionUser?.email} and all their data. This action cannot be undone.`}
        loading={isLoading}
      />
    </>
  );
}
