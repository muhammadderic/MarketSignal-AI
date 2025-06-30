import { useParams } from 'react-router';

export function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <main className="mx-auto max-w-3xl space-y-4 p-8">
      <h1 className="text-2xl font-bold text-slate-900">Article #{id}</h1>
      <p className="text-sm text-slate-500">Article detail view not yet implemented.</p>
    </main>
  );
}