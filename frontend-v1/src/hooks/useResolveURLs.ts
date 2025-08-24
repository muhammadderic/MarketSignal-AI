import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resolveArticleURLs } from '@/services/articleService';
import type { ArticleResolveURLResponse } from '@/types/article';

/**
 * React Query mutation hook for batch publisher URL resolution (FEAT-005).
 *
 * On success invalidates `['articles']` and `['archive-counts']` so freshly
 * resolved publisher URLs (and any downstream effects on article views) are
 * refetched (FEAT-005 §4.1).
 *
 * Defaults from `queryClient.ts` apply (`mutations.retry: 0` per ARC-003).
 */
export function useResolveURLs() {
  const queryClient = useQueryClient();

  return useMutation<ArticleResolveURLResponse, Error, number[]>({
    mutationFn: (articleIds: number[]) => resolveArticleURLs(articleIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['articles'] });
      void queryClient.invalidateQueries({ queryKey: ['archive-counts'] });
    },
  });
}