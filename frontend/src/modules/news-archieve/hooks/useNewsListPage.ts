import { useCallback } from "react";
import { useSearchParams } from "react-router";
import { useNewsByDate } from "./useNewsByDate";
import { useMonthlyCounts } from "../queries/useMonthlyCounts";
import { toArchiveMonth } from "../utils/date";
import { isValidDate } from "../utils/date";
import type { Locale } from "@shared/types";

const DEFAULT_LOCALE: Locale = "UNASSIGNED";

/**
 * Orchestrates the news-list page.
 * On empty result for a date that previously had a badge,
 * refreshes the relevant month's counts (UD §2.2.16, §4).
 */
export const useNewsListPage = () => {
  const [searchParams] = useSearchParams();
  const date = searchParams.get("date");

  const localeParam = searchParams.get("locale") as Locale | null;

  const validDate = date && isValidDate(date) ? date : null;
  const locale: Locale = localeParam ?? DEFAULT_LOCALE;

  const newsQuery = useNewsByDate(validDate ? { date: validDate } : null);

  // Counts query for the month of the selected date — used to reconcile
  // the calendar when the list comes back empty.
  const month = validDate ? toArchiveMonth(new Date(validDate)) : null;
  const countsQuery = useMonthlyCounts(month ? { month, locale } : null);

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
    reconcileCounts,
  };
};