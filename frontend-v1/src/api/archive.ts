import { apiClient } from '@/api/apiClient';
import type { ArchiveCountsResponse } from '@/types/archive';

/**
 * Fetch aggregated per-day article counts for a given month.
 * Backend: GET /api/v1/archive-counts?year=&month= (API_CONTRACTS.md).
 */
export async function fetchArchiveCounts(
  year: number,
  month: number,
): Promise<ArchiveCountsResponse> {
  const { data } = await apiClient.get<ArchiveCountsResponse>('/archive-counts', {
    params: { year, month },
  });
  return data;
}