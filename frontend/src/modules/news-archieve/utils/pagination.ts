export const PAGE_SIZE = 20;

/** Clamp a raw page query param to a 1-based page number. */
export const parsePage = (raw: string | null): number => {
  const n = Number(raw);
  return Number.isInteger(n) && n >= 1 ? n : 1;
};

/** Slice an array for a 1-based page. */
export const paginate = <T>(items: T[], page: number, pageSize = PAGE_SIZE) => {
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;
  const end = start + pageSize;

  return {
    pageItems: items.slice(start, end),
    page: safePage,
    totalPages,
    totalItems,
    hasPrev: safePage > 1,
    hasNext: safePage < totalPages,
  };
};