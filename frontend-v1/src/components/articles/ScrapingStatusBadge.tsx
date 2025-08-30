import type { ScrapingStatus } from '@/types/article';

export interface ScrapingStatusBadgeProps {
  status: ScrapingStatus;
}

const STYLES: Record<ScrapingStatus, { label: string; className: string }> = {
  PENDING: {
    label: 'Scrape Pending',
    className: 'border-slate-200 bg-slate-100 text-slate-600',
  },
  IN_PROGRESS: {
    label: 'Scraping…',
    className: 'border-amber-200 bg-amber-50 text-amber-700',
  },
  SUCCESS: {
    label: 'Scraped',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  FAILED: {
    label: 'Scrape Failed',
    className: 'border-red-200 bg-red-50 text-red-700',
  },
};

export function ScrapingStatusBadge({ status }: ScrapingStatusBadgeProps) {
  const { label, className } = STYLES[status];
  return (
    <span
      className={`rounded border px-1.5 py-0.5 text-xs font-medium ${className}`}
      data-scraping-status={status}
    >
      {label}
    </span>
  );
}