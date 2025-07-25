import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { MonthNavigator } from '@/components/calendar/MonthNavigator';

describe('MonthNavigator', () => {
  it('renders the current month name and year', () => {
    render(
      <MonthNavigator
        year={2026}
        month={10}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onYearChange={vi.fn()}
      />,
    );

    expect(screen.getByTestId('calendar-month-label')).toHaveTextContent('October');
    expect(screen.getByLabelText('Year')).toHaveValue('2026');
  });

  it('invokes onPrev / onNext on button click', async () => {
    const user = userEvent.setup();
    const onPrev = vi.fn();
    const onNext = vi.fn();

    render(
      <MonthNavigator
        year={2026}
        month={10}
        onPrev={onPrev}
        onNext={onNext}
        onYearChange={vi.fn()}
      />,
    );

    await user.click(screen.getByRole('button', { name: /previous month/i }));
    await user.click(screen.getByRole('button', { name: /next month/i }));

    expect(onPrev).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it('renders a year range of current ±5 and calls onYearChange with a number', async () => {
    const user = userEvent.setup();
    const onYearChange = vi.fn();

    render(
      <MonthNavigator
        year={2026}
        month={10}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onYearChange={onYearChange}
      />,
    );

    const select = screen.getByLabelText('Year') as HTMLSelectElement;
    const optionValues = Array.from(select.options).map((o) => Number(o.value));
    expect(optionValues).toEqual([2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031]);

    await user.selectOptions(select, '2024');
    expect(onYearChange).toHaveBeenCalledWith(2024);
  });
});