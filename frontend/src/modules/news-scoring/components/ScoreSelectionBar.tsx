import { Loader2 } from "lucide-react";

interface ScoreSelectionBarProps {
  count: number;
  minSelection: number;
  maxSelection: number;
  canSubmit: boolean;
  isSubmitting: boolean;
  onSubmit: () => void;
}

export const ScoreSelectionBar = ({
  count,
  minSelection,
  maxSelection,
  canSubmit,
  isSubmitting,
  onSubmit,
}: ScoreSelectionBarProps) => {
  // Button is hidden until minimum reached.
  const visible = count >= minSelection;

  const remaining = Math.max(0, minSelection - count);

  return (
    <div className="sticky bottom-0 mt-4 rounded-lg border bg-white/95 backdrop-blur p-3 flex items-center justify-between gap-3">
      <span className="text-sm text-gray-700">
        {count} / {maxSelection} selected
        {count < minSelection && (
          <span className="text-gray-500">
            {" "}
            — select {remaining} more to score
          </span>
        )}
      </span>

      {visible && (
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || isSubmitting}
          className="inline-flex items-center gap-2 px-4 py-2 rounded bg-blue-600 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSubmitting ? "Scoring selected news…" : "Score Selected News"}
        </button>
      )}
    </div>
  );
};