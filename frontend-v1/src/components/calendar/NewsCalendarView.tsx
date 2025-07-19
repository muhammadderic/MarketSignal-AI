import { useArchiveCounts } from '@/hooks/useArchiveCounts';
import { useCalendarParams } from '@/hooks/useCalendarParams';
import { useUIStore } from '@/stores/useUIStore';
import { MonthNavigator } from '@/components/calendar/MonthNavigator';
import { NewsCalendar } from '@/components/calendar/NewsCalendar';

export function NewsCalendarView() {
  const { year, month, date, setMonth, setDate, prevMonth, nextMonth } = useCalendarParams();
  const { countsByDate, isLoading, isError } = useArchiveCounts(year, month);
  const setSelectedDate = useUIStore((s) => s.setSelectedDate);

  const handleYearChange = (nextYear: number) => {
    setMonth(nextYear, month);
  };

  const handleSelectDate = (iso: string) => {
    // AC-005: update URL (?date=) and mirror into client UI state for FEAT-003.
    setDate(iso);
    setSelectedDate(iso);
  };

  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <MonthNavigator
        year={year}
        month={month}
        onPrev={prevMonth}
        onNext={nextMonth}
        onYearChange={handleYearChange}
      />
      <NewsCalendar
        year={year}
        month={month}
        countsByDate={countsByDate}
        selectedDate={date}
        isLoading={isLoading}
        isError={isError}
        onSelectDate={handleSelectDate}
      />
      {date ? (
        <p className="text-sm text-slate-600" data-testid="selected-date">
          Selected date: <span className="font-medium">{date}</span>
        </p>
      ) : null}
    </section>
  );
}