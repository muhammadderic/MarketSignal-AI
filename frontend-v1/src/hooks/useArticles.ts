import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { fetchArticles } from '@/services/articleService';
import type {
  Article,
  ArticleFilters,
  ArticlePagination,
  ArticleListResponse,
} from '@/types/article';

/**
 * React Query hook for the paginated, date-filtered article list.
 *
 * The hook is pure: it does not read URL state. The caller passes filters
 * (derived from `useCalendarParams()`) and pagination explicitly so the same
 * hook can be reused across surfaces (NFR-007).
 */
export function useArticles(
  filters: ArticleFilters,
  pagination: ArticlePagination,
) {
  const { dateISO, workflowState = null } = filters;
  const { limit, offset } = pagination;

  return useQuery<ArticleListResponse, Error>({
    queryKey: ['articles', dateISO, workflowState, limit, offset],
    queryFn: () => {
      if (!dateISO) {
        // Query is disabled when `dateISO` is null; this branch is unreachable
        // in practice but keeps the function total and type-safe.
        return Promise.resolve({ total: 0, limit, offset, items: [] });
      }
      return fetchArticles({ dateISO, workflowState, limit, offset });
    },
    enabled: Boolean(dateISO),
    placeholderData: keepPreviousData,
  });
}

export type { Article };