import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { BatchToolbar } from '@/components/articles/BatchToolbar';
import type { Article } from '@/types/article';

function makeArticle(id: number): Article {
  return {
    id,
    title: `Article ${id}`,
    source_name: 'Source',
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
  };
}

describe('BatchToolbar', () => {
  it('displays the selected count (AC-004)', () => {
    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1), makeArticle(2)]}
        selectedIds={new Set([1])}
        onToggleAll={vi.fn()}
        onClearSelection={vi.fn()}
      />,
    );

    expect(screen.getByTestId('selected-count')).toHaveTextContent('1 selected');
  });

  it('reflects fully-selected state on the Select All checkbox (AC-005)', () => {
    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1), makeArticle(2)]}
        selectedIds={new Set([1, 2])}
        onToggleAll={vi.fn()}
        onClearSelection={vi.fn()}
      />,
    );

    expect(screen.getByRole('checkbox', { name: /select all/i })).toBeChecked();
  });

  it('is indeterminate when only some visible articles are selected', () => {
    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1), makeArticle(2), makeArticle(3)]}
        selectedIds={new Set([2])}
        onToggleAll={vi.fn()}
        onClearSelection={vi.fn()}
      />,
    );

    const checkbox = screen.getByRole('checkbox', {
      name: /select all/i,
    }) as HTMLInputElement;
    expect(checkbox.indeterminate).toBe(true);
    expect(checkbox).not.toBeChecked();
  });

  it('calls onToggleAll with visible ids when Select All is checked (AC-005)', async () => {
    const user = userEvent.setup();
    const onToggleAll = vi.fn();

    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1), makeArticle(2)]}
        selectedIds={new Set()}
        onToggleAll={onToggleAll}
        onClearSelection={vi.fn()}
      />,
    );

    await user.click(screen.getByRole('checkbox', { name: /select all/i }));

    expect(onToggleAll).toHaveBeenCalledTimes(1);
    expect(onToggleAll).toHaveBeenCalledWith([1, 2]);
  });

  it('calls onClearSelection when Select All is unchecked while fully selected', async () => {
    const user = userEvent.setup();
    const onClearSelection = vi.fn();

    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1), makeArticle(2)]}
        selectedIds={new Set([1, 2])}
        onToggleAll={vi.fn()}
        onClearSelection={onClearSelection}
      />,
    );

    await user.click(screen.getByRole('checkbox', { name: /select all/i }));

    expect(onClearSelection).toHaveBeenCalledTimes(1);
  });

  it('disables action buttons when nothing is selected', () => {
    render(
      <BatchToolbar
        visibleArticles={[makeArticle(1)]}
        selectedIds={new Set()}
        onToggleAll={vi.fn()}
        onClearSelection={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: /score relevance/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /resolve urls/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /scrape articles/i })).toBeDisabled();
  });
})