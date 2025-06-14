import type { NewsItem } from "../types";
import { cardColorClass, getCardColor } from "../utils/score";
import { isSafeArticleUrl, truncateUrl } from "../utils/url";

interface NewsCardProps {
  item: NewsItem;
}

export const NewsCard = ({ item }: NewsCardProps) => {
  const color = getCardColor(item.score);
  const safe = isSafeArticleUrl(item.link);

  return (
    <article className={`rounded-lg border p-4 ${cardColorClass[color]}`}>
      <h3 className="font-semibold text-base mb-1">{item.title}</h3>
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
    </article>
  );
};