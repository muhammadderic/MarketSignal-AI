import { useNewsSelectionStore } from "../store/newsSelectionStore";
import { SELECTION_MAX } from "../types";

export const useNewsSelection = () => {
  const selectedIds = useNewsSelectionStore((s) => s.selectedIds);
  const toggle = useNewsSelectionStore((s) => s.toggle);

  const count = selectedIds.size;

  const maxReached = count >= SELECTION_MAX;

  return {
    selectedIds,
    maxReached,
    toggle,
  }
}