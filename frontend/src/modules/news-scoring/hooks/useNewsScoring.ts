import { useCallback } from "react";

import { useScoreNews } from "../queries/useScoreNews";
import { useNewsSelection } from "./useNewsSelection";
import toast from "react-hot-toast";

/**
 * Orchestrates the scoring submission flow:
 *  - snapshot the IDs at click time
 *  - prevent duplicate submissions
 *  - on success clear processed selections
 */
export const useNewsScoring = (date: string | null) => {
  const selection = useNewsSelection();
  const mutation = useScoreNews();

  const submit = useCallback(() => {
    if (!date) return;
    if (mutation.isPending) return;
    if (!selection.canSubmit) return;

    const ids = selection.snapshotIds();

    mutation.mutate(
      { date, payload: { news_ids: ids } },
      {
        onSuccess: () => {
          // Successfully processed selections are cleared.
          // On partial failure the backend returns updated persisted data;
          selection.clear();
          toast.success("Scoring complete.");
        },
        onError: (error) => {
          // Selection preserved on failure.
          toast.error("Failed to score selected news. Please try again.");
          // error is already surfaced by the shared axios interceptor for
          // generic cases; operation-specific message shown above.
          void error;
        },
      }
    );
  }, [date, mutation, selection])

  return {
    selection,
    isSubmitting: mutation.isPending,
    submit
  }
}