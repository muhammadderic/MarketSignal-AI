import type { ScoreOrNull } from "@shared/types";
import type { NewsItem } from "../types";

/** All filterable score buckets, in display order. */
export const SCORE_FILTER_OPTIONS: ScoreOrNull[] = [null, 1, 2, 3, 4, 5];

/** URL token for null. */
const NULL_TOKEN = "none";

/** Convert a URL token ("none" | "1"..."5") into a ScoreOrNull. */
const parseToken = (raw: string): ScoreOrNull | undefined => {
  if (raw === NULL_TOKEN) return null;
  const n = Number(raw);
  if (!Number.isInteger(n)) return undefined;
  return SCORE_FILTER_OPTIONS.find((s) => s === n);
};

/**
 * Parse the `score` query param into a set of selected scores.
 * Empty set means "no filter" (show everything).
 */
export const parseScoreFilter = (raw: string | null): Set<ScoreOrNull> => {
  if (!raw) return new Set();
  const tokens = raw.split(",").map((t) => t.trim()).filter(Boolean);
  const result = new Set<ScoreOrNull>();
  for (const t of tokens) {
    const v = parseToken(t);
    if (v !== undefined) result.add(v);
  }
  return result;
};

/** Serialize a set of selected scores back into a `score` query param. */
export const serializeScoreFilter = (selected: Set<ScoreOrNull>): string => {
  return SCORE_FILTER_OPTIONS.filter((s) => selected.has(s))
    .map((s) => (s === null ? NULL_TOKEN : String(s)))
    .join(",");
};

/** Apply the score filter to a list of news items. */
export const applyScoreFilter = (
  items: NewsItem[],
  selected: Set<ScoreOrNull>
): NewsItem[] => {
  if (selected.size === 0) return items;
  return items.filter((item) => selected.has(item.score));
};

/** Human-readable label for a score bucket (used in the filter UI). */
export const scoreFilterLabel = (score: ScoreOrNull): string =>
  score === null ? "Unscored" : String(score);