import type { ScoreOrNull } from "@shared/types";
import type { NewsItem } from "../types";

export type CardColor = "gold" | "light-blue" | "gray" | "white";

/**
 * Derive card color from score per UD §2.3.
 * UI-only concern — not part of the API contract.
 */
export const getCardColor = (score: ScoreOrNull): CardColor => {
  if (score === null) return "white";
  if (score === 5) return "gold";
  if (score === 1) return "gray";
  return "light-blue"; // 2, 3, 4
};

export const cardColorClass: Record<CardColor, string> = {
  gold: "bg-amber-100 border-amber-300",
  "light-blue": "bg-sky-100 border-sky-300",
  gray: "bg-gray-100 border-gray-300",
  white: "bg-white border-gray-200",
};

/**
 * Normalize a raw score coming from the API.
 * Integers 1–5 are kept; everything else becomes null.
 */
export const normalizeScore = (raw: unknown): ScoreOrNull => {
  if (typeof raw !== "number" || !Number.isInteger(raw)) return null;
  if (raw < 1 || raw > 5) return null;
  return raw as ScoreOrNull;
};

/**
 * Normalize a raw locale. Unrecognized / missing → UNASSIGNED.
 */
export const normalizeLocale = (raw: unknown): NewsItem["locale"] => {
  if (raw === "ID" || raw === "US" || raw === "GLOBAL" || raw === "UNASSIGNED") {
    return raw;
  }
  return "UNASSIGNED";
};