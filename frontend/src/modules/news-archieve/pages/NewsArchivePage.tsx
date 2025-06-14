import { useArchiveCalendar } from "../hooks/useArchiveCalendar";
import { ArchiveCalendar } from "../components/ArchiveCalendar";
import type { Locale } from "@shared/types";

const LOCALES: Locale[] = ["ID", "US", "GLOBAL", "UNASSIGNED"];

export const NewsArchivePage = () => {
  const calendar = useArchiveCalendar();

  return (
    <main className="max-w-3xl mx-auto p-4">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">News Archive</h1>
         <div className="flex gap-2">
          <LocaleSelect value={calendar.locale} onChange={calendar.setLocale} />
          <MonthPicker
            value={calendar.displayedMonth}
            onChange={calendar.setDisplayedMonth}
          />
        </div>
      </header>

      <ArchiveCalendar calendar={calendar} />
    </main>
  );
};

interface LocaleSelectProps {
  value: Locale;
  onChange: (locale: Locale) => void;
}

const LocaleSelect = ({ value, onChange }: LocaleSelectProps) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value as Locale)}
    className="border rounded px-2 py-1 text-sm"
  >
    {LOCALES.map((l) => (
      <option key={l} value={l}>
        {l}
      </option>
    ))}
  </select>
);

interface MonthPickerProps {
  value: string;
  onChange: (month: string) => void;
}

const MonthPicker = ({ value, onChange }: MonthPickerProps) => (
  <input
    type="month"
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="border rounded px-2 py-1 text-sm"
  />
);