import { QueryClient } from "@tanstack/react-query";
import { cache } from "react";

/**
 * Creates a new QueryClient instance with admin-tuned defaults.
 * Shorter staleTime (30s) and limited retries for admin operations.
 */
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000, // 30 seconds
        retry: 1,
      },
    },
  });
}

/**
 * Server-side singleton QueryClient for Next.js App Router.
 * Uses React cache to ensure one client per request.
 */
export const getQueryClient = cache(makeQueryClient);
