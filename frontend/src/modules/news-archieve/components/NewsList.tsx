import { NewsCard } from "./NewsCard";
import type { NewsItem } from "../types";

interface NewsListProps {
  items: NewsItem[];
}

export const NewsList = ({ items }: NewsListProps) => (
  <div className="space-y-3">
    {items.map((item) => (
      <NewsCard key={item.id} item={item} />
    ))}
  </div>
);