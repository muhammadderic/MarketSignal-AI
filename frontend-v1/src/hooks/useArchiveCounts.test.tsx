import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ApiError } from '@/types/api';

// vi.hoisted lets us define mocks that vi.mock factories reference.
// Without it, factories run before top-level consts are initialized.
const { invalidateQueriesMock, fetchArchiveCountsMock } = vi.hoisted(() => ({
  invalidateQueriesMock: vi.fn(),
  fetchArchiveCountsMock: vi.fn(),
}));

vi.mock('@/api/queryClient', () => ({
  queryClient: { invalidateQueries: invalidateQueriesMock },
}));

vi.mock('@/api/archive', () => ({
  fetchArchiveCounts: (...args: unknown[]) => fetchArchiveCountsMock(...args),
}));

import {
  useArchiveCounts,
} from '@/hooks/useArchiveCounts';

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe('useArchiveCounts', () => {
  beforeEach(() => {
    fetchArchiveCountsMock.mockReset();
    invalidateQueriesMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('fetches counts and derives an O(1) countsByDate map', async () => {
    fetchArchiveCountsMock.mockResolvedValueOnce([
      { date: '2026-10-01', count: 12 },
      { date: '2026-10-21', count: 15 },
    ]);

    const { result } = renderHook(() => useArchiveCounts(2026, 10), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(fetchArchiveCountsMock).toHaveBeenCalledWith(2026, 10);
    expect(result.current.items).toHaveLength(2);
    expect(result.current.countsByDate.get('2026-10-01')).toBe(12);
    expect(result.current.countsByDate.get('2026-10-21')).toBe(15);
    expect(result.current.countsByDate.get('2026-10-02')).toBeUndefined();
    expect(result.current.isError).toBe(false);
  });

  it('exposes error state without crashing when the request fails', async () => {
    fetchArchiveCountsMock.mockRejectedValueOnce(new ApiError(500, 'boom'));

    const { result } = renderHook(() => useArchiveCounts(2026, 10), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.items).toEqual([]);
    expect(result.current.countsByDate.size).toBe(0);
    expect(result.current.error).toBeInstanceOf(ApiError);
  });
});