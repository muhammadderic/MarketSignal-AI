import type { NewsByDateResponse } from "@modules/news-archieve/types";

/** Selection limits (DEV-MODE) */
export const SELECTION_MIN = 3; // 10
export const SELECTION_MAX = 5; // 20

/** Request body for POST /api/news/score */
export interface ScoreNewsRequest {
  news_ids: string[];
}

/** Response of POST /api/news/score (same shape as NewsByDateResponse) */
export type ScoreNewsResponse = NewsByDateResponse;