"use client";

import { useMemo, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronsLeftIcon,
  ChevronsRightIcon,
  InfoIcon,
} from "lucide-react";
import type { AuditLogEntry, AuditLogParams } from "@/types/audit";

const columnHelper = createColumnHelper<AuditLogEntry>();

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Color-coded badge for common audit actions. */
function ActionBadge({ action }: { action: string }) {
  const label = action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  let variant: "default" | "secondary" | "outline" | "destructive" = "outline";
  if (action.includes("delete") || action.includes("revoke") || action.includes("deactivate")) {
    variant = "destructive";
  } else if (action.includes("create") || action.includes("add") || action.includes("activate")) {
    variant = "default";
  } else if (action.includes("update") || action.includes("adjust") || action.includes("reset")) {
    variant = "secondary";
  }

  return <Badge variant={variant}>{label}</Badge>;
}

interface AuditLogTableProps {
  data: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  isLoading: boolean;
  params: AuditLogParams;
  onParamsChange: (params: Partial<AuditLogParams>) => void;
}

const AUDIT_ACTIONS = [
  "login",
  "logout",
  "update_settings",
  "credit_adjustment",
  "credit_manual_reset",
  "create_invitation",
  "revoke_invitation",
  "resend_invitation",
  "activate_user",
  "deactivate_user",
  "delete_user",
  "change_tier",
  "view_credit_history",
];

export function AuditLogTable({
  data,
  total,
  page,
  pageSize,
  totalPages,
  isLoading,
  params,
  onParamsChange,
}: AuditLogTableProps) {
  const columns = useMemo(
    () => [
      columnHelper.accessor("created_at", {
        header: "Timestamp",
        cell: (info) => (
          <span className="whitespace-nowrap text-sm">
            {formatTimestamp(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("admin_email", {
        header: "Admin",
        cell: (info) => (
          <span className="text-sm">{info.getValue() ?? "System"}</span>
        ),
      }),
      columnHelper.accessor("action", {
        header: "Action",
        cell: (info) => <ActionBadge action={info.getValue()} />,
      }),
      columnHelper.accessor("target_type", {
        header: "Target Type",
        cell: (info) => (
          <span className="text-sm capitalize text-muted-foreground">
            {info.getValue()?.replace(/_/g, " ") ?? "-"}
          </span>
        ),
      }),
      columnHelper.accessor("target_id", {
        header: "Target ID",
        cell: (info) => {
          const val = info.getValue();
          if (!val) return <span className="text-muted-foreground">-</span>;
          const short = val.length > 8 ? `${val.slice(0, 8)}...` : val;
          return (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-help font-mono text-xs">{short}</span>
              </TooltipTrigger>
              <TooltipContent>
                <span className="font-mono text-xs">{val}</span>
              </TooltipContent>
            </Tooltip>
          );
        },
      }),
      columnHelper.accessor("details", {
        header: "Details",
        cell: (info) => {
          const details = info.getValue();
          if (!details || Object.keys(details).length === 0) {
            return <span className="text-muted-foreground">-</span>;
          }
          return (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <InfoIcon className="size-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-xs">
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(details, null, 2)}
                </pre>
              </TooltipContent>
            </Tooltip>
          );
        },
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={params.action ?? "__all__"}
          onValueChange={(val) =>
            onParamsChange({ action: val === "__all__" ? null : val, page: 1 })
          }
        >
          <SelectTrigger className="w-52">
            <SelectValue placeholder="All actions" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All Actions</SelectItem>
            {AUDIT_ACTIONS.map((a) => (
              <SelectItem key={a} value={a}>
                {a.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={params.target_type ?? "__all__"}
          onValueChange={(val) =>
            onParamsChange({
              target_type: val === "__all__" ? null : val,
              page: 1,
            })
          }
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All targets" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All Targets</SelectItem>
            <SelectItem value="user">User</SelectItem>
            <SelectItem value="user_credit">User Credit</SelectItem>
            <SelectItem value="invitation">Invitation</SelectItem>
            <SelectItem value="platform_settings">Settings</SelectItem>
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={params.date_from ?? ""}
          onChange={(e) =>
            onParamsChange({
              date_from: e.target.value || null,
              page: 1,
            })
          }
          className="w-40"
          placeholder="From date"
        />

        <Input
          type="date"
          value={params.date_to ?? ""}
          onChange={(e) =>
            onParamsChange({
              date_to: e.target.value || null,
              page: 1,
            })
          }
          className="w-40"
          placeholder="To date"
        />

        {(params.action || params.target_type || params.date_from || params.date_to) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              onParamsChange({
                action: null,
                target_type: null,
                date_from: null,
                date_to: null,
                page: 1,
              })
            }
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {columns.map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="h-12">
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
                  No audit log entries found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-2">
        <div className="text-sm text-muted-foreground">
          {total > 0 ? (
            <>
              Showing {start} to {end} of {total} entries
            </>
          ) : (
            "No entries"
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onParamsChange({ page: 1 })}
            disabled={page <= 1}
          >
            <ChevronsLeftIcon className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onParamsChange({ page: page - 1 })}
            disabled={page <= 1}
          >
            <ChevronLeftIcon className="size-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages || 1}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onParamsChange({ page: page + 1 })}
            disabled={page >= totalPages}
          >
            <ChevronRightIcon className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onParamsChange({ page: totalPages })}
            disabled={page >= totalPages}
          >
            <ChevronsRightIcon className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
