import type { ScoreOrNull } from "@shared/types";

import {
  SCORE_FILTER_OPTIONS,
  scoreFilterLabel,
} from "../utils/scoreFilter";

interface NewsScoreFilterProps {
  selected: Set<ScoreOrNull>;
  onToggle: (score: ScoreOrNull) => void;
  onClear: () => void;
}

export const NewsScoreFilter = ({
  selected,
  onToggle,
  onClear,
}: NewsScoreFilterProps) => {
  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <span className="text-sm text-gray-600 mr-1">Score:</span>

      {SCORE_FILTER_OPTIONS.map((score) => {
        const isActive = selected.has(score);
        return (
          <button
            key={score === null ? "none" : score}
            type="button"
            onClick={() => onToggle(score)}
            aria-pressed={isActive}
            className={`px-3 py-1 rounded-full border text-sm transition-colors
              ${
                isActive
                  ? "bg-blue-600 border-blue-600 text-white"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
          >
            {scoreFilterLabel(score)}
          </button>
        );
      })}

      {selected.size > 0 && (
        <button
          type="button"
          onClick={onClear}
          className="ml-1 text-sm text-blue-700 underline"
        >
          Clear
        </button>
      )}
    </div>
  );
};