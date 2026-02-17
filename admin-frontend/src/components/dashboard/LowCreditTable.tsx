"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { LowCreditUser } from "@/types/dashboard";

interface LowCreditTableProps {
  users: LowCreditUser[];
}

/**
 * Table showing users with low credit balances.
 * Balance values below 5 are highlighted in red.
 */
export function LowCreditTable({ users }: LowCreditTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Low Credit Users</CardTitle>
      </CardHeader>
      <CardContent>
        {users.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">
            All users have sufficient credits
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead className="text-right">Balance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.user_id}>
                  <TableCell>
                    <div>
                      <p className="font-medium text-sm">{user.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{user.tier}</Badge>
                  </TableCell>
                  <TableCell
                    className={cn(
                      "text-right font-mono text-sm",
                      user.balance < 5
                        ? "text-red-600 dark:text-red-400 font-semibold"
                        : ""
                    )}
                  >
                    {user.balance.toLocaleString(undefined, {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
