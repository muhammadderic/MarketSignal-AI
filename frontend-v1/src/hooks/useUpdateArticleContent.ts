import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateArticleContent } from '@/services/articleService';
import type { ArticleContentUpdateResponse } from '@/types/article';

interface UpdateArticleContentVariables {
  articleId: number;
  scrapedContent: string;
}

/**
 * Manual content-save mutation for `PUT /api/v1/articles/{id}/content`.
 * On success invalidates the list family and the specific detail entry so
 * the modal and the card status refresh against freshly persisted state.
 */
export function useUpdateArticleContent() {
  const queryClient = useQueryClient();
  return useMutation<
    ArticleContentUpdateResponse,
    Error,
    UpdateArticleContentVariables
  >({
    mutationFn: ({ articleId, scrapedContent }) =>
      updateArticleContent(articleId, scrapedContent),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['articles'] });
      void queryClient.invalidateQueries({
        queryKey: ['article', variables.articleId],
      });
    },
  });
}