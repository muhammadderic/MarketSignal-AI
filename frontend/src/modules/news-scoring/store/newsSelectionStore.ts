import { create } from "zustand";
import { SELECTION_MAX } from "../types";

interface NewsSelectionState {
  /** Date the current selection. */
  date: string | null;
  /** Unique set of selected article IDs. */
  selectedIds: Set<string>;

  /** Start/continue selection for a given date; resets if date differs. */
  toggle: (id: string) => void;
}

export const useNewsSelectionStore = create<NewsSelectionState>((set, get) => ({
  date: null,
  selectedIds: new Set<string>(),

  toggle: (id) => {
    const { selectedIds } = get();
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      if (next.size >= SELECTION_MAX) return; // enforce max
      next.add(id);
    }
    set({ selectedIds: next });
  },
}))