import { createBrowserRouter } from 'react-router';

import { HomePage } from '@/pages/HomePage';
import { CalendarDatePage } from '@/pages/CalendarDatePage';
import { ArticleDetailPage } from '@/pages/ArticleDetailPage';

/**
 * Client-side route tree per TASK-006 §5 Recommended Route Set.
 * Path shapes match API_CONTRACTS.md date (`YYYY-MM-DD`) and id conventions.
 */
export const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/calendar/:date', element: <CalendarDatePage /> },
  { path: '/articles/:id', element: <ArticleDetailPage /> },
]);