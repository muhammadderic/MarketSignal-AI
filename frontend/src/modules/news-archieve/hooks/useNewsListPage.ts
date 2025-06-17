import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import type { Locale } from "@shared/types";
import { useNewsScoring } from "@modules/news-scoring/hooks/useNewsScoring";

import { useNewsByDate } from "../queries/useNewsByDate";
import { useMonthlyCounts } from "../queries/useMonthlyCounts";
import { toArchiveMonth } from "../utils/date";
import { isValidDate } from "../utils/date";
import { paginate, parsePage } from "../utils/pagination";

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

  const validDate = date && isValidDate(date) ? date : null;
  const locale: Locale = localeParam ?? DEFAULT_LOCALE;

  const newsQuery = useNewsByDate(validDate ? { date: validDate } : null);

  // Counts query for the month of the selected date — used to reconcile
  // the calendar when the list comes back empty.
  const month = validDate ? toArchiveMonth(new Date(validDate)) : null;
  const countsQuery = useMonthlyCounts(month ? { month, locale } : null);

  /** Paginate client-side over the fetched items. */
  const pagination = useMemo(() => {
    const items = newsQuery.data?.items ?? [];
    return paginate(items, parsePage(pageParam));
  }, [newsQuery.data, pageParam]);

  // Selection + scoring orchestration.
  const scoring = useNewsScoring();

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
    scoring
  };
};