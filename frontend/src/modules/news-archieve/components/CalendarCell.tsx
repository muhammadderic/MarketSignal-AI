import { NewsBadge } from "./NewsBadge";

interface CalendarCellProps {
  date: string;
  day: number;
  total: number;
  isSelected?: boolean;
  onSelect: (date: string) => void;
}

export const CalendarCell = ({
  date,
  day,
  total,
  isSelected,
  onSelect,
}: CalendarCellProps) => (
  <button
    type="button"
    onClick={() => onSelect(date)}
    aria-pressed={isSelected}
    className={`relative aspect-square rounded-md border text-sm
                transition-colors hover:bg-gray-50
                ${isSelected ? "ring-2 ring-blue-500" : ""}`}
  >
    <span className="absolute top-1 left-1">{day}</span>
    {total > 0 && <NewsBadge total={total} />}
  </button>
);