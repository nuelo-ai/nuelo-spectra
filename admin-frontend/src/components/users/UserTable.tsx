"use client";

import { useState, useMemo, useCallback } from "react";
import {
  createColumnHelper,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  flexRender,
  type SortingState,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import { ChevronUpIcon, ChevronDownIcon, MoreHorizontalIcon } from "lucide-react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfirmModal } from "@/components/shared/ConfirmModal";
import { ChallengeCodeDialog } from "@/components/shared/ChallengeCodeDialog";
import {
  useActivateUser,
  useDeactivateUser,
  useResetPassword,
  useDeleteUser,
  useDeleteChallenge,
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
  const [sorting, setSorting] = useState<SortingState>([]);

  const activateUser = useActivateUser();
  const deactivateUser = useDeactivateUser();
  const resetPassword = useResetPassword();
  const deleteUser = useDeleteUser();
  const deleteChallenge = useDeleteChallenge();

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
    closeAction,
  ]);

  const handleDeleteConfirm = useCallback(
    async (challengeCode: string) => {
      if (!actionUser) return;
      try {
        await deleteUser.mutateAsync({
          userId: actionUser.id,
          challenge_code: challengeCode,
        });
        toast.success(`${actionUser.email} deleted`);
      } catch (e: any) {
        toast.error(e.message);
      }
      closeAction();
    },
    [actionUser, deleteUser, closeAction]
  );

  const handleFetchDeleteChallenge = useCallback(async () => {
    if (!actionUser) throw new Error("No user selected");
    return deleteChallenge.mutateAsync(actionUser.id);
  }, [actionUser, deleteChallenge]);

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
        enableSorting: false,
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
        enableSorting: true,
      }),
      columnHelper.accessor("email", {
        header: "Email",
        cell: (info) => (
          <span className="text-muted-foreground">{info.getValue()}</span>
        ),
        enableSorting: true,
      }),
      columnHelper.accessor("is_active", {
        header: "Status",
        cell: (info) => (
          <StatusBadge
            type="status"
            value={info.getValue() ? "active" : "inactive"}
          />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor("user_class", {
        header: "Tier",
        cell: (info) => (
          <StatusBadge type="tier" value={info.getValue()} />
        ),
        enableSorting: true,
      }),
      columnHelper.accessor("created_at", {
        header: "Created",
        cell: (info) => (
          <span className="text-muted-foreground">
            {formatDate(info.getValue())}
          </span>
        ),
        enableSorting: true,
      }),
      columnHelper.accessor("last_login_at", {
        header: "Last Login",
        cell: (info) => (
          <span className="text-muted-foreground">
            {formatDate(info.getValue())}
          </span>
        ),
        enableSorting: true,
      }),
      columnHelper.accessor("credit_balance", {
        header: "Credits",
        cell: (info) => (
          <span className="font-mono text-sm">
            {info.getValue().toFixed(1)}
          </span>
        ),
        enableSorting: true,
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
        enableSorting: false,
      }),
    ],
    [router, handleAction]
  );

  const rowSelection = useMemo(() => {
    const selection: Record<string, boolean> = {};
    selectedIds.forEach((id) => {
      selection[id] = true;
    });
    return selection;
  }, [selectedIds]);

  const table = useReactTable({
    data: users,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    pageCount: totalPages,
    state: {
      rowSelection,
      sorting,
    },
    onSortingChange: setSorting,
    onRowSelectionChange: (updater) => {
      const newSelection =
        typeof updater === "function" ? updater(rowSelection) : updater;
      const newIds = Object.entries(newSelection)
        .filter(([, v]) => v)
        .map(([id]) => id);
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

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <>
      <div className="space-y-4">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      className={header.column.getCanSort() ? "cursor-pointer select-none" : ""}
                    >
                      <div className="flex items-center gap-1">
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getIsSorted() === "asc" && <ChevronUpIcon className="size-3" />}
                        {header.column.getIsSorted() === "desc" && <ChevronDownIcon className="size-3" />}
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className="h-12"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center text-muted-foreground"
                  >
                    No users found matching your criteria.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            {total > 0 ? (
              <>
                Showing {start} to {end} of {total} results
              </>
            ) : (
              "No results"
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onFilterChange({ ...filters, page: 1 })}
              disabled={page <= 1}
            >
              First
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onFilterChange({ ...filters, page: page - 1 })}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onFilterChange({ ...filters, page: page + 1 })}
              disabled={page >= totalPages}
            >
              Next
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onFilterChange({ ...filters, page: totalPages })}
              disabled={page >= totalPages}
            >
              Last
            </Button>
          </div>
        </div>
      </div>

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
        onFetchChallenge={handleFetchDeleteChallenge}
        onConfirm={handleDeleteConfirm}
        title="Delete User"
        description={`This will permanently delete ${actionUser?.email} and all their data. This action cannot be undone.`}
        loading={isLoading}
      />
    </>
  );
}
