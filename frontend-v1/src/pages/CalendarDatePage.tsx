import { useParams } from 'react-router';

export function CalendarDatePage() {
  const { date } = useParams<{ date: string }>();
  
  return (
    <main className="mx-auto max-w-3xl space-y-4 p-8">
      <h1 className="text-2xl font-bold text-slate-900">Calendar: {date}</h1>
      <p className="text-sm text-slate-500">Calendar view not yet implemented.</p>
    </main>
  );
}