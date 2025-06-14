import type {
  MonthlyCountsRequest,
  NewsByDateRequest,
} from "../types";

export const newsArchiveKeys = {
  all: ["news-archive"] as const,

  monthlyCounts: (params: MonthlyCountsRequest) =>
    [...newsArchiveKeys.all, "monthly-counts", params] as const,

  newsByDate: (params: NewsByDateRequest) =>
    [...newsArchiveKeys.all, "news-by-date", params] as const,
};