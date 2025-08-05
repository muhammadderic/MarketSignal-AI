import { ExternalLink } from 'lucide-react';
import type { Article, ScrapingStatus, WorkflowState } from '@/types/article';

export interface ArticleCardProps {
  article: Article;
  isSelected: boolean;
  onToggleSelection: (id: number) => void;
}

const SCORE_BADGE_CLASS: Record<number, string> = {
  1: 'bg-red-100 text-red-800 border-red-200',
  2: 'bg-orange-100 text-orange-800 border-orange-200',
  3: 'bg-amber-100 text-amber-800 border-amber-200',
  4: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  5: 'bg-emerald-200 text-emerald-900 border-emerald-300',
};

const WORKFLOW_BADGE_CLASS: Record<WorkflowState, string> = {
  Ingested: 'bg-slate-100 text-slate-700 border-slate-200',
  'Relevance Scored': 'bg-blue-100 text-blue-800 border-blue-200',
  'URL Resolved': 'bg-indigo-100 text-indigo-800 border-indigo-200',
  Scraped: 'bg-violet-100 text-violet-800 border-violet-200',
  'Financial Insight Extracted': 'bg-emerald-100 text-emerald-800 border-emerald-200',
};

const SCRAPING_BADGE_CLASS: Record<ScrapingStatus, string> = {
  PENDING: 'bg-slate-100 text-slate-600 border-slate-200',
  IN_PROGRESS: 'bg-amber-100 text-amber-800 border-amber-200',
  SUCCESS: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  FAILED: 'bg-red-100 text-red-800 border-red-200',
};

function formatPublishedAt(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return `${parsed.toISOString().slice(0, 10)} ${parsed.toISOString().slice(11, 16)} UTC`;
}

function scoreClass(score: number | null): string {
  if (score === null) return 'bg-slate-100 text-slate-600 border-slate-200';
  return SCORE_BADGE_CLASS[score] ?? 'bg-slate-100 text-slate-600 border-slate-200';
}

export function ArticleCard({ article, isSelected, onToggleSelection }: ArticleCardProps) {
  const linkUrl = article.resolved_url ?? article.google_url;
  const linkLabel = article.resolved_url ? 'Publisher URL' : 'Google News URL';
  const scoreTitle =
    article.relevance_score !== null && article.relevance_reasoning
      ? `Score ${article.relevance_score}: ${article.relevance_reasoning}`
      : article.relevance_reasoning ?? undefined;

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
          <span
            className={`rounded border px-1.5 py-0.5 text-xs font-medium ${scoreClass(article.relevance_score)}`}
            title={scoreTitle}
          >
            {article.relevance_score !== null
              ? `Score ${article.relevance_score}/5`
              : 'Unscored'}
          </span>
          <span
            className={`rounded border px-1.5 py-0.5 text-xs font-medium ${WORKFLOW_BADGE_CLASS[article.workflow_state]}`}
          >
            {article.workflow_state}
          </span>
          <span
            className={`rounded border px-1.5 py-0.5 text-xs font-medium ${SCRAPING_BADGE_CLASS[article.scraping_status]}`}
          >
            Scrape: {article.scraping_status}
          </span>
        </div>

        {article.relevance_reasoning ? (
          <p className="text-xs text-slate-500">{article.relevance_reasoning}</p>
        ) : null}
      </div>
    </article>
  );
}