import type { NewsByDateRequest } from "@modules/news-archieve/types";

export const newsScoringKeys = {
  all: ["newsScoring"] as const,
  newsByDate: (params: NewsByDateRequest) =>
    [...newsScoringKeys.all, "newsByDate", params] as const,
};