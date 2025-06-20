import { create } from "zustand";
import { SELECTION_MAX } from "../types";

interface NewsSelectionState {
  /** Date the current selection. */
  date: string | null;
  /** Unique set of selected article IDs. */
  selectedIds: Set<number>;

  /** Start/continue selection for a given date; resets if date differs. */
  ensureDate: (date: string) => void;
  toggle: (id: number) => void;
  /** Remove multiple IDs. */
  clear: () => void;
}

export const useNewsSelectionStore = create<NewsSelectionState>((set, get) => ({
  date: null,
  selectedIds: new Set<number>(),

  ensureDate: (date) => {
    const current = get().date;
    if (current !== date) {
      // Date changed — selection must not silently mix dates (UD §2.2.8).
      set({ date, selectedIds: new Set<number>() });
    }
  },

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

  clear: () => set({ selectedIds: new Set<number>() }),
}))