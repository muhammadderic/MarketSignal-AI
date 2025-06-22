import { useEffect } from "react";

import { BackBtn } from "@shared/components/buttons";
import { ScoreSelectionBar } from "@modules/news-scoring/components/ScoreSelectionBar";

import { useNewsListPage } from "../hooks/useNewsListPage";
import { NewsList } from "../components/NewsList";
import { NewsPagination } from "../components/NewsPagination";
import { NewsScoreFilter } from "../components/NewsScoreFilter";

export const NewsListPage = () => {
  const { 
    date, 
    newsQuery, 
    pagination, 
    setPage, 
    reconcileCounts, 
    scoring,
    // Filtering
    scoreFilter,
    toggleScore,
    clearScoreFilter,
  } = useNewsListPage();

  const {
    selection,
    isSubmitting,
    submit
  } = scoring;

  // Reconcile counts when a previously-badged date returns no items.
  const isEmptyResult =
    newsQuery.isSuccess && (newsQuery.data?.items.length ?? 0) === 0;

    // "News exists for this date, but the score filter excluded all of it".
  const isEmptyAfterFilter =
    newsQuery.isSuccess &&
    (newsQuery.data?.items.length ?? 0) > 0 &&
    pagination.totalItems === 0;

  useEffect(() => {
    if (isEmptyResult) reconcileCounts();
  }, [isEmptyResult, reconcileCounts]);

  if (!date) {
    return (
      <main className="max-w-3xl mx-auto p-4">
        <p className="text-red-600">Invalid or missing date.</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-4">
      <BackBtn />
      
      <h1 className="text-xl font-bold mb-4">News for {date}</h1>

      {newsQuery.isLoading && (
        <p className="text-gray-500" aria-busy="true">
          Loading news…
        </p>
      )}

      {newsQuery.isError && (
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load news.</p>
          <button
            type="button"
            onClick={() => newsQuery.refetch()}
            className="px-3 py-1 rounded bg-blue-600 text-white text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {newsQuery.isSuccess && (newsQuery.data?.items.length ?? 0) > 0 && (
        <NewsScoreFilter
          selected={scoreFilter}
          onToggle={toggleScore}
          onClear={clearScoreFilter}
        />
      )}

      {isEmptyResult && (
        <p className="text-gray-500">No news available for this date.</p>
      )}

      {isEmptyAfterFilter && (
        <p className="text-gray-500">
          No news matches the selected score filter for this date.
        </p>
      )}

      {newsQuery.isSuccess && pagination.totalItems > 0 && (
        <>
          <NewsList 
            items={pagination.pageItems}
            selectedIds={selection.selectedIds}
            maxReached={selection.maxReached}
            onToggle={selection.toggle}
          />
          <NewsPagination
            page={pagination.page}
            totalPages={pagination.totalPages}
            totalItems={pagination.totalItems}
            onPageChange={setPage}
          />
          <ScoreSelectionBar 
            count={selection.count}
            minSelection={selection.minSelection}
            maxSelection={selection.maxSelection}
            canSubmit={selection.canSubmit}
            isSubmitting={isSubmitting}
            onSubmit={submit}
            onClear={selection.clear}
          />
        </>
      )}
    </main>
  );
};