import { useMutation, useQueryClient } from '@tanstack/react-query';
import { scrapeArticles } from '@/services/articleService';
import type { ArticleScrapeResponse } from '@/types/article';

/**
 * Batch scraping mutation for `POST /api/v1/articles/scrape`.
 *
 * Per-article failures are reflected in the 200 response body
 * (`scraping_status: "FAILED"` + `error`), not thrown as mutation errors.
 * On success we invalidate the `['articles']` cache family so the list view
 * re-reads updated `scraping_status` / `workflow_state` values.
 */
export function useScrapeArticles() {
  const queryClient = useQueryClient();
  return useMutation<ArticleScrapeResponse, Error, number[]>({
    mutationFn: (articleIds) => scrapeArticles(articleIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}