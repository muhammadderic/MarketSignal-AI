import type { Locale, ScoreOrNull } from "@shared/types";

/** Query params for GET /api/news/archive/counts */
export interface MonthlyCountsRequest {
  /** Format: YYYY-MM (e.g. "2026-10") */
  month: string;
  /** Locale filter, e.g. "ID" | "US" | "GLOBAL" | "UNASSIGNED" */
  locale: Locale;
}

/** A single date-to-count entry */
export interface DailyCount {
  /** Format: YYYY-MM-DD */
  date: string;
  /** Integer >= 1 */
  total: number;
}

/** Response for GET /api/news/archive/counts */
export interface MonthlyCountsResponse {
  /** Format: YYYY-MM */
  month: string;
  counts: DailyCount[];
}

/** Query params for GET /api/news */
export interface NewsByDateRequest {
  /** Format: YYYY-MM-DD */
  date: string;
}

/** A stored news record */
export interface NewsItem {
  id: number;
  title: string;
  source: string;
  /** ISO 8601 datetime */
  published_at: string;
  /** Complete article URL (never truncated) */
  link: string;
  locale: Locale;
  score: ScoreOrNull;
  reason: string | null;
}

/** Response for GET /api/news */
export interface NewsByDateResponse {
  /** Format: YYYY-MM-DD */
  date: string;
  items: NewsItem[];
}