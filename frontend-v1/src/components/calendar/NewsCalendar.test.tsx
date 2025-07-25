import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';

import { NewsCalendar } from '@/components/calendar/NewsCalendar';

function makeMap(entries: Array<[string, number]>) {
  return new Map<string, number>(entries);
}

describe('NewsCalendar', () => {
    it('renders Sun–Sat headers and the correct number of grid cells for October 2026', () => {
    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([['2026-10-01', 12]])}
        selectedDate={null}
        isLoading={false}
        isError={false}
        onSelectDate={vi.fn()}
      />,
    );

    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent);
    expect(headers).toEqual(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']);

    // Query all gridcells including aria-hidden leading blanks.
    const grid = screen.getByRole('grid');
    const allCells = within(grid).getAllByRole('gridcell', { hidden: true });

    const visibleDays = allCells.filter((c) => c.getAttribute('data-date') !== null);
    expect(visibleDays).toHaveLength(31);

    // Oct 1 2026 is a Thursday → 4 leading blank cells.
    expect(allCells.length).toBe(4 + 31);
    expect(
      allCells.slice(0, 4).every((c) => c.getAttribute('data-date') === null),
    ).toBe(true);
  });
});