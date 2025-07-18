import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';

export interface CalendarParams {
  year: number;
  month: number; // 1..12
  date: string | null; // YYYY-MM-DD or null
}

export interface CalendarParamsController extends CalendarParams {
  setMonth: (year: number, month: number) => void;
  setDate: (date: string | null) => void;
  prevMonth: () => void;
  nextMonth: () => void;
}

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const MIN_YEAR = 2001;

function parsePositiveInt(value: string | null): number | null {
  if (value === null) return null;
  const n = Number(value);
  return Number.isInteger(n) && n > 0 ? n : null;
}

function shiftMonth(year: number, month: number, delta: number): { year: number; month: number } {
  const zeroBased = year * 12 + (month - 1) + delta;
  return { year: Math.floor(zeroBased / 12), month: (zeroBased % 12) + 1 };
}

/**
 * URL-synchronized calendar navigation state (`?year&month&date`).
 * R-003: source of truth is React Router search params.
 * Normalizes absent/invalid params to the current UTC month (replace: true).
 */
export function useCalendarParams(): CalendarParamsController {
  const [searchParams, setSearchParams] = useSearchParams();

  const parsed = useMemo<CalendarParams>(() => {
    const now = new Date();
    const rawYear = parsePositiveInt(searchParams.get('year'));
    const rawMonth = parsePositiveInt(searchParams.get('month'));

    const year = rawYear !== null && rawYear >= MIN_YEAR ? rawYear : now.getUTCFullYear();
    const month =
      rawMonth !== null && rawMonth >= 1 && rawMonth <= 12 ? rawMonth : now.getUTCMonth() + 1;

    const rawDate = searchParams.get('date');
    const date = rawDate !== null && ISO_DATE_RE.test(rawDate) ? rawDate : null;

    return { year, month, date };
  }, [searchParams]);

  const write = useCallback(
    (next: Partial<CalendarParams>) => {
      setSearchParams(
        (prev) => {
          const merged: CalendarParams = {
            year: next.year ?? parsed.year,
            month: next.month ?? parsed.month,
            date: next.date !== undefined ? next.date : parsed.date,
          };
          const params = new URLSearchParams(prev);
          params.set('year', String(merged.year));
          params.set('month', String(merged.month));
          if (merged.date) {
            params.set('date', merged.date);
          } else {
            params.delete('date');
          }
          return params;
        },
        { replace: true },
      );
    },
    [parsed, setSearchParams],
  );

  const setMonth = useCallback(
    (year: number, month: number) => {
      // Changing the month invalidates any previously selected day.
      write({ year, month, date: null });
    },
    [write],
  );

  const setDate = useCallback(
    (date: string | null) => {
      write({ date });
    },
    [write],
  );

  const prevMonth = useCallback(() => {
    const { year, month } = shiftMonth(parsed.year, parsed.month, -1);
    setMonth(year, month);
  }, [parsed.year, parsed.month, setMonth]);

  const nextMonth = useCallback(() => {
    const { year, month } = shiftMonth(parsed.year, parsed.month, 1);
    setMonth(year, month);
  }, [parsed.year, parsed.month, setMonth]);

  return { ...parsed, setMonth, setDate, prevMonth, nextMonth };
}