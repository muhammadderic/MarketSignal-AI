import { HealthCheckPanel } from '@/components/HealthCheckPanel';

export function HomePage(){
  return (
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-2xl font-bold text-slate-900">MarketSignal AI</h1>
      <HealthCheckPanel />
    </main>
  );
}