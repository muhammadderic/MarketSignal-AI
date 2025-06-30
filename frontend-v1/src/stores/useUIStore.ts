import { create } from 'zustand';

interface UIStoreState {
  selectedArticleIds: Set<number>;
  selectedDate: string | null;
  isEditorOpen: boolean;

  toggleArticleSelection: (id: number) => void;
  selectAll: (ids: number[]) => void;
  clearSelection: () => void;
  setSelectedDate: (date: string | null) => void;
  openEditor: () => void;
  closeEditor: () => void;
}

/**
 * Zustand store for purely client-side UI state per FRONTEND_COMPONENT.md Component #7.
 * Server state MUST live in TanStack Query; this store is not a cache.
 */
export const useUIStore = create<UIStoreState>((set) => ({
  selectedArticleIds: new Set<number>(),
  selectedDate: null,
  isEditorOpen: false,
  
  toggleArticleSelection: (id: number) =>
    set((state) => {
      const next = new Set(state.selectedArticleIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { selectedArticleIds: next };
    }),
  selectAll: (ids: number[]) => set({ selectedArticleIds: new Set(ids) }),
  clearSelection: () => set({ selectedArticleIds: new Set<number>() }),
  setSelectedDate: (date: string | null) => set({ selectedDate: date }),
  openEditor: () => set({ isEditorOpen: true }),
  closeEditor: () => set({ isEditorOpen: false }),
}));