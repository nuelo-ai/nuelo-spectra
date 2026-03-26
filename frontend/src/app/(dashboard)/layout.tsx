"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { UnifiedSidebar } from "@/components/sidebar/UnifiedSidebar";
import { LinkedFilesPanel } from "@/components/session/LinkedFilesPanel";
import { useSessionStore } from "@/stores/sessionStore";
import { useSessionDetail } from "@/hooks/useChatSessions";
import { TrialBanner } from "@/components/trial/TrialBanner";
import { TrialExpiredOverlay } from "@/components/trial/TrialExpiredOverlay";

/**
 * Dashboard layout - protected route that requires authentication.
 * Shows loading spinner while checking auth state.
 * Redirects to login if not authenticated.
 * Layout: SidebarProvider wrapping ChatSidebar (left) + main content (center) + LinkedFilesPanel (right).
 * No top nav header - user menu is in the sidebar UserSection.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const { data: sessionDetail } = useSessionDetail(currentSessionId);

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
    <SidebarProvider defaultOpen={true}>
      <div className="flex h-screen overflow-hidden w-full">
        <UnifiedSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <TrialBanner />
          <main className="flex-1 overflow-y-auto overflow-x-hidden transition-all duration-300 ease-in-out">
            {children}
          </main>
        </div>
        {currentSessionId && (
          <LinkedFilesPanel
            sessionId={currentSessionId}
            files={sessionDetail?.files ?? []}
          />
        )}
      </div>
      <TrialExpiredOverlay />
    </SidebarProvider>
  );
}
