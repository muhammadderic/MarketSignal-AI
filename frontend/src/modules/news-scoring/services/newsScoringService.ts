import { apiClient } from "@shared/api/axiosClient";

import type {
  ScoreNewsRequest,
  ScoreNewsResponse,
} from "../types";

const API_BASE = "/api/v1/news-scoring";

export const newsScoringService = {
  /**
   * Submit a batch of news IDs for scoring.
   * POST /api/news/score?date=YYYY-MM-DD
   * Body: { news_ids: number[] }
   */
  scoreNews: async (
    date: string,
    payload: ScoreNewsRequest,
    signal?: AbortSignal
  ): Promise<ScoreNewsResponse> => {
    const endpoint = `${API_BASE}/batch-by-ids`;

    const { data } = await apiClient.post<ScoreNewsResponse>(
      endpoint,
      payload,
      {
        params: { date },
        signal,
      }
    );
    return data;
  },
};