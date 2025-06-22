import { useCallback, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router";

import type { Locale, ScoreOrNull } from "@shared/types";
import { useNewsScoring } from "@modules/news-scoring/hooks/useNewsScoring";

import { useNewsByDate } from "../queries/useNewsByDate";
import { useMonthlyCounts } from "../queries/useMonthlyCounts";
import { toArchiveMonth } from "../utils/date";
import { isValidDate } from "../utils/date";
import { paginate, parsePage } from "../utils/pagination";
import { applyScoreFilter, parseScoreFilter, serializeScoreFilter } from "../utils/scoreFilter";

const DEFAULT_LOCALE: Locale = "ID";

/**
 * Orchestrates the news-list page.
 * On empty result for a date that previously had a badge,
 * refreshes the relevant month's counts (UD §2.2.16, §4).
 */
export const useNewsListPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const date = searchParams.get("date");
  const pageParam = searchParams.get("page");
  const localeParam = searchParams.get("locale") as Locale | null;
  const scoreParam = searchParams.get("score");

  const validDate = date && isValidDate(date) ? date : null;
  const locale: Locale = localeParam ?? DEFAULT_LOCALE;

  const newsQuery = useNewsByDate(validDate ? { date: validDate } : null);

  // Counts query for the month of the selected date — used to reconcile
  // the calendar when the list comes back empty.
  const month = validDate ? toArchiveMonth(new Date(validDate)) : null;
  const countsQuery = useMonthlyCounts(month ? { month, locale } : null);

  /** Score filter parsed from the URL. */
  const scoreFilter = useMemo(
    () => parseScoreFilter(scoreParam),
    [scoreParam]
  );

  /** Filter first, then paginate — so page counts reflect the filtered set. */
  const pagination = useMemo(() => {
    const all = newsQuery.data?.items ?? [];
    const filtered = applyScoreFilter(all, scoreFilter);
    return paginate(filtered, parsePage(pageParam));
  }, [newsQuery.data, scoreFilter, pageParam]);

  // Selection + scoring orchestration.
  const scoring = useNewsScoring(validDate);
  const { ensureDate } = scoring.selection;

  // Keep the store's date in sync with the URL date. Since changing the
  // date resets selection here, the page handles the warning before the
  // URL changes (see NewsListPage). This is a safety net.
  useEffect(() => {
    if (validDate) ensureDate(validDate);
  }, [validDate, ensureDate]);

  /** Toggle a single score bucket; resets page to 1. */
  const toggleScore = useCallback(
    (score: ScoreOrNull) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          const next = new Set(parseScoreFilter(params.get("score")));
          if (next.has(score)) {
            next.delete(score);
          } else {
            next.add(score);
          }

          const serialized = serializeScoreFilter(next);
          if (serialized) {
            params.set("score", serialized);
          } else {
            params.delete("score");
          }
          params.delete("page"); // reset to page 1 on filter change
          return params;
        },
        { replace: false }
      );
    },
    [setSearchParams]
  );

  /** Clear all score filters. */
  const clearScoreFilter = useCallback(() => {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev);
        params.delete("score");
        params.delete("page");
        return params;
      },
      { replace: false }
    );
  }, [setSearchParams]);

  /** Write the page back to the URL; reset to 1 if the date/locale changes. */
  const setPage = useCallback(
    (next: number) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          if (next <= 1) {
            params.delete("page");
          } else {
            params.set("page", String(next));
          }
          return params;
        },
        { replace: false }
      );
      // Scroll to top so the new page starts at the first card.
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [setSearchParams]
  );

  /**
   * Called by the page when the news request succeeds with zero items.
   * Refreshes the affected month's counts to reconcile the calendar.
   */
  const reconcileCounts = useCallback(() => {
    if (countsQuery.data) {
      countsQuery.refetch();
    }
  }, [countsQuery]);

  return {
    date: validDate,
    locale,
    newsQuery,
    pagination,
    setPage,
    reconcileCounts,
    scoring,
    // Filtering
    scoreFilter,
    toggleScore,
    clearScoreFilter,
  };
};