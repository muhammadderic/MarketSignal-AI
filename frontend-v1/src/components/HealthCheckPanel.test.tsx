import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { HealthCheckPanel } from './HealthCheckPanel';

const useHealthCheckMock = vi.hoisted(() => vi.fn());

vi.mock('@/hooks/useHealthCheck', () => ({
  useHealthCheck: useHealthCheckMock,
}));

describe('HealthCheckPanel', () => {
  beforeEach(() => {
    useHealthCheckMock.mockReset();
  });

  it('renders the section heading in every state', () => {
    useHealthCheckMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    render(<HealthCheckPanel />);
    expect(
      screen.getByRole('heading', { name: /backend connectivity/i }),
    ).toBeInTheDocument();
  });

  it('renders the pending message while the query is loading', () => {
    useHealthCheckMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    render(<HealthCheckPanel />);
    expect(screen.getByText(/Probing \/api\/v1\/health/)).toBeInTheDocument();
  });

  it('renders the error message with the underlying error text', () => {
    useHealthCheckMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new Error('boom'),
    });
    render(<HealthCheckPanel />);
    expect(screen.getByText(/Health check failed: boom/)).toBeInTheDocument();
  });

  it('renders status, database, and timestamp when data is present', () => {
    useHealthCheckMock.mockReturnValue({
      data: {
        status: 'healthy',
        database: 'connected',
        timestamp: '2026-10-28T12:00:00Z',
      },
      isPending: false,
      isError: false,
      error: null,
    });
    render(<HealthCheckPanel />);
    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
    expect(screen.getByText('2026-10-28T12:00:00Z')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getByText('Timestamp')).toBeInTheDocument();
  });

  it('omits the database and timestamp rows when those fields are absent', () => {
    useHealthCheckMock.mockReturnValue({
      data: { status: 'healthy' },
      isPending: false,
      isError: false,
      error: null,
    });
    render(<HealthCheckPanel />);
    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.queryByText('Database')).not.toBeInTheDocument();
    expect(screen.queryByText('Timestamp')).not.toBeInTheDocument();
  });
});