import { NewsCard } from "./NewsCard";
import type { NewsItem } from "../types";

interface NewsListProps {
  items: NewsItem[];
  selectedIds: Set<string>;
  maxReached: boolean;
  onToggle: (id: string) => void;
}

export const NewsList = ({ 
  items,
  selectedIds,
  maxReached,
  onToggle,
}: NewsListProps) => (
  <div className="space-y-3">
    {items.map((item) => {
      const selected = selectedIds.has(item.id);
      return (
        <NewsCard
          key={item.id}
          item={item}
          selected={selected}
          // Disable unchecked cards when max is reached.
          disabled={maxReached && !selected}
          onToggle={onToggle}
        />
      )
    })}
  </div>
);