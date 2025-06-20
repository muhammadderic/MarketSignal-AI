import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { NewsByDateRequest } from "@modules/news-archieve/types";
import { newsArchiveKeys } from "@modules/news-archieve/queries/queryKeys";

import type { ScoreNewsRequest, ScoreNewsResponse } from "../types";
import { newsScoringService } from "../services/newsScoringService";

interface ScoreNewsVariables {
  date: string;
  payload: ScoreNewsRequest;
}

/**
 * POST /api/news/score mutation.
 * On success, seeds the date cache with the returned items and invalidates
 * so the affected view (including other pages) reflects persisted results
 */
export const useScoreNews = () => {
  const queryClient = useQueryClient();

  return useMutation<ScoreNewsResponse, unknown, ScoreNewsVariables>({
    mutationFn: ({ date, payload }) =>
      newsScoringService.scoreNews(date, payload),

    onSuccess: (data, variables) => {
      const key = newsArchiveKeys.newsByDate({
        date: variables.date,
      } satisfies NewsByDateRequest);

      // Use persisted backend data directly.
      queryClient.setQueryData(key, data);

      // Also invalidate so any stale copies elsewhere refresh.
      queryClient.invalidateQueries({ queryKey: key });
    },
  });
}