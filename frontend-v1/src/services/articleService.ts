import { apiClient } from '@/api/apiClient';
import type { Article, ArticleBatchScoreResponse, ArticleListResponse } from '@/types/article';

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

/**
 * Submit selected article IDs for LLM title relevance scoring.
 * Consumes `POST /api/v1/articles/score-relevance` (API_CONTRACTS.md §Endpoint: Batch Title Relevance Scoring).
 *
 * The backend enforces per-article fault isolation, so a 200 response may
 * contain both `SUCCESS` and `FAILED` items.
 */
export async function scoreArticlesRelevance(
  articleIds: number[],
): Promise<ArticleBatchScoreResponse> {
  const { data } = await apiClient.post<ArticleBatchScoreResponse>(
    '/articles/score-relevance',
    { article_ids: articleIds },
  );
  return data;
}

export type { Article };