import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
// import userEvent from '@testing-library/user-event';

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
})