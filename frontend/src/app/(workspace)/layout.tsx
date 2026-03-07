"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { UnifiedSidebar } from "@/components/sidebar/UnifiedSidebar";

/**
 * Workspace layout - protected route for workspace pages.
 * Uses UnifiedSidebar without ChatSidebar or LinkedFilesPanel.
 */
export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex h-screen overflow-hidden w-full">
        <UnifiedSidebar />
        <main className="flex-1 overflow-y-auto overflow-x-hidden transition-all duration-300 ease-in-out">
          {children}
        </main>
      </div>
    </SidebarProvider>
  );
}
