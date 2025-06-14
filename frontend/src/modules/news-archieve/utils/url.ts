const SAFE_PROTOCOLS = new Set(["https:", "http:"]);

/**
 * Validate an article URL before rendering it as a clickable link.
 * Returns true only for http/https URLs.
 */
export const isSafeArticleUrl = (raw: string | null | undefined): boolean => {
  if (!raw) return false;
  try {
    const url = new URL(raw);
    return SAFE_PROTOCOLS.has(url.protocol);
  } catch {
    return false;
  }
};

/**
 * Truncate visible URL text only; the underlying href must remain complete.
 */
export const truncateUrl = (url: string, max = 48): string =>
  url.length <= max ? url : `${url.slice(0, max - 1)}...`;