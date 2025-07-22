import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
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

  it('exposes a valid ISO date from the query string', () => {
    const { result } = renderCalendarParams(['/?year=2026&month=10&date=2026-10-21']);

    expect(result.current.date).toBe('2026-10-21');
  });

  it('drops malformed date values', () => {
    const { result } = renderCalendarParams(['/?year=2026&month=10&date=not-a-date']);

    expect(result.current.date).toBeNull();
  });

  it('prevMonth wraps across year boundary', () => {
    const { result } = renderCalendarParams(['/?year=2026&month=01']);

    act(() => result.current.prevMonth());

    expect(result.current.year).toBe(2025);
    expect(result.current.month).toBe(12);
  });

  it('nextMonth wraps across year boundary', () => {
    const { result } = renderCalendarParams(['/?year=2026&month=12']);

    act(() => result.current.nextMonth());

    expect(result.current.year).toBe(2027);
    expect(result.current.month).toBe(1);
  });
});