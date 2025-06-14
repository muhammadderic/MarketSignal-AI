import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import toast from "react-hot-toast";
import { toArchiveMonth } from "../utils/date";
import type { DailyCount, MonthlyCountsResponse } from "../types";
import { useMonthlyCounts } from "../queries/useMonthlyCounts";
import type { UseQueryResult } from "@tanstack/react-query";
import type { Locale } from "@shared/types";

export interface UseArchiveCalendarOptions {
  /** Base path for the news-list route, e.g. "/news" */
  newsListPath?: string;
  initialLocale?: Locale;
}

export interface UseArchiveCalendarResult {
  displayedMonth: string;
  setDisplayedMonth: (month: string) => void;
  locale: Locale;
  setLocale: (locale: Locale) => void;
  countsQuery: UseQueryResult<MonthlyCountsResponse, Error>;
  countByDate: Map<string, number>;
  hasCount: (date: string) => boolean;
  selectDate: (date: string) => void;
  refreshCounts: () => void;
}

export const useArchiveCalendar = (
  options: UseArchiveCalendarOptions = {}
): UseArchiveCalendarResult => {
  const { newsListPath = "/news", initialLocale = "ID"  } = options;
  const navigate = useNavigate();

  // Default to the current month (UD §2.1.2).
  const [displayedMonth, setDisplayedMonth] = useState<string>(() =>
    toArchiveMonth(new Date())
  );
  const [locale, setLocale] = useState<Locale>(initialLocale);

  const countsQuery = useMonthlyCounts({ month: displayedMonth, locale  });

  /** Map YYYY-MM-DD → total for O(1) badge lookup. */
  const countByDate = useMemo(() => {
    const map = new Map<string, number>();
    countsQuery.data?.counts.forEach((c: DailyCount) => {
      if (c.total > 0) map.set(c.date, c.total);
    });
    return map;
  }, [countsQuery.data]);

  const hasCount = useCallback(
    (date: string): boolean => (countByDate.get(date) ?? 0) > 0,
    [countByDate]
  );

  /**
   * Handle a date selection.
   * - Date with badge → navigate to news-list page.
   * - Date without badge → toast only, no API call (UD §2.2.12–15).
   */
  const selectDate = useCallback(
    (date: string) => {
      if (hasCount(date)) {
        navigate(`${newsListPath}?date=${encodeURIComponent(date)}&locale=${locale}`);
        return;
      }
      toast("No news available for this date.");
    },
    [hasCount, navigate, newsListPath, locale]
  );

  /** Manually refresh the displayed month's counts (UD §2.2.16, §2.4.34). */
  const refreshCounts = useCallback(() => {
    countsQuery.refetch();
  }, [countsQuery]);

  return {
    displayedMonth,
    setDisplayedMonth,
    locale,
    setLocale,
    countsQuery,
    countByDate,
    hasCount,
    selectDate,
    refreshCounts,
  };
};