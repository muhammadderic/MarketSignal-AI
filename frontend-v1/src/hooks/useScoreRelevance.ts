import { useMutation, useQueryClient } from '@tanstack/react-query';
import { scoreArticlesRelevance } from '@/services/articleService';
import type { ArticleBatchScoreResponse } from '@/types/article';

/**
 * React Query mutation hook for batch LLM title relevance scoring (FEAT-004).
 *
 * On success invalidates article list and detail queries so the newly persisted
 * `relevance_score` / `relevance_reasoning` / `workflow_state` are refetched.
 *
 * Defaults from `queryClient.ts` apply (`mutations.retry: 0` per ARC-003).
 */
export function useScoreRelevance() {
  const queryClient = useQueryClient();

  return useMutation<ArticleBatchScoreResponse, Error, number[]>({
    mutationFn: (articleIds: number[]) => scoreArticlesRelevance(articleIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['articles'] });
      void queryClient.invalidateQueries({ queryKey: ['article-detail'] });
    },
  });
}