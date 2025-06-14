import { useQuery } from "@tanstack/react-query";
import { minutes } from "@shared/utils/time";
import { newsArchiveService } from "../services/newsArchiveService";
import { newsArchiveKeys } from "./queryKeys";
import type { MonthlyCountsRequest } from "../types";
import { isValidMonth } from "../utils/date";

/**
 * Fetch date-to-news-count data for a given month.
 * Cached to reduce repeated work (UD §2.1.7).
 * Invalidated by the ingestion flow / manual refresh.
 */
export const useMonthlyCounts = (params: MonthlyCountsRequest | null) => {
  return useQuery({
    queryKey: newsArchiveKeys.monthlyCounts(
      params ?? { month: "", locale: "UNASSIGNED" }
    ),
    queryFn: async ({ signal }) => {
      // Caller guarantees non-null via `enabled`.
      return newsArchiveService.getMonthlyCounts(
        params as MonthlyCountsRequest,
        signal
      );
    },

    enabled: !!params && isValidMonth(params.month) && !!params.locale,

    staleTime: minutes(5),
    gcTime: minutes(30),
    retry: 1,

    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
};