"use client";

import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { BillingHistoryItem } from "@/hooks/useBillingHistory";

interface BillingHistoryTableProps {
  items: BillingHistoryItem[] | undefined;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
}

export function BillingHistoryTable({ items, isLoading, isError, refetch }: BillingHistoryTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-6 space-y-2">
        <p className="text-sm text-muted-foreground">Failed to load billing history. Please try again.</p>
        <Button variant="outline" size="sm" onClick={refetch}>Retry</Button>
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        No billing history yet.
      </p>
    );
  }

  const statusBadge = (status: string) => {
    switch (status) {
      case "succeeded":
        return <Badge variant="outline" className="text-green-600 border-green-500/20">Paid</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "refunded":
        return <Badge variant="outline">Refunded</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Amount</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="text-sm">
              {new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
            </TableCell>
            <TableCell className="text-sm">{item.type_display}</TableCell>
            <TableCell className="text-sm">{item.amount_display}</TableCell>
            <TableCell>{statusBadge(item.status)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
