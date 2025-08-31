import { useEffect, useRef } from 'react';
import type { Article } from '@/types/article';

export interface BatchToolbarProps {
  visibleArticles: Article[];
  selectedIds: Set<number>;
  onToggleAll: (ids: number[]) => void;
  onClearSelection: () => void;
  onScoreRelevance?: (ids: number[]) => void;
  onResolveUrls?: (ids: number[]) => void;
  onScrapeArticles?: (ids: number[]) => void;
  /** True while the batch scoring mutation is in flight (NFR-008). */
  isScoring?: boolean;
  /** Last batch scoring result summary, e.g. "Scored 3, 1 failed". */
  scoreSummary?: string | null;
  /** True while the batch URL resolution mutation is in flight (NFR-008). */
  isResolving?: boolean;
  /** Last batch URL resolution summary, e.g. "Resolved 4, 1 failed of 5". */
  resolveSummary?: string | null;
  /** True while the batch scraping mutation is in flight (NFR-008). */
  isScraping?: boolean;
  /** Last batch scraping summary, e.g. "Scraped 3, 1 failed of 4". */
  scrapeSummary?: string | null;
  /**
   * When set, the Scrape button is disabled and this string is surfaced via
   * `title` and `aria-describedby` (R-001: all selected must have `resolved_url`).
   */
  scrapeDisabledReason?: string | null;
}

export function BatchToolbar({
  visibleArticles,
  selectedIds,
  onToggleAll,
  onClearSelection,
  onScoreRelevance,
  onResolveUrls,
  onScrapeArticles,
  isScoring,
  scoreSummary,
  isResolving,
  resolveSummary,
  isScraping,
  scrapeSummary,
  scrapeDisabledReason,
}: BatchToolbarProps) {
  const selectAllRef = useRef<HTMLInputElement>(null);
  const visibleIds = visibleArticles.map((a) => a.id);
  const visibleSelectedCount = visibleIds.filter((id) => selectedIds.has(id)).length;
  const allVisibleSelected =
    visibleIds.length > 0 && visibleSelectedCount === visibleIds.length;
  const someVisibleSelected = visibleSelectedCount > 0 && !allVisibleSelected;

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = someVisibleSelected;
    }
  }, [someVisibleSelected]);

  const selectedArray = Array.from(selectedIds);
  const hasSelection = selectedArray.length > 0;

  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            ref={selectAllRef}
            type="checkbox"
            checked={allVisibleSelected}
            onChange={() => {
              if (allVisibleSelected) {
                onClearSelection();
              } else {
                onToggleAll(visibleIds);
              }
            }}
            disabled={visibleIds.length === 0}
            className="h-4 w-4 rounded border-slate-300 text-slate-900 focus-visible:ring-2 focus-visible:ring-slate-400"
          />
          Select All
        </label>
        <span className="text-sm text-slate-600" data-testid="selected-count">
          {selectedIds.size} selected
        </span>
        {hasSelection ? (
          <button
            type="button"
            onClick={onClearSelection}
            className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
          >
            Deselect All
          </button>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-2">
        {/* === SCORING BUTTON === */}
        <button
          type="button"
          disabled={!hasSelection || isScoring}
          onClick={() => onScoreRelevance?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isScoring ? 'Scoring…' : 'Score Relevance'}
        </button>
        {scoreSummary ? (
          <span className="self-center text-xs text-slate-600" role="status" data-testid="score-summary">
            {scoreSummary}
          </span>
        ) : null}

        {/* === RESOLVING URL BUTTON === */}
        <button
          type="button"
          disabled={!hasSelection || isResolving}
          onClick={() => onResolveUrls?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isResolving ? 'Resolving…' : 'Resolve URLs'}
        </button>
        {resolveSummary ? (
          <span className="self-center text-xs text-slate-600" role="status" data-testid="resolve-summary">
            {resolveSummary}
          </span>
        ) : null}

        {/* === SCRAPING ARTICLES === */}
        <button
          type="button"
          disabled={!hasSelection || isScraping || Boolean(scrapeDisabledReason)}
          title={scrapeDisabledReason ?? undefined}
          aria-describedby={scrapeDisabledReason ? 'scrape-disabled-reason' : undefined}
          onClick={() => onScrapeArticles?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isScraping ? 'Scraping…' : 'Scrape Articles'}
        </button>
        {scrapeDisabledReason ? (
          <span
            id="scrape-disabled-reason"
            className="self-center text-xs text-amber-700"
            role="status"
            data-testid="scrape-disabled-reason"
          >
            {scrapeDisabledReason}
          </span>
        ) : null}
        {scrapeSummary ? (
          <span
            className="self-center text-xs text-slate-600"
            role="status"
            data-testid="scrape-summary"
          >
            {scrapeSummary}
          </span>
        ) : null}
      </div>
    </div>
  );
}