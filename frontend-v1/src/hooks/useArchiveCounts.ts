import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { queryClient } from '@/api/queryClient';
import { fetchArchiveCounts } from '@/api/archive';
import type { ArchiveCountItem } from '@/types/archive';

export const ARCHIVE_COUNTS_QUERY_KEY = 'archive-counts' as const;

export function archiveCountsQueryKey(year: number, month: number) {
  return [ARCHIVE_COUNTS_QUERY_KEY, year, month] as const;
}

export interface ArchiveCountsResult {
  items: ArchiveCountItem[];
  countsByDate: Map<string, number>;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
}

/**
 * Fetches daily article counts for `(year, month)` and derives an O(1)
 * `YYYY-MM-DD -> count` lookup for the calendar grid (TD-1).
 * Cached per `['archive-counts', year, month]` (R-004).
 */
export function useArchiveCounts(year: number, month: number): ArchiveCountsResult {
  const query = useQuery({
    queryKey: archiveCountsQueryKey(year, month),
    queryFn: () => fetchArchiveCounts(year, month),
  });

  const countsByDate = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of query.data ?? []) {
      map.set(item.date, item.count);
    }
    return map;
  }, [query.data]);

  return {
    items: query.data ?? [],
    countsByDate,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}

/**
 * Invalidate all archive-count queries (all months).
 * Call after successful ingestion (AC-007, TD-5).
 */
export function invalidateArchiveCounts(): Promise<void> {
  return queryClient.invalidateQueries({ queryKey: [ARCHIVE_COUNTS_QUERY_KEY] });
}