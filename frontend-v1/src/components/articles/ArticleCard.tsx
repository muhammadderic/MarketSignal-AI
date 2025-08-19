import { ExternalLink } from 'lucide-react';
import type { Article } from '@/types/article';
import { ScoreBadge } from './ScoreBadge';

export interface ArticleCardProps {
  article: Article;
  isSelected: boolean;
  onToggleSelection: (id: number) => void;
  /** Single-article score trigger (AC-007 / FR-009). */
  onScoreArticle?: (id: number) => void;
  /** True while a scoring mutation is pending for this article. */
  isScoring?: boolean;
}

function formatPublishedAt(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return `${parsed.toISOString().slice(0, 10)} ${parsed.toISOString().slice(11, 16)} UTC`;
}

export function ArticleCard({
  article,
  isSelected,
  onToggleSelection,
  onScoreArticle,
  isScoring,
}: ArticleCardProps) {
  const linkUrl = article.resolved_url ?? article.google_url;
  const linkLabel = article.resolved_url ? 'Publisher URL' : 'Google News URL';

  return (
    <article
      className={`flex gap-3 rounded-lg border p-4 transition-colors ${
        isSelected
          ? 'border-slate-900 bg-slate-50'
          : 'border-slate-200 bg-white hover:bg-slate-50'
      }`}
      data-article-id={article.id}
    >
      <div className="pt-1">
        <input
          type="checkbox"
          aria-label={`Select article ${article.id}`}
          checked={isSelected}
          onChange={() => onToggleSelection(article.id)}
          className="h-4 w-4 rounded border-slate-300 text-slate-900 focus-visible:ring-2 focus-visible:ring-slate-400"
        />
      </div>

      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-900">{article.title}</h3>
          <a
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            title={linkLabel}
            aria-label={`Open ${linkLabel}`}
            className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
          {article.source_name ? (
            <span className="rounded border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-medium text-slate-700">
              {article.source_name}
            </span>
          ) : null}
          <span>{formatPublishedAt(article.published_at)}</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <ScoreBadge
            score={article.relevance_score}
            reasoning={article.relevance_reasoning}
            onScore={onScoreArticle ? () => onScoreArticle(article.id) : undefined}
            isScoring={isScoring}
          />
        </div>

        {article.relevance_reasoning ? (
          <p className="text-xs text-slate-500">{article.relevance_reasoning}</p>
        ) : null}
      </div>
    </article>
  );
}