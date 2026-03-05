"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { AdminSidebar } from "@/components/layout/admin-sidebar";

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Admin Sidebar */}
      <AdminSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content area — offset by sidebar width */}
      <div
        className={cn(
          "flex min-h-screen flex-col transition-all duration-200",
          sidebarCollapsed ? "ml-16" : "ml-60"
        )}
      >
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
