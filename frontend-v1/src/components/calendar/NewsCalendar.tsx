import {
  addDays,
  endOfMonth,
  format,
  getDay,
  startOfMonth,
} from 'date-fns';

export interface NewsCalendarProps {
  year: number;
  month: number; // 1..12
  countsByDate: Map<string, number>;
  selectedDate: string | null; // YYYY-MM-DD
  isLoading: boolean;
  isError: boolean;
  onSelectDate: (date: string) => void;
}

const WEEKDAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const;

export function NewsCalendar({
  year,
  month,
  countsByDate,
  selectedDate,
  isLoading,
  isError,
  onSelectDate,
}: NewsCalendarProps) {
  const monthStart = startOfMonth(new Date(Date.UTC(year, month - 1, 1)));
  const monthEnd = endOfMonth(monthStart);
  const leadingBlanks = getDay(monthStart); // 0..6 (Sun=0)
  const dayCount = Number(format(monthEnd, 'd'));

  const cells: Array<{ iso: string; day: number } | null> = [];
  for (let i = 0; i < leadingBlanks; i += 1) {
    cells.push(null);
  }
  for (let d = 1; d <= dayCount; d += 1) {
    const iso = format(addDays(monthStart, d - 1), 'yyyy-MM-dd');
    cells.push({ iso, day: d });
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-7 gap-1" role="row">
        {WEEKDAY_LABELS.map((label) => (
          <div
            key={label}
            role="columnheader"
            className="py-1 text-center text-xs font-medium uppercase tracking-wide text-slate-500"
          >
            {label}
          </div>
        ))}
      </div>

      {isError ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          Failed to load calendar counts.
        </p>
      ) : null}

      <div className="grid grid-cols-7 gap-1" role="grid" aria-busy={isLoading}>
        {cells.map((cell, idx) => {
          if (cell === null) {
            return <div key={`blank-${idx}`} role="gridcell" aria-hidden="true" />;
          }

          const count = countsByDate.get(cell.iso) ?? 0;
          const hasArticles = count > 0;
          const isSelected = selectedDate === cell.iso;

          const baseClass =
            'relative flex aspect-square flex-col items-center justify-center rounded-md border p-1 text-sm';
          const stateClass = !hasArticles
            ? 'border-slate-100 bg-slate-50 text-slate-400'
            : isSelected
              ? 'border-slate-900 bg-slate-900 text-white'
              : 'border-slate-200 bg-white text-slate-900 hover:bg-slate-100';

          if (!hasArticles) {
            return (
              <div
                key={cell.iso}
                role="gridcell"
                aria-disabled="true"
                data-date={cell.iso}
                className={`${baseClass} ${stateClass}`}
              >
                <span>{cell.day}</span>
              </div>
            );
          }

          return (
            <button
              type="button"
              key={cell.iso}
              role="gridcell"
              data-date={cell.iso}
              aria-pressed={isSelected}
              aria-label={`${cell.iso}, ${count} article${count === 1 ? '' : 's'}`}
              className={`${baseClass} ${stateClass} focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400`}
              onClick={() => onSelectDate(cell.iso)}
            >
              <span>{cell.day}</span>
              <span
                className={`absolute right-1 top-1 rounded-full px-1.5 text-[10px] font-semibold ${
                  isSelected ? 'bg-white text-slate-900' : 'bg-slate-900 text-white'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <p className="text-xs text-slate-500" role="status">
          Loading counts…
        </p>
      ) : null}
    </div>
  );
}