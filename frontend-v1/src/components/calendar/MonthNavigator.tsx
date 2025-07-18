import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface MonthNavigatorProps {
  year: number;
  month: number; // 1..12
  onPrev: () => void;
  onNext: () => void;
  onYearChange: (year: number) => void;
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
] as const;

const YEAR_RADIUS = 5;

export function MonthNavigator({
  year,
  month,
  onPrev,
  onNext,
  onYearChange,
}: MonthNavigatorProps) {
  const years: number[] = [];
  for (let y = year - YEAR_RADIUS; y <= year + YEAR_RADIUS; y += 1) {
    years.push(y);
  }

  const navButtonClass =
    'rounded-md border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-50 ' +
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 ' +
    'disabled:cursor-not-allowed disabled:opacity-50';

  return (
    <div className="flex items-center justify-between gap-3">
      <button
        type="button"
        aria-label="Previous month"
        className={navButtonClass}
        onClick={onPrev}
      >
        <ChevronLeft className="h-5 w-5" aria-hidden="true" />
      </button>

      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-slate-900" data-testid="calendar-month-label">
          {MONTH_NAMES[month - 1]}
        </span>
        <label className="sr-only" htmlFor="calendar-year-select">
          Year
        </label>
        <select
          id="calendar-year-select"
          className="rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          value={year}
          onChange={(e) => onYearChange(Number(e.target.value))}
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        aria-label="Next month"
        className={navButtonClass}
        onClick={onNext}
      >
        <ChevronRight className="h-5 w-5" aria-hidden="true" />
      </button>
    </div>
  );
}