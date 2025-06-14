import { useEffect } from "react";

import { useNewsListPage } from "../hooks/useNewsListPage";
import { NewsList } from "../components/NewsList";
import { NewsPagination } from "../components/NewsPagination";

export const NewsListPage = () => {
  const { date, newsQuery, pagination, setPage, reconcileCounts } = useNewsListPage();

  // Reconcile counts when a previously-badged date returns no items (UD §2.2.16).
  const isEmptyResult =
    newsQuery.isSuccess && (newsQuery.data?.items.length ?? 0) === 0;

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

      {isEmptyResult && (
        <p className="text-gray-500">No news available for this date.</p>
      )}

      {newsQuery.isSuccess && pagination.totalItems > 0 && (
        <>
          <NewsList items={pagination.pageItems} />
          <NewsPagination
            page={pagination.page}
            totalPages={pagination.totalPages}
            totalItems={pagination.totalItems}
            onPageChange={setPage}
          />
        </>
      )}
    </main>
  );
};