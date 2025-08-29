/**
 * Article domain types mirroring the backend `ArticleSummaryResponse` contract
 * (API_CONTRACTS.md §Endpoint: List Articles). Heavy text columns
 * (`scraped_content`, `financial_insight`) are intentionally absent.
 */

export type WorkflowState =
  | 'Ingested'
  | 'Relevance Scored'
  | 'URL Resolved'
  | 'Scraped'
  | 'Financial Insight Extracted';

export type ScrapingStatus = 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED';

export interface Article {
  id: number;
  title: string;
  source_name: string | null;
  published_at: string; // ISO-8601 UTC
  published_at_date: string; // YYYY-MM-DD
  google_url: string;
  resolved_url: string | null;
  relevance_score: number | null;
  relevance_reasoning: string | null;
  scraping_status: ScrapingStatus;
  workflow_state: WorkflowState;
  created_at: string;
  updated_at: string;
}

export interface ArticleListResponse {
  total: number;
  limit: number;
  offset: number;
  items: Article[];
}

export interface ArticleFilters {
  dateISO: string | null;
  workflowState?: WorkflowState | null;
}

export interface ArticlePagination {
  limit: number;
  offset: number;
}

// --------------------------------------
// --- The Batch Scoring API Contract ---
// --------------------------------------
export type ScoreItemStatus = 'SUCCESS' | 'FAILED';

/** Per-article result returned by POST /api/v1/articles/score-relevance. */
export interface ScoreItemResult {
  article_id: number;
  status: ScoreItemStatus;
  relevance_score: number | null;
  relevance_reasoning: string | null;
  error: string | null;
}

/** Response body for POST /api/v1/articles/score-relevance (API_CONTRACTS.md). */
export interface ArticleBatchScoreResponse {
  processed_count: number;
  success_count: number;
  failed_count: number;
  results: ScoreItemResult[];
}

// ----------------------
// --- Resolving APIs ---
// ----------------------
export type ResolveItemStatus = 'SUCCESS' | 'FAILED';

/** Per-article result returned by POST /api/v1/articles/resolve-url. */
export interface ResolveItemResult {
  article_id: number;
  status: ResolveItemStatus;
  resolved_url: string | null;
  error: string | null;
}

/** Response body for POST /api/v1/articles/resolve-url (API_CONTRACTS.md). */
export interface ArticleResolveURLResponse {
  processed_count: number;
  success_count: number;
  failed_count: number;
  results: ResolveItemResult[];
}

// ----------------------
// --- Scraping APIs ---
// ----------------------
/** Per-article result returned by POST /api/v1/articles/scrape. */
export interface ScrapeItemResult {
  article_id: number;
  scraping_status: ScrapingStatus;
  scraped_content_length: number | null;
  error: string | null;
}

/** Response body for POST /api/v1/articles/scrape (API_CONTRACTS.md). */
export interface ArticleScrapeResponse {
  processed_count: number;
  success_count: number;
  failed_count: number;
  results: ScrapeItemResult[];
}