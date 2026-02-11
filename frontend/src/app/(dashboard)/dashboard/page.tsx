"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy dashboard page - redirects to /sessions/new.
 * Kept to avoid broken bookmarks/links during transition.
 * Will be removed in Phase 18 cleanup.
 */
export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/sessions/new");
  }, [router]);

  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}
