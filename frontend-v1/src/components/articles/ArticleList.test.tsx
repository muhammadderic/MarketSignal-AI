import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
// import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';

import type { Article, ArticleListResponse } from '@/types/article';
import { ApiError } from '@/types/api';
import { useUIStore } from '@/stores/useUIStore';

const { fetchArticlesMock } = vi.hoisted(() => ({
  fetchArticlesMock: vi.fn(),
}));

vi.mock('@/services/articleService', () => ({
  fetchArticles: (...args: unknown[]) => fetchArticlesMock(...args),
}));

import { ArticleList } from '@/components/articles/ArticleList';

function makeArticle(id: number, overrides: Partial<Article> = {}): Article {
  return {
    id,
    title: `Article ${id}`,
    source_name: 'Financial News',
    published_at: '2026-10-21T08:30:00Z',
    published_at_date: '2026-10-21',
    google_url: `https://news.google.com/articles/${id}`,
    resolved_url: null,
    relevance_score: null,
    relevance_reasoning: null,
    scraping_status: 'PENDING',
    workflow_state: 'Ingested',
    created_at: '2026-10-21T09:00:00Z',
    updated_at: '2026-10-21T09:00:00Z',
    ...overrides,
  };
}

function makeResponse(
  overrides: Partial<ArticleListResponse> = {},
): ArticleListResponse {
  return {
    total: 2,
    limit: 50,
    offset: 0,
    items: [makeArticle(1), makeArticle(2)],
    ...overrides,
  };
}

function renderWithProviders(ui: ReactNode, initialEntries: string[]) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

const DATE_URL = '/calendar?year=2026&month=10&date=2026-10-21';
// const OTHER_DATE_URL = '/calendar?year=2026&month=10&date=2026-10-22';

describe('ArticleList', () => {
  beforeEach(() => {
    fetchArticlesMock.mockReset();
    useUIStore.setState({
      selectedArticleIds: new Set<number>(),
      selectedDate: null,
      isEditorOpen: false,
    });
  });

  it('renders nothing when no date is selected', () => {
    const { container } = renderWithProviders(<ArticleList />, [
      '/calendar?year=2026&month=10',
    ]);

    expect(container).toBeEmptyDOMElement();
    expect(fetchArticlesMock).not.toHaveBeenCalled();
  });

  it('renders the article total, cards, and page indicator (AC-003, AC-007)', async () => {
    fetchArticlesMock.mockResolvedValueOnce(makeResponse());

    renderWithProviders(<ArticleList />, [DATE_URL]);

    expect(
      await screen.findByRole('heading', { name: /articles on 2026-10-21/i }),
    ).toBeInTheDocument();
    expect(await screen.findByTestId('article-total')).toHaveTextContent('2 total');
    expect(screen.getByText('Article 1')).toBeInTheDocument();
    expect(screen.getByText('Article 2')).toBeInTheDocument();
    expect(screen.getByTestId('page-indicator')).toHaveTextContent('Page 1 of 1');
  });

  it('shows a loading skeleton before data resolves', async () => {
    let resolveFetch: (value: ArticleListResponse) => void = () => undefined;
    fetchArticlesMock.mockReturnValueOnce(
      new Promise<ArticleListResponse>((resolve) => {
        resolveFetch = resolve;
      }),
    );

    renderWithProviders(<ArticleList />, [DATE_URL]);

    expect(screen.getByRole('status', { name: /loading articles/i })).toBeInTheDocument();

    resolveFetch(makeResponse());
    await waitFor(() => expect(screen.queryByRole('status', { name: /loading articles/i })).toBeNull());
  });

  it('shows the empty state when no articles exist', async () => {
    fetchArticlesMock.mockResolvedValueOnce(
      makeResponse({ total: 0, items: [] }),
    );

    renderWithProviders(<ArticleList />, [DATE_URL]);

    expect(await screen.findByText(/no articles for 2026-10-21/i)).toBeInTheDocument();
    expect(screen.getByTestId('page-indicator')).toHaveTextContent('Page 1 of 1');
  });

  it('shows an error banner with Retry that refetches', async () => {
    fetchArticlesMock.mockRejectedValueOnce(new ApiError(500, 'boom'));

    renderWithProviders(<ArticleList />, [DATE_URL]);

    expect(await screen.findByRole('alert')).toHaveTextContent(/failed to load articles/i);

    fetchArticlesMock.mockResolvedValueOnce(makeResponse());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /retry/i }));

    expect(await screen.findByText('Article 1')).toBeInTheDocument();
  });

  it('toggles per-card selection through the shared store (AC-004)', async () => {
    fetchArticlesMock.mockResolvedValueOnce(makeResponse());

    renderWithProviders(<ArticleList />, [DATE_URL]);
    await screen.findByText('Article 1');

    const user = userEvent.setup();
    await user.click(screen.getByRole('checkbox', { name: /select article 1/i }));

    expect(useUIStore.getState().selectedArticleIds.has(1)).toBe(true);
    expect(screen.getByTestId('selected-count')).toHaveTextContent('1 selected');
  });
})