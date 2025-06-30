import { Activity } from 'lucide-react';

import { useHealthCheck } from '@/hooks/useHealthCheck';

/**
 * Temporary root-route panel used to verify AC-003 (Vite proxy to backend).
 * Will be replaced when the calendar view is implemented under a feature task.
 */
export function HealthCheckPanel() {
  const { data, isPending, isError, error } = useHealthCheck();

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <header className="mb-4 flex items-center gap-2">
        <Activity className="h-5 w-5 text-slate-600" aria-hidden="true" />
        <h2 className="text-lg font-semibold text-slate-900">Backend connectivity</h2>
      </header>
      {isPending && <p className="text-sm text-slate-500">Probing /api/v1/health…</p>}
      {isError && (
        <p className="text-sm text-red-600">
          Health check failed: {error.message}
        </p>
      )}
      {data && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="font-medium text-slate-600">Status</dt>
          <dd className="text-slate-900">{data.status}</dd>
          {data.database && (
            <>
              <dt className="font-medium text-slate-600">Database</dt>
              <dd className="text-slate-900">{data.database}</dd>
            </>
          )}
          {data.timestamp && (
            <>
              <dt className="font-medium text-slate-600">Timestamp</dt>
              <dd className="text-slate-900">{data.timestamp}</dd>
            </>
          )}
        </dl>
      )}
    </section>
  );
}