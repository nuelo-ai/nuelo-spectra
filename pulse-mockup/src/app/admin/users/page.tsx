"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ADMIN_USERS } from "@/lib/mock-data";

function TierBadge({ tier }: { tier: "free" | "pro" | "enterprise" }) {
  if (tier === "pro") {
    return (
      <Badge variant="outline" className="text-blue-400 border-blue-400/30">
        pro
      </Badge>
    );
  }
  if (tier === "enterprise") {
    return (
      <Badge variant="outline" className="text-purple-400 border-purple-400/30">
        enterprise
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-muted-foreground">
      free
    </Badge>
  );
}

function StatusBadge({ status }: { status: "active" | "suspended" }) {
  if (status === "active") {
    return (
      <Badge variant="outline" className="text-emerald-400 border-emerald-400/30">
        active
      </Badge>
    );
  }
  return (
    <Badge variant="destructive">
      suspended
    </Badge>
  );
}

export default function AdminUsersPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Users</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage workspace users and monitor their activity
        </p>
      </div>

      <div className="bg-card border border-border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Tier</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Credits Used</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ADMIN_USERS.map((user) => (
              <TableRow
                key={user.id}
                className="cursor-pointer hover:bg-muted/50"
              >
                <TableCell className="font-medium">
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="block w-full"
                  >
                    {user.name}
                  </Link>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="block w-full"
                  >
                    {user.email}
                  </Link>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="block w-full"
                  >
                    <TierBadge tier={user.tier} />
                  </Link>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="block w-full"
                  >
                    <StatusBadge status={user.status} />
                  </Link>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/admin/users/${user.id}`}
                    className="block w-full"
                  >
                    {user.credits}
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
