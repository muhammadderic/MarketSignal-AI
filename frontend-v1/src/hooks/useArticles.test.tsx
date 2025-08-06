import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';


const { fetchArticlesMock } = vi.hoisted(() => ({
  fetchArticlesMock: vi.fn(),
}));

vi.mock('@/services/articleService', () => ({
  fetchArticles: (...args: unknown[]) => fetchArticlesMock(...args),
}));

import { useArticles } from '@/hooks/useArticles';

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe('useArticles', () => {
  beforeEach(() => {
    fetchArticlesMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('is disabled when dateISO is null and does not call the service', () => {
    const { result } = renderHook(
      () => useArticles({ dateISO: null }, { limit: 50, offset: 0 }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
    expect(fetchArticlesMock).not.toHaveBeenCalled();
  });
});