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
}

export function BatchToolbar({
  visibleArticles,
  selectedIds,
  onToggleAll,
  onClearSelection,
  onScoreRelevance,
  onResolveUrls,
  onScrapeArticles,
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
        <button
          type="button"
          disabled={!hasSelection}
          onClick={() => onScoreRelevance?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Score Relevance
        </button>
        <button
          type="button"
          disabled={!hasSelection}
          onClick={() => onResolveUrls?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Resolve URLs
        </button>
        <button
          type="button"
          disabled={!hasSelection}
          onClick={() => onScrapeArticles?.(selectedArray)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Scrape Articles
        </button>
      </div>
    </div>
  );
}