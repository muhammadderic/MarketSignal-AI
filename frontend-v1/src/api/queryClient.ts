import { QueryClient } from '@tanstack/react-query';

/**
 * Shared TanStack Query client.
 *
 * Defaults:
 * - 5-minute `staleTime` to match cached article/archive data freshness.
 * - 10-minute `gcTime` to retain inactive cache entries during navigation.
 * - `retry: 1` for queries (avoid amplifying upstream 429/5xx against external services).
 * - `retry: 0` for mutations (user-initiated, per ARC-003).
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});