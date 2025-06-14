import { CalendarCell } from "./CalendarCell";
import type { UseArchiveCalendarResult } from "../hooks/useArchiveCalendar";

interface ArchiveCalendarProps {
  calendar: UseArchiveCalendarResult;
}

export const ArchiveCalendar = ({ calendar }: ArchiveCalendarProps) => {
  const { displayedMonth, countsQuery, countByDate, selectDate } = calendar;

  if (countsQuery.isLoading) {
    return <CalendarSkeleton />;
  }

  if (countsQuery.isError) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-600 mb-2">
          Failed to load news counts for this month.
        </p>
        <button
          type="button"
          onClick={() => countsQuery.refetch()}
          className="px-3 py-1 rounded bg-blue-600 text-white text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  const days = buildMonthGrid(displayedMonth);
  const isEmptyMonth = (countsQuery.data?.counts.length ?? 0) === 0;

  return (
    <div>
      {isEmptyMonth && (
        <p className="text-center text-gray-500 mb-2">
          No news archived for this month yet.
        </p>
      )}
      <div className="grid grid-cols-7 gap-1">
        {days.map(({ date, day, inMonth }) => (
          <CalendarCell
            key={date}
            date={date}
            day={day}
            total={inMonth ? countByDate.get(date) ?? 0 : 0}
            onSelect={selectDate}
          />
        ))}
      </div>
    </div>
  );
};

const CalendarSkeleton = () => (
  <div className="grid grid-cols-7 gap-1" aria-busy="true">
    {Array.from({ length: 42 }).map((_, i) => (
      <div key={i} className="aspect-square rounded-md bg-gray-100 animate-pulse" />
    ))}
  </div>
);

/** Build a 6-week grid for the given YYYY-MM. */
const buildMonthGrid = (month: string) => {
  const [y, m] = month.split("-").map(Number);
  const first = new Date(Date.UTC(y, m - 1, 1));
  const startDay = first.getUTCDay(); // 0 = Sunday
  const start = new Date(first);
  start.setUTCDate(first.getUTCDate() - startDay);

  const cells: { date: string; day: number; inMonth: boolean }[] = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(start);
    d.setUTCDate(start.getUTCDate() + i);
    const date = d.toISOString().slice(0, 10);
    cells.push({
      date,
      day: d.getUTCDate(),
      inMonth: d.getUTCMonth() === m - 1,
    });
  }
  return cells;
};