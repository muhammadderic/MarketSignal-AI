import { useCallback, useMemo } from "react";
import { useNewsSelectionStore } from "../store/newsSelectionStore";
import { SELECTION_MAX, SELECTION_MIN } from "../types";

export const useNewsSelection = () => {
  const selectedIds = useNewsSelectionStore((s) => s.selectedIds);
  const toggle = useNewsSelectionStore((s) => s.toggle);
  const clear = useNewsSelectionStore((s) => s.clear);

  const count = selectedIds.size;

  const canSubmit = useMemo(
    () => count >= SELECTION_MIN && count <= SELECTION_MAX,
    [count]
  );

  const maxReached = count >= SELECTION_MAX;

  /** IDs snapshot for submission — order stable, unique. */
  const snapshotIds = useCallback(
    () => Array.from(selectedIds),
    [selectedIds]
  );

  return {
    selectedIds,
    count,
    canSubmit,
    maxReached,
    minSelection: SELECTION_MIN,
    maxSelection: SELECTION_MAX,
    toggle,
    clear,
    snapshotIds,
  }
}