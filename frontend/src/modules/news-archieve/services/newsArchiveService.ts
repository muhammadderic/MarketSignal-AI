import { apiClient } from "@shared/api/axiosClient";

import type {
  MonthlyCountsRequest,
  MonthlyCountsResponse,
  NewsByDateRequest,
  NewsByDateResponse,
  NewsItem,
} from "../types";
import { normalizeLocale, normalizeScore } from "../utils/score";
import { isValidDate, isValidMonth } from "../utils/date";

const API_BASE = "/api/v1/news-archieve";
const API_BASE_OLD = "/api/v1/news";

/**
 * Normalize a raw news item so the rest of the app can trust the shape.
 * Missing/unrecognized locale → UNASSIGNED; out-of-range score → null.
 */
const normalizeNewsItem = (raw: NewsItem): NewsItem => ({
  ...raw,
  locale: normalizeLocale(raw.locale),
  score: normalizeScore(raw.score),
  reason: typeof raw.reason === "string" ? raw.reason : null,
});

export const newsArchiveService = {
  /**
   * GET /api/news/archive/counts?month=YYYY-MM
   * Supply date-to-count data used to render calendar badges.
   */
  getMonthlyCounts: async (
    params: MonthlyCountsRequest,
    signal?: AbortSignal
  ): Promise<MonthlyCountsResponse> => {
    if (!isValidMonth(params.month)) {
      throw new Error(`Invalid month format: ${params.month}. Expected YYYY-MM.`);
    }

    const endpoint = `${API_BASE}/archive/counts`;

    const { data } = await apiClient.get<MonthlyCountsResponse>(endpoint, {
      params: { month: params.month, locale: params.locale },
      signal,
    });

    return data;
  },

  /**
   * GET /api/news?date=YYYY-MM-DD
   * Return stored news articles for a selected date.
   */
  getNewsByDate: async (
    params: NewsByDateRequest,
    signal?: AbortSignal
  ): Promise<NewsByDateResponse> => {
    if (!isValidDate(params.date)) {
      throw new Error(`Invalid date format: ${params.date}. Expected YYYY-MM-DD.`);
    }

    const endpoint = `${API_BASE_OLD}/by-date`;

    const { data } = await apiClient.get<NewsByDateResponse>(endpoint, {
      params: { date: params.date },
      signal,
    });

    return {
      date: data.date,
      items: data.items.map(normalizeNewsItem),
    };
  },
};