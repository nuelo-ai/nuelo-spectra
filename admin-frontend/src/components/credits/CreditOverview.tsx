"use client";

import {
  Card,
  CardContent,
  CardDescription,
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
import { Skeleton } from "@/components/ui/skeleton";
import { CoinsIcon, TrendingUpIcon, UsersIcon } from "lucide-react";
import type { CreditDistribution } from "@/types/credit";

interface CreditOverviewProps {
  distributions: CreditDistribution[] | undefined;
  isLoading: boolean;
}

export function CreditOverview({
  distributions,
  isLoading,
}: CreditOverviewProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const data = distributions ?? [];
  const totalUsers = data.reduce((sum, d) => sum + d.user_count, 0);
  const totalAvgBalance =
    data.length > 0
      ? data.reduce((sum, d) => sum + d.avg_balance * d.user_count, 0) /
        totalUsers
      : 0;
  const tiers = data.length;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription className="text-sm font-medium">
              Total Users
            </CardDescription>
            <UsersIcon className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalUsers.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Across {tiers} tier{tiers !== 1 ? "s" : ""}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription className="text-sm font-medium">
              Avg Credit Balance
            </CardDescription>
            <CoinsIcon className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalAvgBalance.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              Weighted average across tiers
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription className="text-sm font-medium">
              Active Tiers
            </CardDescription>
            <TrendingUpIcon className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tiers}</div>
            <p className="text-xs text-muted-foreground">
              User classes with credits
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tier breakdown table */}
      <Card>
        <CardHeader>
          <CardTitle>Credit Distribution by Tier</CardTitle>
          <CardDescription>
            Breakdown of credit balances across user classes
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.length === 0 ? (
            <p className="py-8 text-center text-muted-foreground">
              No credit data available
            </p>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tier</TableHead>
                    <TableHead className="text-right">Users</TableHead>
                    <TableHead className="text-right">Avg Balance</TableHead>
                    <TableHead className="text-right">% of Users</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((row) => (
                    <TableRow key={row.user_class}>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {row.user_class}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {row.user_count.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {Number(row.avg_balance).toFixed(1)}
                      </TableCell>
                      <TableCell className="text-right">
                        {totalUsers > 0
                          ? ((row.user_count / totalUsers) * 100).toFixed(1)
                          : "0.0"}
                        %
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
