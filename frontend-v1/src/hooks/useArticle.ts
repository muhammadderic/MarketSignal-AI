import { useQuery } from '@tanstack/react-query';
import { fetchArticleById } from '@/services/articleService';
import type { ArticleDetail } from '@/types/article';

/**
 * Load a single article's full detail (including `scraped_content`).
 * Keyed as `['article', id]` so other mutations (e.g. content updates) can
 * invalidate precisely this entry.
 */
export function useArticle(id: number | null) {
  return useQuery<ArticleDetail, Error>({
    queryKey: ['article', id],
    queryFn: () => {
      if (id === null) {
        return Promise.reject(new Error('Missing article id'));
      }
      return fetchArticleById(id);
    },
    enabled: id !== null,
  });
}