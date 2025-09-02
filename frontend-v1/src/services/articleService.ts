import { apiClient } from '@/api/apiClient';
import type { 
  Article, 
  ArticleBatchScoreResponse, 
  ArticleContentUpdateResponse, 
  ArticleDetail, 
  ArticleListResponse, 
  ArticleResolveURLResponse, 
  ArticleScrapeResponse
} from '@/types/article';

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

/**
 * Submit selected article IDs for batch publisher URL resolution.
 * Consumes `POST /api/v1/articles/resolve-url` (API_CONTRACTS.md §Endpoint: Batch Publisher URL Resolution).
 *
 * The backend resolves Google News redirect URLs to canonical publisher URLs,
 * updates `workflow_state` to `'URL Resolved'` on success, and isolates
 * per-article failures (returned in `results` with `status: "FAILED"`).
 */
export async function resolveArticleURLs(
  articleIds: number[],
): Promise<ArticleResolveURLResponse> {
  const { data } = await apiClient.post<ArticleResolveURLResponse>(
    '/articles/resolve-url',
    { article_ids: articleIds },
  );
  return data;
}

/**
 * Submit selected article IDs for batch article content scraping.
 * Consumes `POST /api/v1/articles/scrape` (API_CONTRACTS.md §Endpoint: Batch Article Content Scraping).
 *
 * The backend requires `resolved_url` to be non-null for every submitted
 * article (otherwise HTTP 400); per-article failures are surfaced inside
 * `results` with `scraping_status: "FAILED"` and a descriptive `error`.
 */
export async function scrapeArticles(
  articleIds: number[],
): Promise<ArticleScrapeResponse> {
  const { data } = await apiClient.post<ArticleScrapeResponse>(
    '/articles/scrape',
    { article_ids: articleIds },
  );
  return data;
}

/**
 * Fetch a single article's full detail including heavy text columns.
 * Consumes `GET /api/v1/articles/{id}` (API_CONTRACTS.md §Endpoint: Get Article Detail).
 */
export async function fetchArticleById(id: number): Promise<ArticleDetail> {
  const { data } = await apiClient.get<ArticleDetail>(`/articles/${id}`);
  return data;
}

/**
 * Overwrite an article's `scraped_content` with manually edited text.
 * Consumes `PUT /api/v1/articles/{id}/content` (API_CONTRACTS.md §Endpoint: Update Scraped Article Content).
 *
 * On success the backend transitions `scraping_status -> 'SUCCESS'`, clears
 * `scraping_error`, and advances `workflow_state -> 'Scraped'`.
 */
export async function updateArticleContent(
  id: number,
  scrapedContent: string,
): Promise<ArticleContentUpdateResponse> {
  const { data } = await apiClient.put<ArticleContentUpdateResponse>(
    `/articles/${id}/content`,
    { scraped_content: scrapedContent },
  );
  return data;
}

export type { Article };