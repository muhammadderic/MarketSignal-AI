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