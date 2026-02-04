import { QueryClient } from "@tanstack/react-query";
import { cache } from "react";

/**
 * Creates a new QueryClient instance with default configuration.
 * Each client has a default staleTime of 60 seconds.
 */
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 60 seconds
      },
    },
  });
}

/**
 * Server-side singleton QueryClient for Next.js App Router.
 * Uses React cache to ensure one client per request.
 */
export const getQueryClient = cache(makeQueryClient);
