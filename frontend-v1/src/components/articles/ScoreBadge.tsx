export interface ScoreBadgeProps {
  score: number | null;
  reasoning?: string | null;
  /** Optional callback to (re)score this single article (AC-007 / FR-009). */
  onScore?: () => void;
  /** Disables the inline score trigger while a mutation is pending. */
  isScoring?: boolean;
}

const TIER_CLASS: Record<number, string> = {
  1: 'bg-gray-100 text-gray-700 border-gray-200',
  2: 'bg-gray-100 text-gray-700 border-gray-200',
  3: 'bg-blue-100 text-blue-800 border-blue-200',
  4: 'bg-green-100 text-green-800 border-green-200',
  5: 'bg-purple-100 text-purple-800 border-purple-300',
};

const UNSCORED_CLASS = 'bg-slate-100 text-slate-500 border-slate-200';

function tierClass(score: number | null): string {
  if (score === null) return UNSCORED_CLASS;
  return TIER_CLASS[score] ?? UNSCORED_CLASS;
}

/**
 * Numeric relevance score badge with color-coded tier and hoverable reasoning.
 * Read-only display; the parent controls the single-article score trigger.
 */
export function ScoreBadge({ score, reasoning, onScore, isScoring }: ScoreBadgeProps) {
  const title =
    score !== null && reasoning
      ? `Score ${score}/5 — ${reasoning}`
      : score !== null
        ? `Score ${score}/5`
        : 'Not yet scored';

  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`rounded border px-1.5 py-0.5 text-xs font-medium ${tierClass(score)}`}
        title={title}
        aria-label={title}
        data-score-tier={score ?? 'unscored'}
      >
        {score !== null ? `Score ${score}/5` : 'Unscored'}
      </span>
      {onScore ? (
        <button
          type="button"
          onClick={onScore}
          disabled={isScoring}
          title={score !== null ? 'Re-score relevance' : 'Score relevance'}
          className="rounded border border-slate-300 bg-white px-1.5 py-0.5 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isScoring ? 'Scoring…' : score !== null ? 'Re-score' : 'Score'}
        </button>
      ) : null}
    </span>
  );
}