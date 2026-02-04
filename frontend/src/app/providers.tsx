"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { makeQueryClient } from "@/lib/query-client";

/**
 * Client-side providers wrapper.
 * Wraps children with TanStack Query provider and sonner toast notifications.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  // Create QueryClient instance only on client side
  const [queryClient] = useState(() => makeQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}
