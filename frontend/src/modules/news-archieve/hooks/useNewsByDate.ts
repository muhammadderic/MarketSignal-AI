import { useQuery } from "@tanstack/react-query";

import { minutes, seconds } from "@shared/utils/time";

import { newsArchiveService } from "../services/newsArchiveService";
import type { NewsByDateRequest } from "../types";
import { isValidDate } from "../utils/date";
import { newsArchiveKeys } from "../queries/queryKeys";

/**
 * Fetch the stored news list for a selected date.
 * Only enabled for dates that have a count badge (UD §2.2.10–15).
 */
export const useNewsByDate = (params: NewsByDateRequest | null) => {
  return useQuery({
    queryKey: newsArchiveKeys.newsByDate(params ?? { date: "" }),
    queryFn: async ({ signal }) => {
      return newsArchiveService.getNewsByDate(
        params as NewsByDateRequest,
        signal
      );
    },

    enabled: !!params && isValidDate(params.date),

    staleTime: seconds(30),
    gcTime: minutes(5),
    retry: 1,

    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
};