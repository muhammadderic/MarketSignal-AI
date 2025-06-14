/**
 * Timezone convention for the News Archive feature.
 * All publication-date grouping is done in UTC+7 (Asia/Jakarta),
 * matching the agreed source of truth for this application.
 */
export const ARCHIVE_TIMEZONE = "Asia/Jakarta";

const MONTH_REGEX = /^\d{4}-(0[1-9]|1[0-2])$/;
const DATE_REGEX = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;

export const isValidMonth = (month: string): boolean => MONTH_REGEX.test(month);

export const isValidDate = (date: string): boolean => DATE_REGEX.test(date);

/** Format a Date as YYYY-MM-DD in the archive timezone. */
export const toArchiveDate = (d: Date): string => {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: ARCHIVE_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(d);
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}`;
};

/** Format a Date as YYYY-MM in the archive timezone. */
export const toArchiveMonth = (d: Date): string =>
  toArchiveDate(d).slice(0, 7);