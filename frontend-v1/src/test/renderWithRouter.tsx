import type { ReactElement } from 'react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { render, type RenderResult } from '@testing-library/react';

export interface RenderWithRouterOptions {
  initialEntries?: string[];
}

export function renderWithRouter(
  ui: ReactElement,
  { initialEntries = ['/'] }: RenderWithRouterOptions = {},
): RenderResult & { router: ReturnType<typeof createMemoryRouter> } {
  const router = createMemoryRouter(
    [{ path: '*', element: ui }],
    { initialEntries },
  );
  const result = render(<RouterProvider router={router} />);
  return { ...result, router };
}