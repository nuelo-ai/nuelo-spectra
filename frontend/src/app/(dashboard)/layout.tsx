"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { FileSidebar } from "@/components/file/FileSidebar";

/**
 * Dashboard layout - protected route that requires authentication.
 * Shows loading spinner while checking auth state.
 * Redirects to login if not authenticated.
 * Layout: FileSidebar (left) + main content (right)
 */
export default function DashboardLayout({
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

  // Show loading spinner while checking auth state
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Show nothing if not authenticated (redirecting)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <FileSidebar />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
