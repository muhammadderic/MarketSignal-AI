import { ChevronLeft, ChevronRight } from "lucide-react";

interface NewsPaginationProps {
  page: number;
  totalPages: number;
  totalItems: number;
  onPageChange: (page: number) => void;
}

export const NewsPagination = ({
  page,
  totalPages,
  totalItems,
  onPageChange,
}: NewsPaginationProps) => {
  if (totalPages <= 1) return null;

  return (
    <nav
      className="flex items-center justify-between mt-4"
      aria-label="News pagination"
    >
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="inline-flex items-center gap-1 px-3 py-1 rounded border
                   text-sm disabled:opacity-40 disabled:cursor-not-allowed
                   hover:bg-gray-50"
      >
        <ChevronLeft size={16} />
        Previous
      </button>

      <span className="text-sm text-gray-600">
        Page {page} of {totalPages} · {totalItems} articles
      </span>

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="inline-flex items-center gap-1 px-3 py-1 rounded border
                   text-sm disabled:opacity-40 disabled:cursor-not-allowed
                   hover:bg-gray-50"
      >
        Next
        <ChevronRight size={16} />
      </button>
    </nav>
  );
};