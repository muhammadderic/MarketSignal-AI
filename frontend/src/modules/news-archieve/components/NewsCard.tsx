import type { NewsItem } from "../types";
import { cardColorClass, getCardColor } from "../utils/score";
import { isSafeArticleUrl, truncateUrl } from "../utils/url";

interface NewsCardProps {
  item: NewsItem;
  /** Selection wiring (optional to make the card stays reusable). */
  selected?: boolean;
  disabled?: boolean;
  onToggle?: (id: number) => void;
}

export const NewsCard = ({ 
  item,
  selected = false,
  disabled = false,
  onToggle,
}: NewsCardProps) => {
  const color = getCardColor(item.score);
  const safe = isSafeArticleUrl(item.link);

  // NewsCard is a reusable component, so onToggle is an optional prop (onToggle?).
  const selectable = typeof onToggle === "function";

  return (
    <article 
      className={`rounded-lg border p-4 ${cardColorClass[color]}`}
      aria-selected={selectable ? selected : undefined}
    >
      <div className="flex items-start gap-3">
        {selectable && (
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 shrink-0 cursor-pointer"
            checked={selected}
            disabled={disabled && !selected}
            onChange={() => onToggle?.(item.id)}
            aria-label={`Select "${item.title}" for scoring`}
          />
        )}

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="font-semibold text-base mb-1">{item.title}</h3>
            {item.score !== null && (
              <span
                className="shrink-0 inline-flex items-center justify-center
                          w-8 h-8 rounded-full border border-black/60
                          text-lg font-semibold leading-none"
              >
                {item.score}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-700">{item.source}</p>
          <p className="text-xs text-gray-500">
            {new Date(item.published_at).toLocaleString()}
          </p>

          {safe ? (
            <a
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 underline break-all text-sm"
              title={item.link}
            >
              {truncateUrl(item.link)}
            </a>
          ) : (
            <span className="text-gray-400 text-sm">Link unavailable</span>
          )}

          {item.reason !== null && (
            <p className="mt-2 text-sm text-gray-800">{item.reason}</p>
          )}
        </div>
      </div>
    </article>
  );
};