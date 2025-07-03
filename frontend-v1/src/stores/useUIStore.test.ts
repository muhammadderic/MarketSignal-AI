import { beforeEach, describe, expect, it } from 'vitest';
import { useUIStore } from './useUIStore';

/**
 * Unit tests for the Zustand UI store (TESTING_STRATEGY.md §1 Unit — frontend:
 * "Zustand UI store state mutations").
 *
 * The store is a module-level singleton; state is reset before each test to
 * keep assertions independent of execution order.
 */
describe('useUIStore', () => {
  beforeEach(() => {
    useUIStore.setState({
      selectedArticleIds: new Set<number>(),
      selectedDate: null,
      isEditorOpen: false,
    });
  });

  it('setSelectedDate stores and clears the date', () => {
    useUIStore.getState().setSelectedDate('2026-10-28');
    expect(useUIStore.getState().selectedDate).toBe('2026-10-28');

    useUIStore.getState().setSelectedDate(null);
    expect(useUIStore.getState().selectedDate).toBeNull();
  });

  it('toggleArticleSelection adds an id, then removes it on the second call', () => {
    useUIStore.getState().toggleArticleSelection(1);
    expect(useUIStore.getState().selectedArticleIds.has(1)).toBe(true);

    useUIStore.getState().toggleArticleSelection(1);
    expect(useUIStore.getState().selectedArticleIds.has(1)).toBe(false);
  });

  it('toggleArticleSelection replaces the Set instance (immutable update)', () => {
    const before = useUIStore.getState().selectedArticleIds;
    useUIStore.getState().toggleArticleSelection(2);
    const after = useUIStore.getState().selectedArticleIds;

    expect(after).not.toBe(before);
    expect(before.has(2)).toBe(false);
    expect(after.has(2)).toBe(true);
  });

  it('selectAll replaces the current selection', () => {
    useUIStore.getState().toggleArticleSelection(99);
    useUIStore.getState().selectAll([1, 2, 3]);

    const ids = useUIStore.getState().selectedArticleIds;
    expect(Array.from(ids).sort()).toEqual([1, 2, 3]);
  });

  it('clearSelection empties the selected id set', () => {
    useUIStore.getState().selectAll([1, 2]);
    useUIStore.getState().clearSelection();

    expect(useUIStore.getState().selectedArticleIds.size).toBe(0);
  });

  it('openEditor and closeEditor flip isEditorOpen', () => {
    useUIStore.getState().openEditor();
    expect(useUIStore.getState().isEditorOpen).toBe(true);

    useUIStore.getState().closeEditor();
    expect(useUIStore.getState().isEditorOpen).toBe(false);
  });
});