import { apiClient } from '@/api/apiClient';
import type { Article, ArticleListResponse } from '@/types/article';

export interface ListArticlesParams {
  dateISO: string;
  workflowState?: string | null;
  limit: number;
  offset: number;
}

/**
 * Fetch a paginated page of article metadata for a given UTC publication date.
 * Consumes `GET /api/v1/articles` (API_CONTRACTS.md §Endpoint: List Articles).
 */
export async function fetchArticles(params: ListArticlesParams): Promise<ArticleListResponse> {
  const { dateISO, workflowState, limit, offset } = params;
  const query: Record<string, string | number> = {
    date: dateISO,
    limit,
    offset,
  };
  if (workflowState) {
    query.workflow_state = workflowState;
  }
  const { data } = await apiClient.get<ArticleListResponse>('/articles', {
    params: query,
  });
  return data;
}

export type { Article };