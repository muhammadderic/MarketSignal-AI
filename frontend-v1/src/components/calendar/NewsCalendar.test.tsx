import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

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

    it('renders zero-count days as non-interactive gridcells', () => {
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

    const day01 = document.querySelector('[data-date="2026-10-01"]');
    expect(day01).not.toBeNull();
    // Day 01 has articles → rendered as an interactive button.
    expect(day01!.tagName).toBe('BUTTON');

    const day02 = document.querySelector('[data-date="2026-10-02"]');
    expect(day02).not.toBeNull();
    // Day 02 has zero articles → rendered as a disabled div, not clickable.
    expect(day02!.tagName).toBe('DIV');
    expect(day02!.getAttribute('aria-disabled')).toBe('true');
  });

  it('calls onSelectDate with the ISO date when an active day is clicked', async () => {
    const user = userEvent.setup();
    const onSelectDate = vi.fn();

    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([['2026-10-21', 15]])}
        selectedDate={null}
        isLoading={false}
        isError={false}
        onSelectDate={onSelectDate}
      />,
    );

    await user.click(screen.getByRole('gridcell', { name: /2026-10-21, 15 article/i }));

    expect(onSelectDate).toHaveBeenCalledTimes(1);
    expect(onSelectDate).toHaveBeenCalledWith('2026-10-21');
  });

  it('marks the selected day with aria-pressed=true', () => {
    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([['2026-10-21', 15]])}
        selectedDate="2026-10-21"
        isLoading={false}
        isError={false}
        onSelectDate={vi.fn()}
      />,
    );

    const day21 = screen.getByRole('gridcell', { name: /2026-10-21/i });
    expect(day21).toHaveAttribute('aria-pressed', 'true');
  });

  it('does not call onSelectDate when a zero-count day is clicked (non-interactive)', async () => {
    const user = userEvent.setup();
    const onSelectDate = vi.fn();

    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([['2026-10-21', 15]])}
        selectedDate={null}
        isLoading={false}
        isError={false}
        onSelectDate={onSelectDate}
      />,
    );

    const day02 = document.querySelector('[data-date="2026-10-02"]') as HTMLElement;
    await user.click(day02);
    expect(onSelectDate).not.toHaveBeenCalled();
  });

  it('renders the loading indicator while isLoading is true', () => {
    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([])}
        selectedDate={null}
        isLoading={true}
        isError={false}
        onSelectDate={vi.fn()}
      />,
    );

    expect(screen.getByRole('status')).toHaveTextContent(/loading counts/i);
  });

  it('renders an error alert when isError is true', () => {
    render(
      <NewsCalendar
        year={2026}
        month={10}
        countsByDate={makeMap([])}
        selectedDate={null}
        isLoading={false}
        isError={true}
        onSelectDate={vi.fn()}
      />,
    );

    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load calendar counts/i);
  });
});