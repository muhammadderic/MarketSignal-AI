import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { MemoryRouter } from 'react-router';

import { useCalendarParams } from '@/hooks/useCalendarParams';
import type { ReactNode } from 'react';


// Render hook inside a router context via a tiny bridge component.
function renderCalendarParams(initialEntries: string[]) {
  function Wrapper({ children }: { children: ReactNode }) {
    return <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>;
  }
  return renderHook(() => useCalendarParams(), { wrapper: Wrapper });
}

describe('useCalendarParams', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('normalizes absent year/month to the current UTC month', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-15T12:00:00Z'));

    const { result } = renderCalendarParams(['/']);

    expect(result.current.year).toBe(2026);
    expect(result.current.month).toBe(10);
    expect(result.current.date).toBeNull();
  });

  it('normalizes out-of-range month to current UTC month', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-15T12:00:00Z'));

    const { result } = renderCalendarParams(['/?year=2026&month=13']);

    expect(result.current.year).toBe(2026);
    expect(result.current.month).toBe(10);
  });

  it('rejects years below 2001 and falls back to current UTC year', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-15T12:00:00Z'));

    const { result } = renderCalendarParams(['/?year=1999&month=5']);

    expect(result.current.year).toBe(2026);
    expect(result.current.month).toBe(5);
  });
});