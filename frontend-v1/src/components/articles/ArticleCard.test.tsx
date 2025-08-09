import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
// import userEvent from '@testing-library/user-event';

import { ArticleCard } from '@/components/articles/ArticleCard';
import type { Article } from '@/types/article';

function makeArticle(overrides: Partial<Article> = {}): Article {
  return {
    id: 101,
    title: 'Central Bank Signals Rate Adjustments',
    source_name: 'Financial News',
    published_at: '2026-10-21T08:30:00Z',
    published_at_date: '2026-10-21',
    google_url: 'https://news.google.com/articles/101',
    resolved_url: 'https://example.com/article/101',
    relevance_score: 4,
    relevance_reasoning: 'Direct macroeconomic impact.',
    scraping_status: 'SUCCESS',
    workflow_state: 'Scraped',
    created_at: '2026-10-21T09:00:00Z',
    updated_at: '2026-10-21T09:15:00Z',
    ...overrides,
  };
}

describe('ArticleCard', () => {
  it('renders headline, source, UTC timestamp, and status badges (AC-003)', () => {
    render(
      <ArticleCard
        article={makeArticle()}
        isSelected={false}
        onToggleSelection={vi.fn()}
      />,
    );

    expect(
      screen.getByRole('heading', { name: /central bank signals rate adjustments/i }),
    ).toBeInTheDocument();
    expect(screen.getByText('Financial News')).toBeInTheDocument();
    expect(screen.getByText(/2026-10-21 08:30 UTC/)).toBeInTheDocument();
    expect(screen.getByText('Score 4/5')).toBeInTheDocument();
    expect(screen.getByText('Scraped')).toBeInTheDocument();
    expect(screen.getByText('Scrape: SUCCESS')).toBeInTheDocument();
    expect(screen.getByText('Direct macroeconomic impact.')).toBeInTheDocument();
  });

  it('uses resolved_url for the external link when present', () => {
    render(
      <ArticleCard
        article={makeArticle()}
        isSelected={false}
        onToggleSelection={vi.fn()}
      />,
    );

    const link = screen.getByRole('link', { name: /open publisher url/i });
    expect(link).toHaveAttribute('href', 'https://example.com/article/101');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('falls back to google_url when resolved_url is null', () => {
    render(
      <ArticleCard
        article={makeArticle({ resolved_url: null })}
        isSelected={false}
        onToggleSelection={vi.fn()}
      />,
    );

    const link = screen.getByRole('link', { name: /open google news url/i });
    expect(link).toHaveAttribute('href', 'https://news.google.com/articles/101');
  });
})