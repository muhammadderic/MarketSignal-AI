import { useEffect, useState } from 'react';
import { useCalendarParams } from '@/hooks/useCalendarParams';
import { useArticles } from '@/hooks/useArticles';
import { useUIStore } from '@/stores/useUIStore';
import { ArticleCard } from '@/components/articles/ArticleCard';
import { BatchToolbar } from '@/components/articles/BatchToolbar';
import { useScoreRelevance } from '@/hooks/useScoreRelevance';
import type { Article, ArticleBatchScoreResponse, ArticleResolveURLResponse, ArticleScrapeResponse } from '@/types/article';
import { useResolveURLs } from '@/hooks/useResolveURLs';
import { useScrapeArticles } from '@/hooks/useScrapeArticles';
import { ScrapedContentModal } from './ScrapedContentModal';

const PAGE_SIZE = 50;

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 h-4 w-3/4 rounded bg-slate-200" />
      <div className="mb-2 h-3 w-1/3 rounded bg-slate-200" />
      <div className="flex gap-2">
        <div className="h-5 w-16 rounded bg-slate-200" />
        <div className="h-5 w-20 rounded bg-slate-200" />
        <div className="h-5 w-24 rounded bg-slate-200" />
      </div>
    </div>
  );
}

/**
 * Outer wrapper: resets local pagination and batch selection when the active
 * date changes by remounting the inner list via `key` (avoids setState-in-effect
 * cascading renders). Selection clearing is synced to the external Zustand
 * store inside the inner component because it is an external system.
 */
export function ArticleList() {
  const { date } = useCalendarParams();
  if (!date) {
    return null;
  }
  return <ArticleListBody key={date} date={date} />;
}

interface ArticleListBodyProps {
  date: string;
}

function ArticleListBody({ date }: ArticleListBodyProps) {
  const [offset, setOffset] = useState(0);

  const selectedIds = useUIStore((s) => s.selectedArticleIds);
  const toggleArticleSelection = useUIStore((s) => s.toggleArticleSelection);
  const selectAll = useUIStore((s) => s.selectAll);
  const clearSelection = useUIStore((s) => s.clearSelection);

  // R-004: selections are scoped to the active date filter. The component is
  // remounted on date change (key), so resetting the external store here runs
  // once per date — synchronizing React with the Zustand store, not local state.
  useEffect(() => {
    clearSelection();
  }, [clearSelection]);

  const { data, isLoading, isError, error, refetch, isFetching } = useArticles(
    { dateISO: date },
    { limit: PAGE_SIZE, offset },
  );

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const pageIndex = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  const handleSelectAllVisible = (ids: number[]) => {
    selectAll(ids);
  };

  // === SCORING ===
  const scoreMutation = useScoreRelevance();
  const [lastScoreSummary, setLastScoreSummary] = useState<string | null>(null);

  const handleScoreRelevance = (ids: number[]) => {
  if (ids.length === 0) return;
    setLastScoreSummary(null);
    scoreMutation.mutate(ids, {
      onSuccess: (res: ArticleBatchScoreResponse) => {
        setLastScoreSummary(
          `Scored ${res.success_count}, ${res.failed_count} failed of ${res.processed_count}`,
        );
      },
      onError: (err: Error) => {
        setLastScoreSummary(`Scoring failed: ${err.message}`);
      },
    });
  };

  const handleScoreSingle = (id: number) => {
    handleScoreRelevance([id]);
  };

  // === RESOLVING URLS ===
  const resolveMutation = useResolveURLs();
  const [lastResolveSummary, setLastResolveSummary] = useState<string | null>(null);

  const handleResolveUrls = (ids: number[]) => {
    if (ids.length === 0) return;
    setLastResolveSummary(null);
    resolveMutation.mutate(ids, {
      onSuccess: (res: ArticleResolveURLResponse) => {
        setLastResolveSummary(
          `Resolved ${res.success_count}, ${res.failed_count} failed of ${res.processed_count}`,
        );
      },
      onError: (err: Error) => {
        setLastResolveSummary(`Resolution failed: ${err.message}`);
      },
    });
  };

  // === SCRAPING ARTICLES ===
  const scrapeMutation = useScrapeArticles();
  const [lastScrapeSummary, setLastScrapeSummary] = useState<string | null>(null);

  const handleScrapeArticles = (ids: number[]) => {
    if (ids.length === 0) return;
    setLastScrapeSummary(null);
    scrapeMutation.mutate(ids, {
      onSuccess: (res: ArticleScrapeResponse) => {
        setLastScrapeSummary(
          `Scraped ${res.success_count}, ${res.failed_count} failed of ${res.processed_count}`,
        );
      },
      onError: (err: Error) => {
        setLastScrapeSummary(`Scraping failed: ${err.message}`);
      },
    });
  };

  // === CONTENT EDITOR (FEAT-007) ===
  const [editingArticleId, setEditingArticleId] = useState<number | null>(null);
  const handleEditContent = (article: Article) => {
    setEditingArticleId(article.id);
  };

  // R-001 UX: disable scrape when any selected article lacks a resolved URL.
  const selectedArticlesLackingResolvedUrl = items.filter(
    (a) => selectedIds.has(a.id) && a.resolved_url === null,
  );
  const scrapeDisabledReason =
    selectedArticlesLackingResolvedUrl.length > 0
      ? `${selectedArticlesLackingResolvedUrl.length} selected article(s) have no resolved URL — resolve URLs first.`
      : null;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">
          Articles on <span className="font-mono text-base">{date}</span>
        </h2>
        <span className="text-sm text-slate-600" data-testid="article-total">
          {total} total
        </span>
      </div>

      <BatchToolbar
        visibleArticles={items}
        selectedIds={selectedIds}
        onToggleAll={handleSelectAllVisible}
        onClearSelection={clearSelection}
        onScoreRelevance={handleScoreRelevance}
        isScoring={scoreMutation.isPending}
        scoreSummary={lastScoreSummary}
        onResolveUrls={handleResolveUrls}
        isResolving={resolveMutation.isPending}
        resolveSummary={lastResolveSummary}
        onScrapeArticles={handleScrapeArticles}
        isScraping={scrapeMutation.isPending}
        scrapeSummary={lastScrapeSummary}
        scrapeDisabledReason={scrapeDisabledReason}
      />

      {isError ? (
        <div
          className="flex items-center justify-between rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          <span>Failed to load articles: {error?.message ?? 'unknown error'}</span>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded border border-red-300 bg-white px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
          >
            Retry
          </button>
        </div>
      ) : null}

      {isLoading ? (
        <div className="space-y-3" role="status" aria-label="Loading articles">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-center text-sm text-slate-500">
          No articles for {date}.
        </p>
      ) : (
        <div className={`space-y-3 ${isFetching ? 'opacity-70' : ''}`}>
          {items.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              isSelected={selectedIds.has(article.id)}
              onToggleSelection={toggleArticleSelection}
              onScoreArticle={handleScoreSingle}
              isScoring={scoreMutation.isPending && scoreMutation.variables?.includes(article.id)}
              onEditContent={handleEditContent}
            />
          ))}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-slate-200 pt-3">
        <button
          type="button"
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          disabled={!canPrev}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-slate-600" data-testid="page-indicator">
          Page {pageIndex} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() => setOffset(offset + PAGE_SIZE)}
          disabled={!canNext}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>

      <ScrapedContentModal
        articleId={editingArticleId}
        onClose={() => setEditingArticleId(null)}
      />
    </section>
  );
}